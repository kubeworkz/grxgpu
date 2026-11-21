# G100-T0 G2 Gate Record — Architecture and Interface Freeze

**Status:** **G2 PASSED (T0 engineering ICD only), 2026-11-21.** The v1
contract is approved and the golden workload is frozen. Gridworkz approved all
five roles. This does not lift the commercial G0 hold or authorize G4
purchases, G5 implementation, G6 tapeout, or production release.
**Gate:** G2 — product architecture and interface freeze
([production plan](../../grxgpu_production_plan.md) §3).
**Scope:** G100-T0 engineering die only. Commercial G0 remains on HOLD; this
record does not authorize a sellable SKU, purchase, G4, G5, G6 tapeout, or
production release.
**Contract:** [G100-T0 v1 Interface Contract](../../proposals/g100_t0_interface_contract.md).
**Golden workload:** [Frozen workload and corpus](golden-workload.md).
**Prepared by:** engineering agent supporting the G100-T0 program, 2026-11-21.
The author is not an approver and does not sign this record.

---

## 1. What was frozen

| Artifact | Version / identity | State |
|---|---|---|
| System diagram | v1.0, contract §2, Figure 1 | Approved v1.0 |
| Interface contract / ICD | v1.0, 2026-11-21 | Approved v1.0, signed |
| Named workload | `G100-T0-G2-SGEMM-1.0`, `sgemm_tcu_wg_dxa` | Frozen |
| CPU reference | `matmul_cpu` semantics, standalone `gen_golden` | Frozen, run |
| Golden data | 6 files, both K values, SHA-256 in manifest | Frozen, verified |
| Source pin | `ff550c27570f17b0c8242be42257043d3de4ffa7` | Pinned |
| Configuration | T0 1×16 `CONFIGS`, resolver output `cd5336…` | Proposed (G1), not built |

Approved v1.0 means the content is the G2 interface baseline and is under
contract §14 change control. The approval records the interface, not
conformance: the G3 closure items in contract §13 remain open.

---

## 2. Exit-criteria mapping

| G2 exit requirement | Where frozen | Status |
|---|---|---|
| Approved system diagram | Contract §2 | Approved v1.0 (Gridworkz, 2026-11-21) |
| Host interface | Contract §4 | T0 JTAG defined; product host explicitly TBD |
| Memory / DDR / HBM | Contract §5 | 256 KB SRAM and map defined; DRAM/HBM excluded from T0 |
| DMA / DXA | Contract §6 | DXA descriptor/issue defined; T0 DXA attach is required-new |
| Addressability / coherency | Contract §5.2–§5.3 | T0 physical map and no-coherency rule defined; product coherency TBD |
| Command ABI | Contract §7 | Boot DCR ABI and CP ring ABI defined; CP not in T0-A |
| Boot / reset / debug / recovery | Contract §8 | T0-A defined; update/secure recovery TBD |
| Package | Contract §10 | QFN-128 boundary defined; pin numbers/PDK open |
| Clocks | Contract §9 | 400 MHz target, 10 MHz TCK frozen; STA open |
| Power / thermal | Contract §9 | 10 W design case frozen; Tj/θJA open measurement |
| Named workload with runnable CPU reference | Workload manifest §1, §4 | Frozen and run standalone |
| Frozen golden data | Workload manifest §5 | 6 files, hashes, independent verification |
| Unsupported operators / shapes | Contract §12, workload manifest §7 | Specified |
| Error handling / timeouts | Contract §11 | Specified, with listed conformance gaps |
| Compatibility / change control | Contract §7.2, §14 | Specified |
| Every interface has producer, consumer, limit, reset/error, verification owner | Contract §3 | Defined; owners are roles, not named people |

The content side of G2 is complete for the T0 boundary, and the approvals in
§5 make the gate pass. Several implementation behaviors are explicitly
deferred to G3 (contract §13); they are tracked conformance work, not
unfrozen interfaces.

---

## 3. Golden workload freeze

`G100-T0-G2-SGEMM-1.0` freezes:

- `sgemm_tcu_wg_dxa`, M=N=64, K=64 and K=512, FP16→FP32, `WGMMA_NRC=16`;
- the `srand(50)` / glibc / `rv_ftoh_s` input semantics;
- the FP32-product, double-accumulate CPU reference;
- the ULP budgets (40 at K=64, 114 at K=512);
- six raw corpus files with SHA-256 values.

Verification at freeze:

- generator rerun produced byte-identical A, B and C;
- an independent NumPy implementation of the glibc sequence, FP16 conversion
  and reference matched all A/B/C words with `max ULP=0`;
- file sizes match the declared shapes.

This satisfies the G2 wording "runnable CPU reference and frozen golden data."
It does **not** record a T0 device execution; that remains G3/E-302 work.

---

## 4. Open items and blockers

| # | Item | Why it matters | Disposition |
|---|---|---|---|
| O-1 | No named Product, System/SoC, Software, Board, or Verification approver (prior state) | G2 required five signatures; G0 recorded owners as TBD | **Closed:** Gridworkz approved all five roles on 2026-11-21 (§5) |
| O-2 | Product host, DRAM/HBM, coherency, and update interfaces are TBD | v1 is a T0 bring-up ICD, not a product ICD | Explicitly out of scope; product boundary needs a later gate/ICD |
| O-3 | DXA has no path to the test SRAM in the T0 top | Without it, the frozen GEMM cannot use DXA tiles on T0 | Required-new under v1; G3 closure (G-4) |
| O-4 | T0 16-core cluster and L1/L2 are not integrated; only one core is simulated | T0 die target is frozen but not yet represented by a full top | G3 closure (G-5) |
| O-5 | ECC RTL absent; S0 decisions unsigned; status window at `0x8010_0000` conditional | RAS requirement and address map reservation | G3 closure (G-6); reserved but not allocated until S0 |
| O-6 | SBA drain timeout, OOB zero-fill, CP fault channel, DMA tail, FENCE semantics | Interface error behavior is defined but not fully conforming | G3 closure (G-1–G-3) |
| O-7 | 400 MHz / 10 W not closed by STA or measurement; package/pinout/PDK unselected | Frozen targets without implementation evidence | G3/G4; open measurements are marked in the contract |
| O-8 | CP ring ABI is not instantiated or exercised on T0-A | ABI is a software contract, not T0 evidence | G3/product host work; T0 does not claim it |

No item above silently relaxes the contract. O-3 through O-6 are requirements
that G3 must close; O-1 is closed by the approvals in §5; O-2 is a scope
boundary.

---

## 5. Approval and gate disposition

**Signoff rule:** G2 passes only when all five signatures are present, every
condition is written into this record, and the disposition is `Approve v1.0`
or `Approve with conditions`. All five signatures are recorded below.
Self-signoff is not signoff; a signer must not be the author of the artifact
they approve.

| Role | Name | Decision | Date | Conditions / notes |
|---|---|---|---|---|
| Product | Gridworkz | **Approve v1.0** | 2026-11-21 | T0 engineering ICD only |
| System/SoC architect | Gridworkz | **Approve v1.0** | 2026-11-21 | Contract §2 diagram and §3 interface register |
| Software/runtime lead | Gridworkz | **Approve v1.0** | 2026-11-21 | §7 ABI frozen; CP path remains G3 |
| Board/package lead | Gridworkz | **Approve v1.0** | 2026-11-21 | QFN-128 boundary; pinout remains G4 |
| Verification lead | Gridworkz | **Approve v1.0** | 2026-11-21 | Golden corpus verified; G3 conformance open |

All five approvals are recorded to Gridworkz as the authorized approver for
this engineering gate. Gridworkz is not the author of this record.

**Gate disposition:**

- [x] **G2 PASS (T0 engineering ICD only).** The contract is approved v1.0 and
  the frozen corpus is the G3 comparison baseline.
- [ ] **G2 PASS WITH CONDITIONS.** Conditions: ______________________________
- [ ] **G2 HOLD / REJECT.** Reason: _________________________________________

**Authority boundary.** A G2 pass is an engineering interface freeze for
G100-T0. It does not lift the commercial G0 HOLD, does not authorize G4
purchases, G5 implementation, G6 tapeout, or production release, and does not
approve a product host, DRAM/HBM, package, or process.

---

## 6. Change control after signature

1. The contract version increments for any behavior change; editorial changes
   do not.
2. A change to the frozen workload (dimensions, types, seed, generator, libc,
   reference, tolerance) creates a new workload ID and a new corpus. The
   existing files and hashes are not edited.
3. Every change records the affected interface IDs, producer/consumer impact,
   golden-workload impact, re-verification, and gate impact.
4. A product host, memory, coherency, or package interface is a v2 boundary,
   not a v1 edit.

---

## 7. Evidence index

| Artifact | Path |
|---|---|
| v1 interface contract | [`docs/proposals/g100_t0_interface_contract.md`](../../proposals/g100_t0_interface_contract.md) |
| Frozen workload manifest | [`golden-workload.md`](golden-workload.md) |
| Golden corpus and checksums | [`golden/`](golden/), [`golden/SHA256SUMS`](golden/SHA256SUMS) |
| Independent verification log | [`golden/verify.log`](golden/verify.log) |
| Corpus generator | [`golden/gen_golden.cpp`](golden/gen_golden.cpp) |
| Independent verifier | [`golden/verify_golden.py`](golden/verify_golden.py) |
| Pinned T0 configuration | [`../g100-t0-g1-audit-2026-11-20/proposed-config.txt`](../g100-t0-g1-audit-2026-11-20/proposed-config.txt) |
| G1 evidence audit | [`../../grxgpu_g100_t0_g1_evidence_audit.md`](../../grxgpu_g100_t0_g1_evidence_audit.md) |
| G0 engineering authorization | [`../../grxgpu_g100_g0_authorization.md`](../../grxgpu_g100_g0_authorization.md) |
