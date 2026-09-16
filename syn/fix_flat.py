#!/usr/bin/env python3
"""Fix the flattened VX_dxa_gmem_req.sv."""
import re

with open('/tmp/dxa_flat/VX_dxa_gmem_req.sv') as f:
    content = f.read()

# 1. Replace the multi-line VX_mem_bus_if instance with flat wires
old_instance = '''    VX_mem_bus_if #(
        .DATA_SIZE (GMEM_BYTES),
        .TAG_WIDTH (GMEM_TAG_WIDTH)
    ) mem_bus_w ();'''

flat_wires = '''    wire        mem_bus_w_req_valid;
    wire [31:0] mem_bus_w_req_addr;
    wire [511:0] mem_bus_w_req_data;
    wire [63:0] mem_bus_w_req_byteen;
    wire [1:0]  mem_bus_w_req_attr;
    wire [31:0] mem_bus_w_req_tag_uuid;
    wire [12:0] mem_bus_w_req_tag_value;
    wire        mem_bus_w_req_ready;
    wire        mem_bus_w_rsp_valid;
    wire [511:0] mem_bus_w_rsp_data;
    wire [31:0] mem_bus_w_rsp_tag_uuid;
    wire [12:0] mem_bus_w_rsp_tag_value;
    wire        mem_bus_w_rsp_ready;'''

content = content.replace(old_instance, flat_wires)

# 2. Flatten hierarchical references to mem_bus_w
replacements = [
    ('mem_bus_w.req_data.rw', 'mem_bus_w_req_data_rw'),
    ('mem_bus_w.req_data.addr', 'mem_bus_w_req_data_addr'),
    ('mem_bus_w.req_data.data', 'mem_bus_w_req_data_data'),
    ('mem_bus_w.req_data.byteen', 'mem_bus_w_req_data_byteen'),
    ('mem_bus_w.req_data.attr', 'mem_bus_w_req_data_attr'),
    ('mem_bus_w.req_data.tag.uuid', 'mem_bus_w_req_tag_uuid'),
    ('mem_bus_w.req_data.tag.value', 'mem_bus_w_req_tag_value'),
    ('mem_bus_w.req_valid', 'mem_bus_w_req_valid'),
    ('mem_bus_w.req_ready', 'mem_bus_w_req_ready'),
    ('mem_bus_w.rsp_data.data', 'mem_bus_w_rsp_data'),
    ('mem_bus_w.rsp_data.tag.uuid', 'mem_bus_w_rsp_tag_uuid'),
    ('mem_bus_w.rsp_data.tag.value', 'mem_bus_w_rsp_tag_value'),
    ('mem_bus_w.rsp_valid', 'mem_bus_w_rsp_valid'),
    ('mem_bus_w.rsp_ready', 'mem_bus_w_rsp_ready'),
]

for old, new in replacements:
    content = content.replace(old, new)

# 3. Fix VX_mem_bus_slice (replace with direct wire connections)
old_slice = '''    VX_mem_bus_slice #(
        .DATAW (GMEM_DATAW),
        .TAGW (GMEM_TAG_WIDTH)
    ) mem_bus_slice (
        .bus_in_if  (mem_bus_w),
        .bus_out_if (gmem_bus_if)
    );'''

new_slice = '''    // Direct connection (flattened from VX_mem_bus_slice)
    assign gmem_bus_if_req_valid = mem_bus_w_req_valid;
    assign gmem_bus_if_req_addr = mem_bus_w_req_data_addr;
    assign gmem_bus_if_req_data = mem_bus_w_req_data_data;
    assign gmem_bus_if_req_byteen = mem_bus_w_req_data_byteen;
    assign gmem_bus_if_req_attr = mem_bus_w_req_data_attr;
    assign gmem_bus_if_req_tag_uuid = mem_bus_w_req_tag_uuid;
    assign gmem_bus_if_req_tag_value = mem_bus_w_req_tag_value;
    assign mem_bus_w_req_ready = gmem_bus_if_req_ready;
    assign mem_bus_w_rsp_valid = gmem_bus_if_rsp_valid;
    assign mem_bus_w_rsp_data = gmem_bus_if_rsp_data;
    assign mem_bus_w_rsp_tag_uuid = gmem_bus_if_rsp_tag_uuid;
    assign mem_bus_w_rsp_tag_value = gmem_bus_if_rsp_tag_value;
    assign gmem_bus_if_rsp_ready = mem_bus_w_rsp_ready;'''

content = content.replace(old_slice, new_slice)

# Write back
with open('/tmp/dxa_flat/VX_dxa_gmem_req.sv', 'w') as f:
    f.write(content)

# Check for remaining hierarchical refs
remaining = [l for l in content.split('\n') if 'mem_bus_w.' in l or 'gmem_bus_if.' in l]
if remaining:
    print("REMAINING hierarchical refs:")
    for l in remaining:
        print("  " + l.strip())
else:
    print("All hierarchical references flattened!")
