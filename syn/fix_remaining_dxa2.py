#!/usr/bin/env python3
"""Fix remaining issues in DXA files for Synlig synthesis."""
import re

# Fix VX_dxa_completion.sv
with open('/tmp/dxa_synth/VX_dxa_completion.sv') as f:
    text = f.read()
# Remove orphaned backtick + end + endif left by RUNTIME_ASSERT stripping
text = text.replace('    `\n        end\n    end\n`endif\nendmodule', 'endmodule')
with open('/tmp/dxa_synth/VX_dxa_completion.sv', 'w') as f:
    f.write(text)
print('Fixed VX_dxa_completion.sv')

# Fix VX_dxa_setup.sv
with open('/tmp/dxa_synth/VX_dxa_setup.sv') as f:
    text = f.read()
# Remove orphaned backtick line before wire declaration
text = re.sub(r'    `\n    wire', '    wire', text)
# Fix remaining +: part-selects: base +: width -> base+width-1:base
def fix_part_select(m):
    var = m.group(1)
    base = m.group(2)
    width = m.group(3)
    return f"{var}[({base})+({width})-1:({base})]"
text = re.sub(r'(\w+)\[([^+\]]+)\s*\+:\s*(\w+)\]', fix_part_select, text)
with open('/tmp/dxa_synth/VX_dxa_setup.sv', 'w') as f:
    f.write(text)
print('Fixed VX_dxa_setup.sv')

# Fix VX_dxa_watchdog.sv: define RUNTIME_ASSERT as empty
with open('/tmp/dxa_synth/VX_dxa_watchdog.sv') as f:
    text = f.read()
# Replace RUNTIME_ASSERT(x); with nothing
text = re.sub(r'\s*RUNTIME_ASSERT\s*\([^)]*\)\s*;', '', text)
with open('/tmp/dxa_synth/VX_dxa_watchdog.sv', 'w') as f:
    f.write(text)
print('Fixed VX_dxa_watchdog.sv')
