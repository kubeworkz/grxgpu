#!/usr/bin/env python3
"""Add ALL missing constants from VX_gpu_pkg to the stub."""
import os
os.chdir("/tmp/dxa_synth")

with open("vx_gpu_pkg_stub.sv") as f:
    content = f.read()

# Find where to insert (before endpackage)
# Remove old missing block and replace with comprehensive one
old_missing_start = content.find("\n    // DXA constants from VX_gpu_pkg.sv")
if old_missing_start >= 0:
    endpackage_idx = content.find("endpackage", old_missing_start)
    content = content[:old_missing_start] + "\nendpackage" + content[endpackage_idx + len("endpackage"):]

# Now add ALL needed constants
constants = """
    // Constants needed by DXA modules (from VX_gpu_pkg.sv)
    localparam BAR_ADDR_BITS = 8;
    localparam BAR_ADDR_W = (BAR_ADDR_BITS > 0) ? BAR_ADDR_BITS : 1;
    localparam DXA_LMEM_ENGINE_TAG_W = 8;
    localparam NC_BITS = 1;
    localparam DXA_LMEM_ATTR_W = (BAR_ADDR_W + 1);
    localparam DXA_LMEM_TAG_W = DXA_LMEM_ENGINE_TAG_W + NC_BITS;
    localparam DXA_LMEM_OUT_TAG_W = DXA_LMEM_TAG_W + 1;
    localparam TCU_LMEM_ATTR_W = 1;
    localparam TCU_LMEM_BLK_TAG_W = UUID_WIDTH + 1;
    localparam TCU_LMEM_NUM_MASTERS = 2;
    localparam TCU_LMEM_TAG_W = TCU_LMEM_BLK_TAG_W + 1;
    localparam LMEM_DMA_ADDR_WIDTH = 12;
    localparam LMEM_DMA_ATTR_W = (DXA_LMEM_ATTR_W > TCU_LMEM_ATTR_W) ? DXA_LMEM_ATTR_W : TCU_LMEM_ATTR_W;
    localparam LMEM_DMA_TAG_W = (DXA_LMEM_TAG_W > TCU_LMEM_TAG_W) ? DXA_LMEM_TAG_W : TCU_LMEM_TAG_W;
    localparam LMEM_DMA_IN_TAG_MAX = (DXA_LMEM_OUT_TAG_W > TCU_LMEM_TAG_W) ? DXA_LMEM_OUT_TAG_W : TCU_LMEM_TAG_W;
    
    // L1/L2 memory arbiter tag widths
    localparam ICACHE_MEM_TAG_WIDTH = 8;
    localparam DCACHE_MEM_TAG_WIDTH = 8;
    localparam L1_MEM_TAG_WIDTH = (ICACHE_MEM_TAG_WIDTH > DCACHE_MEM_TAG_WIDTH) ? ICACHE_MEM_TAG_WIDTH : DCACHE_MEM_TAG_WIDTH;
    localparam L1_MEM_ARB_TAG_WIDTH = (L1_MEM_TAG_WIDTH + 1);
    localparam DXA_L2_ARB_TAG_BITS = 1;
    localparam L2_TAG_WIDTH = L1_MEM_ARB_TAG_WIDTH + DXA_L2_ARB_TAG_BITS;
    
    // LSU word size
    localparam LSU_WORD_SIZE = 4;
"""

content = content.replace("endpackage", constants + "\nendpackage")
with open("vx_gpu_pkg_stub.sv", "w") as f:
    f.write(content)
print("Added comprehensive constants to vx_gpu_pkg_stub.sv")
