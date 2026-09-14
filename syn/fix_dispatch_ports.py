#!/usr/bin/env python3
import os
os.chdir("/tmp/dxa_synth")

fname = "VX_dxa_dispatch.sv"
with open(fname) as f:
    c = f.read()

# Replace interface array ports with flat wire ports
old_ports = """    VX_dxa_worker_req_if.slave  req_in  [NUM_INPUTS],
    VX_dxa_worker_req_if.master req_out [NUM_OUTPUTS]"""

new_ports = """    input  wire [NUM_INPUTS-1:0]              req_in_valid,
    input  wire [NUM_INPUTS*DATAW-1:0]        req_in_req_data,
    input  wire [NUM_INPUTS*320-1:0]          req_in_desc_data,
    output wire [NUM_INPUTS-1:0]              req_in_ready,
    output wire [NUM_OUTPUTS-1:0]             req_out_valid,
    output wire [NUM_OUTPUTS*DATAW-1:0]       req_out_req_data,
    output wire [NUM_OUTPUTS*320-1:0]         req_out_desc_data,
    input  wire [NUM_OUTPUTS-1:0]             req_out_ready"""

c = c.replace(old_ports, new_ports)

# Replace $bits() with hardcoded values
c = c.replace("$bits(dxa_req_data_t)", "128")
c = c.replace("$bits(dxa_desc_t)", "320")

with open(fname, "w") as f:
    f.write(c)
print(f"Fixed {fname}")
