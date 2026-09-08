#!/usr/bin/env python3
"""Replace SV part-select (+:) operators with explicit bit slicing for Yosys compatibility."""
import re, os

os.chdir("/tmp/dxa_synth")

# Map of files that need fixing (from the error messages)
files_to_fix = ["VX_dxa_setup.sv", "VX_dxa_smem_wr.sv", "VX_dxa_core.sv", "VX_dxa_worker.sv", "VX_dxa_gmem_req.sv"]

for fname in files_to_fix:
    with open(fname) as f:
        content = f.read()
    
    original = content
    
    # Pattern: identifier[base +: width]  →  identifier[base+width-1:base]
    # This handles cases like: req_data.meta[4 +: NW_BITS]
    def replace_part_select(match):
        full = match.group(0)
        signal = match.group(1)
        base_expr = match.group(2)
        width_expr = match.group(3)
        # Convert to explicit range: [base+width-1:base]
        return f"{signal}[({base_expr})+({width_expr})-1:({base_expr})]"
    
    # Match word[expr +: expr] or word[expr -: expr]
    pattern = r'(\w+(?:\.\w+)*)\[(.+?)\s*\+\:\s*(.+?)\]'
    content = re.sub(pattern, replace_part_select, content)
    
    # Also handle -: part-selects
    def replace_minus_select(match):
        full = match.group(0)
        signal = match.group(1)
        base_expr = match.group(2)
        width_expr = match.group(3)
        return f"{signal}[({base_expr}):-({width_expr})]"
    
    pattern2 = r'(\w+(?:\.\w+)*)\[(.+?)\s*\-\:\s*(.+?)\]'
    content = re.sub(pattern2, replace_minus_select, content)
    
    if content != original:
        with open(fname, 'w') as f:
            f.write(content)
        count = len(re.findall(r'\+\:', original))
        print(f"  {fname}: replaced {count} part-select operators")
    else:
        print(f"  {fname}: no changes needed")
