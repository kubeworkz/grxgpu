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

module VX_kmu_arb import VX_gpu_pkg::*; #(
    parameter NUM_INPUTS     = 1,
    parameter NUM_OUTPUTS    = 1,
    parameter NUM_LANES      = 1,
    parameter OUT_BUF        = 0,
    parameter `STRING ARBITER = "R"
) (
    input wire              clk,
    input wire              reset,

    // input request
    VX_kmu_bus_if.slave  bus_in_if [NUM_INPUTS],

    // output requests
    VX_kmu_bus_if.master bus_out_if [NUM_OUTPUTS]
);
    // Demux of the KMU CTA stream. A beat-rotating demux would scatter a
    // cluster's members across consumers; the dispatch contract requires
    // every member of a cluster to be co-resident on the consumer that
    // admitted the cluster's first CTA (group barriers and DXA multicast
    // releases are per-consumer, so a fragmented cluster can never satisfy
    // its rendezvous). For the 1-in/N-out fan-out shape the routing is
    // therefore sticky per cluster: a first-of-cluster beat selects a
    // round-robin destination, all following members (is_first_of_cluster
    // == 0) go to the same destination until the member counter drains. A
    // single-entry skid holds the beat toward its destination and
    // backpressures the KMU stream while that destination is not ready, so
    // backpressure can never tear a cluster apart (the KMU walks clusters
    // back-to-back with no interleaved standalone CTAs, so membership is
    // reconstructible from is_first_of_cluster + a down-counter). Other
    // shapes (e.g. the device-KMU + raster merge) keep the plain arbiter.

    localparam DATAW = NUM_LANES * $bits(kmu_req_t);

    wire [NUM_INPUTS-1:0]             valid_in;
    wire [NUM_INPUTS-1:0][DATAW-1:0]  data_in;
    wire [NUM_INPUTS-1:0]             ready_in;

    for (genvar i = 0; i < NUM_INPUTS; ++i) begin : g_in
        assign valid_in[i] = bus_in_if[i].valid;
        assign data_in[i]  = bus_in_if[i].data;
        assign bus_in_if[i].ready = ready_in[i];
    end

    if (NUM_INPUTS == 1 && NUM_OUTPUTS > 1) begin : g_sticky_cluster_demux

        localparam LOG2_OUT = `CLOG2(NUM_OUTPUTS);

        wire [NUM_OUTPUTS-1:0]            core_valid_out;
        wire [NUM_OUTPUTS-1:0][DATAW-1:0] core_data_out;
        wire [NUM_OUTPUTS-1:0]            core_ready_out;

        reg                 ibuf_valid_r;
        reg [DATAW-1:0]     ibuf_data_r;
        reg [LOG2_OUT-1:0]  ibuf_dst_r;

        // Cluster membership: armed to K-1 when a first-of-cluster beat is
        // accepted; every accepted member beat decrements it. While nonzero,
        // member beats route to the sticky destination.
        reg [NW_WIDTH:0]   members_left_r;
        reg [LOG2_OUT-1:0] sticky_dst_r;

        // Round-robin destination for cluster heads and standalone CTAs.
        reg [LOG2_OUT-1:0] rr_ptr_r;

        wire ibuf_ready = ~ibuf_valid_r;
        assign ready_in[0] = ibuf_ready;

        wire in_push = valid_in[0] && ibuf_ready;
        wire out_pop = ibuf_valid_r && core_ready_out[ibuf_dst_r];

        // Struct-typed view of the head interface: member selection must go
        // through a struct variable — data_in[0] is a packed slice, and
        // selecting a member off it fails the full verilator build.
        kmu_req_t head_data_s;
        assign head_data_s = bus_in_if[0].data;
        wire [NW_WIDTH:0] cluster_k_raw = head_data_s.cluster_size;
        wire              is_first      = head_data_s.is_first_of_cluster;

        wire in_cluster = is_first || (members_left_r != '0);
        wire [LOG2_OUT-1:0] route_dst = in_cluster ? sticky_dst_r : rr_ptr_r;

        always @(posedge clk) begin
            if (reset) begin
                ibuf_valid_r   <= 1'b0;
                ibuf_data_r    <= '0;
                ibuf_dst_r     <= '0;
                members_left_r <= '0;
                sticky_dst_r   <= '0;
                rr_ptr_r       <= '0;
            end else if (in_push) begin
                ibuf_valid_r <= 1'b1;
                ibuf_data_r  <= data_in[0];
                ibuf_dst_r   <= route_dst;
                if (is_first) begin
                    sticky_dst_r   <= rr_ptr_r;
                    members_left_r <= (cluster_k_raw <= (NW_WIDTH+1)'(1))
                                    ? '0 : cluster_k_raw - (NW_WIDTH+1)'(1);
                    rr_ptr_r       <= (rr_ptr_r == (LOG2_OUT)'(NUM_OUTPUTS-1))
                                    ? '0 : rr_ptr_r + 1'b1;
                end else if (members_left_r != '0) begin
                    members_left_r <= members_left_r - (NW_WIDTH+1)'(1);
                end else begin
                    rr_ptr_r <= (rr_ptr_r == (LOG2_OUT)'(NUM_OUTPUTS-1))
                              ? '0 : rr_ptr_r + 1'b1;
                end
            end else if (out_pop) begin
                ibuf_valid_r <= 1'b0;
            end
        end

        for (genvar o = 0; o < NUM_OUTPUTS; ++o) begin : g_core_out
            assign core_valid_out[o] = ibuf_valid_r && (ibuf_dst_r == LOG2_OUT'(o));
            assign core_data_out[o]  = ibuf_data_r;
        end

        // Output buffering matches the generic path's OUT_BUF registration
        // (SLR-crossing skid). Each buffer only ever sees its own
        // destination's beats, so ordering within a cluster is preserved.
        for (genvar o = 0; o < NUM_OUTPUTS; ++o) begin : g_out_buf
            VX_elastic_buffer #(
                .DATAW   (DATAW),
                .SIZE    (`TO_OUT_BUF_SIZE(OUT_BUF)),
                .OUT_REG (`TO_OUT_BUF_REG(OUT_BUF)),
                .LUTRAM  (`TO_OUT_BUF_LUTRAM(OUT_BUF))
            ) out_buf (
                .clk       (clk),
                .reset     (reset),
                .valid_in  (core_valid_out[o]),
                .ready_in  (core_ready_out[o]),
                .data_in   (core_data_out[o]),
                .data_out  (bus_out_if[o].data),
                .valid_out (bus_out_if[o].valid),
                .ready_out (bus_out_if[o].ready)
            );
        end

    end else begin : g_generic_arb

        wire [NUM_OUTPUTS-1:0]            valid_out;
        wire [NUM_OUTPUTS-1:0][DATAW-1:0] data_out;
        wire [NUM_OUTPUTS-1:0]            ready_out;

        VX_stream_arb #(
            .NUM_INPUTS (NUM_INPUTS),
            .NUM_OUTPUTS(NUM_OUTPUTS),
            .DATAW      (DATAW),
            .ARBITER    (ARBITER),
            .OUT_BUF    (OUT_BUF)
        ) arb (
            .clk        (clk),
            .reset      (reset),
            .valid_in   (valid_in),
            .ready_in   (ready_in),
            .data_in    (data_in),
            .data_out   (data_out),
            .valid_out  (valid_out),
            .ready_out  (ready_out),
            `UNUSED_PIN (sel_out)
        );

        for (genvar o = 0; o < NUM_OUTPUTS; ++o) begin : g_out_if
            assign bus_out_if[o].valid = valid_out[o];
            assign bus_out_if[o].data  = data_out[o];
            assign ready_out[o]        = bus_out_if[o].ready;
        end

    end

endmodule
