#!/usr/bin/env python3
"""Strip all macros from tcu_struct.sv for Yosys compatibility."""
import re

with open('/tmp/tcu_struct.sv') as f:
    c = f.read()

# Remove all define lines (but keep default_nettype)
lines = c.split('\n')
result = []
for line in lines:
    stripped = line.strip()
    if stripped.startswith('`define'):
        continue
    if stripped.startswith('`default_nettype'):
        continue
    result.append(line)

c2 = '\n'.join(result)

# Replace backtick references with literal values
replacements = {
    '`VX_CFG_XLEN': '32',
    '`VX_CFG_NUM_THREADS': '4',
    '`VX_CFG_NUM_WARPS': '4',
    '`VX_CFG_NUM_TCU_LANES': '4',
    '`VX_CFG_ISSUE_WIDTH': '4',
    '`VX_CFG_NUM_TCU_BLOCKS': '4',
    '`VX_MEM_LMEM_BASE_ADDR': '32\'hFFFF0000',
    '`VX_CFG_LMEM_LOG_SIZE': '14',
    '`VX_CFG_LMEM_NUM_BANKS': '4',
    '`MAX': 'MAX',
    '`UNUSED_VAR(x)': '',
    '`UNUSED_SPARAM(x)': '',
    '`UNUSED_PARAM(p)': '',
    '`STATIC_ASSERT(cond, msg)': '',
    '`SCOPE_IO_SWITCH(count)': '',
    '`SCOPE_IO_DECL': '',
    '`SCOPE_IO_BIND(i)': '',
    '`SCOPE_IO_UNUSED(i)': '',
    '`STRING': 'reg',
    '`SFORMATF(x)': '""',
    '`MAP_AOS_SOA(i, n, a, b)': '',
    '`TRACING_OFF': '',
    '`FORCE_BUILTIN_ADDER(x)': '',
}

for old, new in replacements.items():
    c2 = c2.replace(old, new)

# Remove any remaining backtick references
c2 = re.sub(r'`\w+', '', c2)

# Add default_nettype wire at top
c2 = '`default_nettype wire\n' + c2

with open('/tmp/tcu_ys2.sv', 'w') as f:
    f.write(c2)

print(f'Done: {len(c2)} bytes, {c2.count(chr(10))+1} lines')
