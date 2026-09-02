// Copyright (c) 2024 grxgpu
// TGM instruction encoding for Phase 2 self-pipelining tensor FSM.
#pragma once
#include <stdint.h>

// R-type encoding:
//   opcode  [6:0]  = 0x0B (EXT1)
//   rd      [11:7] = accumulator register (float)
//   funct3  [14:12]= 3 (TGM selector)
//   rs1     [19:15]= A descriptor register (a0)
//   rs2     [24:20]= B descriptor register (a1)
//   funct7  [31:25]= K_end (number of K-tiles, 0-127)
// Format params hardcoded: fp16->fp32, 8 C/D regs, A from smem.

#ifdef __cplusplus
extern "C" {
#endif

static inline uint32_t vx_tgm_encode(uint32_t k_end) {
  return 0x0B | (0u << 7) | (3u << 12) | (10u << 15) | (11u << 20) | ((k_end & 0x7Fu) << 25);
}

#ifdef __cplusplus
}
#endif

// Templated TGM issue: K_END must be a compile-time constant.
template <uint32_t K_END>
static inline void vx_tgm_imm(uint32_t desc_a, uint32_t desc_b) {
#ifdef __VORTEX__
  constexpr uint32_t INSN = 0x0B | (0u << 7) | (3u << 12) | (10u << 15) | (11u << 20) | ((K_END & 0x7Fu) << 25);
  __asm__ volatile (
    "mv a0, %[da]\n"
    "mv a1, %[db]\n"
    ".word %[insn]\n"
    : : [da] "r" (desc_a), [db] "r" (desc_b),
        [insn] "i" (INSN)
    : "a0", "a1", "memory"
  );
#endif
}
