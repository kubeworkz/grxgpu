// Copyright (c) 2024 grxgpu
// TGM instruction encoding for Phase 2 self-pipelining tensor FSM.
#pragma once
#include <stdint.h>

// R-type encoding:
//   opcode  [6:0]  = 0x0B (EXT1)
//   rd      [11:7] = accumulator base register (float f0)
//   funct3  [14:12]= 3 (TGM selector)
//   rs1     [19:15]= A descriptor register (a0)
//   rs2     [24:20]= B descriptor register (a1)
//   funct7  [31:25]= 2 (TCU extension route; K_END travels in a2=x12)
// Additional args via caller-saved registers:
//   a2 (x12) = K_END (number of K-tiles)
// Tile row/col are derived by the FSM from the CTA's block_idx CSRs.
// Format params derived from the fixed WGMMA context: fp16->fp32, 8 C/D regs,
// A from smem. The FSM writes the computed fragment into f0..f7 (per-lane).

#ifdef __cplusplus
extern "C" {
#endif

// Runtime variant: K_END from a variable (a2).
// On return, frag_out receives the per-lane accumulator fragment f0..f7
// (WGMMA n-major layout: r = n*m_steps + m) written by the FSM.
static inline void vx_tgm(uint32_t desc_a, uint32_t desc_b, uint32_t k_tiles,
                          float* frag_out /* NRC floats, one per lane */) {
#ifdef __VORTEX__
  constexpr uint32_t INSN = 0x0B | (0u << 7) | (3u << 12) | (10u << 15) | (11u << 20) | (2u << 25);
  register float fd0 __asm__("f0");
  register float fd1 __asm__("f1");
  register float fd2 __asm__("f2");
  register float fd3 __asm__("f3");
  register float fd4 __asm__("f4");
  register float fd5 __asm__("f5");
  register float fd6 __asm__("f6");
  register float fd7 __asm__("f7");
  __asm__ volatile (
    "mv a0, %[da]\n"
    "mv a1, %[db]\n"
    "mv a2, %[ke]\n"
    ".word %[insn]\n"
    : "=f"(fd0), "=f"(fd1), "=f"(fd2), "=f"(fd3),
      "=f"(fd4), "=f"(fd5), "=f"(fd6), "=f"(fd7)
    : [da] "r" (desc_a), [db] "r" (desc_b),
      [ke] "r" (k_tiles & 0x7Fu),
      [insn] "i" (INSN)
    : "a0", "a1", "a2", "memory"
  );
  frag_out[0] = fd0;
  frag_out[1] = fd1;
  frag_out[2] = fd2;
  frag_out[3] = fd3;
  frag_out[4] = fd4;
  frag_out[5] = fd5;
  frag_out[6] = fd6;
  frag_out[7] = fd7;
#else
  (void)desc_a; (void)desc_b; (void)k_tiles;
  for (uint32_t i = 0; i < 8; ++i) frag_out[i] = 0;
#endif
}

static inline uint32_t vx_tgm_encode(uint32_t k_end) {
  return 0x0B | (0u << 7) | (3u << 12) | (10u << 15) | (11u << 20) | ((k_end & 0x7Fu) << 25);
}

#ifdef __cplusplus
}
#endif