#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <unistd.h>
#include <vector>
#include <vortex2.h>
#include "common.h"

#define RT_CHECK(_expr)                                         \
   do {                                                         \
     int _ret = _expr;                                          \
     if (0 == _ret)                                             \
       break;                                                   \
     printf("Error: '%s' returned %d!\n", #_expr, (int)_ret);   \
     cleanup();                                                 \
     exit(-1);                                                  \
   } while (false)

const char* kernel_file = "kernel.vxbin";

vx_device_h device = nullptr;
vx_buffer_h pre_buffer = nullptr;
vx_buffer_h post_buffer = nullptr;
vx_buffer_h phase_buffer = nullptr;
vx_buffer_h status_buffer = nullptr;
vx_queue_h  queue   = nullptr;
vx_module_h module_ = nullptr;
vx_kernel_h kernel  = nullptr;
kernel_arg_t kernel_arg = {};

static void show_usage() {
  std::cout << "Vortex Test." << std::endl;
  std::cout << "Usage: [-k: kernel] [-h: help]" << std::endl;
}

static void parse_args(int argc, char** argv) {
  int c;
  while ((c = getopt(argc, argv, "k:h")) != -1) {
    switch (c) {
    case 'k':
      kernel_file = optarg;
      break;
    case 'h':
      show_usage();
      exit(0);
      break;
    default:
      show_usage();
      exit(-1);
    }
  }
}

void cleanup() {
  if (device) {
    if (pre_buffer)    vx_buffer_release(pre_buffer);
    if (post_buffer)   vx_buffer_release(post_buffer);
    if (phase_buffer)  vx_buffer_release(phase_buffer);
    if (status_buffer) vx_buffer_release(status_buffer);
    if (kernel)  vx_kernel_release(kernel);
    if (module_) vx_module_release(module_);
    if (queue)   vx_queue_release(queue);
    vx_device_dump_perf(device, stdout);
    vx_device_release(device);
  }
}

int main(int argc, char* argv[]) {
  parse_args(argc, argv);

  std::cout << "open device connection" << std::endl;
  RT_CHECK(vx_device_open(0, &device));

  vx_queue_info_t qi = { sizeof(qi), nullptr, VX_QUEUE_PRIORITY_NORMAL, 0 };
  RT_CHECK(vx_queue_create(device, &qi, &queue));

  uint64_t num_cores, num_warps, num_threads;
  RT_CHECK(vx_device_query(device, VX_CAPS_NUM_CORES, &num_cores));
  RT_CHECK(vx_device_query(device, VX_CAPS_NUM_WARPS, &num_warps));
  RT_CHECK(vx_device_query(device, VX_CAPS_NUM_THREADS, &num_threads));

  if (num_cores < 2) {
    std::cout << "Device does not have enough cores to run the test (need at least 2)" << std::endl;
    cleanup();
    return -1;
  }

  kernel_arg.num_cores  = static_cast<uint32_t>(num_cores);
  kernel_arg.num_groups = static_cast<uint32_t>(num_cores * num_warps);
  kernel_arg.group_size = static_cast<uint32_t>(num_threads);

  constexpr uint32_t num_rounds = ASYNC_GBARRIER_NUM_ROUNDS;
  constexpr uint32_t num_launches = 2;
  uint32_t result_count = kernel_arg.num_cores * num_rounds * num_launches;
  uint32_t result_size = result_count * sizeof(uint32_t);
  uint32_t status_size = num_rounds * num_launches * sizeof(uint32_t);

  std::cout << "num_cores=" << num_cores
            << ", num_warps=" << num_warps
            << ", num_threads=" << num_threads << std::endl;
  std::cout << "num_groups=" << kernel_arg.num_groups << std::endl;

  std::cout << "allocate device memory" << std::endl;
  RT_CHECK(vx_buffer_create(device, result_size, VX_MEM_READ_WRITE, &pre_buffer));
  RT_CHECK(vx_buffer_address(pre_buffer, &kernel_arg.pre_addr));
  RT_CHECK(vx_buffer_create(device, result_size, VX_MEM_READ_WRITE, &post_buffer));
  RT_CHECK(vx_buffer_address(post_buffer, &kernel_arg.post_addr));
  RT_CHECK(vx_buffer_create(device, result_size, VX_MEM_READ_WRITE, &phase_buffer));
  RT_CHECK(vx_buffer_address(phase_buffer, &kernel_arg.phase_addr));
  RT_CHECK(vx_buffer_create(device, status_size, VX_MEM_READ_WRITE, &status_buffer));
  RT_CHECK(vx_buffer_address(status_buffer, &kernel_arg.status_addr));

  std::vector<uint32_t> h_pre(result_count, 0);
  std::vector<uint32_t> h_post(result_count, 0);
  std::vector<uint32_t> h_phase(result_count, 0xffffffffu);
  std::vector<uint32_t> h_status(num_rounds * num_launches, 0xdeadbeef);

  RT_CHECK(vx_enqueue_write(queue, pre_buffer, 0, h_pre.data(), result_size, 0, nullptr, nullptr));
  RT_CHECK(vx_enqueue_write(queue, post_buffer, 0, h_post.data(), result_size, 0, nullptr, nullptr));
  RT_CHECK(vx_enqueue_write(queue, phase_buffer, 0, h_phase.data(), result_size, 0, nullptr, nullptr));
  RT_CHECK(vx_enqueue_write(queue, status_buffer, 0, h_status.data(), status_size, 0, nullptr, nullptr));

  std::cout << "load kernel module" << std::endl;
  RT_CHECK(vx_module_load_file(device, kernel_file, &module_));
  RT_CHECK(vx_module_get_kernel(module_, "main", &kernel));

  std::cout << "launch twice to exercise global-barrier reset" << std::endl;
  for (uint32_t launch = 0; launch < num_launches; ++launch) {
    kernel_arg.launch_id = launch;
    uint32_t grid_dim[1]  = {kernel_arg.num_groups};
    uint32_t block_dim[1] = {kernel_arg.group_size};
    vx_launch_info_t li = {};
    li.struct_size  = sizeof(li);
    li.kernel       = kernel;
    li.args_host    = &kernel_arg;
    li.args_size    = sizeof(kernel_arg);
    li.ndim         = 1;
    li.grid_dim[0]  = grid_dim[0];
    li.block_dim[0] = block_dim[0];
    vx_event_h launch_ev = nullptr;
    RT_CHECK(vx_enqueue_launch(queue, &li, 0, nullptr, &launch_ev));
    RT_CHECK(vx_event_wait_value(launch_ev, 1, VX_TIMEOUT_INFINITE));
    vx_event_release(launch_ev);
  }

  std::cout << "download results" << std::endl;
  vx_event_h read_pre = nullptr, read_post = nullptr, read_phase = nullptr, read_status = nullptr;
  RT_CHECK(vx_enqueue_read(queue, h_pre.data(), pre_buffer, 0, result_size, 0, nullptr, &read_pre));
  RT_CHECK(vx_enqueue_read(queue, h_post.data(), post_buffer, 0, result_size, 0, nullptr, &read_post));
  RT_CHECK(vx_enqueue_read(queue, h_phase.data(), phase_buffer, 0, result_size, 0, nullptr, &read_phase));
  RT_CHECK(vx_enqueue_read(queue, h_status.data(), status_buffer, 0, status_size, 0, nullptr, &read_status));
  RT_CHECK(vx_event_wait_value(read_status, 1, VX_TIMEOUT_INFINITE));
  vx_event_release(read_status);
  vx_event_release(read_phase);
  vx_event_release(read_post);
  vx_event_release(read_pre);

  int errors = 0;
  for (uint32_t launch = 0; launch < num_launches; ++launch) {
    for (uint32_t round = 0; round < num_rounds; ++round) {
      uint32_t base = (launch * num_rounds + round) * kernel_arg.num_cores;
      for (uint32_t i = 0; i < kernel_arg.num_cores; ++i) {
        uint32_t expected_pre = launch * 1000 + (round + 1) * (i + 1);
        uint32_t expected_post = round == 0
                               ? kernel_arg.num_cores * launch * 1000
                                   + (kernel_arg.num_cores * (kernel_arg.num_cores + 1)) / 2
                               : expected_pre;
        if (h_pre[base + i] != expected_pre) {
          std::cout << "pre mismatch at launch " << launch << ", round " << round
                    << ", core " << i << ": got " << h_pre[base + i]
                    << ", expected " << expected_pre << std::endl;
          ++errors;
        }
        if (h_post[base + i] != expected_post) {
          std::cout << "post mismatch at launch " << launch << ", round " << round
                    << ", core " << i << ": got " << h_post[base + i]
                    << ", expected " << expected_post << std::endl;
          ++errors;
        }
        uint32_t expected_phase = (round >> 1) & 1;
        if (h_phase[base + i] != expected_phase) {
          std::cout << "phase mismatch at launch " << launch << ", round " << round
                    << ", core " << i << ": got " << h_phase[base + i]
                    << ", expected " << expected_phase << std::endl;
          ++errors;
        }
      }
      uint32_t status_index = launch * num_rounds + round;
      if (h_status[status_index] != 0) {
        std::cout << "kernel reported status errors=" << h_status[status_index]
                  << " at launch " << launch << ", round " << round << std::endl;
        ++errors;
      }
    }
  }

  std::cout << "cleanup" << std::endl;
  cleanup();

  if (errors != 0) {
    std::cout << "Found " << errors << " errors!" << std::endl;
    std::cout << "FAILED!" << std::endl;
    return errors;
  }

  std::cout << "PASSED!" << std::endl;
  return 0;
}
