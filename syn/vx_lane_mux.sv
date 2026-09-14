`default_nettype wire

// ============================================================
// Configuration
// ============================================================
localparam NUM_THREADS = 16;
localparam XLEN = 32;
localparam NUM_LANES = 16;
localparam LANES_PER_CYCLE = 4;
localparam MUX_CYCLES = 4;  // NUM_LANES / LANES_PER_CYCLE
localparam LANE_BITS = 2;   // $clog2(MUX_CYCLES)

// Full-width data paths (original design)
localparam FULL_DISPATCH_W = 1024;  // 16 lanes × 64 bits
localparam FULL_RESULT_W = 512;     // 16 lanes × 32 bits

// Muxed data paths (4× narrower)
localparam MUX_DISPATCH_W = 256;    // 4 lanes × 64 bits
localparam MUX_RESULT_W = 128;      // 4 lanes × 32 bits

// ============================================================
// VX_lane_dispatch_mux: Time-multiplexed dispatch register
// ============================================================
// Stores 4 lanes per cycle instead of 16, serializing over 4 cycles.
// Input:  Full 1024-bit dispatch packet (from scheduler)
// Output: 256-bit muxed dispatch packet (4 lanes per cycle)
//
// Throughput: 4 lanes/cycle (vs 16 lanes/cycle original)
// Area: ~4× fewer FFs in the register bank
// ============================================================
module VX_lane_dispatch_mux (
    input  wire clk,
    input  wire reset,

    // Full-width input (from scheduler, 16 lanes)
    input  wire in_valid,
    output wire in_ready,
    input  wire [FULL_DISPATCH_W-1:0] in_data,

    // Muxed output (to EX units, 4 lanes per cycle)
    output wire out_valid,
    input  wire out_ready,
    output wire [MUX_DISPATCH_W-1:0] out_data,

    // Lane counter for downstream to know which 4-lane slice
    output wire [LANE_BITS-1:0] out_lane_idx
);
    // Internal state
    reg [LANE_BITS-1:0] lane_counter;
    reg valid_r;
    reg [FULL_DISPATCH_W-1:0] data_r;

    // Extract 4-lane slice from stored full packet
    wire [MUX_DISPATCH_W-1:0] slice_data;
    assign slice_data = data_r[lane_counter * MUX_DISPATCH_W +: MUX_DISPATCH_W];

    // Handshake: accept new packet when all 4 cycles are done
    wire all_cycles_done = (lane_counter == MUX_CYCLES - 1) && out_ready;

    always @(posedge clk) begin
        if (reset) begin
            valid_r <= 0;
            lane_counter <= 0;
        end else begin
            if (in_valid && in_ready) begin
                // Load new packet
                valid_r <= 1;
                data_r <= in_data;
                lane_counter <= 0;
            end else if (valid_r && out_ready) begin
                // Advance to next 4-lane slice
                if (lane_counter == MUX_CYCLES - 1) begin
                    valid_r <= 0;
                    lane_counter <= 0;
                end else begin
                    lane_counter <= lane_counter + 1;
                end
            end
        end
    end

    assign in_ready = !valid_r || all_cycles_done;
    assign out_valid = valid_r;
    assign out_data = slice_data;
    assign out_lane_idx = lane_counter;

endmodule

// ============================================================
// VX_lane_gather_mux: Time-multiplexed gather register
// ============================================================
// Stores 4 result lanes per cycle instead of 16.
// Input:  128-bit muxed result (4 lanes per cycle from EX unit)
// Output: Full 512-bit result packet (after 4 cycles)
//
// Throughput: 4 lanes/cycle (matches muxed dispatch)
// Area: ~4× fewer FFs in the register bank
// ============================================================
module VX_lane_gather_mux (
    input  wire clk,
    input  wire reset,

    // Muxed input (from EX unit, 4 lanes per cycle)
    input  wire in_valid,
    output wire in_ready,
    input  wire [MUX_RESULT_W-1:0] in_data,
    input  wire [LANE_BITS-1:0] in_lane_idx,

    // Full-width output (to commit, 16 lanes)
    output wire out_valid,
    input  wire out_ready,
    output wire [FULL_RESULT_W-1:0] out_data
);
    // Internal state
    reg [LANE_BITS-1:0] lane_counter;
    reg valid_r;
    reg [FULL_RESULT_W-1:0] data_r;

    // Accept new 4-lane slice and store at correct offset
    wire [FULL_RESULT_W-1:0] updated_data;
    assign updated_data = (data_r & ~({{(FULL_RESULT_W-MUX_RESULT_W){1'b0}}, {MUX_RESULT_W{1'b1}}} << (in_lane_idx * MUX_RESULT_W)))
                        | ({{(FULL_RESULT_W-MUX_RESULT_W){1'b0}}, in_data} << (in_lane_idx * MUX_RESULT_W));

    // Handshake: output full packet when all 4 cycles received
    wire all_cycles_done = (lane_counter == MUX_CYCLES - 1) && in_valid;

    always @(posedge clk) begin
        if (reset) begin
            valid_r <= 0;
            lane_counter <= 0;
        end else begin
            if (in_valid && in_ready) begin
                // Store 4-lane slice
                data_r <= updated_data;
                lane_counter <= lane_counter + 1;

                // Mark valid when all cycles received
                if (lane_counter == MUX_CYCLES - 1) begin
                    valid_r <= 1;
                    lane_counter <= 0;
                end else begin
                    valid_r <= 0;
                end
            end else if (valid_r && out_ready) begin
                valid_r <= 0;
            end
        end
    end

    assign in_ready = !valid_r || (valid_r && out_ready);
    assign out_valid = valid_r;
    assign out_data = data_r;

endmodule

// ============================================================
// VX_lane_dispatch_original: Original 16-lane parallel register
// (for comparison)
// ============================================================
module VX_lane_dispatch_original (
    input  wire clk,
    input  wire reset,
    input  wire in_valid,
    output wire in_ready,
    input  wire [FULL_DISPATCH_W-1:0] in_data,
    output wire out_valid,
    input  wire out_ready,
    output wire [FULL_DISPATCH_W-1:0] out_data
);
    reg        valid_r;
    reg [FULL_DISPATCH_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) begin
            valid_r <= 0;
        end else if (in_valid && in_ready) begin
            valid_r <= 1;
            data_r <= in_data;
        end else if (out_ready) begin
            valid_r <= 0;
        end
    end

    assign out_valid = valid_r;
    assign out_data = data_r;
    assign in_ready = out_ready;

endmodule

// ============================================================
// VX_lane_gather_original: Original 16-lane parallel register
// (for comparison)
// ============================================================
module VX_lane_gather_original (
    input  wire clk,
    input  wire reset,
    input  wire in_valid,
    output wire in_ready,
    input  wire [FULL_RESULT_W-1:0] in_data,
    output wire out_valid,
    input  wire out_ready,
    output wire [FULL_RESULT_W-1:0] out_data
);
    reg        valid_r;
    reg [FULL_RESULT_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) begin
            valid_r <= 0;
        end else if (in_valid && in_ready) begin
            valid_r <= 1;
            data_r <= in_data;
        end else if (out_ready) begin
            valid_r <= 0;
        end
    end

    assign out_valid = valid_r;
    assign out_data = data_r;
    assign in_ready = out_ready;

endmodule

// ============================================================
// VX_core_mux_top: Wrapper for synthesis comparison
// ============================================================
module VX_core_mux_top (
    input  wire clk,
    input  wire reset
);
    // Original design
    wire orig_disp_valid, orig_disp_ready;
    wire [FULL_DISPATCH_W-1:0] orig_disp_data;
    wire orig_disp_out_valid;
    wire orig_disp_out_ready;
    wire [FULL_DISPATCH_W-1:0] orig_disp_out_data;

    wire orig_gath_valid, orig_gath_ready;
    wire [FULL_RESULT_W-1:0] orig_gath_data;
    wire orig_gath_out_valid;
    wire orig_gath_out_ready;
    wire [FULL_RESULT_W-1:0] orig_gath_out_data;

    VX_lane_dispatch_original orig_disp (
        .clk(clk), .reset(reset),
        .in_valid(1'b0), .in_ready(orig_disp_ready),
        .in_data({FULL_DISPATCH_W{1'b0}}),
        .out_valid(orig_disp_out_valid), .out_ready(1'b1),
        .out_data(orig_disp_out_data)
    );

    VX_lane_gather_original orig_gath (
        .clk(clk), .reset(reset),
        .in_valid(1'b0), .in_ready(orig_gath_ready),
        .in_data({FULL_RESULT_W{1'b0}}),
        .out_valid(orig_gath_out_valid), .out_ready(1'b1),
        .out_data(orig_gath_out_data)
    );

    // Time-muxed design
    wire mux_disp_valid, mux_disp_ready;
    wire [MUX_DISPATCH_W-1:0] mux_disp_data;
    wire mux_disp_out_valid;
    wire mux_disp_out_ready;
    wire [MUX_DISPATCH_W-1:0] mux_disp_out_data;
    wire [LANE_BITS-1:0] mux_disp_lane_idx;

    wire mux_gath_valid, mux_gath_ready;
    wire [MUX_RESULT_W-1:0] mux_gath_data;
    wire [LANE_BITS-1:0] mux_gath_lane_idx;
    wire mux_gath_out_valid;
    wire mux_gath_out_ready;
    wire [FULL_RESULT_W-1:0] mux_gath_out_data;

    VX_lane_dispatch_mux mux_disp (
        .clk(clk), .reset(reset),
        .in_valid(1'b0), .in_ready(mux_disp_ready),
        .in_data({FULL_DISPATCH_W{1'b0}}),
        .out_valid(mux_disp_out_valid), .out_ready(1'b1),
        .out_data(mux_disp_out_data),
        .out_lane_idx(mux_disp_lane_idx)
    );

    VX_lane_gather_mux mux_gath (
        .clk(clk), .reset(reset),
        .in_valid(1'b0), .in_ready(mux_gath_ready),
        .in_data({MUX_RESULT_W{1'b0}}),
        .in_lane_idx(2'd0),
        .out_valid(mux_gath_out_valid), .out_ready(1'b1),
        .out_data(mux_gath_out_data)
    );

endmodule
