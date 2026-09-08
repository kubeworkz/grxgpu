#!/usr/bin/env python3
"""Pre-expand all macros in the flat file so Yosys doesn't need to parse them."""
import re

with open("/tmp/tcu_flat.sv") as f:
    content = f.read()

# Remove all `define lines
content = re.sub(r'^`define\s+\w+.*$', '', content, flags=re.MULTILINE)

# Pre-expand known function-like macros (use lambda to avoid backreference issues)
content = re.sub(r'`UP\(([^)]+)\)', lambda m: f'((( {m.group(1)} ) > 0) ? ( {m.group(1)} ) : 1)', content)
content = re.sub(r'`CLOG2\(([^)]+)\)', lambda m: f'($clog2( {m.group(1)} ))', content)
content = re.sub(r'`LOG2UP\(([^)]+)\)', lambda m: f'($clog2( {m.group(1)} ))', content)
content = re.sub(r'`__MIN\(([^,]+),\s*([^)]+)\)', lambda m: f'(( {m.group(1)} ) < ( {m.group(2)} ) ? ( {m.group(1)} ) : ( {m.group(2)} ))', content)
content = re.sub(r'`MAX\(([^,]+),\s*([^)]+)\)', lambda m: f'(( {m.group(1)} ) > ( {m.group(2)} ) ? ( {m.group(1)} ) : ( {m.group(2)} ))', content)

# Replace known constant macros
REPLACEMENTS = {
    '`VX_CFG_XLEN': '32',
    '`VX_CFG_NUM_THREADS': '4',
    '`VX_CFG_NUM_WARPS': '4',
    '`VX_CFG_NUM_TCU_LANES': '4',
    '`VX_CFG_ISSUE_WIDTH': '4',
    '`VX_CFG_NUM_TCU_BLOCKS': '4',
    '`VX_MEM_LMEM_BASE_ADDR': "32'hFFFF0000",
    '`VX_CFG_LMEM_LOG_SIZE': '14',
    '`VX_CFG_LMEM_NUM_BANKS': '4',
}
for old, new in REPLACEMENTS.items():
    content = content.replace(old, new)

# Strip any remaining backtick macros (comment them out to avoid Yosys errors)
content = re.sub(r'`\w+', '/* [removed] */', content)

with open("/tmp/tcu_flat.sv", "w") as f:
    f.write(content)

print("Pre-expanded all macros")
print(f"Remaining backticks: {content.count(chr(96))}")
