#!/usr/bin/env python3
"""
Hoist generate-scoped wire declarations to module scope.
Yosys can't handle hierarchical references like g_lane[0].a_man.
"""
import re, sys

with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()

lines = content.split('\n')
out = []
gen_depth = 0
gen_wire_decls = []  # (indent, declaration)
pending_gen_wires = []  # wires to hoist after current generate block

i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    # Track generate block depth
    if re.match(r'\s*for\s*\(\s*genvar', stripped):
        gen_depth += 1
    if re.match(r'\s*end\b', stripped) and gen_depth > 0:
        # Check if this ends a generate block
        # Simple heuristic: look back for matching 'begin :'
        gen_depth = max(0, gen_depth - 1)
    
    # If we're inside a generate block, collect wire declarations to hoist
    if gen_depth > 0:
        # Match wire declarations inside generate blocks
        m = re.match(r'(\s*)(wire\s+\[[^\]]+\]\s+\w+(?:\s*,\s*\w+)*)\s*;', stripped)
        if m:
            indent = line[:len(line) - len(line.lstrip())]
            decl = m.group(2)
            # Parse comma-separated names
            # e.g., "wire [3:0][1:0] a_man, b_man" -> two declarations
            # Actually, just collect the full declaration line
            pending_gen_wires.append((indent, decl))
            # Replace with empty (we'll add hoisted versions)
            i += 1
            continue
        
        # Also match "wire [W:0] name;" style
        m = re.match(r'(\s*)(wire\s+\S+\s+\w+)\s*;', stripped)
        if m:
            indent = line[:len(line) - len(line.lstrip())]
            decl = m.group(2)
            pending_gen_wires.append((indent, decl))
            i += 1
            continue
    
    # When we exit a generate block, insert hoisted declarations
    if gen_depth == 0 and pending_gen_wires:
        # Find the last localparam/wire declaration before the generate block
        # and insert after it
        hoisted = []
        seen_decls = set()
        for indent, decl in pending_gen_wires:
            # Extract variable names
            names = re.findall(r'\b(\w+)\b', decl.split(']')[-1] if ']' in decl else decl)
            for name in names:
                if name not in seen_decls:
                    seen_decls.add(name)
                    # Get the full width/type from the declaration
                    type_match = re.match(r'(wire\s+\[[^\]]+\])', decl)
                    if type_match:
                        hoisted.append(f'{indent}{type_match.group(1)} {name};')
                    else:
                        hoisted.append(f'{indent}{decl};')
        
        # Insert hoisted declarations - find a good insertion point
        # Look for the last 'endmodule' or the first 'end' of a generate
        insert_idx = len(out)
        for j in range(len(out) - 1, max(0, len(out) - 50), -1):
            if 'endmodule' in out[j]:
                insert_idx = j
                break
            if out[j].strip().startswith('// ----'):
                insert_idx = j
                break
        
        for h in reversed(hoisted):
            out.insert(insert_idx, h)
        
        pending_gen_wires = []
    
    out.append(line)
    i += 1

# Handle any remaining hoisted wires at the end
if pending_gen_wires:
    for indent, decl in pending_gen_wires:
        names = re.findall(r'\b(\w+)\b', decl.split(']')[-1] if ']' in decl else decl)
        for name in names:
            type_match = re.match(r'(wire\s+\[[^\]]+\])', decl)
            if type_match:
                out.append(f'{indent}{type_match.group(1)} {name};')

content = '\n'.join(out)

with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)

print(f'Lines: {len(content.splitlines())}')
