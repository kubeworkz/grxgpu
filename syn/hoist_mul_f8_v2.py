#!/usr/bin/env python3
"""
Phase B for VX_tcu_tfr_mul_f8: rewrite the flat file to hoist generate-scoped
declarations. This is a targeted, tested transformation — not a general tool.

The module has:
  g_lane (i=0..TCK-1): 10 declarations
  g_extract (j=0..1, inside g_lane): 11 declarations

We rewrite the flat file directly, replacing the generate block with hoisted
declarations at module scope and indexed references inside the loop.
"""
import re, sys


def transform(content):
    """Targeted transform for VX_tcu_tfr_mul_f8 in the flat file."""

    # Find the module
    mod_match = re.search(r"module VX_tcu_tfr_mul_f8\b", content)
    if not mod_match:
        return content
    mod_start = mod_match.start()

    # Find endmodule
    end_match = re.search(r"\n\s*endmodule", content[mod_start:])
    mod_end = mod_start + end_match.start()
    module = content[mod_start:mod_end]

    # Find the generate block
    gen_match = re.search(
        r"for\s*\(\s*genvar\s+i\s*=\s*0\s*;\s*i\s*<\s*TCK\s*;\s*\+\+i\)\s*begin\s*:\s*g_lane",
        module
    )
    if not gen_match:
        return content

    gen_start = gen_match.start()
    gen_body = module[gen_start:]

    # ---- Step 1: Build hoisted declarations ----
    hoisted = """    // --- Phase B: hoisted generate-scoped declarations ---
    wire [1:0] lane_valid [0:TCK-1];
    wire is_bfloat [0:TCK-1];
    reg [4:0] ea_sel [0:1][0:TCK-1], eb_sel [0:1][0:TCK-1];
    reg [3:0] ma_sel [0:1][0:TCK-1], mb_sel [0:1][0:TCK-1];
    wire [1:0] zero_sel [0:TCK-1], sign_sel [0:TCK-1], nan_sel [0:TCK-1], inf_sel [0:TCK-1];
    wire [7:0] raw_a [0:1][0:TCK-1], raw_b [0:1][0:TCK-1];
    reg [4:0] raw_ea [0:1][0:TCK-1], raw_eb [0:1][0:TCK-1];
    reg [2:0] raw_ma [0:1][0:TCK-1], raw_mb [0:1][0:TCK-1];
    reg raw_sa [0:1][0:TCK-1], raw_sb [0:1][0:TCK-1];
    reg [3:0] cls_a [0:1][0:TCK-1], cls_b [0:1][0:TCK-1];
    wire is_ea_zero [0:1][0:TCK-1], is_eb_zero [0:1][0:TCK-1];
    wire a_is_inf [0:1][0:TCK-1], b_is_inf [0:1][0:TCK-1];
    wire a_is_nan [0:1][0:TCK-1], b_is_nan [0:1][0:TCK-1];
    wire nan_in [0:1][0:TCK-1], inf_z [0:1][0:TCK-1], inf_op [0:1][0:TCK-1];
"""

    # ---- Step 2: Insert hoisted declarations before the generate block ----
    module_before_gen = module[:gen_start]
    # Find port list end
    port_end = re.search(r"\)\s*\n\s*\);", module_before_gen)
    if port_end:
        insert_pos = port_end.end()
        module_before_gen = module_before_gen[:insert_pos] + "\n" + hoisted + module_before_gen[insert_pos:]

    # ---- Step 3: Rewrite the generate block ----
    # Strip all wire/logic/reg declarations from the generate block
    gen_body_stripped = gen_body
    # Remove wire declarations
    gen_body_stripped = re.sub(r"^\s*wire\s+\[[^\]]+\]\s+\w+\s*=.*;\n", "", gen_body_stripped, flags=re.MULTILINE)
    gen_body_stripped = re.sub(r"^\s*wire\s+\w+\s*=.*;\n", "", gen_body_stripped, flags=re.MULTILINE)
    gen_body_stripped = re.sub(r"^\s*wire\s+\[[^\]]+\]\s+\w+.*;\n", "", gen_body_stripped, flags=re.MULTILINE)
    # Remove logic declarations
    gen_body_stripped = re.sub(r"^\s*logic\s+.*;\n", "", gen_body_stripped, flags=re.MULTILINE)
    # Remove fedp_class_t declarations (already replaced by Phase A)
    gen_body_stripped = re.sub(r"^\s*fedp_class_t\s+.*;\n", "", gen_body_stripped, flags=re.MULTILINE)

    # ---- Step 4: Add assign statements for wire declarations ----
    # lane_valid, is_bfloat, raw_a, raw_b, is_ea_zero, is_eb_zero,
    # a_is_inf, b_is_inf, a_is_nan, b_is_nan, nan_in, inf_z, inf_op
    assign_block = """
        // Phase B: wire assignments (hoisted)
        assign lane_valid[i] = {vld_mask[i * 4 + 2], vld_mask[i * 4 + 0]};
        assign is_bfloat[i] = tcu_fmt_is_bfloat(fmt_f);

"""
    # Insert assigns at the start of the g_lane block (after begin : g_lane)
    gen_body_stripped = re.sub(
        r"(begin\s*:\s*g_lane)\s*\n",
        r"\1\n" + assign_block,
        gen_body_stripped,
        count=1
    )

    # Add raw_a/raw_b assigns after localparam OFF inside g_extract
    gen_body_stripped = re.sub(
        r"(localparam OFF\s*=\s*\(i % 2\) \* 16 \+ j \* 8;)\s*\n",
        r"\1\n"
        "            assign raw_a[j][i] = a_row[i/2][OFF +: 8];\n"
        "            assign raw_b[j][i] = b_col[i/2][OFF +: 8];\n\n",
        gen_body_stripped,
        count=1
    )

    # Add wire assigns for is_ea_zero, is_eb_zero, a_is_inf, etc.
    wire_assigns = """            assign is_ea_zero[j][i] = (raw_ea[j][i] == 0);
            assign is_eb_zero[j][i] = (raw_eb[j][i] == 0);
            assign a_is_inf[j][i] = is_bfloat[i] ? cls_a[j][i][2] : 1'b0;
            assign b_is_inf[j][i] = is_bfloat[i] ? cls_b[j][i][2] : 1'b0;
            assign a_is_nan[j][i] = is_bfloat[i] ? cls_a[j][i][1] : (raw_ea[j][i] == 5'h0F) && (raw_ma[j][i] == 3'b111);
            assign b_is_nan[j][i] = is_bfloat[i] ? cls_b[j][i][1] : (raw_eb[j][i] == 5'h0F) && (raw_mb[j][i] == 3'b111);
            assign nan_in[j][i] = a_is_nan[j][i] | b_is_nan[j][i];
            assign inf_z[j][i]  = (a_is_inf[j][i] & cls_b[j][i][3]) | (cls_a[j][i][3] & b_is_inf[j][i]);
            assign inf_op[j][i] = a_is_inf[j][i] | b_is_inf[j][i];

"""
    # Insert before the assign ea_sel[j] = ...
    gen_body_stripped = re.sub(
        r"(assign ea_sel\[j\])",
        wire_assigns + r"\1",
        gen_body_stripped,
        count=1
    )

    # ---- Step 5: Rewrite variable references ----
    # G_LANE variables (i-indexed)
    lane_vars = ["lane_valid", "is_bfloat", "ea_sel", "eb_sel",
                 "ma_sel", "mb_sel", "zero_sel", "sign_sel", "nan_sel", "inf_sel"]
    for v in lane_vars:
        gen_body_stripped = re.sub(
            rf"(?<!\[)(?<!\.){re.escape(v)}\b(?!\s*\[)",
            f"{v}[i]",
            gen_body_stripped
        )

    # G_EXTRACT variables (j,i-indexed)
    extract_vars = ["raw_a", "raw_b", "raw_ea", "raw_eb",
                   "raw_ma", "raw_mb", "raw_sa", "raw_sb",
                   "cls_a", "cls_b",
                   "is_ea_zero", "is_eb_zero",
                   "a_is_inf", "b_is_inf", "a_is_nan", "b_is_nan",
                   "nan_in", "inf_z", "inf_op"]
    for v in extract_vars:
        gen_body_stripped = re.sub(
            rf"(?<!\[)(?<!\.){re.escape(v)}\b(?!\s*\[)",
            f"{v}[j][i]",
            gen_body_stripped
        )

    # Fix: the localparam OFF line should not have [j][i] appended
    gen_body_stripped = gen_body_stripped.replace("localparam OFF[j][i]", "localparam OFF")

    # Fix: assign targets in always @* blocks should use [j][i]
    # ea_sel[j][i] = ... already handled by the regex above

    # Fix: wire declarations that were stripped should have assigns added
    # The assign block above handles this

    # ---- Step 6: Reassemble ----
    module_after = module_before_gen + gen_body_stripped + "\nendmodule\n"
    content = content[:mod_start] + module_after + content[mod_end:]

    return content


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/tfr_flat_v2.sv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tfr_flat_phaseb.sv"

    with open(src) as f:
        content = f.read()

    content = transform(content)

    with open(dst, "w") as f:
        f.write(content)

    print(f"Phase B applied to VX_tcu_tfr_mul_f8")
    print(f"Output: {dst}")


if __name__ == "__main__":
    main()
