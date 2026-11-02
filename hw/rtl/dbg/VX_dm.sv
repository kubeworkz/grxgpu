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

module VX_dm (
    input  wire        clk,
    input  wire        reset,

    input  wire [1:0]  dm_req_op,
    input  wire [6:0]  dm_req_addr,
    input  wire [31:0] dm_req_data,
    input  wire        dm_req_valid,
    output wire        dm_req_ready,
    output reg  [1:0]  dm_rsp_op,
    output reg  [6:0]  dm_rsp_addr,
    output reg  [31:0] dm_rsp_data,
    output reg         dm_rsp_valid,

    output wire        ndmreset,

    output wire        sba_start,
    output wire        sba_rw,
    output wire [31:0] sba_addr,
    output wire [31:0] sba_wdata,
    output wire [2:0]  sba_access,
    input  wire        sba_done,
    input  wire [31:0] sba_rdata,
    input  wire [2:0]  sba_error,
    input  wire        sba_busy
);
    localparam [6:0] DM_DATA0        = 7'h04;
    localparam [6:0] DM_DATA1        = 7'h05;
    localparam [6:0] DM_DATA2        = 7'h06;
    localparam [6:0] DM_DATA3        = 7'h07;
    localparam [6:0] DM_DMCONTROL    = 7'h10;
    localparam [6:0] DM_DMSTATUS     = 7'h11;
    localparam [6:0] DM_HARTINFO     = 7'h12;
    localparam [6:0] DM_ABSTRACTCS   = 7'h16;
    localparam [6:0] DM_COMMAND      = 7'h17;
    localparam [6:0] DM_ABSTRACTAUTO = 7'h18;
    localparam [6:0] DM_SBCS         = 7'h38;
    localparam [6:0] DM_SBADDRESS0   = 7'h39;
    localparam [6:0] DM_SBDATA0      = 7'h3c;

    reg        dmactive;
    reg        ndmreset_q;
    reg [9:0]  hartsel;
    reg [31:0] data0;
    reg [2:0]  cmderr;
    reg        sbreadonaddr;
    reg        sbbusyerror;
    reg        sbbusy;
    reg [2:0]  sberror;
    reg [2:0]  sbaccess;
    reg [31:0] sbaddress0;
    reg [31:0] sbdata0;

    reg        sba_start_q;
    reg        sba_seen_busy;
    reg        sba_rw_q;
    reg [31:0] sba_addr_q;
    reg [31:0] sba_wdata_q;
    reg [2:0]  sba_access_q;

    reg [31:0] dmstatus_rdata;
    reg [31:0] abstractcs_rdata;
    reg [31:0] sbcs_rdata;
    reg [31:0] dmcontrol_rdata;
    reg [31:0] rsp_data_c;
    reg [1:0]  rsp_op_c;

    always @(*) begin
        dmstatus_rdata = 32'd0;
        dmstatus_rdata[3:0] = 4'd2;
        dmstatus_rdata[7] = 1'b1;
        dmstatus_rdata[10] = ~ndmreset_q;
        dmstatus_rdata[11] = ~ndmreset_q;

        abstractcs_rdata = 32'd0;
        abstractcs_rdata[3:0] = 4'd1;
        abstractcs_rdata[10:8] = cmderr;

        sbcs_rdata = 32'd0;
        sbcs_rdata[31:29] = 3'd1;
        sbcs_rdata[22] = sbbusyerror;
        sbcs_rdata[21] = sbbusy;
        sbcs_rdata[20] = sbreadonaddr;
        sbcs_rdata[19:17] = sbaccess;
        sbcs_rdata[14:12] = sberror;
        sbcs_rdata[11:5] = 7'd32;
        sbcs_rdata[2] = 1'b1;

        dmcontrol_rdata = 32'd0;
        dmcontrol_rdata[0] = dmactive;
        dmcontrol_rdata[1] = ndmreset_q;
        dmcontrol_rdata[25:16] = hartsel;
    end

    always @(*) begin
        rsp_op_c = 2'b00;
        case (dm_req_addr)
            DM_DATA0:        rsp_data_c = data0;
            DM_DATA1, DM_DATA2, DM_DATA3: rsp_data_c = 32'd0;
            DM_DMCONTROL:    rsp_data_c = dmcontrol_rdata;
            DM_DMSTATUS:     rsp_data_c = dmstatus_rdata;
            DM_HARTINFO:     rsp_data_c = 32'd0;
            DM_ABSTRACTCS:   rsp_data_c = abstractcs_rdata;
            DM_COMMAND:      rsp_data_c = 32'd0;
            DM_ABSTRACTAUTO: rsp_data_c = 32'd0;
            DM_SBCS:         rsp_data_c = sbcs_rdata;
            DM_SBADDRESS0:   rsp_data_c = sbaddress0;
            DM_SBDATA0:      rsp_data_c = sbdata0;
            default: begin
                rsp_data_c = 32'd0;
                rsp_op_c = 2'b10;
            end
        endcase
        if (dm_req_op == 2'b10) begin
            rsp_data_c = 32'd0;
        end
    end

    assign dm_req_ready = 1'b1;
    assign ndmreset = ndmreset_q;
    assign sba_start = sba_start_q;
    assign sba_rw = sba_rw_q;
    assign sba_addr = sba_addr_q;
    assign sba_wdata = sba_wdata_q;
    assign sba_access = sba_access_q;

    always @(posedge clk) begin
        if (reset) begin
            dmactive <= 1'b0;
            ndmreset_q <= 1'b0;
            hartsel <= 10'd0;
            data0 <= 32'd0;
            cmderr <= 3'd0;
            sbreadonaddr <= 1'b0;
            sbbusyerror <= 1'b0;
            sbbusy <= 1'b0;
            sberror <= 3'd0;
            sbaccess <= 3'd2;
            sbaddress0 <= 32'd0;
            sbdata0 <= 32'd0;
            sba_start_q <= 1'b0;
            sba_seen_busy <= 1'b0;
            sba_rw_q <= 1'b0;
            sba_addr_q <= 32'd0;
            sba_wdata_q <= 32'd0;
            sba_access_q <= 3'd2;
            dm_rsp_op <= 2'd0;
            dm_rsp_addr <= 7'd0;
            dm_rsp_data <= 32'd0;
            dm_rsp_valid <= 1'b0;
        end else begin
            sba_start_q <= 1'b0;
            dm_rsp_valid <= 1'b0;

            if (dm_req_valid) begin
                dm_rsp_valid <= 1'b1;
                dm_rsp_op <= rsp_op_c;
                dm_rsp_addr <= dm_req_addr;
                dm_rsp_data <= rsp_data_c;
            end

            if (dm_req_valid && dm_req_op == 2'b10 && dm_req_addr == DM_DMCONTROL) begin
                dmactive <= dm_req_data[0];
                if (dmactive) begin
                    ndmreset_q <= dm_req_data[1];
                    hartsel <= dm_req_data[25:16];
                end
            end

            if (!dmactive) begin
                ndmreset_q <= 1'b0;
                hartsel <= 10'd0;
                data0 <= 32'd0;
                cmderr <= 3'd0;
                sbreadonaddr <= 1'b0;
                sbbusyerror <= 1'b0;
                sbbusy <= 1'b0;
                sberror <= 3'd0;
                sbaccess <= 3'd2;
                sbaddress0 <= 32'd0;
                sbdata0 <= 32'd0;
                sba_start_q <= 1'b0;
                sba_seen_busy <= 1'b0;
            end else begin
                if (dm_req_valid && dm_req_op == 2'b10) begin
                    case (dm_req_addr)
                        DM_DATA0: begin
                            data0 <= dm_req_data;
                        end
                        DM_ABSTRACTCS: begin
                            cmderr <= cmderr & ~dm_req_data[10:8];
                        end
                        DM_COMMAND: begin
                            if (cmderr == 3'd0) begin
                                cmderr <= 3'd2;
                            end
                        end
                        DM_SBCS: begin
                            if (dm_req_data[22]) begin
                                sbbusyerror <= 1'b0;
                            end
                            sberror <= sberror & ~dm_req_data[14:12];
                            sbreadonaddr <= dm_req_data[20];
                            sbaccess <= dm_req_data[19:17];
                        end
                        DM_SBADDRESS0: begin
                            if (sbbusy) begin
                                sbbusyerror <= 1'b1;
                            end else begin
                                sbaddress0 <= dm_req_data;
                                if (sbreadonaddr && sberror == 3'd0 && !sbbusyerror) begin
                                    if (sbaccess != 3'd2) begin
                                        sberror <= 3'd4;
                                    end else begin
                                        sba_start_q <= 1'b1;
                                        sba_seen_busy <= 1'b0;
                                        sba_rw_q <= 1'b0;
                                        sba_addr_q <= dm_req_data;
                                        sba_wdata_q <= 32'd0;
                                        sba_access_q <= sbaccess;
                                        sbbusy <= 1'b1;
                                    end
                                end
                            end
                        end
                        DM_SBDATA0: begin
                            if (sbbusy) begin
                                sbbusyerror <= 1'b1;
                            end else if (sberror == 3'd0 && !sbbusyerror) begin
                                if (sbaccess != 3'd2) begin
                                    sberror <= 3'd4;
                                end else begin
                                    sba_start_q <= 1'b1;
                                    sba_seen_busy <= 1'b0;
                                    sba_rw_q <= 1'b1;
                                    sba_addr_q <= sbaddress0;
                                    sba_wdata_q <= dm_req_data;
                                    sba_access_q <= sbaccess;
                                    sbbusy <= 1'b1;
                                end
                            end
                        end
                        default: ;
                    endcase
                end

                if (dm_req_valid && dm_req_op == 2'b01 && dm_req_addr == DM_SBDATA0 && sbbusy) begin
                    sbbusyerror <= 1'b1;
                end

                if (sba_busy) begin
                    sba_seen_busy <= 1'b1;
                end
                if (sbbusy && sba_seen_busy && !sba_busy) begin
                    sbbusy <= 1'b0;
                end
                if (sba_done && !sba_busy) begin
                    sbbusy <= 1'b0;
                end

                if (sba_done) begin
                    if (sba_error != 3'd0) begin
                        sberror <= sba_error;
                    end else if (!sba_rw_q) begin
                        sbdata0 <= sba_rdata;
                    end
                end
            end
        end
    end

endmodule
