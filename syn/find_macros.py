#!/usr/bin/env python3
import re
with open('/tmp/tcu_struct.sv') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    s = line.strip()
    for m in re.finditer(r'`\w+\s*\(', s):
        macro = m.group(0).split()[0]
        start = s.find('(', m.start())
        depth = 0
        for j in range(start, min(start+200, len(s))):
            if s[j] == '(':
                depth += 1
            elif s[j] == ')':
                depth -= 1
                if depth == 0:
                    arg = s[start+1:j]
                    if '.' in arg:
                        print(f'Line {i}: {macro}({arg[:80]})')
                    break
