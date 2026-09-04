#!/usr/bin/env python3
"""Strip simulation-only constructs from flat TFR file"""
import re

with open("/tmp/tfr_flat.sv") as f:
    content = f.read()

# Replace `STRING with nothing (it's a typedef for 'string' in simulation)
content = content.replace("`STRING ", "")
content = content.replace("`STRING", "string")

# Strip parameter lines that contain INSTANCE_ID (debug labels)
lines = content.split("\n")
filtered = []
for line in lines:
    stripped = line.strip()
    if "INSTANCE_ID" in stripped and "parameter" in stripped:
        continue
    filtered.append(line)

content = "\n".join(filtered)

# Remove any remaining `define STRING lines
content = re.sub(r'`define STRING\(x\)[^\n]*\n', '', content)

# Collapse multiple blank lines
content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

with open("/tmp/tfr_flat.sv", "w") as f:
    f.write(content)

print(f"Updated: {len(content)} bytes")
# Count remaining backtick macros
macros = sorted(set(re.findall(r"`([A-Z_]+)", content)))
print(f"Remaining macros: {macros}")
