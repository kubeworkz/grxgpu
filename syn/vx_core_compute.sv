`default_nettype wire

// ============================================================
// G100 config constants
// ============================================================
localparam NUM_THREADS = 16;
localparam XLEN = 32;
localparam NW_WIDTH = 4;
localparam NUM_WARPS = 16;
localparam NUM_LANES = 16;
localparam NUM_ISSUE_WIDTH = 2;
localparam NUM_TCU_BLOCKS = 2;
localparam NUM_TCU_LANES = 16;
localparam EXECUTE_DATA_W = 1024;
localparam RESULT_DATA_W = 512;

// ============================================================
// VX_lane_dispatch: 1-cycle pipeline register for dispatch
// ============================================================
module VX_lane_dispatch (
    input  wire clk,
    input  wire reset,
    input  wire in_valid,
    output wire in_ready,
    input  wire [EXECUTE_DATA_W-1:0] in_data,
    output wire out_valid,
    input  wire out_ready,
    output wire [EXECUTE_DATA_W-1:0] out_data
);
    reg        valid_r;
    reg [EXECUTE_DATA_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) begin
            valid_r <= 0;
        end else if (in_valid && out_ready) begin
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
// VX_lane_gather: 1-cycle pipeline register for results
// ============================================================
module VX_lane_gather (
    input  wire clk,
    input  wire reset,
    input  wire in_valid,
    output wire in_ready,
    input  wire [RESULT_DATA_W-1:0] in_data,
    output wire out_valid,
    input  wire out_ready,
    output wire [RESULT_DATA_W-1:0] out_data
);
    reg        valid_r;
    reg [RESULT_DATA_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) begin
            valid_r <= 0;
        end else if (in_valid && out_ready) begin
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
// VX_tcu_core_stub: wrapper around the flattened TCU
// ============================================================
// NOTE: VX_tcu_core is defined in tcu_flat.sv (synthesized separately)
// This stub just passes through valid/ready/data for integration testing.

module VX_tcu_core (
    input  wire clk,
    input  wire reset,
    input  wire execute_if_valid,
    output wire execute_if_ready,
    input  wire [EXECUTE_DATA_W-1:0] execute_if_data,
    output wire result_if_valid,
    input  wire result_if_ready,
    output wire [RESULT_DATA_W-1:0] result_if_data
);
    // Pipeline: execute → 1 cycle → result
    reg        valid_r;
    reg [RESULT_DATA_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) begin
            valid_r <= 0;
        end else if (execute_if_valid && execute_if_ready) begin
            valid_r <= 1;
            // Pass through lower bits as result
            data_r <= execute_if_data[RESULT_DATA_W-1:0];
        end else if (result_if_ready) begin
            valid_r <= 0;
        end
    end

    assign execute_if_ready = result_if_ready;
    assign result_if_valid = valid_r;
    assign result_if_data = data_r;
endmodule

// ============================================================
// VX_alu_int_stub: 16-lane integer ALU (32-bit add/sub/shift/branch)
// ============================================================
module VX_alu_int (
    input  wire clk,
    input  wire reset,
    input  wire execute_if_valid,
    output wire execute_if_ready,
    input  wire [EXECUTE_DATA_W-1:0] execute_if_data,
    output wire result_if_valid,
    input  wire result_if_ready,
    output wire [RESULT_DATA_W-1:0] result_if_data,
    output wire branch_valid,
    output wire [1:0] branch_taken,
    output wire [XLEN-1:0] branch_target
);
    // 16-lane parallel adder/subtractor
    wire [NUM_LANES-1:0][XLEN-1:0] rs1, rs2;
    wire [NUM_LANES-1:0][XLEN-1:0] add_out, sub_out;
    wire [7:0] op_type;

    assign op_type = execute_if_data[7:0];
    assign rs1 = execute_if_data[EXECUTE_DATA_W/2-1:0];
    assign rs2 = execute_if_data[EXECUTE_DATA_W-1:EXECUTE_DATA_W/2];

    genvar i;
    for (i = 0; i < NUM_LANES; i = i + 1) begin : g_alu_lanes
        assign add_out[i] = rs1[i] + rs2[i];
        assign sub_out[i] = rs1[i] - rs2[i];
    end

    // 1-cycle pipeline
    reg        valid_r;
    reg [RESULT_DATA_W-1:0] data_r;
    reg        br_valid_r;
    reg [1:0]  br_taken_r;
    reg [XLEN-1:0] br_target_r;

    always @(posedge clk) begin
        if (reset) begin
            valid_r <= 0;
        end else if (execute_if_valid && execute_if_ready) begin
            valid_r <= 1;
            data_r <= {{(RESULT_DATA_W-XLEN){1'b0}}, add_out[0]};
            br_valid_r <= (op_type[7:4] == 4'hB); // branch opcodes
            br_taken_r <= {1'b0, ~sub_out[0][XLEN]};
            br_target_r <= add_out[0];
        end else if (result_if_ready) begin
            valid_r <= 0;
        end
    end

    assign execute_if_ready = result_if_ready;
    assign result_if_valid = valid_r;
    assign result_if_data = data_r;
    assign branch_valid = br_valid_r;
    assign branch_taken = br_taken_r;
    assign branch_target = br_target_r;
endmodule

// ============================================================
// VX_alu_muldiv_stub: 16-lane multiplier (1-cycle MUL, stub DIV)
// ============================================================
module VX_alu_muldiv (
    input  wire clk,
    input  wire reset,
    input  wire execute_if_valid,
    output wire execute_if_ready,
    input  wire [EXECUTE_DATA_W-1:0] execute_if_data,
    output wire result_if_valid,
    input  wire result_if_ready,
    output wire [RESULT_DATA_W-1:0] result_if_data
);
    wire [NUM_LANES-1:0][XLEN-1:0] rs1, rs2;
    wire [NUM_LANES-1:0][XLEN-1:0] mul_out;

    assign rs1 = execute_if_data[EXECUTE_DATA_W/2-1:0];
    assign rs2 = execute_if_data[EXECUTE_DATA_W-1:EXECUTE_DATA_W/2];

    genvar i;
    for (i = 0; i < NUM_LANES; i = i + 1) begin : g_mul
        assign mul_out[i] = rs1[i] * rs2[i];
    end

    reg        valid_r;
    reg [RESULT_DATA_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) begin
            valid_r <= 0;
        end else if (execute_if_valid && execute_if_ready) begin
            valid_r <= 1;
            data_r <= {{(RESULT_DATA_W-XLEN){1'b0}}, mul_out[0]};
        end else if (result_if_ready) begin
            valid_r <= 0;
        end
    end

    assign execute_if_ready = result_if_ready;
    assign result_if_valid = valid_r;
    assign result_if_data = data_r;
endmodule

// ============================================================
// VX_sfu_unit_stub: CSR + IMUL + scoreboard
// ============================================================
module VX_sfu_unit (
    input  wire clk,
    input  wire reset,
    input  wire execute_if_valid,
    output wire execute_if_ready,
    input  wire [EXECUTE_DATA_W-1:0] execute_if_data,
    output wire result_if_valid,
    input  wire result_if_ready,
    output wire [RESULT_DATA_W-1:0] result_if_data
);
    // CSR read/write: register file
    reg [XLEN-1:0] csr_regs [0:63];
    wire [5:0] csr_addr = execute_if_data[13:8];
    wire [XLEN-1:0] csr_wdata = execute_if_data[47:16];

    always @(posedge clk) begin
        if (execute_if_valid && execute_if_ready)
            csr_regs[csr_addr] <= csr_wdata;
    end

    reg        valid_r;
    reg [RESULT_DATA_W-1:0] data_r;

    always @(posedge clk) begin
        if (reset) begin
            valid_r <= 0;
        end else if (execute_if_valid && execute_if_ready) begin
            valid_r <= 1;
            data_r <= {{(RESULT_DATA_W-XLEN){1'b0}}, csr_regs[csr_addr]};
        end else if (result_if_ready) begin
            valid_r <= 0;
        end
    end

    assign execute_if_ready = result_if_ready;
    assign result_if_valid = valid_r;
    assign result_if_data = data_r;
endmodule

// ============================================================
// VX_core_compute_top: Full core compute block
// ============================================================
// Per G100 config: 2 ALU + 2 MULDIV + 2 TCU + 2 SFU + pipeline regs
// (NUM_ISSUE_WIDTH=2, each EX unit has BLOCK_SIZE=2)
// ============================================================
module VX_core_compute_top (
    input  wire clk,
    input  wire reset
);

    // ============================================================
    // Per-unit dispatch/commit buses
    // ============================================================
    wire [NUM_ISSUE_WIDTH-1:0] disp_valid, disp_ready;
    wire [EXECUTE_DATA_W-1:0]  disp_data [0:NUM_ISSUE_WIDTH-1];
    wire [NUM_ISSUE_WIDTH-1:0] comm_valid, comm_ready;
    wire [RESULT_DATA_W-1:0]   comm_data [0:NUM_ISSUE_WIDTH-1];

    // Tied-off dispatch inputs (not driven by scheduler in standalone synth)
    genvar i;
    for (i = 0; i < NUM_ISSUE_WIDTH; i = i + 1) begin : g_tie
        assign disp_valid[i] = 1'b0;
        assign disp_data[i] = {EXECUTE_DATA_W{1'b0}};
        assign comm_ready[i] = 1'b1;
    end

    // ============================================================
    // ALU blocks (2 instances, one per ISSUE_WIDTH slot)
    // ============================================================
    wire [NUM_ISSUE_WIDTH-1:0] alu_br_valid;
    wire [1:0] alu_br_taken [0:NUM_ISSUE_WIDTH-1];
    wire [XLEN-1:0] alu_br_target [0:NUM_ISSUE_WIDTH-1];

    for (i = 0; i < NUM_ISSUE_WIDTH; i = i + 1) begin : g_alu
        VX_alu_int alu (
            .clk              (clk),
            .reset            (reset),
            .execute_if_valid (disp_valid[i]),
            .execute_if_ready (disp_ready[i]),
            .execute_if_data  (disp_data[i]),
            .result_if_valid  (comm_valid[i]),
            .result_if_ready  (comm_ready[i]),
            .result_if_data   (comm_data[i]),
            .branch_valid     (alu_br_valid[i]),
            .branch_taken     (alu_br_taken[i]),
            .branch_target    (alu_br_target[i])
        );
    end

    // ============================================================
    // TCU blocks (2 instances)
    // ============================================================
    wire [NUM_ISSUE_WIDTH-1:0] tcu_disp_valid, tcu_disp_ready;
    wire [EXECUTE_DATA_W-1:0]  tcu_disp_data [0:NUM_ISSUE_WIDTH-1];
    wire [NUM_ISSUE_WIDTH-1:0] tcu_comm_valid, tcu_comm_ready;
    wire [RESULT_DATA_W-1:0]   tcu_comm_data [0:NUM_ISSUE_WIDTH-1];

    for (i = 0; i < NUM_ISSUE_WIDTH; i = i + 1) begin : g_tcu
        VX_tcu_core tcu (
            .clk               (clk),
            .reset             (reset),
            .execute_if_valid  (tcu_disp_valid[i]),
            .execute_if_ready  (tcu_disp_ready[i]),
            .execute_if_data   (tcu_disp_data[i]),
            .result_if_valid   (tcu_comm_valid[i]),
            .result_if_ready   (tcu_comm_ready[i]),
            .result_if_data    (tcu_comm_data[i])
        );
        assign tcu_disp_valid[i] = 1'b0;
        assign tcu_disp_data[i] = {EXECUTE_DATA_W{1'b0}};
        assign tcu_comm_ready[i] = 1'b1;
    end

    // ============================================================
    // MULDIV blocks (2 instances)
    // ============================================================
    wire [NUM_ISSUE_WIDTH-1:0] mul_disp_valid, mul_disp_ready;
    wire [EXECUTE_DATA_W-1:0]  mul_disp_data [0:NUM_ISSUE_WIDTH-1];
    wire [NUM_ISSUE_WIDTH-1:0] mul_comm_valid, mul_comm_ready;
    wire [RESULT_DATA_W-1:0]   mul_comm_data [0:NUM_ISSUE_WIDTH-1];

    for (i = 0; i < NUM_ISSUE_WIDTH; i = i + 1) begin : g_mul
        VX_alu_muldiv muldiv (
            .clk               (clk),
            .reset             (reset),
            .execute_if_valid  (mul_disp_valid[i]),
            .execute_if_ready  (mul_disp_ready[i]),
            .execute_if_data   (mul_disp_data[i]),
            .result_if_valid   (mul_comm_valid[i]),
            .result_if_ready   (mul_comm_ready[i]),
            .result_if_data    (mul_comm_data[i])
        );
        assign mul_disp_valid[i] = 1'b0;
        assign mul_disp_data[i] = {EXECUTE_DATA_W{1'b0}};
        assign mul_comm_ready[i] = 1'b1;
    end

    // ============================================================
    // SFU blocks (2 instances)
    // ============================================================
    wire [NUM_ISSUE_WIDTH-1:0] sfu_disp_valid, sfu_disp_ready;
    wire [EXECUTE_DATA_W-1:0]  sfu_disp_data [0:NUM_ISSUE_WIDTH-1];
    wire [NUM_ISSUE_WIDTH-1:0] sfu_comm_valid, sfu_comm_ready;
    wire [RESULT_DATA_W-1:0]   sfu_comm_data [0:NUM_ISSUE_WIDTH-1];

    for (i = 0; i < NUM_ISSUE_WIDTH; i = i + 1) begin : g_sfu
        VX_sfu_unit sfu (
            .clk               (clk),
            .reset             (reset),
            .execute_if_valid  (sfu_disp_valid[i]),
            .execute_if_ready  (sfu_disp_ready[i]),
            .execute_if_data   (sfu_disp_data[i]),
            .result_if_valid   (sfu_comm_valid[i]),
            .result_if_ready   (sfu_comm_ready[i]),
            .result_if_data    (sfu_comm_data[i])
        );
        assign sfu_disp_valid[i] = 1'b0;
        assign sfu_disp_data[i] = {EXECUTE_DATA_W{1'b0}};
        assign sfu_comm_ready[i] = 1'b1;
    end

    // ============================================================
    // Pipeline dispatch registers (2 per issue width)
    // ============================================================
    wire [NUM_ISSUE_WIDTH-1:0] pipe_disp_valid, pipe_disp_ready;
    wire [EXECUTE_DATA_W-1:0]  pipe_disp_data [0:NUM_ISSUE_WIDTH-1];

    for (i = 0; i < NUM_ISSUE_WIDTH; i = i + 1) begin : g_pipe
        VX_lane_dispatch dispatch (
            .clk      (clk),
            .reset    (reset),
            .in_valid (1'b0),
            .in_ready (),
            .in_data  ({EXECUTE_DATA_W{1'b0}}),
            .out_valid(pipe_disp_valid[i]),
            .out_ready(pipe_disp_ready[i]),
            .out_data (pipe_disp_data[i])
        );
    end

    // ============================================================
    // Pipeline gather registers (2 per issue width)
    // ============================================================
    wire [NUM_ISSUE_WIDTH-1:0] pipe_comm_valid, pipe_comm_ready;
    wire [RESULT_DATA_W-1:0]   pipe_comm_data [0:NUM_ISSUE_WIDTH-1];

    for (i = 0; i < NUM_ISSUE_WIDTH; i = i + 1) begin : g_gather
        VX_lane_gather gather (
            .clk      (clk),
            .reset    (reset),
            .in_valid (1'b0),
            .in_ready (),
            .in_data  ({RESULT_DATA_W{1'b0}}),
            .out_valid(pipe_comm_valid[i]),
            .out_ready(pipe_comm_ready[i]),
            .out_data (pipe_comm_data[i])
        );
    end

endmodule
