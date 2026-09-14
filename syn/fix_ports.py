#!/usr/bin/env python3
"""Fix remaining interface port declarations in flattened DXA modules."""

# Fix VX_dxa_desc_table.sv port list
with open('/tmp/dxa_flat/VX_dxa_desc_table.sv') as f:
    content = f.read()

old_port = '    VX_dcr_bus_if.slave dcr_bus_if,'
new_ports = '''    input  wire        dcr_bus_if_req_valid,
    input  wire        dcr_bus_if_req_data_rw,
    input  wire [11:0] dcr_bus_if_req_data_addr,
    input  wire [31:0] dcr_bus_if_req_data_data,
    output wire        dcr_bus_if_rsp_valid,
    output wire [31:0] dcr_bus_if_rsp_data_data,'''
content = content.replace(old_port, new_ports)

with open('/tmp/dxa_flat/VX_dxa_desc_table.sv', 'w') as f:
    f.write(content)
print("Fixed VX_dxa_desc_table.sv ports")

# Fix VX_dxa_completion.sv port list
with open('/tmp/dxa_flat/VX_dxa_completion.sv') as f:
    content = f.read()

old_port = '    VX_txbar_bus_if.master                     txbar_bus_if'
new_ports = '''    output wire        txbar_bus_if_valid,
    output wire [31:0] txbar_bus_if_data_addr,
    output wire        txbar_bus_if_data_is_done,
    input  wire        txbar_bus_if_ready'''
content = content.replace(old_port, new_ports)

with open('/tmp/dxa_flat/VX_dxa_completion.sv', 'w') as f:
    f.write(content)
print("Fixed VX_dxa_completion.sv ports")

# Verify
for fname in ['VX_dxa_desc_table.sv', 'VX_dxa_completion.sv', 'VX_dxa_worker.sv']:
    with open('/tmp/dxa_flat/' + fname) as f:
        c = f.read()
    remaining = [l.strip() for l in c.split('\n') 
                 if 'dcr_bus_if.' in l or 'txbar_bus_if.' in l or 'gmem_bus_if.' in l or 'smem_bus_if.' in l
                 or 'VX_dcr_bus_if' in l or 'VX_txbar_bus_if' in l]
    if remaining:
        print("  " + fname + ": " + str(len(remaining)) + " remaining")
        for l in remaining[:3]:
            print("    " + l)
    else:
        print("  " + fname + ": clean!")
