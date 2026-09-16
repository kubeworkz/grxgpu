#!/usr/bin/env python3
"""Add missing ports to VX_dxa_req_arb.sv."""
import os
os.chdir("/tmp/dxa_synth")

fname = "VX_dxa_req_arb.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    
    # Add missing ports before the closing );
    old_end = "    output wire [127:0] bus_out_if_req_data"
    new_ports = """    output wire [31:0] bus_in_if_req_addr,
    output wire [7:0] bus_in_if_req_byteen,
    output wire [7:0] bus_in_if_req_attr,
    output wire [127:0] bus_in_if_req_tag,
    input  wire        bus_in_if_rsp_valid,
    input  wire [127:0] bus_in_if_rsp_data,
    input  wire [127:0] bus_in_if_rsp_tag,
    output wire        bus_in_if_rsp_ready,
    input  wire [31:0] bus_out_if_req_addr,
    input  wire [7:0] bus_out_if_req_byteen,
    input  wire [7:0] bus_out_if_req_attr,
    input  wire [127:0] bus_out_if_req_tag,
    output wire        bus_out_if_rsp_valid,
    output wire [127:0] bus_out_if_rsp_data,
    output wire [127:0] bus_out_if_rsp_tag,
    input  wire        bus_out_if_rsp_ready,
    output wire [127:0] bus_out_if_req_data"""
    c = c.replace(old_end, new_ports)
    
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname}")
