#!/usr/bin/env python3
import re
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()
content = re.sub(r'`CLOG2\(', '$clog2(', content)
content = re.sub(r'^[ \t]*`[^\n]*\n', '', content, flags=re.MULTILINE)
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)
remaining = set(re.findall(r'`([A-Z_][A-Z0-9_]+)', content))
print(f'Remaining: {remaining}')
print(f'Lines: {len(content.splitlines())}')
