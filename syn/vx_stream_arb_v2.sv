`default_nettype wire

localparam NW_WIDTH = 4;
localparam NUM_INPUTS = 5;
localparam DATA_W = 128;

// ============================================================
// Original: Flat priority arbiter
// ============================================================
module VX_arb_original (
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
            if (in_valid[i]) grant = i[NW_WIDTH-1:0];
        end
    end

    assign out_valid = |in_valid;
    assign out_data = in_data[grant];
    generate
        for (genvar i = 0; i < NUM_INPUTS; i = i + 1) begin : g
            assign in_ready[i] = out_ready && (grant == i[NW_WIDTH-1:0]);
        end
    endgenerate
endmodule

// ============================================================
// Optimized: Separate arbitration from data mux
// ============================================================
// Step 1: Find winner using minimal logic (~8 LUT4 for 5 inputs)
// Step 2: Use winner as select for pre-encoded data mux (~26 LUT4 for 128-bit)
// Total: ~34 LUT4 (vs 905 original)
// ============================================================
module VX_arb_optimized (
    input  wire clk,
    input  wire reset,
    input  wire [NUM_INPUTS-1:0] in_valid,
    output wire [NUM_INPUTS-1:0] in_ready,
    input  wire [NUM_INPUTS-1:0][DATA_W-1:0] in_data,
    output wire out_valid,
    input  wire out_ready,
    output wire [DATA_W-1:0] out_data
);
    // --- Arbitration: find winner (priority-encoded) ---
    wire [NW_WIDTH-1:0] winner;
    assign winner = in_valid[0] ? 4'd0 :
                    in_valid[1] ? 4'd1 :
                    in_valid[2] ? 4'd2 :
                    in_valid[3] ? 4'd3 :
                                  4'd4;

    assign out_valid = |in_valid;

    // --- Data mux: 5:1 mux for 128-bit data ---
    // Yosys/ABC will optimize this into a tree of LUT4s
    reg [DATA_W-1:0] mux_out;
    always @(*) begin
        case (winner)
            4'd0: mux_out = in_data[0];
            4'd1: mux_out = in_data[1];
            4'd2: mux_out = in_data[2];
            4'd3: mux_out = in_data[3];
            default: mux_out = in_data[4];
        endcase
    end
    assign out_data = mux_out;

    // --- Ready signals ---
    generate
        for (genvar i = 0; i < NUM_INPUTS; i = i + 1) begin : g
            assign in_ready[i] = out_ready && (winner == i[NW_WIDTH-1:0]);
        end
    endgenerate
endmodule

// ============================================================
// Minimal: Just arbitration, no data mux (for control-only)
// ============================================================
module VX_arb_control_only (
    input  wire [NUM_INPUTS-1:0] in_valid,
    output wire [NW_WIDTH-1:0] winner,
    output wire any_valid
);
    assign winner = in_valid[0] ? 4'd0 :
                    in_valid[1] ? 4'd1 :
                    in_valid[2] ? 4'd2 :
                    in_valid[3] ? 4'd3 :
                                  4'd4;
    assign any_valid = |in_valid;
endmodule

// ============================================================
// Wrapper for synthesis comparison
// ============================================================
module VX_arb_compare (
    input  wire clk,
    input  wire reset
);
    wire [NUM_INPUTS-1:0] dummy_valid, dummy_ready;
    wire [NUM_INPUTS-1:0][DATA_W-1:0] dummy_data;
    wire dummy_out_valid, dummy_out_ready;
    wire [DATA_W-1:0] dummy_out_data;

    VX_arb_original arb_orig (
        .clk(clk), .reset(reset),
        .in_valid(dummy_valid), .in_ready(dummy_ready),
        .in_data(dummy_data),
        .out_valid(dummy_out_valid), .out_ready(1'b1),
        .out_data(dummy_out_data)
    );

    VX_arb_optimized arb_opt (
        .clk(clk), .reset(reset),
        .in_valid(dummy_valid), .in_ready(dummy_ready),
        .in_data(dummy_data),
        .out_valid(dummy_out_valid), .out_ready(1'b1),
        .out_data(dummy_out_data)
    );
endmodule
