#!/usr/bin/env python3
"""Compare tree (MAX_FANOUT=8) vs flat (MAX_FANOUT=0) BB16 cluster fabric syntheses."""
import re
import sys

def parse_stat(path):
    txt = open(path).read()
    mods = re.findall(r"Chip area for module '([^']*)': ([0-9.]+)", txt)
    return [(m, float(a)) for m, a in mods]

def summarize(name, pairs, topn=8):
    total = sum(a for _, a in pairs)
    print(f"=== {name}: {len(pairs)} modules, total {total/1e6:.3f} mm^2 ===")
    arbs = [(m, a) for m, a in pairs if 'stream_arb' in m]
    arbs.sort(key=lambda x: -x[1])
    print(f"  stream_arb modules: {len(arbs)}, sum {sum(a for _, a in arbs)/1e6:.3f} mm^2")
    for m, a in arbs[:topn]:
        print(f"    {a/1e6:.4f} mm^2  ...{m[-70:]}")
    return total

if __name__ == '__main__':
    tree_path = sys.argv[1]
    flat_path = sys.argv[2]
    tree = parse_stat(tree_path)
    flat = parse_stat(flat_path)
    t = summarize('TREE (MAX_FANOUT=8)', tree)
    f = summarize('FLAT (MAX_FANOUT=0)', flat)
    print(f"\nCluster fabric total: tree={t/1e6:.3f} mm^2, flat={f/1e6:.3f} mm^2")
    print(f"Delta: {f-t:.0f} um^2 = {(f-t)/t*100:.2f}%")