#!/usr/bin/env python3
"""Replace remaining TCU package constants with literal values."""
import re, sys

with open('/tmp/tfr_ecp5/tfr_v2.sv') as f:
    content = f.read()

# TCU package constants (G100 default config: VX_CFG_NUM_THREADS=4)
CONSTANTS = {
    'TCU_TC_K': '2',
    'TCU_TC_M': '2',
    'TCU_TC_N': '2',
    'TCU_BLOCK_CAP': '4',
    'TCU_TILE_CAP': '32',
    'TCU_TILE_M': '8',
    'TCU_TILE_N': '4',
    'TCU_TILE_K': '4',
    'TCU_EXP_BITS': '10',  # fp16 path
    # Format IDs
    'TCU_FP16_ID': '2',
    'TCU_FP8_ID': '4',
    'TCU_BF8_ID': '5',
    'TCU_MXFP8_ID': '8',
    'TCU_MXBF8_ID': '9',
    'TCU_MXFP4_ID': '10',
    'TCU_NVFP4_ID': '11',
}

for name, value in CONSTANTS.items():
    content = re.sub(r'\b' + name + r'\b', value, content)

with open('/tmp/tfr_ecp5/tfr_v2.sv', 'w') as f:
    f.write(content)

remaining = set(re.findall(r'`([A-Z_][A-Z0-9_]+)', content))
tcu_remaining = set(re.findall(r'\b(TCU_[A-Z_]+)\b', content))
print(f'Backtick remaining: {remaining}')
print(f'TCU_ references remaining: {len(tcu_remaining)}')
