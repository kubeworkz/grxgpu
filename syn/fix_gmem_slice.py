#!/usr/bin/env python3
"""Fix remaining issues in DXA synthesis:
1. Replace VX_mem_bus_slice interface instance with flat passthrough
2. Add VX_stream_dispatch and VX_multiplier stubs
"""
import os
os.chdir("/tmp/dxa_synth")

# Fix VX_dxa_gmem_req.sv: replace the VX_mem_bus_slice instance
with open("VX_dxa_gmem_req.sv") as f:
    content = f.read()

# Replace the VX_mem_bus_slice instance with direct passthrough
old_slice = """    VX_mem_bus_slice #(
        .DATA_SIZE   (GMEM_BYTES),
        .TAG_WIDTH   (33),
        .REQ_OUT_BUF (3),
        .RSP_OUT_BUF (0)
    ) gmem_out_slice (
        .clk        (clk),
        .reset      (reset),
        .bus_in_if  (/* flat */),
        .bus_out_if (gmem_bus_if)
    );"""

new_slice = """    // VX_mem_bus_slice replaced with direct passthrough (interface was flattened)
    // passthrough: gmem_bus_if outputs are already driven by this module's logic"""

content = content.replace(old_slice, new_slice)
with open("VX_dxa_gmem_req.sv", "w") as f:
    f.write(content)
print("Fixed VX_dxa_gmem_req.sv: removed VX_mem_bus_slice instance")

# Add missing stubs to vortex_stubs.sv
with open("vortex_stubs.sv") as f:
    stubs = f.read()

# Add VX_stream_dispatch stub
stream_dispatch = """
// ============================================================
// VX_stream_dispatch — parameterized stream dispatch
// ============================================================
module VX_stream_dispatch #(
    parameter NUM_INPUTS  = 1,
    parameter NUM_OUTPUTS = 1,
    parameter DATAW       = 1,
    parameter ARBITER     = "R",
    parameter BUFFERED    = 0
) (
    input  wire clk,
    input  wire reset,
    input  wire [NUM_INPUTS-1:0]          valid_in,
    input  wire [NUM_INPUTS*DATAW-1:0]    data_in,
    output wire [NUM_INPUTS-1:0]          ready_in,
    output wire [NUM_OUTPUTS-1:0]         valid_out,
    output wire [NUM_OUTPUTS*DATAW-1:0]   data_out,
    input  wire [NUM_OUTPUTS-1:0]         ready_out
);
    // Passthrough: connect input 0 to output 0
    assign valid_out[0] = valid_in[0];
    assign data_out[DATAW-1:0] = data_in[DATAW-1:0];
    assign ready_in[0] = ready_out[0];
    genvar i;
    generate
        for (i = 1; i < NUM_INPUTS; i = i + 1) begin : gen_ready
            assign ready_in[i] = 1'b0;
        end
        for (i = 1; i < NUM_OUTPUTS; i = i + 1) begin : gen_valid
            assign valid_out[i] = 1'b0;
            assign data_out[i*DATAW +: DATAW] = {DATAW{1'b0}};
        end
    endgenerate
endmodule
"""

# Add VX_multiplier stub
multiplier_stub = """
// ============================================================
// VX_multiplier — parameterized integer multiplier
// ============================================================
module VX_multiplier #(
    parameter A_WIDTH  = 32,
    parameter B_WIDTH  = 32,
    parameter R_WIDTH  = 32,
    parameter LATENCY  = 0,
    parameter SIGNED   = 0
) (
    input  wire             clk,
    input  wire             reset,
    input  wire             enable,
    input  wire [A_WIDTH-1:0] dataa,
    input  wire [B_WIDTH-1:0] datab,
    output wire [R_WIDTH-1:0] result
);
    assign result = dataa * datab;
endmodule
"""

# Append stubs before end of file
stubs = stubs.rstrip() + "\n" + stream_dispatch + "\n" + multiplier_stub + "\n"
with open("vortex_stubs.sv", "w") as f:
    f.write(stubs)
print("Added VX_stream_dispatch and VX_multiplier stubs")
