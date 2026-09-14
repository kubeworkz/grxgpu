#!/usr/bin/env python3
import os
os.chdir("/tmp/dxa_synth")

fname = "VX_dxa_core.sv"
with open(fname) as f:
    c = f.read()

# Replace interface array ports with flat wire ports
old_ports = """    VX_mem_bus_if.master gmem_bus_if[GMEM_OUT_PORTS],
    VX_mem_bus_if.master smem_bus_if[1],"""

new_ports = """    output wire                          gmem_bus_if_req_valid,
    output wire [31:0]                   gmem_bus_if_req_addr,
    output wire [GMEM_BYTES*8-1:0]       gmem_bus_if_req_data,
    output wire [GMEM_BYTES-1:0]         gmem_bus_if_req_byteen,
    output wire [MEM_ATTR_W-1:0]         gmem_bus_if_req_attr,
    output wire [UUID_WIDTH-1:0]         gmem_bus_if_req_tag_uuid,
    output wire [GMEM_TAG_WIDTH-1:0]     gmem_bus_if_req_tag_value,
    input  wire                          gmem_bus_if_req_ready,
    input  wire                          gmem_bus_if_rsp_valid,
    input  wire [GMEM_BYTES*8-1:0]       gmem_bus_if_rsp_data,
    input  wire [UUID_WIDTH-1:0]         gmem_bus_if_rsp_tag_uuid,
    input  wire [GMEM_TAG_WIDTH-1:0]     gmem_bus_if_rsp_tag_value,
    output wire                          gmem_bus_if_rsp_ready,
    output wire                          smem_bus_if_req_valid,
    output wire [SMEM_ADDR_WIDTH-1:0]    smem_bus_if_req_addr,
    output wire [SMEM_BYTES*8-1:0]       smem_bus_if_req_data,
    output wire [SMEM_BYTES-1:0]         smem_bus_if_req_byteen,
    output wire [MEM_ATTR_W-1:0]         smem_bus_if_req_attr,
    output wire [UUID_WIDTH-1:0]         smem_bus_if_req_tag_uuid,
    output wire [GMEM_TAG_WIDTH-1:0]     smem_bus_if_req_tag_value,
    input  wire                          smem_bus_if_req_ready,
    input  wire                          smem_bus_if_rsp_valid,
    input  wire [SMEM_BYTES*8-1:0]       smem_bus_if_rsp_data,
    input  wire [UUID_WIDTH-1:0]         smem_bus_if_rsp_tag_uuid,
    input  wire [GMEM_TAG_WIDTH-1:0]     smem_bus_if_rsp_tag_value,
    output wire                          smem_bus_if_rsp_ready,"""

c = c.replace(old_ports, new_ports)

with open(fname, "w") as f:
    f.write(c)
print("Fixed VX_dxa_core.sv port list")
