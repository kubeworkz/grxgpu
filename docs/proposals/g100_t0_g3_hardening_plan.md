# G100-T0 G3 Functional and Software Hardening Plan

**Status:** Draft for review — plan only. No RTL, no contract change, no
evidence claimed.
**Gate:** G3 — functional and software hardening
([production plan](../grxgpu_production_plan.md) §3).
**Entry baseline:** [G100-T0 v1 Interface Contract](g100_t0_interface_contract.md),
Approved v1.0 on 2026-11-21, and the frozen workload `G100-T0-G2-SGEMM-1.0`
([G2 gate record](../evidence/g100-t0-g2-2026-11-21/gate-record.md),
[workload manifest](../evidence/g100-t0-g2-2026-11-21/golden-workload.md)).
**Scope:** the G100-T0 engineering die only. Commercial G0 remains on HOLD.
This plan does not authorize G4 purchases, G5 implementation, G6 tapeout, or
production release.
**Prepared by:** engineering agent supporting the G100-T0 program, 2026-11-21.
The author is not an approver and does not sign the G3 record.

---

## 1. Relationship to the frozen contract

This plan schedules conformance work; it does not re-open the interface.

1. **No new behavior is specified here.** Every test below names a frozen
   interface row (IF-01–IF-14) or an open conformance item (contract §13,
   G-1–G-8). Exit criteria are written as pass/fail checks against those
   frozen rows, not as design preferences.
2. **Three closure classes.** Each item is marked:
   - **CLOSE** — evidence produced at a named tier inside G3 satisfies the
     existing frozen wording.
   - **REVISION** — closing the item necessarily adds or changes observable
     behavior (fault status, a numeric bound, FENCE semantics). RTL must not
     start until a contract revision is approved under §14; the test is
     written now so the revision has an acceptance target.
   - **CARRY** — the contract itself assigns closure to a later gate. G3
     records the requirements and an explicit carry.
3. **Naming collision.** `G-n` in this plan always means contract §13. The
   [debug security review](g100_t0_debug_security_review.md) has a separate
   production-gate list that also uses `G-1`–`G-9`; those are cited here as
   `SR-G-n` and are not G3 items.
4. **Roles are owners, not signatures.** The contract's verification roles
   (Bring-up, Verification, Software, Power/thermal, Package/board) are the
   accountable evidence owners. Approval is separate: the author cannot sign
   their own evidence, and Gridworkz records the gate decision.
5. **T0 does not prove the CP.** The CP ring ABI is frozen software contract
   only; T0-A instantiates no CP (contract §7.2). CP evidence is
   software-conformance evidence and must be labelled that way.

---

## 2. Evidence model

### 2.1 Tiers

A result is only valid at the tier its exit criterion names. A lower tier
never substitutes for a higher one, and a higher tier never excuses a missing
lower-tier check.

| Tier | Model | How it runs |
|---|---|---|
| L0 | Unit bench | `make -C hw/unittest/<block> run` |
| L1 | T0-A island top, Verilator | `make -C hw/unittest run-t0` (`VX_t0_dbg_tb_top`) |
| L2 | Cluster/socket RTL | Verilator cluster top, explicit `--clusters=1 --cores=<n>` |
| L3 | SimX / rtlsim regression | `ci/blackbox.sh`, `ci/regression.sh --test <selector>` |
| L4 | FPGA / board | No T0 board at plan time; used where hardware exists |
| L5 | Silicon | G7 |

L1 currently instantiates the core, SBA/arbiter, test SRAM, boot sequencer and
KMU — not a cluster, DXA, TCU, or L1 cache
([`VX_t0_dbg_top.sv`](../../hw/rtl/dbg/VX_t0_dbg_top.sv)). L2 is therefore the
first tier that can carry DXA, TCU/LMEM and 16-core claims. L3 runs the
regression suite on SimX and the rtlsim RTL model for model parity; a pass
there does not replace a directed L1/L2 check, and SimX alone cannot close a
hardware-conformance row. xrt is the product RTL coverage path, but T0 has no
AFU, so L2 is the highest directed RTL tier in this plan. Commands are the catalog
forms; run them from the configured build tree and rebuild the app when its
`CONFIGS` differ from the driver's.

`ci/blackbox.sh` bounds rtlsim to 1 cluster × 4 cores unless a topology is
named, because the TOML default is 8 × 16 = 128 cores
([`blackbox.sh`](../../ci/blackbox.sh)). Any 16-core claim must pass
`--clusters=1 --cores=16`; `RTL_UNBOUND=1` selects the TOML default and is not
a 16-core argument.

### 2.2 Evidence record

Each test writes one record under `docs/evidence/g100-t0-g3-<date>/` with:

1. test ID and the contract row it covers;
2. source commit and root tree, plus the T0 configuration hash;
3. tool versions (Verilator/compiler/simulator) and build stamp;
4. command line, seed, and the tier;
5. raw log, unedited, plus its SHA-256;
6. PASS/FAIL against the exit criterion, with the measured number when the
   criterion is numeric;
7. accountable owner role and date;
8. open deviations, each tied to a revision or a carry.

A summary is not evidence. If the raw log is missing, the row is open.

---

## 3. Interface conformance matrix

Every row is testable against the frozen row as written. "Existing" means the
current T0 bench already exercises part of the behavior; the exit criterion
still requires the directed case named.

| IF | Behavior under test | Test | Accountable owner | Exit criterion |
|---|---|---|---|---|
| IF-01 | Five JTAG pins, 5-bit IR, IDCODE `0x00100001`, mandatory BYPASS/DTMCS/DMI, `TRST_n` resets TAP only | T-IF-01a IR/IDCODE walk and T-IF-01b `TRST_n` isolation, L1 [`t0_dbg`](../../hw/unittest/t0_dbg/main.cpp) | Bring-up lead | All four IR decodes match; IDCODE exact; a known SRAM word and DM state survive `TRST_n`; TCK cycle ratio documented at ≤10 MHz equivalent |
| IF-02 | 41-bit DMI, 7-bit address, one outstanding; busy → `op=3`, sticky `dmistat=3`; unsupported → status 2 | T-IF-02a busy (existing) and T-IF-02b reserved-address sweep, L1 | Verification lead | `op=3` returned, `dmistat` sticky, no hang; every unsupported address returns status 2 and leaves the first transaction intact |
| IF-03 | 32-bit SBA, `sbaccess=2` only, one outstanding, codes 1/2/3/4/7, 1024-cycle timeout, sticky W1C | T-IF-03a error codes 2/3/4, T-IF-03b timeout=1 and W1C, T-IF-03c `sbbusyerror` drop, L1 | Verification lead | Codes 1/2/3/4 observed exactly, code 7 reserved and not produced by the directed cases; clear-on-write observed; second access sets `sbbusyerror` and is dropped without corrupting the first; timeout counted at 1024 core cycles within recorded synchronizer latency |
| IF-04 | 512-bit data, 64 B line, 64-bit byte enable, 4096 lines, window `0x8000_0000`–`0x8003_FFFF` exact | T-IF-04a line-uniqueness walk (existing), T-IF-04b byte-enable matrix, T-IF-04c window-edge/alias probe, L1 | Verification lead | All 4096 lines uniquely addressed; each of 8 byte enables writes only its byte; `0x7FFF_FFFC` and `0x8004_0000` are not answered from SRAM; unmapped behavior per G-2 |
| IF-05 | Core I 4 B / D 8 B widened to a 64 B line; `ndmreset` stalls or resets the core; no bus error | T-IF-05a boot-image load/readback (existing), T-IF-05b `ndmreset` mid-fetch, T-IF-05c store-then-SBA-read, L1 | Verification lead | Image result word matches the CPU reference; `ndmreset` mid-fetch leaves no bus error and the next boot succeeds; SBA read after a completed core store returns the stored word |
| IF-06 | 20 KMU DCR writes, start pulse, 1024-cycle timeout; `boot_en=0` holds core | T-IF-06a DCR-trace monitor, T-IF-06b forced no-busy timeout, T-IF-06c `boot_en` hold, L1 | Bring-up lead | All 20 DCR values equal contract §7.1 word-for-word; `boot_done` on accept; `boot_error` on forced timeout with no retry; `boot_en=0` keeps the core in reset |
| IF-07 | DXA GMEM 64 B lines, 1 beat/cycle, ≤8 in flight, 16-entry queue; watchdog is an assertion, not a status code | T-IF-07a attach read into LMEM, T-IF-07b 8-outstanding credit, T-IF-07c stalled-response watchdog, L2 (cluster; T0-A has no DXA) | Verification lead | A full FP16 tile read from the test SRAM window arrives byte-exact in LMEM; 8 outstanding reads complete and credits recover; a stalled response fires the watchdog assertion and does not hang the top |
| IF-08 | 16 descriptor slots × 24 DCRs, 64-bit base, host encoders match RTL, write-only from host | T-IF-08a encoder/decoder equivalence, T-IF-08b slot isolation, L0/L2 [`dxa_core`](../../hw/unittest/dxa_core) | Software lead | For a shape table including both frozen descriptors, `program_2d`/`set_layout`/`set_tile_geometry` produce the DCR words the RTL consumes; writing slot n leaves n±1 unchanged; 16 slots usable |
| IF-09 | 1 LMEM word/cycle; DXA priority 0, TCU priority 1; completion by barrier transaction | T-IF-09a DXA/TCU contention, T-IF-09b barrier completion, L2 | Verification lead | DXA wins every conflict while both saturate; TCU progress bound recorded with no starvation past it; completion observed by barrier `tx` with no error status |
| IF-10 | CP ring 64 B lines, 4 B header, ≤5 commands/line, 1 queue, 11 mandatory opcodes, capability-gated `0x0B`/`0x0C`; no fault channel | T-IF-10a encoder→decoder round-trip, T-IF-10b overpack rejection, T-IF-10c capability gating, L0 software against [`VX_cp_pkg.sv`](../../hw/rtl/cp/VX_cp_pkg.sv) | Software lead | All 11 opcodes round-trip; a 6th command in one line is rejected by the encoder; optional opcodes require their capability bit; record states "software conformance, no T0 device evidence"; fault behavior is G-3 |
| IF-11 | Reset domains per contract §8.1; `core_reset = reset \| ndmreset \| ~boot_en`; one core clock plus TCK; DMI is the only CDC | T-IF-11a reset-domain matrix, T-IF-11b `core_reset` truth table, T-IF-11c DMI CDC check, L1 | Bring-up lead | Each of the five reset sources resets exactly the listed blocks and nothing else; no functional reset clears SRAM; the DMI crossing is the only clock-domain crossing and is synchronized as frozen; any other reported crossing fails the row |
| IF-12 | 10 W design case; Tj/θJA open; no throttle or shutdown | T-IF-12a power/thermal record, L4 where available | Power/thermal lead | A measurement states ambient, cooling, θJA, Tj and the measurement boundary, or the row is carried with "no product claim" |
| IF-13 | QFN-128, memory unbonded, fixed pin groups, `test_mode` present, numbers TBD | T-IF-13a pin-budget reconciliation at `VX_MEM_PORTS=0`, T-IF-13b package requirement record, L0 documentation | Package/board lead | Signal groups fit within 128 leaving a recorded power/ground budget, with no high-speed pins; `test_mode` and status/debug groups present; pin numbers explicitly carried to G4 (G-8) |
| IF-14 | `G100-T0-G2-SGEMM-1.0` identity and tolerances; device-run record contract | T-IF-14a corpus regeneration and hash match, T-IF-14b C comparison at the tier that runs all CTAs, L0/L2/L3 | Verification lead | Regenerated A/B match the manifest hashes; C max ULP ≤40 at K=64 and ≤114 at K=512; run record carries source, config, seed, toolchain; T0-A does not claim a full-matrix C |

---

## 4. Open conformance items G-1–G-8

### 4.1 Summary

| Item | Class |
|---|---|
| G-1 drain bound and reset recovery | CLOSE |
| G-2 out-of-window access | CLOSE |
| G-3 CP fault channel, DMA tail, FENCE | REVISION |
| G-4 DXA-to-SRAM attach | CLOSE |
| G-5 16-core top and cluster memories | CLOSE |
| G-6 ECC | CLOSE |
| G-7 400 MHz / 10 W | CARRY |
| G-8 package/pinout/PDK | CARRY |

G-7 and G-8 are carries in this plan: the contract assigns G-8 to G4, and G-7's
board measurement follows the production plan's "board regression passes where
hardware exists" rule. G-3 is revision-gated: the implementing branch supplies
the evidence, and the removal branch removes FENCE, still fixes the DMA tail,
and defers the fault channel to a later revision before any host-facing
product. The record states the evidence obtained at each tier and what remains
open.

### 4.2 G-1 — Bounded SBA drain and reset recovery

**Frozen requirement.** Timeout returns `sberror=1` and enters a drain; the
drain is currently unbounded (contract §11, §13; security review F-3). Reset
during an SBA transaction must leave no stale response.

**Tests.**

- T-G-1a: stall the SRAM response, count cycles from timeout to `sbbusy=0`,
  assert the drain reaches idle within the approved bound and no state
  machine remains armed.
- T-G-1b: assert `ndmreset` mid-write and mid-read; after release the next SBA
  access succeeds and the interrupted transfer leaves no response behind.
- T-G-1c: randomized timeout/reset fuzz (10,000 cases) with the bound as an
  assertion, not a post-hoc check.

The existing bench already observes `sbbusy` clearing after one stalled
response and a successful read after timeout
([`main.cpp`](../../hw/unittest/t0_dbg/main.cpp)); it does not assert a bound
and does not reset during a transaction.

**Evidence owner.** Verification lead, with the RTL owner for the bound.

**Exit criterion.** The drain bound is a written numeric limit in the RTL and
in the G3 record; every directed and fuzz case terminates within it; no case
leaves `sbbusy` set or returns a stale response after reset. If the bound
changes the frozen timeout wording, the numeric limit is approved under §14
before the RTL change.

### 4.3 G-2 — Out-of-window access must not return data

**Frozen requirement.** Unmapped windows return `sberror=2` over SBA and MUST
NOT silently succeed from the core (contract §5.1, §11). The SRAM decode and
the SBA comparator must describe the same 256 KB.

**Tests.**

- T-G-2a: SBA access below, above and in the `0x8004_0000`–`0x800F_FFFF` gap
  returns `sberror=2` and does not disturb SRAM (partly existing).
- T-G-2b: core fetch and load/store to `0x7FFF_FFFC` and `0x8004_0000` must not
  be answered with SRAM contents; the access either raises the documented
  failure or stalls until `ndmreset` clears it, never a silent zero word.
- T-G-2c: assertion that SRAM select implies the exact byte window, and that
  every request accepted by SBA is claimed by exactly one slave.
- T-G-2d: DXA out-of-bounds remains clamp-plus-`cfill` as frozen; this test
  exists to prove G-2 did not accidentally turn a defined DXA fill into an
  error.

**Evidence owner.** Verification lead.

**Exit criterion.** All three masters behave as their frozen rows require; the
decode-drift assertion is active in L1; no SBA or core access to an unmapped
address returns zeros or SRAM data. Because IF-05 freezes "no bus error", an
unmapped core access either raises the documented failure or stalls until
`ndmreset`; a successful zero word fails the row. Adding a core-visible error
channel is a §14 revision, not a test fix.

### 4.4 G-3 — CP fault channel, byte-exact DMA tail, FENCE

**Frozen requirement.** v1 has no CP fault channel, rounds unaligned DMA to
64 B, and retires FENCE immediately (contract §6.3, §7.2, §11, §13). The
contract's own closure wording is "add fault status, byte-exact tail, real
fence or remove from contract."

**Class: REVISION.** Each sub-item adds observable behavior or removes a
frozen one, so a v1.x revision must be approved before RTL. The tests are
defined now so the revision has acceptance targets.

**Tests.**

- T-G-3a malformed command: unknown opcode, bad length, command count over 5
  per line, and a descriptor pointing outside the queue must set a sticky
  fault record (code, queue id, command index), must not hang the engine, and
  the next valid command must succeed.
- T-G-3b tail: for lengths 1–4096 and unaligned offsets, the destination bytes
  outside the transfer must be unchanged, compared byte-for-byte against a CPU
  model. This is the direct test of the 64 B rounding defect.
- T-G-3c FENCE: `FENCE_DMA_BIT`/`FENCE_GPU_BIT` must order the named traffic,
  or the revision removes FENCE from the mandatory set and the test asserts
  the removal.

**Evidence owner.** Software/runtime lead for the ABI and expected status;
Verification lead for the benches.

**Exit criterion.** Either (a) a v1.x revision is approved with the fault
record layout and FENCE semantics, and T-G-3a–c pass in `cp_dma`,
`cp_engine` and `cp_core`; or (b) a revision removes FENCE, keeps the
byte-exact tail requirement, and defers the fault channel to a later revision
required before any host-facing product, with the removal recorded in the
contract. Leaving any of the three as "known non-conformance" keeps G-3 open.
T0 has no CP, so all evidence is L0/L3 and is labelled software-model evidence.

### 4.5 G-4 — DXA path to the test SRAM

**Frozen requirement.** DXA's GMEM port MUST reach
`0x8000_0000`–`0x8003_FFFF`; the current T0 top connects only core I/D and SBA
to the arbiter (contract §2 Figure 1, §6.2, §13).

**Tests.**

- T-G-4a: a DXA read of a 64 × 64 FP16 tile from the test SRAM window into
  LMEM, compared byte-exact with the golden A or B words.
- T-G-4b: three-master arbitration (SBA, core I/D, DXA) with SBA priority and
  no lost or duplicated beat; record the starvation bound for each master.
- T-G-4c: DXA watchdog assertion on a non-responding SRAM, with the top
  returning to idle rather than hanging.

A one-core cluster harness may carry T-G-4a–c before the 16-core top exists,
so G-4 does not wait on G-5.

**Evidence owner.** System/SoC architect, with the Verification lead for the
benches.

**Exit criterion.** DXA-sourced tiles arrive byte-exact from the test SRAM;
arbitration matches the frozen priority and each master's frozen outstanding
limit; the watchdog is observable as an assertion, not a hang; the attach is
present in the top that G5 uses, not only in a bench.

### 4.6 G-5 — 1 × 16 cluster and cluster memories

**Frozen requirement.** T0 is one cluster of 16 cores, 4 warps × 4 threads,
TCU and DXA, 16 KB LMEM/ICache/DCache per core, no L2/L3 (contract §1, §2,
§13). Only one core is simulated today.

**Tests.**

- T-G-5a: elaborate and lint the frozen configuration at
  `--clusters=1 --cores=16`; record resource use and elaboration time.
- T-G-5b: boot all 16 cores; each core writes a distinct result word; 16/16
  checked over SBA, not sampled.
- T-G-5c: `sgemm_tcu_wg_dxa` with the full 16-CTA grid; C compared to the
  golden corpus at the frozen ULP budgets, with A/B hashes checked first.
- T-G-5d: repeated launches and backpressure: the same kernel twice with
  different inputs, plus a saturating SBA stream, with no lost completion.
- T-G-5e: cache/coherency claim test. T0-A has no L1; the cluster build does.
  SBA-after-core-store must be characterized, and the record must state
  whether the result relies on the frozen no-coherency rule. The product-plan
  rule applies: prove the selected core count or reduce the claim.
- T-G-5f: edge-shape conformance, in two arms.
  - Supported arm: M and N multiples of 16 and K multiples of 8 at the frozen
    4-warp, `WGMMA_NRC=16` configuration. Examples: M=N=64 with K=8 (smallest
    K tile) and K=24 (not a power of two), both producible by the frozen
    [`gen_golden`](../evidence/g100-t0-g2-2026-11-21/golden/gen_golden.cpp)
    unchanged; and 16×16×8 (one CTA) plus non-square 32×16×8, which that
    generator cannot produce because it fixes M=N=64 and accepts only K. Their
    references come from
    [`gen_golden_dims.cpp`](../evidence/g100-t0-g3-2026-11-21/golden/gen_golden_dims.cpp)
    (M, N, K arguments, same `srand(50)` order, `rv_ftoh_s` conversion, and
    double-accumulate reference), whose source hash and generated A/B/C are
    recorded for `G100-T0-G3-SGEMM-M16N16K8-1.0` and
    `G100-T0-G3-SGEMM-M32N16K8-1.0` in the
    [edge-workload manifest](../evidence/g100-t0-g3-2026-11-21/edge-workloads.md).
    The frozen generator, corpus, and
    `G100-T0-G2-SGEMM-1.0` are not edited. Every supported shape is a new
    workload with its own ID and CPU reference. Before the run, the evidence
    record fixes that shape's FP32 ULP budget and comparator: the budget is
    `max(12, ceil(5·√K))` and the comparator is the manifest's integer
    distance between positive FP32 bit patterns, with zero mismatches beyond
    the budget. A shape without a recorded budget is not run as supported.
  - Rejection arm: `M % 16 != 0`, `N % 16 != 0`, and `K % 8 != 0` (for
    example 17×16×8 and 16×16×12) must be refused by the workload's own
    dimension checks with a clear error and a non-zero exit, not a silent
    wrong result. The unsupported set is the frozen manifest's
    [unsupported-shapes section](../evidence/g100-t0-g2-2026-11-21/golden-workload.md),
    not the contract's TBD interface list.

**Evidence owner.** System/SoC architect, with the Verification lead for the
regression and the Software lead for the run record.

**Exit criterion.** The 16-core top elaborates at the frozen configuration;
16/16 cores retire and report distinct correct results; the frozen workload
passes at 16 CTAs with A/B hash matches and C within budget; a second launch
succeeds; each supported edge shape matches its own recorded CPU reference
within its recorded ULP budget, and each rejection case exits non-zero with a
clear error; the coherency statement is explicit. If the run stays at 4 cores,
G3 records 4-core conformance and the 16-core claim is not made.

### 4.7 G-6 — ECC decisions and implementation

**Frozen requirement.** SECDED is a T0 requirement with no RTL; the ECC S0
decisions are unsigned; the `0x8010_0000` status window is conditional
(contract §1, §5.1, §13). The closure path already exists in the
[ECC closure plan](g100_t0_ecc_closure_plan.md) and its
[S0 signoff record](../evidence/g100-t0-ecc-s0-2026-11-20/signoff.md).

**Tests.** The ECC plan's stages are the test plan; this document does not
restate them. The mapping is:

- T-G-6a: S0 signature on D1–D14 by the Architecture and Verification roles.
- T-G-6b: `hw-ecc` codec bench (S1) and `hw-ecc-ram` wrapper bench (S2).
- T-G-6c: LMEM and cache integration cases (S3, S4), including RMW and
  uncorrectable-line invalidation.
- T-G-6d: one-shot injection over SBA and counter readout (S5, S6), with the
  containment test proving the SRAM and status windows cannot drift.
- T-G-6e: TSRAM-only counter evidence recorded as TSRAM-only; the three-array
  counters recorded as simulation evidence until a cluster build exists.

**Evidence owner.** Verification lead, with the System/SoC architect for the
decode contract and the security reviewer for the delta review.

**Exit criterion.** S0 is signed; S1–S7 exit gates in the ECC plan are met;
injection and readout work over SBA at L1; the containment test passes; the
status window is either implemented as approved or `0x8010_0000` remains
unallocated with the deferral recorded. No ECC claim is made for an array that
is not in the built top.

### 4.8 G-7 — 400 MHz and 10 W

**Frozen requirement.** 400 MHz core and 10 MHz TCK targets; 10 W design
case; Tj/θJA and STA open (contract §9, §13). G3 "must record the actual
ambient, θJA, and junction temperature."

**Tests.**

- T-G-7a: synthesis and STA at the target library, 400 MHz (2.5 ns), all
  available corners, with the frozen T0 configuration; record WNS/TNS and the
  worst path.
- T-G-7b: TCK-domain timing and the DMI CDC constraint at 10 MHz.
- T-G-7c: board measurement at declared ambient and cooling, or a recorded
  deferral.

**Evidence owner.** Physical design for STA (G4 role); Power/thermal lead for
the measurement.

**Class: CARRY.** The target library is selected at G4 (G-8). T-G-7a can run
on a proxy library as readiness evidence, labelled as such and not as
target-library closure. T-G-7c follows the production plan's "board regression
passes where hardware exists": if no board is available at the G3 review, the
record states that the measurement was not possible and carries the item to
the gate that first has hardware.

**Exit criterion.** WNS ≥ 0 at 2.5 ns on the selected library, or an approved
§14 target change; measured power ≤10 W and Tj within the declared limit at a
stated ambient; or an explicit carry to G4/G7 with "no product claim" in the
G3 record. The carry records what was measured, on which library or board, and
what remains open.

### 4.9 G-8 — Package, pinout, PDK

**Frozen requirement.** QFN-128 planning boundary, memory unbonded, pin
numbers and PDK unselected (contract §10, §13). The contract assigns closure
to G4.

**Tests.**

- T-G-8a: pin-budget reconciliation from the frozen groups at
  `VX_MEM_PORTS=0`, including power/ground and the thermal pad.
- T-G-8b: package requirement record: 128 pins, no bonded memory, 3.3 V CMOS
  JTAG, thermal path, bring-up observability pins.
- T-G-8c: PDK/library availability and licence evidence (G4).

**Evidence owner.** Package/board lead, with sourcing for T-G-8c.

**Exit criterion.** T-G-8a/b accepted as the G4 input; G-8 listed as an open
carry in the G3 record with the G4 owner named. G3 does not claim a selected
package or PDK.

---

## 5. Software hardening track

These items make the runtime and evidence flow release-candidate quality, as
G3 requires. They do not add product features.

| ID | Item | Test | Owner | Exit criterion |
|---|---|---|---|---|
| S-1 | Reproducible build and build stamp (E-101) | T-S-1 two clean builds from the same pin and config | Build/release + RTL lead | Builds are byte-identical, or every difference is enumerated; the stamp appears in the image and the run record |
| S-2 | Host ABI conformance for DXA and CP (E-106) | T-S-2 encoder/decoder round-trip and capability gating | Software lead | Same result as T-IF-08a and T-IF-10a, run as one suite against the pinned RTL constants |
| S-3 | Diagnostics without a fault channel | T-S-3 injected SBA timeout, boot error, and bad descriptor; operator-visible output | Software lead | Each failure is reported from existing status (`sberror`, `boot_error`) with no register pokes and no false CP fault code |
| S-4 | SimX ↔ rtlsim parity harness (E-302) | T-S-4 frozen workload on both models, word-exact output compare | Verification lead | Outputs match; retired-instruction counts match exactly; cycle agreement is within the `model_parity` tolerance; counts are archived |
| S-5 | Golden-workload device-run runner | T-S-5 run record per the [manifest §6](../evidence/g100-t0-g2-2026-11-21/golden-workload.md) | Verification lead | Runner refuses to compute when generated A/B hashes differ from the manifest |
| S-6 | Recovery procedure | T-S-6 reload-over-SBA recovery twice from a clean state | Bring-up lead | Both runs reach the same result word; retained-SRAM behavior is stated, not assumed scrubbed |
| S-7 | Compiler and operator path | T-S-7a pinned-toolchain rebuild of the frozen kernel and one other supported kernel; T-S-7b operator-scope record | Build/release + Software lead | Both kernels build and run from the pinned source; the operator surface is listed and tested, or an explicit T0 exclusion names the later gate |

### 5.1 Coverage and defect closure

| ID | Item | Evidence | Owner | Exit criterion |
|---|---|---|---|---|
| T-V-1 | Functional coverage review | Coverage bins mapped to the acceptance matrix; exclusions and waivers listed | Verification lead | Every critical bin is covered or has a written waiver; no gap is unclassified |
| T-V-2 | Critical-defect log | Every open defect with severity, owner, and target | Verification lead + RTL owners | No open critical defect at G3 exit; each non-critical defect has an owner and target |

### 5.2 Release-candidate checklist

`T-RC-1` audits this checklist; an unmet row keeps the checklist open.

| ID | Area | Required state | Evidence |
|---|---|---|---|
| RC-1 | Runtime | Load, launch, and status work through the supported ABI without manual register pokes | S-2, S-3 |
| RC-2 | Firmware | T0 has no firmware or ROM; record the exclusion, or cover the loader if one is added | contract §8.2 |
| RC-3 | Compiler | The frozen kernel and one other supported kernel rebuild from the pinned source and toolchain | S-7a |
| RC-4 | Operator scope | Supported operators are listed and tested, or an explicit T0 exclusion is signed | S-7b |
| RC-5 | Diagnostics | Failures report from existing status; no invented CP fault code | S-3 |
| RC-6 | Update/recovery | Reload-over-SBA recovery succeeds twice from a clean state | S-6 |
| RC-7 | Reproducible build | Build stamp present; rebuild byte-identical or differences enumerated | S-1 |
| RC-8 | Supported-model path | T0 has no supported model path; record the exclusion, or cover the path if one is added | [workload manifest](../evidence/g100-t0-g2-2026-11-21/golden-workload.md) §1; [production plan](../grxgpu_production_plan.md) G3 row |
| RC-9 | Evidence | All G3 logs filed with hashes; coverage and defect records complete | T-V-1, T-V-2 |

**Evidence owner.** Verification lead, with the Software and Build/release
leads for the runtime, compiler, model-path, and build rows.

---

## 6. Sequence, dependencies, stop conditions

### 6.1 Waves

| Wave | Work | Why this order |
|---|---|---|
| 1 | G-1, G-2, IF-01–IF-06 hardening, S-1 | Debug and load path must be trustworthy before anything runs on top of it |
| 2 | G-3 revision decision, G-4 attach, IF-07–IF-09, S-2, S-3, S-7 | The DXA path, ABI decision, and compiler path gate all later compute evidence |
| 3 | G-5 16-core integration, G-6 ECC (S0 first), IF-10, IF-14, T-G-5f | Full-workload, edge-shape, and ECC evidence need the cluster top |
| 4 | G-7 STA, G-8 requirements, S-4–S-6, T-V-1, T-V-2, T-RC-1, G3 record | Closure evidence, coverage/defect records, and the explicit carries |

G-6 S0 can run in parallel with wave 1 because it changes no RTL; ECC RTL
starts only after signature. G-4 may run on a one-core cluster harness so it
does not wait for G-5.

### 6.2 Stop conditions

Stop the affected test and file a §14 change request, rather than editing the
contract in place, when:

1. a test shows a frozen row cannot be implemented as written;
2. closing G-1 or G-3 needs a numeric limit or status field the contract does
   not contain;
3. a golden-workload hash, seed, or tolerance would have to change — that
   creates a new workload ID and corpus, never an edit;
4. a 16-core or coherency claim would rest on a 4-core run;
5. ECC RTL would start before S0 is signed, or a status window would be
   allocated before D9/D14 are accepted.

---

## 7. G3 exit rollup

| G3 requirement (production plan) | Evidence | State now |
|---|---|---|
| Product regression on reference and RTL models | T-IF-14a/b, T-G-5c, S-4 | Open; corpus frozen, no device run |
| Board regression where hardware exists | Frozen workload and T-G-7c on L4 if a board exists | No T0 board at plan time; the absence is recorded |
| Multi-tile and maximum-size transfers | T-G-5c, T-G-3b | Open |
| Edge shapes and DMA tails | T-G-5f, T-G-3b | Open |
| Repeated and concurrent launches; backpressure | T-G-5d, T-IF-09a | Open |
| Compiler/operator path | T-S-7a, T-S-7b | Open |
| Reset and recovery | T-G-1b/c, T-S-6 | Partly exercised; bound and mid-transaction reset open |
| Malformed commands and failure injection | T-G-3a, T-G-6d, S-3 | Open; needs the G-3 revision |
| Boundary addresses | T-IF-04c, T-G-2a/b | SBA side tested; core side open |
| Coherency proven for the selected core count, or reduced claim | T-G-5e | Open; no L1 in T0-A |
| Assertions/formal reviewed; critical coverage bins covered or waived | T-G-1c, T-G-2c, T-IF-07c, T-V-1, E-107 | Open |
| Critical-defect closure | T-V-2 | Open; no defect log yet |
| Runtime/firmware, supported-model path, diagnostics, update/recovery, reproducible builds as release candidates | S-1–S-7, T-RC-1 | Open |

**Gate rule.** Every G-1–G-8 row must be recorded as closed, revisioned, or
carried with a named later gate, and the production-plan evidence above must
be present. The record must also show no open critical defect (T-V-2) and
coverage bins covered or waived (T-V-1). A carry records an open limitation
rather than completed exit evidence; pass, conditional pass, or hold is the
approver's decision.

**What G3 will still not prove:** a product host interface, DRAM/HBM, product
coherency, package selection, silicon timing or thermal behavior, tapeout
readiness, or any commercial release. Those stay outside T0 under the G0 hold.

---

## 8. Traceability

| G2 gate-record open item | Contract §13 item | G3 tests |
|---|---|---|
| O-3 DXA has no path to the test SRAM | G-4 | T-G-4a–c |
| O-4 16-core cluster not integrated | G-5 | T-G-5a–e |
| O-5 ECC absent; S0 unsigned | G-6 | T-G-6a–e |
| O-6 SBA drain, OOB, CP fault, DMA tail, FENCE | G-1, G-2, G-3 | T-G-1a–c, T-G-2a–d, T-G-3a–c |
| O-7 STA, power, package, PDK | G-7, G-8 | T-G-7a–c, T-G-8a–c |
| O-8 CP ring ABI not exercised on T0-A | G-3, S-2 | T-IF-10a–c, T-G-3a |

Related engineering tasks: E-101 (S-1), E-103 (T-G-5c, T-G-5f), E-104
(T-G-5e), E-105 (G-1, G-2, G-3), E-106 (S-2, S-3, S-6, S-7), E-107 (T-V-1,
T-V-2), E-302 (S-4, golden run). See the
[engineering task list](../grxgpu_engineering_task_list.md).
