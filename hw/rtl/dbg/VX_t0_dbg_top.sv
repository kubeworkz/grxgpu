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

module VX_t0_dbg_top import VX_gpu_pkg::*; #(
    parameter IDCODE              = 32'h00100001,
    parameter [63:0] BOOT_ENTRY   = 64'h0000_0000_8000_0000,
    parameter BOOT_TIMEOUT_CYCLES = 1024
) (
    input  wire        jtag_tck,
    input  wire        jtag_tms,
    input  wire        jtag_tdi,
    input  wire        jtag_trst_n,
    output wire        jtag_tdo,

    input  wire        clk,
    input  wire        reset,

    input  wire        boot_en,

    VX_kmu_bus_if.master core_kmu_if,

    VX_mem_bus_if.slave  core_icache_if,
    VX_mem_bus_if.slave  core_dcache_if[DCACHE_NUM_REQS],
    VX_mem_bus_if.master mem_bus_if,

    output wire        ndmreset,
    output wire        core_reset,
    output wire        boot_busy,
    output wire        boot_done,
    output wire        boot_error
);
    wire [4:0]  ir;
    wire [40:0] dr_out;
    wire        dr_update;
    wire [40:0] dmi_capture;
    wire [31:0] dtmcs_capture;

    wire [1:0]  dm_req_op;
    wire [6:0]  dm_req_addr;
    wire [31:0] dm_req_data;
    wire        dm_req_valid;
    wire        dm_req_ready;
    wire [1:0]  dm_rsp_op;
    wire [6:0]  dm_rsp_addr;
    wire [31:0] dm_rsp_data;
    wire        dm_rsp_valid;

    wire        sba_start;
    wire        sba_rw;
    wire [31:0] sba_addr;
    wire [31:0] sba_wdata;
    wire [2:0]  sba_access;
    wire        sba_done;
    wire [31:0] sba_rdata;
    wire [2:0]  sba_error;
    wire        sba_busy;

    wire        boot_dcr_valid;
    wire [11:0] boot_dcr_addr;
    wire [31:0] boot_dcr_data;
    wire        boot_start;
    wire        kmu_busy;

    VX_mem_bus_if #(.DATA_SIZE(64)) sba_bus_if();
    VX_mem_bus_if #(.DATA_SIZE(64)) core_mem_if();

`ifdef VX_CFG_EXT_RASTER_ENABLE
    VX_raster_launch_if raster_launch_if();
`endif

    VX_jtag_tap #(
        .IDCODE (IDCODE)
    ) tap (
        .tck          (jtag_tck),
        .trst_n       (jtag_trst_n),
        .tms          (jtag_tms),
        .tdi          (jtag_tdi),
        .tdo          (jtag_tdo),
        .ir           (ir),
        .dr_out       (dr_out),
        .dr_update    (dr_update),
        .dmi_capture  (dmi_capture),
        .dtmcs_capture(dtmcs_capture)
    );

    VX_jtag_dtm dtm (
        .tck          (jtag_tck),
        .trst_n       (jtag_trst_n),
        .ir           (ir),
        .dr_out       (dr_out),
        .dr_update    (dr_update),
        .dmi_capture  (dmi_capture),
        .dtmcs_capture(dtmcs_capture),
        .clk          (clk),
        .reset        (reset),
        .dm_req_op    (dm_req_op),
        .dm_req_addr  (dm_req_addr),
        .dm_req_data  (dm_req_data),
        .dm_req_valid (dm_req_valid),
        .dm_req_ready (dm_req_ready),
        .dm_rsp_op    (dm_rsp_op),
        .dm_rsp_addr  (dm_rsp_addr),
        .dm_rsp_data  (dm_rsp_data),
        .dm_rsp_valid (dm_rsp_valid)
    );

    VX_dm dm (
        .clk          (clk),
        .reset        (reset),
        .dm_req_op    (dm_req_op),
        .dm_req_addr  (dm_req_addr),
        .dm_req_data  (dm_req_data),
        .dm_req_valid (dm_req_valid),
        .dm_req_ready (dm_req_ready),
        .dm_rsp_op    (dm_rsp_op),
        .dm_rsp_addr  (dm_rsp_addr),
        .dm_rsp_data  (dm_rsp_data),
        .dm_rsp_valid (dm_rsp_valid),
        .ndmreset     (ndmreset),
        .sba_start    (sba_start),
        .sba_rw       (sba_rw),
        .sba_addr     (sba_addr),
        .sba_wdata    (sba_wdata),
        .sba_access   (sba_access),
        .sba_done     (sba_done),
        .sba_rdata    (sba_rdata),
        .sba_error    (sba_error),
        .sba_busy     (sba_busy)
    );

    VX_dm_sba sba (
        .clk     (clk),
        .reset   (reset),
        .start   (sba_start),
        .rw      (sba_rw),
        .addr    (sba_addr),
        .wdata   (sba_wdata),
        .access  (sba_access),
        .rdata   (sba_rdata),
        .done    (sba_done),
        .error   (sba_error),
        .busy    (sba_busy),
        .bus_if  (sba_bus_if)
    );

    VX_t0_boot #(
        .ENTRY         (BOOT_ENTRY),
        .TIMEOUT_CYCLES(BOOT_TIMEOUT_CYCLES)
    ) boot (
        .clk        (clk),
        .reset      (reset),
        .ndmreset   (ndmreset),
        .boot_en    (boot_en),
        .kmu_busy   (kmu_busy),
        .dcr_valid  (boot_dcr_valid),
        .dcr_addr   (boot_dcr_addr),
        .dcr_data   (boot_dcr_data),
        .kmu_start  (boot_start),
        .boot_busy  (boot_busy),
        .boot_done  (boot_done),
        .boot_error (boot_error)
    );

    VX_kmu kmu (
        .clk           (clk),
        .reset         (reset | ndmreset),
        .dcr_req_valid (boot_dcr_valid),
        .dcr_req_rw    (boot_dcr_valid),
        .dcr_req_addr  (boot_dcr_addr),
        .dcr_req_data  (boot_dcr_data),
        .start         (boot_start),
        .busy          (kmu_busy),
`ifdef VX_CFG_EXT_RASTER_ENABLE
        .raster_launch_if (raster_launch_if),
`endif
        .kmu_bus_if    (core_kmu_if)
    );

`ifdef VX_CFG_EXT_RASTER_ENABLE
    // No raster engine on T0, so a grid-less launch retires immediately.
    assign raster_launch_if.ready = 1'b1;
`endif

    VX_t0_core_attach #(
        .NUM_DCACHE_REQS (DCACHE_NUM_REQS)
    ) core_attach (
        .clk       (clk),
        .reset     (core_reset),
        .icache_if (core_icache_if),
        .dcache_if (core_dcache_if),
        .mem_if    (core_mem_if)
    );

    VX_t0_mem_arb arb (
        .clk     (clk),
        .reset   (reset),
        .sba_if  (sba_bus_if),
        .core_if (core_mem_if),
        .out_if  (mem_bus_if)
    );

    assign core_reset = reset | ndmreset | ~boot_en;

endmodule
