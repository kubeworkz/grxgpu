// Minimal DSMEM smoke test.
// Writes a known value to shared memory, then reads it back via
// vx_dsmem_read (same core) to verify decode + execute path.

#include <stdint.h>
#include <vx_intrinsics.h>
#include <vx_dsmem.h>

extern "C" kernel_arg_t kernel_arg;

void kernel_body() {
  uint32_t tid = threadIdx.x;

  if (tid == 0) {
    // Write a known value to the start of our LMEM.
    volatile uint32_t* lmem = (volatile uint32_t*)0x80000000;
    lmem[0] = 0xDEADBEEF;
    __asm__ volatile ("fence" ::: "memory");

    // Read it back via DSMEM (same core = core 0).
    uint32_t val = vx_dsmem_read(0, 0x80000000);

    // Store result to global memory for verification.
    kernel_arg.C_addr[0] = val;
  }
}
