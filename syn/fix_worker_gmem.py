#!/usr/bin/env python3
"""Complete interface flattening for VX_dxa_worker.sv and VX_dxa_gmem_req.sv."""
import re, os

os.chdir("/tmp/dxa_synth")

# ============================================================
# Fix VX_dxa_worker.sv
# ============================================================
fname = "VX_dxa_worker.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    
    # 1. Replace interface port declaration with flat wires
    # VX_mem_bus_if.master smem_bus_if  ->  flat wire ports
    old_port = "VX_mem_bus_if.master smem_bus_if"
    new_ports = """    output wire                        smem_bus_if_req_valid,
    output wire [SMEM_ADDR_WIDTH-1:0]  smem_bus_if_req_addr,
    output wire [SMEM_BYTES*8-1:0]     smem_bus_if_req_data,
    output wire [SMEM_BYTES-1:0]       smem_bus_if_req_byteen,
    output wire [MEM_ATTR_W-1:0]       smem_bus_if_req_attr,
    output wire [UUID_WIDTH-1:0]       smem_bus_if_req_tag_uuid,
    output wire [GMEM_TAG_WIDTH-1:0]   smem_bus_if_req_tag_value,
    input  wire                        smem_bus_if_req_ready,
    input  wire                        smem_bus_if_rsp_valid,
    input  wire [SMEM_BYTES*8-1:0]     smem_bus_if_rsp_data,
    input  wire [UUID_WIDTH-1:0]       smem_bus_if_rsp_tag_uuid,
    input  wire [GMEM_TAG_WIDTH-1:0]   smem_bus_if_rsp_tag_value,
    output wire                        smem_bus_if_rsp_ready"""
    c = c.replace(old_port, new_ports)
    
    # 2. Fix submodule instantiation: .gmem_bus_if(gmem_bus_if)
    # The gmem_bus_if port is already flat, but the submodule connection
    # references the old interface name
    # VX_dxa_gmem_req uses interface ports - we need to connect flat wires
    c = c.replace('.gmem_bus_if        (gmem_bus_if),',
                  '.gmem_bus_if_req_valid(gmem_bus_if_req_valid),\n        .gmem_bus_if_req_addr(gmem_bus_if_req_addr),\n        .gmem_bus_if_req_data(gmem_bus_if_req_data),\n        .gmem_bus_if_req_byteen(gmem_bus_if_req_byteen),\n        .gmem_bus_if_req_attr(gmem_bus_if_req_attr),\n        .gmem_bus_if_req_tag_uuid(gmem_bus_if_req_tag_uuid),\n        .gmem_bus_if_req_tag_value(gmem_bus_if_req_tag_value),\n        .gmem_bus_if_req_ready(gmem_bus_if_req_ready),\n        .gmem_bus_if_rsp_valid(gmem_bus_if_rsp_valid),\n        .gmem_bus_if_rsp_data(gmem_bus_if_rsp_data),\n        .gmem_bus_if_rsp_tag_uuid(gmem_bus_if_rsp_tag_uuid),\n        .gmem_bus_if_rsp_tag_value(gmem_bus_if_rsp_tag_value),\n        .gmem_bus_if_rsp_ready(gmem_bus_if_rsp_ready),')
    
    # 3. Fix submodule instantiation: .smem_bus_if(smem_bus_if)
    c = c.replace('.smem_bus_if           (smem_bus_if)',
                  '.smem_bus_if_req_valid(smem_bus_if_req_valid),\n        .smem_bus_if_req_addr(smem_bus_if_req_addr),\n        .smem_bus_if_req_data(smem_bus_if_req_data),\n        .smem_bus_if_req_byteen(smem_bus_if_req_byteen),\n        .smem_bus_if_req_attr(smem_bus_if_req_attr),\n        .smem_bus_if_req_tag_uuid(smem_bus_if_req_tag_uuid),\n        .smem_bus_if_req_tag_value(smem_bus_if_req_tag_value),\n        .smem_bus_if_req_ready(smem_bus_if_req_ready),\n        .smem_bus_if_rsp_valid(smem_bus_if_rsp_valid),\n        .smem_bus_if_rsp_data(smem_bus_if_rsp_data),\n        .smem_bus_if_rsp_tag_uuid(smem_bus_if_rsp_tag_uuid),\n        .smem_bus_if_rsp_tag_value(smem_bus_if_rsp_tag_value),\n        .smem_bus_if_rsp_ready(smem_bus_if_rsp_ready)')
    
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname}")

# ============================================================
# Fix VX_dxa_gmem_req.sv
# ============================================================
fname = "VX_dxa_gmem_req.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    
    # 1. Remove the internal interface instance declaration
    # VX_mem_bus_if #(...) mem_bus_w ();
    # This creates an internal interface - we need to replace it with flat wires
    old_inst = """    VX_mem_bus_if #(
        .DATA_SIZE   (GMEM_BYTES),
        .TAG_WIDTH   (33),
        .REQ_OUT_BUF (3),
        .RSP_OUT_BUF (0)
    ) mem_bus_w ();"""
    new_wires = """    // Flat wires replacing mem_bus_w interface instance
    wire        mem_bus_w_req_valid;
    wire [31:0] mem_bus_w_req_addr;
    wire [GMEM_BYTES*8-1:0] mem_bus_w_req_data;
    wire [GMEM_BYTES-1:0] mem_bus_w_req_byteen;
    wire [MEM_ATTR_W-1:0] mem_bus_w_req_attr;
    wire [TAG_W-1:0] mem_bus_w_req_tag;
    wire        mem_bus_w_req_ready;
    wire        mem_bus_w_rsp_valid;
    wire [GMEM_BYTES*8-1:0] mem_bus_w_rsp_data;
    wire [TAG_W-1:0] mem_bus_w_rsp_tag;
    wire        mem_bus_w_rsp_ready;"""
    c = c.replace(old_inst, new_wires)
    
    # 2. Fix internal interface member accesses
    # mem_bus_w.req_ready -> mem_bus_w_req_ready
    c = c.replace('mem_bus_w.req_ready', 'mem_bus_w_req_ready')
    c = c.replace('mem_bus_w.rsp_valid', 'mem_bus_w_rsp_valid')
    c = c.replace('mem_bus_w.rsp_ready', 'mem_bus_w_rsp_ready')
    c = c.replace('mem_bus_w.req_valid', 'mem_bus_w_req_valid')
    c = c.replace('mem_bus_w.req_data.rw', 'mem_bus_w_req_data_rw')  # These are struct member accesses
    c = c.replace('mem_bus_w.req_data.addr', 'mem_bus_w_req_addr')
    c = c.replace('mem_bus_w.req_data.data', 'mem_bus_w_req_data')
    c = c.replace('mem_bus_w.req_data.byteen', 'mem_bus_w_req_byteen')
    c = c.replace('mem_bus_w.req_data.attr', 'mem_bus_w_req_attr')
    
    # 3. Fix submodule instantiation: .bus_in_if(mem_bus_w) -> flat wire connections
    c = c.replace('.bus_in_if  (mem_bus_w),',
                  '.bus_in_req_valid(mem_bus_w_req_valid),\n        .bus_in_req_addr(mem_bus_w_req_addr),\n        .bus_in_req_data(mem_bus_w_req_data),\n        .bus_in_req_byteen(mem_bus_w_req_byteen),\n        .bus_in_req_attr(mem_bus_w_req_attr),\n        .bus_in_req_tag(mem_bus_w_req_tag),\n        .bus_in_req_ready(mem_bus_w_req_ready),\n        .bus_in_rsp_valid(mem_bus_w_rsp_valid),\n        .bus_in_rsp_data(mem_bus_w_rsp_data),\n        .bus_in_rsp_tag(mem_bus_w_rsp_tag),\n        .bus_in_rsp_ready(mem_bus_w_rsp_ready),')
    
    # 4. Fix submodule instantiation: .bus_out_if(gmem_bus_if) -> flat wire connections
    c = c.replace('.bus_out_if (gmem_bus_if)',
                  '.bus_out_req_valid(gmem_bus_if_req_valid),\n        .bus_out_req_addr(gmem_bus_if_req_addr),\n        .bus_out_req_data(gmem_bus_if_req_data),\n        .bus_out_req_byteen(gmem_bus_if_req_byteen),\n        .bus_out_req_attr(gmem_bus_if_req_attr),\n        .bus_out_req_tag(gmem_bus_if_req_tag_uuid),\n        .bus_out_req_ready(gmem_bus_if_req_ready),\n        .bus_out_rsp_valid(gmem_bus_if_rsp_valid),\n        .bus_out_rsp_data(gmem_bus_if_rsp_data),\n        .bus_out_rsp_tag(gmem_bus_if_rsp_tag_uuid),\n        .bus_out_rsp_ready(gmem_bus_if_rsp_ready)')
    
    # 5. Fix struct member accesses that weren't caught
    # mem_bus_w.req_data.rw was replaced with mem_bus_w_req_data_rw above
    # But it should be a separate wire for the rw field
    # Let's check if this pattern exists
    if 'mem_bus_w_req_data_rw' in c:
        # Add the rw wire and fix the assignment
        c = c.replace('mem_bus_w_req_data_rw', 'mem_bus_w_req_rw')
        # Add rw wire declaration after the other mem_bus_w wires
        c = c.replace('    wire [GMEM_BYTES-1:0] mem_bus_w_req_byteen;',
                      '    wire [GMEM_BYTES-1:0] mem_bus_w_req_byteen;\n    wire mem_bus_w_req_rw;')
    
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname}")

print("Done")
