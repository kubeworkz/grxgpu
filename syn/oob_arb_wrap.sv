`include "VX_define.vh"

module oob_arb_wrap #(
    parameter NUM_INPUTS  = 32,
    parameter NUM_OUTPUTS = 2,
    parameter DATA_OOB    = 0
) (
    input  wire clk,
    input  wire reset,

    // Request side: inputs -> arb
    input  wire [NUM_INPUTS-1:0]                 req_valid_in,
    input  wire [NUM_INPUTS-1:0][629:0]          req_data_in,
    output wire [NUM_INPUTS-1:0]                 req_ready_in,

    // Request side: arb -> outputs
    output wire [NUM_OUTPUTS-1:0]                req_valid_out,
    output wire [NUM_OUTPUTS-1:0][629:0]         req_data_out,
    input  wire [NUM_OUTPUTS-1:0]                req_ready_out,

    // Response side: outputs -> arb (rsp switch)
    input  wire [NUM_OUTPUTS-1:0]                rsp_valid_in,
    input  wire [NUM_OUTPUTS-1:0][521:0]         rsp_data_in,
    output wire [NUM_OUTPUTS-1:0]                rsp_ready_in,

    // Response side: arb -> inputs
    output wire [NUM_INPUTS-1:0]                 rsp_valid_out,
    output wire [NUM_INPUTS-1:0][521:0]          rsp_data_out,
    input  wire [NUM_INPUTS-1:0]                 rsp_ready_out
);
    localparam DATA_SIZE = 64;
    localparam TAG_WIDTH = 10;

    VX_mem_bus_if #(
        .DATA_SIZE (DATA_SIZE),
        .TAG_WIDTH (TAG_WIDTH)
    ) bus_in_if [NUM_INPUTS]();

    VX_mem_bus_if #(
        .DATA_SIZE (DATA_SIZE),
        .TAG_WIDTH (TAG_WIDTH)
    ) bus_out_if [NUM_OUTPUTS]();

    for (genvar i = 0; i < NUM_INPUTS; ++i) begin : g_in
        assign bus_in_if[i].req_valid = req_valid_in[i];
        assign bus_in_if[i].req_data  = req_data_in[i];
        assign req_ready_in[i] = bus_in_if[i].req_ready;
        assign bus_in_if[i].rsp_ready = rsp_ready_out[i];
        assign rsp_valid_out[i] = bus_in_if[i].rsp_valid;
        assign rsp_data_out[i]  = bus_in_if[i].rsp_data;
    end

    for (genvar o = 0; o < NUM_OUTPUTS; ++o) begin : g_out
        assign bus_out_if[o].req_ready = req_ready_out[o];
        assign req_valid_out[o] = bus_out_if[o].req_valid;
        assign req_data_out[o]  = bus_out_if[o].req_data;
        assign bus_out_if[o].rsp_valid = rsp_valid_in[o];
        assign bus_out_if[o].rsp_data  = rsp_data_in[o];
        assign rsp_ready_in[o] = bus_out_if[o].rsp_ready;
    end

    oob_arb_top #(
        .NUM_INPUTS  (NUM_INPUTS),
        .NUM_OUTPUTS (NUM_OUTPUTS),
        .DATA_OOB    (DATA_OOB)
    ) u_arb (
        .clk        (clk),
        .reset      (reset),
        .bus_in_if  (bus_in_if),
        .bus_out_if (bus_out_if)
    );
endmodule