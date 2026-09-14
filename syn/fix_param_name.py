import re
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()
content = content.replace('parameter 16 = 16', 'parameter TCU_MAX_INPUTS = 16')
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)
print('fixed')
