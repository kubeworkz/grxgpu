<<<<<<< Updated upstream
#!/usr/bin/env python3
"""
Combined Phase A transform + flatten: produces a single Yosys-compatible
flat TFR file for Yosys synthesis.

Usage: python3 flatten_tfr_v2.py [ROOT_DIR] [OUTPUT_FILE]
"""
import re, sys, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/grxgpu"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tfr_flat_v2.sv"

TFR_DIR = os.path.join(ROOT, "hw/rtl/tcu/tfr")

# Module load order (dependencies first)
MODULES = [
    "VX_tcu_tfr_wmul.sv",
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

# ---- Phase A transforms ----

BITS_MAP = {
    "fedp_excep_t": "3", "fedp_class_t": "4", "tcu_header_t": "32",
}


def transform(content):
    """Apply all Phase A transforms."""

    # Strip simulation macros — use parenthesis-depth counting
    for macro in ["STATIC_ASSERT", "UNUSED_SPARAM", "UNUSED_PARAM",
                  "UNUSED_PIN", "UNUSED_VAR", "MAP_AOS_SOA"]:
        result = []
        i = 0
        while i < len(content):
            # Look for the macro at current position
            match = re.search(rf"`{macro}\s*\(", content[i:])
            if match:
                result.append(content[i:i+match.start()])
                # Skip past the matching closing paren
                depth = 1
                j = i + match.end()
                while j < len(content) and depth > 0:
                    if content[j] == '(':
                        depth += 1
                    elif content[j] == ')':
                        depth -= 1
                    j += 1
                i = j
            else:
                result.append(content[i:])
                break
        content = "".join(result)

    # Strip UNUSED_ macros that appear inline (not at line start)
    content = re.sub(r"`UNUSED_VAR\s*\([^)]*\)", "", content)
    content = re.sub(r"`UNUSED_SPARAM\s*\([^)]*\)", "", content)
    content = re.sub(r"`UNUSED_PARAM\s*\([^)]*\)", "", content)
    content = re.sub(r"`UNUSED_PIN\s*\([^)]*\)", "", content)

    # Replace inline `FORCE_BUILTIN_ADDER(x) with 1 (use carry-chain)
    content = re.sub(r"`FORCE_BUILTIN_ADDER\s*\(([^)]+)\)", r"1", content)

    # Strip any remaining `FORCE_BUILTIN_ADDER lines
    content = re.sub(r"^\s*`FORCE_BUILTIN_ADDER[^\n]*\n?", "", content, flags=re.MULTILINE)

    # Strip DBG_TRACE_TCU blocks
    content = re.sub(r"`ifdef\s+DBG_TRACE_TCU.*?`endif[^\n]*\n", "", content, flags=re.DOTALL)

    # Strip TRACE / TRACE_ARRAY
    content = re.sub(r"^\s*`TRACE\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*`TRACE_ARRAY\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)

    # Strip $display / $write / $time / $error (only when preceded by whitespace or start-of-line)
    content = re.sub(r"(?<=\s)\$display\s*\([^)]*\)", "0", content)
    content = re.sub(r"(?<=\s)\$write\s*\([^)]*\)", "0", content)
    content = re.sub(r"(?<=\s)\$time\b", "0", content)
    content = re.sub(r"(?<=\s)\$error\s*\([^)]*\)", "/* error */", content)
    # Also handle $display at start of statement
    content = re.sub(r"^\s*\$display\s*\([^)]*\)", "0", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*\$write\s*\([^)]*\)", "0", content, flags=re.MULTILINE)

    # Replace always_ff → always @(posedge ...)
    content = re.sub(r"always_ff\s+@\s*\(\s*posedge\s+(\w+)\s*\)", r"always @(\1)", content)
    content = re.sub(r"always_ff\s+@\s*\(([^)]+)\)", r"always @(\1)", content)

    # Replace always_comb / always_latch → always @*
    content = re.sub(r"\balways_comb\b", "always @*", content)
    content = re.sub(r"\balways_latch\b", "always @*", content)

    # Strip parameter STRING INSTANCE_ID
    content = re.sub(r"^\s*parameter\s+STRING\s+\w+\s*=\s*\"[^\"]*\"\s*,?\s*\n?",
                     "", content, flags=re.MULTILINE)

    # Strip verilator attributes
    content = re.sub(r"/\*\s*verilator[^*]*\*/", "", content)

    # Replace $bits()
    for type_name, width in BITS_MAP.items():
        content = content.replace(f"$bits({type_name})", width)
    content = re.sub(r"\$bits\(\w+\)", "32", content)

    # Strip typedef struct packed
    content = re.sub(r"typedef\s+struct\s+packed\s*\{[^}]*\}\s*\w+\s*;",
                     "/* typedef stripped */", content, flags=re.DOTALL)

    # Replace type names with explicit wire widths
    content = re.sub(r"\bfedp_excep_t\b", "logic [2:0]", content)
    content = re.sub(r"\bfedp_class_t\b", "logic [3:0]", content)

    # Replace struct field accesses with bit indexing
    content = content.replace(".is_inf", "[2]")
    content = content.replace(".is_nan", "[1]")
    content = content.replace(".sign", "[0]")
    content = content.replace(".is_zero", "[3]")
    content = content.replace(".is_sub", "[2]")

    # Strip remaining backtick macros
    content = content.replace("`STRING", "")
    content = re.sub(r"`ifdef\s+SIMULATION.*?`endif[^\n]*\n", "", content, flags=re.DOTALL)
    content = re.sub(r'`include\s+"[^"]*"', '', content)

    # Strip package imports
    content = re.sub(r"import\s+\w+::\*;", "", content)

    # Resolve VX_tcu_pkg::func(TCU_XXX_ID) calls FIRST (before backtick-escaping)
    func_map = {
        "exp_bits": {"TCU_FP32_ID": "8", "TCU_TF32_ID": "8", "TCU_FP16_ID": "5",
                      "TCU_BF16_ID": "8", "TCU_FP8_ID": "4", "TCU_BF8_ID": "5"},
        "sign_pos": {"TCU_FP32_ID": "31", "TCU_TF32_ID": "18", "TCU_FP16_ID": "15",
                      "TCU_BF16_ID": "15", "TCU_FP8_ID": "7", "TCU_BF8_ID": "7"},
        "sig_bits": {"TCU_FP32_ID": "23", "TCU_TF32_ID": "10", "TCU_FP16_ID": "10",
                      "TCU_BF16_ID": "7", "TCU_FP8_ID": "3", "TCU_BF8_ID": "2"},
        "tcu_fmt_width": {"TCU_FP32_ID": "32", "TCU_TF32_ID": "32", "TCU_FP16_ID": "16",
                           "TCU_BF16_ID": "16", "TCU_FP8_ID": "8", "TCU_BF8_ID": "8"},
    }
    for func_name, vals in func_map.items():
        for fmt_id, val in vals.items():
            content = content.replace(f"VX_tcu_pkg::{func_name}({fmt_id})", val)
            content = content.replace(f"tcu_pkg::{func_name}({fmt_id})", val)
            content = content.replace(f"{func_name}({fmt_id})", val)

    # Backtick-escape bare TCU_*_ID constants (they're `define macros in tcu_synth_defs.vh)
    content = re.sub(r"(?<!\w)(TCU_(?:FP32|TF32|FP16|BF16|FP8|BF8|MXFP8|MXBF8|MXFP4|NVFP4|I32|I8|U8|I4|U4)_ID)(?!\w)",
                     r"`\1", content)

    # Also backtick-escape TCU constant names used as bare identifiers
    content = re.sub(r"(?<!\w)(TCU_(?:NT|NR|NRA|NRB|NRC|EXP_BITS|FMT_WIDTH|TILE_CAP|BLOCK_CAP|TC_[MNK]|M_STEPS|N_STEPS|K_STEPS))(?!\w)",
                     r"`\1", content)

    return content


def main():
    output_lines = []

    # Add synthesis header
    output_lines.append("""// Yosys-compatible TFR flat file (Phase A preprocessed)
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

""")

    seen_modules = set()
    total_gen_scoped = 0

    for modfile in MODULES:
        path = os.path.join(TFR_DIR, modfile)
        if not os.path.exists(path):
            print(f"  SKIP {modfile} (not found)")
            continue

        with open(path) as f:
            content = f.read()

        content = transform(content)

        # Deduplicate modules
        m = re.match(r"module\s+(\w+)", content)
        if m and m.group(1) in seen_modules:
            continue
        if m:
            seen_modules.add(m.group(1))

        # Count gen-scoped
        gen_scoped = 0
        in_gen = False
        depth = 0
        for line in content.split("\n"):
            stripped = line.strip()
            if "for (genvar" in stripped:
                in_gen = True
                depth = 1
            elif in_gen:
                depth += stripped.count("begin") - stripped.count("end")
                if re.match(r"(wire|reg|logic)\s+", stripped):
                    gen_scoped += 1
                if depth <= 0:
                    in_gen = False
        total_gen_scoped += gen_scoped

        output_lines.append(f"// ---- {modfile} ----")
        output_lines.append(content)
        output_lines.append("")

        status = f"  {modfile}: {gen_scoped} gen-scoped" if gen_scoped else f"  {modfile}: clean"
        print(status)

    with open(OUT, "w") as f:
        f.write("\n".join(output_lines))

    print(f"\nFlattened {len(seen_modules)} modules -> {OUT}")
    print(f"  File size: {os.path.getsize(OUT)} bytes")
    print(f"  Generate-scoped declarations: {total_gen_scoped} (Phase B)")


if __name__ == "__main__":
    main()
=======
#!/usr/bin/env python3
"""
Combined Phase A transform + flatten: produces a single Yosys-compatible
flat TFR file for Yosys synthesis.

Usage: python3 flatten_tfr_v2.py [ROOT_DIR] [OUTPUT_FILE]
"""
import re, sys, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/grxgpu"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tfr_flat_v2.sv"

TFR_DIR = os.path.join(ROOT, "hw/rtl/tcu/tfr")

# Module load order (dependencies first)
MODULES = [
    "VX_tcu_tfr_wmul.sv",
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

# ---- Phase A transforms ----

BITS_MAP = {
    "fedp_excep_t": "3", "fedp_class_t": "4", "tcu_header_t": "32",
}


def transform(content):
    """Apply all Phase A transforms."""

    # Strip simulation macros — use parenthesis-depth counting
    for macro in ["STATIC_ASSERT", "UNUSED_SPARAM", "UNUSED_PARAM",
                  "UNUSED_PIN", "UNUSED_VAR", "MAP_AOS_SOA"]:
        result = []
        i = 0
        while i < len(content):
            # Look for the macro at current position
            match = re.search(rf"`{macro}\s*\(", content[i:])
            if match:
                result.append(content[i:i+match.start()])
                # Skip past the matching closing paren
                depth = 1
                j = i + match.end()
                while j < len(content) and depth > 0:
                    if content[j] == '(':
                        depth += 1
                    elif content[j] == ')':
                        depth -= 1
                    j += 1
                i = j
            else:
                result.append(content[i:])
                break
        content = "".join(result)

    # Strip UNUSED_ macros that appear inline (not at line start)
    content = re.sub(r"`UNUSED_VAR\s*\([^)]*\)", "", content)
    content = re.sub(r"`UNUSED_SPARAM\s*\([^)]*\)", "", content)
    content = re.sub(r"`UNUSED_PARAM\s*\([^)]*\)", "", content)
    content = re.sub(r"`UNUSED_PIN\s*\([^)]*\)", "", content)

    # Replace inline `FORCE_BUILTIN_ADDER(x) with 1 (use carry-chain)
    content = re.sub(r"`FORCE_BUILTIN_ADDER\s*\(([^)]+)\)", r"1", content)

    # Strip any remaining `FORCE_BUILTIN_ADDER lines
    content = re.sub(r"^\s*`FORCE_BUILTIN_ADDER[^\n]*\n?", "", content, flags=re.MULTILINE)

    # Strip DBG_TRACE_TCU blocks
    content = re.sub(r"`ifdef\s+DBG_TRACE_TCU.*?`endif[^\n]*\n", "", content, flags=re.DOTALL)

    # Strip TRACE / TRACE_ARRAY
    content = re.sub(r"^\s*`TRACE\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*`TRACE_ARRAY\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)

    # Strip $display / $write / $time / $error (only when preceded by whitespace or start-of-line)
    content = re.sub(r"(?<=\s)\$display\s*\([^)]*\)", "0", content)
    content = re.sub(r"(?<=\s)\$write\s*\([^)]*\)", "0", content)
    content = re.sub(r"(?<=\s)\$time\b", "0", content)
    content = re.sub(r"(?<=\s)\$error\s*\([^)]*\)", "/* error */", content)
    # Also handle $display at start of statement
    content = re.sub(r"^\s*\$display\s*\([^)]*\)", "0", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*\$write\s*\([^)]*\)", "0", content, flags=re.MULTILINE)

    # Replace always_ff → always @(posedge ...)
    content = re.sub(r"always_ff\s+@\s*\(\s*posedge\s+(\w+)\s*\)", r"always @(\1)", content)
    content = re.sub(r"always_ff\s+@\s*\(([^)]+)\)", r"always @(\1)", content)

    # Replace always_comb / always_latch → always @*
    content = re.sub(r"\balways_comb\b", "always @*", content)
    content = re.sub(r"\balways_latch\b", "always @*", content)

    # Strip parameter STRING INSTANCE_ID
    content = re.sub(r"^\s*parameter\s+STRING\s+\w+\s*=\s*\"[^\"]*\"\s*,?\s*\n?",
                     "", content, flags=re.MULTILINE)

    # Strip verilator attributes
    content = re.sub(r"/\*\s*verilator[^*]*\*/", "", content)

    # Replace $bits()
    for type_name, width in BITS_MAP.items():
        content = content.replace(f"$bits({type_name})", width)
    content = re.sub(r"\$bits\(\w+\)", "32", content)

    # Strip typedef struct packed
    content = re.sub(r"typedef\s+struct\s+packed\s*\{[^}]*\}\s*\w+\s*;",
                     "/* typedef stripped */", content, flags=re.DOTALL)

    # Replace type names with explicit wire widths
    content = re.sub(r"\bfedp_excep_t\b", "logic [2:0]", content)
    content = re.sub(r"\bfedp_class_t\b", "logic [3:0]", content)

    # Replace struct field accesses with bit indexing
    content = content.replace(".is_inf", "[2]")
    content = content.replace(".is_nan", "[1]")
    content = content.replace(".sign", "[0]")
    content = content.replace(".is_zero", "[3]")
    content = content.replace(".is_sub", "[2]")

    # Strip remaining backtick macros
    content = content.replace("`STRING", "")
    content = re.sub(r"`ifdef\s+SIMULATION.*?`endif[^\n]*\n", "", content, flags=re.DOTALL)
    content = re.sub(r'`include\s+"[^"]*"', '', content)

    # Strip package imports
    content = re.sub(r"import\s+\w+::\*;", "", content)

    # Resolve VX_tcu_pkg::func(TCU_XXX_ID) calls FIRST (before backtick-escaping)
    func_map = {
        "exp_bits": {"TCU_FP32_ID": "8", "TCU_TF32_ID": "8", "TCU_FP16_ID": "5",
                      "TCU_BF16_ID": "8", "TCU_FP8_ID": "4", "TCU_BF8_ID": "5"},
        "sign_pos": {"TCU_FP32_ID": "31", "TCU_TF32_ID": "18", "TCU_FP16_ID": "15",
                      "TCU_BF16_ID": "15", "TCU_FP8_ID": "7", "TCU_BF8_ID": "7"},
        "sig_bits": {"TCU_FP32_ID": "23", "TCU_TF32_ID": "10", "TCU_FP16_ID": "10",
                      "TCU_BF16_ID": "7", "TCU_FP8_ID": "3", "TCU_BF8_ID": "2"},
        "tcu_fmt_width": {"TCU_FP32_ID": "32", "TCU_TF32_ID": "32", "TCU_FP16_ID": "16",
                           "TCU_BF16_ID": "16", "TCU_FP8_ID": "8", "TCU_BF8_ID": "8"},
    }
    for func_name, vals in func_map.items():
        for fmt_id, val in vals.items():
            content = content.replace(f"VX_tcu_pkg::{func_name}({fmt_id})", val)
            content = content.replace(f"tcu_pkg::{func_name}({fmt_id})", val)
            content = content.replace(f"{func_name}({fmt_id})", val)

    # Backtick-escape bare TCU_*_ID constants (they're `define macros in tcu_synth_defs.vh)
    content = re.sub(r"(?<!\w)(TCU_(?:FP32|TF32|FP16|BF16|FP8|BF8|MXFP8|MXBF8|MXFP4|NVFP4|I32|I8|U8|I4|U4)_ID)(?!\w)",
                     r"`\1", content)

    # Also backtick-escape TCU constant names used as bare identifiers
    content = re.sub(r"(?<!\w)(TCU_(?:NT|NR|NRA|NRB|NRC|EXP_BITS|FMT_WIDTH|TILE_CAP|BLOCK_CAP|TC_[MNK]|M_STEPS|N_STEPS|K_STEPS))(?!\w)",
                     r"`\1", content)

    return content


def main():
    output_lines = []

    # Add synthesis header
    output_lines.append("""// Yosys-compatible TFR flat file (Phase A preprocessed)
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

""")

    seen_modules = set()
    total_gen_scoped = 0

    for modfile in MODULES:
        path = os.path.join(TFR_DIR, modfile)
        if not os.path.exists(path):
            print(f"  SKIP {modfile} (not found)")
            continue

        with open(path) as f:
            content = f.read()

        content = transform(content)

        # Deduplicate modules
        m = re.match(r"module\s+(\w+)", content)
        if m and m.group(1) in seen_modules:
            continue
        if m:
            seen_modules.add(m.group(1))

        # Count gen-scoped
        gen_scoped = 0
        in_gen = False
        depth = 0
        for line in content.split("\n"):
            stripped = line.strip()
            if "for (genvar" in stripped:
                in_gen = True
                depth = 1
            elif in_gen:
                depth += stripped.count("begin") - stripped.count("end")
                if re.match(r"(wire|reg|logic)\s+", stripped):
                    gen_scoped += 1
                if depth <= 0:
                    in_gen = False
        total_gen_scoped += gen_scoped

        output_lines.append(f"// ---- {modfile} ----")
        output_lines.append(content)
        output_lines.append("")

        status = f"  {modfile}: {gen_scoped} gen-scoped" if gen_scoped else f"  {modfile}: clean"
        print(status)

    with open(OUT, "w") as f:
        f.write("\n".join(output_lines))

    print(f"\nFlattened {len(seen_modules)} modules -> {OUT}")
    print(f"  File size: {os.path.getsize(OUT)} bytes")
    print(f"  Generate-scoped declarations: {total_gen_scoped} (Phase B)")


if __name__ == "__main__":
    main()
>>>>>>> Stashed changes
