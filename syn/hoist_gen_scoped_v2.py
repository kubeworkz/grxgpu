#!/usr/bin/env python3
"""
Hoist generate-scoped wire declarations to module scope.
For each generate block, collect wire declarations inside it,
remove them from the generate block, and add them as array declarations
at module scope (before the first generate block).

Also fix hierarchical references like g_lane[0].a_man -> a_man.
"""
import re, sys

with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()

# Strategy: for each module, find all generate blocks, collect their wire
# declarations, hoist them as arrays, and fix references.

# Step 1: Find all generate blocks and their wire declarations
# Pattern: for (genvar ...) begin : label ... end
# We need to track nesting

lines = content.split('\n')

# Find all generate blocks with their labels and nesting
gen_blocks = []  # (start_line, end_line, label, indent)
stack = []
for i, line in enumerate(lines):
    s = line.strip()
    m = re.match(r'for\s*\(\s*genvar\s+\w+\s*=.*begin\s*:\s*(\w+)', s)
    if m:
        label = m.group(1)
        indent = len(line) - len(line.lstrip())
        stack.append((i, label, indent))
    if s == 'end' and stack:
        start, label, indent = stack.pop()
        gen_blocks.append((start, i, label, indent))

print(f'Found {len(gen_blocks)} generate blocks')

# Step 2: For each generate block, collect wire declarations
hoisted = []  # (label, declaration_lines)
for start, end, label, indent in gen_blocks:
    decls = []
    for i in range(start + 1, end):
        s = lines[i].strip()
        # Match wire declarations: wire [W:0] name, wire [W:0] name1, name2;
        m = re.match(r'wire\s+(\[[^\]]+(?:\]\[[^\]]+)*\])\s+([\w,\s]+);', s)
        if m:
            width = m.group(1)
            names_str = m.group(2)
            names = [n.strip() for n in names_str.split(',') if n.strip()]
            for name in names:
                decls.append((width, name, lines[i][:len(lines[i]) - len(lines[i].lstrip())]))
    
    if decls:
        hoisted.append((label, decls))
        # Remove the declarations from the generate block
        for i in range(start + 1, end):
            s = lines[i].strip()
            m = re.match(r'wire\s+\[[^\]]+(?:\]\[[^\]]+)*\]\s+[\w,\s]+;', s)
            if m:
                lines[i] = ''  # Remove the line

# Step 3: Insert hoisted declarations as arrays at module scope
# Find insertion points (after localparam declarations, before first generate)
for label, decls in hoisted:
    # Find the generate block's start line to insert before it
    for start, end, lbl, indent in gen_blocks:
        if lbl == label:
            # Insert before this generate block
            insert_indent = '    '
            for width, name, orig_indent in decls:
                insert_line = f'{insert_indent}wire {width} {name} [{label.upper()}_SIZE];'
                lines.insert(start, insert_line)
                # Adjust indices
                start += 1
                end += 1
            break

# Step 4: Fix hierarchical references
# g_lane[0].a_man -> a_man[g_lane_IDX]
# Actually, we need to replace g_label[expr].var with var[expr] for arrays
# This is complex. Let me use a simpler approach:
# Replace g_label[anything].name with name[g_label_anything_idx]
# But the index depends on the genvar...

# Actually, the simplest approach: since Yosys elaborates generate blocks,
# the arrays will be indexed by the same genvar. So:
# g_lane_mxfp4[i].a_man -> a_man[i] (where a_man is now an array)

# Let me find and replace all hierarchical references
for label, decls in hoisted:
    for width, name, orig_indent in decls:
        # Replace g_label[expr].name with name[expr]
        # The genvar is typically 'i' or the loop variable
        # Find the genvar from the for loop
        for start, end, lbl, indent in gen_blocks:
            if lbl == label:
                m = re.match(r'for\s*\(\s*genvar\s+(\w+)', lines[start].strip())
                if m:
                    genvar = m.group(1)
                    # Replace all references
                    pattern = re.compile(rf'{label}\[([^\]]+)\]\.{name}\b')
                    content_new = pattern.sub(rf'{name}[\1]', '\n'.join(lines))
                    lines = content_new.split('\n')
                break

content = '\n'.join(lines)

# Remove empty lines that were left by removal
content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)

print(f'Hoisted {sum(len(d) for _, d in hoisted)} declarations from {len(hoisted)} generate blocks')
print(f'Lines: {len(content.splitlines())}')
