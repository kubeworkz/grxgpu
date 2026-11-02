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

module VX_dm_sba #(
    parameter TIMEOUT_CYCLES = 1024
) (
    input  wire        clk,
    input  wire        reset,

    input  wire        start,
    input  wire        rw,
    input  wire [31:0] addr,
    input  wire [31:0] wdata,
    input  wire [2:0]  access,
    output reg  [31:0] rdata,
    output reg         done,
    output reg  [2:0]  error,
    output wire        busy,

    VX_mem_bus_if.master bus_if
);
    localparam ST_IDLE  = 3'd0;
    localparam ST_REQ   = 3'd1;
    localparam ST_WAIT  = 3'd2;
    localparam ST_DRAIN = 3'd3;

    localparam [15:0] TIMEOUT_MAX = TIMEOUT_CYCLES - 1;

    reg [2:0]  state;
    reg [31:0] addr_q;
    reg [31:0] wdata_q;
    reg [3:0]  lane_q;
    reg        rw_q;
    reg [15:0] timeout;

    wire [31:0] rsp_word = bus_if.rsp_data.data[{lane_q, 5'b0} +: 32];

    assign busy = (state != ST_IDLE);

    always @(*) begin
        bus_if.req_valid = (state == ST_REQ);
        bus_if.req_data.rw = rw_q;
        bus_if.req_data.addr = addr_q[31:6];
        bus_if.req_data.data = '0;
        bus_if.req_data.data[{lane_q, 5'b0} +: 32] = wdata_q;
        bus_if.req_data.byteen = 64'hF << addr_q[5:0];
        bus_if.req_data.attr = '0;
        bus_if.req_data.tag = '0;
        bus_if.rsp_ready = (state == ST_WAIT) || (state == ST_DRAIN);
    end

    always @(posedge clk) begin
        if (reset) begin
            state <= ST_IDLE;
            addr_q <= 32'd0;
            wdata_q <= 32'd0;
            lane_q <= 4'd0;
            rw_q <= 1'b0;
            timeout <= 16'd0;
            rdata <= 32'd0;
            done <= 1'b0;
            error <= 3'd0;
        end else begin
            done <= 1'b0;
            case (state)
                ST_IDLE: begin
                    if (start) begin
                        addr_q <= addr;
                        wdata_q <= wdata;
                        lane_q <= addr[5:2];
                        rw_q <= rw;
                        if (access != 3'd2) begin
                            error <= 3'd4;
                            done <= 1'b1;
                        end else if (addr[1:0] != 2'd0) begin
                            error <= 3'd3;
                            done <= 1'b1;
                        end else if (addr[31:18] != 14'h2000) begin
                            error <= 3'd2;
                            done <= 1'b1;
                        end else begin
                            error <= 3'd0;
                            timeout <= 16'd0;
                            state <= ST_REQ;
                        end
                    end
                end
                ST_REQ: begin
                    if (bus_if.req_ready) begin
                        state <= ST_WAIT;
                    end
                end
                ST_WAIT: begin
                    if (bus_if.rsp_valid && bus_if.rsp_ready) begin
                        rdata <= rw_q ? wdata_q : rsp_word;
                        done <= 1'b1;
                        error <= 3'd0;
                        state <= ST_IDLE;
                    end else if (timeout == TIMEOUT_MAX) begin
                        error <= 3'd1;
                        done <= 1'b1;
                        state <= ST_DRAIN;
                    end else begin
                        timeout <= timeout + 16'd1;
                    end
                end
                ST_DRAIN: begin
                    if (bus_if.rsp_valid && bus_if.rsp_ready) begin
                        state <= ST_IDLE;
                    end
                end
                default: begin
                    state <= ST_IDLE;
                end
            endcase
        end
    end

endmodule
