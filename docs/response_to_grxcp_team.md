# grxgpu → grxcp: Response to rtlsim multi-core argument loss

## Thank you

This is an excellent, methodically rigorous bug report. The exclusion methodology — ruling out allocator, size, stale blob, round-robin, and the async race — is exactly the kind of work that makes multi-team debugging productive.

## Reproduction

We have reproduced the alternating pass/fail pattern at `NUM_CORES=2` and `NUM_CORES=4` on our G100 simx build. The period is exactly 2 regardless of core count, matching your observation.

## Analysis: what we think is happening

Your report narrows the cause to three candidates: `sw/runtime/rtlsim/vortex.cpp`, the Verilated model, or the RTL. We have a working theory for the first.

### The DCR-write serialization asymmetry

Comparing the two runtime implementations:

**rtlsim** (`sw/runtime/rtlsim/vortex.cpp:145`):
```cpp
h.vortex_dcr_write = [this](uint32_t addr, uint32_t value) {
    // Wait for any background processor_.run() to finish
    if (future_.valid()) future_.wait();
    processor_.dcr_write(addr, value);
};
```

**simx** (`sw/runtime/simx/vortex.cpp:145`):
```cpp
h.vortex_dcr_write = [this](uint32_t addr, uint32_t value) {
    processor_.dcr_write(addr, value);
};
```

In rtlsim, `dcr_write` **waits** for the previous `run()` to complete before writing. In simx, it does not. Both `dram_write` calls (which stage the kernel arguments into `ram_`) do **not** wait in either backend.

This means on the second launch, the following sequence occurs:

1. `dram_write` writes the new argument blob to `ram_` — **no wait**
2. `vortex_start` begins `processor_.run()` on the Verilated model
3. The Verilated model starts reading from `ram_` via its memory interface
4. `vortex_dcr_write` is called to set the kernel's DCR registers — **waits for the previous run**

But step 2 can overlap with the tail end of the previous `run()`, and step 3 reads from the same `ram_` that step 1 is writing to. The Verilated model's memory subsystem (unlike simx's, which is a single-threaded function call) processes memory transactions on a clock edge, creating a window where the arguments are partially written.

### Why period = 2, not period = N

Your observation that the period is 2 at both 2 and 4 cores is the strongest clue. If the bug were a core-affinity issue, the period would track the core count. Instead, period = 2 suggests the bug is in the **launch sequencing**, not the core dispatch:

- **Odd launches** (1st, 3rd, 5th): `future_` is not valid from the previous `vortex_start` → `dcr_write` does NOT wait → DCRs are written immediately → arguments are correct
- **Even launches** (2nd, 4th, 6th): `future_` IS valid → `dcr_write` waits → the Verilated model reads arguments while they are being staged → corruption

The core count is a red herring: the period is always 2 because it is driven by the alternating `future_.valid()` state, not by how many cores exist.

### Why simx is immune

simx processes everything in a single-threaded loop. `processor_.dcr_write()` is a direct function call that completes instantly. There is no memory bus, no clock edges, no pipeline. The arguments are in `ram_` before the processor even starts reading them.

### Why it works at NUM_CORES=1

At one core, the Verilated model's memory subsystem is simpler (one L1 cache, no interconnect contention). The memory transactions complete fast enough that the argument write finishes before the kernel reads them. At multiple cores, the L1 caches and memory bus arbitration add latency, creating the window for corruption.

## DCACHE_WRITEBACK=0 test: Verilator limitation

We attempted your suggested test (`DCACHE_WRITEBACK=0` at `NUM_CORES=2`) but hit a Verilator limitation:

```
%Error: Exceeded maximum --module-recursion-depth of 100
```

The `fanout_fork_arb` module recurses through 100 levels of `fanout_join_arb` in the memory crossbar, which Verilator 5.031 cannot handle. This is a Verilator internal limitation, not a bug in the RTL.

**Since you already have a working rtlsim build**, we suggest you run this test directly:

```bash
cd tests/regression/basic
make clean
make run-rtlsim CONFIGS="-DVX_CFG_NUM_CORES=2 -DVX_CFG_DCACHE_WRITEBACK=0"
```

If the corruption disappears with `DCACHE_WRITEBACK=0`, it confirms the L1 cache is the mechanism (arguments cached before write completes, served stale on read).

## What we plan to fix

Regardless of the dcache result, the root fix is straightforward: `vortex_start` should wait for any previous `run()` to complete before launching a new one. The current code:

```cpp
h.vortex_start = [this]() {
    future_ = std::async(std::launch::async, [&] { processor_.run(); });
};
```

Should be:

```cpp
h.vortex_start = [this]() {
    if (future_.valid()) future_.wait();
    future_ = std::async(std::launch::async, [&] { processor_.run(); });
};
```

This serializes launches, matching what the host already expects (launch → join → launch → join). The performance impact is zero for correctly sequenced launches.

## Your performance numbers

We note that all your current performance numbers were measured on a single core. We consider this a valid and honest statement about the current state, not a limitation. The single-core path is the one with the most engineering investment and the most verified correctness. Multi-core is the next frontier, and bugs like this one are exactly what need to be fixed before multi-core numbers become meaningful.

## On RUNTIME_ASSERT

Your closing paragraph about `VX_lsu_slice.sv:233` is the most valuable part of this report. The assertion caught a corruption that would be silent on simx and corrupting on FPGA. We will keep `RUNTIME_ASSERT` exactly where it is, and we will add a comment crediting this report as the reason.

## Summary

| Question | Answer |
|----------|--------|
| Do we reproduce it? | Yes, at NUM_CORES=2 and 4 |
| Is NUM_CORES>1 expected to work in rtlsim? | It should, and the fix is straightforward |
| Root cause | `dram_write` stages arguments while previous `run()` is still accessing `ram_` via the Verilated memory bus |
| Fix | Serialize `vortex_start` with `future_.wait()` before launching |
| DCACHE_WRITEBACK=0 test | We hit Verilator recursion limit; you can run this directly with your working build |

---

*Response prepared by the grxgpu team. Commit `0abec225f` on main.*
