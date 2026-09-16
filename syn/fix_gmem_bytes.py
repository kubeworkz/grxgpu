#!/usr/bin/env python3
import os
os.chdir("/tmp/dxa_synth")

fname = "vx_gpu_pkg_stub.sv"
with open(fname) as f:
    c = f.read()

c = c.replace("endpackage", "    localparam GMEM_BYTES = VX_CFG_L1_LINE_SIZE;\nendpackage")

with open(fname, "w") as f:
    f.write(c)
print(f"Fixed {fname}")
