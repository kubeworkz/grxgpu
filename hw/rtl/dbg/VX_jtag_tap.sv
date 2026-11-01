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

module VX_jtag_tap #(
    parameter IDCODE = 32'h00100001
) (
    input  wire        tck,
    input  wire        trst_n,

    input  wire        tms,
    input  wire        tdi,
    output wire        tdo,

    output wire [4:0]  ir,
    output wire [40:0] dr_out,
    output wire        dr_update,

    input  wire [40:0] dmi_capture,
    input  wire [31:0] dtmcs_capture
);
    localparam [4:0] IR_IDCODE = 5'h01;
    localparam [4:0] IR_DTMCS  = 5'h10;
    localparam [4:0] IR_DMI    = 5'h11;

    localparam [3:0] S_TLR      = 4'd0;
    localparam [3:0] S_RTI      = 4'd1;
    localparam [3:0] S_SEL_DR   = 4'd2;
    localparam [3:0] S_CAP_DR   = 4'd3;
    localparam [3:0] S_SHIFT_DR = 4'd4;
    localparam [3:0] S_EXIT1_DR = 4'd5;
    localparam [3:0] S_PAUSE_DR = 4'd6;
    localparam [3:0] S_EXIT2_DR = 4'd7;
    localparam [3:0] S_UPD_DR   = 4'd8;
    localparam [3:0] S_SEL_IR   = 4'd9;
    localparam [3:0] S_CAP_IR   = 4'd10;
    localparam [3:0] S_SHIFT_IR = 4'd11;
    localparam [3:0] S_EXIT1_IR = 4'd12;
    localparam [3:0] S_PAUSE_IR = 4'd13;
    localparam [3:0] S_EXIT2_IR = 4'd14;
    localparam [3:0] S_UPD_IR   = 4'd15;

    reg [3:0]  state;
    reg [3:0]  next_state;
    reg [4:0]  ir_q;
    reg [4:0]  ir_shift;
    reg [40:0] dr_shift;
    reg [40:0] dr_capture;
    reg        dr_update_q;
    reg        tdo_q;

    always @(*) begin
        case (state)
            S_TLR:      next_state = tms ? S_TLR      : S_RTI;
            S_RTI:      next_state = tms ? S_SEL_DR   : S_RTI;
            S_SEL_DR:   next_state = tms ? S_SEL_IR   : S_CAP_DR;
            S_CAP_DR:   next_state = tms ? S_EXIT1_DR : S_SHIFT_DR;
            S_SHIFT_DR: next_state = tms ? S_EXIT1_DR : S_SHIFT_DR;
            S_EXIT1_DR: next_state = tms ? S_UPD_DR   : S_PAUSE_DR;
            S_PAUSE_DR: next_state = tms ? S_EXIT2_DR : S_PAUSE_DR;
            S_EXIT2_DR: next_state = tms ? S_UPD_DR   : S_SHIFT_DR;
            S_UPD_DR:   next_state = tms ? S_SEL_DR   : S_RTI;
            S_SEL_IR:   next_state = tms ? S_TLR      : S_CAP_IR;
            S_CAP_IR:   next_state = tms ? S_EXIT1_IR : S_SHIFT_IR;
            S_SHIFT_IR: next_state = tms ? S_EXIT1_IR : S_SHIFT_IR;
            S_EXIT1_IR: next_state = tms ? S_UPD_IR   : S_PAUSE_IR;
            S_PAUSE_IR: next_state = tms ? S_EXIT2_IR : S_PAUSE_IR;
            S_EXIT2_IR: next_state = tms ? S_UPD_IR   : S_SHIFT_IR;
            S_UPD_IR:   next_state = tms ? S_SEL_DR   : S_RTI;
            default:    next_state = S_TLR;
        endcase
    end

    always @(*) begin
        case (ir_q)
            IR_IDCODE: dr_capture = {9'd0, IDCODE};
            IR_DTMCS:  dr_capture = {9'd0, dtmcs_capture};
            IR_DMI:    dr_capture = dmi_capture;
            default:   dr_capture = 41'd0;
        endcase
    end

    always @(posedge tck or negedge trst_n) begin
        if (!trst_n) begin
            state <= S_TLR;
            ir_q <= IR_IDCODE;
            ir_shift <= 5'h01;
            dr_shift <= 41'd0;
            dr_update_q <= 1'b0;
        end else begin
            state <= next_state;
            dr_update_q <= 1'b0;
            case (state)
                S_CAP_DR:   dr_shift <= dr_capture;
                S_SHIFT_DR: dr_shift <= {tdi, dr_shift[40:1]};
                S_UPD_DR:   dr_update_q <= 1'b1;
                S_CAP_IR:   ir_shift <= 5'h01;
                S_SHIFT_IR: ir_shift <= {tdi, ir_shift[4:1]};
                S_UPD_IR:   ir_q <= ir_shift;
                default: ;
            endcase
        end
    end

    always @(negedge tck or negedge trst_n) begin
        if (!trst_n) begin
            tdo_q <= 1'b0;
        end else if (state == S_SHIFT_DR) begin
            tdo_q <= dr_shift[0];
        end else if (state == S_SHIFT_IR) begin
            tdo_q <= ir_shift[0];
        end else begin
            tdo_q <= 1'b0;
        end
    end

    assign ir = ir_q;
    assign dr_out = dr_shift;
    assign dr_update = dr_update_q;
    assign tdo = tdo_q;

endmodule
