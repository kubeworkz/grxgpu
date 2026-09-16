#!/usr/bin/env python3
"""Targeted patch for double-buffer TGM FSM — only touches stage-related code."""
import sys, re

h_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/tcu_unit.h"
cpp_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tcu_unit.cpp"

# Patch 1: Add stage_stride_bytes to TgmFsmState
with open(h_path, 'r') as f:
    h = f.read()
if 'stage_stride_bytes' not in h:
    h = h.replace(
        '  bool       has_prefetch = false;',
        '  uint32_t   stage_stride_bytes = 0;  // double-buffer stride in bytes\n  bool       has_prefetch = false;'
    )
    with open(h_path, 'w') as f: f.write(h)
    print("1. tcu_unit.h: added stage_stride_bytes")

# Patch 2: All changes in tcu_unit.cpp
with open(cpp_path, 'r') as f:
    cpp = f.read()

# 2a: Compute stage_stride_bytes in IDLE — use cfg (WMMA) to match main.cpp
old = "        if (fsm.k_end == 0) fsm.k_end = 1;  // minimum 1 K-tile"
new = """        if (fsm.k_end == 0) fsm.k_end = 1;  // minimum 1 K-tile
        // Double-buffer stage stride — must match main.cpp's wgmma_dbuf_stride_elems.
        // Use cfg (WMMA config) to match main.cpp, NOT wg_cfg (WGMMA config).
        {
          uint32_t elem_bytes = elem_bits(fsm.fmt_s) / 8;
          uint32_t cta_M = VX_CFG_NUM_WARPS * cfg::xtileM;
          uint32_t stage_elems = cta_M * cfg::tileK + cfg::tileK * cfg::xtileN;
          uint32_t stage_bytes = stage_elems * elem_bytes;
          const uint32_t sweep = VX_CFG_LMEM_NUM_BANKS * (VX_CFG_XLEN / 8);
          uint32_t shift = ((sweep / 2) % VX_CFG_MEM_BLOCK_SIZE == 0) ? sweep / 2 : 0;
          fsm.stage_stride_bytes = ((stage_bytes + sweep - 1) / sweep) * sweep + shift;
        }"""
if 'Double-buffer stage stride' not in cpp:
    cpp = cpp.replace(old, new, 1)
    print("2a. IDLE: compute stage_stride_bytes (using cfg)")

# 2b: Add stage offset to DXA smem_addr (A)
old_a = 'req.smem_addr = uint64_t(VX_MEM_LMEM_BASE_ADDR) + (fsm.a_desc & 0xFFFF) - slice_bytes;'
new_a = 'req.smem_addr = uint64_t(VX_MEM_LMEM_BASE_ADDR) + fsm.stage * fsm.stage_stride_bytes + (fsm.a_desc & 0xFFFF) - slice_bytes;'
n_a = cpp.count(old_a)
if n_a: cpp = cpp.replace(old_a, new_a); print(f"2b. A smem_addr: {n_a} patched")

# 2c: Add stage offset to DXA smem_addr_b (B)
old_b = 'req.smem_addr_b = uint64_t(VX_MEM_LMEM_BASE_ADDR) + (fsm.b_desc & 0xFFFF);'
new_b = 'req.smem_addr_b = uint64_t(VX_MEM_LMEM_BASE_ADDR) + fsm.stage * fsm.stage_stride_bytes + (fsm.b_desc & 0xFFFF);'
n_b = cpp.count(old_b)
if n_b: cpp = cpp.replace(old_b, new_b); print(f"2c. B smem_addr_b: {n_b} patched")

# 2d: Add stage offset to COMPUTE setup uop descriptors
old_setup = """            this->wgmma(fsm.wid, tpuArgs.fmt_s, tpuArgs.fmt_d, 0, 0, 0,
                        fsm.a_desc, fsm.b_desc, rd_data, rd_data, rd_data,
                        rd_data, false, tpuArgs.cd_nregs, tpuArgs.is_a_smem, 1);"""
new_setup = """            {
              uint32_t so = fsm.stage * fsm.stage_stride_bytes;
              uint32_t sa = (fsm.a_desc & 0xFFFF0000) | ((fsm.a_desc & 0xFFFF) + so);
              uint32_t sb = (fsm.b_desc & 0xFFFF0000) | ((fsm.b_desc & 0xFFFF) + so);
              this->wgmma(fsm.wid, tpuArgs.fmt_s, tpuArgs.fmt_d, 0, 0, 0,
                          sa, sb, rd_data, rd_data, rd_data,
                          rd_data, false, tpuArgs.cd_nregs, tpuArgs.is_a_smem, 1);
            }"""
if 'uint32_t so = fsm.stage' not in cpp and old_setup in cpp:
    cpp = cpp.replace(old_setup, new_setup, 1)
    print("2d. COMPUTE setup uop: staged descriptors")

with open(cpp_path, 'w') as f: f.write(cpp)
print("\nDone — only stage-related code modified.")
