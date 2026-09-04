#!/usr/bin/env python3
"""Add typedef replacements for fedp_excep_t and fedp_class_t"""
import re

with open("/tmp/tfr_flat.sv") as f:
    content = f.read()

# Add typedef definitions after the defines header
typedef_header = """
// Replaced typedefs for synthesis
typedef struct packed {
    logic is_inf;
    logic is_nan;
    logic sign;
} fedp_excep_t;

typedef struct packed {
    logic is_zero;
    logic is_sub;
    logic is_inf;
    logic is_nan;
} fedp_class_t;

"""

# Insert after the first comment line
content = content.replace("// Yosys synthesis defines\n", "// Yosys synthesis defines\n" + typedef_header)

with open("/tmp/tfr_flat.sv", "w") as f:
    f.write(content)

print(f"Updated: {len(content)} bytes")
