# PDK Conformance Harness — Specification (draft v0.1)

**Status:** Draft attachment for partner review. The tolerances below are
engineering targets to be agreed with the partner, not measured results, and
nothing here is a signoff or manufacturability claim.
**Date:** 2026-11-03
**Companions:** [open 28 nm PDK program proposal](open_28nm_pdk_program.md) §5.2
and the [engagement letters](open_pdk_engagement_letters.md) that offer this
document to a recipient.

## 1. What it proves

Given a foundry PDK and an open re-expression of it, the harness shows that both
return the same DRC, LVS, PEX and timing answers within stated tolerances on a
defined corpus, and reports every difference it cannot reconcile rather than
asserting equivalence.

## 2. Inputs

| Input | Form | Source | Handling |
|---|---|---|---|
| Reference PDK | Decks, golden PEX, Liberty, layer map, revision string | Foundry, under NDA | Stays in the harness workspace; never copied into the public tree |
| Open re-expression | KLayout DRC/LVS rules, open LEF/Liberty/GDS, PEX rules | Us | Publishable only after partner review |
| Corpus | GDS/OASIS plus a manifest of what each layout exercises | Us; partner may add cases | Public where the layout is ours, held where it is not |
| Tool container | Pinned image with KLayout, Netgen, ngspice, OpenROAD, CharLib | Us | Digest recorded in every report |

## 3. Tests and pass criteria

| # | Test | Reference | Pass criterion |
|---|---|---|---|
| 1 | DRC equivalence | Foundry deck | Empty symmetric difference on the corpus, including known-marginal layouts |
| 2 | LVS | Foundry deck | 100 % match on 100 library cells and 10 placed blocks |
| 3 | PEX | Foundry golden extraction | R and C within 5 % per net; delay within 3 % on 20 blocks |
| 4 | Liberty / CCS | Foundry characterization | Delay and transition within 3 %; leakage within 2 %, at every corner |
| 5 | Static timing | PrimeTime or Tempus on the foundry Liberty | Block WNS within 20 ps and 5 % on 10 blocks |
| 6 | Fill / density | Foundry rules | Density and CMP checks clean on the same corpus |

## 4. How a comparison is made

1. Both runs use the same container digest, corpus hash and PDK revision; the
   run is refused if any of the three is missing.
2. Outputs are normalized before comparison: sorted, unit-normalized, and
   snapped to the deck's database grid.
3. Every difference is classified as a reference-deck defect, a re-expression
   defect, or a corpus case needing a ruling.
4. Unresolved differences stay in the report and count against the criterion.
   They are never dropped, and never resolved by widening a tolerance.

## 5. Outputs

Each run emits `manifest.json` (corpus hash, PDK revision, container digest, tool
versions, operator, date), `drc.json` and `lvs.json` (difference sets with
classification), `pex.csv`, `liberty.csv` and `timing.csv` (metrics and delta
against reference), and `report.md` (pass/fail per test, unresolved differences,
reviewer initials). Every machine-readable output is schema-validated, so a CI
job can assert a result rather than a human reading prose.

## 6. Self-validation before any NDA data

The harness is not used on restricted data until it reproduces a published
answer: sky130 first (self-consistency against the public deck), then gf180mcu
(second process family). A harness that cannot reproduce a known deck is not
evidence about an unknown one.

## 7. Interface

The harness reads a PDK descriptor (`syn/pdk/<name>.pdk`): liberty, LEF, cell
set, layer stack and a readiness flag. A descriptor with `PDK_READY=0` is a
skeleton and the harness refuses to run it; shape is enforced by
`ci/check_pdk_descriptors.sh`. Adding a technology is a descriptor, not a code
change.

## 8. What we need from the partner

1. The reference PDK, its revision string, and the deck version it corresponds
   to.
2. A golden extraction for 20 blocks, and timing signoff for 10, to anchor
   tests 3 and 5.
3. One named reviewer for disputed differences, with an agreed ruling time.
4. Written terms for what may be published about the results.

## 9. Limits and custody

- Not a replacement for the foundry's signoff; their deck stays authoritative.
- Not an equivalence claim beyond the corpus, and not a claim about RET, OPC or
  mask prep, which stay with the foundry.
- Not a publication route for NDA data: the partner approves the report before
  any of it is released.
- Not a schedule commitment; Stage 0 effort is scoped in the proposal §6.
- Harness, corpus format and report schema are Apache-2.0. Reference data, decks
  and partner-supplied layouts remain the partner's property and are deleted
  from the workspace on request, with the deletion recorded in the run log.
