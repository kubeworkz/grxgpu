# Open 28 nm PDK Program — What Is Buildable, What Is Not, and the Route to Production

**Status:** Proposal. It scopes a program and states its gates. It does not
approve a foundry, a budget, an NDA, a process, or a tapeout, and it is not
evidence for any number in the tapeout plan.
**Date:** 2026-11-03
**Scope:** [G100 tapeout plan](../grxgpu_g100_tapeout_plan.md) §3 and §8, the
[16 KB ORRAM record](../grxgpu_g100_evidence_manifest.md) §5, the
[PDK descriptor contract](../../syn/pdk/README.md), and the 28 nm area and
process assumptions of [the G100 baseline](g100_production_baseline.md) §5.
**What it answers:** whether Vortex can build its own openly licensed 28 nm PDK,
what such a program would actually produce, and whether it can ever become a
production PDK.
**What it is not:** a tapeout path, a substitute for a foundry PDK, or a claim
that an open 28 nm process is achievable by effort alone.

---

## 1. Summary

1. **The proposal bundles three goals that have different owners.** Designing
   28 nm silicon with open tools is ours to do; publishing an open 28 nm PDK
   requires the fab's data and the fab's consent; having a foundry support *our*
   PDK is a process-development contract, not a tapeout arrangement.
2. **A PDK is a warranty, not a data bundle.** Models, decks, PEX and EM/IR
   limits are measurements of one fab's silicon plus that fab's yield and
   reliability liability. Those cannot be authored, only measured and granted.
3. **The frontier of foundry-released open PDKs is 55 nm.** ICsprout's ICS55
   (Apache-2.0, October 2025) is preview-only, non-production, ships **Calibre**
   decks, and its first shuttle silicon came back in September 2026. No foundry
   has released or announced a 28 nm open PDK. SkyWater's 90 nm effort
   (SKY90FD) has sat at "experimental preview" for years.
4. **What is genuinely buildable is the layer in between:** an open PDK
   enablement kit — the descriptor contract already started in `syn/pdk/`, plus
   a conformance harness that *proves* an open re-expression of a fab PDK
   produces the same DRC, LVS, PEX and timing answers within stated tolerances.
   It is calibrated on sky130 and gf180mcu, whose decks and silicon are public.
5. **A route to production exists, but it is gated by a fab, not by us.** The
   only successful open PDKs were released by fabs. Our lever is making that
   release cheap: hand a fab a validated open package and the marginal cost of
   publishing falls from years of work to a review. Without that partner there
   is no production PDK, open or otherwise.
6. **Recommendation:** target 55 nm for the *open* experiment, keep 28 nm
   silicon on an NDA PDK with an open flow, and do not make G100's tapeout wait
   on this program.

---

## 2. What a PDK is, and which parts can be authored

| Component | Authorable by us? | Where it comes from |
|---|---|---|
| DRC deck (thousands of rules) | Only re-expressed | The fab's Calibre/SVRF source; re-expression must be proven equivalent |
| LVS / device extraction | Yes | KLayout + Netgen against device definitions the fab states |
| SPICE models, corners, mismatch | **No** | IV/CV measurement on that fab's silicon, per Vt flavor, per IO voltage |
| PEX (ITF/TLU+, width-spacing RC) | **No** | Field solve on the fab's stack, calibrated to their golden extraction |
| Standard cells (1000+ at 28 nm) | Yes, against a real PDK | Characterization compute, not invention |
| SRAM bitcell / compiler | **No** | Foundry-supplied; custom bitcells need their approval |
| IO / ESD, latch-up | **No** | TLP and HBM/CDM testing, fab-qualified structures |
| EM / IR limits, reliability (HCI/BTI) | **No** | The fab's qualification data |
| OPC / RET / SRAF, mask prep | **No** | Foundry tapeout service |
| Density, fill, CMP, seal ring, PCM | Partly | Rules from the fab, generation is automatable |

The distinction that decides this program: **the missing ingredient is silicon**.
A corner model is a measurement, not a document. A deck is a liability promise,
not a specification of "28 nm".

The second constraint is acceptance. We found no foundry program at or below
28 nm that signs off GDS against a customer-authored deck or customer rule file;
foundries sign off on their own decks because yield and liability ride on them.
Absent evidence of such a program, this document assumes none exists.

---

## 3. Evidence: what exists today

| PDK | Node | Origin | Status | Lesson |
|---|---|---|---|---|
| [SKY130](https://github.com/google/skywater-pdk) | 130 nm | SkyWater / Google | Apache-2.0, manufacturable, still "experimental preview" | Works because the fab released it |
| [GF180MCU](https://gf.com/about-gf/innovation/university-partnerships/) | 180 nm | GlobalFoundries / Google | Apache-2.0, shuttle access now intermittent | Same model; the shuttle can disappear |
| [IHP SG13G2](https://www.ihp-microelectronics.com/services/research-and-prototyping-service/open-source-design-enablement) | 130 nm SiGe | IHP | Apache-2.0, "alpha / early access", 100+ fabricated designs, LibreLane flow | Best-functioning open PDK, still not tagged production |
| [ICS55](https://github.com/openecos-projects/icsprout55-pdk) | 55 nm | ICsprout + Zhejiang University / ECOS | Apache-2.0, **preview, barred from production**, Calibre decks, first silicon Sept 2026 | Frontier of the model, and it took a foundry, a university and public funding |
| [SKY90FD](https://github.com/google/sky90fd-pdk) | 90 nm FDSOI | SkyWater / Google | "Experimental preview / alpha", no production tag | A well-resourced 90 nm attempt did not finish |
| [OpenRPDK28](https://github.com/RIOSLaboratory/OpenRPDK28) | 28 nm | RIOS Lab (academic) | Template only; layer map plus one GF180 model file | What "28 nm open PDK" means today |
| [ASAP7](https://asap.asu.edu/) | 7 nm | ASU + ARM | "Not manufacturable", cells shipped 4× scaled | Predictive kits are research aids |
| [FreePDK45](https://eda.ncsu.edu/freepdk/freepdk45/) | 45 nm | NCSU | PTM-based, "no variation information in the PEX rules" | Still predictive nearly two decades later |

Two conclusions follow. First, **every open PDK that works was released by the
fab that owns the process**; none was authored by a customer. Second, the
difficulty is not linear in node: 180 → 130 nm is open and productive, 90 nm is
stalled, 55 nm arrived this year as a preview, and 28 nm is empty. A program
that starts by authoring 28 nm starts at the hardest point on that curve.

---

## 4. Three goals, separated

| Goal | What it needs | Owner | Verdict |
|---|---|---|---|
| A. Design G100/PTA at 28 nm using open tools | A fab PDK under NDA, an equivalence-proven open flow, commercial signoff | Us + a fab | Buildable now; this is the real objective |
| B. Publish an openly licensed 28 nm PDK | The fab's data, models from its silicon, its redistribution licence | The fab | Not ours to decide; can be made cheap |
| C. A foundry supports *our* PDK | Process-development engagement, their decks replaced by ours | The fab, as a paid development contract | Not a tapeout; not recommended |

C is the reading to retire. No fab will accept a customer's process definition
at 28 nm, and buying one means owning a process, not shipping a chip.

---

## 5. What we will build: the open PDK enablement kit

### 5.1 The descriptor contract

`syn/pdk/*.pdk` already carries one technology's liberty, LEF, cell set, layer
stack and readiness flag, and `ci/check_pdk_descriptors.sh` enforces its shape.
That file is the kit's interface: one descriptor per technology, independent of
which foundry produced it, with `PDK_READY=0` marking a skeleton.

### 5.2 The conformance harness

Given a fab PDK (under NDA) and an open re-expression of it, the harness proves
equivalence instead of asserting it. Proposed tolerances are engineering
targets to be agreed with the partner, not measured results.

| Test | Reference | Proposed pass criterion |
|---|---|---|
| DRC equivalence | Fab's Calibre deck | Empty violation-set difference on a corpus of ~100 layouts, including known-marginal cases |
| LVS | Fab's deck | 100 % match on 100 library cells and 10 placed blocks |
| PEX | Fab's golden extraction | R, C within 5 % per net; delay within 3 % on 20 blocks |
| Liberty / CCS | Fab's characterization | Cell delay and transition within 3 %; leakage within 2 %, all corners |
| Timing | PrimeTime on the fab's Liberty | Block WNS within 20 ps and 5 % on 10 blocks |
| Fill / density | Fab's rules | Density and CMP checks clean on the same corpus |

### 5.3 Calibration target

sky130 first, then gf180mcu. Both have open decks and proven silicon, so the
harness can be shown to reproduce a *known* answer before any NDA data enters
its scope. A harness that cannot reproduce an open 130 nm deck will not
reproduce a 28 nm one, where the rule count and patterning complexity are an
order of magnitude higher.

### 5.4 Outputs

Open-format decks (KLayout DRC/LVS), open library views (LEF, Liberty, GDS,
CDL), an equivalence report per PDK revision, and the descriptor. **No NDA data
is published, ever.** The public tree holds tooling, contracts, test vectors and
reports; the data stays with the fab.

---

## 6. Program stages and gates

| Stage | Deliverable | Exit criterion | Kill criterion |
|---|---|---|---|
| **0** (0–3 mo) | Descriptor contract, harness skeleton, sky130 round-trip | DRC diff empty on 100 layouts; LVS 100 % on 100 cells; PEX within 5 % on 20 blocks | Harness cannot reproduce sky130 within a quarter |
| **1** (3–9 mo) | Fab engagement: NDA PDK, open-flow permission, first port | The 16 KB ORRAM macro DRC-clean under both decks, accepted by the fab's pre-tapeout check | No NDA plus open-flow permission within 12 months |
| **2** (9–18 mo) | Starter library (200–400 cells) characterized with open tools, cross-checked | Characterization within 5 % of commercial on a 50-cell sample | Deviation persists past 5 % after two char iterations |
| **3** (18–30 mo) | Test chip: PCM, ring oscillators, SRAM block, one small GPU tile | Silicon within model prediction; deck signoff repeated end-to-end | Two silicon spins without correlation to models |
| **4** (fab-led) | Optional: fab publishes an open PDK built from this work | The fab's legal and business decision | Never a decision we can make |

Stage 1 is the real gate. Nothing before it needs a foundry; nothing after it
matters without one.

---

## 7. Can it become a production PDK?

**Yes, along exactly one route, and the trigger is a fab's decision, not our
engineering effort.**

"Production" is not a property of data completeness. It is a warranty: this GDS
will yield, these models predict silicon, this deck will pass the foundry's
tapeout review, and someone is liable if it does not. Our kit can produce the
first three as *evidence*; only the fab can issue the warranty.

| Route | What it means | Precedent | Assessment |
|---|---|---|---|
| **A. Fab releases openly** | The fab publishes its own PDK, using our kit to make that cheap | sky130, gf180mcu, SG13G2, ICS55 | The only route with working examples. Realistic only if our output saves the fab years |
| **B. Production use, closed data** | We ship 28 nm silicon on their NDA PDK, validated with an open flow | Standard commercial practice | This is the G100/PTA route, and it is available without route A |
| **C. Predictive kit, correlated over time** | Author a predictive 28 nm kit, narrow its error with each shuttle | None; FreePDK45 remains predictive nearly two decades on | Low probability, multi-shuttle cost, and the fab's deck still governs signoff |

Route A is the one a "production open 28 nm PDK" would take, and the honest
conditions are these:

- models extracted from that fab's silicon at all corners, with mismatch, noise
  and aging;
- decks proven equivalent on a corpus the fab accepts, not just by us;
- PEX correlated to their golden extraction within an agreed tolerance;
- a library that is DRC/LVS clean, EM/IR clean, characterized at every PVT
  corner, and silicon-validated;
- SRAM macros from their compiler; IO/ESD qualified for HBM/CDM and latch-up;
- reliability qualification and yield data, which only the fab has;
- a redistribution licence, which is a legal instrument, not an engineering one.

On timing: ICS55 reached a 55 nm preview with a foundry, a university and public
funding. A third party authoring 28 nm, then persuading a fab to adopt it, is a
multi-year effort with a low prior. Plan for 3–5 years *if* a partner commits,
and treat "no partner" as the default outcome, not the failure case.

---

## 8. Cost order of magnitude

Shuttle cost dominates and does not shrink because the flow is open. The
[tapeout plan](../grxgpu_g100_tapeout_plan.md) §3 already carries the 28 nm
numbers; this program adds:

- **Characterization compute**: a 200–400 cell library at several PVT corners
  is thousands of CPU-hours with open tools (CharLib plus ngspice) — rentable,
  but not free, and slower than commercial characterization.
- **Test-chip spins**: at least two, each at full shuttle cost, before a product
  die is credible.
- **Engineering**: one to two engineers for the harness, plus a physical-design
  owner for decks and correlation. This is the long pole, not the EDA licences.
- **Commercial signoff**: PrimeTime/Tempus, StarRC/QRC and Calibre are not
  replaced by this program at 28 nm; the kit reduces how much they are needed,
  not whether they are.

---

## 9. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Fab will not grant open-flow permission | Routes A and B both stop | Secure permission before porting anything; make it Stage 1's gate |
| Deck equivalence cannot be proven at 28 nm | Signoff stays commercial-only | Prove the harness on sky130/gf180 first; corpus includes marginal layouts |
| Model error without silicon | Numbers look precise and are wrong | No model enters the tapeout plan or evidence manifest without a silicon record |
| Patterning (double patterning, OPC) | Layouts clean in our deck fail at mask prep | Keep mask prep with the fab; do not claim RET coverage |
| SRAM and IO are not authorable | Blocks missing at integration | Licence compiled SRAM; use fab IO cells |
| Program starves G100 | Tapeout slips for a research goal | G100 stays on the foundry PDK path; this program runs in parallel, separately staffed |

---

## 10. Decisions needed

1. **Is the target 28 nm or 55 nm?** ICS55 is open, has silicon, and carries
   none of the 28 nm unknowns. 28 nm has no open PDK anywhere.
2. **Which fab is approached, and by whom?** The NDA and the open-flow
   permission are commercial negotiations, not engineering tasks.
3. **What is the budget envelope for two test-chip spins?**
4. **Does a predictive 28 nm kit have enough internal value** (G100 PPA studies
   before silicon) to justify authoring it while a fab partner is sought? If
   yes, it is a quarter of work and must be fenced off as non-silicon.

---

## 11. Non-goals

- Replacing a foundry's deck for signoff.
- Publishing any NDA data, model file or deck we did not author.
- Building a 28 nm SRAM bitcell or IO/ESD library.
- Claiming a manufacturable process without silicon behind it.
- Blocking G100 or the PTA chiplet on this program's schedule.

---

## 12. Related documents

- [G100 tapeout plan](../grxgpu_g100_tapeout_plan.md) — fabrication path, cost
  rows, and the 28 nm area scaling this program would have to validate.
- [PDK descriptor contract](../../syn/pdk/README.md) — the kit's interface.
- [G100 production baseline](g100_production_baseline.md) — the configuration
  whose area figures a real 28 nm PDK would replace.
- [G100 evidence manifest](../grxgpu_g100_evidence_manifest.md) — where a
  silicon-calibrated result would have to be recorded.
