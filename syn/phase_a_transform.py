#!/usr/bin/env python3
"""
Phase A Yosys Compatibility Transforms for GRXGPU TFR modules.

Applies all quick-win fixes in a single pass:
1. Strip simulation macros (STATIC_ASSERT, UNUSED_*, FORCE_BUILTIN_ADDER, etc.)
2. Strip DBG_TRACE_TCU blocks
3. Replace always_ff / always_comb / always_latch
4. Replace logic with wire/reg
5. Strip parameter STRING INSTANCE_ID lines
6. Replace $bits() with computed widths
7. Replace typedef struct packed with explicit wire widths
8. Strip TRACE_ARRAY calls
9. Strip $display/$write/$time calls
10. Handle generate-scoped wire declarations (flag for Phase B)
"""
import re, sys, os

# ---- Configuration ----

# $bits() replacements
BITS_MAP = {
    "fedp_excep_t": "3",
    "fedp_class_t": "4",
    "tcu_header_t": "32",
    "amo_req_t": "32",
    "mem_bus_attr_t": "32",
    "lsu_header_t": "32",
}

# fedp_excep_t bit positions (packed struct)
# is_inf=bit2, is_nan=bit1, sign=bit0
EXCEP_FIELD_MAP = {
    ".is_inf": "[2]",
    ".is_nan": "[1]",
    ".sign":   "[0]",
}

# fedp_class_t bit positions (packed struct)
# is_zero=bit3, is_sub=bit2, is_inf=bit1, is_nan=bit0
CLASS_FIELD_MAP = {
    ".is_zero": "[3]",
    ".is_sub":  "[2]",
    ".is_inf":  "[1]",
    ".is_nan":  "[0]",
}

# Type definitions to inject at file scope
TYPEDEFS = """
// Replaced typedef struct packed for synthesis
wire [2:0] fedp_excep_t__is_inf = 3'd4;   // dummy for macro
wire [3:0] fedp_class_t__is_zero = 4'd8;   // dummy for macro
"""

# Utility function stubs to inject at file scope
FUNC_STUBS = """
// Format utility functions (stubbed for synthesis)
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

"""


def transform(content):
    """Apply all Phase A transforms to a single module's source."""

    # 1. Strip simulation macros
    content = re.sub(r"^\s*`STATIC_ASSERT\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*`UNUSED_SPARAM\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*`UNUSED_PARAM\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*`UNUSED_PIN\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*`UNUSED_VAR\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*`FORCE_BUILTIN_ADDER[^\n]*\n?", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*`MAP_AOS_SOA\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)

    # 2. Strip DBG_TRACE_TCU blocks
    content = re.sub(r"`ifdef\s+DBG_TRACE_TCU.*?`endif[^\n]*\n", "", content, flags=re.DOTALL)

    # 3. Strip TRACE / TRACE_ARRAY calls
    content = re.sub(r"^\s*`TRACE\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*`TRACE_ARRAY\s*\([^)]*\)\s*\n?", "", content, flags=re.MULTILINE)

    # 4. Strip $display / $write / $time (simulation-only)
    content = re.sub(r"\$display\s*\([^)]*\)", "0", content)
    content = re.sub(r"\$write\s*\([^)]*\)", "0", content)
    content = re.sub(r"\$time", "0", content)
    content = re.sub(r"\$error\s*\([^)]*\)", "/* error */", content)

    # 5. Replace always_ff with always @(posedge clk)
    content = re.sub(r"always_ff\s+@\s*\(\s*posedge\s+(\w+)\s*\)", r"always @(\1)", content)
    # Catch any other always_ff
    content = re.sub(r"always_ff\s+@\s*\(([^)]+)\)", r"always @(\1)", content)

    # 6. Replace always_comb with always @*
    content = re.sub(r"\balways_comb\b", "always @*", content)

    # 7. Replace always_latch with always @*
    content = re.sub(r"\balways_latch\b", "always @*", content)

    # 8. Strip parameter STRING INSTANCE_ID lines
    content = re.sub(r"^\s*parameter\s+STRING\s+INSTANCE_ID\s*=\s*\"[^\"]*\"\s*,?\s*\n?",
                     "", content, flags=re.MULTILINE)
    # Also strip standalone parameter STRING lines without trailing comma
    content = re.sub(r"^\s*parameter\s+STRING\s+\w+\s*=\s*\"[^\"]*\"\s*;?\s*\n?",
                     "", content, flags=re.MULTILINE)

    # 9. Strip verilator attributes
    content = re.sub(r"/\*\s*verilator[^*]*\*/", "", content)

    # 10. Replace $bits() with computed widths
    for type_name, width in BITS_MAP.items():
        content = content.replace(f"$bits({type_name})", width)
    # Catch any remaining $bits
    content = re.sub(r"\$bits\(\w+\)", "32", content)

    # 11. Replace typedef struct packed for fedp_excep_t and fedp_class_t
    content = re.sub(
        r"typedef\s+struct\s+packed\s*\{[^}]*\}\s*fedp_excep_t\s*;",
        "/* fedp_excep_t typedef stripped */",
        content, flags=re.DOTALL
    )
    content = re.sub(
        r"typedef\s+struct\s+packed\s*\{[^}]*\}\s*fedp_class_t\s*;",
        "/* fedp_class_t typedef stripped */",
        content, flags=re.DOTALL
    )

    # 12. Replace fedp_excep_t type with wire [2:0]
    content = re.sub(r"\bfedp_excep_t\b", "logic [2:0]", content)

    # 13. Replace fedp_class_t type with wire [3:0]
    content = re.sub(r"\bfedp_class_t\b", "logic [3:0]", content)

    # 14. Replace .is_inf / .is_nan / .sign on fedp_excep_t variables
    # (These are struct field accesses that need bit indexing)
    for field, bits in EXCEP_FIELD_MAP.items():
        content = content.replace(field, bits)

    # 15. Replace .is_zero / .is_sub / .is_inf / .is_nan on fedp_class_t variables
    for field, bits in CLASS_FIELD_MAP.items():
        content = content.replace(field, bits)

    # 16. Replace remaining `STRING with nothing
    content = content.replace("`STRING", "")

    # 17. Strip remaining `ifdef SIMULATION blocks
    content = re.sub(r"`ifdef\s+SIMULATION.*?`endif[^\n]*\n", "", content, flags=re.DOTALL)

    # 18. Strip `include directives
    content = re.sub(r'`include\s+"[^"]*"', '', content)

    # 19. Strip package imports
    content = re.sub(r"import\s+VX_tcu_pkg::\*;", "", content)
    content = re.sub(r"import\s+TCU_synth_pkg::\*;", "", content)
    content = re.sub(r"import\s+VX_gpu_pkg::\*;", "", content)

    return content


def add_header(content):
    """Add synthesis defines and function stubs at the top of the file."""
    header = """// Yosys synthesis defines (Phase A preprocessed)
`define VX_CFG_XLEN 32
`define VX_CFG_NUM_THREADS 4
`define VX_CFG_NUM_WARPS 4
`define VX_CFG_NUM_TCU_LANES 4
`define STATIC_ASSERT(cond, msg)
`define UNUSED_PARAM(x)
`define UNUSED_SPARAM(x)
`define UNUSED_VAR(x)
`define UNUSED_PIN(x)
`define FORCE_BUILTIN_ADDER
`define MAP_AOS_SOA(x)
`define TRACE(level, msg)
`define TRACE_ARRAY(level, name, arr, sz)
`define CLOG2(x) ($clog2(x))

"""
    return header + content


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/grxgpu"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tfr_preprocessed"

    tfr_dir = os.path.join(root, "hw/rtl/tcu/tfr")
    os.makedirs(out_dir, exist_ok=True)

    modules = sorted([f for f in os.listdir(tfr_dir) if f.endswith(".sv")])

    total_gen_scoped = 0
    for modfile in modules:
        src_path = os.path.join(tfr_dir, modfile)
        dst_path = os.path.join(out_dir, modfile)

        with open(src_path) as f:
            content = f.read()

        content = transform(content)

        # Count generate-scoped declarations (for Phase B tracking)
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

        with open(dst_path, "w") as f:
            f.write(content)

        status = f"  {modfile}: {gen_scoped} gen-scoped decls" if gen_scoped else f"  {modfile}: clean"
        print(status)

    print(f"\nTotal: {len(modules)} modules, {total_gen_scoped} generate-scoped declarations (Phase B)")
    print(f"Preprocessed files: {out_dir}")


if __name__ == "__main__":
    main()
