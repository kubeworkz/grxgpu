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

module VX_t0_mem_arb (
    input  wire clk,
    input  wire reset,

    VX_mem_bus_if.slave  sba_if,
    VX_mem_bus_if.slave  core_if,
    VX_mem_bus_if.master out_if
);
    localparam ST_IDLE = 1'b0;
    localparam ST_BUSY = 1'b1;

    reg state;
    reg owner;

    always @(*) begin
        sba_if.req_ready = 1'b0;
        core_if.req_ready = 1'b0;
        out_if.req_valid = 1'b0;
        out_if.req_data = '0;
        sba_if.rsp_valid = 1'b0;
        sba_if.rsp_data = '0;
        core_if.rsp_valid = 1'b0;
        core_if.rsp_data = '0;
        out_if.rsp_ready = 1'b0;

        if (state == ST_IDLE) begin
            if (sba_if.req_valid) begin
                out_if.req_valid = 1'b1;
                out_if.req_data = sba_if.req_data;
                sba_if.req_ready = out_if.req_ready;
            end else if (core_if.req_valid) begin
                out_if.req_valid = 1'b1;
                out_if.req_data = core_if.req_data;
                core_if.req_ready = out_if.req_ready;
            end
        end else if (owner) begin
            sba_if.rsp_valid = out_if.rsp_valid;
            sba_if.rsp_data = out_if.rsp_data;
            out_if.rsp_ready = sba_if.rsp_ready;
        end else begin
            core_if.rsp_valid = out_if.rsp_valid;
            core_if.rsp_data = out_if.rsp_data;
            out_if.rsp_ready = core_if.rsp_ready;
        end
    end

    always @(posedge clk) begin
        if (reset) begin
            state <= ST_IDLE;
            owner <= 1'b0;
        end else if (state == ST_IDLE) begin
            if (out_if.req_valid && out_if.req_ready) begin
                owner <= sba_if.req_valid;
                state <= ST_BUSY;
            end
        end else begin
            if (out_if.rsp_valid && out_if.rsp_ready) begin
                state <= ST_IDLE;
            end
        end
    end

endmodule
