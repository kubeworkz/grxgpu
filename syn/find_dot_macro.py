#!/usr/bin/env python3
"""Find macro invocations with dots in arguments."""
import re

with open('/tmp/tcu_struct.sv') as f:
    content = f.read()

# Find all `MACRO patterns and check for dots in arguments
for m in re.finditer(r'`([A-Z]\w+)\s*\(', content):
    macro = m.group(1)
    start = m.end() - 1  # position of '('
    depth = 0
    for j in range(start, min(start + 500, len(content))):
        if content[j] == '(':
            depth += 1
        elif content[j] == ')':
            depth -= 1
            if depth == 0:
                arg = content[start + 1:j]
                if '.' in arg:
                    line_num = content[:m.start()].count('\n') + 1
                    print(f"Line {line_num}: `{macro}({arg[:80]})")
                break
