// Minimal stubs for Vortex pipeline interfaces and modules
// Used only for Yosys hierarchy checking during TCU synthesis

// ---- Vortex internal modules (stubs) ----

module VX_pipe_register #(parameter DATAW=512, parameter DEPTH=1)
    (input wire clk, input wire reset, input wire enable,
     input wire [DATAW-1:0] data_in, output wire [DATAW-1:0] data_out);
    reg [DATAW-1:0] r_data;
    always @(posedge clk) begin
        if (reset) r_data <= 0;
        else if (enable) r_data <= data_in;
    end
    assign data_out = r_data;
endmodule

module VX_dp_ram #(parameter DATAW=32, parameter SIZE=64, parameter BYPASS=1)
    (input wire clk, input wire [31:0] waddr, input wire [DATAW-1:0] wdata,
     input wire wren, input wire [31:0] raddr, output wire [DATAW-1:0] rdata);
    reg [DATAW-1:0] mem [0:SIZE-1];
    always @(posedge clk) if (wren) mem[waddr] <= wdata;
    assign rdata = mem[raddr];
endmodule

module VX_fifo_queue #(parameter DATAW=32, parameter DEPTH=2, parameter ALMOST_FULL=0, parameter LOOKUP=0)
    (input wire clk, input wire reset, input wire push, input wire pop,
     input wire [DATAW-1:0] data_in, output wire [DATAW-1:0] data_out,
     output wire full, output wire empty,
     output wire [$clog2(DEPTH+1)-1:0] count);
    reg [DATAW-1:0] r_data;
    reg r_full, r_empty;
    always @(posedge clk) begin
        if (reset) begin r_full <= 0; r_empty <= 1; end
        else if (push && !pop) begin r_data <= data_in; r_full <= 1; r_empty <= 0; end
        else if (pop && !push) begin r_full <= 0; r_empty <= 1; end
    end
    assign data_out = r_data;
    assign full = r_full;
    assign empty = r_empty;
    assign count = r_full ? 1 : 0;
endmodule

module VX_generic_arbiter #(parameter NUM_REQS=4, parameter TYPE=0, parameter N=1, parameter WAIT=0, parameter LOG_LOCK=0)
    (input wire clk, input wire reset, input wire [NUM_REQS-1:0] in_reqs,
     output wire [NUM_REQS-1:0] in_acks, output wire [$clog2(NUM_REQS)-1:0] grant_index,
     output wire grant_valid);
    assign grant_valid = |in_reqs;
    assign in_acks = in_reqs;
    assign grant_index = 0;
endmodule

module VX_priority_encoder #(parameter N=8, parameter REVERSE=0)
    (input wire [N-1:0] data_in, output wire [$clog2(N)-1:0] data_out, output wire valid_out);
    integer i;
    reg [$clog2(N)-1:0] out;
    reg found;
    always @(*) begin
        out = 0; found = 0;
        for (i = N-1; i >= 0; i = i - 1)
            if (!found && data_in[i]) begin out = i; found = 1; end
    end
    assign data_out = out;
    assign valid_out = |data_in;
endmodule

module VX_lzc #(parameter N=32)
    (input wire [N-1:0] data_in, output wire [$clog2(N)-1:0] data_out, output wire valid_out);
    assign data_out = 0;
    assign valid_out = |data_in;
endmodule

module VX_popcount #(parameter N=32)
    (input wire [N-1:0] data_in, output wire [$clog2(N+1)-1:0] data_out);
    integer i;
    reg [$clog2(N+1)-1:0] sum;
    always @(*) begin
        sum = 0;
        for (i = 0; i < N; i = i + 1) sum = sum + data_in[i];
    end
    assign data_out = sum;
endmodule

module VX_csa_tree #(parameter N=4, parameter W=10, parameter S=10)
    (input wire [N*W-1:0] operands, output wire [S-1:0] sum, output wire [S-1:0] carry);
    assign sum = 0;
    assign carry = 0;
endmodule

module VX_ks_adder #(parameter N=32, parameter BYPASS=0)
    (input wire [N-1:0] dataa, input wire [N-1:0] datab, input wire cin,
     output wire [N-1:0] sum, output wire cout);
    assign {cout, sum} = dataa + datab + cin;
endmodule

module VX_wallace_mul #(parameter N=8, parameter P=16, parameter CPA_KS=1)
    (input wire [N-1:0] a, input wire [N-1:0] b, output wire [P-1:0] p);
    assign p = a * b;
endmodule

// ---- TCU external interface stubs ----

module VX_execute_if #(parameter IS_NRV=0, parameter UUID_WIDTH=0, parameter DATAW=1)
    (input wire clk, input wire reset);
endmodule

module VX_result_if #(parameter DATAW=1, parameter RDW=1, parameter IS_NRV=0, parameter UUID_WIDTH=0)
    (input wire clk, input wire reset);
endmodule

module VX_dispatch_if #(parameter NUM_THREADS=1, parameter DATAW=1)
    (input wire clk, input wire reset);
endmodule

module VX_commit_if #(parameter NUM_THREADS=1, parameter DATAW=1)
    (input wire clk, input wire reset);
endmodule

module VX_lane_dispatch #(parameter NUM_THREADS=1, parameter DATAW=1)
    (input wire clk, input wire reset);
endmodule

module VX_lane_gather #(parameter DATAW=1)
    (input wire clk, input wire reset);
endmodule

module VX_lsu_sched_if #(parameter DATAW=1)
    (input wire clk, input wire reset);
endmodule

module VX_lsu_scheduler #(parameter DATAW=1)
    (input wire clk, input wire reset);
endmodule

module VX_mem_bus_if #(parameter DATAW=1, parameter ADDRW=1, parameter TAGW=1, parameter N=1)
    (input wire clk, input wire reset);
endmodule

module VX_mem_bus_arb #(parameter DATAW=1, parameter ADDRW=1, parameter TAGW=1, parameter NUM_REQS=1, parameter TYPE=0)
    (input wire clk, input wire reset);
endmodule
