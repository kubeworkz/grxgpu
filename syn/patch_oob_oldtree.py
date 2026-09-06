#!/usr/bin/env python3
"""Patch the DATA_OOB control-plane split into the old (pre-DXA) BB16 stub
tree's VX_mem_bus_arb.sv, and enable DATA_OOB=1 on the L2 cache mem_arb
instance in VX_cache_cluster.sv. Keeps the rest of the tree byte-identical
so the BB16 re-synthesis isolates the DATA_OOB effect."""
import sys

ARB = sys.argv[1]  # path to VX_mem_bus_arb.sv in the flat tree
CLUSTER = sys.argv[2]  # path to VX_cache_cluster.sv

# --- 1. VX_mem_bus_arb.sv: add DATA_OOB parameter ---
txt = open(ARB, encoding="utf-8").read()

if "DATA_OOB" not in txt:
    # Add parameter after ATTR_WIDTH (ATTR_WIDTH is last: no trailing comma)
    old_param = "    parameter ADDR_WIDTH     = (32-$clog2(DATA_SIZE)),\n    parameter ATTR_WIDTH     = MEM_ATTR_WIDTH\n"
    new_param = "    parameter ADDR_WIDTH     = (32-$clog2(DATA_SIZE)),\n    parameter ATTR_WIDTH     = MEM_ATTR_WIDTH,\n    parameter DATA_OOB       = 0\n"
    assert old_param in txt, "param block not found"
    txt = txt.replace(old_param, new_param)

    # Add localparams after SEL_COUNT
    old_lp = "    localparam SEL_COUNT    = (((NUM_INPUTS) < (NUM_OUTPUTS)) ? (NUM_INPUTS) : (NUM_OUTPUTS));\n"
    new_lp = old_lp + (
        "    localparam REQ_CTRL_DATAW   = 1 + ADDR_WIDTH + ATTR_WIDTH + TAG_WIDTH;\n"
        "    localparam REQ_DATA_PLANE_W = DATA_WIDTH + DATA_SIZE;\n"
    )
    assert old_lp in txt, "localparam block not found"
    txt = txt.replace(old_lp, new_lp)

    # Wrap the req arb in an if/else: DATA_OOB -> split + switch, else inline
    old_req = (
        "    VX_stream_arb #(\n"
        "        .NUM_INPUTS  (NUM_INPUTS),\n"
        "        .NUM_OUTPUTS (NUM_OUTPUTS),\n"
        "        .DATAW       (REQ_DATAW),\n"
        "        .ARBITER     (ARBITER),\n"
        "        .STICKY      (STICKY),\n"
        "        .OUT_BUF     (REQ_OUT_BUF)\n"
        "    ) req_arb (\n"
        "        .clk       (clk),\n"
        "        .reset     (reset),\n"
        "        .valid_in  (req_valid_in),\n"
        "        .ready_in  (req_ready_in),\n"
        "        .data_in   (req_data_in),\n"
        "        .data_out  (req_data_out),\n"
        "        .sel_out   (req_sel_out),\n"
        "        .valid_out (req_valid_out),\n"
        "        .ready_out (req_ready_out)\n"
        "    );\n"
    )
    assert old_req in txt, "req_arb block not found"
    txt = txt.replace(old_req, """\
    if (DATA_OOB) begin : g_req_data_oob
        wire [NUM_INPUTS-1:0][REQ_CTRL_DATAW-1:0]    req_ctrl_in;
        wire [NUM_INPUTS-1:0][REQ_DATA_PLANE_W-1:0]  req_dplane_in;
        for (genvar i = 0; i < NUM_INPUTS; ++i) begin : g_req_split
            assign {req_ctrl_in[i], req_dplane_in[i]} = req_data_in[i];
        end
        wire [NUM_OUTPUTS-1:0][REQ_CTRL_DATAW-1:0]   req_ctrl_out;
        wire [NUM_OUTPUTS-1:0][REQ_DATA_PLANE_W-1:0] req_dplane_out;
        VX_stream_arb #(
            .NUM_INPUTS  (NUM_INPUTS),
            .NUM_OUTPUTS (NUM_OUTPUTS),
            .DATAW       (REQ_CTRL_DATAW),
            .ARBITER     (ARBITER),
            .STICKY      (STICKY),
            .OUT_BUF     (REQ_OUT_BUF)
        ) req_arb (
            .clk       (clk),
            .reset     (reset),
            .valid_in  (req_valid_in),
            .ready_in  (req_ready_in),
            .data_in   (req_ctrl_in),
            .data_out  (req_ctrl_out),
            .sel_out   (req_sel_out),
            .valid_out (req_valid_out),
            .ready_out (req_ready_out)
        );
        VX_stream_switch #(
            .NUM_INPUTS  (NUM_INPUTS),
            .NUM_OUTPUTS (NUM_OUTPUTS),
            .DATAW       (REQ_DATA_PLANE_W),
            .OUT_BUF     (0)
        ) req_data_switch (
            .clk       (clk),
            .reset     (reset),
            .sel_in    (req_sel_out),
            .valid_in  (req_valid_in),
            .ready_in  (),
            .data_in   (req_dplane_in),
            .data_out  (req_dplane_out),
            .valid_out (),
            .ready_out (req_ready_out)
        );
        for (genvar i = 0; i < NUM_OUTPUTS; ++i) begin : g_req_recombine
            assign req_data_out[i] = {req_ctrl_out[i], req_dplane_out[i]};
        end
    end else begin : g_req_data_inline
        VX_stream_arb #(
            .NUM_INPUTS  (NUM_INPUTS),
            .NUM_OUTPUTS (NUM_OUTPUTS),
            .DATAW       (REQ_DATAW),
            .ARBITER     (ARBITER),
            .STICKY      (STICKY),
            .OUT_BUF     (REQ_OUT_BUF)
        ) req_arb (
            .clk       (clk),
            .reset     (reset),
            .valid_in  (req_valid_in),
            .ready_in  (req_ready_in),
            .data_in   (req_data_in),
            .data_out  (req_data_out),
            .sel_out   (req_sel_out),
            .valid_out (req_valid_out),
            .ready_out (req_ready_out)
        );
    end
""")
    open(ARB, "w", encoding="utf-8").write(txt)
    print(f"patched {ARB}")
else:
    print(f"{ARB} already has DATA_OOB")

# --- 2. VX_cache_cluster.sv: enable DATA_OOB=1 on the mem_arb (L2 -> mem) ---
ctxt = open(CLUSTER, encoding="utf-8").read()
old_mem = (
    "            .ARBITER     (\"R\"),\n"
    "            .REQ_OUT_BUF ((NUM_CACHES > 1) ? MEM_OUT_BUF : 0),\n"
    "            .RSP_OUT_BUF ((NUM_CACHES > 1) ? 2 : 0)\n"
    "        ) mem_arb ("
)
new_mem = (
    "            .ARBITER     (\"R\"),\n"
    "            .REQ_OUT_BUF ((NUM_CACHES > 1) ? MEM_OUT_BUF : 0),\n"
    "            .RSP_OUT_BUF ((NUM_CACHES > 1) ? 2 : 0),\n"
    "            .DATA_OOB    (1)\n"
    "        ) mem_arb ("
)
if ".DATA_OOB" not in ctxt:
    assert old_mem in ctxt, "mem_arb instance not found"
    ctxt = ctxt.replace(old_mem, new_mem)
    open(CLUSTER, "w", encoding="utf-8").write(ctxt)
    print(f"patched {CLUSTER}")
else:
    print(f"{CLUSTER} already has DATA_OOB")