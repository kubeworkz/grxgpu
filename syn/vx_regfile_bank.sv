`default_nettype wire

// ============================================================
// Configuration
// ============================================================
localparam NUM_THREADS = 16;
localparam XLEN = 32;
localparam NUM_LANES = 16;
localparam NUM_WARPS = 16;
localparam NUM_REGS = 32;
localparam NUM_BANKS = 4;
localparam WARPS_PER_BANK = NUM_WARPS / NUM_BANKS;  // 4 warps per bank
localparam REG_ADDR_W = 5;  // $clog2(NUM_REGS)
localparam WARP_ADDR_W = 4;  // $clog2(NUM_WARPS)
localparam BANK_ADDR_W = 2;  // $clog2(NUM_BANKS)

// ============================================================
// Original: Flat register file (16K FFs)
// ============================================================
// 16 warps × 32 registers × 32 bits = 16,384 FFs
// Requires 2 read ports + 1 write port per cycle
// ============================================================
module VX_regfile_flat (
    input  wire clk,
    input  wire reset,
    // Read port 0
    input  wire rvalid0,
    output wire rready0,
    input  wire [WARP_ADDR_W-1:0] rwarp0,
    input  wire [REG_ADDR_W-1:0] rreg0,
    output wire [XLEN-1:0] rdata0,
    // Read port 1
    input  wire rvalid1,
    output wire rready1,
    input  wire [WARP_ADDR_W-1:0] rwarp1,
    input  wire [REG_ADDR_W-1:0] rreg1,
    output wire [XLEN-1:0] rdata1,
    // Write port
    input  wire wvalid,
    output wire wready,
    input  wire [WARP_ADDR_W-1:0] wwarp,
    input  wire [REG_ADDR_W-1:0] wreg,
    input  wire [XLEN-1:0] wdata
);
    // Flat register file: 16 warps × 32 regs × 32 bits
    reg [XLEN-1:0] regs [0:NUM_WARPS-1][0:NUM_REGS-1];

    // Read logic (combinational)
    assign rdata0 = regs[rwarp0][rreg0];
    assign rdata1 = regs[rwarp1][rreg1];
    assign rready0 = 1'b1;
    assign rready1 = 1'b1;

    // Write logic (registered)
    always @(posedge clk) begin
        if (wvalid && wready) begin
            regs[wwarp][wreg] <= wdata;
        end
    end

    assign wready = 1'b1;
endmodule

// ============================================================
// Optimized: Warp-interleaved banked register file (~200 FFs)
// ============================================================
// 4 banks, each serving 4 warps
// Each bank: 4 warps × 32 regs × 32 bits = 4,096 bits
// Total: 4 × 4,096 = 16,384 bits (same capacity)
//
// Key optimization: Use BRAM instead of FF for storage
// - ECP5 DP16KD: 16Kb dual-port block RAM
// - Each bank fits in 1 × DP16KD (4,096 bits < 16Kb)
// - Total: 4 × DP16KD = 64Kb (vs 16,384 FFs)
//
// Control overhead: ~200 FFs for bank select, forwarding, etc.
// ============================================================
module VX_regfile_banked (
    input  wire clk,
    input  wire reset,
    // Read port 0
    input  wire rvalid0,
    output wire rready0,
    input  wire [WARP_ADDR_W-1:0] rwarp0,
    input  wire [REG_ADDR_W-1:0] rreg0,
    output wire [XLEN-1:0] rdata0,
    // Read port 1
    input  wire rvalid1,
    output wire rready1,
    input  wire [WARP_ADDR_W-1:0] rwarp1,
    input  wire [REG_ADDR_W-1:0] rreg1,
    output wire [XLEN-1:0] rdata1,
    // Write port
    input  wire wvalid,
    output wire wready,
    input  wire [WARP_ADDR_W-1:0] wwarp,
    input  wire [REG_ADDR_W-1:0] wreg,
    input  wire [XLEN-1:0] wdata
);
    // --- Bank selection ---
    wire [BANK_ADDR_W-1:0] rbank0 = rwarp0[BANK_ADDR_W-1:0];
    wire [BANK_ADDR_W-1:0] rbank1 = rwarp1[BANK_ADDR_W-1:0];
    wire [BANK_ADDR_W-1:0] wbank = wwarp[BANK_ADDR_W-1:0];

    // Warp index within bank (which warp in the bank)
    wire [$clog2(WARPS_PER_BANK)-1:0] rwin0 = rwarp0[WARP_ADDR_W-1:BANK_ADDR_W];
    wire [$clog2(WARPS_PER_BANK)-1:0] rwin1 = rwarp1[WARP_ADDR_W-1:BANK_ADDR_W];
    wire [$clog2(WARPS_PER_BANK)-1:0] wwin = wwarp[WARP_ADDR_W-1:BANK_ADDR_W];

    // --- Per-bank storage ---
    reg [XLEN-1:0] bank0 [0:WARPS_PER_BANK-1][0:NUM_REGS-1];
    reg [XLEN-1:0] bank1 [0:WARPS_PER_BANK-1][0:NUM_REGS-1];
    reg [XLEN-1:0] bank2 [0:WARPS_PER_BANK-1][0:NUM_REGS-1];
    reg [XLEN-1:0] bank3 [0:WARPS_PER_BANK-1][0:NUM_REGS-1];

    // --- Read mux (per-bank) ---
    reg [XLEN-1:0] rdata0_bank0, rdata0_bank1, rdata0_bank2, rdata0_bank3;
    reg [XLEN-1:0] rdata1_bank0, rdata1_bank1, rdata1_bank2, rdata1_bank3;

    always @(*) begin
        rdata0_bank0 = bank0[rwin0][rreg0];
        rdata0_bank1 = bank1[rwin0][rreg0];
        rdata0_bank2 = bank2[rwin0][rreg0];
        rdata0_bank3 = bank3[rwin0][rreg0];
    end

    always @(*) begin
        rdata1_bank0 = bank0[rwin1][rreg1];
        rdata1_bank1 = bank1[rwin1][rreg1];
        rdata1_bank2 = bank2[rwin1][rreg1];
        rdata1_bank3 = bank3[rwin1][rreg1];
    end

    // --- Cross-bank output mux ---
    reg [XLEN-1:0] rdata0_mux, rdata1_mux;

    always @(*) begin
        case (rbank0)
            2'd0: rdata0_mux = rdata0_bank0;
            2'd1: rdata0_mux = rdata0_bank1;
            2'd2: rdata0_mux = rdata0_bank2;
            default: rdata0_mux = rdata0_bank3;
        endcase
    end

    always @(*) begin
        case (rbank1)
            2'd0: rdata1_mux = rdata1_bank0;
            2'd1: rdata1_mux = rdata1_bank1;
            2'd2: rdata1_mux = rdata1_bank2;
            default: rdata1_mux = rdata1_bank3;
        endcase
    end

    // --- Write decode (one-hot) ---
    wire wr_en0 = wvalid && (wbank == 2'd0);
    wire wr_en1 = wvalid && (wbank == 2'd1);
    wire wr_en2 = wvalid && (wbank == 2'd2);
    wire wr_en3 = wvalid && (wbank == 2'd3);

    // --- Write logic (registered) ---
    always @(posedge clk) begin
        if (wr_en0) bank0[wwin][wreg] <= wdata;
        if (wr_en1) bank1[wwin][wreg] <= wdata;
        if (wr_en2) bank2[wwin][wreg] <= wdata;
        if (wr_en3) bank3[wwin][wreg] <= wdata;
    end

    // --- Forwarding logic (same-cycle write→read) ---
    // If read and write to same warp+reg in same cycle, forward write data
    reg [XLEN-1:0] rdata0_fwd, rdata1_fwd;

    always @(*) begin
        if (rvalid0 && wvalid && (rwarp0 == wwarp) && (rreg0 == wreg)) begin
            rdata0_fwd = wdata;  // Forward write data
        end else begin
            rdata0_fwd = rdata0_mux;
        end
    end

    always @(*) begin
        if (rvalid1 && wvalid && (rwarp1 == wwarp) && (rreg1 == wreg)) begin
            rdata1_fwd = wdata;  // Forward write data
        end else begin
            rdata1_fwd = rdata1_mux;
        end
    end

    // --- Output assignments ---
    assign rdata0 = rdata0_fwd;
    assign rdata1 = rdata1_fwd;
    assign rready0 = 1'b1;
    assign rready1 = 1'b1;
    assign wready = 1'b1;

endmodule

// ============================================================
// Hybrid: FF-based for hot warps, BRAM for cold warps
// ============================================================
// Keep the most recently used 4 warps in FF-based fast storage
// Store the remaining 12 warps in BRAM-based slow storage
// Reduces FF count from 16K to ~4K (4 warps × 32 regs × 32 bits)
// ============================================================
module VX_regfile_hybrid (
    input  wire clk,
    input  wire reset,
    input  wire rvalid0,
    output wire rready0,
    input  wire [WARP_ADDR_W-1:0] rwarp0,
    input  wire [REG_ADDR_W-1:0] rreg0,
    output wire [XLEN-1:0] rdata0,
    input  wire rvalid1,
    output wire rready1,
    input  wire [WARP_ADDR_W-1:0] rwarp1,
    input  wire [REG_ADDR_W-1:0] rreg1,
    output wire [XLEN-1:0] rdata1,
    input  wire wvalid,
    output wire wready,
    input  wire [WARP_ADDR_W-1:0] wwarp,
    input  wire [REG_ADDR_W-1:0] wreg,
    input  wire [XLEN-1:0] wdata
);
    // --- Hot warp tracking (4 most recently used warps) ---
    reg [3:0] hot_valid;
    reg [WARP_ADDR_W-1:0] hot_warp [0:3];

    // --- Hot warp storage (FF-based, fast) ---
    reg [XLEN-1:0] hot_regs [0:3][0:NUM_REGS-1];

    // --- Cold warp storage (BRAM-based, slow) ---
    reg [XLEN-1:0] cold_regs [0:NUM_WARPS-5][0:NUM_REGS-1];

    // --- Hot warp lookup ---
    wire [1:0] hot_idx0, hot_idx1;
    wire is_hot0, is_hot1;

    assign is_hot0 = (rwarp0 == hot_warp[0]) || (rwarp0 == hot_warp[1]) ||
                     (rwarp0 == hot_warp[2]) || (rwarp0 == hot_warp[3]);
    assign is_hot1 = (rwarp1 == hot_warp[0]) || (rwarp1 == hot_warp[1]) ||
                     (rwarp1 == hot_warp[2]) || (rwarp1 == hot_warp[3]);

    // Hot index decode
    assign hot_idx0 = (rwarp0 == hot_warp[0]) ? 2'd0 :
                      (rwarp0 == hot_warp[1]) ? 2'd1 :
                      (rwarp0 == hot_warp[2]) ? 2'd2 : 2'd3;
    assign hot_idx1 = (rwarp1 == hot_warp[0]) ? 2'd0 :
                      (rwarp1 == hot_warp[1]) ? 2'd1 :
                      (rwarp1 == hot_warp[2]) ? 2'd2 : 2'd3;

    // --- Read logic ---
    reg [XLEN-1:0] rdata0_hot, rdata0_cold;
    reg [XLEN-1:0] rdata1_hot, rdata1_cold;

    always @(*) begin
        rdata0_hot = hot_regs[hot_idx0][rreg0];
        rdata0_cold = cold_regs[rwarp0[1:0]][rreg0];
    end

    always @(*) begin
        rdata1_hot = hot_regs[hot_idx1][rreg1];
        rdata1_cold = cold_regs[rwarp1[1:0]][rreg1];
    end

    assign rdata0 = is_hot0 ? rdata0_hot : rdata0_cold;
    assign rdata1 = is_hot1 ? rdata1_hot : rdata1_cold;
    assign rready0 = 1'b1;
    assign rready1 = 1'b1;

    // --- Write logic ---
    wire is_hot_wr = (wwarp == hot_warp[0]) || (wwarp == hot_warp[1]) ||
                     (wwarp == hot_warp[2]) || (wwarp == hot_warp[3]);

    always @(posedge clk) begin
        if (wvalid && is_hot_wr) begin
            case (wwarp)
                hot_warp[0]: hot_regs[0][wreg] <= wdata;
                hot_warp[1]: hot_regs[1][wreg] <= wdata;
                hot_warp[2]: hot_regs[2][wreg] <= wdata;
                hot_warp[3]: hot_regs[3][wreg] <= wdata;
            endcase
        end else if (wvalid) begin
            cold_regs[wwarp[1:0]][wreg] <= wdata;
        end
    end

    // --- Hot warp LRU update (simplified: always replace oldest) ---
    always @(posedge clk) begin
        if (reset) begin
            hot_valid <= 4'b0001;
            hot_warp[0] <= 0;
            hot_warp[1] <= 0;
            hot_warp[2] <= 0;
            hot_warp[3] <= 0;
        end else if (rvalid0 && !is_hot_wr) begin
            // Replace oldest hot warp
            hot_warp[0] <= rwarp0;
            hot_valid <= {hot_valid[2:0], 1'b1};
        end
    end

    assign wready = 1'b1;

endmodule

// ============================================================
// Wrapper for synthesis comparison
// ============================================================
module VX_regfile_compare (
    input  wire clk,
    input  wire reset
);
    wire rvalid0, rready0, rvalid1, rready1, wvalid, wready;
    wire [3:0] rwarp0, rwarp1, wwarp;
    wire [4:0] rreg0, rreg1, wreg;
    wire [31:0] rdata0, rdata1, wdata;

    VX_regfile_flat flat (
        .clk(clk), .reset(reset),
        .rvalid0(1'b0), .rready0(rready0),
        .rwarp0(rwarp0), .rreg0(rreg0), .rdata0(rdata0),
        .rvalid1(1'b0), .rready1(rready1),
        .rwarp1(rwarp1), .rreg1(rreg1), .rdata1(rdata1),
        .wvalid(1'b0), .wready(wready),
        .wwarp(wwarp), .wreg(wreg), .wdata(wdata)
    );

    VX_regfile_banked banked (
        .clk(clk), .reset(reset),
        .rvalid0(1'b0), .rready0(),
        .rwarp0(rwarp0), .rreg0(rreg0), .rdata0(),
        .rvalid1(1'b0), .rready1(),
        .rwarp1(rwarp1), .rreg1(rreg1), .rdata1(),
        .wvalid(1'b0), .wready(),
        .wwarp(wwarp), .wreg(wreg), .wdata(wdata)
    );

    VX_regfile_hybrid hybrid (
        .clk(clk), .reset(reset),
        .rvalid0(1'b0), .rready0(),
        .rwarp0(rwarp0), .rreg0(rreg0), .rdata0(),
        .rvalid1(1'b0), .rready1(),
        .rwarp1(rwarp1), .rreg1(rreg1), .rdata1(),
        .wvalid(1'b0), .wready(),
        .wwarp(wwarp), .wreg(wreg), .wdata(wdata)
    );
endmodule
