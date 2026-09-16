`default_nettype wire

// ============================================================
// Configuration
// ============================================================
localparam NUM_THREADS = 16;
localparam XLEN = 32;
localparam FULL_NUM_LANES = 16;
localparam MUX_NUM_LANES = 4;
localparam MUX_CYCLES = 4;
localparam LANE_BITS = 2;

localparam FULL_DISPATCH_W = 1024;  // 16 × 64
localparam FULL_RESULT_W = 512;     // 16 × 32
localparam MUX_DISPATCH_W = 256;    // 4 × 64
localparam MUX_RESULT_W = 128;      // 4 × 32

// ============================================================
// Original: 16-lane ALU (for comparison)
// ============================================================
module VX_alu_int_16lane (
    input  wire clk,
    input  wire reset,
    input  wire exec_valid,
    output wire exec_ready,
    input  wire [FULL_DISPATCH_W-1:0] exec_data,
    output wire res_valid,
    input  wire res_ready,
    output wire [FULL_RESULT_W-1:0] res_data
);
    wire [FULL_NUM_LANES-1:0][XLEN-1:0] rs1, rs2;
    wire [FULL_NUM_LANES-1:0][XLEN-1:0] add_out;

    assign rs1 = exec_data[FULL_DISPATCH_W/2-1:0];
    assign rs2 = exec_data[FULL_DISPATCH_W-1:FULL_DISPATCH_W/2];

    genvar i;
    for (i = 0; i < FULL_NUM_LANES; i = i + 1) begin : g
        assign add_out[i] = rs1[i] + rs2[i];
    end

    reg valid_r;
    reg [FULL_RESULT_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) valid_r <= 0;
        else if (exec_valid && exec_ready) begin
            valid_r <= 1;
            data_r <= add_out;
        end else if (res_ready) valid_r <= 0;
    end

    assign exec_ready = res_ready;
    assign res_valid = valid_r;
    assign res_data = data_r;
endmodule

// ============================================================
// Muxed: 4-lane ALU (4× narrower, runs 4 cycles)
// ============================================================
module VX_alu_int_4lane (
    input  wire clk,
    input  wire reset,
    input  wire exec_valid,
    output wire exec_ready,
    input  wire [MUX_DISPATCH_W-1:0] exec_data,
    output wire res_valid,
    input  wire res_ready,
    output wire [MUX_RESULT_W-1:0] res_data
);
    wire [MUX_NUM_LANES-1:0][XLEN-1:0] rs1, rs2;
    wire [MUX_NUM_LANES-1:0][XLEN-1:0] add_out;

    assign rs1 = exec_data[MUX_DISPATCH_W/2-1:0];
    assign rs2 = exec_data[MUX_DISPATCH_W-1:MUX_DISPATCH_W/2];

    genvar i;
    for (i = 0; i < MUX_NUM_LANES; i = i + 1) begin : g
        assign add_out[i] = rs1[i] + rs2[i];
    end

    reg valid_r;
    reg [MUX_RESULT_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) valid_r <= 0;
        else if (exec_valid && exec_ready) begin
            valid_r <= 1;
            data_r <= add_out;
        end else if (res_ready) valid_r <= 0;
    end

    assign exec_ready = res_ready;
    assign res_valid = valid_r;
    assign res_data = data_r;
endmodule

// ============================================================
// Original: 16-lane multiplier
// ============================================================
module VX_muldiv_16lane (
    input  wire clk,
    input  wire reset,
    input  wire exec_valid,
    output wire exec_ready,
    input  wire [FULL_DISPATCH_W-1:0] exec_data,
    output wire res_valid,
    input  wire res_ready,
    output wire [FULL_RESULT_W-1:0] res_data
);
    wire [FULL_NUM_LANES-1:0][XLEN-1:0] rs1, rs2;
    wire [FULL_NUM_LANES-1:0][XLEN-1:0] mul_out;

    assign rs1 = exec_data[FULL_DISPATCH_W/2-1:0];
    assign rs2 = exec_data[FULL_DISPATCH_W-1:FULL_DISPATCH_W/2];

    genvar i;
    for (i = 0; i < FULL_NUM_LANES; i = i + 1) begin : g
        assign mul_out[i] = rs1[i] * rs2[i];
    end

    reg valid_r;
    reg [FULL_RESULT_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) valid_r <= 0;
        else if (exec_valid && exec_ready) begin
            valid_r <= 1;
            data_r <= mul_out;
        end else if (res_ready) valid_r <= 0;
    end

    assign exec_ready = res_ready;
    assign res_valid = valid_r;
    assign res_data = data_r;
endmodule

// ============================================================
// Muxed: 4-lane multiplier
// ============================================================
module VX_muldiv_4lane (
    input  wire clk,
    input  wire reset,
    input  wire exec_valid,
    output wire exec_ready,
    input  wire [MUX_DISPATCH_W-1:0] exec_data,
    output wire res_valid,
    input  wire res_ready,
    output wire [MUX_RESULT_W-1:0] res_data
);
    wire [MUX_NUM_LANES-1:0][XLEN-1:0] rs1, rs2;
    wire [MUX_NUM_LANES-1:0][XLEN-1:0] mul_out;

    assign rs1 = exec_data[MUX_DISPATCH_W/2-1:0];
    assign rs2 = exec_data[MUX_DISPATCH_W-1:MUX_DISPATCH_W/2];

    genvar i;
    for (i = 0; i < MUX_NUM_LANES; i = i + 1) begin : g
        assign mul_out[i] = rs1[i] * rs2[i];
    end

    reg valid_r;
    reg [MUX_RESULT_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) valid_r <= 0;
        else if (exec_valid && exec_ready) begin
            valid_r <= 1;
            data_r <= mul_out;
        end else if (res_ready) valid_r <= 0;
    end

    assign exec_ready = res_ready;
    assign res_valid = valid_r;
    assign res_data = data_r;
endmodule

// ============================================================
// Original: 16-lane TCU core stub (pass-through for synthesis)
// ============================================================
module VX_tcu_core_16lane (
    input  wire clk,
    input  wire reset,
    input  wire exec_valid,
    output wire exec_ready,
    input  wire [FULL_DISPATCH_W-1:0] exec_data,
    output wire res_valid,
    input  wire res_ready,
    output wire [FULL_RESULT_W-1:0] res_data
);
    reg valid_r;
    reg [FULL_RESULT_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) valid_r <= 0;
        else if (exec_valid && exec_ready) begin
            valid_r <= 1;
            data_r <= exec_data[FULL_RESULT_W-1:0];
        end else if (res_ready) valid_r <= 0;
    end

    assign exec_ready = res_ready;
    assign res_valid = valid_r;
    assign res_data = data_r;
endmodule

// ============================================================
// Muxed: 4-lane TCU core stub
// ============================================================
module VX_tcu_core_4lane (
    input  wire clk,
    input  wire reset,
    input  wire exec_valid,
    output wire exec_ready,
    input  wire [MUX_DISPATCH_W-1:0] exec_data,
    output wire res_valid,
    input  wire res_ready,
    output wire [MUX_RESULT_W-1:0] res_data
);
    reg valid_r;
    reg [MUX_RESULT_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) valid_r <= 0;
        else if (exec_valid && exec_ready) begin
            valid_r <= 1;
            data_r <= exec_data[MUX_RESULT_W-1:0];
        end else if (res_ready) valid_r <= 0;
    end

    assign exec_ready = res_ready;
    assign res_valid = valid_r;
    assign res_data = data_r;
endmodule

// ============================================================
// Wrapper: Original design (16 lanes, 2 ALU + 2 MUL + 2 TCU)
// ============================================================
module VX_core_original (
    input  wire clk,
    input  wire reset
);
    wire [1:0] dummy_valid, dummy_ready;
    wire [FULL_DISPATCH_W-1:0] dummy_data;
    wire [1:0] dummy_res_valid;
    wire [FULL_RESULT_W-1:0] dummy_res_data;

    // 2× ALU
    VX_alu_int_16lane alu0 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({FULL_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));
    VX_alu_int_16lane alu1 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({FULL_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));

    // 2× MUL
    VX_muldiv_16lane mul0 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({FULL_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));
    VX_muldiv_16lane mul1 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({FULL_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));

    // 2× TCU
    VX_tcu_core_16lane tcu0 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({FULL_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));
    VX_tcu_core_16lane tcu1 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({FULL_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));
endmodule

// ============================================================
// Wrapper: Muxed design (4 lanes, 2 ALU + 2 MUL + 2 TCU)
// ============================================================
module VX_core_muxed (
    input  wire clk,
    input  wire reset
);
    wire [1:0] dummy_valid, dummy_ready;
    wire [MUX_DISPATCH_W-1:0] dummy_data;
    wire [1:0] dummy_res_valid;
    wire [MUX_RESULT_W-1:0] dummy_res_data;

    // 2× ALU (4 lanes each)
    VX_alu_int_4lane alu0 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({MUX_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));
    VX_alu_int_4lane alu1 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({MUX_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));

    // 2× MUL (4 lanes each)
    VX_muldiv_4lane mul0 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({MUX_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));
    VX_muldiv_4lane mul1 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({MUX_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));

    // 2× TCU (4 lanes each)
    VX_tcu_core_4lane tcu0 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({MUX_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));
    VX_tcu_core_4lane tcu1 (.clk(clk), .reset(reset),
        .exec_valid(1'b0), .exec_ready(dummy_ready[0]),
        .exec_data({MUX_DISPATCH_W{1'b0}}),
        .res_valid(dummy_res_valid[0]), .res_ready(1'b1),
        .res_data(dummy_res_data));
endmodule
