# GRXGPU TCU — Fabrication Readiness Gap Analysis

**Date:** September 3, 2026
**Scope:** TCU (Tensor Compute Unit) with WGMMA, DXA, TFR
**Target:** ASIC fabrication (or advanced FPGA prototyping)

---

## Executive Summary

The TCU design is **simulation-complete** (SimX) and **logic-synthesis-complete** (Yosys). However, several critical gaps must be closed before fabrication. The most urgent are:

1. **Multi-core rtlsim bug** — GRXCP team is working on the fix
2. **No place-and-route results** — Yosys only gives logic synthesis, not physical layout
3. **No timing analysis** — We don't know if the design meets timing at target frequency
4. **No FPGA prototyping** — Never tested on real hardware
5. **TGM correctness at K>16** — SimX has bugs in the self-pipelining FSM

---

## Gap Matrix

| Category | Status | Gap | Priority | Owner |
|----------|--------|-----|----------|-------|
| **RTL Design** | ✅ Complete | 41 TCU modules, all interfaces defined | — | grxgpu |
| **SimX Simulation** | ⚠️ Partial | TGM correctness at K>16 broken | P1 | grxgpu |
| **RTL Simulation** | ❌ Blocked | Multi-core rtlsim bug (GRXCP) | P0 | GRXCP |
| **Logic Synthesis** | ✅ Complete | ECP5 + Xilinx 7 results | — | grxgpu |
| **Place-and-Route** | ❌ Missing | No P&R results for any target | P0 | grxgpu |
| **Timing Analysis** | ❌ Missing | No setup/hold analysis | P0 | grxgpu |
| **Power Estimation** | ❌ Missing | No power numbers | P1 | grxgpu |
| **FPGA Prototyping** | ❌ Missing | Never tested on real hardware | P0 | grxgpu |
| **Formal Verification** | ❌ Missing | No equivalence checking | P1 | grxgpu |
| **Test Coverage** | ⚠️ Partial | 22 TCU tests, no corner-case coverage | P1 | grxgpu |
| **Documentation** | ⚠️ Partial | Design doc exists, no timing/power specs | P2 | grxgpu |

---

## Detailed Gap Analysis

### 1. Multi-Core RTL Simulation (P0 — Blocking)

**Status:** GRXCP team is working on the fix

**Issue:** `rtlsim` loses kernel arguments on every other launch at `NUM_CORES > 1`

**Root cause:** `dram_write` stages arguments while previous `run()` is still accessing `ram_` via the Verilated memory bus

**Fix:** Serialize `vortex_start` with `future_.wait()` before launching

**Impact:** Multi-core configurations are unusable until this is fixed. All performance numbers at `NUM_CORES > 1` are suspect.

**Next step:** Wait for GRXCP team's fix, then re-run the full test suite at `NUM_CORES=2` and `NUM_CORES=4`

---

### 2. TGM Correctness at K>16 (P1)

**Status:** SimX has bugs in the TGM FSM

**Issue:** The self-pipelining TGM instruction (Phase 2 of the tensor engine proposal) produces incorrect results at K>16. The COMPUTE phase's per-lane A-slice handling and fragment accumulation have off-by-one errors.

**Current state:**
- K=16: PASSED (IPC=0.395)
- K=512: 3072 errors (warps 1-3 wrong, warp 0 correct, constant -0.001327 offset)

**Impact:** TGM is the key innovation for eliminating per-iteration instruction overhead. Until it works, the software K-loop is the only option.

**Next step:** Debug the COMPUTE phase's per-warp A-slice and per-lane fragment accumulation

---

### 3. Place-and-Route (P0 — Blocking)

**Status:** ❌ Missing

**What we have:**
- Yosys logic synthesis: 2963 LUT4 + 1324 FF (ECP5), 2522 LUT6 + 1288 FF (Xilinx 7)

**What we need:**
- Lattice ECP5-85F P&R with timing closure
- Xilinx Kintex-7 P&R with timing closure
- ASIC target (if applicable): TSMC/Samsung PDK, standard cell library

**Impact:** Without P&R, we don't know:
- Actual clock frequency achievable
- Routing congestion
- Hold time violations
- Total die area

**Next step:** Run Lattice Trellis P&R on ECP5, or Vivado P&R on Kintex-7

---

### 4. Timing Analysis (P0 — Blocking)

**Status:** ❌ Missing

**What we need:**
- Setup time analysis at target frequency (e.g., 200 MHz for ECP5, 500 MHz for Kintex-7)
- Hold time analysis
- Clock tree synthesis
- Multi-corner analysis (fast/slow corners)

**Impact:** Without timing analysis, we don't know if the design can run at the target frequency. The TFR pipeline has 3 stages; at 200 MHz (5 ns period), each stage must complete in <5 ns.

**Next step:** Run static timing analysis after P&R

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
- K=16 and K=512 smoke tests pass
- K=512 full GEMM passes at 512×512×512

**What we're missing:**
- Corner cases (K=1, K=2, K=4, odd K values)
- Edge cases (M=1, N=1, very large M/N)
- Stress tests (maximum CTA count, maximum K)
- Error injection tests (memory corruption, timeout)
- Multi-precision tests (bf16×bf16→fp32, int8×int8→int32)

**Next step:** Write corner-case tests for K=1, K=2, K=4, and odd K values

---

## Recommended Priority Order

### Phase 1: Fix Blocking Issues (Week 1-2)

1. **Wait for GRXCP multi-core fix** — then re-run full test suite
2. **Fix TGM correctness at K>16** — debug COMPUTE phase
3. **Run FPGA P&R** — generate bitstream for ECP5

### Phase 2: Validate on Hardware (Week 3-4)

4. **FPGA prototyping** — test on real hardware
5. **Timing analysis** — verify setup/hold at target frequency
6. **Power estimation** — measure dynamic/static power

### Phase 3: Hardening (Week 5-6)

7. **Formal verification** — write assertions, run equivalence checking
8. **Corner-case tests** — K=1, K=2, K=4, odd K, stress tests
9. **Documentation** — timing specs, power specs, interface specs

### Phase 4: Fabrication Prep (Week 7-8)

10. **ASIC P&R** (if applicable) — target PDK, standard cells
11. **Final timing closure** — multi-corner analysis
12. **Tapeout checklist** — DRC, LVS, antenna rules

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Multi-core bug takes longer than expected | Medium | High | Focus on single-core path first |
| TGM correctness is architectural | Low | High | Fall back to software K-loop |
| Timing closure fails at target frequency | Medium | High | Reduce pipeline stages, lower frequency |
| FPGA resource exhaustion | Low | Medium | Optimize LUT usage, use DSP blocks |
| Power exceeds thermal budget | Low | Medium | Clock gating, power domains |

---

## What's Working Today

Despite the gaps, the following are **validated and working**:

| Component | Status | Evidence |
|-----------|--------|----------|
| TFR (tensor fused-reduce) | ✅ | ECP5 synthesis: 3616 LUT4 + 513 FF |
| Full TCU hierarchy | ✅ | ECP5 synthesis: 2963 LUT4 + 1324 FF |
| WGMMA at K=512 | ✅ | 512×512×512 fp16 GEMM passes |
| Double-buffer DXA | ✅ | IPC improved from 0.608 to 0.804 (+32%) |
| Fused A+B descriptor | ✅ | Phase 1 implemented, reduces issue overhead |
| bf16 support | ✅ | Test exists, RTL has bf16 paths |
| SimX performance model | ✅ | IPC 1.345 at 512³, gate stall breakdown |

---

*Analysis prepared by the grxgpu team. Commit `93c118e89` on main.*
