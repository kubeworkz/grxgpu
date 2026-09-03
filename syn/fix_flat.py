#!/usr/bin/env python3
"""Add missing defines to the flat TFR file"""
import re

with open("/tmp/tfr_flat.sv") as f:
    content = f.read()

# Add missing defines at the top
header = """// Yosys synthesis defines
`define VX_CFG_XLEN 32
`define VX_CFG_NUM_THREADS 4
`define VX_CFG_NUM_WARPS 4
`define VX_CFG_NUM_TCU_LANES 4
`define STATIC_ASSERT(cond, msg)
`define UNUSED(param) /* unused */
`define TRACE(level, msg)

"""

content = header + content

# Also strip any remaining VX_CFG_ backtick references
content = re.sub(r"`VX_CFG_NUM_THREADS", "4", content)
content = re.sub(r"`VX_CFG_NUM_WARPS", "4", content)
content = re.sub(r"`VX_CFG_NUM_TCU_LANES", "4", content)

with open("/tmp/tfr_flat.sv", "w") as f:
    f.write(content)

print(f"Updated: {len(content)} bytes")
