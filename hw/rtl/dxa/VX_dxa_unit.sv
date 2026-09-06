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

`include "VX_define.vh"

module VX_dxa_unit import VX_gpu_pkg::*, VX_dxa_pkg::*; #(
    parameter `STRING INSTANCE_ID = "",
    parameter CORE_ID = 0
) (
    input wire              clk,
    input wire              reset,

    VX_execute_if.slave     execute_if,
    VX_result_if.master     result_if,
    VX_dxa_req_bus_if.master dxa_req_bus_if
);
    `UNUSED_SPARAM (INSTANCE_ID)
    `UNUSED_VAR (execute_if.data.rs3_data)

    // Wgather-based layout (lane index = thread_id & 3):
    //   Non-pair: lane0 rs1=smem_addr,  rs2=coord2
    //             lane1 rs1=meta,       rs2=coord3
    //             lane2 rs1=coord0,     rs2=coord4
    //             lane3 rs1=coord1,     rs2=cta_mask (multicast)
    //   Fused pair (meta[31] = 1, set by vx_dxa_issue_2d_wg_pair):
    //             rs1 lanes carry A (smem_a, meta|PAIR, coord_a0, coord_a1);
    //             rs2 lanes carry B (smem_b, meta_b, coord_b0, coord_b1).
    wire [`VX_CFG_XLEN-1:0] lane0_rs1 = execute_if.data.rs1_data[0];
    wire [`VX_CFG_XLEN-1:0] lane1_rs1 = execute_if.data.rs1_data[1];
    wire [`VX_CFG_XLEN-1:0] lane2_rs1 = execute_if.data.rs1_data[2];
    wire [`VX_CFG_XLEN-1:0] lane3_rs1 = execute_if.data.rs1_data[3];
    wire [`VX_CFG_XLEN-1:0] lane0_rs2 = execute_if.data.rs2_data[0];
    wire [`VX_CFG_XLEN-1:0] lane1_rs2 = execute_if.data.rs2_data[1];
    wire [`VX_CFG_XLEN-1:0] lane2_rs2 = execute_if.data.rs2_data[2];
    wire [`VX_CFG_XLEN-1:0] lane3_rs2 = execute_if.data.rs2_data[3];

    // meta[31] = fused A+B pair flag (exclusive: pack_meta only uses bits
    // [30:0] = (barrier_id << 4) | desc_slot).
    wire pair_iss = lane1_rs1[31];

    // Cluster-contiguous LMEM placement guarantees receiver bases are
    // `issuer_base + r × smem_stride`, so the bus carries the issuer's
    // LMEM-relative byte address (issuer_lmem_base + intra). The per-beat
    // receiver address is `bus_addr + r × stride` and is computed in
    // VX_dxa_smem_wr's replay path. No issuer-side intra_offset, no
    // per-receiver translation in VX_mem_unit.

    // Strip the global LMEM base prefix to land in LMEM's own byte-address
    // space. Equivalently: `lane0_rs1[LMEM_BYTE_W-1:0]`, since `lane0_rs1`
    // is a kernel-supplied LMEM pointer whose high bits ARE VX_MEM_LMEM_BASE
    // when the kernel uses `__local_mem()` derivatives.
    wire [`VX_CFG_XLEN-1:0] lmem_rel_byte_addr =
        lane0_rs1 - `VX_CFG_XLEN'(`VX_MEM_LMEM_BASE_ADDR);

    // ── Request A: the legacy single-tile mapping ────────────────────────
    // In pair mode the rs2 lanes carry B's fields (not coords[2..4] / the
    // multicast mask), so those are zeroed and the PAIR meta bit is cleared;
    // the desc-slot and bar-id bits are untouched.
    dxa_req_data_t req_a_data;
    assign req_a_data.core_id   = NC_WIDTH'(CORE_ID);
    assign req_a_data.uuid      = execute_if.data.header.uuid;
    assign req_a_data.wid       = execute_if.data.header.wid;
    assign req_a_data.smem_addr = lmem_rel_byte_addr[DXA_SMEM_ADDR_W-1:0];
    assign req_a_data.meta      = pair_iss ? {1'b0, lane1_rs1[30:0]} : lane1_rs1[31:0];
    assign req_a_data.coords[0] = lane2_rs1[31:0];
    assign req_a_data.coords[1] = lane3_rs1[31:0];
    assign req_a_data.coords[2] = pair_iss ? '0 : lane0_rs2[31:0];
    assign req_a_data.coords[3] = pair_iss ? '0 : lane1_rs2[31:0];
    assign req_a_data.coords[4] = pair_iss ? '0 : lane2_rs2[31:0];
    assign req_a_data.cta_mask  = pair_iss ? '0 : lane3_rs2[`VX_CFG_NUM_WARPS-1:0];

    // Captured payload — needed after the accept cycle for the pair's B
    // request and the single SFU writeback.
    reg [3:0][`VX_CFG_XLEN-1:0] cap_rs2;
    sfu_header_t                cap_hdr;

    // ── Request B: the pair's B tile (captured rs2 lanes) ────────────────
    dxa_req_data_t req_b_data;
    wire [`VX_CFG_XLEN-1:0] b_rel_byte_addr = cap_rs2[0] - `VX_CFG_XLEN'(`VX_MEM_LMEM_BASE_ADDR);
    assign req_b_data.core_id   = NC_WIDTH'(CORE_ID);
    assign req_b_data.uuid      = cap_hdr.uuid;
    assign req_b_data.wid       = cap_hdr.wid;
    assign req_b_data.smem_addr = b_rel_byte_addr[DXA_SMEM_ADDR_W-1:0];
    assign req_b_data.meta      = cap_rs2[1][31:0];
    assign req_b_data.coords[0] = cap_rs2[2][31:0];
    assign req_b_data.coords[1] = cap_rs2[3][31:0];
    assign req_b_data.coords[2] = '0;
    assign req_b_data.coords[3] = '0;
    assign req_b_data.coords[4] = '0;
    assign req_b_data.cta_mask  = '0;

    // ── Issue control ────────────────────────────────────────────────────
    // A fused pair is split into TWO sibling single-tile requests (A, then
    // B) that flow through the ordinary per-request DXA pipeline. Each
    // request drains and releases its barrier once -> two release events per
    // pair; the kernel arms expect_tx(2). The warp is freed by a SINGLE SFU
    // writeback issued after both requests have been accepted. Non-pair
    // issues keep the original single-cycle accept (req + rsp together).
    localparam PS_IDLE = 2'd0, PS_PAIR_B = 2'd1, PS_PAIR_RSP = 2'd2;
    reg [1:0] pstate_r;

    wire dxa_buf_ready, wb_ready;

    wire issue_single = execute_if.valid && ~pair_iss && (pstate_r == PS_IDLE)
                        && dxa_buf_ready && wb_ready;
    wire issue_pair_a = execute_if.valid &&  pair_iss && (pstate_r == PS_IDLE)
                        && dxa_buf_ready;
    wire issue_pair_b = (pstate_r == PS_PAIR_B) && dxa_buf_ready;
    wire issue_rsp    = (pstate_r == PS_PAIR_RSP) && wb_ready;

    assign execute_if.ready = issue_single || issue_pair_a;

    always_ff @(posedge clk) begin
        if (reset) begin
            pstate_r <= PS_IDLE;
        end else begin
            case (pstate_r)
            PS_IDLE:     if (issue_pair_a) pstate_r <= PS_PAIR_B;
            PS_PAIR_B:   if (issue_pair_b) pstate_r <= PS_PAIR_RSP;
            PS_PAIR_RSP: if (issue_rsp)    pstate_r <= PS_IDLE;
            default:     pstate_r <= PS_IDLE;
            endcase
        end
    end

    // Capture the payload on accept (rs2 lanes + header) for the B request
    // and the writeback that follows the pair's request beats.
    always_ff @(posedge clk) begin
        if (reset) begin
            cap_rs2 <= '0;
            cap_hdr <= '0;
        end else if (issue_single || issue_pair_a) begin
            cap_rs2 <= execute_if.data.rs2_data;
            cap_hdr <= execute_if.data.header;
        end
    end

    wire push_req = issue_single || issue_pair_a || issue_pair_b;

    // Output elastic buffer breaks the combinatorial path between
    // dxa_req_arb and this unit. Barrier transaction registration is
    // handled by software via vx_barrier.h::expect_tx.
    VX_elastic_buffer #(
        .DATAW ($bits(dxa_req_data_t)),
        .SIZE  (2)
    ) dxa_req_buf (
        .clk       (clk),
        .reset     (reset),
        .valid_in  (push_req),
        .ready_in  (dxa_buf_ready),
        .data_in   (issue_pair_b ? req_b_data : req_a_data),
        .valid_out (dxa_req_bus_if.req_valid),
        .ready_out (dxa_req_bus_if.req_ready),
        .data_out  (dxa_req_bus_if.req_data)
    );

    sfu_header_t header_out;

    // Single SFU writeback: once per issue (for a pair, after both sibling
    // requests have been accepted).
    wire push_rsp = issue_single || issue_rsp;

    VX_elastic_buffer #(
        .DATAW ($bits(sfu_header_t)),
        .SIZE  (2)
    ) rsp_buf (
        .clk       (clk),
        .reset     (reset),
        .valid_in  (push_rsp),
        .ready_in  (wb_ready),
        .data_in   (issue_rsp ? cap_hdr : execute_if.data.header),
        .data_out  (header_out),
        .valid_out (result_if.valid),
        .ready_out (result_if.ready)
    );

    assign result_if.data.header = header_out;
    assign result_if.data.data   = '0;


`ifdef DBG_TRACE_DXA
    always_ff @(posedge clk) begin
        if (~reset && dxa_req_bus_if.req_valid && dxa_req_bus_if.req_ready) begin
            `TRACE(1, ("%t: %s dxa-req: wid=%0d, smem=0x%0h, meta=0x%0h, c0=%0d, c1=%0d, c2=%0d, c3=%0d, c4=%0d\n",
                $time, INSTANCE_ID, dxa_req_bus_if.req_data.wid,
                dxa_req_bus_if.req_data.smem_addr, dxa_req_bus_if.req_data.meta,
                dxa_req_bus_if.req_data.coords[0], dxa_req_bus_if.req_data.coords[1],
                dxa_req_bus_if.req_data.coords[2], dxa_req_bus_if.req_data.coords[3],
                dxa_req_bus_if.req_data.coords[4]))
        end
    end
`endif

endmodule
