#!/usr/bin/env python3
"""Fix only interface array port references."""
import re, os

os.chdir("/tmp/dxa_synth")

# Fix VX_dxa_req_arb.sv: bus_in_if[i]_req_valid -> bus_in_if_req_valid[i]
# and bus_out_if[i]_req_valid -> bus_out_if_req_valid[i]
fname = "VX_dxa_req_arb.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    # Only fix bus_in_if[i]_* and bus_out_if[i]_* patterns
    c = re.sub(r'bus_in_if\[(\w+)\]_(\w+)', r'bus_in_if_\2[\1]', c)
    c = re.sub(r'bus_out_if\[(\w+)\]_(\w+)', r'bus_out_if_\2[\1]', c)
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname}")

# Fix VX_dxa_core.sv: req_bus_if[i]_req_valid -> req_bus_if_req_valid[i]
fname = "VX_dxa_core.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    c = re.sub(r'req_bus_if\[(\w+)\]_(\w+)', r'req_bus_if_\2[\1]', c)
    c = re.sub(r'gmem_bus_if\[(\w+)\]_(\w+)', r'gmem_bus_if_\2[\1]', c)
    c = re.sub(r'smem_bus_if\[(\w+)\]_(\w+)', r'smem_bus_if_\2[\1]', c)
    c = re.sub(r'worker_req_if\[(\w+)\]_(\w+)', r'worker_req_if_\2[\1]', c)
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname}")

# Fix VX_dxa_unit.sv port list: the port list ends with ; instead of ,
# Only fix the specific port that has ; where it should be ,
fname = "VX_dxa_unit.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    # The port list has output wire [127:0] dxa_req_bus_if_req_data;
    # followed by UNUSED_SPARAM - this needs to be a comma
    c = c.replace(
        'output wire [127:0] dxa_req_bus_if_req_data;',
        'output wire [127:0] dxa_req_bus_if_req_data,'
    )
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname} port list")
