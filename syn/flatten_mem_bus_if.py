#!/usr/bin/env python3
"""
Flatten VX_mem_bus_if in DXA modules for Yosys/Synlig compatibility.

This script:
1. Reads DXA source files
2. Finds VX_mem_bus_if port declarations and internal instances
3. Replaces them with flat wire declarations
4. Converts hierarchical struct references to flat wire names
"""
import re
import sys
import os

# VX_mem_bus_if field layout (from the interface definition)
# tag_t: uuid[UUID_WIDTH-1:0], value[TAG_WIDTH-UUID_WIDTH-1:0]
# req_data_t: rw, addr[ADDR_WIDTH-1:0], data[DATA_SIZE*8-1:0], byteen[DATA_SIZE-1:0], attr[ATTR_WIDTH-1:0], tag(tag_t)
# rsp_data_t: data[DATA_SIZE*8-1:0], tag(tag_t)
# Ports: req_valid, req_data, req_ready, rsp_valid, rsp_data, rsp_ready

# For our config: UUID_WIDTH=32, TAG_WIDTH=13, DATA_SIZE=64, ADDR_WIDTH=32, ATTR_WIDTH=2
FLAT_PORT_DEFS = {
    'req_valid': ('wire', ''),
    'req_addr': ('wire', '[31:0]'),
    'req_data': ('wire', '[511:0]'),
    'req_byteen': ('wire', '[63:0]'),
    'req_attr': ('wire', '[1:0]'),
    'req_tag_uuid': ('wire', '[31:0]'),
    'req_tag_value': ('wire', '[12:0]'),
    'req_ready': ('wire', ''),
    'rsp_valid': ('wire', ''),
    'rsp_data': ('wire', '[511:0]'),
    'rsp_tag_uuid': ('wire', '[31:0]'),
    'rsp_tag_value': ('wire', '[12:0]'),
    'rsp_ready': ('wire', ''),
}

def flatten_ports_in_portlist(content):
    """Replace VX_mem_bus_if ports in module port list with flat wires."""
    # Find module port list
    # Match: module name #(params) (ports);
    # We need to find VX_mem_bus_if entries and replace them
    
    # Pattern for VX_mem_bus_if port in portlist
    # VX_mem_bus_if.master gmem_bus_if,
    # VX_mem_bus_if #(params) .master gmem_bus_if)
    pattern = r'([ \t]*)VX_mem_bus_if\s*(?:#\([^)]*\))?\s*(?:\.(\w+)\s+)?(\w+)\s*([,\)])'
    
    def replace_port(match):
        indent = match.group(1)
        modport = match.group(2) or 'master'
        name = match.group(3)
        terminator = match.group(4)
        
        # Determine directions
        if modport == 'master':
            req_dir = 'output'
            rsp_dir = 'input'
        else:
            req_dir = 'input'
            rsp_dir = 'output'
        
        flat_lines = []
        for field, (rtype, width) in FLAT_PORT_DEFS.items():
            if field.startswith('req_') and field != 'req_ready':
                direction = req_dir
            elif field == 'req_ready':
                direction = rsp_dir
            elif field.startswith('rsp_') and field != 'rsp_ready':
                direction = rsp_dir
            elif field == 'rsp_ready':
                direction = req_dir
            else:
                direction = req_dir
            
            # Handle special naming for nested struct fields
            flat_name = f'{name}_{field}'
            flat_lines.append(f'{indent}{direction} {rtype} {width} {flat_name}')
        
        # Join with commas, last one gets the terminator
        result = ',\n'.join(flat_lines[:-1])
        result += ',\n' + flat_lines[-1].rstrip() + terminator
        return result
    
    content = re.sub(pattern, replace_port, content)
    return content

def flatten_instances(content):
    """Replace VX_mem_bus_if internal instances with flat wire declarations."""
    # Pattern: VX_mem_bus_if #(params) instance_name ();
    pattern = r'([ \t]*)VX_mem_bus_if\s*(?:#\([^)]*\))?\s+(\w+)\s*\(\);'
    
    def replace_instance(match):
        indent = match.group(1)
        name = match.group(2)
        
        flat_lines = []
        for field, (rtype, width) in FLAT_PORT_DEFS.items():
            flat_lines.append(f'{indent}{rtype} {width} {name}_{field};')
        
        return '\n'.join(flat_lines)
    
    content = re.sub(pattern, replace_instance, content)
    return content

def flatten_hier_refs(content, instance_names):
    """Replace hierarchical struct references with flat wire names."""
    for name in instance_names:
        # req_data struct
        content = re.sub(rf'{name}\.req_data\.rw\b', f'{name}_req_data_rw', content)
        content = re.sub(rf'{name}\.req_data\.addr\b', f'{name}_req_data_addr', content)
        content = re.sub(rf'{name}\.req_data\.data\b', f'{name}_req_data_data', content)
        content = re.sub(rf'{name}\.req_data\.byteen\b', f'{name}_req_data_byteen', content)
        content = re.sub(rf'{name}\.req_data\.attr\b', f'{name}_req_data_attr', content)
        # tag inside req_data
        content = re.sub(rf'{name}\.req_data\.tag\.uuid\b', f'{name}_req_tag_uuid', content)
        content = re.sub(rf'{name}\.req_data\.tag\.value\b', f'{name}_req_tag_value', content)
        # req control
        content = re.sub(rf'{name}\.req_valid\b', f'{name}_req_valid', content)
        content = re.sub(rf'{name}\.req_ready\b', f'{name}_req_ready', content)
        # rsp_data struct
        content = re.sub(rf'{name}\.rsp_data\.data\b', f'{name}_rsp_data', content)
        content = re.sub(rf'{name}\.rsp_data\.tag\.uuid\b', f'{name}_rsp_tag_uuid', content)
        content = re.sub(rf'{name}\.rsp_data\.tag\.value\b', f'{name}_rsp_tag_value', content)
        # rsp control
        content = re.sub(rf'{name}\.rsp_valid\b', f'{name}_rsp_valid', content)
        content = re.sub(rf'{name}\.rsp_ready\b', f'{name}_rsp_ready', content)
    
    return content

def flatten_submod_connections(content):
    """Fix submodule port connections that used interface references."""
    # Pattern: .req_data (instance.req_data),
    # The VX_mem_bus_slice and VX_mem_bus_arb take interface ports
    # We need to convert these to flat wire connections
    
    # For VX_mem_bus_slice: .bus_in_if (instance) -> needs flat connections
    # For now, just remove these connections (they're for the interface version)
    # The flattened version won't use VX_mem_bus_slice
    
    return content

def transform_file(filepath, output_dir=None):
    """Transform a single DXA file."""
    with open(filepath) as f:
        content = f.read()
    
    # Find all VX_mem_bus_if instances (ports + internal)
    port_instances = re.findall(
        r'VX_mem_bus_if\s*(?:#\([^)]*\))?\s*(?:\.(\w+)\s+)?(\w+)\s*[,\)]',
        content
    )
    internal_instances = re.findall(
        r'VX_mem_bus_if\s*(?:#\([^)]*\))?\s+(\w+)\s*\(\)',
        content
    )
    
    all_instances = [n for _, n in port_instances] + internal_instances
    all_instances = list(set(all_instances))  # deduplicate
    
    if not all_instances:
        print(f"  {os.path.basename(filepath)}: no VX_mem_bus_if, skipping")
        return None
    
    print(f"  {os.path.basename(filepath)}: instances={all_instances}")
    
    # Apply transformations
    content = flatten_ports_in_portlist(content)
    content = flatten_instances(content)
    content = flatten_hier_refs(content, all_instances)
    content = flatten_submod_connections(content)
    
    # Write output
    if output_dir:
        basename = os.path.basename(filepath)
        outpath = os.path.join(output_dir, basename)
        with open(outpath, 'w') as f:
            f.write(content)
        print(f"  -> {outpath}")
    
    return content

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: flatten_mem_bus_if.py <file.sv> [file2.sv ...]")
        print("       flatten_mem_bus_if.py --dir <output_dir> <file.sv> ...")
        sys.exit(1)
    
    output_dir = None
    files = []
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--dir':
            output_dir = sys.argv[i+1]
            i += 2
        else:
            files.append(sys.argv[i])
            i += 1
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    for filepath in files:
        transform_file(filepath, output_dir)
