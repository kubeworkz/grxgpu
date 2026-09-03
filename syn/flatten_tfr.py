#!/usr/bin/env python3
"""
Flatten TFR modules into a single Yosys-compatible Verilog file.
Replaces package imports with define macros and literal constants.
"""
import re, sys, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/grxgpu"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tfr_flat.sv"

# TFR module files
TFR_DIR = os.path.join(ROOT, "hw/rtl/tcu/tfr")
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

# Package constant mapping (from tcu_pkg + gpu_pkg with G100 config)
CONSTANTS = {
    "TCU_FP32_ID": "0", "TCU_TF32_ID": "1", "TCU_FP16_ID": "2", "TCU_BF16_ID": "3",
    "TCU_FP8_ID": "4", "TCU_BF8_ID": "5", "TCU_MXFP8_ID": "8", "TCU_MXBF8_ID": "9",
    "TCU_MXFP4_ID": "10", "TCU_NVFP4_ID": "11",
    "TCU_I32_ID": "16", "TCU_I8_ID": "17", "TCU_U8_ID": "18",
    "TCU_I4_ID": "19", "TCU_U4_ID": "20",
    "TCU_FMT_WIDTH": "5",
    "TCU_NT": "4", "TCU_NR": "32", "TCU_NRA": "4", "TCU_DK": "0", "TCU_DP": "0",
    "TCU_TILE_CAP": "128", "TCU_LG_TILE_CAP": "7",
    "TCU_TILE_EN": "3", "TCU_TILE_EM": "4",
    "TCU_TILE_M": "16", "TCU_TILE_N": "8", "TCU_TILE_K": "8",
    "TCU_BLOCK_CAP": "4", "TCU_LG_BLOCK_CAP": "2",
    "TCU_BLOCK_EN": "1", "TCU_BLOCK_EM": "1",
    "TCU_TC_M": "2", "TCU_TC_N": "2", "TCU_TC_K": "2",
    "TCU_M_STEPS": "8", "TCU_N_STEPS": "4", "TCU_K_STEPS": "4",
    "TCU_WG_TILE_M": "4", "TCU_WG_TILE_K": "4",
    "TCU_WG_FEDP_K": "2", "TCU_WG_TILE_N": "32",
    "TCU_WG_M_STEPS": "2", "TCU_WG_N_STEPS": "16", "TCU_WG_K_STEPS": "2",
    "TCU_WG_UOPS": "64",
    "TCU_NRB": "16", "TCU_NRC": "32",
    "TCU_EXP_BITS": "10",
    "TCU_MX_MAX_SF": "1",
    "TCU_MIN_FMT_WIDTH": "4", "TCU_MAX_ELT_RATIO": "8",
    "TCU_MAX_META_ROW_WIDTH": "64", "TCU_MAX_META_BLOCK_WIDTH": "256",
}

# $bits() replacements
BITS_REPLACEMENTS = {
    "fedp_excep_t": "3",
    "fedp_class_t": "4",
}

# VX_tcu_pkg:: function replacements (exp_bits, sign_pos, tcu_fmt_width)
FUNC_MAP = {
    "TCU_FP32_ID": {"exp": "8", "sig": "23", "sign": "31", "width": "32"},
    "TCU_TF32_ID": {"exp": "8", "sig": "10", "sign": "18", "width": "32"},
    "TCU_FP16_ID": {"exp": "5", "sig": "10", "sign": "15", "width": "16"},
    "TCU_BF16_ID": {"exp": "8", "sig": "7", "sign": "15", "width": "16"},
    "TCU_FP8_ID":  {"exp": "4", "sig": "3", "sign": "7", "width": "8"},
    "TCU_BF8_ID":  {"exp": "5", "sig": "2", "sign": "7", "width": "8"},
}

def resolve_func_call(expr):
    """Resolve VX_tcu_pkg::func_name(TCU_XXX_ID) calls"""
    for func_name, id_map in [
        ("exp_bits", {k: v["exp"] for k, v in FUNC_MAP.items()}),
        ("sig_bits", {k: v["sig"] for k, v in FUNC_MAP.items()}),
        ("sign_pos", {k: v["sign"] for k, v in FUNC_MAP.items()}),
        ("tcu_fmt_width", {k: v["width"] for k, v in FUNC_MAP.items()}),
    ]:
        for fmt_id, val in id_map.items():
            pattern = f"VX_tcu_pkg::{func_name}({fmt_id})"
            expr = expr.replace(pattern, val)
            # Also handle bare references
            pattern2 = f"tcu_pkg::{func_name}({fmt_id})"
            expr = expr.replace(pattern2, val)
    return expr

def preprocess(content):
    """Make a single TFR module Yosys-compatible"""
    # Remove include directives
    content = re.sub(r'`include\s+"[^"]*"', '', content)

    # Remove package imports
    content = re.sub(r'import\s+VX_tcu_pkg::\*;', '', content)
    content = re.sub(r'import\s+TCU_synth_pkg::\*;', '', content)
    content = re.sub(r'import\s+VX_gpu_pkg::\*;', '', content)

    # Replace $bits()
    for type_name, bits in BITS_REPLACEMENTS.items():
        content = content.replace(f"$bits({type_name})", bits)

    # Replace remaining $bits with 32
    content = re.sub(r"\$bits\(\w+\)", "32", content)

    # Replace VX_tcu_pkg:: function calls
    content = resolve_func_call(content)

    # Replace VX_CFG_* defines with concrete values where they are used as
    # standalone identifiers (not inside `ifdef/`ifndef/`define)
    content = re.sub(r"`VX_CFG_NUM_THREADS", "4", content)
    content = re.sub(r"`VX_CFG_NUM_WARPS", "4", content)
    content = re.sub(r"`VX_CFG_NUM_TCU_LANES", "4", content)

    # Remove SIMULATION-only blocks
    content = re.sub(r"`ifdef\s+SIMULATION.*?`endif[^\n]*\n", "", content, flags=re.DOTALL)

    # Remove TRACE macros
    content = re.sub(r"`TRACE\([^)]*\)", "/* trace */", content)

    # Remove UNUSED macros
    content = re.sub(r"`IGNORE_UNUSED_BEGIN", "", content)
    content = re.sub(r"`IGNORE_UNUSED_END", "", content)

    # Strip function automatic blocks (multi-line)
    content = re.sub(r"function automatic\b.*?endfunction\n?", "", content, flags=re.DOTALL)

    # Strip task blocks
    content = re.sub(r"task\b.*?endtask\n?", "", content, flags=re.DOTALL)

    return content

# Main
output_lines = []

# Add define header
output_lines.append("// TFR flat file — Yosys synthesis for GRXGPU G100")
output_lines.append("// Auto-generated by flatten_tfr.py")
output_lines.append("")

for modfile in MODULES:
    path = os.path.join(TFR_DIR, modfile)
    if not os.path.exists(path):
        print(f"  SKIP {modfile} (not found)")
        continue
    with open(path) as f:
        content = f.read()
    content = preprocess(content)
    output_lines.append(f"// ---- {modfile} ----")
    output_lines.append(content)
    output_lines.append("")

with open(OUT, "w") as f:
    f.write("\n".join(output_lines))

print(f"Flattened {len(MODULES)} TFR modules -> {OUT}")
print(f"  Output: {os.path.getsize(OUT)} bytes")
