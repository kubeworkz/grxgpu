#!/usr/bin/env python3
"""Flatten VX_mem_bus_if in gmem_req and smem_wr modules."""
import re

def flatten_gmem_req():
    with open('/tmp/dxa_synth/VX_dxa_gmem_req.sv') as f:
        content = f.read()
    
    # Replace the interface port declaration with flat wires
    old_port = '    VX_mem_bus_if.master               gmem_bus_if,'
    new_ports = '''    output wire                          gmem_bus_if_req_valid,
    output wire [31:0]                   gmem_bus_if_req_addr,
    output wire [DATAW-1:0]              gmem_bus_if_req_data,
    output wire [DATAW/8-1:0]            gmem_bus_if_req_byteen,
    output wire [MEM_ATTR_W-1:0]         gmem_bus_if_req_attr,
    output wire [UUID_WIDTH-1:0]         gmem_bus_if_req_tag_uuid,
    output wire [MEM_TAG_WIDTH-1:0]      gmem_bus_if_req_tag_value,
    input  wire                          gmem_bus_if_req_ready,
    input  wire                          gmem_bus_if_rsp_valid,
    input  wire [DATAW-1:0]              gmem_bus_if_rsp_data,
    input  wire [UUID_WIDTH-1:0]         gmem_bus_if_rsp_tag_uuid,
    input  wire [MEM_TAG_WIDTH-1:0]      gmem_bus_if_rsp_tag_value,
    output wire                          gmem_bus_if_rsp_ready,'''
    content = content.replace(old_port, new_ports)
    
    # Remove the internal VX_mem_bus_if instance
    # Pattern: VX_mem_bus_if #( ... .*);
    content = re.sub(
        r'VX_mem_bus_if\s*#\([^)]*\)\s*\n\s*\(\s*\)\s*\n\s*gmem_bus_if\s*\(.*?\);',
        '// VX_mem_bus_if instance removed (flattened)',
        content,
        flags=re.DOTALL
    )
    
    # Replace hierarchical references
    content = content.replace('gmem_bus_if.req_valid', 'gmem_bus_if_req_valid')
    content = content.replace('gmem_bus_if.req_addr', 'gmem_bus_if_req_addr')
    content = content.replace('gmem_bus_if.req_data', 'gmem_bus_if_req_data')
    content = content.replace('gmem_bus_if.req_byteen', 'gmem_bus_if_req_byteen')
    content = content.replace('gmem_bus_if.req_attr', 'gmem_bus_if_req_attr')
    content = content.replace('gmem_bus_if.req_tag.uuid', 'gmem_bus_if_req_tag_uuid')
    content = content.replace('gmem_bus_if.req_tag.value', 'gmem_bus_if_req_tag_value')
    content = content.replace('gmem_bus_if.req_ready', 'gmem_bus_if_req_ready')
    content = content.replace('gmem_bus_if.rsp_valid', 'gmem_bus_if_rsp_valid')
    content = content.replace('gmem_bus_if.rsp_data', 'gmem_bus_if_rsp_data')
    content = content.replace('gmem_bus_if.rsp_ready', 'gmem_bus_if_rsp_ready')
    
    with open('/tmp/dxa_synth/VX_dxa_gmem_req.sv', 'w') as f:
        f.write(content)
    
    # Verify
    remaining = [l.strip() for l in content.split('\n') if 'gmem_bus_if.' in l]
    print(f"VX_dxa_gmem_req.sv: {len(remaining)} remaining refs")
    for l in remaining[:5]:
        print(f"  {l}")

def flatten_smem_wr():
    with open('/tmp/dxa_synth/VX_dxa_smem_wr.sv') as f:
        content = f.read()
    
    # Replace the interface port declaration with flat wires
    old_port = '    VX_mem_bus_if.master               smem_bus_if,'
    new_ports = '''    output wire                          smem_bus_if_req_valid,
    output wire [31:0]                   smem_bus_if_req_addr,
    output wire [DATAW-1:0]              smem_bus_if_req_data,
    output wire [DATAW/8-1:0]            smem_bus_if_req_byteen,
    output wire [MEM_ATTR_W-1:0]         smem_bus_if_req_attr,
    output wire [UUID_WIDTH-1:0]         smem_bus_if_req_tag_uuid,
    output wire [MEM_TAG_WIDTH-1:0]      smem_bus_if_req_tag_value,
    input  wire                          smem_bus_if_req_ready,
    input  wire                          smem_bus_if_rsp_valid,
    input  wire [DATAW-1:0]              smem_bus_if_rsp_data,
    input  wire [UUID_WIDTH-1:0]         smem_bus_if_rsp_tag_uuid,
    input  wire [MEM_TAG_WIDTH-1:0]      smem_bus_if_rsp_tag_value,
    output wire                          smem_bus_if_rsp_ready,'''
    content = content.replace(old_port, new_ports)
    
    # Replace hierarchical references
    content = content.replace('smem_bus_if.req_valid', 'smem_bus_if_req_valid')
    content = content.replace('smem_bus_if.req_data.rw', 'smem_bus_if_req_data_rw')
    content = content.replace('smem_bus_if.req_data.addr', 'smem_bus_if_req_addr')
    content = content.replace('smem_bus_if.req_data.data', 'smem_bus_if_req_data')
    content = content.replace('smem_bus_if.req_data.byteen', 'smem_bus_if_req_byteen')
    content = content.replace('smem_bus_if.req_data.attr', 'smem_bus_if_req_attr')
    content = content.replace('smem_bus_if.req_data.tag.uuid', 'smem_bus_if_req_tag_uuid')
    content = content.replace('smem_bus_if.req_data.tag.value', 'smem_bus_if_req_tag_value')
    content = content.replace('smem_bus_if.req_ready', 'smem_bus_if_req_ready')
    content = content.replace('smem_bus_if.rsp_valid', 'smem_bus_if_rsp_valid')
    content = content.replace('smem_bus_if.rsp_data', 'smem_bus_if_rsp_data')
    content = content.replace('smem_bus_if.rsp_ready', 'smem_bus_if_rsp_ready')
    
    with open('/tmp/dxa_synth/VX_dxa_smem_wr.sv', 'w') as f:
        f.write(content)
    
    # Verify
    remaining = [l.strip() for l in content.split('\n') if 'smem_bus_if.' in l]
    print(f"VX_dxa_smem_wr.sv: {len(remaining)} remaining refs")
    for l in remaining[:5]:
        print(f"  {l}")

if __name__ == '__main__':
    flatten_gmem_req()
    flatten_smem_wr()
