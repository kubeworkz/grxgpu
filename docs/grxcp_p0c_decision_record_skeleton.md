# PTA-MESH-P0C-DR-001 — decision record skeleton

**Version:** 0.1 (skeleton)<br>
**Status:** Unsigned; for P0-C-b owner review targeted 2026-12-12. P0-C remains **OPEN**. This template records no selection or approval.<br>
**Decision owner:** Dave Cook<br>
**Related:** [PIC/EIC agenda](grxcp_p0c_pic_eic_review_agenda.md), [reconciliation memo](grxcp_p0c_reconciliation_memo.md), [candidate operating points](grxcp_p0c_operating_points.csv), and [owner-register v1.1 proposal](grxcp_p0c_owner_register_v1.1_proposal.md).

## 1. Record metadata

| Field | Entry |
|---|---|
| Decision record ID / revision | PTA-MESH-P0C-DR-001 v0.1 |
| P0-C-a bounded-analysis review target | 2026-11-20; no selections intended |
| P0-C-b decision review target | 2026-12-12 |
| Actual meeting date / attendees | TBD |
| Workload/canary manifest revision and hash | TBD |
| PIC/EIC/endpoint source revisions | TBD |
| Candidate table revision and hash | TBD |
| Reviewer / evidence location | TBD |

## 2. Decision table — complete at owner review

The suggested dispositions below are discussion prompts only. Mark one disposition per row at the meeting, record rationale and evidence, and leave unresolved items explicitly open/deferred. **Bounded-for-study and deferred dispositions do not close P0-C.**

| ID | Choice | Suggested disposition (not selected) | Owner decision | Rationale / assumptions | Dependency / affected gate | Evidence path + SHA-256 | Reviewer/date |
|---|---|---|---|---|---|---|---|
| D-1 | Workload and scope | Bounded for study: retain the 64→16 canary only as an integration test assumption; identify any customer/GPU workload separately and keep approval status explicit. | TBD | TBD | Workload owner; §1 scale/workload | TBD | TBD |
| D-2 | Geometry meaning | Bounded for study: treat 128×64 as logical sizing dimensions only; defer physical primitive and mapping until topology evidence exists. | TBD | TBD | PIC connectivity; logical-to-physical mapping; §1 scale | TBD | TBD |
| D-3 | Optical architecture boundary | Defer primitive and field/coherent versus power/intensity choice unless owner evidence supports a selection; mark any absent §2 spec claims unverified. | TBD | TBD | PIC trade study; §2 signal/readout/error model | TBD | TBD |
| D-4 | Rate envelope / shot semantics | Bounded for study: evaluate 1–25 MS/s and define whether a shot is one logical vector, physical tile firing, or batch firing. State sustained/peak, weight residency/update, calibration, and tiling assumptions. | TBD | TBD | D-1–D-3; link/source constraints; §1/§2 | TBD | TBD |
| D-5 | Receiver/source feasibility | Bounded analysis only: record missing source, loss, receiver-noise-versus-bandwidth, responsivity, and thermal values with ranges/provenance; no pass absent selected/sourced evidence. | TBD | TBD | Supplier/IP evidence; §2 source/receiver | TBD | TBD |
| D-6 | EIC/GPU feed constraints | Bounded for study: retain 57.6 GB/s/direction only as the documented sizing assumption; resolve direction-specific traffic, weight reload/residency, overhead, selected UCIe config, and margin. | TBD | TBD | D-1/D-4; selected UCIe config; §3 link budget | TBD | TBD |

## 3. Closeout

| Field | Entry |
|---|---|
| Retain/revise 128×64, batch 16, 25 MS/s | ☐ Retain as provisional only ☐ Revise (new provisional point + rationale) ☐ Defer |
| Dec 3 review carry-forward | Identify dependent checklist rows that remain OPEN, owner, evidence action, and Dec 12 target: TBD |
| Tracker updated | ☐ Yes — date/evidence links/hashes recorded ☐ No |
| Register change approved | ☐ Yes (attach controlled register revision/hash) ☐ No / pending |
| P0-C status | **OPEN by default.** Closure requires selected owner-approved workload/geometry/rate envelope with sourced evidence or an explicitly approved bounded operating-point specification meeting the gate. |
| Dave Cook signature / date | ______________________________ |
| PIC/EIC reviewer(s) / date | ______________________________ |
| GPU workload/link reviewer / date | ______________________________ |

A model output, unsigned recommendation, “bounded for study,” or deferred choice is not optical-device or hardware qualification evidence and does not close P0-C.
