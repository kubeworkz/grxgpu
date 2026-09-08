// Blackbox stubs for Vortex core infrastructure
module VX_fifo_queue #(
    parameter DATAW=32, DEPTH=1, ALM_FULL=0, ALM_EMPTY=0, FAST=0
)(
    input wire clk, reset, push, pop,
    input wire [DATAW-1:0] data_in,
    output wire [DATAW-1:0] data_out,
    output wire full, empty
);
    reg [DATAW-1:0] ram [0:DEPTH-1];
    reg [31:0] cnt;
    always @(posedge clk) begin
        if (reset) cnt <= 0;
        else if (push && !pop) cnt <= cnt + 1;
        else if (!push && pop) cnt <= cnt - 1;
    end
    assign full = (cnt >= DEPTH);
    assign empty = (cnt == 0);
    assign data_out = 0;
endmodule

module VX_dp_ram #(
    parameter DATAW=32, NUMWORDS=64, WORD_SIZE=1, RDW_MODE=ZERO
)(
    input wire clk,
    input wire [(NUMWORDS)-1:0] waddr, raddr,
    input wire [DATAW-1:0] wdata,
    input wire wren,
    output wire [DATAW-1:0] rdata
);
    reg [DATAW-1:0] mem [0:NUMWORDS-1];
    always @(posedge clk) if (wren) mem[waddr] <= wdata;
    assign rdata = mem[raddr];
endmodule

module VX_elastic_buffer #(
    parameter DATAW=32, SKID=1
)(
    input wire clk, reset, in_valid,
    input wire [DATAW-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [DATAW-1:0] out_data,
    input wire out_ready
);
    reg [DATAW-1:0] buf_data;
    reg buf_valid;
    assign out_valid = buf_valid;
    assign out_data = buf_data;
    assign in_ready = !buf_valid;
    always @(posedge clk) begin
        if (reset) buf_valid <= 0;
        else if (in_valid && in_ready) begin
            buf_data <= in_data;
            buf_valid <= 1;
        end else if (out_ready) buf_valid <= 0;
    end
endmodule

module VX_stream_arb #(
    parameter NUM_INPUTS=2, DATAW=32, TYPE=ROUND
)(
    input wire clk, reset,
    input wire [NUM_INPUTS-1:0] valid_in,
    input wire [NUM_INPUTS*DATAW-1:0] data_in,
    output wire valid_out,
    output wire [DATAW-1:0] data_out,
    output wire [(NUM_INPUTS)-1:0] sel,
    input wire ready_out
);
    assign valid_out = |valid_in;
    assign data_out = data_in[DATAW-1:0];
    assign sel = 0;
endmodule

module VX_stream_dispatch #(
    parameter NUM_OUTPUTS=2, DATAW=32
)(
    input wire clk, reset,
    input wire valid_in,
    input wire [DATAW-1:0] data_in,
    input wire [(NUM_OUTPUTS)-1:0] sel_in,
    output wire ready_in,
    output wire [NUM_OUTPUTS-1:0] valid_out,
    output wire [NUM_OUTPUTS*DATAW-1:0] data_out,
    input wire [NUM_OUTPUTS-1:0] ready_out
);
    assign ready_in = 1;
    assign valid_out = valid_in << sel_in;
    assign data_out = data_in;
endmodule

module VX_multiplier #(
    parameter DATAW=32
)(
    input wire clk, reset,
    input wire [DATAW-1:0] a, b,
    output wire [2*DATAW-1:0] result
);
    assign result = a * b;
endmodule

module VX_priority_encoder #(
    parameter N=32
)(
    input wire [N-1:0] valid_in,
    output wire [(N)-1:0] sel,
    output wire valid_out
);
    assign valid_out = |valid_in;
    assign sel = 0;
endmodule

module VX_mem_bus_slice #(
    parameter DATAW=512, TAGW=13
)(
    input wire clk, reset,
    // Input bus
    input wire [31:0] in_addr,
    input wire [DATAW-1:0] in_data,
    input wire in_valid,
    output wire in_ready,
    input wire [TAGW-1:0] in_tag,
    // Output bus
    output wire [31:0] out_addr,
    output wire [DATAW-1:0] out_data,
    output wire out_valid,
    input wire out_ready,
    output wire [TAGW-1:0] out_tag
);
    assign out_addr = in_addr;
    assign out_data = in_data;
    assign out_valid = in_valid;
    assign in_ready = out_ready;
    assign out_tag = in_tag;
endmodule

module VX_mem_bus_arb #(
    parameter NUM_REQS=2, DATAW=512, TAGW=13, TYPE=ROUND
)(
    input wire clk, reset,
    input wire [NUM_REQS-1:0] req_valid,
    input wire [NUM_REQS*32-1:0] req_addr,
    input wire [NUM_REQS*DATAW-1:0] req_data,
    input wire [NUM_REQS*TAGW-1:0] req_tag,
    output wire [NUM_REQS-1:0] req_ready,
    output wire rsp_valid,
    output wire [DATAW-1:0] rsp_data,
    output wire [TAGW-1:0] rsp_tag,
    input wire rsp_ready
);
    assign rsp_valid = req_valid[0];
    assign rsp_data = req_data[DATAW-1:0];
    assign rsp_tag = req_tag[TAGW-1:0];
    assign req_ready = {NUM_REQS{1'b1}};
endmodule

module VX_generic_arbiter #(
    parameter NUM_REQS=2, TYPE=ROUND, LOG=0
)(
    input wire clk, reset,
    input wire [NUM_REQS-1:0] req_in,
    output wire [(NUM_REQS)-1:0] grant_index,
    output wire grant_valid
);
    assign grant_valid = |req_in;
    assign grant_index = 0;
endmodule

module VX_lane_dispatch #(
    parameter NUM_LANES=4, DATAW=32
)(
    input wire clk, reset,
    input wire valid_in,
    input wire [DATAW-1:0] data_in,
    output wire [NUM_LANES-1:0] valid_out,
    output wire [NUM_LANES*DATAW-1:0] data_out
);
    assign valid_out = {NUM_LANES{valid_in}};
    assign data_out = {NUM_LANES{data_in}};
endmodule

module VX_lane_gather #(
    parameter NUM_LANES=4, DATAW=32
)(
    input wire [NUM_LANES-1:0] valid_in,
    input wire [NUM_LANES*DATAW-1:0] data_in,
    output wire valid_out,
    output wire [DATAW-1:0] data_out
);
    assign valid_out = |valid_in;
    assign data_out = data_in[DATAW-1:0];
endmodule
