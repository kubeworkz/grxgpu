#!/usr/bin/env python3
"""Remove all backtick-preprocessor lines from flat file."""
import re, sys

path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/tcu_flat.sv'
with open(path) as f:
    lines = f.readlines()

cleaned = []
removed = 0
for l in lines:
    s = l.strip()
    # Skip lines starting with backtick (preprocessor directives)
    if s.startswith('`'):
        removed += 1
        continue
    cleaned.append(l)

with open(path, 'w') as f:
    f.writelines(cleaned)

print('Removed %d backtick-preprocessor lines from %s' % (removed, path))
