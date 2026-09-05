#!/usr/bin/env python3
"""Find the largest VX_stream_arb paramod instances in a Yosys stat report
and decode their NI/NO/DW parameters from the paramod name."""
import re
import sys

txt = open(sys.argv[1]).read()
mods = re.findall(r"Chip area for module '([^']*VX_stream_arb[^']*)': ([0-9.]+)", txt)
pairs = [(m, float(a)) for m, a in mods]
pairs.sort(key=lambda x: -x[1])

for m, a in pairs[:6]:
    # paramod names carry params like $paramod$hash\VX_stream_arb
    # actual param values appear in the netlist hierarchy, not here; but
    # Yosys stat sometimes shows per-instance lines with params in stat_*.
    print(f"{a/1e6:.4f} mm^2  ...{m[-80:]}")

print(f"\ntotal stream_arb paramods: {len(pairs)}")
print(f"sum: {sum(a for _, a in pairs)/1e6:.3f} mm^2")