import re
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()

# Replace TCU_TC_K in parameter defaults
content = re.sub(r'parameter N = TCU_TC_K', 'parameter N = 2', content)

# Replace all remaining TCU_* package constants with their values
CONSTANTS = {
    'TCU_EXP_BITS': '10',
    'TCU_FP16_ID': '2',
    'TCU_FP8_ID': '4',
    'TCU_BF8_ID': '5',
    'TCU_BF16_ID': '3',
    'TCU_TF32_ID': '1',
    'TCU_MXFP8_ID': '8',
    'TCU_MXBF8_ID': '9',
    'TCU_MXFP4_ID': '10',
    'TCU_NVFP4_ID': '11',
    'TCU_FP32_ID': '0',
    'TCU_MAX_INPUTS': '16',
    'TCU_MAX_ELT_RATIO': '8',
    'TCU_MIN_FMT_WIDTH': '4',
}

for name, value in CONSTANTS.items():
    content = re.sub(r'\b' + name + r'\b', value, content)

with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)

# Check for remaining unresolved references
remaining_tcu = set(re.findall(r'\b(TCU_[A-Z_]+)\b', content))
remaining_vx = set(re.findall(r'\bVX_tcu_pkg::\w+', content))
print(f'TCU remaining: {remaining_tcu}')
print(f'VX_tcu_pkg remaining: {remaining_vx}')
