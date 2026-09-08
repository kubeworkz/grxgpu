#!/usr/bin/env python3
"""Strip all remaining backtick preprocessor directives from dxa_flat_all.sv."""
import re

with open("/tmp/dxa_synth/dxa_flat_all.sv") as f:
    content = f.read()

# Strip ALL remaining backtick directives (line-level)
content = re.sub(r'^\s*`[a-z]+.*$', '', content, flags=re.MULTILINE)

# Also strip inline backtick references like `VX_CFG_XLEN, `UP, `CLOG2, etc
# Replace with reasonable defaults
subs = {
    '`UP': '(x > 0 ? x : 1)',
    '`CLOG2': '(x > 1 ? $clog2(x) : 1)',
    '`CDIV': '((x + y - 1) / y)',
    '`MIN': '((x < y) ? x : y)',
    '`MAX_FANOUT': '16',
    '`STRING': '',
    '`TYPE': '',
}
# Replace macro-like identifiers with empty or safe values
for macro in ['UP', 'CLOG2', 'CDIV', 'MIN', 'MAX_FANOUT', 'STRING', 'TYPE',
              'IGNORE_UNUSED_BEGIN', 'IGNORE_UNUSED_END', 'FORCE_BUILTIN_ADDER']:
    content = content.replace(f'`{macro}', '')

# Replace remaining VX_CFG_* references with hardcoded values
cfg_defaults = {
    'VX_CFG_XLEN': '32',
    'VX_CFG_MEM_ADDR_WIDTH': '32',
    'VX_CFG_NUM_SFU_LANES': '1',
    'VX_CFG_NUM_DXA_CORES': '2',
    'VX_CFG_DXA_QUEUE_SIZE': '4',
    'VX_CFG_L1_LINE_SIZE': '64',
    'VX_CFG_L1_MEM_PORTS': '1',
    'VX_CFG_SFU_L1D_ENABLED': '0',
    'VX_CFG_SFU_L1D_REPLAY_ENABLED': '0',
    'VX_CFG_SFU_CSRS_ENABLED': '0',
    'VX_CFG_SFU_MPM_ENABLED': '0',
    'VX_CFG_SFU_TMU_ENABLED': '0',
    'VX_CFG_SFU_WCTL_ENABLED': '0',
    'VX_CFG_SFU_ISA lưng_ENABLED': '0',
    'VX_CFG_SFU_ARENA_ENABLED': '0',
    'VX_CFG_TCU_ENABLED': '1',
    'VX_CFG_TCU_FP32_ENABLE': '1',
    'VX_CFG_TCU_FP16_ENABLE': '1',
    'VX_CFG_TCU_BF16_ENABLE': '1',
    'VX_CFG_TCU_TF32_ENABLE': '1',
    'VX_CFG_TCU_FP4_ENABLE': '0',
    'VX_CFG_TCU_INT4_ENABLE': '1',
    'VX_CFG_TCU_INT8_ENABLE': '1',
    'VX_CFG_TCU_INT16_ENABLE': '0',
    'VX_CFG_TCU_INT32_ENABLE': '0',
    'VX_CFG_TCU_FP8_ENABLE': '0',
    'VX_CFG_TCU_SPARSE_ENABLE': '0',
    'VX_CFG_EXT_RASTER_ENABLE': '0',
    'VX_CFG_EXT_OM_ENABLE': '0',
    'VX_CFG_EXT_RTU_ENABLE': '0',
}

# Strip remaining backtick defines at line start
content = re.sub(r'^\s*`[a-zA-Z_]\w*.*$', '', content, flags=re.MULTILINE)

with open("/tmp/dxa_synth/dxa_flat_all.sv", "w") as f:
    f.write(content)

remaining = len(re.findall(r'`[a-zA-Z_]\w*', content))
print(f"Remaining backtick refs: {remaining}")
lines = len(content.splitlines())
print(f"Total lines: {lines}")
