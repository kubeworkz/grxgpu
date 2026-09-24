// Copyright © 2019-2023
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Graphics ABI header. Provides on-wire types and pixel helpers via
// <vx_gfx_abi.h> (host and device), plus device-side TEX/OM/RASTER
// intrinsics (gated on __VORTEX__).

#pragma once

#include <vx_gfx_abi.h>
#include <VX_types.h>

///////////////////////////////////////////////////////////////////////////////
// Kernel-only intrinsics for the fixed-function TEX / OM / RASTER units.
// Encodings (CUSTOM1 family):
//   funct3=2, R-type,  funct7=0     : vx_om4          (output-merger, windowed)
//   funct3=5, R-type,  funct7=...   : vx_tex4         (texture sample, windowed)
// RASTER has no kernel op in v2: the raster engine launches the fragment shader
// on-device (push); the payload is in the gfx window at warp launch.
// Trap as illegal-instruction unless VX_CFG_EXT_TEX_ENABLE /
// VX_CFG_EXT_OM_ENABLE / VX_CFG_EXT_RASTER_ENABLE is set.
///////////////////////////////////////////////////////////////////////////////

#ifdef __VORTEX__

#include <vx_intrinsics.h>
#include <vx_gfx_window.h>   // vx_gfx_set / vx_gfx_get* (SETW/GETW window primitives)

namespace vortex {
namespace graphics {

// Texture sample — canonical register form. u, v are S.23 fixed-point
// coordinates, lod the explicit mip level; all three ride registers and the
// texel is returned in rd. The TEX unit takes its operands in registers.
// `stage` is a compile-time constant. CUSTOM1 funct3=5, R4-type.
inline unsigned vx_tex(unsigned stage, unsigned u, unsigned v, unsigned lod) {
  unsigned texel;
  __asm__ volatile (".insn r4 %1, 5, %2, %0, %3, %4, %5"
      : "=r"(texel)
      : "i"(RISCV_CUSTOM1), "i"(stage), "r"(u), "r"(v), "r"(lod));
  return texel;
}

// Texture sample (single mode) — register-direct ABI. u, v are S.23 fixed-point
// coordinates carried in rs1/rs2; `lod` selects the explicit mip level and
// rides window slot 27 (stage it with vx_gfx_set before the sample). The texel
// is returned in rd (scoreboard sync handle) and mirrored into the window at
// `out_slot` for consumers that read it back with vx_gfx_get_after. `stage` and
// `out_slot` are compile-time constants (they ride funct7 =
// {out_slot[4:0], stage, mode=0}). CUSTOM1 funct3=5, R-type.
inline unsigned vx_tex4_single(unsigned stage, unsigned u, unsigned v, unsigned lod, unsigned out_slot) {
  vx_gfx_set(27, lod);
  unsigned texel;
  __asm__ volatile (".insn r %1, 5, %2, %0, %3, %4"
      : "=r"(texel)
      : "i"(RISCV_CUSTOM1), "i"((((out_slot) & 0x1f) << 2) | (((stage) & 1) << 1)), "r"(u), "r"(v));
  return texel;
}

// Texture sample on the shared graphics window, quad mode (hardware LOD). One
// thread owns a 2x2 quad: u[0..3] at window slots in_slot..in_slot+3, v[0..3] at
// in_slot+4..in_slot+7 (frags 0=(x,y) 1=(x+1,y) 2=(x,y+1) 3=(x+1,y+1)). rs1
// carries the texture dims {logh<<16 | logw}; the unit computes one integer mip
// LOD from the quad derivatives. The four texels land in the window at
// out_slot..out_slot+3 (read them with vx_gfx_get_after over that window); rd
// returns the scoreboard sync handle. stage and out_slot are compile-time
// constants (they ride funct7). CUSTOM1 funct3=5, R-type, funct7.mode=1.
inline unsigned vx_tex4_quad(unsigned stage, unsigned logw, unsigned logh,
                             unsigned in_slot, unsigned out_slot) {
  unsigned handle;
  unsigned dims = (logw & 0xffff) | (logh << 16);
  __asm__ volatile (".insn r %1, 5, %2, %0, %3, %4"
      : "=r"(handle)
      : "i"(RISCV_CUSTOM1), "i"((((out_slot) << 2) | ((stage) << 1) | 1u)), "r"(dims), "r"(in_slot));
  return handle;
}

// Output-merger submit on the shared graphics window (vx_om4 — the sole OM op).
// One thread owns a 2x2 quad: color[0..3] at window slots base..base+3, depth[0..3]
// at base+4..base+7 (stage them with vx_gfx_set first; frags 0=(x,y) 1=(x+1,y)
// 2=(x,y+1) 3=(x+1,y+1)). `desc` is the raster pos_mask (cov_mask[3:0], quad
// origin qx@[4 +: 14] / qy@[18 +: 13]) with `face` in bit 31. The unit submits
// each covered sub-pixel (pos_x=(qx<<1)|(F&1), pos_y=(qy<<1)|(F>>1)) to the OM
// core. Fire-and-forget (rd=x0). CUSTOM1 funct3=2, R-type.
inline void vx_om4(unsigned desc, unsigned base) {
  __asm__ volatile (".insn r %0, 2, 0, x0, %1, %2"
      :: "i"(RISCV_CUSTOM1), "r"(desc), "r"(base));
}

// ── fragment export: the aperture store ─────────────────────────────────────
//
// The shader exports a fragment by STORING to the OM aperture. There is no OM bus
// and no window staging: the cluster's OM steer peels the write off the L1->L2
// trunk and the OM ingress turns it back into a {pos, colour, depth, face}
// request for the unchanged VX_om_core.
//
// The aperture address is SHIFT-ONLY (the pitch is padded to a power of two), so
// the ingress decodes it by bit-slicing instead of dividing:
//     offset = ((((rt << 1) | face) << YBITS | y) << XBITS | x) << RECORD_SHIFT
// XBITS/YBITS/RECORD_SHIFT come from the OM DCRs; the runtime programs them and
// passes them to the kernel, so the shader just shifts and adds.
#define VX_OM_APERTURE_ADDR_RT(xbits, ybits, record_shift, x, y, face, rt)     \
  ((VX_MEM_OM_BASE_ADDR) +                                                     \
   (((((uint32_t)(rt) << 1 | (uint32_t)(face)) << ((xbits) + (ybits)))         \
     | ((uint32_t)(y) << (xbits))                                              \
     | (uint32_t)(x)) << (record_shift)))

// A shader with one colour attachment names none.
#define VX_OM_APERTURE_ADDR(xbits, ybits, record_shift, x, y, face) \
  VX_OM_APERTURE_ADDR_RT(xbits, ybits, record_shift, x, y, face, 0)

// vx_om_export — one fragment. CUSTOM1 funct3=3, R4-type, rd=x0 (posted).
// funct7[1:0] = {has_depth, has_colour}: a shader may emit colour only (the
// common case — early-Z owns the depth test AND the depth write), depth only
// (z-prepass / shadow map), or both (gl_FragDepth).
#define vx_om_export(addr, color, depth, mask)                     \
  __asm__ volatile (".insn r4 %0, 3, %1, x0, %2, %3, %4"           \
      :: "i"(RISCV_CUSTOM1), "i"(mask), "r"(addr), "r"(color), "r"(depth))

// The three record shapes.
#define vx_om_export_color(addr, color)        vx_om_export(addr, color, 0, 1)
#define vx_om_export_depth(addr, depth)        vx_om_export(addr, 0, depth, 2)
#define vx_om_export_both(addr, color, depth)  vx_om_export(addr, color, depth, 3)

// RASTER dispatch v2 is PUSH: the raster engine's work distributor launches the
// fragment shader once per covered-quad wave (no pull op). The per-lane payload
// is landed in this warp's launch registers at warp launch (zero LMEM/LSU
// traffic); the FS reads it back as the FRAG_* CSRs via the helpers below.
// There is no bcoord payload — the FS recomputes per-corner edge values from
// the primitive edges + its own pixel (quad group = 4 adjacent lanes, corner
// = lane & 3; see frag_payload_t in <vx_gfx_abi.h>).

// This lane's fragment payload (read back from the warp's launch registers).
#define vx_frag_pos()     ((uint32_t)csr_read(VX_CSR_FRAG_POS))
#define vx_frag_pid()     ((uint32_t)csr_read(VX_CSR_FRAG_PID))

// This lane's pixel, and whether the primitive actually covers it.
#define vx_frag_x(p)       VX_FRAG_POS_X((p).pos)
#define vx_frag_y(p)       VX_FRAG_POS_Y((p).pos)
#define vx_frag_covered(p) VX_FRAG_POS_COVERED((p).pos)

// Load this lane's fragment stamp {pos, pid} into `p`.
#define vx_frag_load(p) do { \
  (p).pos = vx_frag_pos();   \
  (p).pid = vx_frag_pid();   \
} while (0)

} // namespace graphics
} // namespace vortex

#endif // __VORTEX__
