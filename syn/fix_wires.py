#!/usr/bin/env python3
"""Convert wire declarations to reg where needed (inside always blocks)"""
import re

with open("/tmp/tfr_flat.sv") as f:
    lines = f.readlines()

output = []
in_module_ports = False
in_always = False

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Track module port regions
    if re.match(r"module\s+\w+", stripped):
        in_module_ports = True
    if in_module_ports and stripped == ");":
        in_module_ports = False
    
    # Track always blocks
    if re.match(r"always\s+@", stripped) or stripped.startswith("always @"):
        in_always = True
    if in_always and stripped == "end":
        in_always = False
    
    # In module ports, keep wire
    # Inside always blocks, convert wire to reg
    if in_always and not in_module_ports:
        if re.match(r"\s+wire\s+\[", stripped):
            line = line.replace("wire [", "reg [", 1)
        elif re.match(r"\s+wire\s+\w+;", stripped):
            line = line.replace("wire ", "reg ", 1)
    
    output.append(line)

with open("/tmp/tfr_flat.sv", "w") as f:
    f.writelines(output)

print(f"Fixed {len(output)} lines")
