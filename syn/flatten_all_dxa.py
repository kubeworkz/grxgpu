#!/usr/bin/env python3
"""
Comprehensive DXA interface flattener for Yosys/Synlig synthesis.
Flattens ALL interface types across ALL DXA modules.

Interface → flat wire mapping:
  VX_mem_bus_if: req_valid, req_data.{rw,addr,data,byteen,attr,tag.uuid,tag.value}, req_ready, rsp_valid, rsp_data.{data,tag.uuid,tag.value}, rsp_ready
  VX_dcr_bus_if: req_valid, req_data.{rw,addr,data}, rsp_valid, rsp_data.data
  VX_txbar_bus_if: valid, data.{addr,is_done}, ready
  VX_execute_if: valid, data.header.{uuid,wid}, data.rs1_data, data.rs2_data, data.rs3_data, ready
  VX_result_if: valid, data.header.{uuid,wid}, data.data, ready
  VX_dxa_worker_req_if: valid, req_data, desc_data, ready
  VX_dxa_req_bus_if: req_valid, req_data, req_ready
"""
import re
import sys
import os

DXA_DIR = '/tmp/dxa_synth'

def read(fname):
    with open(os.path.join(DXA_DIR, fname)) as f:
        return f.read()

def write(fname, content):
    with open(os.path.join(DXA_DIR, fname), 'w') as f:
        f.write(content)

def flatten_mem_bus(content, inst_name, direction):
    """Flatten a VX_mem_bus_if instance.
    direction: 'master' (outputs req, inputs rsp) or 'slave' (inputs req, outputs rsp)
    """
    prefix = inst_name

    # Port declarations for master (output req, input rsp):
    # req_valid, req_data_*, req_ready (input), rsp_valid (input), rsp_data_* (input), rsp_ready (output)
    # Port declarations for slave (input req, output rsp):
    # req_valid (input), req_data_* (input), req_ready (output), rsp_valid (output), rsp_data_* (output), rsp_ready (input)

    # Replace the interface port declaration
    # Pattern: VX_mem_bus_if.master/varname or VX_mem_bus_if #(params).master/varname
    # Handle both simple and parameterized forms

    # Simple form: VX_mem_bus_if.master varname,
    port_pattern = re.compile(
        r'(\s*)VX_mem_bus_if\s*#\([^)]*\)\s*\.(master|slave)\s+(\w+)\s*,',
        re.MULTILINE
    )
    def replace_port(m):
        indent = m.group(1)
        dir_ = m.group(2)
        name = m.group(3)
        return flatten_mem_bus_port(indent, name, dir_)
    content = port_pattern.sub(replace_port, content)

    # Also handle: VX_mem_bus_if.master varname (without params)
    port_pattern2 = re.compile(
        r'(\s*)VX_mem_bus_if\s*\.(master|slave)\s+(\w+)\s*,',
        re.MULTILINE
    )
    content = port_pattern2.sub(replace_port, content)

    # Also handle last port (no trailing comma)
    port_pattern3 = re.compile(
        r'(\s*)VX_mem_bus_if\s*#\([^)]*\)\s*\.(master|slave)\s+(\w+)\s*\)',
        re.MULTILINE
    )
    def replace_port_last(m):
        indent = m.group(1)
        dir_ = m.group(2)
        name = m.group(3)
        return flatten_mem_bus_port(indent, name, dir_).rstrip(',\n') + '\n)'
    content = port_pattern3.sub(replace_port_last, content)

    # Remove internal VX_mem_bus_if instances (parameterized)
    content = re.sub(
        r'(\s*)VX_mem_bus_if\s*#\([^)]*\)\s*\n\s*(\w+)\s*\[\s*([^\]]+)\]\s*\(\s*\)\s*;',
        lambda m: f'{m.group(1)}// [FLAT] VX_mem_bus_if array {m.group(2)} removed\n',
        content
    )
    content = re.sub(
        r'(\s*)VX_mem_bus_if\s*#\([^)]*\)\s*\n\s*(\w+)\s*\(\s*\)\s*;',
        lambda m: f'{m.group(1)}// [FLAT] VX_mem_bus_if {m.group(2)} removed\n',
        content
    )
    content = re.sub(
        r'(\s*)VX_mem_bus_if\s*\.(master|slave)\s+(\w+)\s*\[\s*([^\]]+)\]\s*\(\s*\)\s*;',
        lambda m: f'{m.group(1)}// [FLAT] VX_mem_bus_if array {m.group(3)} removed\n',
        content
    )

    # Replace hierarchical references: inst.field.subfield
    # req_data.tag.uuid → inst_req_tag_uuid
    # req_data.tag.value → inst_req_tag_value
    # req_data.addr → inst_req_addr
    # req_data.data → inst_req_data
    # req_data.byteen → inst_req_byteen
    # req_data.attr → inst_req_attr
    # req_data.rw → inst_req_rw (usually not used, assign 0)
    # rsp_data.data → inst_rsp_data
    # rsp_data.tag.uuid → inst_rsp_tag_uuid
    # rsp_data.tag.value → inst_rsp_tag_value

    # Order matters: do tag.sub-fields before tag, data before struct
    for field, flat in [
        ('req_data.tag.uuid', 'req_tag_uuid'),
        ('req_data.tag.value', 'req_tag_value'),
        ('req_data.addr', 'req_addr'),
        ('req_data.data', 'req_data'),
        ('req_data.byteen', 'req_byteen'),
        ('req_data.attr', 'req_attr'),
        ('req_data.rw', 'req_rw'),
        ('rsp_data.tag.uuid', 'rsp_tag_uuid'),
        ('rsp_data.tag.value', 'rsp_tag_value'),
        ('rsp_data.data', 'rsp_data'),
        ('req_valid', 'req_valid'),
        ('req_ready', 'req_ready'),
        ('rsp_valid', 'rsp_valid'),
        ('rsp_ready', 'rsp_ready'),
    ]:
        content = content.replace(f'{inst_name}.{field}', f'{prefix}_{flat}')

    # Also handle array indexing: inst[i].field
    for field, flat in [
        ('req_data.tag.uuid', 'req_tag_uuid'),
        ('req_data.tag.value', 'req_tag_value'),
        ('req_data.addr', 'req_addr'),
        ('req_data.data', 'req_data'),
        ('req_data.byteen', 'req_byteen'),
        ('req_data.attr', 'req_attr'),
        ('req_ready', 'req_ready'),
        ('rsp_valid', 'rsp_valid'),
        ('rsp_data.data', 'rsp_data'),
        ('rsp_data.tag.uuid', 'rsp_tag_uuid'),
        ('rsp_data.tag.value', 'rsp_tag_value'),
        ('rsp_ready', 'rsp_ready'),
    ]:
        content = re.sub(
            rf'{inst_name}\[(\w+)\]\.{re.escape(field)}',
            rf'{prefix}[\1]_{flat}',
            content
        )

    return content

def flatten_mem_bus_port(indent, name, direction):
    """Generate flat wire declarations for a VX_mem_bus_if port."""
    wires = []
    # Master: outputs req, inputs rsp
    if direction == 'master':
        wires.append(f'{indent}output wire                          {name}_req_valid,')
        wires.append(f'{indent}output wire [31:0]                   {name}_req_addr,')
        wires.append(f'{indent}output wire [GMEM_BYTES*8-1:0]       {name}_req_data,')
        wires.append(f'{indent}output wire [GMEM_BYTES-1:0]         {name}_req_byteen,')
        wires.append(f'{indent}output wire [MEM_ATTR_W-1:0]         {name}_req_attr,')
        wires.append(f'{indent}output wire [UUID_WIDTH-1:0]         {name}_req_tag_uuid,')
        wires.append(f'{indent}output wire [GMEM_TAG_WIDTH-1:0]     {name}_req_tag_value,')
        wires.append(f'{indent}input  wire                          {name}_req_ready,')
        wires.append(f'{indent}input  wire                          {name}_rsp_valid,')
        wires.append(f'{indent}input  wire [GMEM_BYTES*8-1:0]       {name}_rsp_data,')
        wires.append(f'{indent}input  wire [UUID_WIDTH-1:0]         {name}_rsp_tag_uuid,')
        wires.append(f'{indent}input  wire [GMEM_TAG_WIDTH-1:0]     {name}_rsp_tag_value,')
        wires.append(f'{indent}output wire                          {name}_rsp_ready,')
    else:  # slave
        wires.append(f'{indent}input  wire                          {name}_req_valid,')
        wires.append(f'{indent}input  wire [31:0]                   {name}_req_addr,')
        wires.append(f'{indent}input  wire [GMEM_BYTES*8-1:0]       {name}_req_data,')
        wires.append(f'{indent}input  wire [GMEM_BYTES-1:0]         {name}_req_byteen,')
        wires.append(f'{indent}input  wire [MEM_ATTR_W-1:0]         {name}_req_attr,')
        wires.append(f'{indent}input  wire [UUID_WIDTH-1:0]         {name}_req_tag_uuid,')
        wires.append(f'{indent}input  wire [GMEM_TAG_WIDTH-1:0]     {name}_req_tag_value,')
        wires.append(f'{indent}output wire                          {name}_req_ready,')
        wires.append(f'{indent}input  wire                          {name}_rsp_valid,')
        wires.append(f'{indent}input  wire [GMEM_BYTES*8-1:0]       {name}_rsp_data,')
        wires.append(f'{indent}input  wire [UUID_WIDTH-1:0]         {name}_rsp_tag_uuid,')
        wires.append(f'{indent}input  wire [GMEM_TAG_WIDTH-1:0]     {name}_rsp_tag_value,')
        wires.append(f'{indent}input  wire                          {name}_rsp_ready,')
    return '\n'.join(wires) + ','


def flatten_dcr_bus(content, inst_name):
    """Flatten VX_dcr_bus_if."""
    # Port: VX_dcr_bus_if.slave/master name
    content = re.sub(
        rf'(\s*)VX_dcr_bus_if\.(slave|master)\s+(\w+)\s*,',
        lambda m: flatten_dcr_port(m.group(1), m.group(3), m.group(2)),
        content
    )

    # Hierarchical refs
    for field, flat in [
        ('req_data.rw', 'req_rw'),
        ('req_data.addr', 'req_addr'),
        ('req_data.data', 'req_data'),
        ('rsp_data.data', 'rsp_data'),
        ('req_valid', 'req_valid'),
        ('rsp_valid', 'rsp_valid'),
    ]:
        content = content.replace(f'{inst_name}.{field}', f'{inst_name}_{flat}')

    return content

def flatten_dcr_port(indent, name, direction):
    wires = []
    if direction == 'slave':
        wires.append(f'{indent}input  wire        {name}_req_valid,')
        wires.append(f'{indent}input  wire        {name}_req_rw,')
        wires.append(f'{indent}input  wire [11:0] {name}_req_addr,')
        wires.append(f'{indent}input  wire [31:0] {name}_req_data,')
        wires.append(f'{indent}output wire [31:0] {name}_rsp_data,')
    else:
        wires.append(f'{indent}output wire        {name}_req_valid,')
        wires.append(f'{indent}output wire        {name}_req_rw,')
        wires.append(f'{indent}output wire [11:0] {name}_req_addr,')
        wires.append(f'{indent}output wire [31:0] {name}_req_data,')
        wires.append(f'{indent}input  wire [31:0] {name}_rsp_data,')
    return '\n'.join(wires) + ','


def flatten_txbar_bus(content, inst_name):
    """Flatten VX_txbar_bus_if."""
    content = re.sub(
        rf'(\s*)VX_txbar_bus_if\.(master|slave)\s+(\w+)\s*[,\)]',
        lambda m: flatten_txbar_port(m.group(1), m.group(3), m.group(2), m.group(0).endswith(')')),
        content
    )

    for field, flat in [
        ('data.addr', 'data_addr'),
        ('data.is_done', 'data_is_done'),
        ('valid', 'valid'),
        ('ready', 'ready'),
    ]:
        content = content.replace(f'{inst_name}.{field}', f'{inst_name}_{flat}')

    return content

def flatten_txbar_port(indent, name, direction, is_last):
    wires = []
    comma = '' if is_last else ','
    if direction == 'master':
        wires.append(f'{indent}output wire        {name}_valid,')
        wires.append(f'{indent}output wire [BAR_ADDR_W-1:0] {name}_data_addr,')
        wires.append(f'{indent}output wire        {name}_data_is_done,')
        wires.append(f'{indent}input  wire        {name}_ready{comma}')
    else:
        wires.append(f'{indent}input  wire        {name}_valid,')
        wires.append(f'{indent}input  wire [BAR_ADDR_W-1:0] {name}_data_addr,')
        wires.append(f'{indent}input  wire        {name}_data_is_done,')
        wires.append(f'{indent}output wire        {name}_ready{comma}')
    return '\n'.join(wires)


def flatten_execute_if(content, inst_name):
    """Flatten VX_execute_if — data_t is sfu_execute_t in DXA context."""
    content = re.sub(
        rf'(\s*)VX_execute_if\s*#\([^)]*\)\s*\.(slave|master)\s+(\w+)\s*[,\)]',
        lambda m: flatten_execute_port(m.group(1), m.group(3), m.group(2), m.group(0).endswith(')')),
        content
    )
    content = re.sub(
        rf'(\s*)VX_execute_if\.(slave|master)\s+(\w+)\s*[,\)]',
        lambda m: flatten_execute_port(m.group(1), m.group(3), m.group(2), m.group(0).endswith(')')),
        content
    )

    # Hierarchical refs — sfu_execute_t has: header.{uuid,wid}, rs1_data[3:0], rs2_data[3:0], rs3_data
    for i in range(4):
        content = content.replace(f'{inst_name}.data.rs1_data[{i}]', f'{inst_name}_rs1_data_{i}')
        content = content.replace(f'{inst_name}.data.rs2_data[{i}]', f'{inst_name}_rs2_data_{i}')
    content = content.replace(f'{inst_name}.data.rs3_data', f'{inst_name}_rs3_data')
    content = content.replace(f'{inst_name}.data.header.uuid', f'{inst_name}_hdr_uuid')
    content = content.replace(f'{inst_name}.data.header.wid', f'{inst_name}_hdr_wid')
    # Catch-all for .data.header (used in cap_hdr assignment)
    content = content.replace(f'{inst_name}.data.header', f'{{{inst_name}_hdr_uuid, {inst_name}_hdr_wid}}')
    content = content.replace(f'{inst_name}.data.rs2_data', f'{inst_name}_rs2_data')
    content = content.replace(f'{inst_name}.data.rs1_data', f'{inst_name}_rs1_data')
    content = content.replace(f'{inst_name}.valid', f'{inst_name}_valid')
    content = content.replace(f'{inst_name}.ready', f'{inst_name}_ready')

    return content

def flatten_execute_port(indent, name, direction, is_last):
    wires = []
    comma = '' if is_last else ','
    if direction == 'slave':
        wires.append(f'{indent}input  wire        {name}_valid,')
        wires.append(f'{indent}input  wire [31:0] {name}_hdr_uuid,')
        wires.append(f'{indent}input  wire [31:0] {name}_hdr_wid,')
        wires.append(f'{indent}input  wire [3:0][31:0] {name}_rs1_data,')
        wires.append(f'{indent}input  wire [3:0][31:0] {name}_rs2_data,')
        wires.append(f'{indent}input  wire [3:0][31:0] {name}_rs3_data,')
        wires.append(f'{indent}output wire        {name}_ready{comma}')
    else:
        wires.append(f'{indent}output wire        {name}_valid,')
        wires.append(f'{indent}output wire [31:0] {name}_hdr_uuid,')
        wires.append(f'{indent}output wire [31:0] {name}_hdr_wid,')
        wires.append(f'{indent}output wire [3:0][31:0] {name}_rs1_data,')
        wires.append(f'{indent}output wire [3:0][31:0] {name}_rs2_data,')
        wires.append(f'{indent}output wire [3:0][31:0] {name}_rs3_data,')
        wires.append(f'{indent}input  wire        {name}_ready{comma}')
    return '\n'.join(wires)


def flatten_result_if(content, inst_name):
    """Flatten VX_result_if."""
    content = re.sub(
        rf'(\s*)VX_result_if\s*#\([^)]*\)\s*\.(master|slave)\s+(\w+)\s*[,\)]',
        lambda m: flatten_result_port(m.group(1), m.group(3), m.group(2), m.group(0).endswith(')')),
        content
    )
    content = re.sub(
        rf'(\s*)VX_result_if\.(master|slave)\s+(\w+)\s*[,\)]',
        lambda m: flatten_result_port(m.group(1), m.group(3), m.group(2), m.group(0).endswith(')')),
        content
    )

    content = content.replace(f'{inst_name}.data.header', f'{inst_name}_data_header')
    content = content.replace(f'{inst_name}.data.data', f'{inst_name}_data_data')
    content = content.replace(f'{inst_name}.valid', f'{inst_name}_valid')
    content = content.replace(f'{inst_name}.ready', f'{inst_name}_ready')

    return content

def flatten_result_port(indent, name, direction, is_last):
    wires = []
    comma = '' if is_last else ','
    if direction == 'master':
        wires.append(f'{indent}output wire        {name}_valid,')
        wires.append(f'{indent}output wire [31:0] {name}_data_header,')
        wires.append(f'{indent}output wire [127:0] {name}_data_data,')
        wires.append(f'{indent}input  wire        {name}_ready{comma}')
    else:
        wires.append(f'{indent}input  wire        {name}_valid,')
        wires.append(f'{indent}input  wire [31:0] {name}_data_header,')
        wires.append(f'{indent}input  wire [127:0] {name}_data_data,')
        wires.append(f'{indent}output wire        {name}_ready{comma}')
    return '\n'.join(wires)


def flatten_worker_req_if(content, inst_name):
    """Flatten VX_dxa_worker_req_if."""
    content = re.sub(
        rf'(\s*)VX_dxa_worker_req_if\.(slave|master)\s+(\w+)\s*[,\)]',
        lambda m: flatten_worker_req_port(m.group(1), m.group(3), m.group(2), m.group(0).endswith(')')),
        content
    )

    content = content.replace(f'{inst_name}.valid', f'{inst_name}_valid')
    content = content.replace(f'{inst_name}.req_data', f'{inst_name}_req_data')
    content = content.replace(f'{inst_name}.desc_data', f'{inst_name}_desc_data')
    content = content.replace(f'{inst_name}.ready', f'{inst_name}_ready')

    # Remove internal interface array instances
    content = re.sub(
        rf'(\s*)VX_dxa_worker_req_if\s+(\w+)\s*\[\s*([^\]]+)\]\s*\(\s*\)\s*;',
        lambda m: f'{m.group(1)}// [FLAT] VX_dxa_worker_req_if array {m.group(2)} removed\n',
        content
    )
    content = re.sub(
        rf'(\s*)VX_dxa_worker_req_if\s+(\w+)\s*\(\s*\)\s*;',
        lambda m: f'{m.group(1)}// [FLAT] VX_dxa_worker_req_if {m.group(2)} removed\n',
        content
    )

    # Handle array indexing: inst[i].field
    for field, flat in [
        ('req_data', 'req_data'),
        ('desc_data', 'desc_data'),
        ('valid', 'valid'),
        ('ready', 'ready'),
    ]:
        content = re.sub(
            rf'{inst_name}\[(\w+)\]\.{re.escape(field)}',
            rf'{inst_name}[\1]_{flat}',
            content
        )

    return content

def flatten_worker_req_port(indent, name, direction, is_last):
    wires = []
    comma = '' if is_last else ','
    # dxa_req_data_t is wide, use a generic width
    if direction == 'slave':
        wires.append(f'{indent}input  wire        {name}_valid,')
        wires.append(f'{indent}input  wire [255:0] {name}_req_data,')
        wires.append(f'{indent}input  wire [575:0] {name}_desc_data,')
        wires.append(f'{indent}output wire        {name}_ready{comma}')
    else:
        wires.append(f'{indent}output wire        {name}_valid,')
        wires.append(f'{indent}output wire [255:0] {name}_req_data,')
        wires.append(f'{indent}output wire [575:0] {name}_desc_data,')
        wires.append(f'{indent}input  wire        {name}_ready{comma}')
    return '\n'.join(wires)


def flatten_req_bus_if(content, inst_name):
    """Flatten VX_dxa_req_bus_if."""
    content = re.sub(
        rf'(\s*)VX_dxa_req_bus_if\.(slave|master)\s+(\w+)\s*(\[([^\]]+)\])?\s*[,\)]',
        lambda m: flatten_req_bus_port(m.group(1), m.group(3), m.group(2), m.group(4), m.group(0).endswith(')')),
        content
    )

    # Remove internal instances
    content = re.sub(
        rf'(\s*)VX_dxa_req_bus_if\s+(\w+)\s*\[\s*([^\]]+)\]\s*\(\s*\)\s*;',
        lambda m: f'{m.group(1)}// [FLAT] VX_dxa_req_bus_if array {m.group(2)} removed\n',
        content
    )
    content = re.sub(
        rf'(\s*)VX_dxa_req_bus_if\s+(\w+)\s*\(\s*\)\s*;',
        lambda m: f'{m.group(1)}// [FLAT] VX_dxa_req_bus_if {m.group(2)} removed\n',
        content
    )

    # Hierarchical refs
    content = content.replace(f'{inst_name}.req_valid', f'{inst_name}_req_valid')
    content = content.replace(f'{inst_name}.req_ready', f'{inst_name}_req_ready')
    content = content.replace(f'{inst_name}.req_data.wid', f'{inst_name}_req_data_wid')
    content = content.replace(f'{inst_name}.req_data.smem_addr', f'{inst_name}_req_data_smem_addr')
    content = content.replace(f'{inst_name}.req_data.meta', f'{inst_name}_req_data_meta')
    content = content.replace(f'{inst_name}.req_data.coords', f'{inst_name}_req_data_coords')
    content = content.replace(f'{inst_name}.req_data', f'{inst_name}_req_data')

    # Handle array indexing
    for field, flat in [
        ('req_valid', 'req_valid'),
        ('req_ready', 'req_ready'),
        ('req_data', 'req_data'),
    ]:
        content = re.sub(
            rf'{inst_name}\[(\w+)\]\.{re.escape(field)}',
            rf'{inst_name}[\1]_{flat}',
            content
        )

    return content

def flatten_req_bus_port(indent, name, direction, array_dim, is_last):
    wires = []
    comma = '' if is_last else ','
    if direction == 'slave':
        wires.append(f'{indent}input  wire        {name}_req_valid,')
        wires.append(f'{indent}input  wire [127:0] {name}_req_data,')
        wires.append(f'{indent}output wire        {name}_req_ready{comma}')
    else:
        wires.append(f'{indent}output wire        {name}_req_valid,')
        wires.append(f'{indent}input  wire        {name}_req_ready,')
        wires.append(f'{indent}output wire [127:0] {name}_req_data{comma}')
    return '\n'.join(wires)


def process_module(fname):
    """Apply all interface flattening to a DXA module."""
    content = read(fname)

    # Track which interfaces are used
    has_mem_bus = bool(re.search(r'VX_mem_bus_if', content))
    has_dcr = bool(re.search(r'VX_dcr_bus_if', content))
    has_txbar = bool(re.search(r'VX_txbar_bus_if', content))
    has_execute = bool(re.search(r'VX_execute_if', content))
    has_result = bool(re.search(r'VX_result_if', content))
    has_worker_req = bool(re.search(r'VX_dxa_worker_req_if', content))
    has_req_bus = bool(re.search(r'VX_dxa_req_bus_if', content))

    if not (has_mem_bus or has_dcr or has_txbar or has_execute or has_result or has_worker_req or has_req_bus):
        return  # No interfaces to flatten

    # Find all interface instance names
    if has_mem_bus:
        # Find all VX_mem_bus_if instances (both ports and internal)
        for m in re.finditer(r'VX_mem_bus_if\s*(?:#\([^)]*\))?\s*\.(master|slave)\s+(\w+)', content):
            inst = m.group(2)
            dir_ = m.group(1)
            content = flatten_mem_bus(content, inst, dir_)

    if has_dcr:
        for m in re.finditer(r'VX_dcr_bus_if\.(slave|master)\s+(\w+)', content):
            inst = m.group(2)
            content = flatten_dcr_bus(content, inst)

    if has_txbar:
        for m in re.finditer(r'VX_txbar_bus_if\.(master|slave)\s+(\w+)', content):
            inst = m.group(2)
            content = flatten_txbar_bus(content, inst)

    if has_execute:
        for m in re.finditer(r'VX_execute_if\s*(?:#\([^)]*\))?\s*\.(slave|master)\s+(\w+)', content):
            inst = m.group(2)
            content = flatten_execute_if(content, inst)

    if has_result:
        for m in re.finditer(r'VX_result_if\s*(?:#\([^)]*\))?\s*\.(master|slave)\s+(\w+)', content):
            inst = m.group(2)
            content = flatten_result_if(content, inst)

    if has_worker_req:
        for m in re.finditer(r'VX_dxa_worker_req_if\.(slave|master)\s+(\w+)', content):
            inst = m.group(2)
            content = flatten_worker_req_if(content, inst)

    if has_req_bus:
        for m in re.finditer(r'VX_dxa_req_bus_if\.(slave|master)\s+(\w+)', content):
            inst = m.group(2)
            content = flatten_req_bus_if(content, inst)

    write(fname, content)

    # Verify: count remaining interface refs (excluding comments)
    remaining = len(re.findall(
        r'(?<!// ).*(?:VX_mem_bus_if|VX_dcr_bus_if|VX_txbar_bus_if|VX_execute_if|VX_result_if|VX_dxa_worker_req_if|VX_dxa_req_bus_if)\b(?!.*interface\b)',
        content
    ))
    print(f'{fname}: {remaining} remaining non-comment interface refs')


# DXA modules to flatten (excluding the interface definitions themselves)
MODULES = [
    'VX_dxa_addr_gen.sv',      # has VX_mem_bus_if (internal instance)
    'VX_dxa_completion.sv',     # has VX_txbar_bus_if
    'VX_dxa_core.sv',           # has VX_dcr_bus_if, VX_mem_bus_if, VX_dxa_req_bus_if, VX_dxa_worker_req_if
    'VX_dxa_desc_table.sv',     # has VX_dcr_bus_if
    'VX_dxa_dispatch.sv',       # has VX_dxa_worker_req_if
    'VX_dxa_gmem_req.sv',       # has VX_mem_bus_if
    'VX_dxa_req_arb.sv',        # has VX_dxa_req_bus_if
    'VX_dxa_setup.sv',          # may have interfaces
    'VX_dxa_smem_wr.sv',        # has VX_mem_bus_if
    'VX_dxa_unit.sv',           # has VX_execute_if, VX_result_if, VX_dxa_req_bus_if
    'VX_dxa_watchdog.sv',       # may have interfaces
    'VX_dxa_worker.sv',         # has VX_dxa_worker_req_if, VX_mem_bus_if
]

if __name__ == '__main__':
    for mod in MODULES:
        try:
            process_module(mod)
        except Exception as e:
            print(f'{mod}: ERROR - {e}')
