#!/usr/bin/env python3
"""
Hoist generate-scoped wire declarations to module scope.
For each 'for (genvar ... begin : label' block, collect wire declarations,
remove them from the block, and add array declarations at module scope.
"""
import re, sys

with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()

lines = content.split('\n')

# Find generate blocks and collect their wire declarations
# We need to track nesting depth
gen_stack = []  # [(start_line, label, depth)]
gen_blocks = []  # [(start_line, end_line, label)]
wire_decls_by_label = {}  # label -> [(width_str, name)]

i = 0
while i < len(lines):
    s = lines[i].strip()
    
    # Match generate block start
    m = re.match(r'for\s*\(\s*genvar\s+\w+\s*=.*begin\s*:\s*(\w+)', s)
    if m:
        gen_stack.append((i, m.group(1), len(gen_stack)))
    
    # Match wire declarations inside generate blocks
    if gen_stack:
        m = re.match(r'\s*wire\s+(\[[^\]]+(?:\]\[[^\]]+)*\])\s+([\w,\s]+);', lines[i])
        if m:
            label = gen_stack[-1][1]
            width = m.group(1)
            names = [n.strip() for n in m.group(2).split(',') if n.strip()]
            if label not in wire_decls_by_label:
                wire_decls_by_label[label] = []
            for name in names:
                wire_decls_by_label[label].append((width, name, i))
    
    # Match 'end' to close generate blocks
    if s == 'end' and gen_stack:
        start, label, depth = gen_stack.pop()
        if depth == 0 or not gen_stack:
            gen_blocks.append((start, i, label))

# Hoist wire declarations
lines_to_remove = set()
for label, decls in wire_decls_by_label.items():
    # Find the generate block
    for start, end, lbl in gen_blocks:
        if lbl == label:
            # Remove wire declarations from generate block
            for width, name, line_idx in decls:
                lines_to_remove.add(line_idx)
            
            # Find insertion point (before the generate block)
            insert_idx = start
            indent = '    '
            
            # Add array declarations before the generate block
            for width, name, _ in decls:
                lines.insert(insert_idx, f'{indent}wire {width} {name} [{label.upper()}_SIZE];')
                insert_idx += 1
            
            break

# Remove original wire declarations
new_lines = [lines[i] for i in range(len(lines)) if i not in lines_to_remove]
content = '\n'.join(new_lines)

# Clean up multiple blank lines
content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)

print(f'Found {len(gen_blocks)} generate blocks')
print(f'Hoisted wires from {len(wire_decls_by_label)} blocks')
print(f'Lines: {len(content.splitlines())}')
