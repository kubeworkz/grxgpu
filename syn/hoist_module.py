#!/usr/bin/env python3
"""
General Phase B hoisting: moves generate-scoped declarations to module scope.
Handles nested generate blocks (g_lane → g_extract) with multi-dimensional indexing.

Usage: python3 hoist_module.py MODULE_NAME FLAT_FILE [OUTPUT_FILE]
"""
import re, sys, os

MODULE = sys.argv[1] if len(sys.argv) > 1 else "VX_tcu_tfr_mul_f8"
SRC = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tfr_flat_v2.sv"
DST = sys.argv[3] if len(sys.argv) > 3 else "/tmp/tfr_flat_phaseb.sv"


def find_module_bounds(content, module_name):
    """Find start and end positions of a module in the flat file."""
    pattern = rf"module\s+{re.escape(module_name)}\b"
    m = re.search(pattern, content)
    if not m:
        return None, None
    start = m.start()
    # Find matching endmodule
    end = re.search(r"\n\s*endmodule", content[start:])
    if not end:
        return None, None
    return start, start + end.end()


def collect_gen_blocks(module_content):
    """
    Collect all for(genvar) blocks in a module, tracking nesting depth.
    Returns list of (gen_var, bound_var, label, start_offset, end_offset, parent_label).
    """
    blocks = []
    # Find all for(genvar) lines
    for m in re.finditer(r"for\s*\(\s*genvar\s+(\w+)\s*=\s*\d+\s*;\s*\w+\s*<\s*(\w+)", module_content):
        var = m.group(1)
        bound = m.group(2)
        # Find the begin label
        rest = module_content[m.start():]
        label_m = re.search(r"begin\s*:\s*(\w+)", rest)
        label = label_m.group(1) if label_m else f"gen_{m.start()}"
        # Find matching end
        depth = 0
        pos = rest.find("begin")
        for j in range(pos, len(rest)):
            if rest[j:j+5] == "begin":
                depth += 1
            elif rest[j:j+3] == "end" and (j+3 >= len(rest) or not rest[j+3].isalnum()):
                depth -= 1
                if depth == 0:
                    blocks.append((var, bound, label, m.start(), m.start() + j + 3, None))
                    break
    # Determine parent-child relationships based on position
    for i, b in enumerate(blocks):
        for j, p in enumerate(blocks):
            if i != j and b[3] > p[3] and b[4] < p[4]:
                blocks[i] = (*b[:5], p[2])
                break
    return blocks


def collect_declarations(module_content, block):
    """Collect all wire/logic/reg declarations inside a generate block."""
    gen_var, bound, label, start, end, parent = block
    block_content = module_content[start:end]
    decls = []

    for m in re.finditer(r"^\s*(wire|logic|reg)\s+(.*?)\s*;", block_content, re.MULTILINE):
        dtype = m.group(1)
        rest = m.group(2).strip()
        # Parse: [W:0] name, name2, etc.
        parts = []
        current = ""
        bd = 0
        for ch in rest:
            if ch == "[":
                bd += 1
                current += ch
            elif ch == "]":
                bd -= 1
                current += ch
            elif ch == "," and bd == 0:
                parts.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            parts.append(current.strip())
        for part in parts:
            wm = re.match(r"\[([^\]]+)\]\s+(\w+)", part)
            if wm:
                width, name = wm.group(1), wm.group(2)
                decls.append((dtype, name, width, label, parent))
            else:
                name = part.strip()
                decls.append((dtype, name, None, label, parent))
    return decls


def hoist_module(content, module_name):
    """Hoist all generate-scoped declarations in one module."""
    mod_start, mod_end = find_module_bounds(content, module_name)
    if mod_start is None:
        print(f"  WARNING: module {module_name} not found")
        return content, []

    module_body = content[mod_start:mod_end]

    # Collect all generate blocks
    blocks = collect_gen_blocks(module_body)
    if not blocks:
        return content, []

    # Collect declarations from all blocks
    all_decls = []
    for block in blocks:
        all_decls.extend(collect_declarations(module_body, block))

    # Find port list end for insertion point
    port_end = re.search(r"\)\s*\n\s*\);", module_body)
    if not port_end:
        return content, []

    insert_pos = mod_start + port_end.end()

    # Generate hoisted declarations
    hoisted_lines = []
    for dtype, name, width, label, parent in all_decls:
        # Build the full indexed name
        if parent:
            hname = f"{parent}_{label}_{name}"
            # Find bound for parent and label
            parent_block = next((b for b in blocks if b[2] == parent), None)
            label_block = next((b for b in blocks if b[2] == label), None)
            if parent_block and label_block:
                hoisted_lines.append(
                    f"    {dtype} {'[' + width + '] ' if width else ''}{hname}"
                    f"[0:{parent_block[1]}-1][0:{label_block[1]}-1];"
                )
            else:
                hoisted_lines.append(f"    {dtype} {'[' + width + '] ' if width else ''}{hname}[0:0][0:0];")
        else:
            hname = f"{label}_{name}"
            label_block = next((b for b in blocks if b[2] == label), None)
            if label_block:
                hoisted_lines.append(
                    f"    {dtype} {'[' + width + '] ' if width else ''}{hname}"
                    f"[0:{label_block[1]}-1];"
                )
            else:
                hoisted_lines.append(f"    {dtype} {'[' + width + '] ' if width else ''}{hname}[0:0];")

    # Insert hoisted declarations
    hoisted_block = "\n".join(hoisted_lines) + "\n"
    content = content[:insert_pos] + "\n" + hoisted_block + content[insert_pos:]

    # Now rewrite references inside the module
    mod_start2, mod_end2 = find_module_bounds(content, module_name)
    module_body = content[mod_start2:mod_end2]

    for dtype, name, width, label, parent in all_decls:
        if parent:
            old_name = name
            new_name = f"{parent}_{label}_{name}"
            parent_block = next((b for b in blocks if b[2] == parent), None)
            label_block = next((b for b in blocks if b[2] == label), None)
            if parent_block and label_block:
                parent_var = parent_block[0]  # genvar name
                label_var = label_block[0]
                # Replace references — but not in declarations or already-indexed
                module_body = re.sub(
                    rf"(?<!\[)(?<!\.){re.escape(old_name)}\b(?!\s*\[)",
                    f"{new_name}[{parent_var}][{label_var}]",
                    module_body
                )
        else:
            old_name = name
            new_name = f"{label}_{name}"
            label_block = next((b for b in blocks if b[2] == label), None)
            if label_block:
                label_var = label_block[0]
                module_body = re.sub(
                    rf"(?<!\[)(?<!\.){re.escape(old_name)}\b(?!\s*\[)",
                    f"{new_name}[{label_var}]",
                    module_body
                )

    content = content[:mod_start2] + module_body + content[mod_end2:]

    return content, all_decls


def main():
    with open(SRC) as f:
        content = f.read()

    content, decls = hoist_module(content, MODULE)

    with open(DST, "w") as f:
        f.write(content)

    print(f"Module {MODULE}: {len(decls)} declarations hoisted")
    for dtype, name, width, label, parent in decls[:30]:
        prefix = f"{parent}_" if parent else ""
        print(f"  {dtype} {'[' + width + '] ' if width else ''}{prefix}{label}_{name}")
    if len(decls) > 30:
        print(f"  ... and {len(decls)-30} more")
    print(f"Output: {DST}")


if __name__ == "__main__":
    main()
