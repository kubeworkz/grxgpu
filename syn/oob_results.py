#!/usr/bin/env python3
"""Measured DATA_OOB (control-plane-only arbiter) results, Sep 2026.

Standalone (L2 32->2 x 630b, Nangate45, via syn/oob_arb_sweep.sh):
    DATA_OOB=0 (inline 630b through VX_stream_arb): 349,721 um2
    DATA_OOB=1 (54b control + 576b switch):          128,165 um2   (-63.4%)

BB16 16-socket cluster fabric (Yosys, Nangate45, RAM blackboxed):
    baseline flat (MAX_FANOUT=0, inline):            11,428,017 um2
    mem_arb-only OOB (L2 cache mem port arb):         11,428,441 um2   (+0.004%, negligible)
    ALL mem-bus arbs OOB (module default=1):          10,754,733 um2   (-673,285 um2 = -5.89%)
"""
import sys

baseline = 11428017.286005
all_oob = 10754732.716003

print(f"BB16 baseline flat:     {baseline:>13,.0f} um2")
print(f"BB16 all-arbs DATA_OOB: {all_oob:>13,.0f} um2")
print(f"delta: {all_oob-baseline:>+13,.0f} um2 ({(all_oob-baseline)/baseline*100:+.2f}%)")

# What the 5.9% means for the G100
print("\nG100 scaling (8 clusters):")
print(f"  fabric/cluster: {673285:>9,.0f} um2 saved")
print(f"  G100 fabric total @45nm: {673285*8:>12,.0f} um2 = {673285*8/1e6:.2f} mm2")
print(f"  @28nm (x0.39): {673285*8*0.39/1e6:.2f} mm2")

# Arbiter-level breakdown for the doc
print("\nStandalone L2 arb (32->2 x 630b):")
print("  inline: 349,721 um2")
print("  OOB:    128,165 um2  (-63.4%)")