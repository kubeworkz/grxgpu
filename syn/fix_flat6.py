#!/usr/bin/env python3
"""Remove duplicate typedefs and clean up flat TFR"""
import re

with open("/tmp/tfr_flat.sv") as f:
    content = f.read()

# Remove inline typedef blocks for fedp_excep_t and fedp_class_t
# These are multi-line: typedef struct packed { ... } fedp_excep_t;
content = re.sub(
    r"typedef struct packed \{[^}]*\} fedp_excep_t\s*;",
    "/* fedp_excep_t already defined */",
    content, flags=re.DOTALL
)
content = re.sub(
    r"typedef struct packed \{[^}]*\} fedp_class_t\s*;",
    "/* fedp_class_t already defined */",
    content, flags=re.DOTALL
)

# Also remove duplicate module declarations — keep only the first occurrence
# of each module name
seen_modules = set()
lines = content.split("\n")
filtered = []
skip_block = False
for i, line in enumerate(lines):
    m = re.match(r"^\s*module\s+(\w+)", line)
    if m:
        mod_name = m.group(1)
        if mod_name in seen_modules:
            skip_block = True
            continue
        seen_modules.add(mod_name)
        skip_block = False
    if skip_block:
        if re.match(r"^\s*endmodule", line):
            skip_block = False
        continue
    filtered.append(line)

content = "\n".join(filtered)

# Collapse blank lines
content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

with open("/tmp/tfr_flat.sv", "w") as f:
    f.write(content)

print(f"Updated: {len(content)} bytes, {len(seen_modules)} modules: {sorted(seen_modules)}")
