// tcu_unit_wrapper.sv — Yosys synthesis wrapper for VX_tcu_unit
// Creates interface instances and connects them to VX_tcu_unit.
// VX_tcu_unit uses .master modport on all interfaces, meaning it
// DRIVES req_valid/req_data/rsp_ready and READS req_ready/rsp_valid/rsp_data.
// The wrapper exposes these as plain wire ports with correct directions.

module tcu_unit_wrapper (
    input wire          clk,
    input wire          reset,

    // tcu_lmem_if (VX_mem_bus_if.master)
    // Master DRIVES: req_valid, req_data, rsp_ready
    // Master READS:  req_ready, rsp_valid, rsp_data
    output wire         tcu_lmem_req_valid,
    output wire [135:0] tcu_lmem_req_data,
    input wire          tcu_lmem_req_ready,
    input wire          tcu_lmem_rsp_valid,
    input wire [39:0]   tcu_lmem_rsp_data,
    output wire         tcu_lmem_rsp_ready,

    // tcu_mem_if (VX_lsu_sched_if.master)
    output wire         tcu_mem_req_valid,
    output wire [175:0] tcu_mem_req_data,
    input wire          tcu_mem_req_ready,
    input wire          tcu_mem_rsp_valid,
    input wire [35:0]   tcu_mem_rsp_data,
    output wire         tcu_mem_rsp_ready,

    // dispatch_if[0] (VX_dispatch_if.slave)
    // Slave READS:  valid, data
    // Slave DRIVES: ready
    input wire          dispatch_0_valid,
    input wire [175:0]  dispatch_0_data,
    output wire         dispatch_0_ready,

    // commit_if[0] (VX_commit_if.master)
    // Master DRIVES: valid, data
    // Master READS:  ready
    output wire         commit_0_valid,
    output wire [175:0] commit_0_data,
    input wire          commit_0_ready
);

    localparam ISSUE_WIDTH = 1;

    // Create interface instances
    VX_mem_bus_if #(
        .DATA_SIZE(4)
    ) tcu_lmem_if_inst ();

    VX_lsu_sched_if tcu_mem_if_inst ();

    VX_dispatch_if dispatch_if_inst [ISSUE_WIDTH] ();

    VX_commit_if commit_if_inst [ISSUE_WIDTH] ();

    // tcu_lmem_if: master drives req, reads rsp
    assign tcu_lmem_req_valid            = tcu_lmem_if_inst.req_valid;
    assign tcu_lmem_req_data             = tcu_lmem_if_inst.req_data;
    assign tcu_lmem_if_inst.req_ready    = tcu_lmem_req_ready;
    assign tcu_lmem_if_inst.rsp_valid    = tcu_lmem_rsp_valid;
    assign tcu_lmem_if_inst.rsp_data     = tcu_lmem_rsp_data;
    assign tcu_lmem_rsp_ready            = tcu_lmem_if_inst.rsp_ready;

    // tcu_mem_if: master drives req, reads rsp
    assign tcu_mem_req_valid             = tcu_mem_if_inst.req_valid;
    assign tcu_mem_req_data              = tcu_mem_if_inst.req_data;
    assign tcu_mem_if_inst.req_ready     = tcu_mem_req_ready;
    assign tcu_mem_if_inst.rsp_valid     = tcu_mem_rsp_valid;
    assign tcu_mem_if_inst.rsp_data      = tcu_mem_rsp_data;
    assign tcu_mem_rsp_ready             = tcu_mem_if_inst.rsp_ready;

    // dispatch_if[0]: slave reads valid/data, drives ready
    assign dispatch_if_inst[0].valid     = dispatch_0_valid;
    assign dispatch_if_inst[0].data      = dispatch_0_data;
    assign dispatch_0_ready              = dispatch_if_inst[0].ready;

    // commit_if[0]: master drives valid/data, reads ready
    assign commit_0_valid                = commit_if_inst[0].valid;
    assign commit_0_data                 = commit_if_inst[0].data;
    assign commit_if_inst[0].ready       = commit_0_ready;

    // Instantiate VX_tcu_unit
    VX_tcu_unit #(
        .INSTANCE_ID ("SYNTH")
    ) tcu_unit_inst (
        .clk            (clk),
        .reset          (reset),
        .tcu_lmem_if    (tcu_lmem_if_inst),
        .tcu_mem_if     (tcu_mem_if_inst),
        .dispatch_if    (dispatch_if_inst),
        .commit_if      (commit_if_inst)
    );

endmodule
