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
localparam NUM_EX_UNITS = 5;
localparam EX_BITS = 3;
localparam PERF_CTR_BITS = 32;

// Warp state
localparam WSTATE_BITS = 3;
localparam WSTATE_IDLE = 0;
localparam WSTATE_ACTIVE = 1;
localparam WSTATE_STALL = 2;

// Dispatch/commit widths
localparam DISPATCH_TAG_W = 8;
localparam COMMIT_TAG_W = 8;
localparam INSTR_W = 32;
localparam PC_W = 32;

// ============================================================
// VX_priority_encoder: N-input priority encoder
// ============================================================
module VX_priority_encoder (
    input  wire [NUM_WARPS-1:0] in,
    output wire [NW_WIDTH-1:0]  out,
    output wire                 valid
);
    assign valid = |in;
    assign out = in[0]  ? 4'd0  :
                 in[1]  ? 4'd1  :
                 in[2]  ? 4'd2  :
                 in[3]  ? 4'd3  :
                 in[4]  ? 4'd4  :
                 in[5]  ? 4'd5  :
                 in[6]  ? 4'd6  :
                 in[7]  ? 4'd7  :
                 in[8]  ? 4'd8  :
                 in[9]  ? 4'd9  :
                 in[10] ? 4'd10 :
                 in[11] ? 4'd11 :
                 in[12] ? 4'd12 :
                 in[13] ? 4'd13 :
                 in[14] ? 4'd14 :
                          4'd15;
endmodule

// ============================================================
// VX_pending_size: Count pending requests (used in scheduler)
// ============================================================
module VX_pending_size (
    input  wire clk,
    input  wire reset,
    input  wire push,
    input  wire pop,
    output wire empty,
    output wire full,
    output wire [$clog2(NUM_WARPS+1)-1:0] count
);
    reg [$clog2(NUM_WARPS+1)-1:0] cnt;

    always @(posedge clk) begin
        if (reset)
            cnt <= 0;
        else begin
            case ({push, pop})
                2'b10: cnt <= cnt + 1;
                2'b01: cnt <= cnt - 1;
                default: cnt <= cnt;
            endcase
        end
    end

    assign count = cnt;
    assign empty = (cnt == 0);
    assign full = (cnt == NUM_WARPS);
endmodule

// ============================================================
// VX_uuid_gen: Unique ID generator (counter-based)
// ============================================================
module VX_uuid_gen (
    input  wire clk,
    input  wire reset,
    output wire [31:0] uuid_out
);
    reg [31:0] counter;

    always @(posedge clk) begin
        if (reset)
            counter <= 0;
        else
            counter <= counter + 1;
    end

    assign uuid_out = counter;
endmodule

// ============================================================
// VX_elastic_buffer: Pipeline buffer with valid/ready handshake
// ============================================================
module VX_elastic_buffer #(
    parameter DATA_W = 128
) (
    input  wire clk,
    input  wire reset,
    input  wire in_valid,
    output wire in_ready,
    input  wire [DATA_W-1:0] in_data,
    output wire out_valid,
    input  wire out_ready,
    output wire [DATA_W-1:0] out_data
);
    reg        valid_r;
    reg [DATA_W-1:0] data_r;

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
// VX_stream_arb: Stream arbiter (round-robin or priority)
// ============================================================
module VX_stream_arb #(
    parameter NUM_INPUTS = 2,
    parameter ARBITER = "R"  // "R" = round-robin, "P" = priority
) (
    input  wire clk,
    input  wire reset,
    // Inputs
    input  wire [NUM_INPUTS-1:0] in_valid,
    output wire [NUM_INPUTS-1:0] in_ready,
    input  wire [NUM_INPUTS-1:0][127:0] in_data,
    // Output
    output wire out_valid,
    input  wire out_ready,
    output wire [127:0] out_data
);
    reg [NW_WIDTH-1:0] grant;

    // Simple priority arbiter
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
// VX_split_join: Warp split/join control
// ============================================================
module VX_split_join (
    input  wire clk,
    input  wire reset,
    input  wire split_valid,
    input  wire join_valid,
    output wire [$clog2(NUM_WARPS+1)-1:0] active_warps
);
    reg [$clog2(NUM_WARPS+1)-1:0] warp_cnt;

    always @(posedge clk) begin
        if (reset)
            warp_cnt <= 1;  // Start with 1 active warp
        else begin
            case ({split_valid, join_valid})
                2'b10: warp_cnt <= warp_cnt + 1;
                2'b01: warp_cnt <= warp_cnt - 1;
                default: warp_cnt <= warp_cnt;
            endcase
        end
    end

    assign active_warps = warp_cnt;
endmodule

// ============================================================
// VX_bar_unit: Barrier synchronization unit
// ============================================================
module VX_bar_unit (
    input  wire clk,
    input  wire reset,
    input  wire arrive_valid,
    input  wire [NW_WIDTH-1:0] arrive_wid,
    output wire depart_valid,
    output wire [NW_WIDTH-1:0] depart_wid
);
    // Simple barrier: accumulate arrivals, depart when all warps arrive
    reg [NUM_WARPS-1:0] arrived;
    wire all_arrived;

    always @(posedge clk) begin
        if (reset)
            arrived <= 0;
        else if (arrive_valid)
            arrived[arrive_wid] <= 1'b1;
    end

    assign all_arrived = &arrived;
    assign depart_valid = all_arrived;
    assign depart_wid = arrive_wid;

    // Reset arrived flags on depart
    always @(posedge clk) begin
        if (reset)
            arrived <= 0;
        else if (depart_valid)
            arrived <= 0;
    end
endmodule

// ============================================================
// VX_scheduler_top: Scheduler control logic
// ============================================================
module VX_scheduler_top (
    input  wire clk,
    input  wire reset
);
    // Warp scoreboard
    reg [NUM_WARPS-1:0] warp_active;
    reg [NUM_WARPS-1:0] warp_stalled;
    wire [NW_WIDTH-1:0] sched_warp;
    wire sched_valid;

    // Priority encoder for warp selection
    wire [NUM_WARPS-1:0] ready_warps = warp_active & ~warp_stalled;

    VX_priority_encoder pe (
        .in(ready_warps),
        .out(sched_warp),
        .valid(sched_valid)
    );

    // Pending instruction counter
    wire pending_empty, pending_full;
    wire [$clog2(NUM_WARPS+1)-1:0] pending_count;

    VX_pending_size pending (
        .clk(clk),
        .reset(reset),
        .push(sched_valid),
        .pop(1'b0),
        .empty(pending_empty),
        .full(pending_full),
        .count(pending_count)
    );

    // UUID generator
    wire [31:0] uuid;
    VX_uuid_gen uuid_gen (
        .clk(clk),
        .reset(reset),
        .uuid_out(uuid)
    );

    // Barrier unit
    wire bar_depart_valid;
    wire [NW_WIDTH-1:0] bar_depart_wid;
    VX_bar_unit bar (
        .clk(clk),
        .reset(reset),
        .arrive_valid(1'b0),
        .arrive_wid(0),
        .depart_valid(bar_depart_valid),
        .depart_wid(bar_depart_wid)
    );

    // Split/join control
    wire [$clog2(NUM_WARPS+1)-1:0] active_warps;
    VX_split_join sj (
        .clk(clk),
        .reset(reset),
        .split_valid(1'b0),
        .join_valid(bar_depart_valid),
        .active_warps(active_warps)
    );

    // Warp state management
    always @(posedge clk) begin
        if (reset) begin
            warp_active <= 1;  // Warp 0 active
            warp_stalled <= 0;
        end else begin
            // Activate new warps from CTA dispatch
            if (1'b0) begin  // stub: cta_dispatch
                warp_active[0] <= 1;
            end
            // Stall on memory
            if (1'b0) begin  // stub: memory stall
                warp_stalled[sched_warp] <= 1;
            end
        end
    end
endmodule

// ============================================================
// VX_decode_top: Instruction decode control logic
// ============================================================
module VX_decode_top (
    input  wire clk,
    input  wire reset
);
    // Instruction register file (simplified)
    reg [INSTR_W-1:0] irf [0:NUM_WARPS-1][0:31];
    reg [NW_WIDTH-1:0] last_wid;
    reg last_valid;

    // Decode logic (simplified)
    wire [5:0] rd, rs1, rs2;
    wire [INSTR_W-1:0] instr;

    // Elastic buffer for decoded instruction
    localparam DECODE_DATA_W = INSTR_W + NW_WIDTH + PC_W + 32;  // instr + wid + pc + extras
    wire dec_out_valid, dec_out_ready;
    wire [DECODE_DATA_W-1:0] dec_out_data;

    VX_elastic_buffer #(.DATA_W(DECODE_DATA_W)) dec_buf (
        .clk(clk),
        .reset(reset),
        .in_valid(1'b0),
        .in_ready(),
        .in_data(0),
        .out_valid(dec_out_valid),
        .out_ready(1'b1),
        .out_data(dec_out_data)
    );

    // Instruction decode (simplified)
    always @(posedge clk) begin
        if (reset) begin
            last_valid <= 0;
        end else begin
            last_valid <= 1'b0;  // stub
        end
    end
endmodule

// ============================================================
// VX_commit_top: Commit logic with stream arbiter
// ============================================================
module VX_commit_top (
    input  wire clk,
    input  wire reset
);
    // Per-unit commit buses
    wire [NUM_EX_UNITS-1:0] unit_valid;
    wire [NUM_EX_UNITS-1:0][255:0] unit_data;

    // Commit arbiter (round-robin across EX units)
    VX_stream_arb #(
        .NUM_INPUTS(NUM_EX_UNITS),
        .ARBITER("R")
    ) commit_arb (
        .clk(clk),
        .reset(reset),
        .in_valid(unit_valid),
        .in_ready(),
        .in_data(unit_data),
        .out_valid(),
        .out_ready(1'b1),
        .out_data()
    );

    // Warp state update on commit
    reg [NUM_WARPS-1:0] warp_committed;

    always @(posedge clk) begin
        if (reset)
            warp_committed <= 0;
        else
            warp_committed <= 0;  // stub
    end
endmodule

// ============================================================
// VX_fetch_top: Instruction fetch control
// ============================================================
module VX_fetch_top (
    input  wire clk,
    input  wire reset
);
    // PC register file
    reg [PC_W-1:0] pc [0:NUM_WARPS-1];
    reg [NUM_WARPS-1:0] fetch_pending;

    // Branch prediction (simplified: always not-taken)
    wire [PC_W-1:0] next_pc;
    wire branch_taken;

    // Instruction memory interface (stub)
    wire imem_valid, imem_ready;
    wire [PC_W-1:0] imem_addr;
    wire [INSTR_W-1:0] imem_data;

    // Elastic buffer for fetched instruction
    localparam FETCH_DATA_W = INSTR_W + NW_WIDTH + PC_W;
    wire fetch_out_valid, fetch_out_ready;
    wire [FETCH_DATA_W-1:0] fetch_out_data;

    VX_elastic_buffer #(.DATA_W(FETCH_DATA_W)) fetch_buf (
        .clk(clk),
        .reset(reset),
        .in_valid(1'b0),
        .in_ready(),
        .in_data(0),
        .out_valid(fetch_out_valid),
        .out_ready(1'b1),
        .out_data(fetch_out_data)
    );

    // UUID for fetched instruction
    wire [31:0] fetch_uuid;
    VX_uuid_gen fetch_uuid_gen (
        .clk(clk),
        .reset(reset),
        .uuid_out(fetch_uuid)
    );

    // PC management
    always @(posedge clk) begin
        if (reset) begin
            fetch_pending <= 1;  // Warp 0 fetching
        end else begin
            // Update PC on branch or sequential
            if (branch_taken)
                pc[0] <= next_pc;
            else
                pc[0] <= pc[0] + 4;
        end
    end
endmodule

// ============================================================
// VX_pipeline_control_top: Full pipeline control block
// ============================================================
module VX_pipeline_control_top (
    input  wire clk,
    input  wire reset
);
    // Fetch stage
    VX_fetch_top fetch (
        .clk(clk),
        .reset(reset)
    );

    // Decode stage
    VX_decode_top decode (
        .clk(clk),
        .reset(reset)
    );

    // Scheduler stage
    VX_scheduler_top scheduler (
        .clk(clk),
        .reset(reset)
    );

    // Commit stage
    VX_commit_top commit (
        .clk(clk),
        .reset(reset)
    );
endmodule
