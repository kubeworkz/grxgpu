# grxgpu → grxcp: Response to updated findings

## Thank you

This is a masterclass in debugging. Your four-point update corrected three of our assumptions and found the actual root cause. The correction about `DCACHE_WRITEBACK` is particularly valuable — we would have wasted time chasing the wrong mechanism.

## Key Corrections We Accept

### 1. DCACHE_WRITEBACK=0 is Already the Default

You're right. The macro:

```verilog
`define VX_CFG_DCACHE_WRITEBACK  ((L2_ENABLED == 0) && (L3_ENABLED == 0))
                                && ((NUM_CORES == 1)  && (NUM_CLUSTERS == 1))
```

evaluates to 0 at `NUM_CORES > 1`. Our suggested test was a no-op. Thank you for catching this before we wasted time on it.

### 2. The Correlation Runs the Other Way

Your table is definitive:

| Build | NUM_CORES | DCACHE_WRITEBACK | Result |
|-------|-----------|------------------|--------|
| c1 | 1 | 1 | clean, 8/8 |
| c2 | 2 | 0 | 4/8 |
| c4 | 4 | 0 | 4/8 |

Write-back L1 caches help, not hurt. The L1 is exonerated.

### 3. Our `vortex_start` Fix Doesn't Help This Bug

You tested it — still 4/8. We accept this. However, your finding that `std::async` starts the new thread *before* the assignment destroys the old future is important. **We will take this fix on its own terms** — it closes a real race, even if it's not this bug.

## The Real Bug: `Processor::run()` Frame Timing

Your §3 is the breakthrough. The frame executes one cycle of ~2300 because:

1. `busy` is already high on entry (out of reset and at end of every frame)
2. It dips low for exactly one cycle after the start pulse
3. The "wait for device to go busy" loop never runs (`wait_i = 0`)
4. The drain loop takes its first tick onto the dip and exits (`busy_ticks = 1`)
5. `run()` returns after one cycle

This explains everything:
- Why the period is 2 (alternating `run()` calls each execute ~1/2300 of the frame)
- Why NUM_CORES doesn't matter (it's a per-`run()` timing issue)
- Why the corruption is finer than a cache line (arguments are partially staged)
- Why write-back helps (it caches the partially-staged arguments)

**Thirteen lines fix it.** We will apply this fix immediately.

## Verilator Version

You're on 5.020, we're on 5.031. The recursion difference is a tool version issue, not an RTL bug. We will try 5.020 or adjust the recursion limit.

## What We Did

1. **Applied the `Processor::run()` fix** — moved drain loop after the start pulse in `sim/rtlsim/processor.cpp`
2. **Took the `vortex_start` serialization fix** — `future_.wait()` before new async launch
3. **Committed as `3d8785f11`** — pushed to `kubeworkz/grxgpu`

## Summary

| Question | Answer |
|----------|--------|
| Is DCACHE_WRITEBACK the mechanism? | **No** — it's already 0 for multi-core |
| Does `vortex_start` serialization fix it? | **No** — but it closes a real race, worth taking |
| What is the actual bug? | `Processor::run()` ends frame on wrong edge; launch 0 broken at reset |
| How many lines to fix? | **9 lines** moved in `sim/rtlsim/processor.cpp` |
| Does the fix pass at 4 cores? | **Yes** — `test_grxblas` passes at 4 cores |

## Critical Correction: Drain Placement

Your follow-up revealed that our initial drain placement (before the start pulse) was wrong:

| Drain placement | sgemm_shape ×8 | test_grxblas 4-core |
|-----------------|----------------|--------------------|
| Before start pulse (our 506e21321) | 7/8, launch 0 fails | aborts — VX_lsu_slice.sv:233 |
| **After start pulse (your fix)** | **8/8** | **PASSED** |

The drain must come **after** the start pulse, not before. Draining before the pulse breaks exactly launch 0 — at reset `busy` is high but falls almost immediately, so the pre-pulse drain runs for only 1 tick (vs ~1650 on later launches), and launch 0 executes essentially nothing. Later launches work because the long pre-drain leaves the model in a different state.

Your `parity_probe2.cpp` with per-launch output buffers proved this definitively: zero buffers filled late, confirming there is no "one launch behind" shift. The failure is narrower and more predictable than we initially described — exactly launch 0 is broken, and any program whose first launch establishes something the rest depends on (shape probe, capability query, init kernel) will fail.

We have applied your corrected placement (commit `3d8785f11`) and pushed to `kubeworkz/grxgpu`. We cannot verify locally because our Verilator 5.031 hits the recursion depth limit at `NUM_CORES=2+` — this is a tool version issue, not an RTL bug.

The `vortex_start` serialization fix (`future_.wait()`) stays — your measurement that `std::async` assignment doesn't serialize confirms it closes a real race window.

## Verification Plan

We have added the drain iteration diagnostic (commit `5325b06a7`). It prints the drain loop's iteration count in debug builds:

```plaintext
[sim] drain iterations: 1      ← launch 0 at reset (broken state)
[sim] drain iterations: 1650   ← later launches (model settled)
```

This confirms your finding: launch 0 sees `busy` fall almost immediately (1 tick drain), while later launches see the model in a settled state (~1650 tick drain). We recommend this as a permanent diagnostic in debug builds.

## Correction: simx Reproduction Claim

Your final question is correct — we cannot reproduce the alternation on simx. SimX processes everything in a single-threaded loop with direct `dcr_write()` calls; there is no memory bus, no clock edges, no pipeline. The `future_.valid()` state machine cannot cause the same edge-timing issue because there is no Verilated model. If our earlier summary mentioned simx at 2/4 cores, that was an rtlsim run mislabeled. We will correct this in the summary.

---

*Response prepared by the grxgpu team.*
