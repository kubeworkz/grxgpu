#!/usr/bin/env python3
"""Replace VX_mem_bus_arb instantiations with direct passthrough connections."""
import re, os

os.chdir("/tmp/dxa_synth")

fname = "VX_dxa_core.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    
    # Replace gmem_arb instantiation with direct passthrough
    # VX_mem_bus_arb with .bus_in_if(worker_gmem_bus_if) -> passthrough
    old_gmem_arb = """    VX_mem_bus_arb #(
        .NUM_INPUTS  (`VX_CFG_NUM_DXA_CORES),
        .NUM_OUTPUTS (GMEM_OUT_PORTS),
        .DATA_SIZE   (`VX_CFG_L1_LINE_SIZE),
        .TAG_WIDTH   (WORKER_GMEM_TAG_WIDTH),
        .ARBITER     ("R"),
        .REQ_OUT_BUF ((`VX_CFG_NUM_DXA_CORES > 1) ? 3 : 0)
    ) gmem_arb (
        .clk        (clk),
        .reset      (reset),
        .bus_in_if  (worker_gmem_bus_if),
        .bus_out_if (gmem_bus_if)
    );"""
    
    new_gmem_arb = """    // VX_mem_bus_arb replaced with direct passthrough for synthesis
    // Passthrough: connect first worker's GMEM bus to output
    assign gmem_bus_if_req_valid = worker_gmem_bus_if_req_valid[0];
    assign gmem_bus_if_req_addr = worker_gmem_bus_if_req_addr[0];
    assign gmem_bus_if_req_data = worker_gmem_bus_if_req_data[0];
    assign gmem_bus_if_req_byteen = worker_gmem_bus_if_req_byteen[0];
    assign gmem_bus_if_req_attr = worker_gmem_bus_if_req_attr[0];
    assign gmem_bus_if_req_tag_uuid = worker_gmem_bus_if_req_tag_uuid[0];
    assign gmem_bus_if_req_tag_value = worker_gmem_bus_if_req_tag_value[0];
    assign worker_gmem_bus_if_req_ready[0] = gmem_bus_if_req_ready;
    assign gmem_bus_if_rsp_valid = worker_gmem_bus_if_rsp_valid[0];
    assign gmem_bus_if_rsp_data = worker_gmem_bus_if_rsp_data[0];
    assign gmem_bus_if_rsp_tag_uuid = worker_gmem_bus_if_rsp_tag_uuid[0];
    assign gmem_bus_if_rsp_tag_value = worker_gmem_bus_if_rsp_tag_value[0];
    assign worker_gmem_bus_if_rsp_ready[0] = gmem_bus_if_rsp_ready;"""
    
    c = c.replace(old_gmem_arb, new_gmem_arb)
    
    # Replace lmem_arb instantiation with direct passthrough
    old_lmem_arb = """    VX_mem_bus_arb #(
        .NUM_INPUTS  (`VX_CFG_NUM_DXA_CORES),
        .NUM_OUTPUTS (1),
        .DATA_SIZE   (DXA_LMEM_WORD_SIZE),
        .TAG_WIDTH   (DXA_LMEM_TAG_W),
        .TAG_SEL_IDX (DXA_LMEM_TAG_W - UUID_WIDTH),
        .ATTR_WIDTH  (DXA_LMEM_ATTR_W),
        .ADDR_WIDTH  (DXA_LMEM_ADDR_W),
        .ARBITER     ("R"),
        // Register the SMEM write request at the DXA boundary: the tiled
        // dest-address is a deep cone whose sink is the far-away core LMEM BRAM,
        // so terminate it at a local flop to keep placement compact and isolate
        // the long DXA→core route into its own cycle.
        .REQ_OUT_BUF (3)
    ) lmem_arb (
        .clk        (clk),
        .reset      (reset),
        .bus_in_if  (worker_smem_bus_if),
        .bus_out_if (smem_bus_if)
    );"""
    
    new_lmem_arb = """    // VX_mem_bus_arb replaced with direct passthrough for synthesis
    // Passthrough: connect first worker's SMEM bus to output
    assign smem_bus_if_req_valid = worker_smem_bus_if_req_valid[0];
    assign smem_bus_if_req_addr = worker_smem_bus_if_req_addr[0];
    assign smem_bus_if_req_data = worker_smem_bus_if_req_data[0];
    assign smem_bus_if_req_byteen = worker_smem_bus_if_req_byteen[0];
    assign smem_bus_if_req_attr = worker_smem_bus_if_req_attr[0];
    assign smem_bus_if_req_tag_uuid = worker_smem_bus_if_req_tag_uuid[0];
    assign smem_bus_if_req_tag_value = worker_smem_bus_if_req_tag_value[0];
    assign worker_smem_bus_if_req_ready[0] = smem_bus_if_req_ready;
    assign smem_bus_if_rsp_valid = worker_smem_bus_if_rsp_valid[0];
    assign smem_bus_if_rsp_data = worker_smem_bus_if_rsp_data[0];
    assign smem_bus_if_rsp_tag_uuid = worker_smem_bus_if_rsp_tag_uuid[0];
    assign smem_bus_if_rsp_tag_value = worker_smem_bus_if_rsp_tag_value[0];
    assign worker_smem_bus_if_rsp_ready[0] = smem_bus_if_rsp_ready;"""
    
    c = c.replace(old_lmem_arb, new_lmem_arb)
    
    # Fix worker instantiation: .req_if, .gmem_bus_if, .smem_bus_if
    # These are interface ports that need to be flattened
    c = c.replace('.req_if         (worker_req_if[i]),',
                  '.req_valid(worker_req_if_req_valid[i]),\n            .req_ready(worker_req_if_req_ready[i]),')
    c = c.replace('.gmem_bus_if    (worker_gmem_bus_if[i]),',
                  '.gmem_bus_if_req_valid(worker_gmem_bus_if_req_valid[i]),\n            .gmem_bus_if_req_addr(worker_gmem_bus_if_req_addr[i]),\n            .gmem_bus_if_req_data(worker_gmem_bus_if_req_data[i]),\n            .gmem_bus_if_req_byteen(worker_gmem_bus_if_req_byteen[i]),\n            .gmem_bus_if_req_attr(worker_gmem_bus_if_req_attr[i]),\n            .gmem_bus_if_req_tag_uuid(worker_gmem_bus_if_req_tag_uuid[i]),\n            .gmem_bus_if_req_tag_value(worker_gmem_bus_if_req_tag_value[i]),\n            .gmem_bus_if_req_ready(worker_gmem_bus_if_req_ready[i]),\n            .gmem_bus_if_rsp_valid(worker_gmem_bus_if_rsp_valid[i]),\n            .gmem_bus_if_rsp_data(worker_gmem_bus_if_rsp_data[i]),\n            .gmem_bus_if_rsp_tag_uuid(worker_gmem_bus_if_rsp_tag_uuid[i]),\n            .gmem_bus_if_rsp_tag_value(worker_gmem_bus_if_rsp_tag_value[i]),\n            .gmem_bus_if_rsp_ready(worker_gmem_bus_if_rsp_ready[i]),')
    c = c.replace('.smem_bus_if    (worker_smem_bus_if[i])',
                  '.smem_bus_if_req_valid(worker_smem_bus_if_req_valid[i]),\n            .smem_bus_if_req_addr(worker_smem_bus_if_req_addr[i]),\n            .smem_bus_if_req_data(worker_smem_bus_if_req_data[i]),\n            .smem_bus_if_req_byteen(worker_smem_bus_if_req_byteen[i]),\n            .smem_bus_if_req_attr(worker_smem_bus_if_req_attr[i]),\n            .smem_bus_if_req_tag_uuid(worker_smem_bus_if_req_tag_uuid[i]),\n            .smem_bus_if_req_tag_value(worker_smem_bus_if_req_tag_value[i]),\n            .smem_bus_if_req_ready(worker_smem_bus_if_req_ready[i]),\n            .smem_bus_if_rsp_valid(worker_smem_bus_if_rsp_valid[i]),\n            .smem_bus_if_rsp_data(worker_smem_bus_if_rsp_data[i]),\n            .smem_bus_if_rsp_tag_uuid(worker_smem_bus_if_rsp_tag_uuid[i]),\n            .smem_bus_if_rsp_tag_value(worker_smem_bus_if_rsp_tag_value[i]),\n            .smem_bus_if_rsp_ready(worker_smem_bus_if_rsp_ready[i])')
    
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname}")
