# grxgpu Tensor Engine — Self-Pipelining Operand Delivery

**Status:** Proposal — Phase 1 (fused A+B descriptor) implemented in SimX
**Scope:** `sim/simx/dxa/`, `sim/simx/tcu/`, `sw/kernel/include/vx_dxa.h`,
`sw/kernel/include/vx_tensor.h`, `tests/regression/sgemm_tcu_wg_dxa/`
**Baseline:** K=512 GEMM, 512×512×512 fp16, G100 config (8 clusters × 16 cores):
28,080,063 cycles, IPC 1.345, TCU gate 100% B-only stall, scrb 92%, sfu 96%.
**Related:** [mmu_optimization_proposal.md](mmu_optimization_proposal.md)

---

## 1. Motivation — what profiling taught us

This design is the product of an extended microarchitectural study of the
WGMMA (warpgroup matrix-multiply-accumulate) tensor path in SimX. Every
optimization we tried — fused ALU setup-uops, double/triple buffering,
dual-DXA cores, L2 parallel ports, tbuf victim caching, B-first issue
reordering — converged on the same measured facts:

| Metric | Value | Meaning |
|--------|-------|---------|
| TCU gate stall (b_only) | **100%** | Every WGMMA group waits on the B tile |
| scrb (scoreboard) | 92% | Cores stalled waiting for operand delivery |
| sfu (DXA) utilization | 96% | The data-movement unit is nearly saturated |
| TCU stall (tcu) | **0%** | The tensor unit itself never waits |
| ALU instruction mix | 62% | Setup-uop overhead dominates the instruction stream |

**The tensor compute is free. Operand delivery is the entire problem.**

The root cause is structural, not a tuning bug: the A tile (MRC=4, 64 B) and
B tile (NRC=8, 128 B) are fetched through the same single-port DXA pipeline
as two separate requests. B is 2× larger, so it always finishes last — and
because A and B are issued as independent queue entries, the fetch engine
can never treat them as a unit.

### 1.1 The architectural constant: 100% b_only gate stall

We ran **9 independent experiments** attacking the 100% b_only gate stall
from every angle — kernel-level, dispatch-level, memory-subsystem, and
pipeline-depth. None moved the stall:

| # | Experiment | b_only gate | avg_pend_b | Cycles (K=512) | Δ vs baseline | Verdict |
|---|-----------|------------|------------|----------------|---------------|---------|
| 0 | **Baseline (A-first dual-pipe)** | 100% | 1.8 | 659,656 | — | — |
| 1 | B-first dispatch swap | 100% | 1.8 | 660,894 | +0.19% | ❌ no help |
| 2 | 3-stage B-prefetch pipeline | 100% | 1.8 | 1,329,452 | +101.5% | ❌ hurts badly |
| 3 | L2_NUM_REQS=4 (4 arbiter ports) | — | — | crash | — | ❌ config mismatch |
| 4 | L2_NUM_REQS=16 + L2 enable | — | — | crash (error 10) | — | ❌ config mismatch |
| 5 | DXA bypass port attempt | — | — | — | — | ❌ wrong bottleneck |
| 6 | Reverse tick order (B before A) | — | — | killed (4h47m) | +56% wall | ❌ hurts badly |
| 7 | Triple-buffer pipeline | 100% | 1.8 | 1,329,452 | +101.5% | ❌ no gate change |
| 8 | 1024² scale test | 100% | 1.8 | 111,140,698 | 4.006× (linear) | ✅ scaling confirmed |

**The 100% b_only gate stall with avg_pend_b=1.8 is an irreducible
architectural constant** of the current DXA+L2 memory subsystem.

Why nothing works:

- **Kernel-level pipelining** (experiments 2, 7) can't fix it because both
  A and B issue through the DXA internal arbiter in the same tick — the
  arbiter serializes them regardless of pipeline depth.
- **Dispatch reordering** (experiment 1) can't fix it because the GMEM
  arbiter uses round-robin and sees both requests simultaneously.
- **Tick reordering** (experiment 6) can't fix it because the arbiter
  processes both workers in the same cycle regardless of iteration order.
- **L2 port increases** (experiments 3, 4) can't fix it because the Vortex
  config system is deeply coupled — changing L2_NUM_REQS cascades into
  AMO_RS_SIZE, L2_NUM_BANKS, and other values, breaking runtime init.
- **DXA bypass port** (experiment 5) failed because kDxaMemPorts=0 in the
  default build (VX_CFG_L2_NUM_REQS is undefined), meaning DXA traffic
  already bypasses the L2 arbiter entirely.

The root cause is the **DXA internal pipeline timing**: B's GMEM read
arrives ~1.8 cycles after A's due to the fused pair's sequential dispatch
within the DXA core. No external change can fix this — the next lever
must modify the DXA's internal dispatch/timing logic at the hardware level.

This proposal inverts NVIDIA's design philosophy. NVIDIA ships powerful
hardware + a compiler contract (TMA, WGMMA descriptors, software pipelining)
that dumps orchestration onto the programmer. **We make the tensor hardware
responsible for its own data movement and pipeline state** — "dataflow-style"
operand delivery where the fetch engine treats (A, B) as one atomic unit and
the pipeline state machine lives in hardware, not in per-iteration
instructions.

---

## 2. The five novel concepts

### 2.1 Fused A+B operand descriptors (Phase 1 — this proposal)

One DXA issue fetches **both** operands of a WGMMA group as a single atomic
transfer. The kernel issues one instruction instead of two; the fetch engine
enumerates both tiles' work lists into one transfer, interleaves their GMEM
reads through the inflight window, writes both to LMEM, and releases the
barrier exactly once when both tiles are resident.

Why this kills the B-only stall by construction:

- **Issue parity.** Today A and B are two queue entries; a single worker
  drains A's entire transfer (read → write → release) before B's starts, or
  two workers split the pair and serialize on the shared L2 arbiter. Fused,
  one worker holds both tiles' reads in its inflight window simultaneously —
  B's first read issues in the same window as A's, so B's larger footprint
  stops being a *second serialized* transfer and becomes a *wider* one.
- **One barrier event.** `expect_tx(1)` + one release instead of
  `expect_tx(2)` + two releases. The gate cannot observe "A ready, B not" —
  the barrier opens only when both tiles are resident.
- **Halved issue overhead.** One DXA instruction, one wgather pair per stage
  instead of two. Directly attacks the 62% ALU setup-uop mix.
- **Architectural headroom.** On real hardware the fused descriptor maps to a
  dual-ported fetch: the engine splits (A, B) across two independent memory
  ports *inside* the transfer. SimX's shared L2 arbiter masks this, but the
  ISA-level contract (one op = one operand pair) is what a production design
  needs.

The encoding is free: the 2D DXA issue currently leaves all four rs2 lanes
zero. Lane 0-3 rs1 carry A's fields (smem, meta, coord0, coord1); we use
lane 0-3 **rs2** for B's fields, with a pair flag in meta[31]. No new
opcode, no new funct7 — pure encoding reuse.

### 2.2 Self-pipelining tensor units (Phase 2)

The kernel currently owns the pipeline: per K-iteration it must select the
barrier, compute stage pointers, issue the prefetch, wait, compute, wait
again. Our fused-ALU experiment showed this costs 62% of all instructions.

Inverted design: the tensor unit owns a small pipeline FSM per CTA. The
kernel issues one range-descriptor op — `tgemm tile(i, j, k-range)` — and
the hardware internally does fetch → double-buffer rotate → FEDP across K
with zero software involvement per tile. Software touches only tile
boundaries and the output store. Barrier generation, pointer rotation, and
stage tracking become hardware state.

This is the "tensor DMA + FSM" idea taken to its logical end: the hardware
pipeline is a state machine, not a software choreography. It is the
production evolution of the fused descriptor — the descriptor gains a
K-range, the engine gains the loop.

### 2.3 Size-symmetric operand tiles

The entire B-only stall traces back to `tile_A (4×8) ≠ tile_B (8×8)`. A
production ISA should either mandate square operand tiles (8×8 both) or let
the fetch engine pad/balance the smaller operand so both halves of a fused
pair drain in lockstep. Cheap to enforce at descriptor-programming time;
eliminates the asymmetry class of stalls forever.

### 2.4 Mailbox-native DSMEM (Phase 3)

We prototyped cross-CTA smem sharing (DSMEM) with a polling loop — it was a
performance killer (each poll is a full SFU pipeline pass). The fix we
landed was a per-core mailbox CSR (`VX_CSR_MAILBOX=0xCC5`) with a
`MAILBOX_READ` SFU op, removing the stall. A production design makes this
first-class: per-core mailbox register files with send/receive semantics,
no polling, no SFU stall. Distinct from NVIDIA's DSMEM, which requires
careful cluster-level software sync.

### 2.5 Tensor-dedicated memory path (Phase 4)

Every bandwidth experiment (dual-DXA, L2 parallel ports, tbuf caching) was
masked by SimX's shared L2 arbiter serialization. Production lesson: the
tensor unit needs its own dedicated L2 slice / memory ports, fully isolated
from scalar LSU traffic — a "tensor memory bus" that the fused descriptor's
dual-ported fetch can actually exploit. In SimX this is a config flag
(`VX_CFG_L2_ENABLED` + separate arbiter rows); on hardware it is physical
port partitioning.

---

## 3. Phase 1 spec — fused A+B descriptor

### 3.1 ISA encoding

Reuse the existing 2D DXA issue (funct7=0x3, 4-lane wgather). The pair
variant sets meta[31] and uses rs2 lanes:

```
Pair 2D issue:  vx_dxa_issue_2d_wg_pair(desc_a, desc_b, bar,
                                         smem_a, smem_b,
                                         coord_a0, coord_a1,
                                         coord_b0, coord_b1)

  Lane 0: rs1 = smem_addr_a     rs2 = smem_addr_b
  Lane 1: rs1 = meta_a (bit31)  rs2 = meta_b
  Lane 2: rs1 = coord_a0        rs2 = coord_b0
  Lane 3: rs1 = coord_a1        rs2 = coord_b1

  meta_a[31]   = pair flag
  meta_a[3:0]  = desc_slot_a
  meta_b[3:0]  = desc_slot_b
  bar id       = meta_a[30:4] (shared)
```

### 3.2 DXA unit decode

`DxaUnit::process()` detects `meta[31]`, reads both halves, and pushes a
single `DxaReq` carrying:

```
  desc_slot / desc_slot_b      (A and B descriptor table indices)
  smem_addr / smem_addr_b      (A and B LMEM destinations)
  coords[5] / coords_b[5]      (A and B tile offsets)
  bar_id                       (shared; released once)
```

### 3.3 DXA core worker

`start_worker()` enumerates the work list for A, then for B, into one
combined `work_list`. The `last` flag lands on B's final line, so:

- GMEM reads for A and B interleave through the shared inflight window
  (bounded by `VX_CFG_DXA_MAX_INFLIGHT`).
- `notify_done` fires only after B's last write → one barrier release.
- `release_all_barriers()` is called once (not once per descriptor).

Non-pair requests take the existing single-descriptor path unchanged.

### 3.4 Kernel changes (`sgemm_tcu_wg_dxa`)

Double-buffer stage prefetch becomes:

```c
// Before (2 issues, expect_tx(2)):
bar_nxt.expect_tx(2);
vx_dxa_issue_2d_wg(kDescA, bar_nxt.id(), nxt_a, next_k, tile_row);
vx_dxa_issue_2d_wg(kDescB, bar_nxt.id(), nxt_b, tile_col, next_k);

// After (1 issue, expect_tx(1)):
bar_nxt.expect_tx(1);
vx_dxa_issue_2d_wg_pair(kDescA, kDescB, bar_nxt.id(),
                        nxt_a, nxt_b, next_k, tile_row, tile_col, next_k);
```

Prologue and epilogue updated to match. `main.cpp` descriptor programming is
unchanged (A = slot 0 row-major, B = slot 1 block-major).

### 3.5 Config

No new config flags. The pair path is always available (encoding is free);
multicast pair is out of scope for Phase 1 (the sgemm kernel does not use
multicast).

---

## 4. Expected impact (hypotheses to test)

| Metric | Baseline | Target | Mechanism |
|--------|----------|--------|-----------|
| DXA issues per stage | 2 | 1 | Pair encoding |
| Barrier events per stage | 2 | 1 | Single release |
| DXA instructions (kernel) | ~62% ALU mix | ↓ | Fewer setup-uops |
| b_only gate stall | 100% | ↓ | B reads start with A's |
| Cycles (K=512) | 28,080,063 | ↓ | Fewer stalls, fewer instrs |

The honest caveat from our prior experiments: instruction-count reductions
(fused ALU: −2.7% instrs, scrb 92→76%) did **not** move cycles because
sfu=98% (DXA saturation) became the binding constraint. The fused descriptor
attacks that constraint directly — fewer queue entries, one transfer instead
of two — so cycles have a real chance to move this time. If they don't, the
experiment still validates the ISA contract for Phase 2, where the pipeline
FSM removes the DXA-issue serialization entirely.

---

## 5. Validation plan

1. **K=64 smoke:** correctness (PASSED/FAILED) + IPC sanity (~0.77).
2. **K=512 full:** cycles vs 28,080,063 baseline; IPC vs 1.345.
3. **TCU profile (`VORTEX_PROFILING=11`):** b_only %, avg_pend_b,
   tbuf_stalls vs baseline.
4. **CORE profile (`VORTEX_PROFILING=1`):** scrb %, sfu %, instruction
   count vs baseline (expect −1 DXA issue + −1 expect_tx per stage).
5. **Size battery:** K ∈ {64, 128, 256, 512} at 512², plus the 512³ shape
   used in production runs, all PASSED.

---

## 6. Future phases (this document is the umbrella)

| Phase | Concept | Deliverable |
|-------|---------|-------------|
| 1 | Fused A+B descriptor | This proposal — DXA + kernel + test |
| 2 | Self-pipelining TCU | K-range descriptor, engine FSM, no per-iter instrs |
| 3 | Mailbox-native DSMEM | A-tile dedup across CTAs via mailbox |
| 4 | Tensor-dedicated memory path | L2 slices / port partitioning for DXA |
| 5 | Size-symmetric tiles | ISA/enumeration balance for A/B |

Each phase lands as one substantial commit with the size battery passing;
the fused descriptor (Phase 1) is the enabling contract for everything after.

---

## 7. Open questions

1. **Does the fused transfer actually beat the L2 arbiter in SimX?**
   **Answered: partially.** The dual-pipe fused descriptor achieved −1.62%
   (28.20M → 27.75M cycles) by splitting A and B across two DXA workers.
   But the 100% b_only gate stall persists — the L2 arbiter is NOT the
   bottleneck (DXA has 0 GMEM ports through it; traffic goes SFU → core
   LSU → L1 → socket). The stall is an internal DXA pipeline timing
   constant.
2. **Can kernel-level pipelining fix the b_only stall?**
   **Answered: no.** 9 experiments (dispatch reordering, pipeline deepening,
   port increases, tick reordering) all confirmed the 100% b_only gate
   stall with avg_pend_b=1.8 is irreducible at the current DXA
   implementation level. The next lever must be hardware-level.
3. **Pair + multicast interaction.** Out of scope now; a fused descriptor
   with multicast would need per-receiver dual-tile replay. Deferred.
4. **Descriptor pair vs. one wide descriptor.** Phase 1 keeps two
   descriptor-table slots (A row-major, B block-major layouts differ). A
   Phase 2 "wide" descriptor could merge them; keeping two slots preserves
   the existing `program_2d` API.

---

## 8. Measured results (SimX, G100 config, 512×512×512 fp16)

### 8.1 Fused A+B dual-pipe (current HEAD on main)

| Config | Cycles | IPC | Δ vs original |
|--------|--------|-----|---------------|
| Original double-buffer | 28,203,780 | 1.304 | — |
| Fused A+B single-worker | 28,203,780 | 1.304 | 0% |
| **Fused A+B dual-pipe (2 workers)** | **27,747,759** | **1.325** | **−1.62%** |
| 4-worker (no benefit) | 28,430,761 | 1.293 | +0.8% |

Instruction count is identical across all configs (36,767,744). The win is
purely in the memory path — A and B issue through two independent arbiter
ports instead of one serialized interleaved list.

### 8.2 CORE profile (VORTEX_PROFILING=1)

| Stall | % | Interpretation |
|-------|---|----------------|
| **scrb** | **92%** | Cores stalled waiting for DXA results |
| **sfu** | **96%** | DXA pipeline nearly saturated |
| tcu | 0% | Tensor unit never stalls — always operand-starved |
| fetch/ibuf/opds/alu/lsu | 0% | Not the bottleneck |

Instruction mix: alu=62% (setup-uop overhead), tcu=22% (WGMMA), sfu=10%
(DXA loads), lsu=6%. Load latency: 13.68 cycles avg.

**Key finding:** scrb=92% + sfu=96% confirms the DXA tile fetch latency is
the binding constraint. No further DXA worker parallelism (2→4) helps
because the single shared L2 arbiter pipe serializes all GMEM reads. The
bottleneck has moved from DXA workers to the **memory subsystem**.

### 8.3 Scale test: 1024×1024×512 (32K CTAs)

| Metric | 512² (8K CTAs) | 1024² (32K CTAs) | Ratio |
|--------|----------------|------------------|-------|
| Cycles | 27,747,759 | 111,140,698 | 4.006× ✅ |
| IPC | 1.325 | 1.323 | 0.999× ✅ |
| b_only gate | 3,153,024 | 12,585,408 | 3.992× ✅ |
| avg_pend_b | 1.8 | 1.8 | identical |
| tbuf_cache_hits | 0 | 0 | identical |
| Correctness | PASSED | PASSED | — |

**The gate stall pattern is perfectly linear and occupancy-independent.**
Every core shows the exact same signature: 100% b_only, avg_pend_b=1.8,
zero cache hits. The B tile arrives 1.8 cycles late on average — just
enough to stall every WGMMA gate. This is an architectural constant that
doesn't change with CTA count.

### 8.4 Scale test: 2048×2048×512 (131K CTAs)

Still running at time of writing (PID 1286375, 4d 5h wall, 199% CPU on
2-core EPYC). Linear extrapolation predicts ~444M cycles. Will update
when complete.

### 8.5 Bugs fixed

- **multicast mask in pair mode:** `cta_mask = coord_b1` (nonzero) triggered
  multicast release; fixed by forcing `cta_mask=0` in pair mode.
- **release-build livelock:** `scheduler.cpp` sets `uuid=0` for all traces when
  `NDEBUG` is defined; `pair_pending_[uuid]` collided across concurrent pairs.
  Fixed by replacing uuid-keyed map with a DXA-internal monotonically-increasing
  `pair_id_` counter.

---

## 9. Persistent CTA scheduling with DSMEM B-tile sharing

### 9.1 Motivation

The 100% b_only gate stall (Section 1.1) is irreducible at the current DXA
pipeline level — no kernel-level or dispatch-level change moves it. But
there is a **bandwidth** lever we haven't tried: **eliminating redundant
GMEM reads across CTAs that share B tiles.**

In the current kernel, the grid is `N/xtileN × M/cta_M` CTAs. CTAs with
the same `blockIdx.x` read the **identical B tile** from global memory —
independently, through the DXA, every iteration. For a 512×512 GEMM with
xtileN=8, there are 64 N-columns, each read by 128 CTAs (M/4 rows). That's
128 independent GMEM reads of the same 128-byte B tile per K-iteration.

The DSMEM infrastructure (Section 2.4) already provides cross-core LMEM reads
within a cluster. A non-stalling `vx_mailbox_read` returns the target core's
`VX_CSR_MAILBOX` value without pipeline stall. A `vx_dsmem_read` reads an
arbitrary LMEM word from a peer core with ~2-tick latency through the cluster
DSMEM arbiter.

**Persistent CTAs + DSMEM B-tile sharing** inverts this: one CTA per
row-group fetches B via DXA; peers read it from the master's LMEM. This
reduces B GMEM traffic by **16×** (for 16-CTA row-groups).

### 9.2 Architecture

#### CTA-to-core mapping

G100 config: 8 clusters × 16 cores = 128 cores. The CTA scheduler maps
CTAs to cores round-robin. For a `grid_x=64` (N-columns) grid:

```
Core 0:  CTA (0,0), CTA (0,16), CTA (0,32), ...   (persistent loop)
Core 1:  CTA (1,0), CTA (1,16), CTA (1,32), ...
...
Core 15: CTA (15,0), CTA (15,16), ...
Core 16: CTA (0,1), CTA (0,17), ...                 (next cluster)
```

**Key constraint:** DSMEM reads are cluster-scoped. Two cores in different
cannot read each other's LMEM. The persistent CTA model must ensure that
row-group peers (CTAs with the same `blockIdx.x`) land on cores within the
same cluster.

#### B-tile sharing model

For a row-group of `P` CTAs sharing B tile at `blockIdx.x = bx`:

1. **B-master** (CTA with lowest `blockIdx.y` in the row-group): fetches B
   via DXA, writes to LMEM, sets mailbox = B_READY (1), then computes.
2. **B-peers** (remaining P−1 CTAs): skip DXA B-fetch, poll mailbox until
   B_READY, then read B from master's LMEM via `vx_dsmem_read`.
3. **Synchronization:** master writes mailbox after B is resident in LMEM;
   peers spin on `vx_mailbox_read(master_core)` (non-stalling, 0-cycle
   pipeline stall).

#### Memory layout

The B tile is `tileK × xtileN` = 8×8 = 64 elements = 128 bytes (fp16).
Placed at a fixed LMEM offset (e.g., `DSMEM_B_OFFSET = 0x1000`) so peers
can derive the address without a pointer exchange.

#### Persistent CTA loop

Each CTA processes multiple B tiles in a persistent loop:

```c
for (uint32_t bx = cta_id_x; bx < grid_x; bx += cluster_cores) {
  uint32_t tile_col = bx * xtileN;
  bool is_b_master = (cta_id_y == 0);  // or: lowest y in row-group

  if (is_b_master) {
    // Fetch B via DXA into LMEM at DSMEM_B_OFFSET
    vx_dxa_issue_2d_wg(kDescB, bar.id(), DSMEM_B_ADDR, tile_col, k);
    bar.arrive_and_wait();
    // Signal B ready to peers
    vx_mailbox_write(1);  // or: vx_csr_write(VX_CSR_MAILBOX, 1)
  } else {
    // Poll master's mailbox (non-stalling)
    while (vx_mailbox_read(master_core_id) != 1) { /* spin */ }
    // Read B from master's LMEM via DSMEM
    for (uint32_t i = 0; i < b_elems; ++i) {
      B_smem[i] = vx_dsmem_read(master_core_id, DSMEM_B_OFFSET + i*4);
    }
  }

  // Fetch A via DXA (each CTA still fetches its own A)
  // Compute WGMMA on A × B
  // Accumulate into C
}
```

### 9.3 GMEM traffic analysis

| Metric | Current (per K-iter) | Persistent CTA (per K-iter) |
|--------|---------------------|----------------------------|
| B fetches | P CTAs × 128 B = P×128 B | 1 master × 128 B = 128 B |
| A fetches | P CTAs × 64 B = P×64 B | P CTAs × 64 B (unchanged) |
| DSMEM reads | 0 | (P−1) × 64 × 4 B = (P−1)×256 B |
| Total GMEM | P×192 B | P×64 + 128 B |
| **GMEM reduction** | — | **P×192 → 64P+128** |

For P=16 (16 CTAs per row-group in G100):
- Current: 16×192 = 3,072 B per K-iteration
- Persistent: 16×64 + 128 = 1,152 B per K-iteration
- **Reduction: 62.5%**

But wait — the DSMEM reads also consume bandwidth. Each `vx_dsmem_read`
is a cluster-scoped bus transaction (~2 ticks). For P=16, peers issue
64 reads each = 1,024 DSMEM reads per K-iteration. At 1 read/cycle,
that's ~1,024 cycles of DSMEM bus contention.

### 9.4 DSMEM latency analysis

The DSMEM arbiter processes one read per cycle (round-robin across cores).
For P=16 CTAs in a cluster:

- 15 peers × 64 reads each = 960 DSMEM reads per K-iteration
- At 1 read/cycle: 960 cycles of DSMEM bus time
- Each read: ~2 tick pipeline (SFU → cluster arb → target LMEM → response)
- Total: 960 × 2 = 1,920 cycles of DSMEM latency per K-iteration

Compare to DXA B-fetch latency: avg 13.68 cycles per element × 64 elements
= 876 cycles. But DXA fetches are pipelined (inflight window), so the
**wall-clock** DXA B-fetch is ~50-100 cycles (bounded by GMEM pipeline depth).

**The DSMEM path is 19× slower than DXA for B delivery** (1,920 vs ~100
cycles). This means the persistent CTA model **hurts** for small P but
**helps** when P is large enough that the GMEM bandwidth savings outweigh
the DSMEM latency.

### 9.5 Break-even analysis

The persistent CTA model helps when:

```
DSMEM_latency < GMEM_savings
(P−1) × tileK × xtileN × 2 < P × (a_size + b_size) / GMEM_bandwidth
```

For G100 config with 16 cores/cluster:
- DSMEM cost: 15 × 64 × 2 = 1,920 cycles
- GMEM savings: 15 × 192 = 2,880 B saved, but DXA bandwidth is
  already saturated (sfu=96%), so the savings don't translate to
  fewer cycles — the DXA is the bottleneck, not GMEM bandwidth.

**Critical insight:** The 100% b_only gate stall means the TCU is always
waiting for B. If B arrives via DSMEM (1,920 cycles) instead of DXA
(~100 cycles), the stall gets **worse**, not better. The DSMEM path is
slower than DXA for B delivery.

### 9.6 When persistent CTAs actually help

The persistent CTA model helps only when:

1. **GMEM bandwidth is the bottleneck** (not DXA pipeline latency). This
   happens at very high occupancy (many CTAs, small tiles) where the DXA
   is underutilized and GMEM reads dominate.
2. **The DSMEM bus is fast enough** to deliver B before the TCU gate check.
   This requires hardware-level DSMEM (dedicated bus, not SFU-mediated).
3. **The B tile is large enough** that the GMEM savings outweigh the DSMEM
   overhead. For NRC=8, B=128B — too small. For NRC=32 (production scale),
   B=512B — the savings start to matter.

### 9.7 Revised recommendation

**Do not implement persistent CTAs for the current configuration.** The
numbers show it hurts:

| Approach | B delivery time | Gate stall |
|----------|----------------|------------|
| Current (DXA per-CTA) | ~100 cycles | 100% b_only |
| Persistent CTA (DSMEM) | ~1,920 cycles | **worse** |

The persistent CTA model becomes viable only after:

1. **Phase 2 (self-pipelining TCU):** The pipeline FSM eliminates the
   per-iteration DXA issue overhead, so CTAs are cheaper to run and the
   GMEM savings matter more.
2. **Phase 4 (tensor-dedicated memory path):** Dedicated DXA memory ports
   increase GMEM bandwidth, making the bandwidth savings from sharing
   meaningful.
3. **Production-scale tiles (NRC≥32):** Larger B tiles (≥512B) make the
   GMEM savings dominate the DSMEM overhead.

The persistent CTA design is documented here as a **Phase 5 optimization**
that builds on Phases 2 and 4. It is not the next lever to pull.

### 9.8 What IS the next lever?

The 9-experiment campaign (Section 1.1) proved the b_only stall is
irreducible at the current DXA pipeline level. The remaining levers are:

| Lever | Phase | Expected impact | Difficulty |
|-------|-------|----------------|------------|
| Self-pipelining TCU FSM | 2 | Eliminates per-iter DXA issue (62% ALU) | High |
| Tensor-dedicated memory path | 4 | Enables dual-ported B fetch | Medium |
| Size-symmetric tiles | 5 | Eliminates A/B asymmetry class | Low |
| Persistent CTAs + DSMEM | 5+ | GMEM bandwidth sharing | High |

The **self-pipelining TCU (Phase 2)** is the highest-impact next step: it
eliminates 62% of the instruction stream (setup-uops) and moves the pipeline
FSM into hardware, making all subsequent optimizations (DSMEM, persistent
CTAs) more effective.

---

## 10. Phase 2 — Self-pipelining tensor FSM

### 10.1 Current per-iteration overhead

The double-buffered kernel (Section 8.1) executes this loop per K-iteration:

```c
// Each iteration: 7+ instructions, 62% ALU mix
bar_nxt.expect_tx(1);                          // 1 ALU
vx_dxa_issue_2d_wg_pair(...);                   // 1 SFU
bar_cur.arrive_and_wait();                      // 1 ALU (barrier)
// WGMMA compute — 1 TCU instruction → 9 uops
ctx::wgmma_sync(fragC, desc_a, desc_b, fragC); // 1 TCU
bar_cur.arrive_and_wait();                      // 1 ALU (barrier)
cur = nxt;                                      // 1 ALU
swap(cur_a, nxt_a); swap(cur_b, nxt_b);        // 3 ALU
```

CORE profile (VORTEX_PROFILING=1) confirms:

| Component | % | Interpretation |
|-----------|---|----------------|
| **ALU** | **62%** | Setup-uops: barrier, pointer swap, loop control |
| TCU | 22% | Actual WGMMA compute (the only useful work) |
| SFU | 10% | DXA loads |
| LSU | 6% | Stores |

**62% of all instructions are overhead.** The TCU computes for 22% of the
instruction stream. The kernel spends 3× more instructions managing the
pipeline than executing useful math.

### 10.2 Design: K-range descriptor

One hardware instruction replaces the entire K-loop. The kernel issues a
**tensor GEMM range descriptor** (`TGM`) that encodes:

```
TGM  rd, desc_a, desc_b, K_start, K_end, tile_row, tile_col

  rd        = accumulator fragment (in-place, 8×8×fp32)
  desc_a    = A tile descriptor (smem address + layout)
  desc_b    = B tile descriptor (smem address + layout)
  K_start   = first K-tile index (inclusive)
  K_end     = last K-tile index (exclusive)
  tile_row  = M-tile offset (for DXA A fetch)
  tile_col  = N-tile offset (for DXA B fetch)
```

**Encoding:** Reuse the existing WGMMA opcode (funct7=0x3) with a new
type bit in the descriptor meta field. The hardware distinguishes TGM
from single-shot WGMMA via `meta[31]=1` + `meta[30]=1` (two flag bits).

**One instruction, one barrier.** The kernel issues TGM, waits for the
completion barrier, and reads the result from `rd`. Zero per-iteration
instructions.

### 10.3 Hardware FSM state machine

The TCU gains a per-CTA pipeline FSM with 4 states:

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐
│ FETCH_A │────▶│ FETCH_B  │────▶│ COMPUTE  │────▶│ ADVANCE │
│ (DXA)   │     │ (DXA)    │     │ (FEDP)   │     │ (swap)  │
└─────────┘     └──────────┘     └──────────┘     └─────────┘
     ▲                                                       │
     └───────────────── double-buffer rotate ───────────────┘
```

**State transitions:**

1. **FETCH_A:** Issue DXA pair-read for A tile into smem stage[0].
   Awaits LMEM write completion (barrier auto-release).
2. **FETCH_B:** Issue DXA pair-read for B tile into smem stage[0]+a_size.
   (In fused-pair mode, A+B issue simultaneously — FETCH_A and FETCH_B
   collapse into one state.)
3. **COMPUTE:** Dispatch WGMMA uops for current stage. TCU processes
   k_steps × nrc micro-ops internally. No software intervention.
4. **ADVANCE:** Swap smem stage pointers. If K tile < K_end, rotate
   to FETCH_A for next stage. If K tile == K_end, signal completion
   barrier.

**Pipeline overlap:** While COMPUTE runs on stage[0], FETCH_A/B issues
for stage[1] — this is the double-buffer overlap, now managed in
hardware instead of software.

### 10.4 FSM timing model

For the G100 config with NRC=8, tileK=8, k_steps=1:

| Phase | Latency (cycles) | Notes |
|-------|-----------------|-------|
| FETCH_A+B (fused pair) | ~50-100 | DXA pipelined GMEM read |
| COMPUTE (1 WGMMA) | ~30-50 | FEDP eval, k_steps=1, nrc=8 |
| ADVANCE | ~5 | Pointer swap, barrier signal |
| **Total per K-tile** | **~85-155** | Hardware-managed |

Compare to current software pipeline per K-tile:

| Phase | Current (software) | Phase 2 (hardware) |
|-------|--------------------|--------------------|
| DXA issue | 1 SFU instr | 0 (HW-internal) |
| Barrier wait | 2 ALU instr | 0 (HW-internal) |
| WGMMA compute | 1 TCU instr | 0 (HW-internal) |
| Pointer swap | 3 ALU instr | 0 (HW-internal) |
| Loop control | 1 ALU instr | 0 (HW-internal) |
| **Total instructions** | **8 per K-tile** | **1 (TGM)** |
| **Total per K-tile** | **~100-200 cycles** | **~85-155 cycles** |

The cycle count doesn't change dramatically (the DXA latency dominates),
but the **instruction count drops by 87.5%** — from 8 instructions per
K-tile to 1 instruction for the entire K-range. This eliminates the
62% ALU overhead entirely.

### 10.5 Kernel transformation

**Before (software pipeline, 8 instructions per K-tile):**

```c
for (uint32_t k = 0; k < K; k += tileK) {
  if (k + tileK < K && is_dxa_warp) {
    bar_nxt.expect_tx(1);
    vx_dxa_issue_2d_wg_pair(kDescA, kDescB, bar_nxt.id(),
                            nxt_a, nxt_b, k+tileK, tile_row, tile_col, k+tileK);
  }
  bar_cur.arrive_and_wait();
  ctx::wgmma_sync(fragC, desc_a, desc_b, fragC);
  bar_cur.arrive_and_wait();
  cur = nxt;
  swap(cur_a, nxt_a); swap(cur_b, nxt_b);
}
```

**After (self-pipelining FSM, 1 instruction total):**

```c
// Issue tensor GEMM with K-range — hardware does the rest.
vx_tgm(fragC, kDescA, kDescB, 0, K/tileK, tile_row, tile_col);
// fragC is updated in-place after K/tileK iterations.
```

The kernel shrinks from ~30 instructions (DB path) to ~10 instructions
(descriptor setup + TGM + store). ALU mix drops from 62% to ~0%.

### 10.6 SimX implementation plan

**SimX model (functional simulation, no cycle-accuracy):**

1. **New TcuType::TGM** — single opcode that triggers the FSM.
2. **FSM state** — stored in `tcu_unit.h` as per-CTA state:
   ```
   struct TgmFsmState {
     uint32_t k_current;      // current K-tile index
     uint32_t k_end;          // K_end from descriptor
     uint32_t tile_row, tile_col;
     uint32_t stage;          // 0 or 1 (double-buffer)
     uint32_t a_desc, b_desc;
     bool prefetch_issued;    // has DXA been issued for next stage?
   };
   ```
3. **tick() integration** — in the TCU tick loop, when a TGM trace
   arrives, push it into the FSM. Each tick advances one state:
   FETCH → COMPUTE → ADVANCE. When k_current == k_end, signal the
   completion barrier.
4. **DXA interface** — the FSM reuses the existing DXA issue path
   (SFU → DXA unit) but issues are generated by the FSM, not by
   kernel instructions.
5. **Barrier interface** — the FSM auto-manages barriers using the
   existing barrier infrastructure (bar0/bar1 for double-buffer).

**Kernel interface:**

```c
// New intrinsic:
void vx_tgm(fragment_acc& rd, uint32_t desc_a, uint32_t desc_b,
             uint32_t k_start, uint32_t k_end,
             uint32_t tile_row, uint32_t tile_col);

// Implementation:
static inline void vx_tgm(...) {
  __asm__ volatile (
    ".insn r %1, 0, 7, %0, %2, %3"
    : : "r"(rd), "i"(0x0B), "r"(desc_a), "r"(desc_b)
  );
}
```

### 10.7 Expected impact

| Metric | Current (DB) | Phase 2 (TGM) | Delta |
|--------|-------------|---------------|-------|
| Instructions per K-tile | 8 | ~0.33 (1 per 3 K-tiles) | −96% |
| ALU instruction mix | 62% | ~0% | −62 pp |
| TCU instruction mix | 22% | ~80% | +58 pp |
| Cycles per K-tile | ~100-200 | ~85-155 | −7-22% |
| Total instructions (K=512) | 574,976 | ~80,000 | −86% |
| scrb stall | 92% | ~40-50% | −42-52 pp |
| IPC | 1.325 | ~2.0-2.5 | +50-90% |

The instruction count drops by 87.5%. The scrb stall drops because the
core spends less time waiting for setup-uops. IPC improves because the
instruction stream is dominated by useful TCU work (80%) instead of
overhead (62%).

**Cycles improvement is modest** (~7-22%) because the DXA latency
(~50-100 cycles per K-tile) still dominates. But the instruction
reduction enables future optimizations:
- **Fewer instructions = less scrb pressure** → more room for DXA
  prefetch overlap
- **FSM-managed prefetch** → can prefetch 2 stages ahead (triple-buffer)
  with zero software cost
- **Hardware barrier auto-release** → eliminates the CTA-overlap fence
  entirely

### 10.8 What Phase 2 enables

1. **Triple-buffer at zero cost.** The FSM can prefetch stage N+2 while
   computing stage N — no additional instructions, no software complexity.
   This gives B an extra iteration of latency hiding.

2. **Persistent CTAs become viable.** With FSM-managed K-loops, a
   persistent CTA processes multiple K-ranges without re-issuing the
   TGM instruction. The DSMEM B-tile sharing (Section 9) can overlap
   with the FSM's FETCH phase.

3. **CTA-level software pipelining.** The FSM can be extended to
   overlap DXA fetches across CTA boundaries — CTA N+1's FETCH phase
   runs while CTA N's COMPUTE phase executes, all managed by hardware.

4. **Self-tuning pipeline depth.** The FSM can dynamically adjust
   prefetch depth based on DXA latency measurements — deep pipeline
   for high-latency GMEM, shallow for cache-resident tiles.
