// Copyright (c) 2024 grxgpu
// Tensor GEMM range intrinsic (Phase 2: self-pipelining tensor FSM).
// Issues a single TGM instruction that triggers the hardware FSM to manage
// DXA prefetch, barrier release, double-buffer rotation, and WGMMA compute
// internally — zero per-iteration instructions.

#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern C {
#endif

// Issue a Tensor GEMM range instruction.
// The hardware FSM executes K/tileK WGMMA iterations internally.
//
// Encoding (R-type, CUSTOM2 opcode 0x0B, funct3=3):
//   rd  = accumulator fragment register (destination, in-place)
//   rs1 = A tile descriptor register (smem address + layout)
//   rs2 = B tile descriptor register (smem address + layout)
//   rs3 = K range register: K_start[31:16] | K_end[15:0]
//   funct7[4:0]   = fmt_s (source format, e.g. fp16=9)
//   funct7[9:5]   = fmt_d (dest format, e.g. fp32=1)
//   funct7[11:10] = cd_nregs (0=8, 1=16, 2=32 C/D registers)
//   funct7[12]    = is_a_smem (1=A from shared memory)
//
// Parameters:
//   rd       = pointer to accumulator fragment (modified in-place)
//   desc_a   = A tile descriptor (smem address | layout encoding)
//   desc_b   = B tile descriptor (smem address | layout encoding)
//   k_start  = first K-tile index (inclusive, 0-based)
//   k_end    = last K-tile index (exclusive)
//   fmt_s    = source format ID (e.g. 9 for fp16)
//   fmt_d    = dest format ID (e.g. 1 for fp32)
//   cd_nregs = 0, 1, or 2 (for 8, 16, or 32 C/D registers)
//   is_a_smem = 1 if A is in shared memory, 0 if in registers
static inline void vx_tgm(void* rd, uint32_t desc_a, uint32_t desc_b,
                           uint32_t k_start, uint32_t k_end,
                           uint32_t fmt_s, uint32_t fmt_d,
                           uint32_t cd_nregs, uint32_t is_a_smem) {
#ifdef __VORTEX__
  uint32_t k_range = (k_start << 16) | (k_end & 0xFFFF);
  uint32_t funct7 = (fmt_s & 0x1f)
                   | ((fmt_d & 0x1f) << 5)
                   | ((cd_nregs & 0x3) << 10)
                   | ((is_a_smem & 0x1) << 12);
  uint32_t enc;
  __asm__ volatile (
    // rd=rd, rs1=desc_a, rs2=desc_b, rs3=k_range
    // opcode=0x0B (CUSTOM2), funct3=3 (TGM), funct7=funct7
    mv a0, %[desc_a]n
    mv a1, %[desc_b]n
    mv a2, %[k_range]n
    .insn r 0x0B, 3, %[funct7], 0, a0, a1n
    // Note: this is a simplified encoding. The real encoding needs rs3.
    // For SimX, the instruction is decoded from the raw bits.
    : [enc] =r (enc)
    : [desc_a] r (desc_a), [desc_b] r (desc_b),
      [k_range] r (k_range), [funct7] i (funct7)
    : a0, a1, a2, memory
  );
  (void)rd;
#else
  (void)rd; (void)desc_a; (void)desc_b;
  (void)k_start; (void)k_end;
  (void)fmt_s; (void)fmt_d; (void)cd_nregs; (void)is_a_smem;
#endif
}

#ifdef __cplusplus
}
#endif
