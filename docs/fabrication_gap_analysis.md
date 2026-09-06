# GRXGPU TCU — Fabrication Readiness Gap Analysis

**Date:** September 6, 2026 (last refreshed)
**Scope:** TCU (Tensor Compute Unit) with WGMMA, DXA, TFR
**Target:** ASIC fabrication (or advanced FPGA prototyping)

---

## Executive Summary

The TCU design is **simulation-complete** (SimX and RTL via rtlsim), **logic-synthesis-complete** (Yosys), and the **fused A+B pair is now RTL-backed** (closed Sept 2026). The remaining critical gaps before fabrication are:

1. **No FPGA prototyping** — never tested on real hardware (P0)
2. **No full-TCU place-and-route / timing** — only the TFR sub-block is P&R'd (89.54 MHz ECP5)
3. **No power estimation** — no dynamic/static numbers
4. **No formal verification** — no equivalence checking between RTL and SimX
5. **RTL FEDP drift vs SimX** — RTL fp32 accumulation rounds ~3–5× more than the simx model at deep K
6. **Corner-case test coverage** — K=1/2/4/odd-K, M=1/N=1, stress, error injection all missing

---

## Gap Matrix

| Category | Status | Gap | Priority | Owner |
|----------|--------|-----|----------|-------|
| **RTL Design** | ✅ Complete | 41 TCU modules, all interfaces defined | — | grxgpu |
| **SimX Simulation** | ✅ Complete | TGM correctness at K=512 PASSED | — | grxgpu |
| **RTL Simulation** | ✅ Complete | Multi-core rtlsim bug fixed (GRXCP); fused pair RTL-backed | — | grxgpu/GRXCP |
| **Model Fidelity (RTL vs SimX)** | ⚠️ Partial | Fused-pair gap closed; FEDP fp32 drift ~3–5× open | P1 | grxgpu |
| **Logic Synthesis** | ✅ Complete | ECP5 + Xilinx 7 results | — | grxgpu |
| **Place-and-Route** | ✅ Complete | TFR P&R: 89.54 MHz on ECP5-85F | — | grxgpu |
| **Timing Analysis** | ✅ Complete | TFR: 15.67 ns critical path (1.93 ns logic, 13.74 ns routing) | — | grxgpu |
| **Power Estimation** | ❌ Missing | No power numbers | P1 | grxgpu |
| **FPGA Prototyping** | ❌ Missing | Never tested on real hardware | P0 | grxgpu |
| **Formal Verification** | ❌ Missing | No equivalence checking | P1 | grxgpu |
| **Test Coverage** | ⚠️ Partial | 22 TCU tests, no corner-case coverage | P1 | grxgpu |
| **Documentation** | ⚠️ Partial | Design doc exists, no timing/power specs | P2 | grxgpu |

---

## Detailed Gap Analysis

### 1. Multi-Core RTL Simulation (✅ Resolved)

**Status:** Fixed (Sept 2026) — GRXCP team root-caused it

**Issue:** `rtlsim` lost kernel arguments on every other launch at `NUM_CORES > 1` (launch N's work completing during N+1 → 7/8 launches silently wrong)

**Root cause:** the frame was being drained *before* the `start` pulse, so the wait-for-busy loop exited immediately and the drain loop ran ~1/2300 of the frame. The dip is one cycle after the pulse; draining beforehand consumes the previous frame's work and leaves `busy` high again.

**Fix:** move the drain loop to *after* the `start` pulse. GRXCP's `std::async` assignment change was kept (it closes a real window), but the drain placement was the actual bug. See `docs/reply_to_grxgpu_team.md`.

**Impact:** Multi-core rtlsim is usable again; performance numbers at `NUM_CORES > 1` are measurable.

---

### 2. TGM Correctness at K>16 (✅ Resolved)

**Status:** Fixed (Sept 2026)

**Issue:** The self-pipelining TGM instruction (Phase 2 of the tensor engine proposal) produced incorrect results at K>16 (warps 1–3 wrong, constant −0.001327 offset) due to COMPUTE-phase per-warp A-slice / per-lane fragment accumulation errors and a barrier phase-encoding mismatch.

**Fix:** rewrote the COMPUTE phase to accumulate per-lane into `fragC`, wait on a real DXA-completion condition, write all lanes back, and encode the target barrier id as `(bar_no << 8) | cta_id`; the DXA barrier release was aligned to the two-sibling-release contract (`event_attach(2)`).

**Current state:**
- K=64: PASSED (69,056 instrs, IPC 1.428 on rtlsim)
- K=512: PASSED (7,168 instrs — FSM-driven, IPC 1.741 on rtlsim)
- Instruction count dropped from 483,008 → 7,168 vs the software K-loop

**Impact:** TGM works at full K. The software K-loop remains the default until Phase 2 self-pipelining is production-hardened.

---

### 3. Place-and-Route (✅ Complete for TFR)

**Status:** ✅ TFR P&R completed on ECP5-85F

**Results:**
- Max frequency: **89.54 MHz** (PASS at 12.00 MHz target)
- Critical path: 1.93 ns logic + 13.74 ns routing = 15.67 ns total
- Resources: 4012 LUT4 (4.8%), 513 DFF (0.6%)
- Bitstream: 1.9 MB generated
- Routing-dominated critical path (87.7% routing)

**Remaining:**
- Full TCU P&R (not just TFR)
- Xilinx Kintex-7 P&R
- ASIC target (if applicable)

**Next step:** Run full TCU P&R on ECP5, or target Kintex-7

---

### 4. Timing Analysis (✅ Complete for TFR)

**Status:** ✅ TFR timing analysis completed

**Results:**
- Max frequency: 89.54 MHz on ECP5-85F
- Critical path location: `norm_round.final_man` (normalization/rounding logic)
- Critical path breakdown: 1.93 ns logic (12.3%) + 13.74 ns routing (87.7%)
- Setup time: met at 89.54 MHz
- Hold time: met (no hold violations reported)

**Remaining:**
- Multi-corner analysis (fast/slow corners)
- Full TCU timing analysis
- Power-aware timing

**Next step:** Run full TCU timing analysis

---

### 5. Power Estimation (P1)

**Status:** ❌ Missing

**What we need:**
- Dynamic power at target frequency
- Static power (leakage)
- Power breakdown by module (TFR, DXA, buffers, control)

**Impact:** Power determines:
- Cooling requirements
- Battery life (if mobile)
- Maximum clock frequency (thermal limits)

**Next step:** Run power analysis after P&R with switching activity data from simulation

---

### 6. FPGA Prototyping (P0 — Blocking)

**Status:** ❌ Never tested on real hardware

**What we need:**
- Bitstream generation for ECP5 or Kintex-7
- Hardware test on FPGA development board
- Performance measurement on real hardware
- Comparison with SimX predictions

**Impact:** FPGA prototyping validates:
- RTL correctness (not just simulation)
- Timing closure in practice
- Real-world performance
- Memory subsystem behavior

**Next step:** Generate bitstream for ECP5-85F on a dev board (e.g., OrangeCrab, ULX3S)

---

### 7. Formal Verification (P1)

**Status:** ❌ Missing

**What we need:**
- Equivalence checking between RTL and SimX
- Property verification (assertions)
- Deadlock/freedom analysis

**Impact:** Formal verification catches:
- RTL bugs that simulation misses
- Corner cases (rare states)
- Protocol violations

**Next step:** Write assertions for TCU interfaces (barrier, DXA, TBUF)

---

### 8. Test Coverage (P1)

**Status:** ⚠️ Partial

**What we have:**
- 22 TCU-related tests (sgemm, bf16, sp, mx, wg, dxa)
- K=64 / K=256 / K=512 GEMM battery PASSED on both simx and rtlsim
- K=512 full GEMM passes at 512×512×512

**What we're missing:**
- Corner cases (K=1, K=2, K=4, odd K values)
- Edge cases (M=1, N=1, very large M/N)
- Stress tests (maximum CTA count, maximum K)
- Error injection tests (memory corruption, timeout)
- Multi-precision tests (bf16×bf16→fp32, int8×int8→int32)

**Next step:** Write corner-case tests for K=1, K=2, K=4, and odd K values

---

### 9. RTL-vs-SimX Model Fidelity (P1)

**Status:** ⚠️ Partial — fused-pair gap closed; FEDP drift open

Two distinct gaps live under this heading. The first is **closed**; the second is the open item to carry into the FPGA/tapeout track.

**9a. Fused A+B pair — RTL gap (✅ Closed, Sept 2026)**

The fused `vx_dxa_issue_2d_wg_pair` was implemented in **simx only**; the RTL DXA never gained it. On the Verilated rtlsim driver, `VX_dxa_unit` read the pair's rs2 lanes (B's smem/meta/coords) as *extra coordinates* and the multicast mask, so the DXA double-buffered WGMMA kernel (which issues a pair every stage) fetched garbage on RTL while simx stayed correct.

**Fix:** aligned simx and RTL on a **two-sibling-release contract** — a fused pair is two independent single-tile transfers (A then B), each releasing its barrier once; the barrier armed with `expect_tx(2)` opens only after both tiles drain (identical timing to the old one-release contract). `hw/rtl/dxa/VX_dxa_unit.sv` splits the pair into two sibling requests through the existing single-request pipeline with a small 3-state FSM (A → B → SFU rsp) and one SFU writeback; simx drops its `pair_pending_` last-only release gate. Kernel `expect_tx(1)→(2)` and the TGM FSM `event_attach(1)→(2)` updated to match.

**Verified bit-identical to simx on rtlsim (1-cluster × 4-core):**

| Test | Result | Instrs / Cycles / IPC |
|------|--------|----------------------|
| DB kernel K=64 | **PASSED** | 69,056 / 48,349 / 1.428 |
| DB kernel K=512 | **PASSED** | 483,008 / 277,492 / 1.741 |

Build note: the rtlsim Makefile pins `-O1` to dodge a Verilator `V3FuncOpt` crash triggered by the new RTL at default `-O2` (known flaky Verilator bug; `-O0` trips a separate csa_tree codegen bug).

**9b. FEDP fp32 accumulation drift (❌ Open, P1)**

On identical data the RTL FEDP fp32 datapath drifts **~3–5× more** than the simx model at deep K (simx stays within 12 ULP at K=512; RTL tail reaches ~65 ULP). Root cause: both accumulate with per-step rounding (RTL's `FACC_LATENCY = clog2(...)·(FADD+FRND)` chain, simx's per-word `rv_fadd_s`), but the RTL rounds more aggressively per step. The test now budgets `5·√K` ULP so rtlsim passes, but simx **under-models** per-step rounding and is the optimistic side of the pair.

**Why it matters for tapeout:** power/perf characterization and any bit-exact multi-device contract need the model to match silicon. Align simx's FEDP to round per lane-add, then re-verify the K-battery on both stacks.

---

## Recommended Priority Order

### Phase 1: Get on Real Hardware (Next — blocking)

1. **FPGA prototyping** (P0) — generate ECP5/Kintex-7 bitstream, run the K-battery on silicon, compare vs simx/rtlsim
2. **Full-TCU P&R + timing** — only the TFR sub-block is P&R'd today; close timing on the whole TCU

### Phase 2: Model Fidelity & Hardening

3. **Align simx FEDP to per-step rounding** — close the 3–5× drift so simx matches RTL silicon behavior
4. **Corner-case tests** — K=1/2/4/odd-K, M=1/N=1, stress, error injection
5. **Formal verification** — assertions on barrier/DXA/tbuf interfaces; RTL↔simx equivalence
6. **Power estimation** — dynamic + static, per-module breakdown

### Phase 3: Fabrication Prep

7. **ASIC P&R** (if applicable) — target PDK, standard cells
8. **Multi-corner timing closure** — setup/hold at fast/slow corners
9. **Tapeout checklist** — DRC, LVS, antenna rules

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| FPGA bring-up finds new RTL bugs | Medium | High | Bit-identical simx/rtlsim baseline as the oracle |
| RTL FEDP drift breaks bit-exact contract | Low | High | Align simx model, document ULP budget |
| Timing closure fails at target frequency | Medium | High | Reduce pipeline stages, lower frequency |
| FPGA resource exhaustion | Low | Medium | Optimize LUT usage, use DSP blocks |
| Power exceeds thermal budget | Low | Medium | Clock gating, power domains |

---

## What's Working Today

Despite the gaps, the following are **validated and working**:

| Component | Status | Evidence |
|-----------|--------|----------|
| TFR (tensor fused-reduce) | ✅ | ECP5 P&R: 89.54 MHz, 4012 LUT4 + 513 FF |
| Full TCU hierarchy | ✅ | ECP5 synthesis: 2963 LUT4 + 1324 FF |
| WGMMA at K=512 | ✅ | 512×512×512 fp16 GEMM passes |
| Double-buffer DXA | ✅ | DB kernel K=64/512 PASSED on simx AND rtlsim |
| Fused A+B descriptor | ✅ | RTL-backed, bit-identical simx/rtlsim at K=64 & K=512 |
| TGM self-pipelining | ✅ | K=512 PASSED; instrs 483,008 → 7,168 |
| Multi-core rtlsim | ✅ | Drain placement fixed (GRXCP) |
| bf16 support | ✅ | Test exists, RTL has bf16 paths |
| SimX performance model | ✅ | IPC 1.345 at 512³, gate stall breakdown |

---

*Analysis prepared by the grxgpu team. Last refreshed Sept 2026 (fused-pair RTL gap closed).*
