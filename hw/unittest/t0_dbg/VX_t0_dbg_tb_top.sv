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

module VX_t0_dbg_tb_top import VX_gpu_pkg::*;
`ifdef VX_CFG_EXT_DXA_ENABLE
    import VX_dxa_pkg::*;
`endif
(
    input  wire clk,
    input  wire reset,

    input  wire jtag_tck,
    input  wire jtag_tms,
    input  wire jtag_tdi,
    input  wire jtag_trst_n,
    output wire jtag_tdo,

    input  wire boot_en,
    input  wire core_stall,
    output wire core_reset,
    output wire boot_busy,
    output wire boot_done,
    output wire boot_error,
    output wire ndmreset,

    input  wire sram_stall,
    output wire sram_oob
);
    // Core-side cache interfaces: the T0 attachment stands in for the L1
    // caches, so these are word-granular (4 B fetch, 8 B data).
    VX_mem_bus_if #(
        .DATA_SIZE (ICACHE_WORD_SIZE),
        .TAG_WIDTH (ICACHE_TAG_WIDTH)
    ) core_icache_if();

    VX_mem_bus_if #(
        .DATA_SIZE (DCACHE_WORD_SIZE),
        .TAG_WIDTH (DCACHE_TAG_WIDTH)
    ) core_dcache_if[DCACHE_NUM_REQS]();

    // T0-side line interfaces; the test SRAM is 64 B wide.
    VX_mem_bus_if #(.DATA_SIZE(64)) mem_bus_if();
    VX_mem_bus_if #(.DATA_SIZE(64)) sram_bus_if();

    VX_kmu_bus_if t0_kmu_if();
    VX_kmu_bus_if core_kmu_if();

    wire core_busy;

    VX_t0_dbg_top #(
        .BOOT_ENTRY (64'h0000_0000_8000_0000)
    ) dut (
        .jtag_tck       (jtag_tck),
        .jtag_tms       (jtag_tms),
        .jtag_tdi       (jtag_tdi),
        .jtag_trst_n    (jtag_trst_n),
        .jtag_tdo       (jtag_tdo),
        .clk            (clk),
        .reset          (reset),
        .boot_en        (boot_en),
        .core_kmu_if    (t0_kmu_if),
        .core_icache_if (core_icache_if),
        .core_dcache_if (core_dcache_if),
        .mem_bus_if     (mem_bus_if),
        .ndmreset       (ndmreset),
        .core_reset     (core_reset),
        .boot_busy      (boot_busy),
        .boot_done      (boot_done),
        .boot_error     (boot_error)
    );

    // The KMU is a broadcast master; the core's ready is gated so a stalled
    // core can exercise the sequencer timeout.
    assign core_kmu_if.valid = t0_kmu_if.valid;
    assign core_kmu_if.data  = t0_kmu_if.data;
    assign t0_kmu_if.ready   = core_stall ? 1'b0 : core_kmu_if.ready;

    VX_dcr_bus_if core_dcr_if();
    assign core_dcr_if.req_valid = 1'b0;
    assign core_dcr_if.req_data  = '0;

    VX_gbar_bus_if gbar_bus_if();
    assign gbar_bus_if.req_ready = 1'b1;
    assign gbar_bus_if.rsp_valid = 1'b0;
    assign gbar_bus_if.rsp_data  = '0;

`ifdef VX_CFG_EXT_DXA_ENABLE
    VX_dxa_req_bus_if dxa_req_bus_if();
    assign dxa_req_bus_if.req_ready = 1'b1;

    VX_mem_bus_if #(
        .DATA_SIZE  (DXA_LMEM_WORD_SIZE),
        .TAG_WIDTH  (UUID_WIDTH + 1),
        .ATTR_WIDTH (DXA_LMEM_ATTR_W),
        .ADDR_WIDTH (DXA_LMEM_ADDR_W)
    ) dxa_lmem_bus_if();
    assign dxa_lmem_bus_if.req_valid = 1'b0;
    assign dxa_lmem_bus_if.req_data  = '0;
    assign dxa_lmem_bus_if.rsp_ready = 1'b1;
`endif

    VX_core #(
        .CORE_ID     (0),
        .INSTANCE_ID ("t0-core")
    ) core (
        `SCOPE_IO_BIND (0)
        .clk            (clk),
        .reset          (core_reset),
        .dcr_bus_if     (core_dcr_if),
        .dcache_bus_if  (core_dcache_if),
        .icache_bus_if  (core_icache_if),
    `ifdef VX_CFG_EXT_DXA_ENABLE
        .dxa_req_bus_if (dxa_req_bus_if),
        .dxa_lmem_bus_if(dxa_lmem_bus_if),
    `endif
        .kmu_bus_if     (core_kmu_if),
        .gbar_bus_if    (gbar_bus_if),
        .busy           (core_busy)
    );

    `UNUSED_VAR (core_busy)

    assign sram_bus_if.req_valid = mem_bus_if.req_valid;
    assign sram_bus_if.req_data  = mem_bus_if.req_data;
    assign mem_bus_if.req_ready  = sram_bus_if.req_ready;

    assign mem_bus_if.rsp_valid  = sram_bus_if.rsp_valid && !sram_stall;
    assign mem_bus_if.rsp_data   = sram_bus_if.rsp_data;
    assign sram_bus_if.rsp_ready = mem_bus_if.rsp_ready && !sram_stall;

    VX_t0_test_sram sram (
        .clk    (clk),
        .reset  (reset),
        .bus_if (sram_bus_if),
        .oob    (sram_oob)
    );

endmodule
