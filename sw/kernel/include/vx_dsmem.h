// Copyright (c) 2024 Vortex
//
// Distributed shared memory read intrinsic.
// Reads a word from another core's local memory (smem) within the same cluster.
// In the sim, this is a synchronous direct-read via the SFU.

#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Read a 32-bit word from target_core's local memory at local_addr.
// target_core is cluster-local core index (0..NUM_CORES_PER_CLUSTER-1).
// local_addr is byte address in the target core's LMEM (must be 4-byte aligned).
static inline uint32_t vx_dsmem_read(uint32_t target_core, uint32_t local_addr) {
#ifdef __VORTEX__
  uint32_t result;
  __asm__ volatile (
    // EXT1 opcode (0b0001011), funct7=5 (DSMEM.READ)
    // rd, rs1=target_core, rs2=local_addr
    ".word (0b0000101 << 25 | %[rs2] << 20 | %[rs1] << 15 | %[rd] << 7 | 0b0001011)\n"
    : [rd] "=r" (result)
    : [rs1] "r" (target_core), [rs2] "r" (local_addr)
  );
  return result;
#else
  (void)target_core; (void)local_addr;
  return 0;
#endif
}

#ifdef __cplusplus
}
#endif
