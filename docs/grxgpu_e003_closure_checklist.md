# E-003 Manufacturing and PDK Closure Checklist

**Status:** Review template — no E-003 item is closed by this checklist until evidence is linked, reviewed, and dispositioned.
**Applies to:** GRX930, GRXGPU (including SoC/GPU as applicable), and PTA. Assess each product and foundry route independently; a pass for one chip does not transfer to another.
**Tracker:** [E-003 Manufacturing Inputs Matrix](grxgpu_e003_manufacturing_matrix.md)
**Portfolio intent:** [GRXGPU Production Readiness Plan](grxgpu_production_plan.md)

## 1. How to complete this review

For each row, mark exactly one disposition: **Pass**, **Fail**, **Blocked**, or **N/A with rationale**. `TBD`, `TBA`, planned, verbal, or supplier-marketing statements are not dispositions and do not count as evidence. A deferred item remains open unless the separate deferral approval is recorded; a deferral does not waive a legal, route-acceptance, or required signoff gate.

For every evidence reference, record the controlled repository/vault ID (not a restricted URL in this public checklist), artifact title/revision, supplier or source, date received, reviewer, and review date. Keep contracts, quotes, restricted PDK collateral, credentials, and confidential supplier materials in access-controlled storage. Mark a row **Pass** only when the cited primary evidence supports the claim for the exact product, revision, foundry route, and intended use.

**Current approvals recorded:** Gridworkz accepted proposed E003-D01–D06 target dates on 2026-10-11. Kubeworkz has approved none of the six proposed deferrals as of that date. These schedule facts do not close checklist items. See the [matrix](grxgpu_e003_manufacturing_matrix.md) for each gap, target, and gate.

## 2. Review header and product/route applicability

| Field | Reviewer entry |
|---|---|
| Review ID / revision | TBD |
| Review date | TBD |
| Product under review | Select one: GRX930 / GRXGPU SoC / GRXGPU GPU / PTA |
| Product SKU and scope revision | TBD; attach approved product brief/system boundary |
| Design top / RTL / netlist revision and source digest | TBD |
| Route / provider / shuttle or MPW run | TBD; identify wafer.space GF180MCU vs GF/AMF GlobalShuttle, as applicable |
| PDK name, exact release/commit, variant and corners | TBD |
| Layout stream-out revision / digest / top cell | TBD; record GDS/OASIS and exact format only for this route |
| Slot/order/quote reference | TBD or N/A with rationale; link controlled record |
| Accountable technical reviewer | TBD — named person and role |
| Legal/sourcing reviewer | TBD — named person and role |
| Independent approver / gate authority | TBD — named person and role |
| Overall E-003 disposition | Open / Pass for stated scope / Fail / Blocked — rationale required |

Do not combine multiple products in one “Pass” unless each product has a separately identifiable design revision, route, evidence set, and disposition below.

## 3. E-003 gap closure crosswalk

This crosswalk ties every currently tracked matrix item to the checklist sections needed for its review. Record the evidence reference and disposition in the product/route review header; the gap is not closed while the evidence is absent or the deferral remains unapproved.

| Matrix ID | Gap being closed | Checklist evidence sections | Current state / disposition field |
|---|---|---|---|
| E003-D01 | Product-to-design mapping, including whether GRX930 is the PDB SoC | C-01; 930-01; GPU-01; PTA-01 | Open — record Pass/Fail/Blocked/N/A with rationale |
| E003-D02 | Exact PDK release, variant, and route eligibility | C-02, C-05; 930-02; GPU-03; PTA-01 | Open — record exact revision and evidence reference |
| E003-D03 | PDK/IP rights and manufacturing permissions | C-03; PTA-02 | Open — written rights/route evidence required |
| E003-D04 | Required libraries, macros, signoff inputs, and reproducible flow | C-04, C-05; 930-03; GPU-03; PTA-04 | Open — identify applicable N/A items with rationale |
| E003-D05 | Route, slot/run, orders or documented no-purchase decision, package and schedule | C-06–C-09; 930-04–930-05; GPU-02, GPU-04–GPU-05; PTA-03–PTA-05 | Open — distinguish quote, order, and planning route |
| E003-D06 | Quotes, lead time, cost, yield, and allocation | C-08–C-10; 930-05; GPU-05; PTA-05 | Open — TBD values are not cost-complete evidence |

As of 2026-10-11, Gridworkz accepted the D01–D06 target dates and Kubeworkz had approved none of the proposed deferrals. Verify current status in the [E-003 matrix](grxgpu_e003_manufacturing_matrix.md) before review; accepted dates alone do not close any row.

## 4. Common closure criteria — complete for every product/route

| ID | Reviewer check | Required evidence for Pass | Result | Evidence ref / revision | Reviewer / date / finding |
|---|---|---|---|---|---|
| C-01 | Product and design mapping | Approved product brief/system diagram maps product SKU to exact top design, RTL/source revision, die, board role, and named owner. For GRX930, explicitly resolve whether it is the PDB RISC-V64 SoC. | TBD | TBD | TBD |
| C-02 | Foundry, process, and PDK identity | Provider/foundry documentation and controlled project build manifest identify foundry, process/node, exact PDK release/commit, variant, corners, library family, and eligibility for this route/run. Resolve local competing/stale process-flow artifacts. | TBD | TBD | TBD |
| C-03 | Rights and permitted use | Reviewed license/technology agreement, third-party IP terms, and written manufacturing/route acceptance cover this product, intended use, participants, contractors, and submission. Open-source PDK licensing alone is insufficient. | TBD | TBD | TBD |
| C-04 | IP and design inputs | Complete applicability matrix for standard cells, SRAM/macros, IO/ESD/pads, clocks/resets, analog, DDR controller/PHY if used, DFT/test cells, package/OSAT, and required models/abstracts. Each item has revision, rights, compatibility, status, and owner; N/A items have rationale. | TBD | TBD | TBD |
| C-05 | Signoff collateral and flow | Provider/foundry-supported DRC/LVS/ERC/antenna/extraction/RC and other applicable signoff inputs are versioned and licensed; exact tools, dependencies, configuration, and clean reproducible commands are recorded. | TBD | TBD | TBD |
| C-06 | Area, die, and design fit | Approved die outline/usable area, pad/seal-ring constraints, macro/package area, and route-specific slot allocation are documented and the submitted layout is shown to fit. GPU multi-slot/stitching requires route-provider design-specific approval. | TBD | TBD | TBD |
| C-07 | Stream-out and submission acceptance | Route-specific accepted file format, top cell, hierarchy, layer map, units, naming, checksum, compression/archive, ancillary files, and portal/check requirements are documented. A precheck result is not signoff unless the provider states that it is. | TBD | TBD | TBD |
| C-08 | Package, test, and delivery boundary | Written quote/specification identifies dicing, package/bare-die or COB, wire bonding, probe/final test, yield basis, handling, custody transfer, freight, insurance, and which party performs each operation. Exclusions and double-counted services are reconciled. | TBD | TBD | TBD |
| C-09 | Commercial and schedule basis | Current written order/quote or provider schedule states run/slot, applicable dates, payment/cancellation/defer conditions, minimum demand, price/currency/expiry, lead time, quantities, deliverables, and capacity assumptions. If no purchase is approved, document “not ordered” and the approved planning basis; do not describe a supplier commitment. | TBD | TBD | TBD |
| C-10 | Cost, yield, and allocation | Dated quote/estimate and explicit quantity/yield assumptions support lot cost and per-good-die estimate. Shared costs have an approved, reproducible allocation method; unknown costs/yields remain TBD and prevent a cost-complete Pass. | TBD | TBD | TBD |
| C-11 | Evidence integrity and traceability | Evidence is primary, attributable, revision-specific, access-controlled as needed, and linked to this review. Checksums and reviewer/date are recorded. Marketing, local config presence, or a verbal report alone does not pass. | TBD | TBD | TBD |
| C-12 | Open items, waivers, and deferrals | All findings are listed with owner, severity, gate impact, due date, and closure evidence. Any allowed deferral has item-specific written approval, approver/date, rationale, new due date, trigger, and unaffected-gate analysis. No legal or mandatory foundry signoff requirement is waived by this checklist. | TBD | TBD | TBD |

## 5. Product- and route-specific supplements

Complete the relevant supplement in addition to all applicable common criteria. Do not assume the wafer.space GF180 process/intake requirements apply to AMF photonics, or vice versa.

### A. GRX930 RISC-V64 SoC with NPU

| ID | Reviewer check | Required evidence for Pass | Result | Evidence ref / revision | Reviewer / date / finding |
|---|---|---|---|---|---|
| 930-01 | Product crosswalk | Signed decision states whether GRX930 is the PDB quad-core RISC-V64 SoC; identifies exact SoC scope/revision and PDB integration role. | TBD | TBD | TBD |
| 930-02 | GF180 flow identity | Authoritative GF180 flow and versioned PDK/library/config are tied to the GRX930 RTL/top and selected wafer.space route. SKY130-named flow is classified as separate/stale or corrected. | TBD | TBD | TBD |
| 930-03 | Full SoC implementation inputs | Actual SRAM, pad/IO/ESD, clock/reset, DDR/PHY (or approved memory boundary), DFT and package dependencies are identified, licensed, compatible, and included/explicitly abstracted in the reviewed implementation. | TBD | TBD | TBD |
| 930-04 | SoC route submission | Written wafer.space GF180 run-specific eligibility and acceptance criteria; correct slot/usable area; required template/checker revisions; final stream-out package and submission status. | TBD | TBD | TBD |
| 930-05 | SoC commercial/delivery order | Actual SoC SKU/slot price, quantity, package choice, schedule, minimum-demand/payment/defer terms and wafer.space responsibility through shipment are linked to current order or approved sourcing decision. | TBD | TBD | TBD |

### B. GRXGPU digital GPU

| ID | Reviewer check | Required evidence for Pass | Result | Evidence ref / revision | Reviewer / date / finding |
|---|---|---|---|---|---|
| GPU-01 | Product scope and implementation | Approved GPU product brief maps exact RTL/top, target workload, memory/host/package boundary and supported configuration; do not substitute G100 design aspirations for implementation evidence. | TBD | TBD | TBD |
| GPU-02 | GF180 fit and slot/stitch plan | Measured routed die/reticle footprint, slot count and provider-approved placement/stitch geometry. A generic reticle-stitcher reference is not design acceptance. | TBD | TBD | TBD |
| GPU-03 | GPU-specific IP and PPA | GPU SRAM/macros, IO, clocks, PHY/memory, DFT, package and top-level area/timing/power inputs are route-compatible and assessed in the exact selected PDK/flow. | TBD | TBD | TBD |
| GPU-04 | GPU route submission | Written wafer.space GF180 run-specific multi-slot eligibility (if applicable), submission template/checker revision, layout format, stitching constraints, DRC status, and final package acceptance. | TBD | TBD | TBD |
| GPU-05 | GPU quote/order and supply | Written quote/order defines actual slot count/price, stitching or service charges, die quantity, package/test, shipment and schedule; distinguish quote from purchase commitment. | TBD | TBD | TBD |

### C. PTA photonics accelerator

| ID | Reviewer check | Required evidence for Pass | Result | Evidence ref / revision | Reviewer / date / finding |
|---|---|---|---|---|---|
| PTA-01 | Photonics design and platform | Approved PTA scope maps matrix-vector workload, optical/electrical boundaries, exact AMF process/platform, PDK revision, library stack, and any GF/AMF design services. Do not infer process identity from “90WG” or “45CLO” shorthand. | TBD | TBD | TBD |
| PTA-02 | Technology agreement and rights | Executed technology agreement/quote and access records authorize named users/design, intended research/commercial use, data handling, and required third-party IP. | TBD | TBD | TBD |
| PTA-03 | AMF run and schedule | Current provider-confirmed AMF GlobalShuttle run, MPW eligibility, cutoff, DRC iteration policy, waiver process, and customer-specific dates. | TBD | TBD | TBD |
| PTA-04 | PTA GDS intake and signoff | Controlled AMF-specific GDS requirements, top/layer map, signoff decks, required DRC iterations/waivers, final stream-out and intake acceptance. Do not reuse wafer.space upload assumptions. | TBD | TBD | TBD |
| PTA-05 | Photonics package, test, and supply | Quote/spec defines dicing, photonics package/coupling, optical/electrical test, yield basis, custody, shipment and delivery. Include required source/laser, modulation, detection/readout and calibration equipment in system-level cost/performance boundary where applicable. | TBD | TBD | TBD |

## 6. Findings and overall disposition

| Finding ID | Product/route | Severity (blocker/major/minor) | Requirement / evidence gap | Owner | Due date | Gate impact | Closure evidence / review |
|---|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Choose one overall result for each product/route:

- **Pass — E-003 evidence closure for stated product/revision/route only:** all applicable common and route-specific checks pass; all required owners/reviewers sign; no blocking rights, signoff, route-acceptance, order/sourcing-decision, or cost/lead-time item remains. Scope and exclusions are explicit.
- **Blocked / Open:** required evidence is absent, stale, unreviewed, incompatible, or pending approval. List exact blockers and owners; do not infer closure from accepted target dates or planned route.
- **Fail:** evidence demonstrates the selected route/process/IP is not permitted, compatible, feasible, or accepted. Record decision and required redesign or alternate route.
- **N/A:** only for an inapplicable row, with written rationale and reviewer; “not known” is not N/A.

**E-003 closure is not tapeout approval or production release.** It establishes an evidence-backed PDK/manufacturing-input disposition for the stated design and route. Target-process feasibility/signoff, RTL freeze, tapeout authorization, first silicon, qualification, pilot yield, customer acceptance, and release remain separate gates in the [GRXGPU Production Readiness Plan](grxgpu_production_plan.md) and product-specific plans.

## 7. Sign-off record

| Role | Name | Disposition / scope | Evidence reviewed | Signature / approval reference | Date |
|---|---|---|---|---|---|
| Project DRI | Gridworkz | Open / Pass / Fail — scope required | TBD | TBD | TBD |
| Deferral approver | Kubeworkz | Approve/reject each listed deferral separately; does not waive mandatory gates | TBD | TBD | TBD |
| Physical-design reviewer | TBD | Open / Pass / Fail | TBD | TBD | TBD |
| Sourcing/legal reviewer | TBD | Open / Pass / Fail | TBD | TBD | TBD |
| Package/test reviewer | TBD | Open / Pass / Fail | TBD | TBD | TBD |
| Finance/accounting reviewer | TBD | Cost/allocation evidence only | TBD | TBD | TBD |
| Independent gate authority | TBD | E-003 disposition for named product/route only | TBD | TBD | TBD |

A final reviewer entry must name the specific product(s), revision(s), routes, excluded scope, open findings, and whether each deferral is approved, rejected, or still pending. Keep supplier/PDK evidence in controlled storage and cite only safe record IDs here.
