#!/usr/bin/env python3
"""Fix remaining interface references in submodule instantiations."""
import re, os

os.chdir("/tmp/dxa_synth")

# Map of interface member access patterns to flat wire replacements
# Format: (pattern, replacement)
interface_members = {
    # VX_mem_bus_if members
    'req_valid': 'req_valid',
    'req_addr': 'req_addr',
    'req_data': 'req_data',
    'req_byteen': 'req_byteen',
    'req_attr': 'req_attr',
    'req_tag': 'req_tag',
    'req_ready': 'req_ready',
    'rsp_valid': 'rsp_valid',
    'rsp_data': 'rsp_data',
    'rsp_tag': 'rsp_tag',
    'rsp_ready': 'rsp_ready',
    # VX_dcr_bus_if members
    'dcr_req_valid': 'req_valid',
    'dcr_req_rw': 'req_rw',
    'dcr_req_addr': 'req_addr',
    'dcr_req_data': 'req_data',
    'dcr_rsp_data': 'rsp_data',
    # VX_txbar_bus_if members
    'txbar_valid': 'valid',
    'txbar_data_addr': 'data_addr',
    'txbar_data_is_done': 'data_is_done',
    'txbar_ready': 'ready',
    # VX_execute_if members
    'execute_valid': 'valid',
    'execute_hdr_uuid': 'hdr_uuid',
    'execute_hdr_wid': 'hdr_wid',
    'execute_rs1_data': 'rs1_data',
    'execute_rs2_data': 'rs2_data',
    'execute_rs3_data': 'rs3_data',
    'execute_ready': 'ready',
    # VX_result_if members
    'result_valid': 'valid',
    'result_data_header': 'data_header',
    'result_data_data': 'data_data',
    'result_ready': 'ready',
    # VX_dxa_worker_req_if members
    'worker_valid': 'valid',
    'worker_req_data': 'req_data',
    'worker_desc_data': 'desc_data',
    'worker_ready': 'ready',
}

# Fix VX_dxa_core.sv submodule connections
fname = "VX_dxa_core.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    
    # Fix .dcr_bus_if (dcr_bus_if) -> flat wire connections
    c = c.replace('.dcr_bus_if (dcr_bus_if)', 
                  '.req_valid(dcr_bus_if_req_valid),\n        .req_rw(dcr_bus_if_req_rw),\n        .req_addr(dcr_bus_if_req_addr),\n        .req_data(dcr_bus_if_req_data),\n        .rsp_data(dcr_bus_if_rsp_data)')
    
    # Fix .bus_in_if (req_bus_if) -> flat wire connections
    c = c.replace('.bus_in_if  (req_bus_if)',
                  '.bus_in_req_valid(req_bus_if_req_valid),\n        .bus_in_req_addr(req_bus_if_req_addr),\n        .bus_in_req_data(req_bus_if_req_data),\n        .bus_in_req_byteen(req_bus_if_req_byteen),\n        .bus_in_req_attr(req_bus_if_req_attr),\n        .bus_in_req_tag(req_bus_if_req_tag_uuid),\n        .bus_in_req_ready(req_bus_if_req_ready),\n        .bus_in_rsp_valid(req_bus_if_rsp_valid),\n        .bus_in_rsp_data(req_bus_if_rsp_data),\n        .bus_in_rsp_tag(req_bus_if_rsp_tag_uuid),\n        .bus_in_rsp_ready(req_bus_if_rsp_ready)')
    
    # Fix .bus_out_if (arb_out_bus_if) -> flat wire connections  
    c = c.replace('.bus_out_if (arb_out_bus_if)',
                  '.bus_out_req_valid(arb_out_bus_if_req_valid),\n        .bus_out_req_addr(arb_out_bus_if_req_addr),\n        .bus_out_req_data(arb_out_bus_if_req_data),\n        .bus_out_req_byteen(arb_out_bus_if_req_byteen),\n        .bus_out_req_attr(arb_out_bus_if_req_attr),\n        .bus_out_req_tag(arb_out_bus_if_req_tag_uuid),\n        .bus_out_req_ready(arb_out_bus_if_req_ready),\n        .bus_out_rsp_valid(arb_out_bus_if_rsp_valid),\n        .bus_out_rsp_data(arb_out_bus_if_rsp_data),\n        .bus_out_rsp_tag(arb_out_bus_if_rsp_tag_uuid),\n        .bus_out_rsp_ready(arb_out_bus_if_rsp_ready)')
    
    # Fix arb_out_bus_if[0].req_valid -> arb_out_bus_if_req_valid[0]
    c = re.sub(r'arb_out_bus_if\[(\w+)\]\.(\w+)', r'arb_out_bus_if_\2[\1]', c)
    
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname} submodule connections")

# Fix VX_dxa_gmem_req.sv: mem_bus_w hierarchical refs
fname = "VX_dxa_gmem_req.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    # Replace mem_bus_w.rsp_data.tag.value with flat wire
    c = c.replace('mem_bus_w.rsp_data.tag.value', 'mem_bus_w_rsp_tag_value')
    c = c.replace('mem_bus_w.req_data.tag.uuid', 'mem_bus_w_req_tag_uuid')
    c = c.replace('mem_bus_w.req_data.tag.value', 'mem_bus_w_req_tag_value')
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname} hierarchical refs")

# Fix VX_dxa_desc_table.sv: dcr_bus_if.rsp_data
fname = "VX_dxa_desc_table.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    c = c.replace('dcr_bus_if.rsp_data', 'dcr_bus_if_rsp_data')
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname} hierarchical refs")

# Fix VX_dxa_unit.sv: execute_if.data.header.uuid etc
fname = "VX_dxa_unit.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    c = c.replace('execute_if.data.header.uuid', 'execute_if_hdr_uuid')
    c = c.replace('execute_if.data.header.wid', 'execute_if_hdr_wid')
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname} hierarchical refs")
