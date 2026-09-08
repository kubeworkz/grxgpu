#!/usr/bin/env python3
"""
Combined Phase A + Phase B transform: produces a single Yosys-compatible
flat TFR file for Yosys synthesis.

Phase A: Strip SV constructs Yosys cannot handle (always_ff, macros, ifdefs)
Phase B: Hoist generate-scoped wire declarations to module scope

Usage: python3 flatten_tfr_v2.py [ROOT_DIR] [OUTPUT_FILE]
"""
import re, sys, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/grxgpu"
OUT  = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tfr_flat_v2.sv"

TFR_DIR = os.path.join(ROOT, "hw/rtl/tcu/tfr")

MODULES = [
    #"VX_tcu_tfr_wmul.sv",  # excluded: parameterized ranges incompatible with Yosys 0.48
    "VX_tcu_tfr_shared_mul.sv",
    "VX_tcu_tfr_mul_join.sv",
    "VX_tcu_tfr_mul_f16.sv",
    "VX_tcu_tfr_mul_f8.sv",
    "VX_tcu_tfr_mul_f4.sv",
    "VX_tcu_tfr_mul_i8.sv",
    "VX_tcu_tfr_mul_i4.sv",
    "VX_tcu_tfr_classifier.sv",
    "VX_tcu_tfr_max_exp.sv",
    "VX_tcu_tfr_exc_reduce.sv",
    "VX_tcu_tfr_lane_mask.sv",
    "VX_tcu_tfr_norm_round.sv",
    "VX_tcu_tfr_align.sv",
    "VX_tcu_tfr_pipe_register.sv",
    "VX_tcu_tfr_acc.sv",
    "VX_tcu_fedp_tfr.sv",
]

BITS_MAP = {
    "fedp_excep_t": "3", "fedp_class_t": "4", "tcu_header_t": "32",
}


# ---------------------------------------------------------------------------
# Phase A helpers
# ---------------------------------------------------------------------------

def strip_preprocessor_blocks(content):
    """Strip preprocessor directives but KEEP their bodies."""
    lines = content.split("\n")
    result = []
    stack = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if re.match(r"`define\b", stripped) or re.match(r"`undef\b", stripped) or re.match(r"`include\b", stripped):
            i += 1; continue
        if re.match(r"`ifdef\s+\w+", stripped):
            stack.append("keep"); i += 1; continue
        if re.match(r"`ifndef\s+\w+", stripped):
            stack.append("skip"); i += 1; continue
        if re.match(r"`elsif\s+\w+", stripped):
            if stack: stack[-1] = "skip" if stack[-1] == "keep" else "keep"
            i += 1; continue
        if re.match(r"`else\b", stripped):
            if stack: stack[-1] = "skip" if stack[-1] == "keep" else "keep"
            i += 1; continue
        if re.match(r"`endif\b", stripped):
            if stack: stack.pop()
            i += 1; continue
        if any(s == "skip" for s in stack):
            i += 1; continue
        result.append(line)
        i += 1
    return "\n".join(result)


def strip_simulation_macros(content):
    for macro in ["STATIC_ASSERT", "UNUSED_SPARAM", "UNUSED_PARAM",
                  "UNUSED_PIN", "UNUSED_VAR", "MAP_AOS_SOA"]:
        result = []
        i = 0
        while i < len(content):
            match = re.search(rf"`{macro}\s*\(", content[i:])
            if match:
                result.append(content[i:i+match.start()])
                depth = 1
                j = i + match.end()
                while j < len(content) and depth > 0:
                    if content[j] == '(': depth += 1
                    elif content[j] == ')': depth -= 1
                    j += 1
                i = j
            else:
                result.append(content[i:])
                break
        content = "".join(result)
    content = re.sub(r"`UNUSED_VAR\s*\([^)]*\)", "", content)
    content = re.sub(r"`UNUSED_SPARAM\s*\([^)]*\)", "", content)
    content = re.sub(r"`UNUSED_PARAM\s*\([^)]*\)", "", content)
    content = re.sub(r"`UNUSED_PIN\s*\([^)]*\)", "", content)
    return content


def strip_io_calls(content):
    """Strip $display/$write/$monitor and `TRACE calls using depth counting."""
    for pat in ["$display", "$write", "$monitor", "`TRACE", "`TRACE_ARRAY", "`TRACE_ARRAY1D"]:
        result = []
        i = 0
        while i < len(content):
            idx = content.find(pat, i)
            if idx < 0:
                result.append(content[i:])
                break
            result.append(content[i:idx])
            paren_start = content.find('(', idx + len(pat))
            if paren_start < 0:
                i = idx + len(pat)
                continue
            depth = 1
            j = paren_start + 1
            while j < len(content) and depth > 0:
                if content[j] == '(': depth += 1
                elif content[j] == ')': depth -= 1
                j += 1
            i = j
        content = "".join(result)
    content = re.sub(r"(?<=\s)\$time\b", "0", content)
    content = re.sub(r"(?<=\s)\$error\s*\([^)]*\)", "/* error */", content)
    return content


def transform(content):
    # 1. Strip debug/simulation blocks BEFORE generic preprocessor
    content = re.sub(r"`ifdef\s+SIMULATION.*?`endif[^\n]*\n", "", content, flags=re.DOTALL)
    content = re.sub(r"`ifdef\s+DBG_TRACE_TCU.*?`endif[^\n]*\n", "", content, flags=re.DOTALL)
    # 2. Strip $display/$write/TRACE (depth-counting)
    content = strip_io_calls(content)
    # 3. Strip preprocessor blocks, keeping bodies
    content = strip_preprocessor_blocks(content)
    # 4. Strip simulation macros
    content = strip_simulation_macros(content)
    # 5. FORCE_BUILTIN_ADDER
    content = re.sub(r"`FORCE_BUILTIN_ADDER\s*\(([^)]+)\)", r"1", content)
    content = re.sub(r"^\s*`FORCE_BUILTIN_ADDER[^\n]*\n?", "", content, flags=re.MULTILINE)
    # 6. always_ff
    content = re.sub(r"always_ff\s+@\s*\(\s*posedge\s+(\w+)\s*\)", r"always @(\1)", content)
    content = re.sub(r"always_ff\s+@\s*\(([^)]+)\)", r"always @(\1)", content)
    # 7. always_comb / always_latch
    content = re.sub(r"\balways_comb\b", "always @*", content)
    content = re.sub(r"\balways_latch\b", "always @*", content)
    # 8. Strip parameter STRING
    content = re.sub(r"^\s*parameter\s+STRING\s+\w+\s*=\s*\"[^\"]*\"\s*,?\s*\n?",
                     "", content, flags=re.MULTILINE)
    # 9. Strip verilator attributes
    content = re.sub(r"/\*\s*verilator[^*]*\*/", "", content)
    # 10. Replace $bits()
    for tn, w in BITS_MAP.items():
        content = content.replace(f"$bits({tn})", w)
    content = re.sub(r"\$bits\(\w+\)", "32", content)
    # 11. Strip typedef struct packed
    content = re.sub(r"typedef\s+struct\s+packed\s*\{[^}]*\}\s*\w+\s*;",
                     "/* typedef stripped */", content, flags=re.DOTALL)
    # 12. Type names
    content = re.sub(r"\bfedp_excep_t\b", "logic [2:0]", content)
    content = re.sub(r"\bfedp_class_t\b", "logic [3:0]", content)
    # 13. Struct field access
    content = content.replace(".is_inf", "[2]")
    content = content.replace(".is_nan", "[1]")
    content = content.replace(".sign", "[0]")
    content = content.replace(".is_zero", "[3]")
    content = content.replace(".is_sub", "[2]")
    # 14. Strip `STRING
    content = content.replace("`STRING", "")
    # 15. Strip `include
    content = re.sub(r'`include\s+"[^"]*"', '', content)
    # 16. Strip package imports
    content = re.sub(r"import\s+\w+::\*;", "", content)
    # 17. Resolve VX_tcu_pkg::func(TCU_XXX_ID)
    func_map = {
        "exp_bits": {"TCU_FP32_ID":"8","TCU_TF32_ID":"8","TCU_FP16_ID":"5","TCU_BF16_ID":"8","TCU_FP8_ID":"4","TCU_BF8_ID":"5"},
        "sign_pos": {"TCU_FP32_ID":"31","TCU_TF32_ID":"18","TCU_FP16_ID":"15","TCU_BF16_ID":"15","TCU_FP8_ID":"7","TCU_BF8_ID":"7"},
        "sig_bits": {"TCU_FP32_ID":"23","TCU_TF32_ID":"10","TCU_FP16_ID":"10","TCU_BF16_ID":"7","TCU_FP8_ID":"3","TCU_BF8_ID":"2"},
        "tcu_fmt_width": {"TCU_FP32_ID":"32","TCU_TF32_ID":"32","TCU_FP16_ID":"16","TCU_BF16_ID":"16","TCU_FP8_ID":"8","TCU_BF8_ID":"8"},
    }
    for fn, vals in func_map.items():
        for fid, val in vals.items():
            content = content.replace(f"VX_tcu_pkg::{fn}({fid})", val)
            content = content.replace(f"tcu_pkg::{fn}({fid})", val)
            content = content.replace(f"{fn}({fid})", val)
    # 18. Backtick-escape TCU_*_ID
    content = re.sub(r"(?<!\w)(TCU_(?:FP32|TF32|FP16|BF16|FP8|BF8|MXFP8|MXBF8|MXFP4|NVFP4|I32|I8|U8|I4|U4)_ID)(?!\w)",
                     r"`\1", content)
    content = re.sub(r"(?<!\w)(TCU_(?:NT|NR|NRA|NRB|NRC|EXP_BITS|FMT_WIDTH|TILE_CAP|BLOCK_CAP|TC_[MNK]|M_STEPS|N_STEPS|K_STEPS))(?!\w)",
                     r"`\1", content)
    return content


# ---------------------------------------------------------------------------
# Phase B: Hoist generate-scoped wire/logic/reg to module scope
# ---------------------------------------------------------------------------

def hoist_gen_scoped(mod_text, max_loop=16):
    """Hoist wire/logic/reg declarations from inside for(genvar) blocks to module scope.
    Operates on a SINGLE module's text. Returns modified text.
    """
    lines = mod_text.split('\n')

    # Find all generate for-loops and their wire declarations
    to_hoist = []  # (line_idx, name, dtype, width, var, label)

    # Stack-based gen block tracking: (var, label, begin_depth)
    # begin_depth = begin/end nesting depth when the genvar loop was entered
    gen_stack = []  # stack of (var, label, begin_depth)
    begin_depth = 0

    for i, line in enumerate(lines):
        s = line.strip()
        # Count ALL begin/end for proper nesting (including standalone and labeled)
        if re.search(r'\bbegin\b', s):
            begin_depth += 1
        
        gm = re.match(r'for\s*\(\s*genvar\s+(\w+)\s*=', s)
        if gm:
            var = gm.group(1)
            lm = re.search(r'begin\s*:\s*(\w+)', s)
            label = lm.group(1) if lm else f'gen{i}'
            gen_stack.append((var, label, begin_depth - 1))
        
        if re.match(r'^\s*end\b', s) and not re.match(r'^\s*endmodule', s) and not re.match(r'^\s*endcase', s) and not re.match(r'^\s*endfunction', s) and not re.match(r'^\s*endtask', s):
            if gen_stack and begin_depth - 1 == gen_stack[-1][2]:
                gen_stack.pop()
            begin_depth = max(0, begin_depth - 1)
            continue
        
        # If we're inside any gen block, check for wire declarations
        if gen_stack:
            var, label, _ = gen_stack[-1]  # innermost gen block
            dm = re.match(r'^[ \t]*(wire|logic|reg)\s+(.*);\s*$', s)
            if dm:
                dtype = dm.group(1)
                rest = dm.group(2).strip()
                # Extract width prefix (everything before first name)
                # Handle: [4:0] raw_ea, raw_eb  or  [1:0][7:0] man_prod  or  [3:0][EXP_TERM_W_MXFP4-1:0] term_exp_biased
                width_prefix = ''
                names_part = rest
                # Match bracket pairs with any content (digits, params, expressions)
                wm = re.match(r'((?:\[[^\]]+\]\s*)+)', rest)
                if wm:
                    width_prefix = wm.group(1).strip()
                    names_part = rest[wm.end():].strip()
                elif rest.startswith('signed'):
                    wm2 = re.match(r'signed\s+((?:\[[^\]]+\]\s*)+)', rest)
                    if wm2:
                        width_prefix = 'signed ' + wm2.group(1).strip()
                        names_part = rest[wm2.end():].strip()
                # Split by comma for multi-name declarations: raw_ea, raw_eb
                # BUT only split if there's no '=' (assignment uses {} concatenation with commas)
                if '=' in names_part:
                    name_candidates = [names_part.strip()]
                else:
                    name_candidates = [n.strip() for n in names_part.split(',')]
                for name_raw in name_candidates:
                    name_raw = name_raw.strip()
                    # Strip array dim [N] and assignment = expr
                    name_raw = re.sub(r'\s*\[.*$', '', name_raw)  # remove [N]
                    name_raw = re.sub(r'\s*=.*$', '', name_raw)   # remove = expr
                    name = name_raw.split()[0] if name_raw.split() else ''
                    if not name or not re.match(r'[a-zA-Z_]', name):
                        continue
                    # Skip wires with genvar-dependent widths (e.g. [i-1:0])
                    width = width_prefix
                    if width and re.search(rf'\b{re.escape(var)}\b', width):
                        continue
                    # Resolve known parameter-dependent widths to literals
                    # Build a map of localparams from the module body
                    if width and re.search(r'[a-zA-Z_]\w*\s*[-+*/]', width):
                        # Collect localparam values from the module
                        for lp in re.finditer(r'localparam\s+(?:\[.*?\]\s+)?(\w+)\s*=\s*([^;]+);', mod_text):
                            lp_name, lp_val = lp.group(1), lp.group(2).strip()
                            if lp_val.isdigit():
                                width = re.sub(rf'\b{re.escape(lp_name)}\b', lp_val, width)
                        # Evaluate simple arithmetic expressions in width
                        # e.g. [6-1:0] -> [5:0]
                        for wm_eval in re.finditer(r'\[(\d+)\s*([-+])\s*(\d+)\s*:\s*(\d+)\]', width):
                            a, op, b, lo = int(wm_eval.group(1)), wm_eval.group(2), int(wm_eval.group(3)), wm_eval.group(4)
                            result = a - b if op == '-' else a + b
                            width = width[:wm_eval.start()] + f'[{result}:{lo}]' + width[wm_eval.end():]
                        # If still has non-numeric content after resolution, skip
                        if re.search(r'[a-zA-Z_]', re.sub(r'\[|\]|:', '', width)):
                            continue
                    if name and not name.startswith(var):
                        to_hoist.append((i, name, dtype, width, var, label))

    if not to_hoist:
        return mod_text

    # Remove declaration lines and replace references within the gen block scope only
    # First pass: find gen block boundaries for each declaration
    # For each gen block, find its start (for(genvar) line) and matching end
    gen_boundaries = []  # (start_line, end_line) for each gen block
    gen_stack2 = []
    begin_depth2 = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if re.search(r'\bbegin\b', s):
            begin_depth2 += 1
        gm = re.match(r'for\s*\(\s*genvar\s+(\w+)\s*=', s)
        if gm:
            gen_stack2.append(('start', begin_depth2 - 1))
        if re.match(r'^\s*end\b', s) and not re.match(r'^\s*end(module|case|function|task)\b', s):
            if gen_stack2 and begin_depth2 - 1 == gen_stack2[-1][1]:
                gen_stack2.pop()  # found matching end
            begin_depth2 = max(0, begin_depth2 - 1)
    # Actually, simpler: for each declaration, find the gen block it belongs to
    # by scanning backward from the line to find the for(genvar) and forward to find end
    def find_gen_scope(line_idx):
        # Scan backward to find the enclosing for(genvar)
        depth = 0
        for j in range(line_idx, -1, -1):
            s = lines[j].strip()
            if re.match(r'^\s*end\b', s) and not re.match(r'^\s*end(module|case|function|task)\b', s):
                depth += 1
            if re.search(r'\bbegin\b', s):
                depth -= 1
            if depth < 0 and re.match(r'for\s*\(\s*genvar', s):
                start = j
                # Find matching end
                depth2 = 0
                for k in range(j, len(lines)):
                    sk = lines[k].strip()
                    if re.search(r'\bbegin\b', sk):
                        depth2 += 1
                    if re.match(r'^\s*end\b', sk) and not re.match(r'^\s*end(module|case|function|task)\b', sk):
                        depth2 -= 1
                        if depth2 < 0:
                            return (start, k)
                return (start, len(lines) - 1)
        return (0, len(lines) - 1)

    # Build scope ranges for each declaration
    decl_scopes = []
    for line_idx, name, dtype, width, var, label in to_hoist:
        start, end = find_gen_scope(line_idx)
        decl_scopes.append((line_idx, name, dtype, width, var, label, start, end))

    # Group declarations by line_idx (multi-name lines like 'logic [4:0] raw_ea, raw_eb')
    from collections import defaultdict
    lines_by_idx = defaultdict(list)
    for entry in decl_scopes:
        lines_by_idx[entry[0]].append(entry)

    # Remove declaration lines and replace references within their gen block scope
    # Process each unique line once
    for line_idx in sorted(lines_by_idx.keys(), reverse=True):
        entries = lines_by_idx[line_idx]
        # Replace ALL names from this line in the gen block scope
        scope_start = entries[0][6]
        scope_end = entries[0][7]
        for _, name, dtype, width, var, label, _, _ in entries:
            hname = f'{label}_{name}'
            for j in range(scope_start, scope_end + 1):
                if j == line_idx:
                    continue
                lines[j] = re.sub(rf'(?<!_)\b{re.escape(name)}\b', f'{hname}[{var}]', lines[j])
        # Now remove the declaration line
        lines[line_idx] = ''

    # Build hoisted declarations
    hoisted = []
    seen = set()
    for _, name, dtype, width, var, label in to_hoist:
        hname = f'{label}_{name}'
        if hname in seen:
            continue
        seen.add(hname)
        if width:
            hoisted.append(f'    wire {width} {hname} [0:{max_loop-1}];')
        else:
            hoisted.append(f'    wire [7:0] {hname} [0:{max_loop-1}];')

    # Find insertion point: after the port-list closing `);`
    result_lines = []
    inserted = False
    for i, line in enumerate(lines):
        result_lines.append(line)
        if not inserted and line.strip() == ');':
            result_lines.append('')
            result_lines.append('    // Phase B: Hoisted generate-scoped wires')
            result_lines.extend(hoisted)
            result_lines.append('')
            inserted = True

    return '\n'.join(result_lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

HEADER = """// Yosys-compatible TFR flat file (Phase A+B preprocessed)
// Auto-generated by flatten_tfr_v2.py
`define VX_CFG_XLEN 32
`define VX_CFG_NUM_THREADS 4
`define VX_CFG_NUM_WARPS 4
`define VX_CFG_NUM_TCU_LANES 4
`define CLOG2(x) ($clog2(x))
`define FORCE_BUILTIN_ADDER(x) (1)
`define MAP_AOS_SOA(i, n, a, b)

// Format utility functions (from VX_gpu_pkg)
function automatic logic tcu_fmt_is_int(input logic [4:0] fmt);
    tcu_fmt_is_int = fmt[4];
endfunction

function automatic logic tcu_fmt_is_signed_int(input logic [3:0] int_fmt);
    tcu_fmt_is_signed_int = int_fmt[0];
endfunction

function automatic logic tcu_fmt_is_bfloat(input logic [3:0] float_fmt);
    tcu_fmt_is_bfloat = float_fmt[0];
endfunction

function automatic logic tcu_fmt_is_mx(input logic [4:0] fmt);
    case (fmt)
        5'd10, 5'd11, 5'd8, 5'd9: tcu_fmt_is_mx = 1'b1;
        default: tcu_fmt_is_mx = 1'b0;
    endcase
endfunction

function automatic int unsigned tcu_fmt_width(input logic [4:0] fmt);
    case (fmt)
        5'd2, 5'd3: tcu_fmt_width = 16;
        5'd10, 5'd11, 5'd19, 5'd20: tcu_fmt_width = 4;
        5'd4, 5'd5, 5'd17, 5'd18, 5'd8, 5'd9: tcu_fmt_width = 8;
        5'd0, 5'd16, 5'd1: tcu_fmt_width = 32;
        default: tcu_fmt_width = 0;
    endcase
endfunction

localparam TCU_MAX_INPUTS = 16;

// VX_tcu_tfr_wmul: simplified for synthesis (behavioral multiply)
module VX_tcu_tfr_wmul #(
    parameter N = 4, M = 4, LANES = 1, SHARED_B = 0, P = 8, USE_DSP = 0
) (
    input  wire [LANES*N-1:0] a,
    input  wire [LANES*M-1:0] b,
    output wire [LANES*P-1:0] p
);
    genvar i;
    generate
        for (i = 0; i < LANES; i = i + 1) begin : g_mul
            localparam BI = (SHARED_B != 0) ? 0 : i;
            assign p[i*P +: P] = a[i*N +: N] * b[BI*M +: M];
        end
    endgenerate
endmodule

// Blackbox stubs for VX_popcount
(* blackbox *)
module VX_popcount63 (
    input  wire [5:0] data_in,
    output wire [2:0] data_out
);
endmodule

(* blackbox *)
module VX_popcount32 (
    input  wire [2:0] data_in,
    output wire [1:0] data_out
);
endmodule

// VX_pipe_register: behavioral pipeline register
module VX_pipe_register #(
    parameter DATAW  = 1,
    parameter RESETW = 0,
    parameter DEPTH  = 1,
    parameter INIT_VALUE = 0
) (
    input  wire              clk,
    input  wire              reset,
    input  wire              enable,
    input  wire [DATAW-1:0]  data_in,
    output wire [DATAW-1:0]  data_out
);
    reg [DATAW-1:0] r [0:DEPTH];
    integer i;
    always_ff @(posedge clk) begin
        if (reset) begin
            for (i = 0; i <= DEPTH; i = i + 1)
                r[i] <= DATAW'(INIT_VALUE);
        end else if (enable) begin
            r[0] <= data_in;
            for (i = 1; i <= DEPTH; i = i + 1)
                r[i] <= r[i-1];
        end
    end
    assign data_out = r[DEPTH];
endmodule

// VX_lzc: behavioral leading zero count
module VX_lzc #(
    parameter N       = 2,
    parameter REVERSE = 0,
    parameter LOGN    = 1
) (
    input  wire [N-1:0]    data_in,
    output wire [LOGN-1:0] data_out,
    output wire            valid_out
);
    integer i;
    reg [LOGN-1:0] count;
    reg found;
    always_comb begin
        found = 0;
        count = 0;
        for (i = 0; i < N; i = i + 1) begin
            if (!found && data_in[REVERSE ? (N-1-i) : i]) begin
                count = LOGN'(i);
                found = 1;
            end
        end
    end
    assign data_out = count;
    assign valid_out = |data_in;
endmodule

// VX_csa_tree: simplified behavioral carry-save adder tree
module VX_csa_tree #(
    parameter N = 16,
    parameter W = 8,
    parameter K = 6,
    parameter BAL = 1,
    parameter S = 12
) (
    input  wire [N*W-1:0] operands,
    output wire [S-1:0]   sum,
    output wire [S-1:0]   carry
);
    // Simple addition: sum of all N W-bit operands
    integer i;
    reg [S-1:0] total;
    always_comb begin
        total = 0;
        for (i = 0; i < N; i = i + 1)
            total = total + S'(operands[i*W +: W]);
    end
    assign sum = total;
    assign carry = 0;
endmodule

// VX_ks_adder: simplified for Yosys synthesis (BYPASS only)
module VX_ks_adder #(
    parameter N = 16,
    parameter BYPASS = 0
) (
    input  wire [N-1:0] dataa,
    input  wire [N-1:0] datab,
    input  wire         cin,
    output wire [N-1:0] sum,
    output wire         cout
);
    assign {cout, sum} = dataa + datab + N'(cin);
endmodule

// Blackbox stub for VX_popcount (parameterized popcount)
(* blackbox *)
module VX_popcount #(
    parameter N = 64,
    parameter M = 7
) (
    input  wire [N-1:0] data_in,
    output wire [M-1:0] data_out
);
endmodule

// TCU format ID constants (from VX_tcu_pkg)
`define TCU_FP32_ID   0
`define TCU_TF32_ID   1
`define TCU_FP16_ID   2
`define TCU_BF16_ID   3
`define TCU_FP8_ID    4
`define TCU_BF8_ID    5
`define TCU_MXFP8_ID  6
`define TCU_MXBF8_ID  7
`define TCU_MXFP4_ID  8
`define TCU_NVFP4_ID  9
`define TCU_I8_ID    17
`define TCU_U8_ID    18
`define TCU_I4_ID    19
`define TCU_U4_ID    20
`define TCU_EXP_BITS  8
`define TCU_TC_K     16

"""


def main():
    output_lines = [HEADER]
    seen_modules = set()
    total_gen = 0

    for modfile in MODULES:
        path = os.path.join(TFR_DIR, modfile)
        if not os.path.exists(path):
            print(f"  SKIP {modfile} (not found)")
            continue

        with open(path) as f:
            content = f.read()

        content = transform(content)

        m = re.search(r"module\s+(\w+)", content)
        if m and m.group(1) in seen_modules:
            continue
        if m:
            seen_modules.add(m.group(1))

        # Count gen-scoped
        gen_scoped = 0
        in_gen = False
        depth = 0
        for line in content.split("\n"):
            s = line.strip()
            if "for (genvar" in s:
                in_gen = True
                depth = 1
            elif in_gen:
                depth += s.count("begin") - s.count("end")
                if re.match(r"(wire|reg|logic)\s+", s):
                    gen_scoped += 1
                if depth <= 0:
                    in_gen = False
        total_gen += gen_scoped

        # Phase B: hoist gen-scoped wires
        content = hoist_gen_scoped(content)

        output_lines.append(f"// ---- {modfile} ----")
        output_lines.append(content)
        output_lines.append("")

        status = f"  {modfile}: {gen_scoped} gen-scoped" if gen_scoped else f"  {modfile}: clean"
        print(status)

    flat = "\n".join(output_lines)
    with open(OUT, "w") as f:
        f.write(flat)

    print(f"\nFlattened {len(seen_modules)} modules -> {OUT}")
    print(f"  File size: {os.path.getsize(OUT)} bytes")
    print(f"  Generate-scoped declarations: {total_gen} (Phase B hoisted)")


if __name__ == "__main__":
    main()
