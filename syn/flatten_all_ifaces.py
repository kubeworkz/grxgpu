#!/usr/bin/env python3
"""
Flatten VX_dcr_bus_if and VX_txbar_bus_if in DXA modules.
Also fix VX_dxa_worker port connections to match flattened gmem_req/smem_wr.
"""
import re

def flatten_dcr_bus(content, instance_name):
    """Flatten VX_dcr_bus_if to flat wires."""
    # dcr_req_t: rw, addr[VX_DCR_ADDR_WIDTH-1:0], data[VX_DCR_DATA_WIDTH-1:0]
    # dcr_rsp_t: data[VX_DCR_DATA_WIDTH-1:0]
    # Ports: req_valid, req_data, rsp_valid, rsp_data
    
    # Replace hierarchical references
    content = re.sub(rf'{instance_name}\.req_valid', f'{instance_name}_req_valid', content)
    content = re.sub(rf'{instance_name}\.req_data\.rw', f'{instance_name}_req_data_rw', content)
    content = re.sub(rf'{instance_name}\.req_data\.addr', f'{instance_name}_req_data_addr', content)
    content = re.sub(rf'{instance_name}\.req_data\.data', f'{instance_name}_req_data_data', content)
    content = re.sub(rf'{instance_name}\.rsp_valid', f'{instance_name}_rsp_valid', content)
    content = re.sub(rf'{instance_name}\.rsp_data\.data', f'{instance_name}_rsp_data_data', content)
    content = re.sub(rf'{instance_name}\.rsp_data', f'{instance_name}_rsp_data', content)
    
    return content

def flatten_txbar_bus(content, instance_name):
    """Flatten VX_txbar_bus_if to flat wires."""
    # txbar_t: addr[BAR_ADDR_W-1:0], is_done
    # Ports: valid, data, ready
    
    content = re.sub(rf'{instance_name}\.valid', f'{instance_name}_valid', content)
    content = re.sub(rf'{instance_name}\.data\.addr', f'{instance_name}_data_addr', content)
    content = re.sub(rf'{instance_name}\.data\.is_done', f'{instance_name}_data_is_done', content)
    content = re.sub(rf'{instance_name}\.data', f'{instance_name}_data', content)
    content = re.sub(rf'{instance_name}\.ready', f'{instance_name}_ready', content)
    
    return content

def fix_worker_connections(content):
    """Fix VX_dxa_worker.sv port connections to flattened gmem_req/smem_wr."""
    
    # Fix gmem_req instantiation - replace .gmem_bus_if (gmem_bus_if) with flat wires
    # Pattern: .gmem_bus_if (gmem_bus_if),
    # We need to replace this with the flat wire connections
    
    # For gmem_req module, the port list now has flat wires:
    # gmem_bus_if_req_valid, gmem_bus_if_req_addr, etc.
    # We connect them to the worker's flat gmem_bus_if ports
    
    # Replace .gmem_bus_if (gmem_bus_if) with individual flat connections
    old_gmem = '.gmem_bus_if        (gmem_bus_if)'
    new_gmem = '''        .gmem_bus_if_req_valid   (gmem_bus_if_req_valid),
        .gmem_bus_if_req_addr    (gmem_bus_if_req_addr),
        .gmem_bus_if_req_data    (gmem_bus_if_req_data),
        .gmem_bus_if_req_byteen  (gmem_bus_if_req_byteen),
        .gmem_bus_if_req_attr    (gmem_bus_if_req_attr),
        .gmem_bus_if_req_tag_uuid (gmem_bus_if_req_tag_uuid),
        .gmem_bus_if_req_tag_value (gmem_bus_if_req_tag_value),
        .gmem_bus_if_req_ready   (gmem_bus_if_req_ready),
        .gmem_bus_if_rsp_valid   (gmem_bus_if_rsp_valid),
        .gmem_bus_if_rsp_data    (gmem_bus_if_rsp_data),
        .gmem_bus_if_rsp_tag_uuid (gmem_bus_if_rsp_tag_uuid),
        .gmem_bus_if_rsp_tag_value (gmem_bus_if_rsp_tag_value),
        .gmem_bus_if_rsp_ready   (gmem_bus_if_rsp_ready)'''
    content = content.replace(old_gmem, new_gmem)
    
    # Fix smem_wr connection
    old_smem = '.smem_bus_if           (smem_bus_if)'
    new_smem = '''        .smem_bus_if_req_valid  (smem_bus_if_req_valid),
        .smem_bus_if_req_addr   (smem_bus_if_req_addr),
        .smem_bus_if_req_data   (smem_bus_if_req_data),
        .smem_bus_if_req_byteen (smem_bus_if_req_byteen),
        .smem_bus_if_req_attr   (smem_bus_if_req_attr),
        .smem_bus_if_req_tag_uuid (smem_bus_if_req_tag_uuid),
        .smem_bus_if_req_tag_value (smem_bus_if_req_tag_value),
        .smem_bus_if_req_ready  (smem_bus_if_req_ready),
        .smem_bus_if_rsp_valid  (smem_bus_if_rsp_valid),
        .smem_bus_if_rsp_data   (smem_bus_if_rsp_data),
        .smem_bus_if_rsp_tag_uuid (smem_bus_if_rsp_tag_uuid),
        .smem_bus_if_rsp_tag_value (smem_bus_if_rsp_tag_value),
        .smem_bus_if_rsp_ready  (smem_bus_if_rsp_ready)'''
    content = content.replace(old_smem, new_smem)
    
    return content

# Process VX_dxa_desc_table.sv
with open('/tmp/dxa_flat/VX_dxa_desc_table.sv') as f:
    content = f.read()
content = flatten_dcr_bus(content, 'dcr_bus_if')
with open('/tmp/dxa_flat/VX_dxa_desc_table.sv', 'w') as f:
    f.write(content)
print("Flattened VX_dxa_desc_table.sv")

# Process VX_dxa_completion.sv
with open('/tmp/dxa_flat/VX_dxa_completion.sv') as f:
    content = f.read()
content = flatten_txbar_bus(content, 'txbar_bus_if')
with open('/tmp/dxa_flat/VX_dxa_completion.sv', 'w') as f:
    f.write(content)
print("Flattened VX_dxa_completion.sv")

# Process VX_dxa_worker.sv - fix connections
with open('/tmp/dxa_flat/VX_dxa_worker.sv') as f:
    content = f.read()
content = fix_worker_connections(content)
# Also flatten any remaining dcr_bus_if or txbar_bus_if refs
content = flatten_dcr_bus(content, 'dcr_bus_if')
content = flatten_txbar_bus(content, 'txbar_bus_if')
with open('/tmp/dxa_flat/VX_dxa_worker.sv', 'w') as f:
    f.write(content)
print("Fixed VX_dxa_worker.sv connections")

# Check for remaining interface refs
for fname in ['VX_dxa_desc_table.sv', 'VX_dxa_completion.sv', 'VX_dxa_worker.sv']:
    with open(f'/tmp/dxa_flat/{fname}') as f:
        content = f.read()
    remaining = [l.strip() for l in content.split('\n') 
                 if 'dcr_bus_if.' in l or 'txbar_bus_if.' in l or 'gmem_bus_if.' in l or 'smem_bus_if.' in l]
    if remaining:
        print(f"  {fname}: {len(remaining)} remaining refs")
        for l in remaining[:3]:
            print(f"    {l}")
    else:
        print(f"  {fname}: clean!")
