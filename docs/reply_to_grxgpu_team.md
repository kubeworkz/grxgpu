# grxcp → grxgpu: `rtlsim` loses kernel arguments on every other launch when `NUM_CORES > 1`

Against `grxgpu` at `8aecb6df5`. One defect, reproduced at two and four cores, absent at one core and absent on `simx` at the same core count. Everything below was measured; where we are fitting rather than reading, we say so.

## The claim

With `VX_CFG_NUM_CORES` greater than 1, `rtlsim` delivers a kernel's argument blob to the kernel on **every other launch**. Launches that do not receive it run with something else in the argument struct — usually enough to fail the kernel's own version guard, sometimes enough to pass it and then dereference a pointer field that was never written.

This is not a grxcp defect and we are not asking for a grxcp change. We are reporting it because it makes any multi-core configuration unusable, and because a single-launch test cannot see it.

## Minimal reproduction

Launch **any** kernel N times with an identical argument blob and check, per launch, whether the kernel observed its arguments. We used `sgemm_shape`, whose whole body is a version check and seven stores, because it makes the answer binary: the output buffer is either written or untouched.

```plaintext
CONFIGS="-DVX_CFG_EXT_TCU_ENABLE -DVX_CFG_EXT_DXA_ENABLE \
         -DVX_CFG_NUM_WARPS=16 -DVX_CFG_TCU_FP16_ENABLE \
         -DVX_CFG_TCU_INT8_ENABLE -DVX_CFG_NUM_CORES=<N>"


```

Same blob, same output buffer, same argument size, same process. Only the launch index varies:

```plaintext
rtlsim, NUM_CORES=1:   wrote wrote wrote wrote wrote wrote wrote wrote    8/8
rtlsim, NUM_CORES=2:   ----- wrote ----- wrote ----- wrote ----- wrote    4/8
rtlsim, NUM_CORES=4:   ----- wrote ----- wrote ----- wrote ----- wrote    4/8
simx,   NUM_CORES=1:   wrote wrote wrote wrote wrote wrote wrote wrote    8/8
simx,   NUM_CORES=4:   wrote wrote wrote wrote wrote wrote wrote wrote    8/8


```

Deterministic across processes, and **the first launch is one of the failures**, so this is not a value left behind by a predecessor.

## What we ruled out, and how

Each of these removed a candidate we would otherwise have reported as the cause.

**It is not the host allocator.** Measured on the failing four-core build itself, `grxMalloc(28)` returns `0x10000, 0x10100, 0x10200, 0x10300` — 256-byte aligned, identical to `simx`. Our first draft of this report blamed a misaligned pointer from the allocator. That was an assumption; the measurement contradicted it.

**It is not the argument size.** Sizes 16/24/32/48/64 appear to alternate pass/fail, which reads as a size effect until size is held fixed. At 16 bytes alone, both outcomes still occur in the same alternating order. The first sweep was measuring launch index and calling it size.

**It is not a stale blob from the previous launch.** Eight launches with eight *distinct* output buffers leave buffers 0, 2, 4, 6 untouched and 1, 3, 5, 7 correct. No buffer is written twice and none is written by the wrong launch, so a failing launch is not running with its neighbour's arguments — it is running with arguments whose version field is not what the host wrote.

**It is not a round-robin over cores.** The period is 2 at two cores *and* 2 at four cores. A dispatcher cycling one CTA across cores would give a period of 4 on the four-core part.

**It is not the async-run race, however much it looks like one.** `sw/runtime/rtlsim/vortex.cpp` starts `processor_.run()` on a `std::async` future, lets `dram_read`/`dram_write` reach `ram_` without waiting on it, and guards only `vortex_dcr_read` with `future_.wait()`. We were ready to report that as the bug. `sw/runtime/simx/vortex.cpp` has the identical structure, down to the same comment, and `simx` does not reproduce. It may still be worth a look on its own merits, but it does not explain this.

**The corruption is finer than a cache line.** On the launch that asserts, the kernel's 4-byte load at struct offset 0 returns the correct value and passes the kernel's own guard, while the 8-byte pointer at offset 8 does not. Both fields are inside one 16-byte struct and one 64-byte line.

## What that leaves

grxcp is exonerated: it hands the same blob to the same `vx_enqueue_launch` on both backends. So is everything the two backends share, which includes `sim/common/cmd_processor.cpp` — where the blob is staged by `CMD_MEM_WRITE` — and `sw/runtime/common/utils.cpp`.

What is left is `sw/runtime/rtlsim/vortex.cpp`, the Verilated model, or the RTL. We have not narrowed it further and are not going to guess between them.

One thing we would look at first, offered as a suggestion and not a finding: this configuration runs `DCACHE_WRITEBACK=1` with `L2_ENABLED=0`, so there is no shared level below the per-core L1s. A build with the dcache disabled would say whether that matters, and you can run it faster than we can.

## The assertion, which is the useful part

```plaintext
VX_lsu_slice.sv:233: misaligned memory access, wid=0,
PC=0x180001b80, addr=0x100000001, wsize=2


```

`PC=0x180001b80` disassembles to `sw a2,0(a0)`, where `a0` came from `ld a0,8(a0)` — the pointer field of the argument struct. The kernel passed its version guard and then stored through a pointer that was never delivered.

**This assertion is the only reason we found any of it.** `simx` executes the same access on the same binary and says nothing, on every configuration we tried. Our own FPGA path is worse in the same direction: it rounds unaligned transfers up to 64 bytes with all strobes set, which is silent corruption rather than a stop. Misalignment is invisible on the functional model, corrupting on FPGA, and fatal on RTL, and only the last one tells you. Please keep `RUNTIME_ASSERT` where it is.

## What we changed on our side

Nothing that works around this — a workaround would hide it.

One thing did need fixing, and it is ours. Our grxBLAS asks the loaded module for its tile geometry at startup and treats an unwritten buffer as "this module does not report geometry", falling back to a reference kernel. That is correct for an older module and wrong for a device that dropped the arguments, and from the host the two are indistinguishable. The effect on a two-core build was that grxBLAS silently stopped using its blocked kernels, computed correct answers by the slow path, and said nothing — and no correctness gate could see it, because the fallback is correct. It now prints which module went quiet and names both possible causes. That message is how we noticed the two-core case at all.

## What would help

1. Confirmation that you reproduce it — one kernel, launched twice, arguments checked both times, at `NUM_CORES=2`.
2. Whether `NUM_CORES > 1` is expected to work in `rtlsim` today. If it is known-broken we will stop treating multi-core numbers as measurable and say so in our roadmap rather than chasing it.
3. Nothing else is blocked on this that we can do ourselves. Every performance number we hold today was measured on one core, which is a fact about our numbers we would rather state than discover later.
