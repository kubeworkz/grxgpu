#!/usr/bin/env python3
"""Fix remaining syntax errors."""
import os
os.chdir("/tmp/dxa_synth")

# Fix VX_dxa_desc_table.sv: double comma
fname = "VX_dxa_desc_table.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    c = c.replace(',,', ',')
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname} double comma")

# Fix VX_dxa_setup.sv: STATIC_ASSERT macro
fname = "VX_dxa_setup.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    # Remove STATIC_ASSERT lines (they span multiple lines)
    lines = c.split('\n')
    new_lines = []
    skip = 0
    for line in lines:
        if skip > 0:
            skip -= 1
            continue
        if 'STATIC_ASSERT' in line:
            # Count parens to find end
            depth = 0
            for ch in line:
                if ch == '(': depth += 1
                elif ch == ')': depth -= 1
            if depth <= 0:
                continue  # single line
            else:
                skip = 1  # skip next line too
                continue
        new_lines.append(line)
    c = '\n'.join(new_lines)
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname} STATIC_ASSERT")

# Fix VX_dxa_completion.sv: port list ending with ; instead of );
fname = "VX_dxa_completion.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    # The port list ends with txbar_bus_if_ready; but should be txbar_bus_if_ready\n);
    c = c.replace('input  wire        txbar_bus_if_ready;', 'input  wire        txbar_bus_if_ready\n);')
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname} port list")
