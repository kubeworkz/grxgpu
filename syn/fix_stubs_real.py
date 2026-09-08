#!/usr/bin/env python3
"""Fix VX_mem_bus_arb and other stubs to use interface ports."""
import re

with open('/tmp/dxa_synth/vortex_stubs.sv') as f:
    text = f.read()

# Replace VX_mem_bus_arb stub with one that uses interface ports
old_arb = re.search(r'// VX_mem_bus_arb.*?^endmodule', text, re.MULTILINE | re.DOTALL)
if old_arb:
    new_arb = """module VX_mem_bus_arb import VX_gpu_pkg::*; #(
    parameter NUM_INPUTS   = 1,
    parameter NUM_OUTPUTS  = 1,
    parameter DATA_SIZE    = 4,
    parameter TAG_WIDTH    = 1,
    parameter TAG_SEL_IDX  = 0,
    parameter ATTR_WIDTH   = 0,
    parameter ADDR_WIDTH   = 32,
    parameter ARBITER      = "R",
    parameter REQ_OUT_BUF  = 0,
    parameter RSP_OUT_BUF  = 0,
    parameter STICKY       = 0,
    parameter DATA_OOB     = 0
)(
    input  wire clk,
    input  wire reset,
    VX_mem_bus_if.slave  bus_in_if  [NUM_INPUTS],
    VX_mem_bus_if.master bus_out_if [NUM_OUTPUTS]
);
    // Passthrough
    assign bus_out_if[0].req_valid = bus_in_if[0].req_valid;
    assign bus_in_if[0].req_ready  = bus_out_if[0].req_ready;
    assign bus_out_if[0].req_data  = bus_in_if[0].req_data;
    assign bus_in_if[0].rsp_valid  = bus_out_if[0].rsp_valid;
    assign bus_out_if[0].rsp_ready = bus_in_if[0].rsp_ready;
    assign bus_in_if[0].rsp_data   = bus_out_if[0].rsp_data;
endmodule"""
    text = text[:old_arb.start()] + new_arb + text[old_arb.end():]

# Fix VX_dp_ram stub to match actual ports
old_dpram = re.search(r'// VX_dp_ram.*?^endmodule', text, re.MULTILINE | re.DOTALL)
if old_dpram:
    new_dpram = """module VX_dp_ram #(
    parameter DATAW       = 1,
    parameter SIZE        = 1,
    parameter WRENW       = 1,
    parameter OUT_REG     = 0,
    parameter LUTRAM      = 0,
    parameter RDW_MODE    = "W",
    parameter ADDRW       = 8
)(
    input  wire               clk,
    input  wire               read,
    input  wire               write,
    input  wire [WRENW-1:0]   wren,
    input  wire [ADDRW-1:0]   waddr,
    input  wire [DATAW-1:0]   wdata,
    input  wire [ADDRW-1:0]   raddr,
    output wire [DATAW-1:0]   rdata
);
    reg [DATAW-1:0] mem [0:SIZE-1];
    always @(posedge clk) begin
        if (write) mem[waddr] <= wdata;
    end
    assign rdata = mem[raddr];
endmodule"""
    text = text[:old_dpram.start()] + new_dpram + text[old_dpram.end():]

# Fix VX_stream_dispatch stub to match actual ports
old_dispatch = re.search(r'// VX_stream_dispatch.*?^endmodule', text, re.MULTILINE | re.DOTALL)
if old_dispatch:
    new_dispatch = """module VX_stream_dispatch #(
    parameter NUM_INPUTS  = 1,
    parameter NUM_OUTPUTS = 1,
    parameter DATAW       = 1,
    parameter ARBITER     = "R",
    parameter BUFFERED    = 0,
    parameter OUT_BUF     = 0
)(
    input  wire clk,
    input  wire reset,
    input  wire [NUM_INPUTS-1:0]              valid_in,
    input  wire [NUM_INPUTS-1:0][DATAW-1:0]   data_in,
    output wire [NUM_INPUTS-1:0]              ready_in,
    output wire [NUM_OUTPUTS-1:0]             valid_out,
    output wire [NUM_OUTPUTS-1:0][DATAW-1:0]  data_out,
    input  wire [NUM_OUTPUTS-1:0]             ready_out
);
    assign valid_out = valid_in;
    assign data_out  = data_in;
    assign ready_in  = {NUM_INPUTS{ready_out[0]}};
endmodule"""
    text = text[:old_dispatch.start()] + new_dispatch + text[old_dispatch.end():]

# Fix VX_multiplier stub: remove DATAW param, add SIGNED param
old_mul = re.search(r'// VX_multiplier.*?^endmodule', text, re.MULTILINE | re.DOTALL)
if old_mul:
    new_mul = """module VX_multiplier #(
    parameter A_WIDTH = 1,
    parameter B_WIDTH = 1,
    parameter R_WIDTH = 1,
    parameter SIGNED  = 0,
    parameter LATENCY = 0
)(
    input  wire clk,
    input  wire enable,
    input  wire [A_WIDTH-1:0] dataa,
    input  wire [B_WIDTH-1:0] datab,
    output wire [R_WIDTH-1:0] result
);
    assign result = dataa * datab;
endmodule"""
    text = text[:old_mul.start()] + new_mul + text[old_mul.end():]

# Fix VX_priority_encoder: actual ports are data_in, onehot_out, index_out, valid_out
old_pe = re.search(r'// VX_priority_encoder.*?^endmodule', text, re.MULTILINE | re.DOTALL)
if old_pe:
    new_pe = """module VX_priority_encoder #(
    parameter N = 1,
    parameter REVERSE = 0
)(
    input  wire [N-1:0]           data_in,
    output wire                   valid_out,
    output wire [$clog2(N)-1:0]   index_out,
    output wire [N-1:0]           onehot_out
);
    assign valid_out = |data_in;
    assign index_out = 0;
    assign onehot_out = data_in & ~(data_in - 1);
endmodule"""
    text = text[:old_pe.start()] + new_pe + text[old_pe.end():]

# Fix VX_stream_arb: actual ports match DATAW not NUM_INPUTS*32
old_sa = re.search(r'// VX_stream_arb.*?^endmodule', text, re.MULTILINE | re.DOTALL)
if old_sa:
    new_sa = """module VX_stream_arb #(
    parameter NUM_INPUTS  = 1,
    parameter NUM_OUTPUTS = 1,
    parameter DATAW       = 1,
    parameter ARBITER     = "R",
    parameter BUFFERED    = 0,
    parameter OUT_BUF     = 0
)(
    input  wire clk,
    input  wire reset,
    input  wire [NUM_INPUTS-1:0]              valid_in,
    input  wire [NUM_INPUTS-1:0][DATAW-1:0]   data_in,
    output wire [NUM_INPUTS-1:0]              ready_in,
    output wire [NUM_OUTPUTS-1:0]             valid_out,
    output wire [NUM_OUTPUTS-1:0][DATAW-1:0]  data_out,
    input  wire [NUM_OUTPUTS-1:0]             ready_out,
    output wire [NUM_OUTPUTS-1:0][NUM_INPUTS-1:0] sel_out
);
    assign valid_out = valid_in;
    assign data_out  = data_in;
    assign ready_in  = {NUM_INPUTS{ready_out[0]}};
    assign sel_out   = 1;
endmodule"""
    text = text[:old_sa.start()] + new_sa + text[old_sa.end():]

with open('/tmp/dxa_synth/vortex_stubs.sv', 'w') as f:
    f.write(text)
print('All stubs fixed')
