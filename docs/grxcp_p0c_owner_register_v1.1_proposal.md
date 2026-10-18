# PTA-MESH-OWNER-REG-001 v1.1 — proposed change record

**Status:** Proposal only; not activated, approved, or signed. The cited v1.0 owner register is not present in this workspace, so row IDs and existing assignments below are transcribed from the supplied P0-C integration package and must be checked against the controlled register before adoption. P0-C remains **OPEN**.<br>
**Proposed change authority:** Dave Cook (confirmation/signature pending)<br>
**Proposed record date:** 2026-10-20 (not an assertion that the register was activated)<br>
**Basis:** [P0-C PIC/EIC agenda](grxcp_p0c_pic_eic_review_agenda.md), [reconciliation memo](grxcp_p0c_reconciliation_memo.md), and [board program plan §8](../grxcp/docs/designs/board_program_plan.md#8-open-questions).

## Proposed v1.1 changes

| Supplied row | Supplied v1.0 item/date | Proposed v1.1 disposition | Status / approval |
|---|---|---|---|
| R-04 | §1 scale/workload envelope — 2026-11-20 | Split: bounded-range record due 2026-11-20; selected envelope due 2026-12-12; carry scale/workload OPEN through Dec 3 | Proposed; Dave Cook approval pending |
| R-08 | §1 P0-C reconciliation — 2026-11-20 | Split: preliminary reconciliation due 2026-11-20; final P0-C-b due 2026-12-12 | Proposed; verify row against v1.0 |
| R-13 | §2 source/receiver — 2026-11-20 | Split: bounded analysis range due 2026-11-20; selected/source-backed values due 2026-12-12 | Proposed; dependencies not signed |
| R-17 | §2 link budget — 2026-11-20 | Split: bounded model due 2026-11-20; selected configuration/budget due 2026-12-12 or later selected-IP dependency | Proposed; 57.6 GB/s remains a sizing assumption |
| R-36 | §3 §5.4 UCIe IP record — 2026-11-20 | Split: sizing-assumption record due 2026-11-20; selected configuration proposed for 2027-02-12 with V6 | Proposed; confirm V6 schedule/dependency |

The 2026-12-03 architecture review is not re-dated by this proposal. Any P0-C-dependent checklist items without complete evidence remain OPEN at that review; bounded ranges are review input, not closure evidence.

## Proposed additional rows

| Row | Artifact / item | Proposed owner | Due | Status |
|---|---|---|---|---|
| R-91 | P0-C-a bounded-range package with assumptions and “bounded for study” dispositions | Dave Cook | 2026-11-20 | Proposed |
| R-92 | P0-C-b decision record D-1…D-6 | Dave Cook | 2026-12-12 | Proposed |
| R-93 | Workload/canary manifest and approval status | Dave Cook | 2026-11-20 | Proposed |
| R-94 | PIC block diagram/connectivity/readout sketch for candidates | Dave Cook | 2026-11-20 | Proposed |
| R-95 | Source/receiver evidence package; controlled evidence location and revision | Dave Cook | 2026-12-12 | Proposed |
| R-96 | Reproducible link/buffer/receiver/source/weight-path calculations with model revision | Dave Cook | 2026-11-20 | Proposed |
| R-97 | Candidate operating-point table with confidence classes | Dave Cook | 2026-11-20 | Proposed |
| R-98 | Written disposition for each open choice with rationale/dependency/gate | Dave Cook | 2026-12-12 | Proposed |
| R-99 | Logical-to-physical mapping table, including tiling/accumulation/padding | Dave Cook | 2026-12-12 | Proposed |
| R-100 | §2 revision-impact assessment for coherent versus power/intensity alternatives | Dave Cook | 2026-12-12 | Proposed |

## Adoption checklist

- [ ] Obtain the controlled `PTA-MESH-OWNER-REG-001 v1.0`; verify the five row IDs, owners, due dates, status, and dependencies.
- [ ] Confirm the proposed Nov 20 / Dec 12 split preserves the Dec 3 review target and review owners.
- [ ] Confirm R-36’s V6 dependency and proposed 2027-02-12 date with the actual schedule owner.
- [ ] Check for duplicate IDs and register schema requirements before adding R-91…R-100.
- [ ] Dave Cook approves the complete change set; record signature/date and immutable register revision/hash.

**Activation disposition:** ☐ Accept ☐ Amend ☐ Reject — *no selection made in this proposal.*<br>
**Dave Cook signature/date:** ____________________<br>
**Controlled v1.0/v1.1 artifact paths and SHA-256:** ____________________
