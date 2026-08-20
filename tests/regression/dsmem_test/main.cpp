// Minimal DSMEM smoke test host side.
// Launches 1 CTA, verifies DSMEM read of own LMEM returns 0xDEADBEEF.

#include "common.h"
#include <iostream>
#include <string.h>
#include <unistd.h>
#include <util.h>
#include <vector>
#include <vortex2.h>

#define RT_CHECK(_expr)                                      \
  do {                                                       \
    int _ret = _expr;                                        \
    if (0 == _ret)                                           \
      break;                                                 \
    printf("Error: '%s' returned %d!\n", #_expr, (int)_ret); \
    cleanup();                                               \
    exit(-1);                                                \
  } while (false)

using namespace vortex;

///////////////////////////////////////////////////////////////////////////////

static Device *device = nullptr;

static void cleanup() {
  if (device) {
    device->release();
    device = nullptr;
  }
}

int main(int argc, char **argv) {
  // Number of warps per CTA.
  uint32_t num_warps = 4;

  // Parse options.
  int opt;
  while ((opt = getopt(argc, argv, "w:h")) != -1) {
    switch (opt) {
    case 'w':
      num_warps = std::atoi(optarg);
      break;
    case 'h':
      printf("Usage: %s [-w num_warps]\n", argv[0]);
      return 0;
    default:
      break;
    }
  }

  RT_CHECK(api::init(nullptr));

  api::device_attrib_t attrib;
  RT_CHECK(api::device_get_attrib(VX_DEVICE_ATTRIB_NUM_CORES, &attrib));
  uint32_t num_cores = attrib.value;

  api::device_attrib_t warps_attrib;
  RT_CHECK(api::device_get_attrib(VX_DEVICE_ATTRIB_NUM_WARPS, &warps_attrib));
  uint32_t max_warps = warps_attrib.value;

  RT_CHECK(api::device_get_attrib(VX_DEVICE_ATTRIB_NUM_THREADS, &warps_attrib));
  uint32_t num_threads = warps_attrib.value;

  std::cout << "Device: " << num_cores << " cores, " << max_warps << " warps/core, "
            << num_threads << " threads/warp" << std::endl;

  device = new Device(num_cores, max_warps, num_threads);

  // Allocate output buffer (1 word).
  uint64_t C_size = 4;
  void* C_buf = device->memory_alloc(C_size);
  RT_CHECK(C_buf != nullptr ? 0 : -1);
  memset(C_buf, 0, C_size);

  // Setup kernel args.
  kernel_arg_t kernel_arg;
  memset(&kernel_arg, 0, sizeof(kernel_arg));
  kernel_arg.C_addr = device->memory_to_device(C_buf, C_size);

  // Load kernel.
  RT_CHECK(device->upload_kernel("kernel.cpp"));

  // Launch: 2 CTAs (to test cross-CTA), 1 warp each, 1 thread.
  uint32_t grid_dim_x = 2;
  uint32_t block_dim = 1;
  RT_CHECK(device->launch(grid_dim_x, 1, 1, block_dim, 1, 1, &kernel_arg, sizeof(kernel_arg)));

  std::cout << "Launched kernel: grid=(" << grid_dim_x << "), block=(" << block_dim << ")" << std::endl;

  // Wait for completion.
  RT_CHECK(device->join());

  // Read back result.
  device->memory_download(C_buf, kernel_arg.C_addr, C_size);
  uint32_t result = *(uint32_t*)C_buf;

  std::cout << "Result: 0x" << std::hex << result << std::dec << std::endl;

  int errors = 0;
  if (result != 0xDEADBEEF) {
    std::cout << "MISMATCH! Expected 0xDEADBEEF, got 0x" << std::hex << result << std::dec << std::endl;
    errors++;
  }

  cleanup();

  if (errors) {
    std::cout << "FAILED: " << errors << " errors" << std::endl;
    return -1;
  }

  std::cout << "PASSED!" << std::endl;
  return 0;
}
