#!/usr/bin/env python3
"""Replace $bits() with hardcoded values."""
import os
os.chdir("/tmp/dxa_synth")

# VX_dxa_req_arb.sv: $bits(dxa_req_data_t) = 128 (4 x 32-bit words)
fname = "VX_dxa_req_arb.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    c = c.replace("$bits(dxa_req_data_t)", "128")
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname}")

# Also check for $bits in other files
for fname in ["VX_dxa_setup.sv", "VX_dxa_core.sv", "VX_dxa_worker.sv", "VX_dxa_smem_wr.sv", "VX_dxa_gmem_req.sv"]:
    if not os.path.exists(fname):
        continue
    with open(fname) as f:
        c = f.read()
    if "$bits" in c:
        # Replace $bits(dxa_req_data_t) with 128
        c = c.replace("$bits(dxa_req_data_t)", "128")
        with open(fname, 'w') as f:
            f.write(c)
        print(f"  Fixed {fname}")
