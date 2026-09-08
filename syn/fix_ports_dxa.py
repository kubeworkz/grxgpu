#!/usr/bin/env python3
"""Fix port list syntax issues in DXA modules."""
import re

DXA_DIR = '/tmp/dxa_synth'

def fix_ports(fname):
    with open(f'{DXA_DIR}/{fname}') as f:
        lines = f.readlines()
    
    new_lines = []
    in_ports = False
    
    for i, line in enumerate(lines):
        # Detect start of port list: ); ( on its own line
        if re.match(r'\s*\)\s*\(\s*$', line) or re.match(r'\s*\)\s*\(\s*//', line):
            in_ports = True
            new_lines.append(line)
            continue
        
        if in_ports:
            stripped = line.strip()
            # End of port list: ); on its own
            if stripped == ');':
                in_ports = False
                new_lines.append(line)
                continue
            # Check if this line ends the port list with ) followed by content
            m = re.match(r'(\s*)\)\s*(\S.*)', line)
            if m and not stripped.startswith('//'):
                new_lines.append(m.group(1) + ')\n')
                in_ports = False
                if m.group(2).strip():
                    new_lines.append(m.group(2) + '\n')
                continue
            
            # Fix trailing semicolon on last port before );
            if stripped.endswith(';') and not stripped.startswith('`') and not stripped.startswith('//'):
                next_port_end = False
                for j in range(i+1, min(i+5, len(lines))):
                    ns = lines[j].strip()
                    if ns == ');':
                        next_port_end = True
                        break
                    if ns and not ns.startswith('//') and ns:
                        break
                if next_port_end:
                    line = line.rstrip().rstrip(';') + '\n'
        
        # Fix double commas
        line = line.replace(',,', ',')
        
        # Fix trailing comma before );
        if line.rstrip().endswith(',') and i+1 < len(lines) and lines[i+1].strip() == ');':
            line = line.rstrip().rstrip(',') + '\n'
        
        new_lines.append(line)
    
    with open(f'{DXA_DIR}/{fname}', 'w') as f:
        f.writelines(new_lines)

for f in ['VX_dxa_completion.sv', 'VX_dxa_desc_table.sv', 'VX_dxa_dispatch.sv',
          'VX_dxa_req_arb.sv', 'VX_dxa_unit.sv', 'VX_dxa_worker.sv',
          'VX_dxa_core.sv', 'VX_dxa_smem_wr.sv', 'VX_dxa_gmem_req.sv']:
    fix_ports(f)
    print(f'{f} port-fixed')
