`include "VX_define.vh"

module oob_arb_top #(
    parameter NUM_INPUTS  = 32,
    parameter NUM_OUTPUTS = 2,
    parameter DATA_OOB    = 0
) (
    input  wire clk,
    input  wire reset,

    VX_mem_bus_if.slave  bus_in_if [NUM_INPUTS],
    VX_mem_bus_if.master bus_out_if [NUM_OUTPUTS]
);
    VX_mem_bus_arb #(
        .NUM_INPUTS  (NUM_INPUTS),
        .NUM_OUTPUTS (NUM_OUTPUTS),
        .DATA_SIZE   (64),
        .TAG_WIDTH   (10),
        .ARBITER     ("P"),
        .DATA_OOB    (DATA_OOB)
    ) u_arb (
        .clk        (clk),
        .reset      (reset),
        .bus_in_if  (bus_in_if),
        .bus_out_if (bus_out_if)
    );
endmodule