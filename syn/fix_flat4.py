#!/usr/bin/env python3
"""Strip all UNUSED_* macro calls and simulation-only constructs"""
import re

with open("/tmp/tfr_flat.sv") as f:
    content = f.read()

# Strip UNUSED_SPARAM, UNUSED_PARAM, UNUSED_PIN, UNUSED_VAR lines
content = re.sub(r"^\s*`UNUSED_SPARAM\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)
content = re.sub(r"^\s*`UNUSED_PARAM\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)
content = re.sub(r"^\s*`UNUSED_PIN\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)
content = re.sub(r"^\s*`UNUSED_VAR\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)

# Strip FORCE_BUILTIN_ADDER lines
content = re.sub(r"^\s*`FORCE_BUILTIN_ADDER[^\n]*\n?", "", content, flags=re.MULTILINE)

# Strip MAP_AOS_SOA lines
content = re.sub(r"^\s*`MAP_AOS_SOA[^\n]*\n?", "", content, flags=re.MULTILINE)

# Strip TRACE_ARRAY lines
content = re.sub(r"^\s*`TRACE_ARRAY\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)

# Collapse blank lines
content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

with open("/tmp/tfr_flat.sv", "w") as f:
    f.write(content)

print(f"Updated: {len(content)} bytes")
macros = sorted(set(re.findall(r"`([A-Z_]+)", content)))
print(f"Remaining macros: {macros}")
