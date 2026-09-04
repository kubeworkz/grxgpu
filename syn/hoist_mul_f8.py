#!/usr/bin/env python3
"""
Phase B: Hoist generate-scoped declarations in VX_tcu_tfr_mul_f8.sv

The module has nested generate blocks:
  g_lane (i=0..TCK-1): lane_valid, is_bfloat, ea_sel/eb_sel, ma_sel/mb_sel,
                         zero_sel, sign_sel, nan_sel, inf_sel, pre_sum_*, etc.
  g_extract (j=0..1, inside g_lane): raw_a, raw_b, raw_ea/eb, raw_ma/mb,
                                      raw_sa/sb, cls_a/b, is_ea_zero, etc.

Strategy:
- Hoist g_lane declarations to module scope (no indexing needed — they're scalars/arrays per-lane)
- Hoist g_extract declarations to module scope with [i][j] indexing
- Rewrite all references
"""
import re, sys


def hoist(content):
    # --- G_LANE declarations to hoist (module scope, per-lane) ---

    # wire [1:0] lane_valid = {vld_mask[i * 4 + 2], vld_mask[i * 4 + 0]};
    # → wire [1:0] lane_valid [0:TCK-1];
    content = content.replace(
        "wire [1:0] lane_valid = {vld_mask[i * 4 + 2], vld_mask[i * 4 + 0]};",
        "wire [1:0] lane_valid [0:TCK-1];"
    )

    # wire is_bfloat = tcu_fmt_is_bfloat(fmt_f);
    # → wire is_bfloat [0:TCK-1];
    content = content.replace(
        "wire is_bfloat = tcu_fmt_is_bfloat(fmt_f);",
        "wire is_bfloat [0:TCK-1];"
    )

    # wire [1:0][4:0] ea_sel, eb_sel;
    # → reg [4:0] ea_sel [0:1][0:TCK-1], eb_sel [0:1][0:TCK-1];
    content = content.replace(
        "wire [1:0][4:0] ea_sel, eb_sel;",
        "reg [4:0] ea_sel [0:1][0:TCK-1], eb_sel [0:1][0:TCK-1];"
    )

    # wire [1:0][3:0] ma_sel, mb_sel;
    content = content.replace(
        "wire [1:0][3:0] ma_sel, mb_sel;",
        "reg [3:0] ma_sel [0:1][0:TCK-1], mb_sel [0:1][0:TCK-1];"
    )

    # wire [1:0]      zero_sel, sign_sel, nan_sel, inf_sel;
    content = content.replace(
        "wire [1:0]      zero_sel, sign_sel, nan_sel, inf_sel;",
        "wire [1:0] zero_sel [0:TCK-1], sign_sel [0:TCK-1], nan_sel [0:TCK-1], inf_sel [0:TCK-1];"
    )

    # --- G_EXTRACT declarations to hoist (module scope, per-lane per-sub) ---

    # wire [7:0] raw_a = a_row[i/2][OFF +: 8];
    content = content.replace(
        "wire [7:0] raw_a = a_row[i/2][OFF +: 8];",
        "wire [7:0] raw_a [0:1][0:TCK-1];"
    )
    content = content.replace(
        "wire [7:0] raw_b = b_col[i/2][OFF +: 8];",
        "wire [7:0] raw_b [0:1][0:TCK-1];"
    )

    # logic [4:0] raw_ea, raw_eb;
    content = content.replace(
        "logic [4:0] raw_ea, raw_eb;",
        "reg [4:0] raw_ea [0:1][0:TCK-1], raw_eb [0:1][0:TCK-1];"
    )

    # logic [2:0] raw_ma, raw_mb;
    content = content.replace(
        "logic [2:0] raw_ma, raw_mb;",
        "reg [2:0] raw_ma [0:1][0:TCK-1], raw_mb [0:1][0:TCK-1];"
    )

    # logic       raw_sa, raw_sb;
    content = content.replace(
        "logic       raw_sa, raw_sb;",
        "reg raw_sa [0:1][0:TCK-1], raw_sb [0:1][0:TCK-1];"
    )

    # fedp_class_t cls_a; / fedp_class_t cls_b;
    content = content.replace(
        "fedp_class_t cls_a;",
        "reg [3:0] cls_a [0:1][0:TCK-1];"
    )
    content = content.replace(
        "fedp_class_t cls_b;",
        "reg [3:0] cls_b [0:1][0:TCK-1];"
    )

    # wire is_ea_zero = (raw_ea == 0);
    content = content.replace(
        "wire is_ea_zero = (raw_ea == 0);",
        "wire is_ea_zero [0:1][0:TCK-1];"
    )
    content = content.replace(
        "wire is_eb_zero = (raw_eb == 0);",
        "wire is_eb_zero [0:1][0:TCK-1];"
    )

    # wire a_is_inf = ...
    content = content.replace(
        "wire a_is_inf = is_bfloat ? cls_a.is_inf : 1'b0;",
        "wire a_is_inf [0:1][0:TCK-1];"
    )
    content = content.replace(
        "wire b_is_inf = is_bfloat ? cls_b.is_inf : 1'b0;",
        "wire b_is_inf [0:1][0:TCK-1];"
    )
    content = content.replace(
        "wire a_is_nan = is_bfloat ? cls_a.is_nan : (raw_ea == 5'h0F) && (raw_ma == 3'b111);",
        "wire a_is_nan [0:1][0:TCK-1];"
    )
    content = content.replace(
        "wire b_is_nan = is_bfloat ? cls_b.is_nan : (raw_eb == 5'h0F) && (raw_mb == 3'b111);",
        "wire b_is_nan [0:1][0:TCK-1];"
    )
    content = content.replace(
        "wire nan_in = a_is_nan | b_is_nan;",
        "wire nan_in [0:1][0:TCK-1];"
    )
    content = content.replace(
        "wire inf_z  = (a_is_inf & cls_b.is_zero) | (cls_a.is_zero & b_is_inf);",
        "wire inf_z [0:1][0:TCK-1];"
    )
    content = content.replace(
        "wire inf_op = a_is_inf | b_is_inf;",
        "wire inf_op [0:1][0:TCK-1];"
    )

    # --- Add assign statements for wire declarations ---

    # Find the generate block and add assigns after variable declarations
    gen_start = re.search(
        r"for\s*\(\s*genvar\s+i\s*=\s*0\s*;\s*i\s*<\s*TCK\s*;\s*\+\+i\)\s*begin\s*:\s*g_lane",
        content
    )
    if gen_start:
        pos = gen_start.start()
        # Find the for(genvar j) inside g_lane
        j_start = re.search(r"for\s*\(\s*genvar\s+j\s*=\s*0", content[pos:])
        if j_start:
            j_pos = pos + j_start.start()
            # Insert assigns before the j loop
            assigns = """
        assign lane_valid[i] = {vld_mask[i * 4 + 2], vld_mask[i * 4 + 0]};
        assign is_bfloat[i] = tcu_fmt_is_bfloat(fmt_f);

"""
            content = content[:j_pos] + assigns + content[j_pos:]

        # Find g_extract block and add assigns for raw_a/raw_b
        extract_start = re.search(r"for\s*\(\s*genvar\s+j\s*=\s*0\s*;\s*j\s*<\s*2\s*;\s*\+\+j\)\s*begin\s*:\s*g_extract", content[pos:])
        if extract_start:
            e_pos = pos + extract_start.start()
            # Find the first wire/logic declaration inside g_extract
            first_decl = re.search(r"wire\s+\[7:0\]\s+raw_a\s*\[", content[e_pos:])
            if first_decl:
                d_pos = e_pos + first_decl.start()
                extract_assigns = """
            localparam OFF = (i % 2) * 16 + j * 8;
            assign raw_a[j][i] = a_row[i/2][OFF +: 8];
            assign raw_b[j][i] = b_col[i/2][OFF +: 8];

"""
                content = content[:d_pos] + extract_assigns + content[d_pos:]

    # --- Rewrite references inside g_lane (i-indexed) ---
    # Find g_lane block boundaries
    g_lane_match = re.search(
        r"for\s*\(\s*genvar\s+i\s*=\s*0\s*;\s*i\s*<\s*TCK\s*;\s*\+\+i\)\s*begin\s*:\s*g_lane",
        content
    )
    if g_lane_match:
        g_start = g_lane_match.start()
        # Find endmodule after g_lane
        end_match = re.search(r"\n\s*endmodule", content[g_start:])
        g_end = g_start + end_match.start()
        g_lane_block = content[g_start:g_end]

        # G_LANE variables (i-indexed only)
        lane_vars = ["lane_valid", "is_bfloat", "ea_sel", "eb_sel",
                     "ma_sel", "mb_sel", "zero_sel", "sign_sel", "nan_sel", "inf_sel"]
        for v in lane_vars:
            g_lane_block = re.sub(
                rf"(?<!\[)(?<!\.){re.escape(v)}\b(?!\s*\[)",
                f"{v}[i]",
                g_lane_block
            )

        # G_EXTRACT variables (i,j-indexed)
        extract_vars = ["raw_a", "raw_b", "raw_ea", "raw_eb",
                       "raw_ma", "raw_mb", "raw_sa", "raw_sb",
                       "cls_a", "cls_b",
                       "is_ea_zero", "is_eb_zero",
                       "a_is_inf", "b_is_inf", "a_is_nan", "b_is_nan",
                       "nan_in", "inf_z", "inf_op"]
        for v in extract_vars:
            g_lane_block = re.sub(
                rf"(?<!\[)(?<!\.){re.escape(v)}\b(?!\s*\[)",
                f"{v}[j][i]",
                g_lane_block
            )

        content = content[:g_start] + g_lane_block + content[g_end:]

    return content


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_f8.sv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "/tmp/VX_tcu_tfr_mul_f8_hoisted.sv"

    with open(src) as f:
        content = f.read()

    content = hoist(content)

    with open(dst, "w") as f:
        f.write(content)

    print(f"Output: {dst}")


if __name__ == "__main__":
    main()
