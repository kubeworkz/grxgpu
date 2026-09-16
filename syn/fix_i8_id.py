import re
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()
# TCU_I8_ID = 6, TCU_I4_ID = 7 (from VX_tcu_pkg)
content = re.sub(r'\bTCU_I8_ID\b', '6', content)
content = re.sub(r'\bTCU_I4_ID\b', '7', content)
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)
# Check for any remaining unresolved identifiers
remaining_tcu = set(re.findall(r'\b(TCU_[A-Z_]+)\b', content))
print(f'TCU remaining: {remaining_tcu}')
