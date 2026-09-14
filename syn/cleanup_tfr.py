#!/usr/bin/env python3
"""Comprehensive cleanup for TFR flat file to be Yosys-compatible."""
import re, sys

with open('/tmp/tfr_ecp5/tfr_flat.sv') as f:
    content = f.read()

# 1. Remove all $display, $write, $fatal, $error, $warning lines and their continuation lines
lines = content.split('\n')
out = []
in_display = False
paren_depth = 0
for line in lines:
    s = line.strip()
    if in_display:
        paren_depth += s.count('(') - s.count(')')
        if paren_depth <= 0:
            in_display = False
        continue
    if re.search(r'\$display|\$write|\$fatal|\$error|\$warning', s):
        paren_depth = s.count('(') - s.count(')')
        if paren_depth > 0:
            in_display = True
        continue
    # Remove orphaned display argument lines
    if re.match(r'^\s*\$time,', s) or re.match(r'^\s*\d+\$time', s):
        continue
    # Remove STATIC_ASSERT remnants (orphaned assertion body lines)
    if re.match(r'^\s*\(".*%0', s):
        continue
    out.append(line)

content = '\n'.join(out)

# 2. Fix doubled 'wire wire' -> 'wire'
content = content.replace('wire wire', 'wire')

# 3. Remove all backtick-preprocessor lines
content = re.sub(r'^[ \t]*`[a-zA-Z_].*$', '', content, flags=re.MULTILINE)

# 4. Remove all /* trace */ comment lines
content = re.sub(r'^[ \t]*/\* trace \*/.*$', '', content, flags=re.MULTILINE)

# 5. Remove empty 'begin' blocks (orphaned from ifdef stripping)
content = re.sub(r'begin\s*\n\s*end', '', content)

# 6. Remove lines that are just format strings (orphaned from display stripping)
content = re.sub(r'^[ \t]*(is_int|abs_sum|sign_max|sign_min).*\\n.*$', '', content, flags=re.MULTILINE)

with open('/tmp/tfr_ecp5/tfr_flat.sv', 'w') as f:
    f.write(content)

print(f'Cleaned: {len(content.splitlines())} lines')
