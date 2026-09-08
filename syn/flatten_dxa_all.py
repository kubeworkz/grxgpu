#!/usr/bin/env python3
"""
Comprehensive DXA interface flattener for Yosys/Synlig synthesis.
Flattens VX_execute_if, VX_result_if, VX_mem_bus_if, VX_dxa_req_bus_if
in VX_dxa_unit.sv, VX_dxa_gmem_req.sv, VX_dxa_core.sv
"""
import re

def read(fname):
    with open(fname) as f:
        return f.read()

def write(fname, content):
    with open(fname, 'w') as f:
        f.write(content)

def count_refs(content, patterns):
    count = 0
    for p in patterns:
        count += len(re.findall(re.escape(p), content))
    return count

# ── VX_dxa_unit.sv: flatten execute_if and result_if ──
def flatten_unit():
    c = read('/tmp/dxa_synth/VX_dxa_unit.sv')
    
    # Replace interface ports with flat wires
    c = c.replace(
        '    VX_execute_if.slave     execute_if,',
        '    input  wire                execute_if_valid,\n'
        '    input  wire [4*32-1:0]    execute_if_data_rs1_data,\n'
        '    input  wire [4*32-1:0]    execute_if_data_rs2_data,\n'
        '    input  wire [4*32-1:0]    execute_if_data_rs3_data,\n'
        '    input  wire [32-1:0]      execute_if_data_header_uuid,\n'
        '    input  wire [32-1:0]      execute_if_data_header_wid,\n'
        '    output wire               execute_if_ready,'
    )
    c = c.replace(
        '    VX_result_if.master     result_if,',
        '    output wire               result_if_valid,\n'
        '    input  wire               result_if_ready,\n'
        '    output wire [32-1:0]      result_if_data_header_uuid,\n'
        '    output wire [32-1:0]      result_if_data_header_wid,\n'
        '    output wire [4*32-1:0]    result_if_data_data,'
    )
    
    # Replace hierarchical refs
    # execute_if.data.rs1_data[N] -> extract Nth 32-bit slice
    for i in range(4):
        c = c.replace(f'execute_if.data.rs1_data[{i}]', f'execute_if_data_rs1_data[{i}*32 +: 32]')
        c = c.replace(f'execute_if.data.rs2_data[{i}]', f'execute_if_data_rs2_data[{i}*32 +: 32]')
    # execute_if.data.rs3_data (unused but referenced)
    c = c.replace('execute_if.data.rs3_data', 'execute_if_data_rs3_data')
    c = c.replace('execute_if.data.header.uuid', 'execute_if_data_header_uuid')
    c = c.replace('execute_if.data.header.wid', 'execute_if_data_header_wid')
    # Generic .data.header fallback (for cap_hdr assignment)
    c = c.replace('execute_if.data.header', '{execute_if_data_header_uuid, execute_if_data_header_wid}')
    c = c.replace('execute_if.data.rs2_data', 'execute_if_data_rs2_data')
    c = c.replace('execute_if.valid', 'execute_if_valid')
    c = c.replace('execute_if.ready', 'execute_if_ready')
    c = c.replace('result_if.valid', 'result_if_valid')
    c = c.replace('result_if.ready', 'result_if_ready')
    c = c.replace('result_if.data.header', '{result_if_data_header_uuid, result_if_data_header_wid}')
    c = c.replace('result_if.data.data', 'result_if_data_data')
    
    # Remove UNUSED_VAR macro refs to flattened signals
    c = re.sub(r"`UNUSED_VAR\s*\(\s*execute_if_data_rs3_data\s*\)", '// execute_if_data_rs3_data unused', c)
    
    write('/tmp/dxa_synth/VX_dxa_unit.sv', c)
    remaining = count_refs(c, ['execute_if.', 'result_if.', 'VX_execute_if', 'VX_result_if'])
    print(f"VX_dxa_unit.sv: {remaining} remaining interface refs")

# ── VX_dxa_gmem_req.sv: flatten mem_bus_w internal instance ──
def flatten_gmem_req():
    c = read('/tmp/dxa_synth/VX_dxa_gmem_req.sv')
    
    # Replace the interface port
    c = c.replace(
        '    VX_mem_bus_if.master               gmem_bus_if,',
        '    output wire                          gmem_bus_if_req_valid,\n'
        '    output wire [31:0]                   gmem_bus_if_req_addr,\n'
        '    output wire [GMEM_BYTES*8-1:0]       gmem_bus_if_req_data,\n'
        '    output wire [GMEM_BYTES-1:0]         gmem_bus_if_req_byteen,\n'
        '    output wire [MEM_ATTR_W-1:0]         gmem_bus_if_req_attr,\n'
        '    output wire [UUID_WIDTH-1:0]         gmem_bus_if_req_tag_uuid,\n'
        '    output wire [GMEM_TAG_WIDTH-1:0]     gmem_bus_if_req_tag_value,\n'
        '    input  wire                          gmem_bus_if_req_ready,\n'
        '    input  wire                          gmem_bus_if_rsp_valid,\n'
        '    input  wire [GMEM_BYTES*8-1:0]       gmem_bus_if_rsp_data,\n'
        '    input  wire [GMEM_TAG_WIDTH-1:0]     gmem_bus_if_rsp_tag_value,\n'
        '    output wire                          gmem_bus_if_rsp_ready,'
    )
    
    # Remove the internal VX_mem_bus_if instance (multi-line)
    c = re.sub(
        r'    VX_mem_bus_if\s*#\(\s*\.DATA_SIZE\s*\(GMEM_BYTES\),\s*\.TAG_WIDTH\s*\(GMEM_TAG_WIDTH\)\s*\)\s*\n\s*mem_bus_w\s*\(\s*\)\s*;',
        '    // [FLAT] VX_mem_bus_if instance removed — signals are flat wires',
        c
    )
    
    # Replace hierarchical refs for internal mem_bus_w
    c = c.replace('mem_bus_w.req_ready', 'gmem_bus_if_req_ready')  # connects to output port
    c = c.replace('mem_bus_w.rsp_valid', 'gmem_bus_if_rsp_valid')
    c = c.replace('mem_bus_w.rsp_data.tag.value', 'gmem_bus_if_rsp_tag_value')
    c = c.replace('mem_bus_w.rsp_data.data', 'gmem_bus_if_rsp_data')
    c = c.replace('mem_bus_w.rsp_ready', 'gmem_bus_if_rsp_ready')
    c = c.replace('mem_bus_w.req_valid', 'gmem_bus_if_req_valid')
    c = c.replace('mem_bus_w.req_data.rw', '/* rw */ 1\'b0')  # read-only
    c = c.replace('mem_bus_w.req_data.addr', 'gmem_bus_if_req_addr')
    c = c.replace('mem_bus_w.req_data.data', 'gmem_bus_if_req_data')
    c = c.replace('mem_bus_w.req_data.byteen', 'gmem_bus_if_req_byteen')
    c = c.replace('mem_bus_w.req_data.attr', 'gmem_bus_if_req_attr')
    c = c.replace('mem_bus_w.req_data.tag.uuid', 'gmem_bus_if_req_tag_uuid')
    c = c.replace('mem_bus_w.req_data.tag.value', 'gmem_bus_if_req_tag_value')
    
    # Fix UNUSED_VAR macro
    c = re.sub(r"`UNUSED_VAR\s*\(\s*gmem_bus_if_rsp_tag_value\[GMEM_TAG_VALUEW-1:TAG_W\]\s*\)",
               '// upper tag bits unused', c)
    
    # Remove the STATIC_ASSERT that references removed interface params
    c = re.sub(r'`STATIC_ASSERT\([^)]+\)', '/* STATIC_ASSERT removed */', c)
    
    write('/tmp/dxa_synth/VX_dxa_gmem_req.sv', c)
    remaining = count_refs(c, ['mem_bus_w.', 'gmem_bus_if.', 'VX_mem_bus_if'])
    print(f"VX_dxa_gmem_req.sv: {remaining} remaining interface refs")

# ── VX_dxa_core.sv: flatten dcr_bus_if, mem_bus_if array instances ──
def flatten_core():
    c = read('/tmp/dxa_synth/VX_dxa_core.sv')
    
    # Replace dcr_bus_if port
    c = c.replace(
        '    VX_dcr_bus_if.slave dcr_bus_if,',
        '    input  wire        dcr_bus_if_req_valid,\n'
        '    input  wire [11:0] dcr_bus_if_req_addr,\n'
        '    input  wire [31:0] dcr_bus_if_req_data,\n'
        '    input  wire        dcr_bus_if_req_rw,\n'
        '    output wire [31:0] dcr_bus_if_rsp_data,'
    )
    
    # Replace gmem_bus_if array port
    c = c.replace(
        '    VX_mem_bus_if.master gmem_bus_if[GMEM_OUT_PORTS],',
        '    output wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_req_valid,\n'
        '    output wire [GMEM_OUT_PORTS*32-1:0]           gmem_bus_if_req_addr,\n'
        '    output wire [GMEM_OUT_PORTS*GMEM_BYTES*8-1:0] gmem_bus_if_req_data,\n'
        '    output wire [GMEM_OUT_PORTS*GMEM_BYTES-1:0]   gmem_bus_if_req_byteen,\n'
        '    output wire [GMEM_OUT_PORTS*MEM_ATTR_W-1:0]   gmem_bus_if_req_attr,\n'
        '    output wire [GMEM_OUT_PORTS*GMEM_TAG_WIDTH-1:0] gmem_bus_if_req_tag_uuid,\n'
        '    output wire [GMEM_OUT_PORTS*GMEM_TAG_WIDTH-1:0] gmem_bus_if_req_tag_value,\n'
        '    input  wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_req_ready,\n'
        '    input  wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_rsp_valid,\n'
        '    output wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_rsp_ready,'
    )
    
    # Replace smem_bus_if array port
    c = c.replace(
        '    VX_mem_bus_if.master smem_bus_if[1],',
        '    output wire                          smem_bus_if_req_valid,\n'
        '    output wire [31:0]                   smem_bus_if_req_addr,\n'
        '    output wire [DATAW-1:0]              smem_bus_if_req_data,\n'
        '    output wire [DATAW/8-1:0]            smem_bus_if_req_byteen,\n'
        '    output wire [MEM_ATTR_W-1:0]         smem_bus_if_req_attr,\n'
        '    output wire [UUID_WIDTH-1:0]         smem_bus_if_req_tag_uuid,\n'
        '    output wire [MEM_TAG_WIDTH-1:0]      smem_bus_if_req_tag_value,\n'
        '    input  wire                          smem_bus_if_req_ready,\n'
        '    input  wire                          smem_bus_if_rsp_valid,\n'
        '    input  wire [DATAW-1:0]              smem_bus_if_rsp_data,\n'
        '    input  wire [MEM_TAG_WIDTH-1:0]      smem_bus_if_rsp_tag_value,\n'
        '    output wire                          smem_bus_if_rsp_ready,'
    )
    
    # Remove internal VX_mem_bus_if instances
    c = re.sub(
        r'    VX_mem_bus_if\s*#\([^)]*\)\s*\n\s*\(\s*\)\s*\n\s*gm(?:em|em_w)\s*\w*\s*\(.*?\);',
        '    // [FLAT] internal VX_mem_bus_if instance removed',
        c,
        flags=re.DOTALL
    )
    # Also handle the simpler single-line pattern
    c = re.sub(
        r'    VX_mem_bus_if\s+#\(\s*\.DATA_SIZE\s*\([^)]+\),\s*\.TAG_WIDTH\s*\([^)]+\)\s*\)\s+\w+\s*\(\s*\)\s*;',
        '    // [FLAT] internal VX_mem_bus_if instance removed',
        c
    )
    
    # Remove VX_dxa_worker_req_if array instances
    c = re.sub(
        r'    VX_dxa_worker_req_if\s+\w+\s*\[\s*\w+\s*\]\s*\(\s*\)\s*;',
        '    // [FLAT] VX_dxa_worker_req_if instance removed',
        c
    )
    
    # Replace dcr_bus_if hierarchical refs
    c = c.replace('dcr_bus_if.req_valid', 'dcr_bus_if_req_valid')
    c = c.replace('dcr_bus_if.req_addr', 'dcr_bus_if_req_addr')
    c = c.replace('dcr_bus_if.req_data', 'dcr_bus_if_req_data')
    c = c.replace('dcr_bus_if.req_rw', 'dcr_bus_if_req_rw')
    c = c.replace('dcr_bus_if.rsp_data', 'dcr_bus_if_rsp_data')
    
    write('/tmp/dxa_synth/VX_dxa_core.sv', c)
    remaining = count_refs(c, ['dcr_bus_if.', 'mem_bus_if.', 'req_bus_if.', 'VX_mem_bus_if', 'VX_dxa_worker_req_if', 'VX_dcr_bus_if'])
    print(f"VX_dxa_core.sv: {remaining} remaining interface refs")

# ── VX_dxa_unit.sv: also flatten dxa_req_bus_if ──
def flatten_unit_req_bus():
    c = read('/tmp/dxa_synth/VX_dxa_unit.sv')
    
    # Replace dxa_req_bus_if port  
    c = c.replace(
        '    VX_dxa_req_bus_if.master dxa_req_bus_if',
        '    output wire        dxa_req_bus_if_req_valid,\n'
        '    input  wire        dxa_req_bus_if_req_ready,\n'
        '    output wire [127:0] dxa_req_bus_if_req_data'
    )
    
    # Replace hierarchical refs
    c = c.replace('dxa_req_bus_if.req_valid', 'dxa_req_bus_if_req_valid')
    c = c.replace('dxa_req_bus_if.req_ready', 'dxa_req_bus_if_req_ready')
    c = c.replace('dxa_req_bus_if.req_data.wid', 'dxa_req_bus_if_req_data[31:0]')
    c = c.replace('dxa_req_bus_if.req_data.smem_addr', 'dxa_req_bus_if_req_data[63:32]')
    c = c.replace('dxa_req_bus_if.req_data.meta', 'dxa_req_bus_if_req_data[95:64]')
    c = c.replace('dxa_req_bus_if.req_data.coords', 'dxa_req_bus_if_req_data[127:96]')
    c = c.replace('dxa_req_bus_if.req_data', 'dxa_req_bus_if_req_data')
    
    write('/tmp/dxa_synth/VX_dxa_unit.sv', c)
    remaining = count_refs(c, ['dxa_req_bus_if.', 'VX_dxa_req_bus_if'])
    print(f"VX_dxa_unit.sv: {remaining} remaining req_bus_if refs")

if __name__ == '__main__':
    flatten_unit()
    flatten_gmem_req()
    flatten_core()
    flatten_unit_req_bus()
