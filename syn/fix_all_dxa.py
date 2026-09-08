#!/usr/bin/env python3
"""One-shot fix for all DXA synthesis issues."""
import re, os

os.chdir("/tmp/dxa_synth")

# 1. Strip RUNTIME_ASSERT multi-line blocks
files_to_strip = ["VX_dxa_watchdog.sv", "VX_dxa_setup.sv", "VX_dxa_completion.sv"]
for fname in files_to_strip:
    if not os.path.exists(fname):
        continue
    with open(fname) as f:
        lines = f.readlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '`RUNTIME_ASSERT' in line:
            # Count parens to find end of the block
            depth = 0
            j = i
            while j < len(lines):
                for c in lines[j]:
                    if c == '(': depth += 1
                    elif c == ')': depth -= 1
                if depth <= 0 and j > i:
                    break
                if depth <= 0 and j == i:
                    break
                j += 1
            i = j + 1
            continue
        # Skip orphaned RUNTIME_ASSERT arguments
        stripped = line.strip()
        if stripped.startswith('"') and ('%s' in stripped or '%t' in stripped or '%0d' in stripped or '%0h' in stripped):
            j = i
            depth = 0
            while j < len(lines):
                for c in lines[j]:
                    if c == '(': depth += 1
                    elif c == ')': depth -= 1
                if '))' in lines[j] or (depth <= 0 and j > i):
                    break
                j += 1
            i = j + 1
            continue
        if stripped.startswith('("') or stripped.startswith('('):
            depth = 0
            for c in stripped:
                if c == '(': depth += 1
                elif c == ')': depth -= 1
            if '))' in stripped or depth <= 0:
                i += 1
                continue
            else:
                j = i
                while j < len(lines):
                    for c in lines[j]:
                        if c == '(': depth += 1
                        elif c == ')': depth -= 1
                    if '))' in lines[j]:
                        break
                    j += 1
                i = j + 1
                continue
        new_lines.append(line)
        i += 1
    with open(fname, 'w') as f:
        f.writelines(new_lines)
    print(f"  Stripped RUNTIME_ASSERT from {fname}")

# 2. Fix $countones -> $popcount
for fname in ["VX_dxa_setup.sv"]:
    if os.path.exists(fname):
        with open(fname) as f:
            c = f.read()
        c = c.replace('$countones', '$popcount')
        with open(fname, 'w') as f:
            f.write(c)

# 3. Fix part-selects (+:) -> explicit bit slicing
def fix_part_selects(content):
    """Replace [base +: width] with [base+width-1:base]"""
    result = []
    i = 0
    while i < len(content):
        m = re.match(r'(\w+(?:\.\w+)*)\[', content[i:])
        if m:
            signal = m.group(1)
            bracket_start = i + m.end()
            depth = 1
            j = bracket_start
            found_op = None
            op_pos = -1
            while j < len(content) and depth > 0:
                if content[j] == '[': depth += 1
                elif content[j] == ']': depth -= 1
                elif depth == 1:
                    if content[j:j+2] == '+:':
                        found_op = '+'; op_pos = j; j += 1; break
                    elif content[j:j+2] == '-:':
                        found_op = '-'; op_pos = j; j += 1; break
                j += 1
            if found_op and j < len(content):
                while j < len(content) and content[j] != ']': j += 1
                if j < len(content):
                    base = content[bracket_start:op_pos].strip()
                    width = content[op_pos+2:j].strip()
                    if found_op == '+':
                        replacement = f"{signal}[({base})+({width})-1:({base})]"
                    else:
                        replacement = f"{signal}[({base})-({width})+1:({base})]"
                    result.append(replacement)
                    i = j + 1
                    continue
        result.append(content[i])
        i += 1
    return ''.join(result)

for fname in ["VX_dxa_setup.sv", "VX_dxa_smem_wr.sv", "VX_dxa_core.sv", "VX_dxa_worker.sv", "VX_dxa_gmem_req.sv"]:
    if not os.path.exists(fname):
        continue
    with open(fname) as f:
        c = f.read()
    new_c = fix_part_selects(c)
    if new_c != c:
        with open(fname, 'w') as f:
            f.write(new_c)
        print(f"  Fixed part-selects in {fname}")

# 4. Fix double commas in port lists
for fname in ["VX_dxa_gmem_req.sv", "VX_dxa_smem_wr.sv", "VX_dxa_worker.sv", "VX_dxa_core.sv"]:
    if not os.path.exists(fname):
        continue
    with open(fname) as f:
        c = f.read()
    c = c.replace(',,', ',')
    with open(fname, 'w') as f:
        f.write(c)

# 5. Fix completion port list (txbar_bus_if_ready; -> txbar_bus_if_ready\n);)
fname = "VX_dxa_completion.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    c = c.replace('input  wire        txbar_bus_if_ready;', 'input  wire        txbar_bus_if_ready\n);')
    with open(fname, 'w') as f:
        f.write(c)

print("All fixes applied")
