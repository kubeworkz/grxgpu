#!/usr/bin/env python3
"""Strip /* [removed] */ macro remnants from the flat file."""
import re

with open("/tmp/tcu_flat.sv") as f:
    content = f.read()

# Strip /* [removed] */(args) patterns - these are macro remnants with arguments
result = []
i = 0
while i < len(content):
    idx = content.find('/* [removed] */', i)
    if idx < 0:
        result.append(content[i:])
        break
    result.append(content[i:idx])
    j = idx + len('/* [removed] */')
    while j < len(content) and content[j] in (' ', '\t'):
        j += 1
    if j < len(content) and content[j] == '(':
        depth = 1
        j += 1
        while j < len(content) and depth > 0:
            if content[j] == '(':
                depth += 1
            elif content[j] == ')':
                depth -= 1
            j += 1
        while j < len(content) and content[j] in (' ', '\t', ';'):
            j += 1
        if j < len(content) and content[j] == ';':
            j += 1
    i = j

content = ''.join(result)

# Also strip any remaining /* [removed] */ not followed by ( (in comments etc)
content = re.sub(r'/\* \[removed\] \*/', '', content)

with open("/tmp/tcu_flat.sv", "w") as f:
    f.write(content)

remaining = content.count("[removed]")
print(f"Cleaned removed markers: {remaining} remaining")
