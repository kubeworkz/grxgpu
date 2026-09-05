#!/usr/bin/env python3
"""L2 request bus composition and control-plane-only arbiter savings.

Traced from the BB16 synthesis (Nangate45):
  - VX_mem_bus_arb REQ_DATAW = 1 + ADDR_WIDTH + DATA_WIDTH + DATA_SIZE + ATTR_WIDTH + TAG_WIDTH
  - Resolved: ADDR_WIDTH=26, DATA_WIDTH=512 (8*64B line), DATA_SIZE=64 (byteen),
    ATTR_WIDTH=17 (MEM_ATTR_WIDTH), TAG_WIDTH=10 (L1_MEM_ARB_TAG_WIDTH)
  - REQ_DATAW = 630 bits; the L2 arb is 32 inputs (2*L2_SOCKET_REQS) x 630b.
  - The 155K um2 cluster arb is this L2 arb in fanout-tree form (16:1 x 1260b
    was the decoded slice pair; the flat 32:1 x 630b shape is the real one).

Bus fields (req_data_t packed):
    rw      : 1 bit
    addr    : ADDR_WIDTH = 26 bits
    data    : DATA_WIDTH = 512 bits  (write payload)
    byteen  : DATA_SIZE  = 64 bits   (write byte enables)
    attr    : ATTR_WIDTH = 17 bits   (amo + flags)
    tag     : TAG_WIDTH  = 10 bits
    TOTAL   : 630 bits

Control plane = everything the arbiter needs to route/prioritize:
    rw + addr + attr + tag = 1 + 26 + 17 + 10 = 54 bits
Data plane (write-only) = data + byteen = 512 + 64 = 576 bits
"""

rw = 1
addr = 26
data = 512
byteen = 64
attr = 17
tag = 10
total = rw + addr + data + byteen + attr + tag

print("=== L2 request bus composition (630 bits) ===")
print(f"{'field':<10} {'bits':>5} {'pct':>7}")
for name, w in [("rw", rw), ("addr", addr), ("data", data), ("byteen", byteen), ("attr", attr), ("tag", tag)]:
    print(f"{name:<10} {w:>5} {w/total*100:>6.1f}%")
print(f"{'TOTAL':<10} {total:>5}")

ctrl = rw + addr + attr + tag
dplane = data + byteen
print(f"\n=== Plane split ===")
print(f"control plane (rw+addr+attr+tag): {ctrl} bits ({ctrl/total*100:.1f}%)")
print(f"data plane    (data+byteen):      {dplane} bits ({dplane/total*100:.1f}%)")

# Measured arbiter areas from the DW=512 sweep (flat, RR):
# per-in-per-bit ~= 1.70 um2 at 32:1 (measured 27,778 um2 / 32 / 512)
# But at 630b the L2 arb is 32:1 x 630: area ~= 32 * 630 * 1.70 um2 (linear width)
per_in_per_bit_32 = 27777.848 / 32 / 512  # 1.695 um2/in/bit at 32:1 from measured p32
a_full = 32 * total * per_in_per_bit_32
a_ctrl = 32 * ctrl * per_in_per_bit_32
a_data_byteen_off = 32 * (data + byteen) * per_in_per_bit_32

print(f"\n=== Estimated arbiter area at 32:1 (measured per-in-per-bit {per_in_per_bit_32:.3f} um2) ===")
print(f"full 630b arb:        {a_full:>10,.0f} um2")
print(f"control-only 54b arb: {a_ctrl:>10,.0f} um2   ({a_ctrl/a_full*100:.1f}%)")
print(f"data+byteen plane:    {a_data_byteen_off:>10,.0f} um2  ({a_data_byteen_off/a_full*100:.1f}%)")

# Real measured reference: the flat BB16 run had the L2 arb paramods
# efc31b1 (0.377 mm2) and dad84d3a (0.323 mm2) -- those are the 32:1 x 630b
# and 16:1 x 630b shapes in flat form. Use efc31b1 as the L2 arb ground truth.
a_full_meas = 376900  # flat BB16 stat: $paramod$efc31b1... VX_stream_arb
print(f"\n=== Measured L2 arb in flat BB16 ===")
print(f"32:1 x 630b flat arb (efc31b1): {a_full_meas:,.0f} um2")
print(f"control-only estimate at that scale: {a_full_meas*ctrl/total:,.0f} um2")
print(f"savings: {a_full_meas*(1-ctrl/total):,.0f} um2 = {(1-ctrl/total)*100:.1f}% of the L2 arb")
print(f"note: write-data plane must still exist SOMEWHERE (bank write path),")
print(f"but it moves out of the arbitration network: the arb decision only")
print(f"needs valid/ready + priority, not the 576b write payload.")