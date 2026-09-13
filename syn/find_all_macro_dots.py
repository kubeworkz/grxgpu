#!/usr/bin/env python3
"""Find ALL macro invocations with dots in their arguments."""
import re

with open('/tmp/tcu_struct.sv') as f:
    content = f.read()

# Find ALL backtick-word( patterns
for m in re.finditer(r'`(\w+)\s*\(', content):
    macro = m.group(1)
    start = m.end() - 1
    depth = 1
    j = start + 1
    while j < len(content) and depth > 0:
        if content[j] == '(':
            depth += 1
        elif content[j] == ')':
            depth -= 1
        j += 1
    arg = content[start+1:j-1]
    if '.' in arg:
        line_num = content[:m.start()].count('\n') + 1
        print(f"Line {line_num}: `{macro}({arg[:80]})")
