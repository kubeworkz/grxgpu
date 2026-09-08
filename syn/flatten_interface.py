#!/usr/bin/env python3
"""
Flatten VX_mem_bus_if SV interface into plain wire bundles.

Converts:
  VX_mem_bus_if.master gmem_bus_if
to:
  wire        gmem_bus_if_req_valid,
  wire [31:0] gmem_bus_if_req_addr,
  ...

And converts hierarchical references like:
  mem_bus_w.req_data.rw      -> mem_bus_w_req_data_rw
  mem_bus_w.rsp_data.tag.uuid -> mem_bus_w_rsp_data_tag_uuid
"""
import re
import sys

# VX_mem_bus_if field definitions (from the interface source)
# tag_t: uuid, value
# req_data_t: rw, addr, data, byteen, attr, tag (which has uuid, value)
# rsp_data_t: data, tag (which has uuid, value)

def flatten_interface_reference(instance_name, field_path):
    """Convert hierarchical interface reference to flat wire name.
    
    Examples:
      mem_bus_w.req_data.rw       -> mem_bus_w_req_data_rw
      mem_bus_w.rsp_data.tag.uuid -> mem_bus_w_rsp_data_tag_uuid
      gmem_bus_if.req_valid       -> gmem_bus_if_req_valid
    """
    # Replace dots with underscores
    flat = field_path.replace('.', '_')
    return f"{instance_name}_{flat}"

def generate_flat_ports(interface_name, instance_name, direction_map):
    """Generate flat wire declarations for an interface instance.
    
    Returns list of (direction, width, name) tuples.
    """
    ports = []
    
    # Request channel
    ports.append(('output', '', f'{instance_name}_req_valid'))
    ports.append(('output', '[31:0]', f'{instance_name}_req_addr'))
    ports.append(('output', '[DATA_SIZE*8-1:0]', f'{instance_name}_req_data'))
    ports.append(('output', '[DATA_SIZE-1:0]', f'{instance_name}_req_byteen'))
    ports.append(('output', '[ATTR_WIDTH-1:0]', f'{instance_name}_req_attr'))
    ports.append(('output', '[UUID_WIDTH-1:0]', f'{instance_name}_req_tag_uuid'))
    ports.append(('output', '[TAG_VALUEW-1:0]', f'{instance_name}_req_tag_value'))
    ports.append(('input', '', f'{instance_name}_req_ready'))
    
    # Response channel
    ports.append(('input', '', f'{instance_name}_rsp_valid'))
    ports.append(('input', '[DATA_SIZE*8-1:0]', f'{instance_name}_rsp_data'))
    ports.append(('input', '[UUID_WIDTH-1:0]', f'{instance_name}_rsp_tag_uuid'))
    ports.append(('input', '[TAG_VALUEW-1:0]', f'{instance_name}_rsp_tag_value'))
    ports.append(('output', '', f'{instance_name}_rsp_ready'))
    
    return ports

def transform_module(content, interface_instances):
    """Transform a module to use flat wires instead of interface ports."""
    lines = content.split('\n')
    result = []
    
    for line in lines:
        transformed = False
        
        for iface_name, instance_name in interface_instances:
            # Replace interface port declarations
            # Pattern: VX_mem_bus_if.master instance_name,
            # Pattern: VX_mem_bus_if #(...) instance_name
            if re.search(rf'VX_mem_bus_if\s*(#\([^)]*\))?\s*\.{iface_name}\s+{instance_name}', line):
                # Generate flat port declarations
                flat_ports = generate_flat_ports(iface_name, instance_name, {})
                for i, (dir, width, name) in enumerate(flat_ports):
                    comma = ',' if i < len(flat_ports) - 1 else ''
                    result.append(f'    {dir} {width} {name}{comma}')
                transformed = True
                break
        
        if not transformed:
            # Replace hierarchical references
            # Pattern: instance_name.req_data.field
            # Pattern: instance_name.rsp_data.field
            # Pattern: instance_name.req_valid
            # Pattern: instance_name.rsp_valid
            for iface_name, instance_name in interface_instances:
                # Replace struct member access
                line = re.sub(
                    rf'{instance_name}\.req_data\.rw',
                    f'{instance_name}_req_data_rw',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.req_data\.addr',
                    f'{instance_name}_req_data_addr',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.req_data\.data',
                    f'{instance_name}_req_data_data',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.req_data\.byteen',
                    f'{instance_name}_req_data_byteen',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.req_data\.attr',
                    f'{instance_name}_req_data_attr',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.req_data\.tag\.uuid',
                    f'{instance_name}_req_tag_uuid',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.req_data\.tag\.value',
                    f'{instance_name}_req_tag_value',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.req_valid',
                    f'{instance_name}_req_valid',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.req_ready',
                    f'{instance_name}_req_ready',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.rsp_data\.data',
                    f'{instance_name}_rsp_data',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.rsp_data\.tag\.uuid',
                    f'{instance_name}_rsp_tag_uuid',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.rsp_data\.tag\.value',
                    f'{instance_name}_rsp_tag_value',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.rsp_valid',
                    f'{instance_name}_rsp_valid',
                    line
                )
                line = re.sub(
                    rf'{instance_name}\.rsp_ready',
                    f'{instance_name}_rsp_ready',
                    line
                )
        
        result.append(line)
    
    return '\n'.join(result)

def transform_submodule_ports(content, instance_name):
    """Transform submodule instantiation ports to match flat interface."""
    # Pattern: .req_data (instance.req_data),
    # becomes: .req_data (instance.req_data_data),
    content = re.sub(
        rf'\.req_data\s*\({instance_name}\.req_data\)',
        f'.req_data ({instance_name}_req_data_data)',
        content
    )
    content = re.sub(
        rf'\.req_valid\s*\({instance_name}\.req_valid\)',
        f'.req_valid ({instance_name}_req_valid)',
        content
    )
    content = re.sub(
        rf'\.req_ready\s*\({instance_name}\.req_ready\)',
        f'.req_ready ({instance_name}_req_ready)',
        content
    )
    content = re.sub(
        rf'\.rsp_data\s*\({instance_name}\.rsp_data\)',
        f'.rsp_data ({instance_name}_rsp_data)',
        content
    )
    content = re.sub(
        rf'\.rsp_valid\s*\({instance_name}\.rsp_valid\)',
        f'.rsp_valid ({instance_name}_rsp_valid)',
        content
    )
    content = re.sub(
        rf'\.rsp_ready\s*\({instance_name}\.rsp_ready\)',
        f'.rsp_ready ({instance_name}_rsp_ready)',
        content
    )
    return content

if __name__ == '__main__':
    # Example usage
    if len(sys.argv) < 2:
        print("Usage: flatten_interface.py <module.sv>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        content = f.read()
    
    # Find interface instances in the module
    # Pattern: VX_mem_bus_if #(...) instance_name ();
    instances = re.findall(r'VX_mem_bus_if\s*(?:#\([^)]*\))?\s+(\w+)\s*\(\)', content)
    
    print(f"Found {len(instances)} VX_mem_bus_if instances: {instances}")
    
    # Transform the content
    interface_instances = [('master', inst) for inst in instances]
    transformed = transform_module(content, interface_instances)
    
    print(transformed)
