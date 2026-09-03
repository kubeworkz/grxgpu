#!/usr/bin/env python3
"""Add format utility functions to flat TFR file"""
import re

with open("/tmp/tfr_flat.sv") as f:
    content = f.read()

# Add function definitions before the first module
funcs = """
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

"""

content = content.replace("// ---- VX_tcu_tfr_wmul.sv ----", funcs + "// ---- VX_tcu_tfr_wmul.sv ----")

with open("/tmp/tfr_flat.sv", "w") as f:
    f.write(content)
print("Added format utility functions")
