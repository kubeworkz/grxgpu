import re
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()

# For every module that has TCU_MAX_INPUTS in its ports, add a localparam
# Actually, the simplest fix: replace all remaining TCU_MAX_INPUTS with 16
content = re.sub(r'\bTCU_MAX_INPUTS\b', '16', content)

with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)

remaining = set(re.findall(r'\b(TCU_[A-Z_]+)\b', content))
print(f'TCU remaining: {remaining}')
