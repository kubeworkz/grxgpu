// Stub VX_core for source-level blackbox area synthesis.
// Same module signature as the real core; body replaced with
// constant ties so sv2v inlines an empty cell and the core logic
// contributes zero area. Used to measure cluster fabric (L1/L2/
// arbiters/interconnect) without synthesizing 16 inlined cores.
module VX_core import VX_gpu_pkg::*; #(
    parameter CORE_ID = 0,
    parameter  INSTANCE_ID = ""
) (
    input wire              clk,
    input wire              reset,
    VX_dcr_bus_if     dcr_bus_if,
    VX_mem_bus_if    dcache_bus_if [DCACHE_NUM_REQS],
    VX_mem_bus_if    icache_bus_if,
    VX_kmu_bus_if     kmu_bus_if,
    VX_gbar_bus_if   gbar_bus_if,
    output wire             busy
);
    assign busy = 1'b0;
endmodule
