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

module VX_t0_test_sram import VX_gpu_pkg::*; (
    input  wire clk,
    input  wire reset,

    VX_mem_bus_if.slave bus_if,

    output reg  oob
);
    localparam NUM_LINES = 4096;
    localparam TAG_W = UUID_WIDTH + 1;

    reg [511:0] mem [NUM_LINES];
    reg         busy;
    reg         rsp_valid_q;
    reg [511:0] rsp_data_q;
    reg [TAG_W-1:0] rsp_tag_q;

    assign bus_if.req_ready = !busy && !rsp_valid_q;
    assign bus_if.rsp_valid = rsp_valid_q;
    assign bus_if.rsp_data.data = rsp_data_q;
    assign bus_if.rsp_data.tag = rsp_tag_q;

    integer i;

    always @(posedge clk) begin
        if (reset) begin
            busy <= 1'b0;
            rsp_valid_q <= 1'b0;
            rsp_data_q <= 512'd0;
            rsp_tag_q <= '0;
            oob <= 1'b0;
        end else begin
            if (bus_if.req_valid && bus_if.req_ready) begin
                busy <= 1'b1;
                rsp_tag_q <= bus_if.req_data.tag;
                if (bus_if.req_data.addr[25:12] == 14'h2000) begin
                    if (bus_if.req_data.rw) begin
                        for (i = 0; i < 64; i = i + 1) begin
                            if (bus_if.req_data.byteen[i]) begin
                                mem[bus_if.req_data.addr[11:0]][8*i +: 8] <= bus_if.req_data.data[8*i +: 8];
                            end
                        end
                        rsp_data_q <= bus_if.req_data.data;
                    end else begin
                        rsp_data_q <= mem[bus_if.req_data.addr[11:0]];
                    end
                end else begin
                    oob <= 1'b1;
                    rsp_data_q <= 512'd0;
                end
            end

            if (busy) begin
                busy <= 1'b0;
                rsp_valid_q <= 1'b1;
            end

            if (rsp_valid_q && bus_if.rsp_ready) begin
                rsp_valid_q <= 1'b0;
            end
        end
    end

endmodule
