// Module stubs for Yosys slang synthesis
// Only modules WITHOUT real RTL sources in hw/rtl/libs/

module VX_dp_ram #(
    parameter DATAW = 32,
    parameter SIZE = 256,
    parameter BYTEENW = 4,
    parameter NO_RDATA = 0,
    parameter WRENW = 0,
    parameter LUTRAM = 0,
    parameter OUT_REG = 0,
    parameter RDW_MODE = 0,
    parameter RADDR_REG = 0
) (
    input wire clk,
    input wire reset,
    input wire read,
    input wire write,
    input wire [BYTEENW-1:0] wren,
    input wire [31:0] waddr,
    input wire [31:0] raddr,
    input wire [DATAW-1:0] wdata,
    output wire [DATAW-1:0] rdata
);
endmodule

module VX_fifo_queue #(
    parameter DATAW = 32,
    parameter DEPTH = 2,
    parameter OUT_REG = 0
) (
    input wire clk,
    input wire reset,
    input wire push,
    input wire pop,
    input wire [DATAW-1:0] data_in,
    output wire [DATAW-1:0] data_out,
    output wire full,
    output wire empty,
    output wire alm_full,
    output wire alm_empty,
    output wire [31:0] size
);
endmodule

// VX_priority_arbiter and VX_rr_arbiter use real RTL from hw/rtl/libs/
