#!/usr/bin/env python3
"""
Create a synthesis wrapper for VX_dxa_unit that provides concrete
interface types, bypassing the parameterized interface issue.
"""
import re

WRAPPER = r"""
// ============================================================
// Synthesis wrapper: provides concrete execute_if data_t type
// ============================================================

module dxa_synth_top import VX_gpu_pkg::*, VX_dxa_pkg::*; (
    input  wire        clk,
    input  wire        reset,
    // Execute interface (active-high valid/ready)
    input  wire        execute_valid,
    output wire        execute_ready,
    input  wire [31:0] execute_uuid,
    input  wire [3:0]  execute_wid,
    input  wire [31:0] execute_rs1_0,
    input  wire [31:0] execute_rs1_1,
    input  wire [31:0] execute_rs2_0,
    input  wire [31:0] execute_rs2_2,
    // Result interface
    output wire        result_valid,
    input  wire        result_ready,
    output wire [31:0] result_uuid,
    output wire [31:0] result_data,
    // DXA request bus
    output wire        dxa_req_valid,
    input  wire        dxa_req_ready,
    output wire [DXA_REQ_DATA_W-1:0] dxa_req_data,
    // TXBAR bus
    input  wire        txbar_valid,
    output wire        txbar_ready,
    input  wire [31:0] txbar_addr,
    input  wire        txbar_is_done,
    // DCR bus
    input  wire        dcr_req_valid,
    output wire        dcr_rsp_valid,
    input  wire [31:0] dcr_req_addr,
    input  wire [31:0] dcr_req_data,
    input  wire        dcr_req_rw,
    output wire [31:0] dcr_rsp_data,
    // SMEM bus
    output wire        smem_req_valid,
    input  wire        smem_req_ready,
    output wire [31:0] smem_req_addr,
    output wire [31:0] smem_req_data,
    output wire [7:0]  smem_req_attr,
    output wire [31:0] smem_req_tag,
    input  wire        smem_rsp_valid,
    output wire        smem_rsp_ready,
    input  wire [31:0] smem_rsp_data,
    input  wire [31:0] smem_rsp_tag,
    // GMEM bus (simplified)
    output wire        gmem_req_valid,
    input  wire        gmem_req_ready,
    output wire [31:0] gmem_req_addr,
    output wire [31:0] gmem_req_data,
    output wire [7:0]  gmem_req_mask,
    input  wire        gmem_rsp_valid,
    output wire        gmem_rsp_ready,
    input  wire [31:0] gmem_rsp_data
);

    localparam DXA_REQ_DATA_W = $bits(dxa_req_data_t);

    // Instantiate VX_dxa_unit directly with flat wires
    // The interface connections are handled by the module body

    VX_dxa_unit #(
        .INSTANCE_ID("dxa-synth"),
        .CORE_ID(0)
    ) dxa_unit (
        .clk        (clk),
        .reset      (reset),
        // Execute interface: active high valid/ready
        // execute_if is passed as a modport - we need to bind it
        // For synthesis, we just need the module to elaborate
    );

endmodule
"""

# Actually, the cleanest approach: flatten VX_dxa_unit.sv to replace
# interface ports with flat wire ports, then synthesize standalone.
# This avoids the parameterized interface problem entirely.

def flatten_dxa_unit():
    """Replace interface ports in VX_dxa_unit with flat wire declarations."""
    with open('/tmp/dxa_synth/VX_dxa_unit.sv') as f:
        text = f.read()
    
    # The key interfaces used by VX_dxa_unit:
    # VX_execute_if.slave execute_if
    # VX_result_if.master result_if
    # VX_dxa_req_bus_if.master dxa_req_bus_if
    # VX_txbar_bus_if.slave txbar_bus_if
    # VX_dcr_bus_if.slave dcr_bus_if
    # VX_mem_bus_if.master smem_bus_if (for LMEM writes)
    # VX_mem_bus_if.master gmem_bus_if (for GMEM reads)
    
    # Replace execute_if.data.XXX references with flat wire names
    # Replace result_if.XXX references with flat wire names
    # etc.
    
    # Actually, this is the same approach that failed before.
    # Let me try a different strategy: use -defer to skip elaboration
    # and just get the RTLIL for each individual module.
    
    print("Wrapper approach: use -defer to skip interface elaboration")

if __name__ == "__main__":
    flatten_dxa_unit()
