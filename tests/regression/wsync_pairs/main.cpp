#include <cstdio>
#include <cstdlib>
#include <iostream>
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

static constexpr uint32_t kEmpty = 0xDEADBEEFu;

// A wedged warp never signals the launch event, so bound the wait rather than
// hanging the test until the CI job times out.
static constexpr uint64_t kLaunchTimeoutNs = 120ull * 1000 * 1000 * 1000;

const char* kernel_file = "kernel.vxbin";
uint32_t iterations = 64;

vx_device_h device = nullptr;
vx_buffer_h dst_buffer = nullptr;
vx_queue_h queue = nullptr;
vx_module_h module_ = nullptr;
vx_kernel_h kernel = nullptr;
kernel_arg_t kernel_arg = {};

static void show_usage() {
  std::cout << "Vortex back-to-back WSYNC Test." << std::endl;
  std::cout << "Usage: [-n iterations] [-k kernel] [-h help]" << std::endl;
}

static void parse_args(int argc, char** argv) {
  int c;
  while ((c = getopt(argc, argv, "n:k:h")) != -1) {
    switch (c) {
    case 'n':
      iterations = std::atoi(optarg);
      break;
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
    if (dst_buffer) vx_buffer_release(dst_buffer);
    if (kernel)    vx_kernel_release(kernel);
    if (module_)   vx_module_release(module_);
    if (queue)     vx_queue_release(queue);
    vx_device_dump_perf(device, stdout);
    vx_device_release(device);
  }
}

int main(int argc, char* argv[]) {
  parse_args(argc, argv);

  if (0 == iterations) {
    std::cout << "Error: iterations must be greater than zero" << std::endl;
    return -1;
  }

  std::cout << "open device connection" << std::endl;
  RT_CHECK(vx_device_open(0, &device));

  vx_queue_info_t qi = { sizeof(qi), nullptr, VX_QUEUE_PRIORITY_NORMAL, 0 };
  RT_CHECK(vx_queue_create(device, &qi, &queue));

  uint64_t num_cores = 0;
  uint64_t num_threads = 0;
  RT_CHECK(vx_device_query(device, VX_CAPS_NUM_CORES, &num_cores));
  RT_CHECK(vx_device_query(device, VX_CAPS_NUM_THREADS, &num_threads));

  std::cout << "num_cores: " << num_cores << std::endl;
  std::cout << "iterations: " << iterations << " (wsync pairs per iteration)" << std::endl;

  uint32_t buf_words = iterations + static_cast<uint32_t>(num_cores);
  uint32_t buf_size = buf_words * sizeof(uint32_t);
  std::vector<uint32_t> h_dst(buf_words, kEmpty);

  RT_CHECK(vx_buffer_create(device, buf_size, VX_MEM_READ_WRITE, &dst_buffer));
  RT_CHECK(vx_buffer_address(dst_buffer, &kernel_arg.dst_addr));
  RT_CHECK(vx_enqueue_write(queue, dst_buffer, 0, h_dst.data(), buf_size, 0, nullptr, nullptr));

  kernel_arg.count = iterations;

  std::cout << "load kernel module" << std::endl;
  RT_CHECK(vx_module_load_file(device, kernel_file, &module_));
  RT_CHECK(vx_module_get_kernel(module_, "main", &kernel));

  int errors = 0;
  {
    vx_event_h launch_ev = nullptr;
    vx_launch_info_t li = {};
    li.struct_size  = sizeof(li);
    li.kernel       = kernel;
    li.args_host    = &kernel_arg;
    li.args_size    = sizeof(kernel_arg);
    li.ndim         = 1;
    li.grid_dim[0]  = static_cast<uint32_t>(num_cores);
    li.block_dim[0] = static_cast<uint32_t>(num_threads);

    std::cout << "start execution" << std::endl;
    RT_CHECK(vx_enqueue_launch(queue, &li, 0, nullptr, &launch_ev));

    vx_result_t res = vx_event_wait_value(launch_ev, 1, kLaunchTimeoutNs);
    if (VX_SUCCESS != res) {
      std::cout << "*** error: kernel did not complete within "
                << (kLaunchTimeoutNs / 1000000000ull) << "s; warp wedged on WSYNC" << std::endl;
      ++errors;
    }
    vx_event_release(launch_ev);
  }

  if (0 == errors) {
    vx_event_h read_ev = nullptr;
    RT_CHECK(vx_enqueue_read(queue, h_dst.data(), dst_buffer, 0, buf_size, 0, nullptr, &read_ev));
    RT_CHECK(vx_event_wait_value(read_ev, 1, VX_TIMEOUT_INFINITE));
    vx_event_release(read_ev);

    std::cout << "verify result" << std::endl;
    for (uint32_t i = 0; i < iterations; ++i) {
      uint32_t ref = WSYNC_PAIRS_VALUE ^ i;
      if (h_dst[i] != ref) {
        printf("*** error: [%u] expected=0x%08x, actual=0x%08x\n", i, ref, h_dst[i]);
        ++errors;
      }
    }
    for (uint32_t c = 0; c < num_cores; ++c) {
      uint32_t ref = WSYNC_PAIRS_SENTINEL | c;
      if (h_dst[iterations + c] != ref) {
        printf("*** error: [core %u] expected=0x%08x, actual=0x%08x\n", c, ref, h_dst[iterations + c]);
        ++errors;
      }
    }
  }

  std::cout << "cleanup" << std::endl;
  cleanup();

  if (0 != errors) {
    std::cout << "Found " << errors << " errors!" << std::endl;
    std::cout << "FAILED!" << std::endl;
    return errors;
  }

  std::cout << "PASSED!" << std::endl;
  return 0;
}
