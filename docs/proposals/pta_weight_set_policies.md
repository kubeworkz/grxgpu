# Weight-Set Scheduling for a Cluster-Scope Analog Tile — The Three Policies, Priced

**Status:** Proposal — study only. No RTL, no SimX changes requested yet; this
asks for a SimX run and names what it has to settle.
**Scope:** `sim/simx/kmu/`, `sim/simx/cta_dispatcher.cpp` (read, not changed).
Nothing here patches grxgpu.
**Baseline:** 4096³ SGEMM, 128×128 CTA tile, BK=32, G100 default config
(8 clusters × 16 cores), modelled against the c930's measured shot floor and
bank-select cost.
**Origin:** GRXCP step G1 (`docs/designs/pta_program_plan.md`), the first GPU
deliverable of `docs/designs/pta_gpu_integration.md` §7. The model is
`docs/designs/pta_gpu_sched.py` in GRXCP, standard library only.
**Related:** [grxgpu_tensor_engine.md](grxgpu_tensor_engine.md) — whose measured
100% `b_only` gate stall is the same problem in digital form.

---

## 1. What this asks, and why it comes before any hardware

A weight-stationary analog tile breaks a SIMT machine's founding assumption. Any
resident warp may run at any time only while every warp sees the same functional
units; a photonic tile says *only work whose weight set is currently programmed
may run, and changing it costs `Tw`*. That is a resource with an enormous,
warp-visible switching cost, which the G100 has never had, and a scheduler that
round-robins across CTAs with different weight sets will thrash it.

GRXCP's GPU integration document gives three answers and says the interesting work
is choosing between them with numbers:

1. **Affinity.** The CTA dispatcher binds CTAs sharing a B tile to one cluster and
   issues them contiguously.
2. **A mesh cache.** `W` weight banks per tile, LRU, so `W` weight sets are hot.
   The c930's existing structure is `W = 2`.
3. **Software-declared, hardware-enforced.** The kernel names its weight slot in
   the launch descriptor; a mismatch serialises on the tile's own lock.

**This is worth settling before the engine exists**, because the three differ in
what they ask of your repo: policy 1 is a runtime choice, policy 2 is tile area,
policy 3 is an ABI commitment. Getting the order wrong costs a build.

**Why it connects to work you have already measured.**
[grxgpu_tensor_engine.md](grxgpu_tensor_engine.md) found that the TCU itself never
waits and every WGMMA group waits on the B tile — 100% `b_only` gate stall, with
the conclusion that operand delivery is the entire problem. A weight-stationary
tile is that observation taken to its conclusion: keep B still and move A past it.
So the question below is not exotic. It is your B-delivery problem with the
delivery cost made explicit and schedulable.

---

## 2. What the G100 already has

Read out of this repo rather than assumed, because it changes what policy 1 costs.

**`cluster_dim` is already a run-time CTA grouping.** `sim/simx/kmu/kmu.cpp`
walks the grid as a nested tiling: `cluster_dim` is a 3-D tile of the grid, filled
by `intra_offset` before `group_origin` advances in (X, Y, Z) order, and it is
settable through `VX_DCR_KMU_CLUSTER_DIM_X/Y/Z`. GRXCP's document calls policy 1
"cheapest in hardware, requires the runtime to expose the weight set as a dispatch
attribute". **The attribute exists.** What is missing is a runtime that chooses it
with the weight set in mind.

**The handout is demand-driven, not round-robin.** There is one `Kmu` per
processor (`cta_dispatcher.cpp`: `core->socket()->cluster()->processor()->kmu()`)
and every core's dispatcher pulls from it when it has a free slot. So which CTAs a
given cluster sees is whatever 16 cores' progress makes it. The model below
assumes an even interleave; that is the first thing SimX would correct.

**A CTA cluster is bounded by LMEM co-residency.** `usable_slots()` caps the
reserved run at `lmem_capacity / stride` and at `num_warps`, and
`is_first_of_cluster` reserves that many *consecutive* slots on **one core**. So
`cluster_dim` cannot express an arbitrarily deep grouping, which matters because
the grouping policy 1 needs is as deep as the GEMM's M dimension in CTA tiles — 32
for the baseline here.

---

## 3. The model

A tile holds one `R × C` weight set, so a GEMM's weight sets are the `(kr, nc)`
blocks of B and there are `(K/R)·(N/C)` of them. A shot pushes one A row through
and costs `PTA_TS + 2`, the floor GRX930's C2 gate measured. The three policies
differ **only in the order the tile sees those weight sets**, so the shot term is
identical across them and what is priced is the weight movement. That is why this
can be a model rather than a simulation: the quantity in question is a property of
the reference stream.

**Two costs, not one.** A reference to the set the tile is already driving is
free. A reference to one of the other `W−1` resident banks is a **select** and
costs the settle alone — GRX930 measured that at one cycle. A reference to a set
that is not resident is a **load** and costs the scan as well: `R·C` beats at one
element per beat, which is a DXA `dest_kmajor` transfer and the same serial
discipline the c930's weight scan chain has. Counting these together makes banks
look useless; counting them apart is what makes `W` worth sweeping.

**The fact that drives everything.** The grid is (n-blocks, m-blocks) and a CTA
loops `k` inside, so **the weight set changes within a CTA, not between CTAs.** At
an 8×8 tile with BK=32 and BN=128, one `k` step is 4 weight sets down K and 16
across N, and a CTA touches 8192 of them in sequence. The stream a tile sees is
cyclic with that period, and a cyclic stream is the textbook LRU pathology.

---

## 4. The answer

Baseline: 4096³, 128×128 CTA tile, BK=32, 8 clusters, 8×8 tile. One cluster's
stream is 1,048,576 references over a period of 8192.

| `W` | natural sel/load | affinity sel/load | declared sel/load |
|---|---|---|---|
| 1 | 0 / 1,048,576 | 0 / 1,048,576 | 0 / 32,768 |
| 2 | 0 / 1,048,576 | 0 / 1,048,576 | 0 / 32,768 |
| 4 | 0 / 1,048,576 | 0 / 1,048,576 | 0 / 32,768 |
| 4096 | 0 / 1,048,576 | 0 / 1,048,576 | 0 / 32,768 |
| **8192** | 0 / 1,048,576 | 1,015,808 / **32,768** | 0 / 32,768 |
| 16384 | 0 / 1,048,576 | 1,015,808 / 32,768 | 0 / 32,768 |

**1. The null result is real, and narrower than GRXCP's document expected.** At
every `W` below the period, affinity is **bit-identical** to the natural order —
same selects, same loads, at `W` = 1, 2, 4, 16, 4096. Not close: identical,
because the cycling is intra-CTA and re-ordering CTAs cannot touch it. The period
is **8192 banks** at the 8×8 tile, so every buildable `W` is in that regime, the
c930's `W = 2` included.

**2. Affinity does help, but only at that capacity.** At `W` = 8192 its loads fall
32×, the row blocks sharing a B tile. Below it, nothing. So affinity and the cache
are **not alternatives on one axis**: each is worthless without the other. The
natural order gets nothing even at twice the period, because a cluster sees CTAs
from several n blocks and its working set is a multiple of the cycle however many
banks there are.

**3. The declared policy reaches affinity's best load count with one bank, and
pays no selects at all.** This is the result. Naming the slot is what lets the `k`
loop be hoisted **above** the grid — one launch per weight set, every A row
streamed through it — and that is where the 32× comes from, not from the
scheduler. It is also the only one of the three that needs no hardware and no
dispatcher change.

**4. What it is worth end to end, one cluster:**

| point | `Tw` | natural, `W`=2 | declared, `W`=1 | speedup |
|---|---|---|---|---|
| TO-1ms | 100,000 | 105,864,232,960 | 4,218,421,248 | **25.1×** |
| TO-10us | 1,000 | 2,055,208,960 | 974,389,248 | **2.11×** |
| EO-scan | 0 (scan only) | 469,762,048 | 404,750,336 | 1.16× |
| EO-res | 1 | 470,810,624 | 404,783,104 | 1.16× |

The 32× is the load reduction; end to end the shot term it cannot touch takes
over. **The GPU's weight-set scheduling problem is a thermo-optic problem** — worth
25× on a 1 ms tile and 16% on a Pockels one. That is the same ordering GRXCP's CPU
cost model gives, for the same reason: once `Tw` is small, weight movement stops
being the term that matters.

---

## 5. What SimX has to settle

Three things the model assumes, each of which SimX already has the machinery for:

1. **That a cluster sees every 8th CTA in grid order.** The KMU is one per
   processor and cores pull on demand, so the real split is whatever progress
   makes it. This is the assumption most likely to be wrong and the easiest to
   check — instrument the weight-set id per CTA admission and histogram it per
   cluster.
2. **That affinity can route a whole n column to one cluster.** The mechanism is
   `cluster_dim`, but `usable_slots()` bounds a CTA cluster by LMEM co-residency
   and warp slots, so a column of 32 row blocks may not fit one. **Affinity is
   modelled at its theoretical best above and still loses**, so this bound only
   strengthens reading 3 — but the achievable grouping depth is worth knowing.
3. **That LMEM port contention does not reorder the stream.** SimX models the
   DXA(0)/TCU(1) priority arbiter and this model does not. A third client at the
   same arbiter is what a tile would be.

**What a SimX run would add that a model cannot:** the serialisation cost of
policy 3 when a kernel declares the wrong slot, which is the policy's failure mode
and the only part of it this model does not price.

---

## 6. What we recommend

**Implement policy 3 first, and treat policies 1 and 2 as refinements that need
each other.** Concretely:

- The launch descriptor gains a weight-slot field, and the tile serialises on a
  mismatch. No dispatcher change, no bank array, and the cost is visible to the
  programmer rather than hidden — which for a research vehicle is the right trade,
  and now has a number behind it.
- **Do not build banks for affinity's sake.** At buildable `W` the banks buy
  nothing the declared policy does not already buy, and the capacity that would
  make affinity pay is 8192 sets at the emulated geometry.
- Keep `W = 2` for double-buffering a load behind a shot, which is a different
  argument from the one above and not priced here.

**What this does not settle:** whether a GEMM engine is the right home for a
photonic tile at all. GRXCP holds that behind its own phase C2, and nothing here
changes that staging — G1 was unblocked precisely because it needs no RTL and
shares no IP.

**Reviewers:** this is a GRXCP study handed over for your judgement, under the
one-directional dependency in GRXCP's `AGENTS.md` §2. The model is
`docs/designs/pta_gpu_sched.py` there, runs in a few seconds on the standard
library, and carries its claims as asserts — including the one that caught the
first version of reading 1, which said affinity never helps.
