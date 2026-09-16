import re
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()

# Replace VX_tcu_pkg::exp_bits(N) and VX_tcu_pkg::sign_pos(N) with literal values
# exp_bits: TF32=8, FP16=5, BF16=8, FP8=4, BF8=5, FP32=8
# sign_pos: TF32=18, FP16=15, BF16=15, FP8=7, BF8=7, FP32=31
EXP_BITS = {0: 8, 1: 8, 2: 5, 3: 8, 4: 4, 5: 5}
SIGN_POS = {0: 31, 1: 18, 2: 15, 3: 15, 4: 7, 5: 7}

for fmt_id, val in EXP_BITS.items():
    content = content.replace(f'VX_tcu_pkg::exp_bits({fmt_id})', str(val))

for fmt_id, val in SIGN_POS.items():
    content = content.replace(f'VX_tcu_pkg::sign_pos({fmt_id})', str(val))

with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)

remaining = set(re.findall(r'VX_tcu_pkg::\w+', content))
print(f'VX_tcu_pkg remaining: {remaining}')
