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
    'VX_CFG_LMEM_NUM_BANKS': '4',
    # Package constants (from VX_gpu_pkg)
    'PERF_CTR_BITS': '44',
    'UUID_WIDTH': '44',
    'NW_BITS': '2',
    'NC_BITS': '4',
    'NW_WIDTH': '2',
    'NC_WIDTH': '4',
    'NT_WIDTH': '2',
    'NB_WIDTH': '2',
    'NCTA_WIDTH': '1',
    'HART_ID_WIDTH': '6',
    'HART_ID_BITS': '6',
    'BAR_ADDR_BITS': '4',
    'BAR_ADDR_W': '4',
    'BAR_SIZE_W': '4',
    'CTA_TID_WIDTH': '4',
    'SIMD_IDX_W': '1',
    'NUM_OPCS_W': '1',
    'NUM_SOCKETS': '1',
    'MAX_FANOUT': '8',
    'REG_TYPE_BITS': '2',
    'DV_STACK_SIZE': '3',
    'DV_STACK_SIZEW': '2',
    'LOG2UP': '$clog2',
}

inp = sys.argv[1] if len(sys.argv) > 1 else '/tmp/tcu_ecp5_full/tcu_flat_final.sv'
outp = sys.argv[2] if len(sys.argv) > 2 else '/tmp/tcu_ecp5_full/tcu_flat_final.sv'

with open(inp) as f:
    content = f.read()

# Replace backtick-macro usages
for macro, value in MACROS.items():
    content = re.sub(r'`' + macro + r'(?![0-9A-Za-z_])', value, content)

# Replace `CLOG2(x) with $clog2(x)
content = re.sub(r'`CLOG2\(', '$clog2(', content)

# Replace `MAX(a, b) with ternary
content = re.sub(r'`MAX\(([^,]+),\s*([^)]+)\)', r'((\1 > \2) ? (\1) : (\2))', content)

# Replace `UP(x) with ((x != 0) ? (x) : 1)
content = re.sub(r'`UP\(([^)]+)\)', r'((\1 != 0) ? (\1) : 1)', content)

# Replace `LOG2UP(x) with $clog2(x)
content = re.sub(r'`LOG2UP\(', '$clog2(', content)

# Verify no remaining backtick macros
remaining = set(re.findall(r'`([A-Z_][A-Z0-9_]+)', content))
print(f'Remaining backtick tokens: {remaining}')

with open(outp, 'w') as f:
    f.write(content)

print(f'Output: {len(content.splitlines())} lines')
