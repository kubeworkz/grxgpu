#!/usr/bin/env python3
import os
os.chdir("/tmp/dxa_synth")

fname = "VX_dxa_core.sv"
with open(fname) as f:
    c = f.read()

# Fix dispatch instantiation: .req_in(dispatch_in_if) -> flat wire connections
c = c.replace('.req_in    (dispatch_in_if),',
              '.req_in_valid(dispatch_in_if_req_valid),\n        .req_in_req_data(dispatch_in_if_req_data),\n        .req_in_desc_data(dispatch_in_if_desc_data),\n        .req_in_ready(dispatch_in_if_req_ready),')

# Fix dispatch instantiation: .req_out(worker_req_if) -> flat wire connections
c = c.replace('.req_out   (worker_req_if)',
              '.req_out_valid(worker_req_if_req_valid),\n        .req_out_req_data(worker_req_if_req_data),\n        .req_out_desc_data(worker_req_if_desc_data),\n        .req_out_ready(worker_req_if_req_ready)')

with open(fname, "w") as f:
    f.write(c)
print(f"Fixed {fname} dispatch instantiation")
