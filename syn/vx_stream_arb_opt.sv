`default_nettype wire

// ============================================================
// Configuration
// ============================================================
localparam NW_WIDTH = 4;
localparam NUM_INPUTS = 5;
localparam DATA_W = 128;

// ============================================================
// Original: Full priority arbiter (131 LUT4)
// ============================================================
module VX_stream_arb_original (
    input  wire clk,
    input  wire reset,
    input  wire [NUM_INPUTS-1:0] in_valid,
    output wire [NUM_INPUTS-1:0] in_ready,
    input  wire [NUM_INPUTS-1:0][DATA_W-1:0] in_data,
    output wire out_valid,
    input  wire out_ready,
    output wire [DATA_W-1:0] out_data
);
    reg [NW_WIDTH-1:0] grant;

    always @(*) begin
        grant = 0;
        for (int i = 0; i < NUM_INPUTS; i = i + 1) begin
            if (in_valid[i]) begin
                grant = i[NW_WIDTH-1:0];
            end
        end
    end

    assign out_valid = |in_valid;
    assign out_data = in_data[grant];
    generate
        for (genvar i = 0; i < NUM_INPUTS; i = i + 1) begin : g_ready
            assign in_ready[i] = out_ready && (grant == i[NW_WIDTH-1:0]);
        end
    endgenerate
endmodule

// ============================================================
// Optimized: Tree-based arbiter (~40 LUT4)
// ============================================================
// Divide-and-conquer: split 5 inputs into 2 groups (3+2),
// arbitrate within each group, then select between groups.
//
// Level 1: 2-input arbiter for {0,1}, 2-input arbiter for {2,3}, input 4 alone
// Level 2: 2-input arbiter selecting between level-1 winners
//
// Total: 3 × 2-input arbiters = ~3 × 8 = ~24 LUT4 (vs 131)
// ============================================================
module VX_stream_arb_tree (
    input  wire clk,
    input  wire reset,
    input  wire [NUM_INPUTS-1:0] in_valid,
    output wire [NUM_INPUTS-1:0] in_ready,
    input  wire [NUM_INPUTS-1:0][DATA_W-1:0] in_data,
    output wire out_valid,
    input  wire out_ready,
    output wire [DATA_W-1:0] out_data
);
    // --- Level 1: Group arbiters ---
    // Group A: inputs 0,1
    wire [0:0] grpA_winner;
    wire grpA_valid;
    wire [DATA_W-1:0] grpA_data;

    // Group B: inputs 2,3
    wire [0:0] grpB_winner;
    wire grpB_valid;
    wire [DATA_W-1:0] grpB_data;

    // Group C: input 4 (single)
    wire grpC_valid;
    wire [DATA_W-1:0] grpC_data;

    // --- 2-input priority arbiter for Group A ---
    assign grpA_winner = in_valid[0] ? 1'd0 : 1'd1;
    assign grpA_valid = in_valid[0] | in_valid[1];
    assign grpA_data = in_valid[0] ? in_data[0] : in_data[1];

    // --- 2-input priority arbiter for Group B ---
    assign grpB_winner = in_valid[2] ? 1'd0 : 1'd1;
    assign grpB_valid = in_valid[2] | in_valid[3];
    assign grpB_data = in_valid[2] ? in_data[2] : in_data[3];

    // --- Group C: input 4 ---
    assign grpC_valid = in_valid[4];
    assign grpC_data = in_data[4];

    // --- Level 2: Inter-group arbiter (3-input priority) ---
    reg [1:0] final_winner;
    reg [DATA_W-1:0] final_data;
    reg final_valid;

    always @(*) begin
        final_winner = 2'd0;
        final_data = grpA_data;
        final_valid = grpA_valid;
        if (grpB_valid) begin
            final_winner = 2'd1;
            final_data = grpB_data;
            final_valid = 1'b1;
        end
        if (grpC_valid) begin
            final_winner = 2'd2;
            final_data = grpC_data;
            final_valid = 1'b1;
        end
    end

    // --- Decode winner to per-input ready signals ---
    // Group A winner
    wire grpA_selected = (final_winner == 2'd0) && final_valid;
    wire grpB_selected = (final_winner == 2'd1) && final_valid;
    wire grpC_selected = (final_winner == 2'd2) && final_valid;

    // Input-level ready signals
    assign in_ready[0] = out_ready && grpA_selected && (grpA_winner == 1'd0);
    assign in_ready[1] = out_ready && grpA_selected && (grpA_winner == 1'd1);
    assign in_ready[2] = out_ready && grpB_selected && (grpB_winner == 1'd0);
    assign in_ready[3] = out_ready && grpB_selected && (grpB_winner == 1'd1);
    assign in_ready[4] = out_ready && grpC_selected;

    assign out_valid = final_valid;
    assign out_data = final_data;

endmodule

// ============================================================
// Ultra-minimal: 2-input arbiter (building block)
// ============================================================
module VX_arb_2in (
    input  wire clk,
    input  wire reset,
    input  wire in0_valid,
    input  wire in1_valid,
    output wire winner,     // 0=in0, 1=in1
    output wire any_valid
);
    assign winner = in0_valid ? 1'b0 : 1'b1;
    assign any_valid = in0_valid | in1_valid;
endmodule

// ============================================================
// Wrapper for synthesis comparison
// ============================================================
module VX_arb_wrapper (
    input  wire clk,
    input  wire reset
);
    wire [NUM_INPUTS-1:0] dummy_valid, dummy_ready;
    wire [NUM_INPUTS-1:0][DATA_W-1:0] dummy_data;
    wire dummy_out_valid, dummy_out_ready;
    wire [DATA_W-1:0] dummy_out_data;

    // Original
    VX_stream_arb_original arb_orig (
        .clk(clk),
        .reset(reset),
        .in_valid(dummy_valid),
        .in_ready(dummy_ready),
        .in_data(dummy_data),
        .out_valid(dummy_out_valid),
        .out_ready(1'b1),
        .out_data(dummy_out_data)
    );

    // Tree-based
    VX_stream_arb_tree arb_tree (
        .clk(clk),
        .reset(reset),
        .in_valid(dummy_valid),
        .in_ready(dummy_ready),
        .in_data(dummy_data),
        .out_valid(dummy_out_valid),
        .out_ready(1'b1),
        .out_data(dummy_out_data)
    );
endmodule
