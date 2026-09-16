#!/usr/bin/env python3
"""One-shot cleanup for TFR v2 flat file for Yosys."""
import re, sys

with open('/tmp/tfr_ecp5/tfr_v2.sv') as f:
    content = f.read()

# 1. Remove all backtick-preprocessor lines (start of line)
content = re.sub(r'^[ \t]*`[^\n]*\n', '', content, flags=re.MULTILINE)

# 2. Replace inline backtick macros
content = re.sub(r'`STRING\b', '', content)
content = re.sub(r'`UNUSED_VAR\([^)]*\)', '', content)
content = re.sub(r'`UNUSED_PARAM\([^)]*\)', '', content)
content = re.sub(r'`UNUSED_PIN\([^)]*\)', '', content)
content = re.sub(r'`UNUSED_SPARAM\([^)]*\)', '', content)
content = re.sub(r'`FORCE_BUILTIN_ADDER\([^)]*\)', '0', content)
content = re.sub(r'!0', '1', content)
content = re.sub(r'`STATIC_ASSERT\([^)]*\)', '', content)
content = re.sub(r'`CLOG2\(', '$clog2(', content)
content = re.sub(r'`MAP_AOS_SOA\([^)]*\)', '', content)

# 3. Remove $display, $write, $fatal, $error, $warning (multi-line)
lines = content.split('\n')
out = []
in_syscall = False
depth = 0
for line in lines:
    s = line.strip()
    if in_syscall:
        depth += s.count('(') - s.count(')')
        if depth <= 0:
            in_syscall = False
        continue
    if re.search(r'\$display|\$write|\$fatal|\$error|\$warning', s):
        depth = s.count('(') - s.count(')')
        if depth > 0:
            in_syscall = True
        continue
    # Skip orphaned $time continuation lines
    if re.match(r'^\s*\$time,', s):
        continue
    # Skip orphaned format string lines
    if re.match(r'^\s*\(\s*".*%0', s):
        continue
    # Skip /* trace */ lines
    if '/* trace */' in s:
        continue
    out.append(line)

content = '\n'.join(out)

# 4. Fix doubled 'wire wire' -> 'wire'
while 'wire wire' in content:
    content = content.replace('wire wire', 'wire')

# 5. Remove empty begin/end blocks
content = re.sub(r'begin\s*\n\s*end', '', content)

with open('/tmp/tfr_ecp5/tfr_v2.sv', 'w') as f:
    f.write(content)

# Verify
remaining_backtick = set(re.findall(r'`([A-Z_][A-Z0-9_]+)', content))
remaining_display = content.count('$display')
print(f'Lines: {len(content.splitlines())}')
print(f'Remaining backtick: {remaining_backtick}')
print(f'Remaining $display: {remaining_display}')
