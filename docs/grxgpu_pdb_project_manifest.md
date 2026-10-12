# AI-Driven RISC-V64 + GPU + PTA Development Board Project Manifest

**Status:** Project planning inputs supplied by the project owner; this is not an approved purchase order, foundry acceptance, accounting policy, or tapeout-readiness determination.
**Project:** AI-Driven RISC-V64 + GPU + Photonics Tensor Accelerator (PTA) Development Board (PDB)
**Target customers:** Research organizations and academia
**Design methodology:** AI-assisted RTL generation and verification
**Planning snapshot:** 2026-10-11

## 1. Project overview

| Attribute | Project plan |
|---|---|
| Board | PDB – AI Development Board |
| Chip 1 | Quad-core RISC-V64 SoC with NPU |
| Chip 2 | Full GPU |
| Chip 3 | Photonics Tensor Accelerator (PTA) |
| GF180MCU route | wafer.space GF180MCU Run 3 for the RISC-V64 SoC and GPU. The project owner states wafer.space fabricates, transfers, dices, packages, and ships these prototypes. |
| Photonics route | GlobalFoundries (GF) / Advanced Micro Foundry (AMF) GlobalShuttle photonics MPW for the PTA; commercial quote and technology/PDK access are required. |
| Board components | SoC, GPU, PTA, PCB, passives, connectors, and power management |
| Intended use | Research and academic development; the plan does not establish production qualification or customer commitments. |

**Manufacturing closure review:** Use the [E-003 reviewer checklist](grxgpu_e003_closure_checklist.md) alongside the [E-003 matrix](grxgpu_e003_manufacturing_matrix.md). The checklist evaluates GRX930, GRXGPU SoC/GPU, and PTA separately; closure for one route does not imply closure for another or authorize production.

**Relationship to GRX930:** The quad-core RISC-V64 + NPU description may correspond to the GRX930 candidate tracked in the [E-002 evidence manifest](grx930_evidence_manifest.md), but the supplied project details do not identify the design revision or formally map the two names. Keep that source/design crosswalk open until the owner confirms it. The [E-003 matrix](grxgpu_e003_manufacturing_matrix.md) tracks rights and manufacturing readiness, not proof of an accepted slot or signoff.

**BOM, cost, and ERP workpapers:** The [PDB BOM](grxgpu_pdb_bom.csv), [cost model](grxgpu_pdb_cost_model.md) and its [cost-model CSV](grxgpu_pdb_cost_model.csv), and [ERP account-mapping template](grxgpu_pdb_erp_account_mapping.csv) are quote-ready planning aids. E-003 gaps that cannot yet be answered are tracked with owners/contributors and proposed target dates in the [E-003 matrix](grxgpu_e003_manufacturing_matrix.md). Gridworkz is recorded as project DRI and accepted the D01–D06 target dates on 11 Oct 2026; Kubeworkz is the separate deferral approver and has approved none of the six proposed deferrals as of that date. Evidence remains due on the accepted targets unless separately deferred by approval. `TBA (deferred)` does not close readiness gates. `TBD` remains for unknown numerical inputs. These workpapers are not approved budgets or posting instructions; populate account codes only from the organization's chart of accounts and after controller review.

## 2. Chip 1 — quad-core RISC-V64 SoC with NPU

### Route, slot, and commercial plan

| Field | Project-supplied entry | Evidence/status note |
|---|---|---|
| Program | wafer.space GF180MCU Run 3 | Run 3 campaign is publicly listed; project order not reviewed. |
| Process | GF180MCU open-source PDK, 180 nm | Confirm exact PDK release/variant, rights, and route eligibility. |
| Slot | One full 1×1 slot | Confirm the design fits the usable area and that the order is placed. |
| Area | Up to 3.88 × 5.07 mm, approximately 19.67 mm² | This is the published usable silicon area; the physical die is listed as 3.93 × 5.12 mm. Do not describe usable area as full die dimensions. |
| Quantity | 1,000 chips per slot | Run 3 campaign states 1,000 dies per slot; quantity, yield, and delivery terms remain order-dependent. |
| Slot price | Project detail says pricing starts at $2,000 and lists $8,000 standard for this full-slot plan | Run 3 public material lists full-slot prices of $7,000 early-bird/$8,000 standard in its price table, but a $7,500 full-slot product listing. The $2,000 starting price is not corroborated as a full-slot price. Confirm actual SKU, price, and eligibility before budgeting. |
| Packaging | Bare die or chip-on-board (COB); project estimate +$1,500 for COB | Confirm package/carrier, quote, wire-bond scope, and shipment terms. Public campaign descriptions differ on bare-die carrier. |
| Payment | Full payment at slot purchase | Project-supplied term; verify in checkout/order terms. |
| Minimum threshold | Shuttle proceeds only if minimum demand is fulfilled | Project-supplied; confirm current campaign terms and refund/defer treatment. |
| Late submission | Design deferred to a later shuttle | Project-supplied; verify the applicable Run 3 policy. |

### Schedule and submission

| Milestone / requirement | Project-supplied plan | Public-source / open item |
|---|---|---|
| Slot purchase deadline | 9 Dec 2026 | Listed on the Run 3 campaign; confirm campaign remains open and applicable. |
| Clean design submission deadline | 16 Dec 2026 | Listed on the Run 3 campaign; exact portal acceptance criteria are separate. |
| Delivery | Q2 2027 | Listed as the campaign shipment window; not a guaranteed receipt date. |
| Submission platform | wafer.space platform | Platform is publicly available; project account/order not verified. |
| Template | `gf180mcu-project-template` repository required | Public template exists; pin its commit and confirm any Run 3-specific instructions. |
| Layout format | GDS or OASIS; compressed files proposed as `.zip`, `.gz`, or `.tar.bz2` | Public precheck documents GDS/GDS.GZ/OASIS; direct platform acceptance of every compression/container type and archive structure needs confirmation. |
| Checksums | Uncompressed GDS/OASIS checksums required | Reticle-stitcher schema uses SHA-256 for layouts; customer upload checksum requirement and exact procedure need confirmation. |
| Design rules | Automated wafer.space checks/DRC | Public precheck describes automated checks; passing those checks is not equivalent to foundry signoff or production qualification. |

## 3. Chip 2 — full GPU

| Field | Project-supplied entry | Evidence/status note |
|---|---|---|
| Program/process | wafer.space GF180MCU Run 3, GF180MCU 180 nm | Same route family as SoC; order and PDK eligibility not verified. |
| Slot plan | One full slot if it fits; otherwise multiple slots or a larger/custom arrangement | The usable area is 3.88 × 5.07 mm per full slot. No GPU layout area or fit result was supplied. |
| Quantity | 1,000 dies per slot | Confirm quantity and treatment for any multi-slot order. |
| Slot pricing | Supplied plan gives $2,000–$8,000 per slot and estimates $4,000–$16,000 for two slots | The $2,000 starting figure is not corroborated for a full slot; public Run 3 full-slot pricing is listed as $7,000/$8,000 in the campaign table and $7,500 in a product listing. Obtain the actual multi-slot quote/order; do not budget from the supplied range as a confirmed full-slot quote. |
| Packaging | Bare die or chip-on-board | Confirm exact package option and quote. |
| Submission | GDS or OASIS; `gf180mcu-project-template` with any needed stitching changes | Pin template and route-specific requirements. |
| Multi-slot handling | Project plan calls for reticle-stitcher integration if the design spans slots | Public reticle-stitcher supports assembling GF180MPW reticles from slot/tile manifests. That alone does not confirm that this GPU can span slots, the permitted geometry, or the vendor's acceptance; obtain a design-specific approval. |
| DRC | wafer.space DRC plus any reticle-stitching constraints | Automated prechecks do not establish final signoff or successful stitching. |
| Schedule | Purchase 9 Dec 2026; submission 16 Dec 2026; delivery Q2 2027 | Same campaign milestones; verify multi-slot designs can meet them. |

## 4. Chip 3 — Photonics Tensor Accelerator (PTA)

| Field | Project-supplied entry | Evidence/status note |
|---|---|---|
| Program | GF GlobalShuttle – AMF MPW (photonics) | GF publicly lists an AMF MPW offering. The specific order/run has not been placed or verified. |
| Process | AMF silicon photonics platform | Exact AMF process variant, stack, design kit, and compatibility must come from the technology agreement and PDK. |
| Access | Commercial; quote required | No quote or agreement reviewed. |
| PDK | Technology agreement and PDK access required | Treat access, use rights, permitted design environment, and data handling as open legal/sourcing gates. |
| Run schedule | Per GF/AMF GlobalShuttle schedule; project notes AMF MPW runs in the 2026–2027 schedule | Public schedule identifies AMF MPW, but exact run months/slot remain to be confirmed through the current schedule/customer channel. |
| Submission cutoff | GDS by the 15th of the previous month, per project plan | GF publicly states this cutoff for securing a shuttle slot; confirm it for the selected AMF run. |
| DRC iterations | Maximum three AMF DRC iterations; violations waived by submission deadline | GF publicly states these limits; obtain the selected run's controlled intake instructions. |
| Format / intake | GDS; official photonics MPW intake | Public information supports GDS and the cutoff. Do not assume wafer.space upload, OASIS, compression, checksums, or its template apply to the AMF route. Get the AMF-specific submission package. |
| Commercial terms | Quote required; confidential provider-controlled design/PDK data; technology agreement required | Project-supplied expectations; verify in signed terms. |
| Brochure | AMF shuttle brochure referenced by project | Store controlled or public copy and revision with the route evidence. |

The PTA is planned as a matrix-vector multiplier on silicon photonics. The supplied references to “90WG” and “45CLO” are not established here as the selected AMF process. Public material separately identifies GF 45SPCLO; do not conflate that platform with AMF. Record exact process/platform only from the selected AMF PDK and agreement.

## 5. Development board (PDB) assembly

| Field | Project-supplied plan | Status / follow-up |
|---|---|---|
| Board name | PDB – AI Development Board | Product definition and board specification are still to be approved. |
| Chip sources | Internal inventory from MPW runs | Depends on successful fabrication, receipt, acceptance, and inventory records for all three chips. |
| PCB fabrication | External vendor; non-recurring engineering (NRE) costs expected | Vendor, stack-up, quote, design rules, and lead time not supplied. |
| Assembly | SoC + GPU + PTA, PCB, passives, connectors, and power management | BOM, footprint/package compatibility, yield/rework plan, and assembler not supplied. |
| Chip integration | Wire-bonded chip-on-board PCBs; wafer.space reference designs cited | Verify which parts/package options support this assembly and obtain vendor-approved bonding/assembly instructions. |
| Bonding diagram | Required for wire-bond packaging | Project requirement; confirm template and approval owner with the package/assembly provider. |
| Firmware/software | Embedded software development planned | The tax treatment is separate from book accounting and depends on the work and tax year; see §7. |
| Test firmware | Board-level test firmware required for validation | Define coverage, fixtures, acceptance criteria, and source revision. |
| Chip delivery | Q2 2027 target for all three chips | PTA date depends on a selected AMF run; do not assume it matches wafer.space delivery. |
| PCB and assembly | Q3 2027 target | Vendor schedule and component availability unverified. |
| Board validation | Q4 2027 target | No validation results exist in this project plan. |
| First academic shipments | Q1 2028 target | Commercial, support, regulatory, and delivery commitments are not established. |

## 6. Consolidated planning summary

| Item | Route | Process | Planning cost | Submission / milestone | Target delivery | Draft tracking account |
|---|---|---|---:|---|---|---|
| RISC-V64 SoC | wafer.space | GF180MCU, 180 nm | Supplied $2,000 starting / $8,000 standard; public full-slot values differ ($7,000/$8,000 table; $7,500 listing) | 16 Dec 2026 | Q2 2027 | WIP – Foundry (wafer.space) |
| GPU | wafer.space | GF180MCU, 180 nm | Supplied $4,000–$16,000 for two slots; obtain actual design-specific quote | 16 Dec 2026 | Q2 2027 | WIP – Foundry (wafer.space) |
| PTA | GF / AMF | Silicon photonics; exact platform to be confirmed | Quote required | 15th of month before selected run | Per AMF schedule | WIP – Photonics (GF/AMF) |
| PDB | Internal board assembly | N/A | PCB NRE + BOM + assembly; not yet quoted | Board assembly Q3 2027 | First shipment target Q1 2028 | Inventory – WIP / Finished Goods (PDB) |

## 7. Draft accounting and cost tracking (for accountant review)

The following entries reproduce the project's proposed account mapping for planning; they are not an approved accounting policy or a conclusion under U.S. GAAP or tax law. Account classification depends on the actual contract, stage of work, rights, future use, control, and applicable accounting standards. Separate research and development, foundry production, inventory, equipment/tooling, license, board NRE, grant, and customer-contract costs in the ledger. Do not capitalize all chip-development spending solely because a chip is intended for sale.

### Proposed journal-entry examples

| Event | Debit | Credit | Amount / treatment |
|---|---|---|---|
| SoC slot purchase (early-bird example) | Prepaid Foundry Costs (Asset) | Cash / Accounts Payable | $2,000; use the actual invoice and review whether it is a deposit/prepayment. |
| SoC design submission | WIP – Foundry (wafer.space) | Prepaid Foundry Costs | $2,000, subject to actual contract and stage-of-work accounting. |
| SoC chips received | Inventory – Finished Goods (RISC-V64 SoC) | WIP – Foundry | Transfer accumulated eligible manufacturing cost; do not assume slot price is total landed cost. |
| SoC chip-on-board add-on | Inventory – Finished Goods or applicable package cost | Cash / Accounts Payable | Project estimate +$1,500; confirm quote and accounting policy. |
| GPU slot purchase (two-slot example) | Prepaid Foundry Costs | Cash / Accounts Payable | Project estimate $4,000–$16,000; confirm slot count and actual price. |
| GPU design submission | WIP – Foundry (wafer.space) | Prepaid Foundry Costs | Same amount as prepaid, adjusted to actual invoice/contract. |
| GPU chips received | Inventory – Finished Goods (GPU) | WIP – Foundry | Transfer eligible accumulated manufacturing cost. |
| PTA quote / technology agreement | Prepaid Photonics Costs, license/intangible, R&D expense, or other account as determined | Cash / Accounts Payable | Quote amount; classify each deliverable/contract right before posting. |
| PTA GDS submission / MPW charge | WIP – Photonics (GF/AMF) | Applicable prepaid / payable account | Actual contracted amount; distinguish R&D from manufacturing and service elements. |
| PTA chips received | Inventory – Finished Goods (PTA) | WIP – Photonics | Transfer eligible accumulated manufacturing cost under approved policy. |
| PCB NRE | R&D – PCB Development (project proposal) | Cash / Accounts Payable | NRE amount; capitalization may be appropriate only if the applicable asset/contract criteria are met. |
| Chips transferred to board WIP | Inventory – WIP (PDB) | Inventory – Finished Goods (chips) | Internal cost using the approved allocation/transfer method. |
| PCB/components purchased | Inventory – WIP (PDB), or expense/asset as applicable | Cash / Accounts Payable | Actual eligible BOM cost. |
| Board assembly completed | Inventory – Finished Goods (PDB) | Inventory – WIP (PDB) | Accumulated eligible board cost. |
| Board sale to university | Accounts Receivable | Revenue – Board Sales | Recognize when control transfers under the customer contract; delivery is not automatically the recognition point in every arrangement. |
| Cost of goods sold | COGS – Development Boards | Inventory – Finished Goods (PDB) | Cost associated with boards whose revenue is recognized. |

### Accounting policy decisions to resolve

- **R&D versus inventory/tooling:** Under U.S. GAAP, qualifying R&D is generally expensed as incurred. Determine which activities qualify under the applicable guidance; production inventory, equipment, and assets with alternative future use may follow different guidance. “AI-designed” does not itself determine treatment.
- **Tooling and NRE:** Analyze each item under the applicable asset or contract-cost guidance. “NRE” or customer reimbursement alone does not establish capitalization.
- **PTA/PDK rights:** A contract may contain an identifiable, reusable license right, research-only access, services, or a combination. Determine recognition and useful life from the signed terms; do not assume every PDK/access fee is an intangible asset.
- **Shared MPW costs:** Establish and consistently apply an allocation method for shared shuttle, reticle, package, test, and handling costs across SoC and GPU designs. Document the chosen basis and any costs specific to one design.
- **PTA cost tracking:** Track quote, technology agreement, PDK access/license, MPW, DRC, packaging, and test separately until terms are known.
- **Revenue:** Under ASC 606, recognize revenue when control of the promised board transfers; delivery is often relevant but is not a universal trigger. Evaluate shipping terms, customer acceptance, title, right to payment, support, and any distinct obligations.
- **Software tax treatment:** IRC §§174/174A tax treatment is distinct from book accounting. Under current U.S. law, qualifying domestic research expenditures for tax years beginning after 31 Dec 2024 are generally deductible under §174A, subject to elections and transition rules; qualifying foreign research remains subject to §174 capitalization/amortization rules. Whether particular embedded-firmware or chip-development costs qualify, and how costs are sourced/allocated, requires tax-professional review; do not infer a blanket result from the board plan.
- **Grants:** Track restricted grant proceeds and allowable costs separately according to the award terms and applicable accounting framework; determine whether separate fund accounting or revenue deferral is required with the grant administrator/accountant.

## 8. Evidence and open decisions

1. Confirm whether the SoC in this PDB plan is the GRX930 candidate; identify exact RTL/PDK revisions and owners.
2. Obtain the wafer.space order, selected slot SKU, binding price, eligible design area, minimum-demand terms, payment/refund/defer conditions, package choice, and delivery terms.
3. Confirm GPU layout fit; obtain written approval and quote for any multi-slot/reticle-stitching arrangement.
4. Pin the GF180 PDK/template/checker revisions and exact upload formats, archive rules, checksum procedure, hierarchy/top-cell/layer expectations, and acceptance criteria.
5. Select the AMF process/MPW run; obtain quote, technology agreement, PDK rights, controlled submission instructions, package/test plan, and schedule.
6. Confirm die shipment/receipt, custody transfer, quantity, dicing, packaging, and acceptance documentation for each route.
7. Produce board schematics, PCB/vendor quote, BOM, package/bonding compatibility, assembly plan, test firmware, and validation criteria. Maintain the [BOM](grxgpu_pdb_bom.csv), [cost model](grxgpu_pdb_cost_model.md), and [ERP account-mapping template](grxgpu_pdb_erp_account_mapping.csv); obtain the actual ERP chart of accounts before filling account codes.
8. Have a qualified accountant and tax professional approve cost allocation, journal policy, revenue timing, license treatment, grants, and current-year tax treatment.

Until these items are evidenced, all commercial values, schedule dates, accounting entries, and manufacturing steps in this manifest remain project planning inputs—not accepted supplier commitments or readiness findings. Items unavailable now may be proposed for deferral in the [E-003 register](grxgpu_e003_manufacturing_matrix.md), with accountable owner, approver, re-entry trigger, affected gate, and latest resolution point. They remain due on accepted dates unless approved, are not waived, and do not close E-003; applicable acceptance evidence is still required.

## 9. Public references

Provider sources corroborate service descriptions, not the project's order or contract:

- [wafer.space GF180MCU Run 3 campaign](https://www.crowdsupply.com/wafer-space/gf180mcu-run-3) — campaign quantity, milestones, packaging options, and pricing information.
- [wafer.space slot specifications](https://mith.ro/gf180mcu-project-template/) — usable slot area versus physical die dimensions.
- [wafer.space GF180MCU project template](https://github.com/wafer-space/gf180mcu-project-template).
- [wafer.space submission platform](https://platform.wafer.space/) and [GF180 precheck repository](https://github.com/wafer-space/gf180mcu-precheck) — public submission/precheck information.
- [wafer.space reticle-stitcher repository](https://github.com/wafer-space/reticle-stitcher) — public reticle assembly tool and layout-manifest schema.
- [GF GlobalShuttle MPW program](https://gf.com/manufacturing/services/multi-project-wafer-program/) — AMF MPW, GDS cutoff, and DRC iteration notes.
- [GF acquisition announcement for AMF](https://gf.com/news-and-events/news/globalfoundries-acquires-advanced-micro-foundry-accelerating-silicon-photonics-global-leadership-and-expanding-ai-infrastructure-portfolio/).
- [EUROPRACTICE photonics overview](https://europractice-ic.com/technologies/photonics/) and [AMF process page](https://europractice-ic.com/technologies/photonics/amf/) — distinguish provider/platform descriptions; the selected AMF process still requires confirmation.
- [26 U.S.C. §174](https://www.law.cornell.edu/uscode/text/26/174), [26 U.S.C. §174A](https://www.law.cornell.edu/uscode/text/26/174A), and [Public Law 119-21](https://www.govinfo.gov/content/pkg/PLAW-119publ21/html/PLAW-119publ21.htm) — current U.S. tax provisions; consult current law and a tax professional.
- [Grant Thornton on ASC 730 R&D accounting](https://www.grantthornton.com/insights/alerts/tax/2022/insights/capitalizing-r-and-e-expenditures-requires-detail-focus) and [Deloitte on ASC 606 point-in-time control](https://dart.deloitte.com/USDART/home/codification/revenue/asc606-10/roadmap-revenue-recognition/chapter-8-step-5-determine-when/8-6-revenue-recognized-a-point) — secondary guidance references; the applicable Codification and contract facts govern.
- [IRS §41/ASC 730 FAQ](https://www.irs.gov/businesses/corporations/faqs-irc-41-qres-and-asc-730-lbi-directive) — limited IRS FAQ; it is not an official pronouncement of law.
