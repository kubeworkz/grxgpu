import re, sys

MACROS = {
    'VX_CFG_XLEN': '32',
    'VX_CFG_NUM_TCU_BLOCKS': '4',
    'VX_CFG_NUM_TCU_LANES': '4',
    'VX_CFG_LMEM_LOG_SIZE': '14',
    'VX_MEM_LMEM_BASE_ADDR': "32'h80000000",
    'VX_CFG_NUM_THREADS': '4',
    'VX_CFG_NUM_WARPS': '4',
    'VX_CFG_ISSUE_WIDTH': '4',
    'VX_CFG_NUM_CORES': '16',
    'VX_CFG_NUM_CLUSTERS': '1',
    'VX_CFG_SOCKET_SIZE': '1',
    'VX_CFG_NUM_BARRIERS': '4',
    'VX_CFG_NUM_LSU_LANES': '1',
}

inp = sys.argv[1] if len(sys.argv) > 1 else '/tmp/tcu_ecp5_full/tcu_flat_clean.sv'
outp = sys.argv[2] if len(sys.argv) > 2 else '/tmp/tcu_ecp5_full/tcu_flat_final.sv'

with open(inp) as f:
    content = f.read()

for macro, value in MACROS.items():
    content = re.sub(r'`' + macro + r'(?![0-9A-Za-z_])', value, content)

content = re.sub(r'`CLOG2\(', '$clog2(', content)

with open(outp, 'w') as f:
    f.write(content)

remaining = set(re.findall(r'`([A-Z_][A-Z0-9_]+)', content))
print(f'Replaced macros. Remaining backtick tokens: {remaining}')
print(f'Output: {len(content.splitlines())} lines')
