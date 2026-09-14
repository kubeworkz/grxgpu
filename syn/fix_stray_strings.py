#!/usr/bin/env python3
import re
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    lines = f.readlines()
out = [l for l in lines if l.strip() not in ('""', '"",')]
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.writelines(out)
print(f'Cleaned: {len(lines)} -> {len(out)} lines')
