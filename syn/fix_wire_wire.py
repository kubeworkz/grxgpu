import re
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()
while 'wire wire' in content:
    content = content.replace('wire wire', 'wire')
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)
print('fixed')
