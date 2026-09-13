#!/usr/bin/env python3
"""Find backtick macros with dots that confuse Yosys."""
import re

with open('/tmp/tcu_struct.sv') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    s = line.rstrip()
    # Find all backtick references
    for m in re.finditer(r'`(\w+)', s):
        macro = m.group(1)
        # Check if it's followed by ( with a . inside
        rest = s[m.end():]
        if rest.startswith('('):
            depth = 1
            arg_start = 1
            for j in range(1, min(200, len(rest))):
                if rest[j] == '(':
                    depth += 1
                elif rest[j] == ')':
                    depth -= 1
                    if depth == 0:
                        arg = rest[arg_start:j]
                        if '.' in arg:
                            print(f"Line {i}: `{macro}({arg[:60]})")
                        break
    # Also check for backtick-dot without paren (macro reference like `VX_CFG_SOMETHING.SOMETHING)
    for m in re.finditer(r'`(\w+)\.', s):
        macro = m.group(1)
        print(f"Line {i}: `{macro}.{s[m.end():m.end()+30]}")
