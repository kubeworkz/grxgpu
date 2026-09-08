#!/usr/bin/env python3
"""Fix generate blocks in VX_dxa_core.sv after flattening interface arrays."""
with open('/tmp/dxa_synth/VX_dxa_core.sv') as f:
    text = f.read()

# Fix the req_bus_valid generate block
old = """    wire [NUM_REQS-1:0] req_bus_valid;
    for (genvar i = 0; i < NUM_REQS; ++i) begin : g_req_valid
        assign req_bus_valid = req_bus_if[i].req_valid;
    end"""
new = """    wire req_bus_valid;
    assign req_bus_valid = req_bus_if.req_valid;"""
text = text.replace(old, new)

# Fix the worker_idle generate block
old = """    wire [`VX_CFG_NUM_DXA_CORES-1:0] worker_idle;
    for (genvar i = 0; i < `VX_CFG_NUM_DXA_CORES; ++i) begin : g_worker_idle
        assign worker_idle = worker_req_if[i].ready;
    end"""
new = """    wire worker_idle;
    assign worker_idle = worker_req_if.ready;"""
text = text.replace(old, new)

with open('/tmp/dxa_synth/VX_dxa_core.sv', 'w') as f:
    f.write(text)
print('Fixed generate blocks')
