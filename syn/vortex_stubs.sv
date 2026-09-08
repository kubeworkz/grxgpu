// Stubs for Vortex sub-modules used by the flattened DXA.
// Port signatures match actual instantiation patterns in the flattened DXA code.

// ============================================================
// VX_stream_arb — parameterized stream arbiter
// ============================================================
module VX_stream_arb #(
    parameter NUM_INPUTS  = 1,
    parameter NUM_OUTPUTS = 1,
    parameter DATAW       = 1,
    parameter STICKY      = 0,
    parameter ARBITER     = "R",
    parameter MAX_FANOUT  = 16,
    parameter OUT_BUF     = 0,
    parameter NUM_REQS    = (NUM_INPUTS > NUM_OUTPUTS) ? ((NUM_INPUTS + NUM_OUTPUTS - 1) / NUM_OUTPUTS) : ((NUM_OUTPUTS + NUM_INPUTS - 1) / NUM_INPUTS),
    parameter SEL_COUNT   = (NUM_INPUTS < NUM_OUTPUTS) ? NUM_INPUTS : NUM_OUTPUTS,
    parameter LOG_NUM_REQS= (NUM_REQS > 1) ? $clog2(NUM_REQS) : 0,
    parameter NUM_REQS_W  = (LOG_NUM_REQS > 0) ? LOG_NUM_REQS : 1
) (
    input  wire clk,
    input  wire reset,

    input  wire [NUM_INPUTS-1:0]             valid_in,
    input  wire [NUM_INPUTS*DATAW-1:0]       data_in,
    output wire [NUM_INPUTS-1:0]             ready_in,

    output wire [NUM_OUTPUTS-1:0]            valid_out,
    output wire [NUM_OUTPUTS*DATAW-1:0]      data_out,
    input  wire [NUM_OUTPUTS-1:0]            ready_out,

    output wire [SEL_COUNT*NUM_REQS_W-1:0]   sel_out
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
    assign sel_out = {NUM_SEL_COUNT{NUM_REQS_W'(0)}};
endmodule

// ============================================================
// VX_elastic_buffer — parameterized elastic buffer
// ============================================================
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
    reg             buf_valid;

    assign ready_in  = ready_out || !buf_valid;
    assign data_out  = buf_data;
    assign valid_out = buf_valid;

    always @(posedge clk) begin
        if (reset) begin
            buf_valid <= 1'b0;
        end else begin
            if (valid_in && ready_in) begin
                buf_data  <= data_in;
                buf_valid <= 1'b1;
            end else if (ready_out) begin
                buf_valid <= 1'b0;
            end
        end
    end
endmodule

// ============================================================
// VX_fifo_queue — parameterized FIFO queue
// ============================================================
module VX_fifo_queue #(
    parameter DATAW     = 32,
    parameter DEPTH     = 32,
    parameter ALM_FULL  = (DEPTH - 1),
    parameter ALM_EMPTY = 1,
    parameter OUT_REG   = 0,
    parameter LUTRAM    = 0,
    parameter SIZEW     = ($clog2(DEPTH+1) > 0) ? $clog2(DEPTH+1) : 1
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
    reg [SIZEW-1:0] count;
    reg [$clog2(DEPTH)-1:0] rd_ptr, wr_ptr;

    assign data_out = ram[rd_ptr];
    assign empty    = (count == 0);
    assign full     = (count == DEPTH[SIZEW-1:0]);
    assign alm_empty = (count <= ALM_EMPTY[SIZEW-1:0]);
    assign alm_full  = (count >= ALM_FULL[SIZEW-1:0]);
    assign size      = count;

    always @(posedge clk) begin
        if (reset) begin
            count   <= 0;
            rd_ptr  <= 0;
            wr_ptr  <= 0;
        end else begin
            if (push && !full) begin
                ram[wr_ptr] <= data_in;
                wr_ptr <= wr_ptr + 1;
            end
            if (pop && !empty) begin
                rd_ptr <= rd_ptr + 1;
            end
            if (push && !pop)
                count <= count + 1;
            else if (!push && pop)
                count <= count - 1;
        end
    end
endmodule

// ============================================================
// VX_mem_bus_arb — parameterized memory bus arbiter
// Flattened port signature matching DXA core instantiation
// ============================================================
module VX_mem_bus_arb import VX_gpu_pkg::*; #(
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
    input wire              clk,
    input wire              reset,

    // Flattened input bus(es) — each input has req/rsp channels
    input  wire [NUM_INPUTS-1:0]           req_valid,
    input  wire [NUM_INPUTS*ADDR_WIDTH-1:0] req_addr,
    input  wire [NUM_INPUTS*DATA_SIZE*8-1:0] req_data,
    input  wire [NUM_INPUTS*DATA_SIZE-1:0]  req_byteen,
    input  wire [NUM_INPUTS*ATTR_WIDTH-1:0] req_attr,
    input  wire [NUM_INPUTS*TAG_WIDTH-1:0]  req_tag,
    output wire [NUM_INPUTS-1:0]           req_ready,

    output wire [NUM_OUTPUTS-1:0]          rsp_valid,
    output wire [NUM_OUTPUTS*DATA_SIZE*8-1:0] rsp_data,
    output wire [NUM_OUTPUTS*TAG_WIDTH-1:0]  rsp_tag,
    input  wire [NUM_OUTPUTS-1:0]          rsp_ready
);
    // Passthrough: connect input 0 to output 0
    assign rsp_valid[0]   = req_valid[0];
    assign rsp_data[DATA_SIZE*8-1:0] = req_data[DATA_SIZE*8-1:0];
    assign rsp_tag[TAG_WIDTH-1:0]    = req_tag[TAG_WIDTH-1:0];
    assign req_ready[0]   = rsp_ready[0];

    genvar i;
    generate
        for (i = 1; i < NUM_INPUTS; i = i + 1) begin : gen_req_ready
            assign req_ready[i] = 1'b0;
        end
        for (i = 1; i < NUM_OUTPUTS; i = i + 1) begin : gen_rsp
            assign rsp_valid[i] = 1'b0;
            assign rsp_data[i*DATA_SIZE*8 +: DATA_SIZE*8] = {(DATA_SIZE*8){1'b0}};
            assign rsp_tag[i*TAG_WIDTH +: TAG_WIDTH] = {TAG_WIDTH{1'b0}};
        end
    endgenerate
endmodule

// ============================================================
// VX_mem_bus_slice — parameterized memory bus pipeline slice
// Flattened port signature matching DXA core instantiation
// ============================================================
module VX_mem_bus_slice import VX_gpu_pkg::*; #(
    parameter DATA_SIZE   = 1,
    parameter TAG_WIDTH   = 1,
    parameter REQ_OUT_BUF = 0,
    parameter RSP_OUT_BUF = 0,
    parameter ADDR_WIDTH  = 32,
    parameter ATTR_WIDTH  = 8
) (
    input wire              clk,
    input wire              reset,

    // Flattened request channel (slave side)
    input  wire             bus_in_req_valid,
    input  wire [ADDR_WIDTH-1:0]  bus_in_req_addr,
    input  wire [DATA_SIZE*8-1:0] bus_in_req_data,
    input  wire [DATA_SIZE-1:0]   bus_in_req_byteen,
    input  wire [ATTR_WIDTH-1:0]  bus_in_req_attr,
    input  wire [TAG_WIDTH-1:0]   bus_in_req_tag,
    output wire             bus_in_req_ready,

    // Flattened response channel (slave side)
    output wire             bus_in_rsp_valid,
    output wire [DATA_SIZE*8-1:0] bus_in_rsp_data,
    output wire [TAG_WIDTH-1:0]   bus_in_rsp_tag,
    input  wire             bus_in_rsp_ready,

    // Flattened request channel (master side)
    output wire             bus_out_req_valid,
    output wire [ADDR_WIDTH-1:0]  bus_out_req_addr,
    output wire [DATA_SIZE*8-1:0] bus_out_req_data,
    output wire [DATA_SIZE-1:0]   bus_out_req_byteen,
    output wire [ATTR_WIDTH-1:0]  bus_out_req_attr,
    output wire [TAG_WIDTH-1:0]   bus_out_req_tag,
    input  wire             bus_out_req_ready,

    // Flattened response channel (master side)
    input  wire             bus_out_rsp_valid,
    input  wire [DATA_SIZE*8-1:0] bus_out_rsp_data,
    input  wire [TAG_WIDTH-1:0]   bus_out_rsp_tag,
    output wire             bus_out_rsp_ready
);
    // Passthrough
    assign bus_out_req_valid = bus_in_req_valid;
    assign bus_out_req_addr  = bus_in_req_addr;
    assign bus_out_req_data  = bus_in_req_data;
    assign bus_out_req_byteen = bus_in_req_byteen;
    assign bus_out_req_attr  = bus_in_req_attr;
    assign bus_out_req_tag   = bus_in_req_tag;
    assign bus_in_req_ready  = bus_out_req_ready;

    assign bus_in_rsp_valid  = bus_out_rsp_valid;
    assign bus_in_rsp_data   = bus_out_rsp_data;
    assign bus_in_rsp_tag    = bus_out_rsp_tag;
    assign bus_out_rsp_ready = bus_in_rsp_ready;
endmodule

// ============================================================
// VX_stream_switch — parameterized stream switch
// ============================================================
module VX_stream_switch #(
    parameter NUM_INPUTS  = 1,
    parameter NUM_OUTPUTS = 1,
    parameter DATAW       = 1,
    parameter OUT_BUF     = 0,
    parameter NUM_REQS    = (NUM_INPUTS > NUM_OUTPUTS) ? ((NUM_INPUTS + NUM_OUTPUTS - 1) / NUM_OUTPUTS) : ((NUM_OUTPUTS + NUM_INPUTS - 1) / NUM_INPUTS),
    parameter SEL_COUNT   = (NUM_INPUTS < NUM_OUTPUTS) ? NUM_INPUTS : NUM_OUTPUTS,
    parameter LOG_NUM_REQS= (NUM_REQS > 1) ? $clog2(NUM_REQS) : 0
) (
    input wire                              clk,
    input wire                              reset,

    input wire  [SEL_COUNT*LOG_NUM_REQS-1:0] sel_in,

    input  wire [NUM_INPUTS-1:0]            valid_in,
    input  wire [NUM_INPUTS*DATAW-1:0]      data_in,
    output wire [NUM_INPUTS-1:0]            ready_in,

    output wire [NUM_OUTPUTS-1:0]           valid_out,
    output wire [NUM_OUTPUTS*DATAW-1:0]     data_out,
    input  wire [NUM_OUTPUTS-1:0]           ready_out
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

// ============================================================
// VX_priority_encoder — parameterized priority encoder
// ============================================================
module VX_priority_encoder #(
    parameter N  = 1,
    parameter LOGN = (N > 1) ? $clog2(N) : 1,
    parameter REVERSE = 0
) (
    input  wire [N-1:0]    data_in,
    output wire [LOGN-1:0] index_out,
    output wire [N-1:0]    onehot_out,
    output wire            valid_out
);
    assign valid_out = |data_in;
    assign onehot_out = data_in;
    assign index_out = {LOGN{1'b0}};
endmodule

// ============================================================
// VX_lzc — leading zero counter
// ============================================================
module VX_lzc #(
    parameter N = 1,
    parameter LOGN = (N > 1) ? $clog2(N) : 1
) (
    input  wire [N-1:0]    data_in,
    output wire [LOGN-1:0] index_out,
    output wire [N-1:0]    onehot_out,
    output wire            valid_out
);
    assign valid_out = |data_in;
    assign onehot_out = data_in;
    assign index_out = {LOGN{1'b0}};
endmodule

// ============================================================
// VX_dp_ram — dual-port RAM (blackbox for synthesis)
// ============================================================
module VX_dp_ram #(
    parameter DATAW   = 1,
    parameter SIZE    = 1,
    parameter ENABLE_BYPASS = 0,
    parameter RDW_ENABLE = 0,
    parameter BYTES   = 1,
    parameter WORDS   = 1
) (
    input  wire             clk,
    input  wire             reset,
    input  wire             wren,
    input  wire [BYTES-1:0] wr_byteen,
    input  wire [ADDRW-1:0] wr_addr,
    input  wire [DATAW-1:0] wr_data,
    input  wire             rden,
    input  wire [ADDRW-1:0] rd_addr,
    output wire [DATAW-1:0] rd_data
);
    parameter ADDRW = $clog2(WORDS > 1 ? WORDS : 2);
    reg [DATAW-1:0] ram [0:WORDS-1];
    always @(posedge clk) begin
        if (wren) ram[wr_addr] <= wr_data;
    end
    assign rd_data = ram[rd_addr];
endmodule

// ============================================================
// VX_csa_tree — carry-save adder tree
// ============================================================
module VX_csa_tree #(
    parameter DATAW  = 32,
    parameter N      = 2,
    parameter ADDER_TYPE = 0,
    parameter LATENCY = 0
) (
    input  wire [N*DATAW-1:0]  data_in,
    output wire [DATAW-1:0]    sum,
    output wire [DATAW-1:0]    carry
);
    assign sum   = data_in[DATAW-1:0];
    assign carry = (N > 1) ? data_in[2*DATAW-1:DATAW] : {DATAW{1'b0}};
endmodule

// ============================================================
// VX_ks_adder — Kogge-Stone adder
// ============================================================
module VX_ks_adder #(
    parameter DATAW  = 32,
    parameter LATENCY = 0
) (
    input  wire             clk,
    input  wire [DATAW-1:0] dataa,
    input  wire [DATAW-1:0] datab,
    output wire [DATAW-1:0] result
);
    assign result = dataa + datab;
endmodule

// ============================================================
// VX_popcount — population count
// ============================================================
module VX_popcount #(
    parameter N  = 32,
    parameter LOGN = $clog2(N)
) (
    input  wire [N-1:0]    data_in,
    output wire [LOGN-1:0] result
);
    // Simple behavioral popcount
    integer i;
    reg [LOGN-1:0] cnt;
    always @(*) begin
        cnt = 0;
        for (i = 0; i < N; i = i + 1)
            if (data_in[i]) cnt = cnt + 1;
    end
    assign result = cnt;
endmodule

// ============================================================
// VX_pipe_register — parameterized pipeline register
// ============================================================
module VX_pipe_register #(
    parameter DATAW = 1,
    parameter DEPTH = 1,
    parameter RESET = 0,
    parameter INITIAL = 0
) (
    input  wire             clk,
    input  wire             reset,
    input  wire [DATAW-1:0] data_in,
    output wire [DATAW-1:0] data_out
);
    reg [DATAW-1:0] regs [0:DEPTH-1];
    integer i;
    always @(posedge clk) begin
        if (reset) begin
            for (i = 0; i < DEPTH; i = i + 1)
                regs[i] <= DATAW'(INITIAL);
        end else begin
            regs[0] <= data_in;
            for (i = 1; i < DEPTH; i = i + 1)
                regs[i] <= regs[i-1];
        end
    end
    assign data_out = regs[DEPTH-1];
endmodule

// ============================================================
// VX_tcu_uops — TCU micro-ops ROM (blackbox)
// ============================================================
module VX_tcu_uops #(
    parameter UOPS = 1,
    parameter OPW  = 8,
    parameter DATAW = 32
) (
    input  wire [$clog2(UOPS)-1:0] uop_addr,
    output wire [OPW-1:0]          uop_op,
    output wire [DATAW-1:0]        uop_data
);
    assign uop_op  = {OPW{1'b0}};
    assign uop_data = {DATAW{1'b0}};
endmodule

// ============================================================
// VX_tcu_tfr_mul_f16 — TFR half-precision multiplier (blackbox)
// ============================================================
module VX_tcu_tfr_mul_f16 (
    input  wire [15:0] a,
    input  wire [15:0] b,
    output wire [31:0] result
);
    assign result = 32'h0;
endmodule

// ============================================================
// VX_tcu_tfr_mul_f32 — TFR single-precision multiplier (blackbox)
// ============================================================
module VX_tcu_tfr_mul_f32 (
    input  wire [31:0] a,
    input  wire [31:0] b,
    output wire [31:0] result
);
    assign result = a * b;
endmodule

// ============================================================
// VX_tcu_tfr_mul_f4 — TFR 4-bit multiplier (blackbox)
// ============================================================
module VX_tcu_tfr_mul_f4 (
    input  wire [3:0] a,
    input  wire [3:0] b,
    output wire [7:0] result
);
    assign result = a * b;
endmodule

// ============================================================
// VX_tcu_tfr_mul_f8 — TFR 8-bit multiplier (blackbox)
// ============================================================
module VX_tcu_tfr_mul_f8 (
    input  wire [7:0] a,
    input  wire [7:0] b,
    output wire [15:0] result
);
    assign result = a * b;
endmodule

// ============================================================
// VX_tcu_tfr_mul_int8 — TFR INT8 multiplier (blackbox)
// ============================================================
module VX_tcu_tfr_mul_int8 (
    input  wire signed [7:0] a,
    input  wire signed [7:0] b,
    output wire signed [15:0] result
);
    assign result = a * b;
endmodule

// ============================================================
// VX_tcu_tfr_mul_int4 — TFR INT4 multiplier (blackbox)
// ============================================================
module VX_tcu_tfr_mul_int4 (
    input  wire signed [3:0] a,
    input  wire signed [3:0] b,
    output wire signed [7:0] result
);
    assign result = a * b;
endmodule

// ============================================================
// VX_tcu_tfr_wmul — TFR weighted multiplier (blackbox)
// ============================================================
module VX_tcu_tfr_wmul #(
    parameter DATAW = 32,
    parameter WEIGHTW = 16
) (
    input  wire [DATAW-1:0] dataa,
    input  wire [WEIGHTW-1:0] datab,
    output wire [DATAW-1:0] result
);
    assign result = dataa;
endmodule
