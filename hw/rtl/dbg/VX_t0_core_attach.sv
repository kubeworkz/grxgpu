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

// Attaches the core's word-granular instruction and data ports to the single
// line-granular T0 test-memory port. The core normally sits behind an L1
// cache, so its I/D buses are the cache core-side interfaces: 4-byte fetch
// requests and 8-byte data requests. The test SRAM is 64-byte line-oriented,
// so a request is widened on the way out and the addressed word is selected
// on the way back. One request is outstanding at a time because the SRAM is
// single-outstanding; a round-robin arbiter keeps instruction fetch from
// starving stores.
module VX_t0_core_attach import VX_gpu_pkg::*; #(
    parameter NUM_DCACHE_REQS = DCACHE_NUM_REQS
) (
    input wire clk,
    input wire reset,

    VX_mem_bus_if.slave  icache_if,
    VX_mem_bus_if.slave  dcache_if[NUM_DCACHE_REQS],
    VX_mem_bus_if.master mem_if
);
    localparam LINE_SIZE        = 64;
    localparam ICACHE_LANES     = LINE_SIZE / ICACHE_WORD_SIZE;
    localparam DCACHE_LANES     = LINE_SIZE / DCACHE_WORD_SIZE;
    localparam ICACHE_LANE_BITS = `CLOG2(ICACHE_LANES);
    localparam DCACHE_LANE_BITS = `CLOG2(DCACHE_LANES);
    localparam LINE_ADDR_W      = `VX_CFG_MEM_ADDR_WIDTH - `CLOG2(LINE_SIZE);
    localparam OWNER_W          = `CLOG2(NUM_DCACHE_REQS + 1);
    localparam D_IDX_W          = (NUM_DCACHE_REQS > 1) ? `CLOG2(NUM_DCACHE_REQS) : 1;

    localparam ICACHE_TAG_BITS = ICACHE_TAG_WIDTH;
    localparam DCACHE_TAG_BITS = DCACHE_TAG_WIDTH;
    localparam MAX_TAG_BITS    = (ICACHE_TAG_BITS > DCACHE_TAG_BITS)
                               ? ICACHE_TAG_BITS : DCACHE_TAG_BITS;

    localparam ST_IDLE = 1'b0;
    localparam ST_WAIT = 1'b1;

    localparam [OWNER_W-1:0] OWNER_ICACHE = '0;

    reg        state;
    reg        rw_r;
    reg [OWNER_W-1:0] owner;
    reg [3:0]  lane_r;
    reg [MAX_TAG_BITS-1:0] tag_r;
    reg [OWNER_W-1:0] rr;

    // Flat views of every requester so the selected port can be indexed at
    // runtime; interface arrays themselves only accept constant indices.
    wire [NUM_DCACHE_REQS:0] req_valid;
    assign req_valid[0] = icache_if.req_valid;
    for (genvar i = 0; i < NUM_DCACHE_REQS; ++i) begin : g_req_valid
        assign req_valid[i + 1] = dcache_if[i].req_valid;
    end

    wire [LINE_ADDR_W-1:0] icache_line_addr =
        icache_if.req_data.addr[ICACHE_ADDR_WIDTH-1:ICACHE_LANE_BITS];
    wire [ICACHE_LANE_BITS-1:0] icache_lane =
        icache_if.req_data.addr[ICACHE_LANE_BITS-1:0];

    wire [LINE_ADDR_W-1:0] d_line_addr[NUM_DCACHE_REQS];
    wire [DCACHE_LANE_BITS-1:0] d_lane[NUM_DCACHE_REQS];
    wire d_rw[NUM_DCACHE_REQS];
    wire [MEM_ATTR_WIDTH-1:0] d_attr[NUM_DCACHE_REQS];
    wire [DCACHE_WORD_SIZE*8-1:0] d_data[NUM_DCACHE_REQS];
    wire [DCACHE_WORD_SIZE-1:0] d_byteen[NUM_DCACHE_REQS];
    wire [MAX_TAG_BITS-1:0] d_tag[NUM_DCACHE_REQS];
    wire d_rsp_ready[NUM_DCACHE_REQS];

    for (genvar i = 0; i < NUM_DCACHE_REQS; ++i) begin : g_d_flat
        assign d_line_addr[i] = dcache_if[i].req_data.addr[DCACHE_ADDR_WIDTH-1:DCACHE_LANE_BITS];
        assign d_lane[i]      = dcache_if[i].req_data.addr[DCACHE_LANE_BITS-1:0];
        assign d_rw[i]        = dcache_if[i].req_data.rw;
        assign d_attr[i]      = dcache_if[i].req_data.attr;
        assign d_data[i]      = dcache_if[i].req_data.data;
        assign d_byteen[i]    = dcache_if[i].req_data.byteen;
        assign d_tag[i]       = MAX_TAG_BITS'(dcache_if[i].req_data.tag);
        assign d_rsp_ready[i] = dcache_if[i].rsp_ready;
    end

    // Round-robin selection, starting after the previous grant.
    reg found_q;
    reg [OWNER_W-1:0] sel_q;
    integer k;
    always @(*) begin
        found_q = 1'b0;
        sel_q = '0;
        for (k = 0; k <= NUM_DCACHE_REQS; k = k + 1) begin
            if (!found_q && (k >= rr) && req_valid[k]) begin
                sel_q = k[OWNER_W-1:0];
                found_q = 1'b1;
            end
        end
        for (k = 0; k <= NUM_DCACHE_REQS; k = k + 1) begin
            if (!found_q && (k < rr) && req_valid[k]) begin
                sel_q = k[OWNER_W-1:0];
                found_q = 1'b1;
            end
        end
    end

    wire [ICACHE_WORD_SIZE*8-1:0] i_rsp_word =
        mem_if.rsp_data.data[{lane_r, 5'b0} +: ICACHE_WORD_SIZE*8];
    wire [DCACHE_WORD_SIZE*8-1:0] d_rsp_word =
        mem_if.rsp_data.data[{lane_r[DCACHE_LANE_BITS-1:0], 6'b0} +: DCACHE_WORD_SIZE*8];
    wire [D_IDX_W-1:0] d_sel = sel_q[D_IDX_W-1:0] - 1'b1;

    always @(*) begin
        icache_if.req_ready = 1'b0;
        icache_if.rsp_valid = 1'b0;
        icache_if.rsp_data = '0;

        mem_if.req_valid = 1'b0;
        mem_if.req_data = '0;
        mem_if.rsp_ready = 1'b0;

        if (reset) begin
            // A core reset can land mid-transaction; the arbiter may still be
            // holding a response for us. Drain it so the SBA is not blocked.
            mem_if.rsp_ready = mem_if.rsp_valid;
        end else if (state == ST_IDLE) begin
            icache_if.req_ready = found_q && (sel_q == OWNER_ICACHE) && mem_if.req_ready;
            mem_if.req_valid = found_q;
            if (found_q) begin
                if (sel_q == OWNER_ICACHE) begin
                    mem_if.req_data.rw   = icache_if.req_data.rw;
                    mem_if.req_data.addr = icache_line_addr;
                    mem_if.req_data.attr = icache_if.req_data.attr;
                    if (icache_if.req_data.rw) begin
                        mem_if.req_data.data[{icache_lane, 5'b0} +: ICACHE_WORD_SIZE*8] =
                            icache_if.req_data.data;
                        mem_if.req_data.byteen[{icache_lane, 2'b0} +: ICACHE_WORD_SIZE] =
                            icache_if.req_data.byteen;
                    end
                end else begin
                    mem_if.req_data.rw   = d_rw[d_sel];
                    mem_if.req_data.addr = d_line_addr[d_sel];
                    mem_if.req_data.attr = d_attr[d_sel];
                    if (d_rw[d_sel]) begin
                        mem_if.req_data.data[{d_lane[d_sel], 6'b0} +: DCACHE_WORD_SIZE*8] =
                            d_data[d_sel];
                        mem_if.req_data.byteen[{d_lane[d_sel], 3'b0} +: DCACHE_WORD_SIZE] =
                            d_byteen[d_sel];
                    end
                end
            end
        end else if (rw_r) begin
            // Stores complete at request acceptance: the core's store path has
            // no unmerge buffer to release, and the L1 it stands in for does
            // not return a write response. Drain the SRAM response here.
            mem_if.rsp_ready = 1'b1;
        end else begin
            icache_if.rsp_valid = (owner == OWNER_ICACHE) && mem_if.rsp_valid;
            icache_if.rsp_data.data = i_rsp_word;
            icache_if.rsp_data.tag = ICACHE_TAG_BITS'(tag_r);
            if (owner == OWNER_ICACHE) begin
                mem_if.rsp_ready = icache_if.rsp_ready;
            end else begin
                mem_if.rsp_ready = d_rsp_ready[owner[D_IDX_W-1:0] - 1'b1];
            end
        end
    end

    for (genvar i = 0; i < NUM_DCACHE_REQS; ++i) begin : g_d_rsp
        assign dcache_if[i].req_ready = !reset && (state == ST_IDLE) && found_q
                                     && (sel_q == i + 1) && mem_if.req_ready;
        assign dcache_if[i].rsp_valid = !reset && (state == ST_WAIT) && (owner == i + 1)
                                     && mem_if.rsp_valid && !rw_r;
        assign dcache_if[i].rsp_data.data = d_rsp_word;
        assign dcache_if[i].rsp_data.tag = DCACHE_TAG_BITS'(tag_r);
    end

    always @(posedge clk) begin
        if (reset) begin
            state <= ST_IDLE;
            owner <= '0;
            rw_r <= 1'b0;
            lane_r <= 4'b0;
            tag_r <= '0;
            rr <= '0;
        end else if (state == ST_IDLE) begin
            if (found_q && mem_if.req_ready) begin
                owner <= sel_q;
                rw_r <= mem_if.req_data.rw;
                if (sel_q == OWNER_ICACHE) begin
                    lane_r <= icache_lane;
                    tag_r <= MAX_TAG_BITS'(icache_if.req_data.tag);
                end else begin
                    lane_r <= 4'(d_lane[d_sel]);
                    tag_r <= d_tag[d_sel];
                end
                rr <= (sel_q == OWNER_W'(NUM_DCACHE_REQS)) ? '0 : (sel_q + 1'b1);
                state <= ST_WAIT;
            end
        end else if (mem_if.rsp_valid && mem_if.rsp_ready) begin
            state <= ST_IDLE;
        end
    end

endmodule
