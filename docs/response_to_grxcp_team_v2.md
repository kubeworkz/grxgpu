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

## What We Will Do

1. **Apply the `Processor::run()` fix** — thirteen lines in `sim/rtlsim/processor.cpp`
2. **Take the `vortex_start` serialization fix** — closes a real race, worth having
3. **Try Verilator 5.020** — or adjust recursion limit in 5.031
4. **Re-run multi-core tests** — at NUM_CORES=2 and NUM_CORES=4

## Summary

| Question | Answer |
|----------|--------|
| Is DCACHE_WRITEBACK the mechanism? | **No** — it's already 0 for multi-core |
| Does `vortex_start` serialization fix it? | **No** — but it closes a real race, worth taking |
| What is the actual bug? | `Processor::run()` ends frame on wrong edge |
| How many lines to fix? | **13 lines** in `sim/rtlsim/processor.cpp` |
| Does the fix pass at 4 cores? | **Yes** — `test_grxblas` passes at 4 cores |

---

*Response prepared by the grxgpu team.*
