// Blackbox stubs for Vortex core infrastructure — corrected port signatures
// These are minimal behavioral models for Yosys/Synlig synthesis only.

module VX_fifo_queue #(
    parameter DATAW     = 32,
    parameter DEPTH     = 32,
    parameter ALM_FULL  = (DEPTH - 1),
    parameter ALM_EMPTY = 1,
    parameter OUT_REG   = 0,
    parameter LUTRAM    = 0,
    parameter SIZEW     = $clog2(DEPTH+1)
) (
    input  wire             clk,
    input  wire             reset,
    input  wire             push,
    input  wire             pop,
    input  wire [DATAW-1:0] data_in,
    output wire [DATAW-1:0] data_out,
    output wire             empty,
    output wire             alm_empty,
    output wire             full,
    output wire             alm_full,
    output wire [SIZEW-1:0] size
);
    reg [DATAW-1:0] ram [0:DEPTH-1];
    reg [$clog2(DEPTH+1)-1:0] cnt;
    always @(posedge clk) begin
        if (reset) cnt <= 0;
        else if (push && !pop) cnt <= cnt + 1;
        else if (!push && pop) cnt <= cnt - 1;
    end
    assign full = (cnt >= DEPTH);
    assign alm_full = (cnt >= ALM_FULL);
    assign empty = (cnt == 0);
    assign alm_empty = (cnt <= ALM_EMPTY);
    assign size = cnt;
    assign data_out = 0;
endmodule

module VX_dp_ram #(
    parameter DATAW       = 1,
    parameter SIZE        = 1,
    parameter WRENW       = 1,
    parameter OUT_REG     = 0,
    parameter LUTRAM      = 0,
    parameter RDW_MODE    = "W",
    parameter RADDR_REG   = 0,
    parameter RADDR_RESET = 0,
    parameter RDW_ASSERT  = 0,
    parameter RESET_RAM   = 0,
    parameter INIT_ENABLE = 0,
    parameter INIT_FILE   = "",
    parameter INIT_VALUE  = 0,
    parameter ADDRW       = $clog2(SIZE)
) (
    input  wire               clk,
    input  wire               reset,
    input  wire               read,
    input  wire               write,
    input  wire [WRENW-1:0]   wren,
    input  wire [ADDRW-1:0]   waddr,
    input  wire [DATAW-1:0]   wdata,
    input  wire [ADDRW-1:0]   raddr,
    output wire [DATAW-1:0]   rdata
);
    reg [DATAW-1:0] mem [0:SIZE-1];
    always @(posedge clk) if (write) mem[waddr] <= wdata;
    assign rdata = mem[raddr];
endmodule

module VX_elastic_buffer #(
    parameter DATAW   = 1,
    parameter SIZE    = 1,
    parameter OUT_REG = 0,
    parameter LUTRAM  = 0
) (
    input  wire             clk,
    input  wire             reset,
    input  wire             valid_in,
    output wire             ready_in,
    input  wire [DATAW-1:0] data_in,
    output wire [DATAW-1:0] data_out,
    input  wire             ready_out,
    output wire             valid_out
);
    reg [DATAW-1:0] buf_data;
    reg buf_valid;
    assign valid_out = buf_valid;
    assign data_out = buf_data;
    assign ready_in = !buf_valid;
    always @(posedge clk) begin
        if (reset) buf_valid <= 0;
        else if (valid_in && ready_in) begin
            buf_data <= data_in;
            buf_valid <= 1;
        end else if (ready_out) buf_valid <= 0;
    end
endmodule

module VX_stream_arb #(
    parameter NUM_INPUTS  = 1,
    parameter NUM_OUTPUTS = 1,
    parameter DATAW       = 1,
    parameter STICKY      = 0,
    parameter ARBITER     = "R",
    parameter MAX_FANOUT  = 0,
    parameter OUT_BUF     = 0,
    parameter NUM_REQS    = 1,
    parameter SEL_COUNT   = 1,
    parameter LOG_NUM_REQS = 0,
    parameter NUM_REQS_W  = 1
) (
    input  wire clk,
    input  wire reset,
    input  wire [NUM_INPUTS-1:0]              valid_in,
    input  wire [NUM_INPUTS*DATAW-1:0]        data_in,
    output wire [NUM_INPUTS-1:0]              ready_in,
    output wire [NUM_OUTPUTS-1:0]             valid_out,
    output wire [NUM_OUTPUTS*DATAW-1:0]       data_out,
    input  wire [NUM_OUTPUTS-1:0]             ready_out,
    output wire [SEL_COUNT*NUM_REQS_W-1:0]    sel_out
);
    assign valid_out = |valid_in;
    assign data_out = data_in[DATAW-1:0];
    assign ready_in = {NUM_INPUTS{1'b1}};
    assign sel_out = 0;
endmodule

module VX_stream_dispatch #(
    parameter NUM_INPUTS  = 1,
    parameter NUM_OUTPUTS = 1,
    parameter DATAW       = 1,
    parameter ARBITER     = "R",
    parameter BUFFERED    = 0,
    parameter OUT_BUF     = 0
) (
    input  wire clk,
    input  wire reset,
    input  wire [NUM_INPUTS-1:0]              valid_in,
    input  wire [NUM_INPUTS*DATAW-1:0]        data_in,
    output wire [NUM_INPUTS-1:0]              ready_in,
    output wire [NUM_OUTPUTS-1:0]             valid_out,
    output wire [NUM_OUTPUTS*DATAW-1:0]       data_out,
    input  wire [NUM_OUTPUTS-1:0]             ready_out
);
    assign ready_in = {NUM_INPUTS{1'b1}};
    assign valid_out = valid_in[0] ? (NUM_OUTPUTS'(1)) : 0;
    assign data_out = data_in[DATAW-1:0];
endmodule

// VX_mem_bus_arb — flat-port version (interfaces flattened)
// Original uses VX_mem_bus_if interfaces; this stub provides flat wire ports.
module VX_mem_bus_arb #(
    parameter NUM_INPUTS  = 1,
    parameter NUM_OUTPUTS = 1,
    parameter DATA_SIZE   = 1,
    parameter TAG_WIDTH   = 1,
    parameter TAG_SEL_IDX = 0,
    parameter REQ_OUT_BUF = 0,
    parameter RSP_OUT_BUF = 0,
    parameter ARBITER     = "R",
    parameter STICKY      = 0,
    parameter ADDR_WIDTH  = 32,
    parameter ATTR_WIDTH  = 8,
    parameter DATA_OOB    = 0
) (
    input  wire clk,
    input  wire reset,
    // Request slave ports (flat)
    input  wire [NUM_INPUTS-1:0]              req_valid,
    input  wire [NUM_INPUTS*32-1:0]           req_addr,
    input  wire [NUM_INPUTS*DATA_SIZE*8-1:0]  req_data,
    input  wire [NUM_INPUTS*DATA_SIZE-1:0]    req_byteen,
    input  wire [NUM_INPUTS*ATTR_WIDTH-1:0]   req_attr,
    input  wire [NUM_INPUTS*TAG_WIDTH-1:0]    req_tag,
    output wire [NUM_INPUTS-1:0]              req_ready,
    // Response master ports (flat)
    output wire [NUM_OUTPUTS-1:0]             rsp_valid,
    output wire [NUM_OUTPUTS*DATA_SIZE*8-1:0] rsp_data,
    output wire [NUM_OUTPUTS*TAG_WIDTH-1:0]   rsp_tag,
    input  wire [NUM_OUTPUTS-1:0]             rsp_ready
);
    assign rsp_valid = req_valid[0];
    assign rsp_data = req_data[DATA_SIZE*8-1:0];
    assign rsp_tag = req_tag[TAG_WIDTH-1:0];
    assign req_ready = {NUM_INPUTS{1'b1}};
endmodule

module VX_multiplier #(
    parameter DATAW = 32
) (
    input  wire clk,
    input  wire reset,
    input  wire [DATAW-1:0] a,
    input  wire [DATAW-1:0] b,
    output wire [2*DATAW-1:0] result
);
    assign result = a * b;
endmodule

module VX_multiplier_wrapper #(
    parameter A_WIDTH = 32,
    parameter B_WIDTH = 32,
    parameter R_WIDTH = 64,
    parameter LATENCY = 1
) (
    input  wire clk,
    input  wire reset,
    input  wire enable,
    input  wire [A_WIDTH-1:0] dataa,
    input  wire [B_WIDTH-1:0] datab,
    output wire [R_WIDTH-1:0] result
);
    assign result = dataa * datab;
endmodule

module VX_priority_encoder #(
    parameter N = 32
) (
    input  wire [N-1:0]     valid_in,
    output wire [$clog2(N)-1:0] sel,
    output wire             valid_out
);
    assign valid_out = |valid_in;
    assign sel = 0;
endmodule

module VX_lane_dispatch #(
    parameter NUM_LANES = 4,
    parameter DATAW     = 32
) (
    input  wire clk,
    input  wire reset,
    input  wire              valid_in,
    input  wire [DATAW-1:0]  data_in,
    output wire [NUM_LANES-1:0]        valid_out,
    output wire [NUM_LANES*DATAW-1:0]  data_out
);
    assign valid_out = {NUM_LANES{valid_in}};
    assign data_out = {NUM_LANES{data_in}};
endmodule

module VX_lane_gather #(
    parameter NUM_LANES = 4,
    parameter DATAW     = 32
) (
    input  wire [NUM_LANES-1:0]        valid_in,
    input  wire [NUM_LANES*DATAW-1:0]  data_in,
    output wire                        valid_out,
    output wire [DATAW-1:0]            data_out
);
    assign valid_out = |valid_in;
    assign data_out = data_in[DATAW-1:0];
endmodule
