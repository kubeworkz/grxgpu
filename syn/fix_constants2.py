#!/usr/bin/env python3
"""Add remaining missing constants to vx_gpu_pkg_stub.sv."""
import os
os.chdir("/tmp/dxa_synth")

with open("vx_gpu_pkg_stub.sv") as f:
    c = f.read()

extra = """
    localparam NC_WIDTH = (NC_BITS > 0) ? NC_BITS : 1;
    localparam NW_BITS = 2;
    localparam NW_WIDTH = (NW_BITS > 0) ? NW_BITS : 1;
    localparam NT_BITS = 1;
    localparam NT_WIDTH = (NT_BITS > 0) ? NT_BITS : 1;
    localparam HART_ID_BITS = NC_BITS + NW_BITS + NT_BITS;
    localparam NW_WIDTH_BYTES = 4;
    localparam NW_ADDR_WIDTH = 32;
    localparam NUM_SOCKETS = 1;
    localparam VX_CFG_MAX_BAR_EVENTS = 16;
    localparam BAR_SIZE_W = (NW_WIDTH > NC_WIDTH) ? NW_WIDTH : NC_WIDTH;
"""

c = c.replace("endpackage", extra + "endpackage")
with open("vx_gpu_pkg_stub.sv", "w") as f:
    f.write(c)
print("Added NC_WIDTH and core config constants")
