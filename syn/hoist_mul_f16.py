#!/usr/bin/env python3
"""
Phase B pilot: Hoist generate-scoped declarations in VX_tcu_tfr_mul_f16.sv

Variables declared inside for(genvar i) are hoisted to module scope as arrays,
and all references inside the loop body are rewritten with [i] indexing.
"""
import re, sys


def hoist_mul_f16(content):
    gen_var = "i"
    gen_bound = "TCK"

    # --- Step 1: Hoist declarations to module scope ---

    # Wire with inline assign
    content = content.replace(
        "wire lane_valid = vld_mask[i*4];",
        "wire lane_valid[TCK-1:0];"
    )

    # Logic declarations → reg arrays at module scope
    replacements = [
        ("logic [7:0] raw_ea, raw_eb;", "reg [7:0] raw_ea[0:TCK-1], raw_eb[0:TCK-1];"),
        ("logic [9:0] raw_ma, raw_mb;", "reg [9:0] raw_ma[0:TCK-1], raw_mb[0:TCK-1];"),
        ("logic       raw_sa, raw_sb;", "reg raw_sa[0:TCK-1], raw_sb[0:TCK-1];"),
        ("logic [7:0] bias_sel;", "reg [7:0] bias_sel[0:TCK-1];"),
        ("logic [3:0] cls_a_f16;", "reg [3:0] cls_a_f16[0:TCK-1];"),
        ("logic [3:0] cls_b_f16;", "reg [3:0] cls_b_f16[0:TCK-1];"),
        ("logic [3:0] cls_a_wide;", "reg [3:0] cls_a_wide[0:TCK-1];"),
        ("logic [3:0] cls_b_wide;", "reg [3:0] cls_b_wide[0:TCK-1];"),
        ("logic [3:0] cls_a;", "reg [3:0] cls_a[0:TCK-1];"),
        ("logic [3:0] cls_b;", "reg [3:0] cls_b[0:TCK-1];"),
    ]
    for old, new in replacements:
        content = content.replace(old, new)

    # --- Step 2: Rewrite references inside the generate block ---
    # Find the generate block boundaries
    gen_match = re.search(
        r"for\s*\(\s*genvar\s+i\s*=\s*0\s*;\s*i\s*<\s*TCK\s*;\s*\+\+i\)\s*begin\s*:\s*g_lane",
        content
    )
    if not gen_match:
        print("WARNING: generate block not found")
        return content

    gen_start = gen_match.start()

    # Find endmodule after the generate block
    endmodule_match = re.search(r"\n\s*endmodule", content[gen_start:])
    if not endmodule_match:
        return content

    gen_end = gen_start + endmodule_match.start()
    gen_block = content[gen_start:gen_end]

    # Variables that need [i] appended (only the 14 hoisted ones)
    hoisted_names = [
        "lane_valid", "raw_ea", "raw_eb", "raw_ma", "raw_mb",
        "raw_sa", "raw_sb", "bias_sel",
        "cls_a_f16", "cls_b_f16", "cls_a_wide", "cls_b_wide",
        "cls_a", "cls_b",
    ]

    for name in hoisted_names:
        # Replace variable references, but NOT:
        # 1. Already-indexed: name[i] or name[something]
        # 2. In module instantiation port connections: .name(...)
        # 3. In the wire/reg declaration line (already handled)
        # 4. The assignment target on the left side of = (already has [i])
        gen_block = re.sub(
            rf"(?<!\[)(?<!\.){re.escape(name)}\b(?!\s*\[)",
            f"{name}[{gen_var}]",
            gen_block
        )

    content = content[:gen_start] + gen_block + content[gen_end:]

    return content


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/tfr_flat_v2.sv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tfr_flat_phaseb.sv"

    with open(src) as f:
        content = f.read()

    content = hoist_mul_f16(content)

    with open(dst, "w") as f:
        f.write(content)

    print(f"Phase B applied to VX_tcu_tfr_mul_f16")
    print(f"Output: {dst}")


if __name__ == "__main__":
    main()
