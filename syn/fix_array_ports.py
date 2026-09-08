#!/usr/bin/env python3
"""Fix array interface port references after flattening."""
import re, os

os.chdir("/tmp/dxa_synth")

for fname in ["VX_dxa_req_arb.sv", "VX_dxa_core.sv", "VX_dxa_unit.sv"]:
    if not os.path.exists(fname):
        continue
    with open(fname) as f:
        c = f.read()
    # Pattern: word[i]_word -> word_word[i]
    # e.g., bus_in_if[i]_req_valid -> bus_in_if_req_valid[i]
    c = re.sub(r'(\w+)\[(\w+)\]_(\w+)', r'\1_\3[\2]', c)
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname}")

# Also fix VX_dxa_unit.sv port list syntax
fname = "VX_dxa_unit.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    # Fix missing closing paren - find the pattern where a port list doesn't close properly
    # The issue is: output wire [127:0] dxa_req_bus_if_req_data; followed by more ports
    # This means the port list terminator ); is missing
    # Check if there's a ; where there should be ,
    # Look for the last port before the body
    c = re.sub(r'(\w+_data);(\s*\n\s*\w)', r'\1,\2', c)
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname} port list")
