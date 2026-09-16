#!/usr/bin/env python3
"""Fix synth_alu_int.sv: move assigns inside module, remove import, strip STRING."""
import re

with open('/tmp/synth_alu_int.sv') as f:
    src = f.read()

# Remove import
src = src.replace('module VX_alu_int import VX_gpu_pkg::*;', 'module VX_alu_int')

# Remove `STRING parameter
src = re.sub(r'parameter `STRING INSTANCE_ID.*?,\n', '', src)

# Remove standalone assign lines
src = re.sub(r'^assign res_wb = 1;\n', '', src, flags=re.MULTILINE)
src = re.sub(r'^assign res_eop = 1;\n', '', src, flags=re.MULTILINE)

# Find module declaration end and insert assigns
lines = src.split('\n')
in_module = False
insert_idx = 0
for i, line in enumerate(lines):
    s = line.strip()
    if s.startswith('module VX_alu_int'):
        in_module = True
    if in_module and s == ');':
        insert_idx = i + 1
        break

lines.insert(insert_idx, '')
lines.insert(insert_idx + 1, '    assign res_wb = 1;')
lines.insert(insert_idx + 2, '    assign res_eop = 1;')

with open('/tmp/synth_alu_int.sv', 'w') as f:
    f.write('\n'.join(lines))

print('Fixed synth_alu_int.sv')
