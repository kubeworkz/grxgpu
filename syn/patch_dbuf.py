#!/usr/bin/env python3
"""Patch the TGM FSM to add double-buffer smem stage offsets."""
import re, sys

# Patch 1: Add stage_stride_bytes to TgmFsmState in tcu_unit.h
h_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/tcu_unit.h"
with open(h_path, 'r') as f:
    h = f.read()

if 'stage_stride_bytes' not in h:
    h = h.replace(
        '  bool       has_prefetch = false;',
        '  uint32_t   stage_stride_bytes = 0;  // double-buffer stride in bytes\n  bool       has_prefetch = false;'
    )
    with open(h_path, 'w') as f:
        f.write(h)
    print("patched tcu_unit.h: added stage_stride_bytes")
else:
    print("tcu_unit.h already patched")

# Patch 2: All changes in tcu_unit.cpp
cpp_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tcu_unit.cpp"
with open(cpp_path, 'r') as f:
    cpp = f.read()

changes = 0

# 2a: Compute stage_stride_bytes in IDLE phase
old_idle = "        if (fsm.k_end == 0) fsm.k_end = 1;  // minimum 1 K-tile"
new_idle = """        if (fsm.k_end == 0) fsm.k_end = 1;  // minimum 1 K-tile
        // Compute double-buffer stage stride matching wgmma_dbuf_stride_elems in common.h.
        {
          uint32_t e_bits = elem_bits(fsm.fmt_s);
          uint32_t elem_bytes = e_bits / 8;
          uint32_t cta_M = VX_CFG_NUM_WARPS * wg_cfg::xtileM;
          uint32_t stage_elems = cta_M * wg_cfg::tileK + wg_cfg::tileK * wg_cfg::xtileN;
          uint32_t stage_bytes = stage_elems * elem_bytes;
          const uint32_t sweep_bytes = VX_CFG_LMEM_NUM_BANKS * (VX_CFG_XLEN / 8);
          const uint32_t half_bytes = sweep_bytes / 2;
          uint32_t shift = ((half_bytes % VX_CFG_MEM_BLOCK_SIZE) == 0) ? half_bytes : 0;
          fsm.stage_stride_bytes = ((stage_bytes + sweep_bytes - 1) / sweep_bytes) * sweep_bytes + shift;
        }"""
if 'stage_elems = cta_M' not in cpp:
    cpp = cpp.replace(old_idle, new_idle, 1)
    changes += 1
    print("  + IDLE: compute stage_stride_bytes")

# 2b: Add stage offset to DXA smem_addr (A) - appears in FETCH and ADVANCE
old_a = 'req.smem_addr = uint64_t(VX_MEM_LMEM_BASE_ADDR) + (fsm.a_desc & 0xFFFF) - slice_bytes;'
new_a = 'req.smem_addr = uint64_t(VX_MEM_LMEM_BASE_ADDR) + fsm.stage * fsm.stage_stride_bytes + (fsm.a_desc & 0xFFFF) - slice_bytes;'
count_a = cpp.count(old_a)
if count_a > 0:
    cpp = cpp.replace(old_a, new_a)
    changes += count_a
    print(f"  + A smem_addr: {count_a} occurrences patched")

# 2c: Add stage offset to DXA smem_addr_b (B) - appears in FETCH and ADVANCE
old_b = 'req.smem_addr_b = uint64_t(VX_MEM_LMEM_BASE_ADDR) + (fsm.b_desc & 0xFFFF);'
new_b = 'req.smem_addr_b = uint64_t(VX_MEM_LMEM_BASE_ADDR) + fsm.stage * fsm.stage_stride_bytes + (fsm.b_desc & 0xFFFF);'
count_b = cpp.count(old_b)
if count_b > 0:
    cpp = cpp.replace(old_b, new_b)
    changes += count_b
    print(f"  + B smem_addr_b: {count_b} occurrences patched")

# 2d: Add stage offset to lmem_desc_ in the COMPUTE setup uop
# The setup uop calls wgmma with fsm.a_desc and fsm.b_desc.
# Inside wgmma, lmem_desc_[wid][0] = {LMEM_BASE + (a_desc & 0xFFFF), ...}
# We need to add stage offset to the descriptor before passing to wgmma.
# Replace the setup uop call to use staged descriptors.
old_setup = """            this->wgmma(fsm.wid, tpuArgs.fmt_s, tpuArgs.fmt_d, 0, 0, 0,
                        fsm.a_desc, fsm.b_desc, rd_data, rd_data, rd_data,
                        rd_data, false, tpuArgs.cd_nregs, tpuArgs.is_a_smem, 1);"""
new_setup = """            // Stage-offset descriptors so lmem_desc_ reads from the current buffer.
            {
              uint32_t so = fsm.stage * fsm.stage_stride_bytes;
              uint32_t sa = (fsm.a_desc & 0xFFFF0000) | ((fsm.a_desc & 0xFFFF) + so);
              uint32_t sb = (fsm.b_desc & 0xFFFF0000) | ((fsm.b_desc & 0xFFFF) + so);
              this->wgmma(fsm.wid, tpuArgs.fmt_s, tpuArgs.fmt_d, 0, 0, 0,
                          sa, sb, rd_data, rd_data, rd_data,
                          rd_data, false, tpuArgs.cd_nregs, tpuArgs.is_a_smem, 1);
            }"""
if 'Stage-offset descriptors' not in cpp and old_setup in cpp:
    cpp = cpp.replace(old_setup, new_setup, 1)
    changes += 1
    print("  + COMPUTE setup uop: staged descriptors")

with open(cpp_path, 'w') as f:
    f.write(cpp)
print(f"\nTotal: {changes} patches applied")
