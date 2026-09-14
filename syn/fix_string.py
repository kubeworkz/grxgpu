import re
with open('/tmp/tfr_ecp5/tfr_flat.sv') as f:
    content = f.read()
content = re.sub(r'parameter `STRING', 'parameter', content)
with open('/tmp/tfr_ecp5/tfr_flat.sv', 'w') as f:
    f.write(content)
remaining = set(re.findall(r'`([A-Z_][A-Z0-9_]+)', content))
print(f'Remaining: {remaining}')
