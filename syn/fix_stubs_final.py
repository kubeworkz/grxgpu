#!/usr/bin/env python3
"""Fix remaining synthesis issues: elastic_buffer stub, interface fields, $countones."""
import re

# Fix VX_elastic_buffer stub: wrong port names
with open('/tmp/dxa_synth/vortex_stubs.sv') as f:
    text = f.read()

# Replace the elastic_buffer module with correct port names
old_eb = """module VX_elastic_buffer #(
    parameter DATAW  = 1,
    parameter SIZE   = 2,
    parameter LUTRAM = 0
)(
    input  wire clk,
    input  wire reset,
    // input side
    output wire in_ready,
    input  wire in_valid,
    input  wire [DATAW-1:0] in_data,
    // output side
    input  wire out_ready,
    output wire out_valid,
    output wire [DATAW-1:0] out_data
);"""

new_eb = """module VX_elastic_buffer #(
    parameter DATAW   = 1,
    parameter SIZE    = 1,
    parameter OUT_REG = 0,
    parameter LUTRAM  = 0
)(
    input  wire clk,
    input  wire reset,
    input  wire valid_in,
    output wire ready_in,
    input  wire [DATAW-1:0] data_in,
    output wire [DATAW-1:0] data_out,
    input  wire ready_out,
    output wire valid_out
);"""

text = text.replace(old_eb, new_eb)

# Fix: replace assign statements to use correct port names
text = text.replace(
    '    assign in_ready  = out_ready;\n    assign out_valid = in_valid;\n    assign out_data  = in_data;',
    '    assign ready_in  = ready_out;\n    assign valid_out = valid_in;\n    assign data_out  = data_in;'
)

with open('/tmp/dxa_synth/vortex_stubs.sv', 'w') as f:
    f.write(text)
print('Fixed VX_elastic_buffer stub')

# Fix $countones in VX_dxa_setup.sv -> use popcount stub
with open('/tmp/dxa_synth/VX_dxa_setup.sv') as f:
    text = f.read()
# Replace $countones(x) with a simple function call
# Actually, let's just define count_ones as a local function
text = text.replace('$countones(', 'count_ones(')
# Add the function definition at the top of the module body
text = text.replace(
    'module VX_dxa_setup',
    '''function automatic integer count_ones(input integer val);
    integer i, cnt;
    begin
        cnt = 0;
        for (i = 0; i < 32; i = i + 1)
            if (val[i]) cnt = cnt + 1;
        count_ones = cnt;
    end
endfunction

module VX_dxa_setup'''
)
with open('/tmp/dxa_synth/VX_dxa_setup.sv', 'w') as f:
    f.write(text)
print('Fixed $countones in VX_dxa_setup.sv')

# Fix execute_if.data.header - the VX_execute_if needs a 'header' field
# Check what execute_if actually defines
print('Done')
