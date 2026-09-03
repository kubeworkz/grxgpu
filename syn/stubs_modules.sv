// Module stubs for Yosys slang synthesis
// These are black-box definitions for external modules

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

module VX_pipe_register #(
    parameter DATAW = 32,
    parameter RESETW = 0,
    parameter DEPTH = 1,
    parameter ASYNC_RESET = 0,
    parameter MODEL = 1
) (
    input wire clk,
    input wire reset,
    input wire enable,
    input wire [DATAW-1:0] data_in,
    output wire [DATAW-1:0] data_out
);
endmodule

module VX_lzc #(
    parameter N = 32,
    parameter MODEL = 1
) (
    input wire [N-1:0] data_in,
    output wire [$clog2(N)-1:0] data_out,
    output wire valid_out
);
endmodule

module VX_popcount #(
    parameter N = 32,
    parameter MODEL = 1
) (
    input wire [N-1:0] data_in,
    output wire [5:0] data_out
);
endmodule

module VX_csa_tree #(
    parameter N = 3,
    parameter W = 32,
    parameter S = 32,
    parameter MODEL = 1
) (
    input wire [N*W-1:0] operands,
    output wire [S-1:0] sum,
    output wire [S-1:0] carry
);
endmodule

module VX_ks_adder #(
    parameter N = 32,
    parameter BYPASS = 0
) (
    input wire cin,
    input wire [N-1:0] dataa,
    input wire [N-1:0] datab,
    output wire [N-1:0] sum,
    output wire cout
);
endmodule

module VX_wallace_mul #(
    parameter N = 16,
    parameter M = 16,
    parameter P = 32,
    parameter CPA_KS = 1
) (
    input wire [N-1:0] a,
    input wire [M-1:0] b,
    output wire [P-1:0] p
);
endmodule

module VX_priority_arbiter #(
    parameter NUM_REQS = 2,
    parameter STICKY = 0,
    parameter LOG_NUM_REQS = $clog2(NUM_REQS)
) (
    input wire clk,
    input wire reset,
    input wire [NUM_REQS-1:0] requests,
    output wire [LOG_NUM_REQS-1:0] grant_index,
    output wire [NUM_REQS-1:0] grant_onehot,
    output wire grant_valid
);
endmodule

module VX_rr_arbiter #(
    parameter NUM_REQS = 2,
    parameter MODEL = 1,
    parameter LOG_NUM_REQS = $clog2(NUM_REQS),
    parameter STICKY = 0,
    parameter LUT_OPT = 0
) (
    input wire clk,
    input wire reset,
    input wire [NUM_REQS-1:0] requests,
    output wire [LOG_NUM_REQS-1:0] grant_index,
    output wire [NUM_REQS-1:0] grant_onehot,
    output wire grant_valid
);
endmodule


