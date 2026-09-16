#!/usr/bin/env python3
"""Find backtick identifiers followed by a dot - these confuse Yosys."""
import re
with open('/tmp/tcu_struct.sv') as f:
    content = f.read()
for m in re.finditer(r'`\w+\.', content):
    line_num = content[:m.start()].count('\n') + 1
    ctx = content[m.start():m.start()+40]
    print(f"Line {line_num}: {ctx}")
