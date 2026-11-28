# G100-T0 ECC — Conditional D1 Amendment (32+7)

**Status:** Draft, conditional, **not applied**. Apply only after S0 signs D1 as
`Accept` for 32+7 on the 32-bit LMEM and ICache slices. Editing either
requirement document before that signature would pre-empt the gate.
**Date:** 2026-11-20.
**Source decision:** [ECC closure plan](g100_t0_ecc_closure_plan.md) §2.1;
[S0 decision signoff](../evidence/g100-t0-ecc-s0-2026-11-20/signoff.md) D1.
**Documents changed when applied:** [production baseline](g100_production_baseline.md)
and [T0 tapeout checklist](../grxgpu_g100_t0_tapeout_checklist.md) only.
**Not changed:** the closure plan, G1 audit, S0 signoff (apart from marking its
D1 caveat resolved), and any RTL. No RTL work starts from this proposal.

## 1. Scope

D1 keeps 64+8 for the 64-bit DCache slice and for XLEN=64 builds, and uses
32+7 for the 32-bit LMEM and ICache slices at the T0 configuration. Five
requirement statements and five derived area figures assume 64+8 everywhere.
This proposal records the exact replacement text for each, so the amendment is
a mechanical edit after signoff.

The D3 text in the baseline ("an uncorrectable one raises a fault") is separate
from this amendment and is left untouched, even though D3 proposes different
behaviour; changing both at once would conflate two decisions.

### Check-bit arithmetic used below

All three arrays are 16 KB, so 393,216 data bits total.

| Array | Codewords at T0 | Check bits | Overhead |
|---|---:|---:|---:|
| LMEM, 32-bit words | 4,096 × 39 | 28,672 | 21.9% |
| ICache, 32-bit slices | 4,096 × 39 | 28,672 | 21.9% |
| DCache, 64-bit slices | 2,048 × 72 | 16,384 | 12.5% |
| **Total** | | **73,728** | **18.75%** |

The present all-64+8 assumption has 49,152 check bits (12.5%). The area figures
are scaled linearly from the baseline's 0.2 mm² ECC estimate: 0.2 × 1.5 =
0.3 mm², taking the 10.8 mm² die to 10.9 mm². This is a planning estimate, not a
synthesis result; §5 records how to replace it.

## 2. Production baseline edits

### B1 — ECC row (`g100_production_baseline.md:207`)

Before:

```markdown
| ECC | SECDED 64+8 on LMEM, ICache and DCache; **no RTL yet** (P10) | Production SRAM does not ship without it. The 256 KB test SRAM is bring-up storage and is outside this requirement. Closure work and the unsigned decisions are in the [ECC closure plan](g100_t0_ecc_closure_plan.md); the gate record is the [S0 decision signoff](../evidence/g100-t0-ecc-s0-2026-11-20/signoff.md). |
```

After:

```markdown
| ECC | SECDED 32+7 on the 32-bit LMEM and ICache slices and 64+8 on the DCache slice and XLEN=64 builds; **no RTL yet** (P10) | Production SRAM does not ship without it. The 256 KB test SRAM is bring-up storage and is outside this requirement. Closure work and the unsigned decisions are in the [ECC closure plan](g100_t0_ecc_closure_plan.md); the gate record is the [S0 decision signoff](../evidence/g100-t0-ecc-s0-2026-11-20/signoff.md). |
```

### B2 — ECC paragraph (`g100_production_baseline.md:299-302`)

Before:

```markdown
- **ECC.** SECDED on each 64-bit word: eight check bits, 12.5% area overhead,
  ~0.2 mm² on T0. A correctable error increments a counter; an uncorrectable
  one raises a fault the debug path can read. Without this, first silicon cannot
  distinguish a soft error from a logic bug.
```

After:

```markdown
- **ECC.** SECDED with seven check bits on each 32-bit word and eight on each
  64-bit word: 18.75% check-bit overhead across the three arrays, and ~0.3 mm²
  on T0 (linear estimate from the 0.2 mm² all-64+8 figure; confirm at
  synthesis). A correctable error increments a counter; an uncorrectable one
  raises a fault the debug path can read. Without this, first silicon cannot
  distinguish a soft error from a logic bug.
```

### B3 — Die row (`g100_production_baseline.md:211`)

Before:

```markdown
| Die | ~10.8 mm² with ECC, pads, clock tree, 256 KB test SRAM | 9.0 mm² + 0.2 ECC + 0.6 test SRAM + ~1 mm² overhead |
```

After:

```markdown
| Die | ~10.9 mm² with ECC, pads, clock tree, 256 KB test SRAM | 9.0 mm² + 0.3 ECC + 0.6 test SRAM + ~1 mm² overhead |
```

### B4 — T0 summary (`g100_production_baseline.md:46`)

Before:

```markdown
with a measured logic area and a working RTL path, at ~10.8 mm² with ECC, pads
```

After:

```markdown
with a measured logic area and a working RTL path, at ~10.9 mm² with ECC, pads
```

## 3. Tapeout checklist edits

### C1 — SECDED width (`g100_t0_tapeout_checklist.md:110-112`)

Before:

```markdown
- [ ] **SECDED on all three arrays.** 64 data bits + 8 check bits on LMEM,
  ICache and DCache; encode on write, decode on read. The code is Hsiao or
  equivalent, with the parity matrix recorded.
```

After:

```markdown
- [ ] **SECDED on all three arrays.** 32 data bits + 7 check bits on the
  32-bit LMEM and ICache slices; 64 data bits + 8 check bits on the DCache
  slice; encode on write, decode on read. The code is Hsiao or equivalent,
  with the parity matrix recorded.
```

### C2 — Fault injection (`g100_t0_tapeout_checklist.md:122-124`)

Before:

```markdown
- [ ] **Fault injection.** Each bit of a 72-bit codeword is flipped in
  simulation: single-bit errors correct, double-bit errors flag, no false
  correction. The test is part of the regression, not a one-off.
```

After:

```markdown
- [ ] **Fault injection.** Every single-bit position of a 39-bit or 72-bit
  codeword is flipped in simulation and corrects; every double-bit pair (741 or
  2,556) flags with no false correction. The test is part of the regression, not
  a one-off.
```

### C3 — Area and timing (`g100_t0_tapeout_checklist.md:127-129`)

Before:

```markdown
- [ ] **Area and timing.** 12.5% bit overhead and the encode/decode delay are
  accounted in the 10.8 mm² die estimate and the 400 MHz timing; the delta is
  reported, not absorbed silently.
```

After:

```markdown
- [ ] **Area and timing.** 18.75% check-bit overhead across the three arrays
  and the encode/decode delay are accounted in the ~10.9 mm² die estimate and
  the 400 MHz timing; the delta is reported, not absorbed silently.
```

### C4 — Die size (`g100_t0_tapeout_checklist.md:151-154`)

Before:

```markdown
- [ ] **Die size and aspect ratio.** ~10.8 mm² including the 256 KB test SRAM,
  pad ring and ECC; the actual size and the delta from the estimate are
  recorded. The test SRAM's attachment point is new RTL, not a port the current
  configuration already exposes.
```

After:

```markdown
- [ ] **Die size and aspect ratio.** ~10.9 mm² including the 256 KB test SRAM,
  pad ring and ECC; the actual size and the delta from the estimate are
  recorded. The test SRAM's attachment point is new RTL, not a port the current
  configuration already exposes.
```

### C5 — Header scope line (`g100_t0_tapeout_checklist.md:9`)

Before:

```markdown
core, no L2, SECDED ECC, 256 KB test SRAM, 400 MHz, 10 W, ~10.8 mm², QFN-128.
```

After:

```markdown
core, no L2, SECDED ECC, 256 KB test SRAM, 400 MHz, 10 W, ~10.9 mm², QFN-128.
```

C5 is already listed in the signoff's D1 caveat (checklist `:9`), so it needs
no separate caveat edit beyond the status update in §4 step 3.

## 4. Apply procedure after signoff

1. Confirm the S0 record carries `Accept` for D1 with 32+7, and that no
   condition changes the width.
2. Apply B1–B4 and C1–C5 by exact string replacement. Do not touch D3 text.
3. Update the signoff D1 caveat from "requires an explicit baseline amendment"
   to "amended `<date>`"; checklist `:9` is already listed.
4. Re-run the link check, trailing-whitespace check and LF check over the two
   files. Commit the baseline and checklist together; keep the signoff update
   in its own commit.
5. Do not start the codec or any RTL from this amendment; S1 in the plan is a
   separate gate.

## 5. Verification and estimate discipline

- `grep -n "64+8 on LMEM, ICache and DCache\|each 64-bit word\|72-bit codeword\|12.5% bit overhead"` over the two files must return no requirement hits after
  the edit. The plan §7 and audit test-SRAM 64+8-per-lane figures are expected
  to remain and are not part of this grep target.
- `18.75`, `0.3` and `10.9` must agree across B2–B4 and C3–C5.
- The 0.3 mm² and 10.9 mm² values are linear planning estimates. When S1/S2
  synthesis or the memory compiler reports ECC area, replace them with the
  measured delta and record the source; if the measured area exceeds the
  estimate, revise the die row and the checklist item together.
- No RTL, CI lane, register map or S0 signature is changed by this proposal.

## 6. Risks

- **Premature edit.** Applying any part before S0 signs would turn a conditional
  draft into an unratified baseline change. The status line at the top is the
  guard.
- **Area linearity.** SRAM area does not scale exactly with check bits; 0.3 mm²
  could be off in either direction. It is labelled an estimate in both
  documents, not a measured result.
- **Mixed widths.** Readers may apply 32+7 to the DCache or to XLEN=64. Both
  texts state the 64+8 exceptions explicitly; check them in review.
- **D3 bleed.** While editing the ECC paragraph it is tempting to replace
  "raises a fault" with the D3 proposal. Do not; that requires its own signed
  decision and a separate amendment.
