// Copyright © 2019-2023
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

`include "VX_cache_define.vh"

// Per-LLC-bank AMO helper: the RVA RMW kernel + a small reservation cache.
//
// Reservations are tracked by a bounded, fixed-size set of stations per bank
// (NUM_RS, default load-matched to system concurrency) rather than a slot per
// hart. The cache is line-indexed (direct-mapped on the reserved line's low
// address bits): the {hart,tag} payload lives in a synchronous block RAM read
// one stage ahead (look-ahead address, the VX_cache_tags pattern) so the
// registered output lands the same cycle the SC commit decision is made; the
// valid bits live in resettable flops (BRAM contents are not reset).
//
//   LR  : claim the slot for {hart, line} if it is free or already ours; an
//         occupied slot stays with its owner until that owner's SC, a write,
//         or the hold deadline (see rs_busy).
//   SC  : succeeds iff the slot still holds {hart, line}; the success store
//         then clears it through the write path below.
//   write: a committed store/RMW to a line clears the slot iff it holds that
//          line (tag match) — breaks the reserver, any hart.
//
// A bounded set is RISC-V-legal: SC may fail spuriously for any reason. What a
// bounded set cannot do is let one hart's LR evict another hart's live
// reservation: the set would then hold only the newest LR, and with enough
// harts contending on one line every SC would find a stranger's tag and fail,
// so the retry loop would livelock instead of converging. An occupied station
// therefore stays with its owner until that owner's SC resolves it; harts that
// cannot get a station simply fail their SC and retry. Nor may a station be
// held forever by a reservation that is never retired, since that bars every
// other hart from the index with no store coming to break it -- hence the
// hold deadline. This keeps the per-hart table's O(NUM_HARTS) storage and CAM
// off the critical path while still guaranteeing that every station retires.
module VX_amo_unit import VX_gpu_pkg::*; #(
    parameter NUM_RES_ENTRIES = 4,   // reservation stations per bank (NUM_RS)
    parameter AMO_TURNAROUND  = 64,  // cycles one AMO round trip adds to another hart's wait
    parameter LINE_ADDR_BITS  = 32,
    parameter DATA_WIDTH      = 64   // ALU operand width (cache word, capped at 64)
) (
    input  wire                          clk,
    input  wire                          reset,
    input  wire                          pipe_stall,

    // Combinational compute kernel.
    input  amo_op_e                      compute_op,
    input  wire                          compute_unsigned,
    input  wire [1:0]                    compute_width,
    input  wire [63:0]                   compute_old,
    input  wire [63:0]                   compute_rhs,
    output wire [63:0]                   compute_new_word,
    output wire [63:0]                   compute_ret_word,

    // Reservation activity (single-fire per cycle).
    input  wire                          res_reserve,    // LR commit
    input  wire                          res_clear,      // SC commit (success or fail)
    input  wire                          res_invalidate, // committed write to res_line_addr
    input  wire [HART_ID_WIDTH-1:0]      res_hart_id,
    input  wire [LINE_ADDR_BITS-1:0]     res_line_addr,   // committed line (stC)
    input  wire [LINE_ADDR_BITS-1:0]     res_line_addr_n, // line entering stC next cycle
    output wire                          res_check        // SC outcome (1 = match)
);

    // Pure ALU (no state, no clock).
    VX_amo_alu #(
        .DATA_WIDTH (DATA_WIDTH)
    ) alu (
        .op       (compute_op),
        .is_unsigned (compute_unsigned),
        .width    (compute_width),
        .old_word (compute_old),
        .rhs      (compute_rhs),
        .new_word (compute_new_word),
        .ret_word (compute_ret_word)
    );

    // ============================================================
    // Reservation cache: NUM_RS stations, line-indexed.
    // ============================================================
    // Effective capacity is the next power-of-two >= NUM_RS (>=2), so the line
    // index fully covers the storage depth for any requested NUM_RS.
    localparam RS_ADDRW    = `UP(`CLOG2(NUM_RES_ENTRIES));
    localparam RS_DEPTH    = 1 << RS_ADDRW;
    localparam RS_TAG_BITS = LINE_ADDR_BITS - RS_ADDRW;   // {tag,idx} = full line
    localparam RS_DATA_W   = HART_ID_WIDTH + RS_TAG_BITS;  // BRAM payload: {hart, tag}

    wire en = ~pipe_stall;

    // index by the reserved line's low bits; the rest is the stored tag.
    // (only the index bits of the look-ahead address are needed)
    wire [RS_ADDRW-1:0]    rs_idx   = res_line_addr  [RS_ADDRW-1:0];
    wire [RS_ADDRW-1:0]    rs_idx_n = res_line_addr_n[RS_ADDRW-1:0];
    wire [RS_TAG_BITS-1:0] rs_tag   = res_line_addr[LINE_ADDR_BITS-1:RS_ADDRW];
    `UNUSED_VAR (res_line_addr_n)

    // Look-ahead BRAM payload (cache_tags pattern): read at the next index so
    // the registered output presents the entry at the commit cycle (stC); the
    // LR installs {hart,tag} at the committed index.
    wire                 rs_we;
    wire [RS_DATA_W-1:0] rs_wdata = {res_hart_id, rs_tag};
    wire [RS_DATA_W-1:0] rs_rdata;
    VX_dp_ram #(
        .DATAW    (RS_DATA_W),
        .SIZE     (RS_DEPTH),
        .OUT_REG  (1),
        .RDW_MODE ("R")
    ) rs_store (
        .clk   (clk),
        .reset (reset),
        .read  (en),
        .write (rs_we),
        .wren  (1'b1),
        .waddr (rs_idx),
        .raddr (rs_idx_n),
        .wdata (rs_wdata),
        .rdata (rs_rdata)
    );

    // Read-during-write forward: an LR installs at the committed index the same
    // cycle the next op prefetches it; the registered read would miss it, so
    // forward the just-written payload for one cycle.
    wire                 rdw_set = rs_we && (rs_idx == rs_idx_n);
    reg                  rdw_valid_r;
    reg [RS_DATA_W-1:0]  rdw_data_r;
    always @(posedge clk) begin
        if (reset) begin
            rdw_valid_r <= 1'b0;
        end else if (en) begin
            rdw_valid_r <= rdw_set;
            rdw_data_r  <= rs_wdata;
        end
    end
    wire [RS_DATA_W-1:0] rs_data = rdw_valid_r ? rdw_data_r : rs_rdata;

    // current entry at the committed line index: valid from flops, payload from BRAM
    reg  [RS_DEPTH-1:0]      rs_valid;
    wire                     e_valid = rs_valid[rs_idx];
    wire [HART_ID_WIDTH-1:0] e_hart  = rs_data[RS_TAG_BITS +: HART_ID_WIDTH];
    wire [RS_TAG_BITS-1:0]   e_tag   = rs_data[RS_TAG_BITS-1:0];

    // Hold deadline. A station is only ever retired by its owner's SC or by a
    // committed write to the line, so a reservation whose SC never arrives --
    // the hart left the LR/SC sequence, or the SC pairs with another address --
    // would hold its index for the rest of the run. Every LR to that index is
    // then refused, and no store to the line is coming to break it, so other
    // harts' loops could never win: the ISA's eventuality guarantee forbids
    // exactly that, because loads and load-reserved instructions of one hart
    // may not impede another hart's LR/SC loop indefinitely. Lapsing an
    // unclaimed station only turns an SC that would have won into a spurious
    // failure, which SC permits, and it keeps every station re-acquirable.
    //
    // The bound is one AMO_TURNAROUND per hart that can queue ahead of the SC,
    // plus the requester's own trip, so it scales with the config instead of
    // being a literal. Measured LR install -> that hart's SC commit
    // (lrsc_counter -n32), average/worst: 57/73 cycles at 16 harts, 62/103 at
    // 32 and 79/214 at 64. The 32- and 64-hart machines were built both by
    // adding cores and by adding warps, and the two agreed within ~10%, so the
    // growth is the hart count and not the depth of the AMO queue or of this
    // station table. The per-hart share rises with contention in the shared
    // L2 AMO path (1.4 to 2.6 cycles) but stays far under AMO_TURNAROUND, so
    // AMO_TURNAROUND x (NUM_HARTS + 1) clears the worst case by 15-21x at
    // every size while a small machine keeps a floor above its own trip. A
    // bound under the gap is what fails every SC, so the floor matters as much
    // as the hart term.
    //
    // Lapsing is safe: expiry only *removes* a station, so line_match and
    // own_match go false and an SC that would have won fails spuriously --
    // permitted by Zalrsc, and the retry loop re-establishes the reservation.
    // It can never make an SC succeed that should fail, because forgetting a
    // reservation never invents one.
    localparam NUM_HARTS       = 1 << HART_ID_WIDTH;   // hart-id space of the config
    localparam RES_HOLD_CYCLES = AMO_TURNAROUND * (NUM_HARTS + 1);
    localparam RES_HOLD_BITS   = `CLOG2(RES_HOLD_CYCLES + 1);
    localparam [RES_HOLD_BITS-1:0] RES_HOLD_TICKS = RES_HOLD_BITS'(RES_HOLD_CYCLES);
    reg  [RES_HOLD_BITS-1:0] rs_age [RS_DEPTH];
    wire                     e_expired = e_valid && (rs_age[rs_idx] >= RES_HOLD_TICKS);

    wire line_match = e_valid && ~e_expired && (e_tag == rs_tag);  // slot holds this line
    wire own_match  = line_match && (e_hart == res_hart_id);      // ...reserved by this hart

    // SC outcome: this hart's reservation on this line is still live.
    assign res_check = own_match;

    // A station belongs to exactly one reservation until that holder's SC
    // retires it or a committed write breaks it. A younger LR from another
    // hart must leave it alone: letting LR steal the station makes it track
    // only the most recent LR, so as soon as LRs arrive faster than one hart's
    // LR->SC gap every SC reads someone else's tag and fails, the retry loop
    // re-issues LR+SC, and no SC ever retires. Refusing the install costs the
    // blocked hart one spurious SC failure (legal, and it retries), while the
    // holder always reaches its own SC and frees the station -- so each
    // station retires in bounded time and the LR/SC loop makes progress.
    wire rs_busy = e_valid && ~e_expired && ~own_match;
    assign rs_we = res_reserve && en && ~rs_busy;
    wire   rs_clr = en && ((res_invalidate && line_match)      // any write breaks the reserver
                        || (res_clear && own_match));          // SC clears its own

    always @(posedge clk) begin
        if (reset) begin
            rs_valid <= '0;
        end else begin
            if (rs_we) begin
                rs_valid[rs_idx] <= 1'b1;
            end else if (rs_clr || e_expired) begin
                rs_valid[rs_idx] <= 1'b0;
            end
        end
    end

    // Age runs from install (or clear) to the deadline; a lapsed station stops
    // answering for its old owner and stops refusing other harts' LRs.
    always @(posedge clk) begin
        if (reset) begin
            for (int i = 0; i < RS_DEPTH; ++i) begin
                rs_age[i] <= '0;
            end
        end else begin
            for (int i = 0; i < RS_DEPTH; ++i) begin
                if ((rs_we || rs_clr) && (rs_idx == RS_ADDRW'(i))) begin
                    rs_age[i] <= '0;
                end else if (rs_valid[i] && ~(&rs_age[i])) begin
                    rs_age[i] <= rs_age[i] + 1'b1;
                end
            end
        end
    end

endmodule
