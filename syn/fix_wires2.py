#!/usr/bin/env python3
"""Convert ALL wire declarations to reg (except module ports) for Yosys"""
import re

with open("/tmp/tfr_flat.sv") as f:
    content = f.read()

# Convert ALL internal wire declarations to reg
# This is safe for Yosys since it treats wire/reg interchangeably
# for logic synthesis purposes
content = re.sub(r"(^|\n)(\s+)wire (\[)", r"\1\2reg \3", content, flags=re.MULTILINE)
content = re.sub(r"(^|\n)(\s+)wire (\w+;)", r"\1\2reg \3", content, flags=re.MULTILINE)

# But keep port declarations as wire — they're between module and );
# Actually, Yosys should handle wire ports fine even with reg internals
# The key issue is that wire can't be assigned in always blocks

with open("/tmp/tfr_flat.sv", "w") as f:
    f.write(content)
print(f"Updated: {len(content)} bytes")
