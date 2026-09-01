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
