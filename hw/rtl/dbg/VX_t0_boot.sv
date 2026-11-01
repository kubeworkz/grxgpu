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

// Programs the KMU the same way the runtime's launch path does, then pulses
// `start` and waits for the dispatch to retire. `boot_done` means the launch
// was accepted by the KMU; execution completion is observed by polling the
// result word the image writes.
module VX_t0_boot import VX_gpu_pkg::*; #(
    parameter [63:0] ENTRY         = 64'h0000_0000_8000_0000,
    parameter [31:0] GRID_X        = 1,
    parameter [31:0] GRID_Y        = 1,
    parameter [31:0] GRID_Z        = 1,
    parameter [31:0] BLOCK_X       = `VX_CFG_NUM_THREADS,
    parameter [31:0] BLOCK_Y       = 1,
    parameter [31:0] BLOCK_Z       = 1,
    parameter [31:0] LMEM_SIZE     = 0,
    parameter        TIMEOUT_CYCLES = 1024
) (
    input wire clk,
    input wire reset,

    input wire ndmreset,
    input wire boot_en,

    input wire kmu_busy,

    output reg        dcr_valid,
    output reg [VX_DCR_ADDR_WIDTH-1:0] dcr_addr,
    output reg [VX_DCR_DATA_WIDTH-1:0] dcr_data,

    output reg        kmu_start,

    output wire       boot_busy,
    output reg        boot_done,
    output reg        boot_error
);
    localparam S_IDLE       = 3'd0;
    localparam S_DCR        = 3'd1;
    localparam S_START      = 3'd2;
    localparam S_WAIT_RUN   = 3'd3;
    localparam S_WAIT_DONE  = 3'd4;
    localparam S_DONE       = 3'd5;
    localparam S_ERROR      = 3'd6;

    // 0x10..0x23; the three cluster dimensions are written explicitly because
    // a zero there makes cluster_size zero and stalls the dispatcher.
    localparam NUM_DCR = 20;

    localparam [31:0] BLOCK_SIZE   = BLOCK_X * BLOCK_Y * BLOCK_Z;
    localparam [31:0] WARP_STEP_X  = (BLOCK_X != 0) ? (`VX_CFG_NUM_THREADS % BLOCK_X) : 0;
    localparam [31:0] WARP_STEP_Y  = (BLOCK_X != 0 && BLOCK_Y != 0)
                                   ? ((`VX_CFG_NUM_THREADS / BLOCK_X) % BLOCK_Y) : 0;
    localparam [31:0] WARP_STEP_Z  = (BLOCK_X != 0 && BLOCK_Y != 0 && BLOCK_Z != 0)
                                   ? ((`VX_CFG_NUM_THREADS / (BLOCK_X * BLOCK_Y)) % BLOCK_Z) : 0;

    localparam TMO_W = `CLOG2(TIMEOUT_CYCLES + 1);
    localparam [TMO_W-1:0] TMO_MAX = TIMEOUT_CYCLES - 1;

    reg [2:0]  state;
    reg [4:0]  dcr_idx;
    reg [TMO_W-1:0] timeout;

    always @(*) begin
        dcr_valid = (state == S_DCR);
        dcr_addr = '0;
        dcr_data = '0;

        if (state == S_DCR) begin
            case (dcr_idx)
                5'd0:  begin dcr_addr = `VX_DCR_KMU_STARTUP_ADDR0;  dcr_data = ENTRY[31:0];  end
                5'd1:  begin dcr_addr = `VX_DCR_KMU_STARTUP_ADDR1;  dcr_data = ENTRY[63:32]; end
                5'd2:  begin dcr_addr = `VX_DCR_KMU_KERNEL_ENTRY0;   dcr_data = ENTRY[31:0];  end
                5'd3:  begin dcr_addr = `VX_DCR_KMU_KERNEL_ENTRY1;   dcr_data = ENTRY[63:32]; end
                5'd4:  begin dcr_addr = `VX_DCR_KMU_STARTUP_ARG0;    dcr_data = 32'd0;        end
                5'd5:  begin dcr_addr = `VX_DCR_KMU_STARTUP_ARG1;    dcr_data = 32'd0;        end
                5'd6:  begin dcr_addr = `VX_DCR_KMU_BLOCK_DIM_X;     dcr_data = BLOCK_X;      end
                5'd7:  begin dcr_addr = `VX_DCR_KMU_BLOCK_DIM_Y;     dcr_data = BLOCK_Y;      end
                5'd8:  begin dcr_addr = `VX_DCR_KMU_BLOCK_DIM_Z;     dcr_data = BLOCK_Z;      end
                5'd9:  begin dcr_addr = `VX_DCR_KMU_GRID_DIM_X;      dcr_data = GRID_X;       end
                5'd10: begin dcr_addr = `VX_DCR_KMU_GRID_DIM_Y;      dcr_data = GRID_Y;       end
                5'd11: begin dcr_addr = `VX_DCR_KMU_GRID_DIM_Z;      dcr_data = GRID_Z;       end
                5'd12: begin dcr_addr = `VX_DCR_KMU_LMEM_SIZE;       dcr_data = LMEM_SIZE;    end
                5'd13: begin dcr_addr = `VX_DCR_KMU_BLOCK_SIZE;      dcr_data = BLOCK_SIZE;   end
                5'd14: begin dcr_addr = `VX_DCR_KMU_WARP_STEP_X;     dcr_data = WARP_STEP_X;  end
                5'd15: begin dcr_addr = `VX_DCR_KMU_WARP_STEP_Y;     dcr_data = WARP_STEP_Y;  end
                5'd16: begin dcr_addr = `VX_DCR_KMU_WARP_STEP_Z;     dcr_data = WARP_STEP_Z;  end
                5'd17: begin dcr_addr = `VX_DCR_KMU_CLUSTER_DIM_X;   dcr_data = 32'd1;        end
                5'd18: begin dcr_addr = `VX_DCR_KMU_CLUSTER_DIM_Y;   dcr_data = 32'd1;        end
                5'd19: begin dcr_addr = `VX_DCR_KMU_CLUSTER_DIM_Z;   dcr_data = 32'd1;        end
                default: ;
            endcase
        end
    end

    assign kmu_start = (state == S_START);
    assign boot_busy = (state == S_DCR) || (state == S_START)
                    || (state == S_WAIT_RUN) || (state == S_WAIT_DONE);

    always @(posedge clk) begin
        if (reset || ndmreset || !boot_en) begin
            state <= S_IDLE;
            dcr_idx <= 5'd0;
            timeout <= '0;
            boot_done <= 1'b0;
            boot_error <= 1'b0;
        end else begin
            case (state)
                S_IDLE: begin
                    boot_done <= 1'b0;
                    boot_error <= 1'b0;
                    timeout <= '0;
                    dcr_idx <= 5'd0;
                    state <= S_DCR;
                end
                S_DCR: begin
                    if (dcr_idx == NUM_DCR - 1) begin
                        state <= S_START;
                    end else begin
                        dcr_idx <= dcr_idx + 5'd1;
                    end
                end
                S_START: begin
                    timeout <= '0;
                    state <= S_WAIT_RUN;
                end
                S_WAIT_RUN: begin
                    if (kmu_busy) begin
                        timeout <= '0;
                        state <= S_WAIT_DONE;
                    end else if (timeout == TMO_MAX) begin
                        state <= S_ERROR;
                    end else begin
                        timeout <= timeout + 1'b1;
                    end
                end
                S_WAIT_DONE: begin
                    if (!kmu_busy) begin
                        boot_done <= 1'b1;
                        state <= S_DONE;
                    end else if (timeout == TMO_MAX) begin
                        state <= S_ERROR;
                    end else begin
                        timeout <= timeout + 1'b1;
                    end
                end
                S_DONE: begin
                    // Hold until ndmreset or boot_en re-arms the sequencer.
                end
                S_ERROR: begin
                    boot_error <= 1'b1;
                end
                default: begin
                    state <= S_IDLE;
                end
            endcase
        end
    end

endmodule
