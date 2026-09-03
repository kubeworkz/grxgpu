#!/usr/bin/env python3
"""
Phase B v3: Properly handle nested generate blocks with recursive finding.
"""
import re, sys, os


def find_all_gen_blocks(content, start, end):
    """Recursively find all for(genvar) blocks in content[start:end]."""
    blocks = []
    pos = start
    while pos < end:
        m = re.search(
            r"for\s*\(\s*genvar\s+(\w+)\s*=\s*\d+\s*;\s*\w+\s*<\s*(\w+)\s*;\s*\+\+\w+\)\s*begin\s*:\s*(\w+)",
            content[pos:end]
        )
        if not m:
            break
        var = m.group(1)
        bound = m.group(2)
        label = m.group(3)
        block_start = pos + m.start()
        # Find matching end (brace counting)
        depth = 0
        block_end = -1
        for i in range(pos + m.end(), end):
            if content[i:i+5] == "begin":
                depth += 1
            elif content[i:i+3] == "end" and (i+3 >= len(content) or not content[i+3].isalnum()):
                depth -= 1
                if depth == 0:
                    block_end = i + 3
                    break
        if block_end > 0:
            blocks.append((var, bound, label, block_start, block_end))
            # Recurse into this block to find nested blocks
            nested = find_all_gen_blocks(content, pos + m.end(), block_end)
            blocks.extend(nested)
            pos = block_end
        else:
            break
    return blocks


def collect_decls_in_block(content, block):
    """Collect wire/logic/reg declarations inside a generate block."""
    var, bound, label, start, end = block
    block_content = content[start:end]
    decls = []

    # Wire with inline assign
    for m in re.finditer(r"^\s*wire\s+(?:\[[^\]]+\]\s+)?(\w+)\s*=\s*(.+);", block_content, re.MULTILINE):
        name = m.group(1)
        expr = m.group(2).rstrip(";").rstrip()
        width_m = re.search(r"wire\s+\[([^\]]+)\]", m.group(0))
        width = width_m.group(1) if width_m else None
        decls.append(("wire_assign", name, width, expr))

    # Wire with range and names: wire [1:0][4:0] ea_sel, eb_sel;
    for m in re.finditer(r"^\s*wire\s+(\[[^\]]+\](?:\[[^\]]+\])*)\s+([\w\s,]+);", block_content, re.MULTILINE):
        width = m.group(1)
        names = [n.strip() for n in m.group(2).split(",") if n.strip()]
        for name in names:
            if not any(d[1] == name for d in decls):
                decls.append(("wire_decl", name, width, None))

    # Logic declarations
    for m in re.finditer(r"^\s*logic\s+(?:\[([^\]]+)\]\s+)?([\w\s,]+);", block_content, re.MULTILINE):
        width = m.group(1)
        names = [n.strip() for n in m.group(2).split(",") if n.strip()]
        for name in names:
            if not any(d[1] == name for d in decls):
                decls.append(("logic", name, width, None))

    # fedp_class_t
    for m in re.finditer(r"^\s*fedp_class_t\s+(\w+)\s*;", block_content, re.MULTILINE):
        name = m.group(1)
        if not any(d[1] == name for d in decls):
            decls.append(("logic", name, "3:0", None))

    # fedp_excep_t
    for m in re.finditer(r"^\s*fedp_excep_t\s+(\w+)\s*;", block_content, re.MULTILINE):
        name = m.group(1)
        if not any(d[1] == name for d in decls):
            decls.append(("logic", name, "2:0", None))

    return decls


def hoist_module(content, module_name):
    """Hoist all generate-scoped declarations in a module."""
    mod_match = re.search(rf"module\s+{re.escape(module_name)}\b", content)
    if not mod_match:
        return content, 0

    mod_start = mod_match.start()
    end_match = re.search(r"\n\s*endmodule", content[mod_start:])
    mod_end = mod_start + end_match.start()

    # Find port list end — must appear BEFORE the first for(genvar) or localparam
    first_gen = re.search(r"for\s*\(\s*genvar", content[mod_start:mod_end])
    first_lp = re.search(r"localparam", content[mod_start:mod_end])
    search_end = mod_end
    if first_gen:
        search_end = min(search_end, mod_start + first_gen.start())
    if first_lp:
        search_end = min(search_end, mod_start + first_lp.start())
    # Try to find the port list end: ) followed by ; or just ) on its own line
    port_end = re.search(r"\)\s*\n\s*\);", content[mod_start:search_end])
    if not port_end:
        # Try alternate format: ) followed by newline (new-style SV)
        port_end = re.search(r"\)\s*\n", content[mod_start:search_end])
    if not port_end:
        return content, 0
    insert_pos = mod_start + port_end.end()

    # Find all generate blocks recursively
    blocks = find_all_gen_blocks(content, mod_start, mod_end)
    if not blocks:
        return content, 0

    # Process blocks innermost-first (so outer blocks can reference hoisted names)
    # Sort by block length (shortest = innermost)
    blocks.sort(key=lambda b: b[4] - b[3])

    all_hoisted = []
    processed_vars = set()  # Track which variables we've already hoisted

    for var, bound, label, b_start, b_end in blocks:
        block_content = content[b_start:b_end]
        decls = collect_decls_in_block(content, (var, bound, label, b_start, b_end))

        if not decls:
            continue

        # Determine the indexing suffix for this block
        # For nested blocks, we need [outer_var][inner_var]
        # Find parent blocks that contain this one
        parents = []
        for pv, pb, pl, ps, pe in blocks:
            if ps < b_start and pe > b_end and pl != label:
                parents.append((pv, pl))

        # Build hoisted declarations
        for dtype, name, width, expr in decls:
            if name in processed_vars:
                continue
            processed_vars.add(name)

            hname = f"{label}_{name}"
            dtype_str = dtype.replace("wire_assign", "wire").replace("wire_decl", "wire").replace("logic", "reg")

            if width:
                all_hoisted.append(f"    {dtype_str} [{width}] {hname} [0:{bound}-1];")
            else:
                all_hoisted.append(f"    {dtype_str} {hname} [0:{bound}-1];")

        # Replace declarations in the block
        new_block = block_content
        for dtype, name, width, expr in decls:
            hname = f"{label}_{name}"
            if dtype == "wire_assign":
                old = re.search(rf"wire\s+(?:\[[^\]]+\]\s+)?{re.escape(name)}\s*=\s*.+;", new_block)
                if old:
                    clean_expr = expr.rstrip(";").rstrip()
                    new_block = new_block[:old.start()] + f"    assign {hname}[{var}] = {clean_expr};" + new_block[old.end():]
            else:
                pattern = rf"^\s*(?:wire|logic|reg|fedp_class_t|fedp_excep_t)\s+(?:\[[^\]]+\](?:\[[^\]]+\])*\s+)?{re.escape(name)}.*;\s*\n"
                new_block = re.sub(pattern, "", new_block, count=1)

        # Rewrite variable references in this block
        hoisted_names = [d[1] for d in decls if d[1] not in processed_vars or True]
        for name in [d[1] for d in decls]:
            hname = f"{label}_{name}"
            # Replace standalone references (not inside identifiers or already indexed)
            new_block = re.sub(
                rf"(?<![a-zA-Z0-9_]){re.escape(name)}(?![a-zA-Z0-9_\[])",
                f"{hname}[{var}]",
                new_block
            )

        content = content[:b_start] + new_block + content[b_end:]

    # Insert hoisted declarations
    if all_hoisted:
        hoisted_block = "\n".join(all_hoisted) + "\n"
        content = content[:insert_pos] + "\n    // Phase B: hoisted generate-scoped declarations\n" + hoisted_block + content[insert_pos:]

    return content, len(all_hoisted)


def main():
    tfr_dir = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/grxgpu/hw/rtl/tcu/tfr"

    modules = [
        "VX_tcu_tfr_mul_f16.sv",
        "VX_tcu_tfr_mul_f8.sv",
        "VX_tcu_tfr_mul_f4.sv",
        "VX_tcu_tfr_mul_i8.sv",
        "VX_tcu_tfr_mul_i4.sv",
        "VX_tcu_tfr_align.sv",
        "VX_tcu_tfr_max_exp.sv",
        "VX_tcu_tfr_acc.sv",
    ]

    total = 0
    for modfile in modules:
        path = os.path.join(tfr_dir, modfile)
        if not os.path.exists(path):
            print(f"  SKIP {modfile}")
            continue

        with open(path) as f:
            content = f.read()

        module_name = modfile.replace(".sv", "")
        content, count = hoist_module(content, module_name)

        if count > 0:
            with open(path, "w") as f:
                f.write(content)
            print(f"  {modfile}: {count} declarations hoisted")
            total += count
        else:
            print(f"  {modfile}: clean")

    print(f"\nTotal: {total} declarations hoisted")


if __name__ == "__main__":
    main()
