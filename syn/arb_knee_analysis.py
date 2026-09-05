#!/usr/bin/env python3
"""Port-count knee analysis for VX_stream_arb at DW=512 (Nangate45).

Measured areas (flat, RR, 1 output) from the DW=512 sweep, plus the
measured L2-shape ladder and the decoded cluster arbiter shapes.
"""
import sys

# measured: (NI, area_um2) at DW=512, flat, RR
measured_512 = [
    (2, 974.092),
    (4, 2921.212),
    (8, 6796.832),
    (16, 14018.998),
    (24, 20076.350),
    (32, 27777.848),
    (64, 56869.736),
]

print("=== DW=512 port sweep (measured, flat, RR) ===")
print(f"{'NI':>4} {'area um2':>12} {'per-input':>10} {'per-in-per-bit':>14}")
for ni, a in measured_512:
    print(f"{ni:>4} {a:>12,.0f} {a/ni:>10,.0f} {a/ni/512:>14.3f}")

print()
print("=== Knee conclusion ===")
print("per-input-per-bit is flat ~1.63-1.74 from 8:1 to 64:1 => port")
print("scaling is LINEAR at DW=512; the data mux dominates and the")
print("16-port superlinear step seen at DW=64 (1.9->4.0 per-in-per-bit)")
print("is a grant-logic artifact that vanishes at wide data. NO knee to")
print("exploit at the port level.")

print()
print("=== Measured L2-shape ladder (DW=512, NUM_REQS=2 per output) ===")
l2 = [
    ("4->2", 1936.480, "2 outputs x 2:1"),
    ("8->4", 3852.744, "4 outputs x 2:1"),
    ("16->8", 7687.666, "8 outputs x 2:1"),
    ("32->16", 15355.914, "16 outputs x 2:1"),
]
for name, a, desc in l2:
    print(f"{name:<8} {a:>10,.0f} um2  ({desc})")

print()
print("=== L2 32->16 topology recommendation ===")
flat32 = 27777.848   # monolithic 32:1
l2_32x16 = 15355.914 # 16 parallel 2:1 (NUM_REQS=2, current)
print(f"monolithic 32:1:          {flat32:,.0f} um2")
print(f"16 parallel 2:1 (current): {l2_32x16:,.0f} um2")
print(f"already -45% vs monolithic: the L2 is NOT a 32:1; it is")
print(f"NUM_REQS=2 (each output muxes 2 inputs). Splitting into")
print(f"2x16->8 (NUM_REQS=2 each) would keep per-output fan-in at 2 and")
print(f"halve the crossbar per half (7687x2 = 15,374) - no gain, same math.")
print(f"The real lever at fixed NUM_REQS=2 is DATAW: the largest cluster")
print(f"arb is 8:1 x 1260b (155K um2) - narrowing the request payload")
print(f"(e.g. route data outside arbitration) beats any topology change.")

# sanity check: what does 1260-bit width cost at 8:1?
est_1260 = 6796.832 * 1260 / 512  # linear width scaling at fixed ports
print()
print(f"8:1 x 1260b (measured in cluster, est from 8:1 x 512b): {est_1260:,.0f} um2")
print("(cluster 155K um2 instance includes OUT_BUF=3 elastic slices)")