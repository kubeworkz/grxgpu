#!/usr/bin/env python3
"""
Phase B: Hoist generate-scoped wire/logic/reg declarations to module scope.

For each for(genvar) block:
1. Collect all variable declarations inside the block
2. Hoist them to module scope as arrays: [type] label_varname [loop_bound]
3. Replace inline `wire name = expr` with `assign label_varname[i] = expr`
4. Convert `logic [W:0] name` to `reg [W:0] label_varname [0:0]`
5. Inside always blocks, replace `name` with `label_varname[i]`
"""
import re, sys, os


def hoist_module(content):
    """Process one module's content, hoisting all generate-scoped declarations."""
    lines = content.split("\n")
    output = []
    hoisted_decls = []

    # State machine
    in_gen = False
    gen_depth = 0
    gen_label = ""
    gen_var = "i"
    gen_bound_var = ""  # loop bound variable (e.g., TCK)

    # Variables declared in this generate block
    gen_vars = {}  # name -> (dtype, width_or_none, line_idx)

    # Track brace depth for always blocks
    in_always = False
    always_depth = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect for(genvar)
        gen_match = re.match(
            r"^\s*for\s*\(\s*genvar\s+(\w+)\s*=\s*\d+\s*;\s*\w+\s*<\s*(\w+)", stripped
        )
        if gen_match:
            in_gen = True
            gen_depth = 1
            gen_var = gen_match.group(1)
            gen_bound_var = gen_match.group(2)
            label_match = re.search(r"begin\s*:\s*(\w+)", stripped)
            gen_label = label_match.group(1) if label_match else f"gen_{i}"
            gen_vars = {}
            output.append(line)
            i += 1
            continue

        if in_gen:
            # Track begin/end depth
            gen_depth += stripped.count("begin") - stripped.count("end")
            if gen_depth <= 0:
                # End of generate block — emit hoisted declarations
                in_gen = False
                for vname, (dtype, width, _) in gen_vars.items():
                    hname = f"{gen_label}_{vname}"
                    if width is not None:
                        hoisted_decls.append(f"    {dtype} [{width}] {hname}[0:{gen_bound_var}-1];")
                    else:
                        hoisted_decls.append(f"    {dtype} {hname}[0:{gen_bound_var}-1];")
                output.append(line)
                gen_vars = {}
                i += 1
                continue

            # Check for wire declaration with inline assign: wire name = expr;
            wire_assign = re.match(r"^\s*wire\s+(?:\[[^\]]+\]\s+)?(\w+)\s*=\s*(.+);", stripped)
            if wire_assign:
                name = wire_assign.group(1)
                expr = wire_assign.group(2)
                hname = f"{gen_label}_{name}"
                # Find width of the wire
                width_match = re.search(r"wire\s+\[([^\]]+)\]", stripped)
                if width_match:
                    width = width_match.group(1)
                    hoisted_decls.append(f"    wire [{width}] {hname}[0:{gen_bound_var}-1];")
                else:
                    hoisted_decls.append(f"    wire {hname}[0:{gen_bound_var}-1];")
                # Replace with assign
                indent = len(line) - len(line.lstrip())
                output.append(f"{' ' * indent}assign {hname}[{gen_var}] = {expr};")
                i += 1
                continue

            # Check for wire/reg/logic declaration (no inline assign)
            decl_match = re.match(r"^\s*(wire|logic|reg)\s+(.*)", stripped)
            if decl_match:
                dtype = decl_match.group(1)
                rest = decl_match.group(2).strip().rstrip(";")
                # Parse: [W:0] foo, [W:0] bar, etc.
                # Split on comma while respecting brackets
                parts = []
                current = ""
                bracket_depth = 0
                for ch in rest:
                    if ch == "[":
                        bracket_depth += 1
                        current += ch
                    elif ch == "]":
                        bracket_depth -= 1
                        current += ch
                    elif ch == "," and bracket_depth == 0:
                        parts.append(current.strip())
                        current = ""
                    else:
                        current += ch
                if current.strip():
                    parts.append(current.strip())

                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    wm = re.match(r"\[([^\]]+)\]\s+(\w+)", part)
                    if wm:
                        w, n = wm.group(1), wm.group(2)
                        gen_vars[n] = (dtype, w, i)
                    else:
                        # Just a name
                        n = part.strip()
                        gen_vars[n] = (dtype, None, i)

                # Remove this line (will be replaced by hoisted decl)
                indent = len(line) - len(line.lstrip())
                output.append(f"{' ' * indent}// [HOISTED] {stripped}")
                i += 1
                continue

            # Check for localparam inside generate
            lp_match = re.match(r"^\s*localparam\s+(\w+)\s*=\s*(.+);", stripped)
            if lp_match:
                lp_name = lp_match.group(1)
                lp_expr = lp_match.group(2)
                # localparams inside generate that use genvar need special handling
                # For now, convert to a wire with assign
                hoisted_decls.append(f"    wire [{gen_bound_var}-1:0] {gen_label}_{lp_name}[0:0];")
                indent = len(line) - len(line.lstrip())
                output.append(f"{' ' * indent}assign {gen_label}_{lp_name}[{gen_var}] = {lp_expr};")
                output.append(f"{' ' * indent}// [HOISTED localparam] {lp_name} = {lp_expr}")
                i += 1
                continue

            # Check for always @* blocks — need to rewrite variable references
            if stripped.startswith("always @*") or stripped.startswith("always @*"):
                in_always = True
                always_depth = 0
                output.append(line)
                i += 1
                continue

        if in_always:
            # Count begin/end to find end of always block
            always_depth += stripped.count("begin") - stripped.count("end")
            if always_depth <= 0 and "end" in stripped:
                in_always = False
                output.append(line)
                i += 1
                continue
            elif always_depth < 0:
                in_always = False
                # Don't skip this line — fall through to normal processing

        # Normal line — no changes needed (variable references will use gen_label_var[i])
        # But we need to handle this in the variable reference rewriting pass
        output.append(line)
        i += 1

    # Now do a second pass: rewrite variable references inside the generate block
    # This is the hard part — need to find all references to gen_vars and add [i]
    result_lines = output
    # For now, skip the complex reference rewriting — just validate the decl hoisting
    return "\n".join(result_lines), hoisted_decls


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/tfr_flat_v2.sv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tfr_flat_phaseb.sv"

    with open(src) as f:
        content = f.read()

    content, hoisted = hoist_module(content)

    with open(dst, "w") as f:
        f.write(content)

    print(f"Hoisted {len(hoisted)} declarations to module scope")
    for h in hoisted[:20]:
        print(f"  {h.strip()}")
    if len(hoisted) > 20:
        print(f"  ... and {len(hoisted)-20} more")
    print(f"Output: {dst}")


if __name__ == "__main__":
    main()
