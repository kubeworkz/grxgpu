#!/usr/bin/env python3
"""Generate a VX_core stub that matches the current VX_core module signature
(including all ifdef-gated ports) but with an empty body, for source-level
blackbox area synthesis of the cluster fabric."""
import re
import sys

src = sys.argv[1] if len(sys.argv) > 1 else "hw/rtl/core/VX_core.sv"
out = sys.argv[2] if len(sys.argv) > 2 else "syn/VX_core_stub.sv"

txt = open(src, encoding="utf-8", errors="replace").read()

# Find the module header: from "module VX_core" to the port-list terminator ");"
m = re.search(r"(module\s+VX_core.*?\)\s*;)", txt, re.S)
if not m:
    print("ERROR: could not find module VX_core header")
    sys.exit(1)

header = m.group(1)

stub = f"""// Stub VX_core for source-level blackbox area synthesis (auto-generated
// from hw/rtl/core/VX_core.sv by syn/gen_core_stub.py).
// Same module signature as the real core (all ifdef-gated ports preserved);
// body replaced with constant ties so sv2v inlines an empty cell and the
// core logic contributes zero area. Used to measure cluster fabric
// (L1/L2/arbiters/interconnect) without synthesizing N inlined cores.

{header}

    assign busy = 1'b0;
endmodule
"""

# Keep any `include lines from the original so the header resolves.
includes = "\n".join(l for l in txt.splitlines() if l.strip().startswith("`include"))
if includes and "`include" not in stub:
    stub = includes + "\n\n" + stub

open(out, "w", encoding="utf-8").write(stub)
print(f"wrote {out} ({len(stub.splitlines())} lines)")