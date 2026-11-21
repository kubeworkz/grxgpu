# G100-T0 G3 Evidence Record — Entry Baseline and Test Index

**Status:** **OPEN — entry only.** No test has run and no result is claimed.
This record fixes the entry baseline, the accountable owners, and the test
index that G3 evidence will be filed against. It is not a gate decision.
**Gate:** G3 — functional and software hardening
([production plan](../../grxgpu_production_plan.md) §3).
**Plan:** [G100-T0 G3 Functional and Software Hardening Plan](../../proposals/g100_t0_g3_hardening_plan.md).
**Contract:** [G100-T0 v1 Interface Contract](../../proposals/g100_t0_interface_contract.md),
Approved v1.0 on 2026-11-21.
**Scope:** the G100-T0 engineering die only. Commercial G0 remains on HOLD;
this record does not authorize G4 purchases, G5 implementation, G6 tapeout, or
production release.
**Prepared by:** engineering agent supporting the G100-T0 program, 2026-11-21.
The author is not an approver and does not sign the G3 record.

---

## 1. Entry baseline

| Item | Entry value | State |
|---|---|---|
| Contract | v1.0, approved 2026-11-21; SHA-256 `6eed0cc55917238346446f2fe5c36b8dc1324cad5d733af5f26f432a0b4bd38d` | Approved; G2 PASS ([G2 gate record](../g100-t0-g2-2026-11-21/gate-record.md)) |
| Frozen workload | `G100-T0-G2-SGEMM-1.0`, `sgemm_tcu_wg_dxa`, M=N=64, K=64/512, FP16→FP32, `WGMMA_NRC=16` | Frozen ([manifest](../g100-t0-g2-2026-11-21/golden-workload.md)) |
| Golden corpus | Six files; SHA-256 in [`golden/SHA256SUMS`](../g100-t0-g2-2026-11-21/golden/SHA256SUMS) | Frozen and verified at G2 |
| Edge-shape workloads | `G100-T0-G3-SGEMM-M16N16K8-1.0` and `G100-T0-G3-SGEMM-M32N16K8-1.0`; references and hashes in [edge-workloads.md](edge-workloads.md) | Generated; no device run; T-G-5f OPEN |
| Source pin | `ff550c27570f17b0c8242be42257043d3de4ffa7`, tree `cf6b2f8657fcba985dd9007fa403231c3d800301` | Pinned; no T0 device build |
| T0 configuration | Proposed `CONFIGS`; resolver SHA-256 `cd5336232fa98454009574121e0b25cc98feb3530a50675874ba98738c154cda` | Proposed at G1; not exercised |
| G1 audit | [G1 evidence audit](../../grxgpu_g100_t0_g1_evidence_audit.md) | **NOT PASSED** at 2026-11-20; unchanged by this record |
| ECC S0 | [S0 decision signoff](../g100-t0-ecc-s0-2026-11-20/signoff.md) | Unsigned; G-6 cannot start RTL |
| Board / FPGA | None for T0 | L4 evidence cannot be produced |
| Plan commits | Entry `2336f90140a13489e24c16b669962b22f8ee893a`, `docs: plan the G100-T0 G3 hardening work`; coverage amendment `86f081ba8`, `docs: extend the G100-T0 G3 coverage plan` | Committed with this record |
| Branch | `ci/runner-health-retries` | Four commits ahead of origin at entry; not pushed |
| Evidence dir | `docs/evidence/g100-t0-g3-2026-11-21/` | Created with this record; no logs yet |

**Corpus identities.** These are the hashes G3 must reproduce before comparing
any device output; the manifest's `SHA256SUMS` is authoritative.

| File | SHA-256 |
|---|---|
| `g100t0_sgemm_m64n64k64_A.fp16` | `985ef83fe0802e90a08fe2023822dc0b31e83aeb66df9051f688c3e694b468a8` |
| `g100t0_sgemm_m64n64k64_B.fp16` | `ad975434b9327b5dfe37f36e7e09e703253dce2bb80ece322797a17ff9356270` |
| `g100t0_sgemm_m64n64k64_C.fp32` | `73a1a0eacd81d64cd451919493da3d9187f418b563e4c52b1f6a8ba68b5ad240` |
| `g100t0_sgemm_m64n64k512_A.fp16` | `70dcc14a134e620c9b5d4be7dbbd01a64e6bb5efdf4fa8b6f432533bd735cfac` |
| `g100t0_sgemm_m64n64k512_B.fp16` | `59fb1324bbfcff9c943fa7ab25b4a2ce0db7be7dec2787eb41c71d4552759cb9` |
| `g100t0_sgemm_m64n64k512_C.fp32` | `d07043551fa7efeae970533f5e86c02af8062ab5bed82e38c68e161fe67628c9` |

G3 starts from a known interface and corpus, not from a known-good device.
The G1 audit remains **NOT PASSED**; entry into G3 does not waive it, and no
G1 evidence is inherited by the tests below.

---

## 2. Evidence owners

Owners produce the raw log, hash it, and file the record. Approval is separate:
the author cannot sign their own evidence, and Gridworkz records the gate
decision. The plan's test IDs name one accountable owner; co-owners support
the test but do not replace that accountability.

| Role | Accountable for | Plan rows |
|---|---|---|
| Bring-up lead | JTAG/TAP, boot/KMU, reset domains, recovery procedure | IF-01, IF-06, IF-11, S-6 |
| Verification lead | SBA/DMI, memory window, core attach, DXA/TLMem, ECC, golden comparison, parity, coverage and defect closure | IF-02–IF-05, IF-07, IF-09, IF-14, G-1, G-2, G-4–G-6, S-4, S-5, T-V-1, T-V-2, T-RC-1 |
| Software/runtime lead | CP ring ABI, DXA descriptor encoders, diagnostics, CP fault contract, operator scope | IF-08, IF-10, G-3, S-2, S-3, S-7b |
| System/SoC architect | DXA attach, 16-core integration, ECC decode contract | G-4, G-5, G-6 (with Verification) |
| Physical design (G4 role) | Synthesis and STA at the target library, TCK-domain timing | G-7 (STA) |
| Power/thermal lead | Board power, ambient, θJA and Tj measurement | IF-12, G-7 (measurement) |
| Package/board lead | Pin budget, package requirements, PDK/sourcing input | IF-13, G-8 |
| Build/release + RTL lead | Reproducible build, build stamp, configuration identity, compiler path | S-1, S-7a |

No owner is named as a person yet. A role owns the evidence; a named person
must sign it before the G3 record can cite it.

---

## 3. Test ID index

The plan is authoritative for each test's method and exit criterion; this
index is the filing key. **All 75 entries are OPEN — none has a log, and no
result is recorded in this document.**

### 3.1 Interfaces

| Test ID | Scope | Tier | Accountable owner |
|---|---|---|---|
| T-IF-01a | IR walk, IDCODE, BYPASS/DTMCS/DMI | L1 | Bring-up |
| T-IF-01b | `TRST_n` resets TAP only | L1 | Bring-up |
| T-IF-02a | DMI busy → `op=3`, sticky `dmistat=3` | L1 | Verification |
| T-IF-02b | Reserved DMI address → status 2 | L1 | Verification |
| T-IF-03a | SBA error codes 2/3/4 | L1 | Verification |
| T-IF-03b | SBA timeout=1 and W1C clear | L1 | Verification |
| T-IF-03c | Second access sets `sbbusyerror`, dropped | L1 | Verification |
| T-IF-04a | 4096-line address uniqueness walk | L1 | Verification |
| T-IF-04b | 64-bit byte-enable matrix | L1 | Verification |
| T-IF-04c | Window edge and alias probe | L1 | Verification |
| T-IF-05a | Boot-image load and readback | L1 | Verification |
| T-IF-05b | `ndmreset` mid-fetch | L1 | Verification |
| T-IF-05c | Core store then SBA read | L1 | Verification |
| T-IF-06a | 20-DCR boot trace | L1 | Bring-up |
| T-IF-06b | Forced no-busy boot timeout | L1 | Bring-up |
| T-IF-06c | `boot_en=0` core hold | L1 | Bring-up |
| T-IF-07a | DXA tile read into LMEM | L2 | Verification |
| T-IF-07b | Eight outstanding reads and credit recovery | L2 | Verification |
| T-IF-07c | Stalled-response watchdog assertion | L2 | Verification |
| T-IF-08a | Descriptor encoder/decoder equivalence | L0/L2 | Software |
| T-IF-08b | Descriptor slot isolation, 16 slots | L0/L2 | Software |
| T-IF-09a | DXA/TCU LMEM contention and priority | L2 | Verification |
| T-IF-09b | Barrier completion | L2 | Verification |
| T-IF-10a | CP ring encoder/decoder round-trip | L0 | Software |
| T-IF-10b | Overpack rejection above 5 commands/line | L0 | Software |
| T-IF-10c | Capability gating for `0x0B`/`0x0C` | L0 | Software |
| T-IF-11a | Five-source reset-domain matrix | L1 | Bring-up |
| T-IF-11b | `core_reset` truth table | L1 | Bring-up |
| T-IF-11c | DMI clock-domain crossing check | L1 | Bring-up |
| T-IF-12a | Power/thermal record at stated ambient | L4 where available | Power/thermal |
| T-IF-13a | Pin-budget reconciliation at `VX_MEM_PORTS=0` | L0 | Package/board |
| T-IF-13b | Package requirement record | L0 | Package/board |
| T-IF-14a | Corpus regeneration and hash match | L0 | Verification |
| T-IF-14b | C comparison within ULP budget | L0/L2/L3 | Verification |

### 3.2 Open conformance items

| Test ID | Scope | Tier | Accountable owner |
|---|---|---|---|
| T-G-1a | Drain reaches idle within the approved bound | L1 | Verification (+RTL) |
| T-G-1b | `ndmreset` mid-read and mid-write | L1 | Verification |
| T-G-1c | Timeout/reset fuzz with bound assertion | L1 | Verification |
| T-G-2a | SBA access below, above and in the gap | L1 | Verification |
| T-G-2b | Core access to unmapped addresses | L1 | Verification |
| T-G-2c | SRAM-select window and one-slave assertion | L1 | Verification |
| T-G-2d | DXA out-of-bounds remains clamp-plus-`cfill` | L2 | Verification |
| T-G-3a | Malformed CP command, sticky fault, recovery | L0/L3 | Software (+Verification) |
| T-G-3b | Byte-exact DMA tail, lengths 1–4096 | L0/L3 | Software (+Verification) |
| T-G-3c | FENCE ordering, or removal | L0/L3 | Software (+Verification) |
| T-G-4a | DXA read of a 64 × 64 FP16 tile from test SRAM | L2 | System/SoC |
| T-G-4b | SBA/core/DXA arbitration and starvation bound | L2 | System/SoC |
| T-G-4c | DXA watchdog on non-responding SRAM | L2 | Verification |
| T-G-5a | Elaborate and lint 1 cluster × 16 cores | L2 | System/SoC |
| T-G-5b | Boot 16 cores, 16/16 result words | L2 | System/SoC |
| T-G-5c | Frozen workload at the full 16-CTA grid | L2 | Verification |
| T-G-5d | Relaunch and SBA backpressure | L2 | Verification |
| T-G-5e | Cache/coherency characterization | L2 | System/SoC |
| T-G-5f | Supported edge shapes (M,N % 16=0; K % 8=0), each a new workload with a recorded ULP budget; M=N=64 K=8/24 via frozen generator; 16×16×8 and 32×16×8 via [gen_golden_dims.cpp](golden/gen_golden_dims.cpp) with hashes in [edge-workloads.md](edge-workloads.md); unsupported multiples rejected | L2/L3 | System/SoC (+Verification) |
| T-G-6a | ECC S0 signature (D1–D14) | Record | Verification |
| T-G-6b | Codec and ECC-bank wrapper benches | L0 | Verification |
| T-G-6c | LMEM and cache integration cases | L0/L2 | Verification |
| T-G-6d | Injection and counter readout over SBA | L1 | Verification |
| T-G-6e | TSRAM-only evidence scope recorded | Record | Verification |
| T-G-7a | STA at 400 MHz on the target library | STA | Physical design |
| T-G-7b | TCK-domain and DMI CDC timing at 10 MHz | STA | Physical design |
| T-G-7c | Board power/thermal measurement | L4 | Power/thermal |
| T-G-8a | Pin budget and thermal pad | L0 | Package/board |
| T-G-8b | Package requirement record | L0 | Package/board |
| T-G-8c | PDK/library availability and licence | G4 | Package/board (+sourcing) |

### 3.3 Software hardening

| Test ID | Scope | Tier | Accountable owner |
|---|---|---|---|
| T-S-1 | Two clean builds, byte compare, build stamp | Build | Build/release (+RTL) |
| T-S-2 | DXA/CP ABI suite against pinned RTL constants | L0/L2 | Software |
| T-S-3 | Injected SBA timeout, boot error, bad descriptor | L1 | Software |
| T-S-4 | SimX/rtlsim model parity on the frozen workload | L3 | Verification |
| T-S-5 | Golden-run runner with A/B hash precondition | L2/L3 | Verification |
| T-S-6 | Reload-over-SBA recovery, twice | L1 | Bring-up |
| T-S-7a | Pinned-toolchain rebuild of the frozen kernel and one other kernel | Build | Build/release (+Software) |
| T-S-7b | Operator scope: supported list tested, or explicit T0 exclusion | Record | Software |

### 3.4 Verification closure

| Test ID | Scope | Tier | Accountable owner |
|---|---|---|---|
| T-V-1 | Functional coverage review and written waivers | Record | Verification |
| T-V-2 | Critical-defect log and zero-open-critical exit | Record | Verification (+RTL) |
| T-RC-1 | Release-candidate checklist audit, including the RC-2 firmware and RC-8 supported-model-path exclusions | Record | Verification (+Software, Build/release) |

---

## 4. Open carries at entry

G-7 and G-8 are listed as open carries. Listing them is not closure, a waiver,
or a gate disposition; the G3 record will state the evidence obtained and the
approver decides pass, conditional pass, or hold.

| Item | What remains open | Accountable owner | Closes at |
|---|---|---|---|
| G-7 | STA at 400 MHz on the target library; TCK-domain timing; board power/thermal measurement where hardware exists | Physical design (STA); Power/thermal (measurement) | G4 library selection for STA; first board or silicon for measurement |
| G-8 | Package selection, pin numbers, PDK and library access | Package/board, with sourcing | G4 |

No T0 board exists at entry, so T-IF-12a and T-G-7c cannot produce a
measurement. The absence is recorded here rather than treated as a pass or a
failure.

---

## 5. Filing rules

1. **No result without a log.** A row moves from OPEN to PASS or FAIL only when
   the plan's eight record fields are present and the raw log with its SHA-256
   is filed in this directory.
2. **No self-signoff.** The evidence owner role and the approver are separate;
   the author of this record cannot approve it.
3. **Revision-gated tests do not run early.** T-G-3a–c wait for the v1.x
   revision described in the plan; a run against the current RTL would record
   a known non-conformance, not progress.
4. **ECC RTL waits for S0.** T-G-6b–d do not start before the S0 decisions are
   signed.
5. **Tier claims stay tiered.** An L2 pass is not an L4 pass, and SimX output
   is not a device result.
6. **Manifest last.** `SHA256SUMS` for this directory is added with the first
   filed log and updated with each new log; it does not exist yet.
7. **Coverage and defect records close the gate.** T-V-1 and T-V-2 are record
   audits, not test runs; they are complete only when every critical coverage
   bin is covered or waived and no critical defect is open.

---

## 6. Document index

| Artifact | Path |
|---|---|
| G3 hardening plan | [`../../proposals/g100_t0_g3_hardening_plan.md`](../../proposals/g100_t0_g3_hardening_plan.md) |
| v1 interface contract | [`../../proposals/g100_t0_interface_contract.md`](../../proposals/g100_t0_interface_contract.md) |
| G2 gate record | [`../g100-t0-g2-2026-11-21/gate-record.md`](../g100-t0-g2-2026-11-21/gate-record.md) |
| Frozen workload manifest | [`../g100-t0-g2-2026-11-21/golden-workload.md`](../g100-t0-g2-2026-11-21/golden-workload.md) |
| Golden corpus hashes | [`../g100-t0-g2-2026-11-21/golden/SHA256SUMS`](../g100-t0-g2-2026-11-21/golden/SHA256SUMS) |
| G3 edge-shape workloads | [`edge-workloads.md`](edge-workloads.md) |
| ECC S0 signoff | [`../g100-t0-ecc-s0-2026-11-20/signoff.md`](../g100-t0-ecc-s0-2026-11-20/signoff.md) |
| G1 evidence audit | [`../../grxgpu_g100_t0_g1_evidence_audit.md`](../../grxgpu_g100_t0_g1_evidence_audit.md) |
| T0 JTAG bench | [`../../../hw/unittest/t0_dbg/main.cpp`](../../../hw/unittest/t0_dbg/main.cpp) |
| CI unit-test catalog | [`../../../ci/testcases/unittest.yaml`](../../../ci/testcases/unittest.yaml) |
