# G100-T0 ECC — Conditional D3 Error-Reporting Amendment

**Status:** Draft, conditional, **not applied**. Apply only after S0 signs D3 as
`Accept`. Editing either requirement document before that signature would
pre-empt the gate.
**Date:** 2026-11-20.
**Source decision:** [ECC closure plan](g100_t0_ecc_closure_plan.md) §2.3;
[S0 decision signoff](../evidence/g100-t0-ecc-s0-2026-11-20/signoff.md) D3.
**Documents changed when applied:** [production baseline](g100_production_baseline.md)
and [T0 tapeout checklist](../grxgpu_g100_t0_tapeout_checklist.md) only.
**Not changed:** the closure plan, G1 audit, S0 signoff (apart from an amendment
note in D3), and any RTL. No RTL work starts from this proposal.

## 1. Scope

D3 replaces the "raise a fault, halt or trap" model with: an uncorrectable
error is never returned as corrected data; the LMEM returns the stored word and
sets a sticky per-array flag; a cache invalidates the affected line so the next
access refetches; per-request signalling (bus error or precise exception) is a
T0-B item. The address and syndrome are available through the debug path.

This amendment is independent of the [D1 32+7 amendment](g100_t0_ecc_d1_32_7_amendment.md).
The baseline edit is a phrase replacement that matches whether or not D1 has
landed; it does not touch the codeword-width sentence. If both are accepted,
apply either first.

## 2. Production baseline edit

### B1 — ECC paragraph (`g100_production_baseline.md:301`, phrase)

The surrounding sentence is:

```markdown
  ~0.2 mm² on T0. A correctable error increments a counter; an uncorrectable
  one raises a fault the debug path can read. Without this, first silicon cannot
  distinguish a soft error from a logic bug.
```

Replace only this phrase:

Before:

```text
raises a fault the debug path can read
```

After:

```text
is never returned as corrected data: the LMEM sets a sticky per-array flag and a cache invalidates the affected line, with the address and syndrome readable through the debug path
```

Resulting sentence:

```markdown
  ~0.2 mm² on T0. A correctable error increments a counter; an uncorrectable
  one is never returned as corrected data: the LMEM sets a sticky per-array
  flag and a cache invalidates the affected line, with the address and syndrome
  readable through the debug path. Without this, first silicon cannot
  distinguish a soft error from a logic bug.
```

The 0.2 mm² and check-bit text is deliberately untouched; that is D1's edit.
The sentence survives D1's rewrapping because only the phrase changes.

## 3. Tapeout checklist edits

### C1 — Uncorrectable error (`g100_t0_tapeout_checklist.md:115-117`)

Before:

```markdown
- [ ] **Uncorrectable error.** Never return silent bad data. The reporting
  action and any logged address or syndrome follow the error policy once it is
  ratified; no policy is ratified yet.
```

After:

```markdown
- [ ] **Uncorrectable error.** Never return silent bad data. An uncorrectable
  error sets a sticky per-array flag on LMEM or invalidates the affected cache
  line; the array, address and syndrome are logged. No bus error or exception
  is raised at T0; per-request signalling is T0-B.
```

### C2 — Bring-up step 6 (`g100_t0_tapeout_checklist.md:280-282`)

Before:

```markdown
6. **ECC.** Inject a correctable and an uncorrectable error through the debug
   path; confirm the counters and the error response. *Blocked in T0-A: no ECC
   RTL exists, and LMEM is not on the SBA path.*
```

After:

```markdown
6. **ECC.** Inject a correctable and an uncorrectable error through the debug
   path; confirm the counters and the sticky flag or line invalidation. *Blocked
   in T0-A: no ECC RTL exists, and LMEM is not on the SBA path.*
```

The T0-A scope and the "no ECC RTL" blocker are unchanged. D13's TSRAM-only
evidence scope still applies; this item names the reporting action, not a new
array target.

## 4. Apply procedure after signoff

1. Confirm the S0 record carries `Accept` for D3, and that no condition changes
   the reporting model.
2. Apply B1 as a phrase replacement, then C1 and C2 by exact string
   replacement. Do not touch codeword-width, counter or area text.
3. Record the amendment date in the D3 record's Notes field; no other signoff
   text changes.
4. Re-run the link check, trailing-whitespace check and LF check over the two
   files. Commit the baseline and checklist together; keep the signoff note in
   its own commit.
5. Do not start the cache invalidation or LMEM flag RTL from this amendment;
   S3/S4 in the plan are separate gates.

## 5. Verification

- `grep -n "raises a fault the debug path can read"` over the baseline must
  return no hits after B1.
- `grep -n "follow the error policy once it is ratified"` and
  `grep -n "confirm the counters and the error response"` over the checklist
  must return no hits after C1/C2.
- The replacements must not introduce "fault", "halt" or "trap" as the T0
  reporting action; the only allowed mention is the negative "No bus error or
  exception" sentence and the T0-B note.
- D1's width text, the counter item and the test-SRAM paragraphs are expected
  to be unchanged by this proposal.
- No RTL, CI lane, register map or S0 signature is changed by this proposal.

## 6. Risks

- **Premature edit.** Applying before S0 signs would turn a conditional draft
  into an unratified baseline change. The status line is the guard.
- **Coupling to D1.** Rewriting the whole baseline paragraph would make this
  amendment depend on D1's exact wording. B1 is phrase-level for that reason;
  keep it that way in review.
- **Scope creep to T0-A.** The checklist item describes the eventual reporting
  action, not three-array silicon evidence. D13 still limits T0-A to the test
  SRAM, and the item stays blocked until ECC RTL exists.
- **Promising a fault path.** "Sticky flag or line invalidation" must not drift
  back into "fault" or "trap" during editing; that would contradict D3 and the
  interface evidence in the signoff.
