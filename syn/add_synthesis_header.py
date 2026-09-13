#!/usr/bin/env python3
import re

with open('flatten_tcu.py', 'rb') as f:
    content = f.read()

# Add SYNTHESIS_HEADER before each function automatic (only if not already present)
# Only add it if the previous line doesn't already have SYNTHESIS_HEADER
lines = content.split(b'\n')
result = []
for i, line in enumerate(lines):
    if b'function automatic' in line:
        # Check if previous line already has SYNTHESIS_HEADER
        if i > 0 and b'SYNTHESIS_HEADER' not in lines[i-1]:
            result.append(b'// SYNTHESIS_HEADER')
    result.append(line)

content = b'\n'.join(result)

with open('flatten_tcu.py', 'wb') as f:
    f.write(content)

print('Done')
