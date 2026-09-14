#!/usr/bin/env python3
import os
os.chdir("/tmp/dxa_synth")

fname = "vx_gpu_pkg_stub.sv"
with open(fname) as f:
    c = f.read()

# Add MEM_ATTR_W before endpackage
c = c.replace("endpackage", "    localparam MEM_ATTR_WIDTH = 8;\n    localparam MEM_ATTR_W = MEM_ATTR_WIDTH;\nendpackage")

with open(fname, "w") as f:
    f.write(c)
print(f"Fixed {fname}")
