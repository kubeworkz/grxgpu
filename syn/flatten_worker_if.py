#!/usr/bin/env python3
"""Flatten VX_dxa_worker_req_if in VX_dxa_worker.sv."""

with open('/tmp/dxa_flat/VX_dxa_worker.sv') as f:
    content = f.read()

# Replace port declaration
old_port = '    VX_dxa_worker_req_if.slave req_if,'
new_ports = '''    input  wire        req_if_valid,
    input  wire [255:0] req_if_req_data,
    input  wire [127:0] req_if_desc_data,
    output wire        req_if_ready,'''
content = content.replace(old_port, new_ports)

# Replace hierarchical references
content = content.replace('req_if.valid', 'req_if_valid')
content = content.replace('req_if.req_data', 'req_if_req_data')
content = content.replace('req_if.desc_data', 'req_if_desc_data')
content = content.replace('req_if.ready', 'req_if_ready')

with open('/tmp/dxa_flat/VX_dxa_worker.sv', 'w') as f:
    f.write(content)

# Check for remaining
remaining = [l.strip() for l in content.split('\n') if 'req_if.' in l or 'VX_dxa_worker_req_if' in l]
if remaining:
    print("Remaining: " + str(len(remaining)))
    for l in remaining[:5]:
        print("  " + l)
else:
    print("VX_dxa_worker.sv: clean!")
