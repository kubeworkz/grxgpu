#!/usr/bin/env python3
"""Replace fedp_excep_t and fedp_class_t with explicit wire types"""
import re

with open("/tmp/tfr_flat.sv") as f:
    content = f.read()

# Remove the typedef declarations entirely
content = re.sub(r"typedef struct packed \{[^}]*\} fedp_excep_t\s*;", "", content, flags=re.DOTALL)
content = re.sub(r"typedef struct packed \{[^}]*\} fedp_class_t\s*;", "", content, flags=re.DOTALL)

# Replace fedp_excep_t with logic [2:0] in all contexts
content = re.sub(r"\bfedp_excep_t\b", "logic [2:0]", content)

# Replace fedp_class_t with logic [3:0] in all contexts  
content = re.sub(r"\bfedp_class_t\b", "logic [3:0]", content)

# Also handle: input/output fedp_excep_t -> input/output logic [2:0]
content = re.sub(r"(input|output)\s+wire\s+logic\s+\[2:0\]", r"\1 wire [2:0]", content)
content = re.sub(r"(input|output)\s+wire\s+logic\s+\[3:0\]", r"\1 wire [3:0]", content)

# Replace field accesses with bit indexing
# fedp_excep_t fields: is_inf=bit2, is_nan=bit1, sign=bit0
content = re.sub(r"\.is_inf\b", "[2]", content)
content = re.sub(r"\.is_nan\b", "[1]", content)
content = re.sub(r"\.sign\b", "[0]", content)

# fedp_class_t fields: is_zero=bit3, is_sub=bit2, is_inf=bit1, is_nan=bit0
# Only replace these in fedp_class_t contexts — too dangerous to globally replace .is_zero etc.
# Let's leave the fedp_class_t field accesses for now and see what happens

with open("/tmp/tfr_flat.sv", "w") as f:
    f.write(content)

print(f"Updated: {len(content)} bytes")
