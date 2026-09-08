#!/usr/bin/env python3
"""Add missing DXA constants to vx_gpu_pkg_stub.sv."""
import os
os.chdir("/tmp/dxa_synth")

with open("vx_gpu_pkg_stub.sv") as f:
    content = f.read()

# Add missing constants before endpackage
missing = """
    // DXA constants from VX_gpu_pkg.sv
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
"""

content = content.replace("endpackage", missing + "\nendpackage")
with open("vx_gpu_pkg_stub.sv", "w") as f:
    f.write(content)
print("Added DXA constants to vx_gpu_pkg_stub.sv")
