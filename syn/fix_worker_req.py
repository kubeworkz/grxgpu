#!/usr/bin/env python3
import os
os.chdir("/tmp/dxa_synth")
with open("VX_dxa_core.sv") as f:
    c = f.read()
c = c.replace(".req_valid(worker_req_if_req_valid[i])", ".req_if_valid(worker_req_if_req_valid[i])")
c = c.replace(".req_ready(worker_req_if_req_ready[i])", ".req_if_ready(worker_req_if_req_ready[i])")
with open("VX_dxa_core.sv", "w") as f:
    f.write(c)
print("Fixed worker req ports")
