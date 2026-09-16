import re
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()
# Add TCU_MAX_INPUTS = 16 as a parameter in the first module's port list
# and replace all localparam TCU_MAX_INPUTS with just a comment
content = content.replace('localparam TCU_MAX_INPUTS = ', '// localparam TCU_MAX_INPUTS = ')
# Add parameter to the first module header
content = content.replace(
    '    parameter USE_DSP = 0   // map mantissa multipliers onto DSP48 slices (same latency)\n)',
    '    parameter USE_DSP = 0,  // map mantissa multipliers onto DSP48 slices (same latency)\n    parameter TCU_MAX_INPUTS = 16\n)'
)
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)
print('fixed')
