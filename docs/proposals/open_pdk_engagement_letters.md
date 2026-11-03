# Open PDK Engagement Letters — IHP and SkyWater (draft)

**Status:** Draft correspondence. Not sent, not approved, and not a commitment by
either party. Every name, address and figure in square brackets must be filled
by the named owner before issue; the programme terms quoted here are the ones
published in November 2026 and must be re-checked against the current price list
and participation agreement at the time of sending.
**Date:** 2026-11-03
**Scope:** §12.7 of [the open 28 nm PDK program proposal](open_28nm_pdk_program.md).
**Rule for both letters:** ask only for what §12.7 lists, offer only work we can
actually do, and never imply a production commitment, a purchase, or a
partnership that has not been agreed in writing.

---

## 1. Why these two, and in this order

The proposal's §12.8 sequence puts a validated 90/130 nm engagement ahead of any
28 nm conversation. IHP and SkyWater are the two organisations that can grant
that first yes: both have released an openly licensed PDK themselves, so neither
has to be persuaded that the model is possible, only that our kit makes their
next release cheaper. IHP is approached first because SG13G2 is the most complete
openly licensed PDK backed by a foundry pilot line, and because its open MPW
terms are published rather than negotiated from zero.

Neither letter names a 28 nm foundry candidate. That conversation comes after a
signed agreement exists, not before.

## 2. Clause coverage

| §12.7 clause | IHP letter | SkyWater letter |
|---|---|---|
| 1. Recipient and screening | closing paragraph: NDA and participation agreement before any restricted material | closing paragraph: same, plus export screening of the receiving entity |
| 2. Tool independence | item 1: re-expression for an open flow, their decks stay signoff | item 2: same for SKY130/SKY90FD |
| 3. Publication split | item 4 and the closing paragraph | item 3 and the closing paragraph |
| 4. Price and payer | item 2: current tiers and participation agreement, published terms only | item 1: not a funding request, terms only |
| 5. Limits | item 2: area cap, design count, cadence | item 1: named per programme |
| 6. Deliverable and deadline | item 3: the 16 KB macro as the first dual-deck result | item 3: corpus and report |
| 7. Status tag | closing paragraph: no production claim, preview tag respected | opening and closing: SKY90FD's preview status acknowledged |

---

## 3. Letter to IHP

> **To:** [Recipient name], [Title]
> **Organisation:** IHP — Leibniz-Institut für innovative Mikroelektronik
> **Address:** [postal address as published at time of sending]
> **From:** [Sender name], [Title], [project], [email]
> **Date:** [date]
> **Subject:** Open-flow re-expression of SG13G2 and participation in the open-silicon MPW programme

Dear [Recipient name],

We maintain Vortex, an open-source RISC-V GPGPU, and are preparing the physical
implementation of a 28 nm design on a foundry PDK. Before that work begins we
are building an open **PDK enablement kit**: a conformance harness that proves an
open re-expression of a foundry PDK — KLayout DRC/LVS, open LEF/Liberty/GDS —
produces the same answers as the foundry's own decks within stated tolerances. A
harness that cannot reproduce a known-good open PDK cannot be trusted on a
closed one, so we are calibrating first on sky130 and then on SG13G2.

We are writing to IHP because SG13G2 is the most complete openly licensed PDK
backed by a foundry pilot line, and because your open-silicon MPW programme is
the clearest published example of how an open tier is funded and administered.
We would like to discuss four things.

**1. Permission to re-express SG13G2 for an open flow.** We would produce
KLayout-compatible DRC and LVS decks, and open library views, from your published
data. Signoff would remain on IHP's decks; our re-expression would be an
additional path for design exploration, not a replacement for your signoff. Any
publication of the re-expression would follow your terms and your review.

**2. Access under the open-silicon MPW programme.** We would like the current
participation agreement, the area cap and design count per shuttle, the shuttle
cadence for [year], and the price for both the standard and the open-source
tiers. We are asking for the published terms, not a discount.

**3. A first dual-deck result.** Our first concrete test is a 16 KB SRAM macro
that must be clean under both your deck and our re-expression, with the
difference documented rather than asserted. We would send you the report before
publishing anything.

**4. Publication and status.** We would like to know what we may publish about
the equivalence results and what stays with IHP, and how you would want the
preview/alpha status of SG13G2 described in anything we write.

What we bring is engineering work, not a request for data: we will do the
re-expression and the correlation, publish only material IHP approves, and hand
over the harness and the equivalence report. We are not asking for
redistribution rights, for confidential data to be published, or for a
production tag on SG13G2.

Before any restricted material is exchanged we will sign IHP's NDA and the
programme participation agreement, and we will complete whatever export
screening IHP requires of the receiving entity.

Would a 30-minute call in the next few weeks be possible? We can send the
harness specification and the PDK descriptor contract in advance.

Yours sincerely,

[Name], [Title]
[Project], [email], [phone]

---

## 4. Letter to SkyWater

> **To:** [Recipient name], [Title]
> **Organisation:** SkyWater Technology
> **Address:** [postal address as published at time of sending]
> **From:** [Sender name], [Title], [project], [email]
> **Date:** [date]
> **Subject:** Open-flow re-expression and validation for SKY130 and SKY90FD

Dear [Recipient name],

We maintain Vortex, an open-source RISC-V GPGPU, and are preparing the physical
implementation of a 28 nm design. Before that work begins we are building an open
**PDK enablement kit**: a conformance harness that proves an open re-expression
of a foundry PDK — KLayout DRC/LVS, open LEF/Liberty/GDS — produces the same
answers as the foundry's own decks within stated tolerances. We plan to calibrate
it on sky130 first, then on gf180mcu, so the method is proven on more than one
process family before we ask any fab to rely on it.

SKY130 is the most widely used open PDK, and SKY90FD is the most instructive
unfinished one: its experimental-preview status is the kind of gap the kit is
meant to narrow. We understand the original release was funded by Google rather
than by wafer revenue, and we are not writing to ask SkyWater to fund anything.

We would like to discuss three things.

**1. SKY90FD status and contribution.** What would move SKY90FD from
experimental preview toward a supported release, and would an external team be
able to contribute validation — DRC/LVS coverage, PEX correlation, cell library
characterisation — under your review? We would scope any contribution so it
does not create a support obligation you have not agreed to.

**2. Open-flow permission.** Under the existing SKY130 licence, is re-expression
for a KLayout/OpenROAD flow permitted, and would SkyWater review a published
equivalence report before it is relied on? We would keep your decks as the
signoff reference and would not present a re-expression as a substitute for them.

**3. A concrete corpus and report.** We would send a defined layout corpus
(roughly 100 layouts including known-marginal cases), the DRC difference set,
LVS results on 100 library cells, and PEX deviation on 20 blocks — the harness
specification's tolerances, reported as measured rather than asserted.

On publication: we would publish only what SkyWater approves. We are not asking
for redistribution rights beyond what the existing licence already grants, for
confidential data to be published, or for a production claim on any preview
release. We will sign an NDA and complete export screening of the receiving
entity before any restricted material is exchanged.

Would a 30-minute call in the next few weeks be possible? We can send the
harness specification, the descriptor contract, and a sample equivalence report
in advance.

Yours sincerely,

[Name], [Title]
[Project], [email], [phone]

---

## 5. Send checklist

- [ ] Named owner assigned, with authority to sign an NDA on the project's behalf.
- [ ] Legal review of the export-control sentence and of any reference to a
      future 28 nm partner. Neither letter names one.
- [ ] Current IHP price list and participation agreement pulled on the day of
      sending; the € figures live in the proposal, not in the letters.
- [ ] Current SkyWater PDK licence text checked, so item 2 of that letter asks
      only about permission the licence does not already grant.
- [ ] Recipient identity and address confirmed from the organisation's own site,
      not from a search summary.
- [ ] Sender's institutional email and a project URL that a recipient can check.
- [ ] Send logged in the engagement record with date, recipient and any
      documents attached.

## 6. What these letters deliberately do not do

- They do not promise a shuttle purchase, a volume, or a schedule.
- They do not claim that an open 28 nm PDK exists, or that either organisation
  has agreed to anything.
- They do not ask for a production tag, and they explicitly respect the preview
  status of both organisations' open releases.
- They do not offer to publish anything the recipient has not approved.
- They do not describe the kit as replacing commercial signoff.

## 7. Related documents

- [Open 28 nm PDK program proposal](open_28nm_pdk_program.md) — §12.7 clauses and
  §12.8 sequence these letters implement.
- [Harness specification](open_pdk_harness_spec.md) — the attachment both letters
  offer to send in advance.
- [GRXGPU production plan](../grxgpu_production_plan.md) — §1.1 ownership rule
  for restricted PDK collateral, and gate G4.
