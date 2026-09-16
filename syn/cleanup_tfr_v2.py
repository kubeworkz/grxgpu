#!/usr/bin/env python3
"""Thorough cleanup for TFR flat file — handles multi-line $display, orphaned statements, etc."""
import re, sys

with open('/tmp/tfr_ecp5/tfr_flat_raw.sv') as f:
    content = f.read()

lines = content.split('\n')
out = []

i = 0
while i < len(lines):
    line = lines[i]
    s = line.strip()
    
    # Skip all backtick-preprocessor lines
    if s.startswith('`'):
        i += 1
        continue
    
    # Skip $display / $write / $fatal / $error / $warning and their continuation lines
    if re.search(r'\$display|\$write|\$fatal|\$error|\$warning', s):
        # Count parens to find end of statement
        depth = s.count('(') - s.count(')')
        while depth > 0 and i < len(lines) - 1:
            i += 1
            depth += lines[i].count('(') - lines[i].count(')')
        i += 1
        continue
    
    # Skip orphaned $time lines (continuation of stripped display)
    if re.match(r'^\s*\$time,', s):
        i += 1
        continue
    
    # Skip orphaned format string lines (continuation of stripped display)
    if re.match(r'^\s*\d+\$time', s) or re.match(r'^\s*\(\s*\".*%0', s):
        i += 1
        continue
    
    # Skip /* trace */ lines
    if '/* trace */' in s and not s.startswith('//'):
        i += 1
        continue
    
    # Skip STATIC_ASSERT lines and their orphaned body
    if 'STATIC_ASSERT' in s:
        i += 1
        continue
    
    # Skip lines that are just orphaned assertion bodies
    if re.match(r'^\s*\(\".*%0.*\",', s):
        i += 1
        continue
    
    out.append(line)
    i += 1

content = '\n'.join(out)

# Fix doubled 'wire wire' -> 'wire'
while 'wire wire' in content:
    content = content.replace('wire wire', 'wire')

# Remove empty begin/end blocks
content = re.sub(r'begin\s*\n\s*end', '', content)

# Remove lines that are just format strings (orphaned from display stripping)
content = re.sub(r'^\s*\"[^"]*%0[^"]*\",\s*$', '', content, flags=re.MULTILINE)

# Remove empty if blocks
content = re.sub(r'if\s*\([^)]*\)\s*\n\s*end', '', content)

with open('/tmp/tfr_ecp5/tfr_flat.sv', 'w') as f:
    f.write(content)

print(f'Cleaned: {len(content.splitlines())} lines')
