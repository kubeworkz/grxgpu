#!/usr/bin/env python3
"""
Prepare DXA RTL files for Yosys synthesis via Synlig.
Applies all necessary transformations in a single pass.
"""
import re, os, sys, glob

DXA_DIR = "/tmp/dxa_synth"
STUBS_FILE = os.path.join(DXA_DIR, "vortex_stubs.sv")
GPU_PKG_STUB = os.path.join(DXA_DIR, "vx_gpu_pkg_stub.sv")
SYNTH_SCRIPT = os.path.join(DXA_DIR, "synth_dxa.ys")

def fix_part_selectes(text):
    """Replace SV dynamic part-select (+:) with explicit bit slicing."""
    # Pattern: var[base +: width] -> var[(base)+(width)-1:(base)]
    def repl(m):
        var = m.group(1)
        base = m.group(2)
        width = m.group(3)
        return f"{var}[({base})+({width})-1:({base})]"
    return re.sub(r'(\w+)\[([^+\]]+)\s*\+:\s*(\w+)\]', repl, text)

def strip_runtime_assert(text):
    """Strip RUNTIME_ASSERT(...); calls and multi-line variants."""
    # Single-line: RUNTIME_ASSERT(...);
    text = re.sub(r'\s*RUNTIME_ASSERT\s*\([^)]*\)\s*;', '', text)
    # Multi-line: RUNTIME_ASSERT(\n  ...\n);
    text = re.sub(r'\s*RUNTIME_ASSERT\s*\([\s\S]*?\);', '', text)
    return text

def fix_bits(text):
    """Replace $bits(x) with hardcoded widths."""
    # Common patterns in DXA
    text = re.sub(r'\$bits\(req_data\)', 'DATAW', text)
    text = re.sub(r'\$bits\(cmd_data\)', 'DATAW', text)
    return text

def fix_string_params(text):
    """Replace string-typed parameters with integer for Yosys."""
    text = re.sub(r'parameter\s+string\s+', 'parameter ', text, flags=re.IGNORECASE)
    return text

def write_stubs():
    """Write all needed blackbox stubs."""
    stubs = r"""
// ============================================================
// Blackbox stubs for Yosys synthesis
// ============================================================

module VX_stream_arb #(
    parameter NUM_INPUTS  = 1,
    parameter NUM_OUTPUTS = 1,
    parameter ARBITER     = "R",
    parameter BUFFERED    = 0,
    parameter DATA_SIZE   = 0,
    parameter LUTRAM      = 0,
    parameter OUT_BUF     = 0
)(
    input  wire clk,
    input  wire reset,
    // inputs
    input  wire [NUM_INPUTS-1:0]              valid_in,
    input  wire [NUM_INPUTS*32-1:0]           data_in,
    output wire [NUM_INPUTS-1:0]              ready_in,
    // outputs
    output wire [NUM_OUTPUTS-1:0]             valid_out,
    output wire [NUM_OUTPUTS*32-1:0]          data_out,
    input  wire [NUM_OUTPUTS-1:0]             ready_out,
    // select
    output wire [NUM_OUTPUTS*NUM_INPUTS-1:0]  sel_out
);
    assign valid_out = valid_in;
    assign data_out  = data_in;
    assign ready_in  = {NUM_INPUTS{ready_out[0]}};
    assign sel_out   = 1;
endmodule

module VX_elastic_buffer #(
    parameter DATAW  = 1,
    parameter SIZE   = 2,
    parameter LUTRAM = 0
)(
    input  wire clk,
    input  wire reset,
    // input side
    output wire in_ready,
    input  wire in_valid,
    input  wire [DATAW-1:0] in_data,
    // output side
    input  wire out_ready,
    output wire out_valid,
    output wire [DATAW-1:0] out_data
);
    assign in_ready  = out_ready;
    assign out_valid = in_valid;
    assign out_data  = in_data;
endmodule

module VX_fifo_queue #(
    parameter DATAW = 1,
    parameter SIZE  = 2,
    parameter LUTRAM = 0,
    parameter SIZEW = 0
)(
    input  wire clk,
    input  wire reset,
    input  wire push,
    input  wire pop,
    input  wire [DATAW-1:0] data_in,
    output wire [DATAW-1:0] data_out,
    output wire empty,
    output wire full
);
    assign empty = 1;
    assign full  = 0;
    assign data_out = data_in;
endmodule

module VX_dp_ram #(
    parameter WORDS = 1,
    parameter WIDTH = 1,
    parameter RDW_MODE = "W",
    parameter OUT_REG  = 0,
    parameter WRENW    = 0
)(
    input  wire clk,
    input  wire [WRENW-1:0] wren,
    input  wire [WRENW-1:0] write,
    input  wire [$clog2(WORDS)-1:0] waddr,
    input  wire [WIDTH-1:0] wdata,
    input  wire [$clog2(WORDS)-1:0] raddr,
    output wire [WIDTH-1:0] rdata
);
    reg [WIDTH-1:0] mem [0:WORDS-1];
    always @(posedge clk) begin
        if (write[0]) mem[waddr] <= wdata;
    end
    assign rdata = mem[raddr];
endmodule

module VX_multiplier #(
    parameter A_WIDTH = 1,
    parameter B_WIDTH = 1,
    parameter R_WIDTH = 1,
    parameter LATENCY = 0
)(
    input  wire clk,
    input  wire enable,
    input  wire [A_WIDTH-1:0] dataa,
    input  wire [B_WIDTH-1:0] datab,
    output wire [R_WIDTH-1:0] result
);
    assign result = dataa * datab;
endmodule

module VX_priority_encoder #(
    parameter N = 1,
    parameter REVERSE = 0
)(
    input  wire [N-1:0]    data_in,
    output wire            valid_out,
    output wire [$clog2(N)-1:0] index_out,
    output wire [N-1:0]    onehot_out
);
    assign valid_out = |data_in;
    assign index_out = 0;
    assign onehot_out = data_in & ~(data_in - 1);
endmodule

module VX_popcount #(
    parameter N = 1
)(
    input  wire [N-1:0] data_in,
    output wire [$clog2(N+1)-1:0] popcount
);
    integer i;
    reg [$clog2(N+1)-1:0] cnt;
    always @(*) begin
        cnt = 0;
        for (i = 0; i < N; i = i + 1)
            if (data_in[i]) cnt = cnt + 1;
    end
    assign popcount = cnt;
endmodule

module VX_mem_bus_arb #(
    parameter NUM_INPUTS   = 1,
    parameter NUM_OUTPUTS  = 1,
    parameter DATA_SIZE    = 4,
    parameter TAG_WIDTH    = 1,
    parameter TAG_SEL_IDX  = 0,
    parameter ATTR_WIDTH   = 0,
    parameter ADDR_WIDTH   = 1,
    parameter ARBITER      = "R",
    parameter REQ_OUT_BUF  = 0,
    parameter RSP_OUT_BUF  = 0,
    parameter RD_FLAGS     = 0,
    parameter REQ_ARB_DTYPE= 0
)(
    input  wire clk,
    input  wire reset,
    // Request input
    input  wire [NUM_INPUTS-1:0]                 bus_in_req_valid,
    output wire [NUM_INPUTS-1:0]                 bus_in_req_ready,
    input  wire [NUM_INPUTS*(ADDR_WIDTH+TAG_WIDTH+DATA_SIZE*8)-1:0] bus_in_req_data,
    // Request output
    output wire [NUM_OUTPUTS-1:0]                bus_out_req_valid,
    input  wire [NUM_OUTPUTS-1:0]                bus_out_req_ready,
    output wire [NUM_OUTPUTS*(ADDR_WIDTH+TAG_WIDTH+DATA_SIZE*8)-1:0] bus_out_req_data,
    // Response input
    input  wire [NUM_OUTPUTS-1:0]                bus_in_rsp_valid,
    output wire [NUM_OUTPUTS-1:0]                bus_in_rsp_ready,
    input  wire [NUM_OUTPUTS*(TAG_WIDTH+DATA_SIZE*8)-1:0] bus_in_rsp_data,
    // Response output
    output wire [NUM_INPUTS-1:0]                 bus_out_rsp_valid,
    input  wire [NUM_INPUTS-1:0]                 bus_out_rsp_ready,
    output wire [NUM_INPUTS*(TAG_WIDTH+DATA_SIZE*8)-1:0] bus_out_rsp_data
);
    assign bus_out_req_valid = bus_in_req_valid;
    assign bus_in_req_ready  = bus_out_req_ready;
    assign bus_out_rsp_valid = bus_in_rsp_valid;
    assign bus_in_rsp_ready  = bus_out_rsp_ready;
endmodule

module VX_stream_dispatch #(
    parameter NUM_INPUTS  = 1,
    parameter NUM_OUTPUTS = 1,
    parameter DATA_SIZE   = 0,
    parameter BUFFERED    = 0
)(
    input  wire clk,
    input  wire reset,
    input  wire [NUM_INPUTS-1:0]              valid_in,
    input  wire [NUM_INPUTS*32-1:0]           data_in,
    output wire [NUM_INPUTS-1:0]              ready_in,
    output wire [NUM_OUTPUTS-1:0]             valid_out,
    output wire [NUM_OUTPUTS*32-1:0]          data_out,
    input  wire [NUM_OUTPUTS-1:0]             ready_out,
    input  wire [$clog2(NUM_OUTPUTS)-1:0]     sel
);
    assign valid_out[0] = valid_in[0];
    assign data_out     = data_in;
    assign ready_in     = {NUM_INPUTS{ready_out[0]}};
endmodule
"""
    with open(STUBS_FILE, 'w') as f:
        f.write(stubs)
    print(f"  Wrote stubs to {STUBS_FILE}")

def write_gpu_pkg_stub():
    """Write minimal VX_gpu_pkg stub with all needed constants."""
    stub = r"""
package vx_gpu_pkg;

  // Memory types
  localparam MEM_TYPE_REG = 0;
  localparam MEM_TYPE_BRAM = 1;
  localparam MEM_TYPE_LUTRAM = 2;

  // Execute types
  localparam EXE_ALU = 0;
  localparam EXE_LSU = 1;
  localparam EXE_CSR = 2;
  localparam EXE_ATG = 3;
  localparam EXE_FPU = 4;
  localparam EXE_SFU = 5;
  localparam EXE_TCU = 6;
  localparam EXE_DXA = 7;
  localparam NUM_EXE_UNITS = 8;

  // LSU types
  localparam LSU_WLOAD  = 0;
  localparam LSU_WSTORE = 1;
  localparam LSU_HLOAD  = 2;
  localparam LSU_HSTORE = 3;
  localparam LSU_BLOAD  = 4;
  localparam LSU_BSTORE = 5;
  localparam LSU_FLOAD  = 6;
  localparam LSU_FSTORE = 7;

  // SFU types
  localparam SFU_CSRRW   = 0;
  localparam SFU_CSRRS   = 1;
  localparam SFU_CSRRC   = 2;
  localparam SFU_ECALL   = 3;
  localparam SFU_EBREAK  = 4;
  localparam SFU_MRET    = 5;
  localparam SFU_FENCE   = 6;
  localparam SFU_TMC     = 7;
  localparam SFU_WSPAWN  = 8;
  localparam SFU_SPAWN   = 9;
  localparam SFU_PRED    = 10;
  localparam SFU_CSRRX   = 11;
  localparam SFU_ISPC    = 12;
  localparam SFU_ICACHE  = 13;

  // AMO types
  localparam AMO_ADD  = 0;
  localparam AMO_AND  = 1;
  localparam AMO_OR   = 2;
  localparam AMO_XOR  = 3;
  localparam AMO_MIN  = 4;
  localparam AMO_MAX  = 5;
  localparam AMO_MINU = 6;
  localparam AMO_MAXU = 7;

  // SRAM types for DXA
  localparam LMEM_DMA_ADDR_WIDTH = 32;
  localparam DXA_LMEM_ATTR_W = 8;
  localparam DXA_LMEM_TAG_W = 32;
  localparam BAR_ADDR_W = 32;
  localparam L1_MEM_ARB_TAG_WIDTH = 32;
  localparam NC_WIDTH = 1;
  localparam HART_ID_BITS = 8;
  localparam BAR_SIZE_W = 32;

  typedef struct packed {
    logic [31:0] data;
    logic [31:0] mask;
    logic [1:0]  addr;
    logic [1:0]  tid;
    logic        pmask;
  } sfu_header_t;

  typedef struct packed {
    logic [31:0] addr;
    logic [31:0] data;
    logic        valid;
    logic [1:0]  mask;
  } mem_req_t;

  typedef struct packed {
    logic [31:0] data;
    logic        valid;
    logic [1:0]  mask;
  } mem_rsp_t;

endpackage
"""
    # Fix package name to match actual RTL
    stub = stub.replace('package vx_gpu_pkg;', 'package VX_gpu_pkg;')
    stub = stub.replace('endpackage', 'endpackage')
    with open(GPU_PKG_STUB, 'w') as f:
        f.write(stub)
    print(f"  Wrote GPU pkg stub to {GPU_PKG_STUB}")

def write_synth_script():
    """Write the Yosys synthesis script."""
    script = r"""
// DXA full unit synthesis via Synlig (Surelog frontend + Yosys backend)
read_systemverilog -sv \
    /tmp/dxa_synth/VX_gpu_pkg_stub.sv \
    /tmp/dxa_synth/VX_dxa_pkg.sv \
    /tmp/dxa_synth/vortex_stubs.sv \
    /tmp/dxa_synth/VX_dxa_req_bus_if.sv \
    /tmp/dxa_synth/VX_dxa_worker_req_if.sv \
    /tmp/dxa_synth/VX_dxa_addr_gen.sv \
    /tmp/dxa_synth/VX_dxa_completion.sv \
    /tmp/dxa_synth/VX_dxa_desc_table.sv \
    /tmp/dxa_synth/VX_dxa_dispatch.sv \
    /tmp/dxa_synth/VX_dxa_req_arb.sv \
    /tmp/dxa_synth/VX_dxa_setup.sv \
    /tmp/dxa_synth/VX_dxa_smem_wr.sv \
    /tmp/dxa_synth/VX_dxa_watchdog.sv \
    /tmp/dxa_synth/VX_dxa_gmem_req.sv \
    /tmp/dxa_synth/VX_dxa_worker.sv \
    /tmp/dxa_synth/VX_dxa_core.sv \
    /tmp/dxa_synth/VX_dxa_unit.sv

hierarchy -top VX_dxa_unit
synth -flatten
stat
"""
    with open(SYNTH_SCRIPT, 'w') as f:
        f.write(script)
    print(f"  Wrote synth script to {SYNTH_SCRIPT}")

def main():
    print("=== Preparing DXA files for Yosys synthesis ===")
    
    # Step 1: Apply transformations to all DXA .sv files
    sv_files = sorted(glob.glob(os.path.join(DXA_DIR, "VX_dxa_*.sv")))
    for fpath in sv_files:
        with open(fpath, 'r') as f:
            text = f.read()
        
        orig = text
        text = fix_part_selectes(text)
        text = strip_runtime_assert(text)
        text = fix_bits(text)
        text = fix_string_params(text)
        
        if text != orig:
            with open(fpath, 'w') as f:
                f.write(text)
            changes = sum(1 for a, b in zip(orig.split('\n'), text.split('\n')) if a != b)
            print(f"  Fixed {os.path.basename(fpath)}: {changes} lines changed")
        else:
            print(f"  {os.path.basename(fpath)}: no changes needed")
    
    # Step 2: Write stubs and GPU pkg
    write_stubs()
    write_gpu_pkg_stub()
    write_synth_script()
    
    print("\n=== Done. Ready for synthesis ===")

if __name__ == "__main__":
    main()
