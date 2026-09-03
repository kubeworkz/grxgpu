// Minimal empty interface stubs for Yosys slang synthesis
// These are black-box definitions so slang can elaborate the TCU hierarchy
// No modports - let slang infer from port direction

interface VX_execute_if;
endinterface
interface VX_result_if;
endinterface
interface VX_dispatch_if;
endinterface
interface VX_commit_if;
endinterface
interface VX_mem_bus_if;
endinterface
interface VX_lsu_sched_if;
endinterface

module VX_dp_ram #(
    parameter DATAW = 32, parameter SIZE = 256, parameter BYTEENW = 4,
    parameter NO_RDATA = 0, parameter WRENW = 0, parameter LUTRAM = 0,
    parameter OUT_REG = 0, parameter RDW_MODE = 0, parameter RADDR_REG = 0
) (
    input wire clk, input wire reset, input wire read, input wire write,
    input wire [BYTEENW-1:0] wren, input wire [31:0] waddr,
    input wire [31:0] raddr, input wire [DATAW-1:0] wdata,
    output wire [DATAW-1:0] rdata
);
endmodule

module VX_fifo_queue #(
    parameter DATAW = 32, parameter DEPTH = 2, parameter OUT_REG = 0
) (
    input wire clk, input wire reset, input wire push, input wire pop,
    input wire [DATAW-1:0] data_in, output wire [DATAW-1:0] data_out,
    output wire full, output wire empty,
    output wire alm_full, output wire alm_empty, output wire [31:0] size
);
endmodule

module VX_pipe_register #(
    parameter DATAW = 32, parameter RESETW = 0, parameter DEPTH = 1,
    parameter ASYNC_RESET = 0, parameter MODEL = 1
) (
    input wire clk, input wire reset, input wire enable,
    input wire [DATAW-1:0] data_in, output wire [DATAW-1:0] data_out
);
endmodule

module VX_lzc #(parameter N = 32, parameter MODEL = 1) (
    input wire [N-1:0] data_in, output wire [$clog2(N)-1:0] data_out,
    output wire valid_out
);
endmodule

module VX_popcount #(parameter N = 32, parameter MODEL = 1) (
    input wire [N-1:0] data_in, output wire [5:0] data_out
);
endmodule

module VX_csa_tree #(parameter N = 3, parameter W = 32, parameter S = 32, parameter MODEL = 1) (
    input wire [N*W-1:0] operands, output wire [S-1:0] sum,
    output wire [S-1:0] carry
);
endmodule

module VX_lsu_scheduler;
endmodule
