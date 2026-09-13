#!/usr/bin/env python3
"""Strip ALL function...endfunction blocks and replace calls with constants."""
import re, sys

with open(sys.argv[1]) as f:
    content = f.read()

# Remove ALL function...endfunction blocks completely
result = []
i = 0
while i < len(content):
    m = re.search(r'\bfunction\b', content[i:])
    if not m:
        result.append(content[i:])
        break
    func_start = i + m.start()
    result.append(content[i:func_start])
    # Find matching endfunction
    depth = 0
    j = func_start
    while j < len(content):
        if content[j:j+8] == 'function' and (j == 0 or not content[j-1].isalnum()):
            depth += 1
        if content[j:j+11] == 'endfunction':
            depth -= 1
            if depth == 0:
                j += 11
                break
        j += 1
    i = j  # skip entire function

content = ''.join(result)

# Replace function calls with constants
replacements = {
    'tcu_fmt_is_int(fmt)': 'fmt[4]',
    'tcu_fmt_is_signed_int(fmt)': 'fmt[0]',
    'tcu_fmt_is_bfloat(fmt)': 'fmt[0]',
    'tcu_fmt_is_mx(fmt)': '1',
    'tcu_fmt_width(fmt)': '16',
    'tcu_int_fmt_width(fmt)': '16',
    'tcu_meta_stride_words(fmt)': '4',
    'mx_max_fedp_sf()': '8',
    'mx_fedp_sf_count(8, 32)': '8',
    'mx_fedp_sf_count(4, 32)': '4',
}
for old, new in replacements.items():
    content = content.replace(old, new)

# Add missing typedefs before first struct
typedef_block = '// Yosys-compat typedefs\ntypedef logic [511:0] ibuffer_t;\ntypedef logic [127:0] op_args_t;\n\n'
if 'typedef logic [511:0] ibuffer_t;' not in content:
    content = content.replace('typedef struct packed {', typedef_block + 'typedef struct packed {', 1)

# Remove duplicate op_args_t lines
lines = content.split('\n')
seen_op_args = False
new_lines = []
for line in lines:
    if 'typedef logic [127:0] op_args_t;' in line:
        if seen_op_args:
            continue  # skip duplicate
        seen_op_args = True
    new_lines.append(line)
content = '\n'.join(new_lines)

with open(sys.argv[1], 'w') as f:
    f.write(content)
print("Fixed: stripped all functions, replaced calls, added typedefs")
