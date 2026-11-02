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

module VX_jtag_dtm (
    input  wire        tck,
    input  wire        trst_n,

    input  wire [4:0]  ir,
    input  wire [40:0] dr_out,
    input  wire        dr_update,
    output wire [40:0] dmi_capture,
    output wire [31:0] dtmcs_capture,

    input  wire        clk,
    input  wire        reset,

    output reg  [1:0]  dm_req_op,
    output reg  [6:0]  dm_req_addr,
    output reg  [31:0] dm_req_data,
    output reg         dm_req_valid,
    input  wire        dm_req_ready,
    input  wire [1:0]  dm_rsp_op,
    input  wire [6:0]  dm_rsp_addr,
    input  wire [31:0] dm_rsp_data,
    input  wire        dm_rsp_valid
);
    localparam [4:0] IR_DTMCS = 5'h10;
    localparam [4:0] IR_DMI   = 5'h11;

    // The TAP has one 41-bit DR register, so a 32-bit DTMCS scan is
    // left-aligned in dr_out: DTMCS bit N lands at dr_out[9+N].
    wire dtmcs_dmireset     = dr_out[25];
    wire dtmcs_dmihardreset = dr_out[26];

    // TCK domain
    reg [1:0]  dmistat;
    reg        req_level;
    reg [1:0]  req_op_q;
    reg [6:0]  req_addr_q;
    reg [31:0] req_data_q;
    reg        req_pending;
    reg        rsp_ack;
    reg        rsp_present;
    reg [1:0]  rsp_op_q;
    reg [6:0]  rsp_addr_q;
    reg [31:0] rsp_data_q;

    reg [1:0]  req_ack_s;
    reg [1:0]  rsp_level_s;
    reg        rsp_level_s_d;

    // core domain
    reg [1:0]  req_level_s;
    reg [1:0]  rsp_ack_s;
    reg        req_seen;
    reg        req_ack_c;
    reg        rsp_level_c;
    reg [1:0]  rsp_op_c;
    reg [6:0]  rsp_addr_c;
    reg [31:0] rsp_data_c;

    always @(posedge tck or negedge trst_n) begin
        if (!trst_n) begin
            dmistat <= 2'd0;
            req_level <= 1'b0;
            req_op_q <= 2'd0;
            req_addr_q <= 7'd0;
            req_data_q <= 32'd0;
            req_pending <= 1'b0;
            rsp_ack <= 1'b0;
            rsp_present <= 1'b0;
            rsp_op_q <= 2'd0;
            rsp_addr_q <= 7'd0;
            rsp_data_q <= 32'd0;
            req_ack_s <= 2'd0;
            rsp_level_s <= 2'd0;
            rsp_level_s_d <= 1'b0;
        end else begin
            req_ack_s <= {req_ack_s[0], req_ack_c};
            rsp_level_s <= {rsp_level_s[0], rsp_level_c};
            rsp_level_s_d <= rsp_level_s[1];

            if (rsp_level_s[1] && !rsp_level_s_d) begin
                rsp_op_q <= rsp_op_c;
                rsp_addr_q <= rsp_addr_c;
                rsp_data_q <= rsp_data_c;
                rsp_present <= 1'b1;
                req_pending <= 1'b0;
                rsp_ack <= 1'b1;
                if (rsp_op_c == 2'b10) begin
                    dmistat <= 2'b10;
                end
            end

            if (!rsp_level_s[1]) begin
                rsp_ack <= 1'b0;
            end

            if (req_ack_s[1]) begin
                req_level <= 1'b0;
            end

            if (dr_update && ir == IR_DTMCS) begin
                if (dtmcs_dmireset) begin
                    dmistat <= 2'b00;
                end
                if (dtmcs_dmihardreset) begin
                    dmistat <= 2'b00;
                    req_level <= 1'b0;
                    req_pending <= 1'b0;
                    rsp_present <= 1'b0;
                    rsp_ack <= 1'b0;
                    rsp_level_s_d <= rsp_level_s[1];
                end
            end else if (dr_update && ir == IR_DMI) begin
                if (dr_out[1:0] != 2'b00) begin
                    if (req_pending || req_level) begin
                        dmistat <= 2'b11;
                    end else begin
                        req_op_q <= dr_out[1:0];
                        req_addr_q <= dr_out[40:34];
                        req_data_q <= dr_out[33:2];
                        req_level <= 1'b1;
                        req_pending <= 1'b1;
                        rsp_present <= 1'b0;
                    end
                end
            end
        end
    end

    always @(posedge clk) begin
        if (reset) begin
            req_level_s <= 2'd0;
            rsp_ack_s <= 2'd0;
            req_seen <= 1'b0;
            req_ack_c <= 1'b0;
            rsp_level_c <= 1'b0;
            rsp_op_c <= 2'd0;
            rsp_addr_c <= 7'd0;
            rsp_data_c <= 32'd0;
            dm_req_op <= 2'd0;
            dm_req_addr <= 7'd0;
            dm_req_data <= 32'd0;
            dm_req_valid <= 1'b0;
        end else begin
            req_level_s <= {req_level_s[0], req_level};
            rsp_ack_s <= {rsp_ack_s[0], rsp_ack};

            if (req_level_s[1] && !req_seen) begin
                req_seen <= 1'b1;
                dm_req_op <= req_op_q;
                dm_req_addr <= req_addr_q;
                dm_req_data <= req_data_q;
                dm_req_valid <= 1'b1;
            end

            if (dm_req_valid && dm_req_ready) begin
                dm_req_valid <= 1'b0;
                req_ack_c <= 1'b1;
            end

            if (!req_level_s[1]) begin
                req_seen <= 1'b0;
                req_ack_c <= 1'b0;
            end

            if (dm_rsp_valid) begin
                rsp_op_c <= dm_rsp_op;
                rsp_addr_c <= dm_rsp_addr;
                rsp_data_c <= dm_rsp_data;
                rsp_level_c <= 1'b1;
            end

            if (rsp_ack_s[1]) begin
                rsp_level_c <= 1'b0;
            end
        end
    end

    assign dmi_capture = req_pending ? {7'd0, 32'd0, 2'b11}
                       : rsp_present ? {rsp_addr_q, rsp_data_q, rsp_op_q}
                       : 41'd0;

    assign dtmcs_capture = {14'd0, 1'b0, 1'b0, 1'b0, 3'd0, dmistat, 6'd7, 4'd1};

endmodule
