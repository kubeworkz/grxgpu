#!/usr/bin/env python3
"""
Decompose the GRX G100 16-socket cluster fabric (BB16) into component types.

Yosys `stat` prints per-module "Chip area for module" as the module's OWN
leaf-cell area (submodule instances print "Area ... is unknown!"). To
reproduce the reported top-module area we must scale each module's own-leaf
area by how many times that module is instantiated in the ELABORATED design
(with hierarchy multiplicity):

    mult(M) = (1 if M is top) + SUM over parents P of count(P->M) * mult(P)

    total_design_area = SUM over module types M of own_leaf(M) * mult(M)

This parser solves the multiplicity recursion, verifies the sum reproduces
the reported top-module area, then aggregates by base type name and category.

Usage:
    python3 decompose_fabric.py BB16_RPT BB1_RPT
"""
import re
import sys
from collections import defaultdict

SECTION = re.compile(r"^=== (.+) ===\s*$")
AREA = re.compile(r"^   Chip area for module '(.*)':\s*([0-9.]+)")
CELL = re.compile(r"^     (\S+)\s+(\d+)\s*$")

PARAM_SUFFIX = re.compile(r"(DATAW|OUT_REG|N=|NUM_|ID=|SIZE|ASSOC|SLOTS)")


def base_type(name):
    """Strip $paramod$<hash>\\ prefix and \\-param suffix from a module name."""
    # e.g. $paramod$abc123\VX_stream_buffer\DATAW=s32'...\OUT_REG=1'1
    #      -> VX_stream_buffer
    if "$" in name:
        # drop the $paramod$<hash> prefix (everything before the first backslash)
        name = name.split("\\", 1)[-1]
    if "\\" in name:
        name = name.split("\\")[0]  # drop param suffixes
    return name


def parse(path):
    """Return (modules, top_name, top_area)."""
    modules = {}  # full name -> {"own": area, "cells": {type: count}}
    top_name = None
    top_area = 0.0
    cur = None
    with open(path) as f:
        for line in f:
            m = SECTION.match(line.rstrip())
            if m:
                cur = m.group(1)
                modules.setdefault(cur, {"own": 0.0, "cells": {}})
                continue
            if cur is None:
                continue
            m = AREA.match(line)
            if m:
                area = float(m.group(2))
                modules[cur]["own"] = area
                if cur in ("\\Vortex", "Vortex"):
                    top_name = cur
                    top_area = area
                continue
            m = CELL.match(line)
            if m:
                modules[cur]["cells"][m.group(1)] = int(m.group(2))
    return modules, top_name, top_area


def multiplicity(modules, top_name):
    """Solve mult(M) = top?1:0 + SUM_P count(P->M)*mult(P)."""
    mult = {}
    for _ in range(len(modules) + 1):
        changed = False
        for name in modules:
            if name == top_name:
                val = 1.0
            else:
                val = 0.0
            for parent, pmod in modules.items():
                val += pmod["cells"].get(name, 0) * mult.get(parent, 0.0)
            if abs(val - mult.get(name, 0.0)) > 1e-9:
                mult[name] = val
                changed = True
        if not changed:
            return mult
    raise RuntimeError("multiplicity recursion did not converge")


def attributed(modules, top_name):
    mult = multiplicity(modules, top_name)
    return {name: mod["own"] * mult.get(name, 0.0) for name, mod in modules.items()}, mult


CATS = {
    "L2 cache logic": [
        "VX_l2_cache", "VX_cache_bank", "VX_cache_data", "VX_cache_mshr",
        "VX_cache_tags", "VX_cache_flush", "VX_cache_adapt", "VX_cache",
        "VX_cache_repl",
    ],
    "Crossbar / switch": [
        "VX_stream_xbar", "VX_stream_switch", "VX_stream_omega",
        "VX_transpose", "VX_stream_fork", "VX_stream_buffer",
    ],
    "Arbiters": [
        "VX_stream_arb", "VX_generic_arbiter", "VX_rr_arbiter",
        "VX_priority_arbiter", "VX_arbiter", "VX_arb", "VX_parallel_arbiter",
        "VX_dynamic_arbiter",
    ],
    "Buffers / queues": [
        "VX_elastic_buffer", "VX_pipe_buffer", "VX_pipe_register",
        "VX_fifo_queue", "VX_pending_size", "VX_pending_fifo",
    ],
    "Misc glue": [
        "VX_demux", "VX_bits_insert", "VX_bits_extract", "VX_bits_remove",
        "VX_bits_concat", "VX_popcount", "VX_lzc", "VX_dff",
        "VX_serializer", "VX_find_first", "VX_mem_adapt", "VX_tex_unit",
    ],
    "RAM macros (blackbox)": [
        "VX_dp_ram", "VX_sp_ram", "VX_dp_ram_asic", "VX_sp_ram_asic",
    ],
}
cat_names = list(CATS.keys())


def cat_of(t):
    for c, names in CATS.items():
        if t in names:
            return c
    return "Uncategorized"


def fmt(v):
    return f"{v/1e6:9.3f} mm2"


def summarize(contrib, label):
    print(f"=== {label} by category ===")
    agg = defaultdict(float)
    for name, area in contrib.items():
        if base_type(name) in ("Vortex", "design hierarchy"):
            continue
        agg[cat_of(base_type(name))] += area
    for c in cat_names + ["Uncategorized"]:
        print(f"  {c:26s} {fmt(agg.get(c, 0.0))}")
    print()


def main():
    bb16_path, bb1_path = sys.argv[1], sys.argv[2]
    for path, label in ((bb16_path, "Cluster fabric (BB16)"),
                        (bb1_path, "Per-socket fabric (BB1)")):
        modules, top, top_leaf = parse(path)
        contrib, mult = attributed(modules, top)
        total = sum(contrib.values())
        print(f"{label}: attributed total = {fmt(total)}  "
              f"(reported top recursive {fmt(top_leaf)})")
        summarize(contrib, label)

    m16, t16, _ = parse(bb16_path)
    m1, t1, _ = parse(bb1_path)
    c16, _ = attributed(m16, t16)
    c1, _ = attributed(m1, t1)

    print("=== Shared portion (BB16 - 16*BB1) by category ===")
    a16, a1 = defaultdict(float), defaultdict(float)
    for name, area in c16.items():
        a16[cat_of(base_type(name))] += area
    for name, area in c1.items():
        a1[cat_of(base_type(name))] += area
    for c in cat_names + ["Uncategorized"]:
        v = a16.get(c, 0.0) - 16 * a1.get(c, 0.0)
        if abs(v) > 1000.0:
            print(f"  {c:26s} {fmt(v)}")
    print()

    print("=== Top BB16 base types by attributed area ===")
    by_base = defaultdict(float)
    inst_mult = defaultdict(float)
    for name, area in c16.items():
        if base_type(name) in ("Vortex", "design hierarchy"):
            continue
        by_base[base_type(name)] += area
    for b, area in sorted(by_base.items(), key=lambda kv: -kv[1])[:22]:
        print(f"  {b:24s} {fmt(area)}")


if __name__ == "__main__":
    main()