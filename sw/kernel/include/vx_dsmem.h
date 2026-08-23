// Copyright (c) 2024 Vortex
//
// Distributed shared memory read intrinsic.
// Reads a 32-bit word from another core's local memory (smem) within the same cluster.
// Also provides a lightweight mailbox for cross-core synchronization.

#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Read a 32-bit word from target_core's local memory at local_addr.
// Uses EXT1 (RISCV_CUSTOM0) opcode, funct7=5 (DSMEM.READ), funct3=0.
static inline uint32_t vx_dsmem_read(uint32_t target_core, uint32_t local_addr) {
#ifdef __VORTEX__
  uint32_t result;
  __asm__ volatile (
    ".insn r %1, 0, 5, %0, %2, %3"
    : "=r" (result)
    : "i" (0x0B), "r" (target_core), "r" (local_addr)
    : "memory"
  );
  return result;
#else
  (void)target_core; (void)local_addr;
  return 0;
#endif
}

// Non-stalling cross-core mailbox read.
// Uses EXT1 (RISCV_CUSTOM0) opcode, funct7=6 (DSMEM.MAILBOX_READ), funct3=0.
// Returns the target core's VX_CSR_MAILBOX value without stalling the pipeline.
static inline uint32_t vx_mailbox_read(uint32_t target_core) {
#ifdef __VORTEX__
  uint32_t result;
  __asm__ volatile (
    ".insn r %1, 0, 6, %0, %2, %3"
    : "=r" (result)
    : "i" (0x0B), "r" (target_core), "r" (0)
    : "memory"
  );
  return result;
#else
  (void)target_core;
  return 0;
#endif
}

#ifdef __cplusplus
}
#endif
