import sys

with open('/OpenROAD/test/Nangate45/Nangate45_typ.lib') as f:
    lines = f.readlines()

output = []
skip = False
for i, line in enumerate(lines):
    if 'cell (CLKGATE' in line or 'cell (CLKGATETST' in line:
        skip = True
    if skip:
        if line.strip() == '}':
            skip = False
        continue
    output.append(line)

with open('/out/Nangate45_typ_noclk.lib', 'w') as f:
    f.writelines(output)
print(f'Removed clock gate cells. {len(lines)} -> {len(output)} lines')
