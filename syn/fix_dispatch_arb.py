#!/usr/bin/env python3
"""Fix remaining array interface port references."""
import re, os

os.chdir("/tmp/dxa_synth")

for fname in ["VX_dxa_dispatch.sv", "VX_dxa_req_arb.sv"]:
    if not os.path.exists(fname):
        continue
    with open(fname) as f:
        c = f.read()
    c = re.sub(r'req_in\[(\w+)\]_(\w+)', r'req_in_\2[\1]', c)
    c = re.sub(r'req_out\[(\w+)\]_(\w+)', r'req_out_\2[\1]', c)
    c = c.replace('bus_out_if_req_data;', 'bus_out_if_req_data,')
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname}")
