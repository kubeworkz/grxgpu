// Copyright (c) 2024 grxgpu
// TGM instruction encoding for Phase 2 self-pipelining tensor FSM.
#pragma once
#include <stdint.h>

// Build raw TGM instruction word (for runtime use / debugging).
// Encoding: funct7[3:0] = K_end, rd=accumulator, rs1=A_desc, rs2=B_desc
#ifdef __cplusplus
extern "C" {
#endif

static inline uint32_t vx_tgm_encode(uint32_t k_end) {
  // R-type: opcode=0x0B | rd=0 | funct3=3 | rs1=10(a0) | rs2=11(a1) | funct7[3:0]=k_end
  return 0x0B | (0u << 7) | (3u << 12) | (10u << 15) | (11u << 20) | ((k_end & 0xF) << 22);
}

#ifdef __cplusplus
}
#endif

// Templated TGM issue: K_END must be a compile-time constant.
template <uint32_t K_END>
static inline void vx_tgm_imm(uint32_t desc_a, uint32_t desc_b) {
#ifdef __VORTEX__
  constexpr uint32_t INSN = 0x0B | (0u << 7) | (3u << 12) | (10u << 15) | (11u << 20) | ((K_END & 0xF) << 22);
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
