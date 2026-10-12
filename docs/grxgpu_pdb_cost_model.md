# PDB Cost Model Guide

**Status:** First-pass planning model. Amounts are not quotes or approved accounting policy. Unknown numeric cost and quantity inputs remain `TBD`; investigations that cannot yet proceed are tracked as `TBA (deferred)` with re-entry gates in the [E-003 matrix](grxgpu_e003_manufacturing_matrix.md). A deferral is not evidence, a waiver, or gate approval.
**Currency:** USD unless a supplier quote requires a different currency; record exchange rate and date before conversion.
**Scope:** MPW lots for the SoC, GPU, and PTA; chip packaging/test/logistics; PDB recurring board BOM and assembly; and one-time engineering/NRE.

## Files

- [Quote-ready PDB BOM](grxgpu_pdb_bom.csv) — per-lot and per-board parts/services with supplier and specification placeholders.
- [Cost model CSV](grxgpu_pdb_cost_model.csv) — route-separated cost line items, inputs, calculation placeholders, and assumptions.
- [ERP account mapping template](grxgpu_pdb_erp_account_mapping.csv) — account-purpose crosswalk with blank ERP account codes/names for the actual chart of accounts.
- [PDB project manifest](grxgpu_pdb_project_manifest.md) — source planning inputs and route constraints.

## Cost boundaries and formulas

Treat three measurements separately:

1. **External project spend:** supplier invoices and internal development spend, including non-recurring charges.
2. **Chip-lot cost:** eligible MPW, packaging, inbound freight, and test cost for each chip lot, tracked by route and lot.
3. **Board unit cost:** chip component costs assigned to boards plus PCB, board components, assembly, and test. Internal chip transfer to board WIP reallocates cost; it is not a second external project expense.

Recommended calculation framework (enter numerical inputs in a spreadsheet or ERP staging workbook; CSV files are templates, not self-calculating spreadsheets):

- `chip_lot_total = slot_count × confirmed_slot_price + route_services + package + test + inbound_freight + other eligible lot costs`
- `good_dies = gross_dies_delivered × accepted_die_yield`
- `cost_per_good_die = chip_lot_total / good_dies`
- `board_starts = target_good_boards / accepted_board_yield`
- `board_recurring_unit_cost = sum(component_qty_per_board × unit_cost) + assembly_per_board + test_per_board + eligible chip costs`
- `board_full_absorption_unit_cost = board_recurring_unit_cost + approved_allocated_NRE_per_good_board`
- `program_cost = SoC_lot_total + GPU_lot_total + PTA_lot_total + board_recurring_total + one_time_NRE + separately tracked engineering`

If any denominator (yield or accepted quantity) is unknown, keep unit cost `TBD`; do not report a zero, infinite, or assumed 100% yield. Model low/base/high scenarios only after identifying defensible quote ranges or clearly labeled sensitivity assumptions.

## Route-specific inputs and caveats

### SoC and GPU — wafer.space GF180MCU Run 3

- The SoC is planned for one full slot; the GPU slot count is unknown pending routed area and written provider acceptance.
- One thousand dies per slot and Q2 2027 shipment are campaign planning inputs, not guaranteed accepted-good-die quantities or project-specific delivery commitments.
- The project supplied $2,000 starting / $8,000 standard for the SoC and a $4,000–$16,000 two-slot GPU estimate. Public Run 3 full-slot price representations conflict: $7,000/$8,000 in a campaign table versus a $7,500 full-slot product listing. Preserve the supplied numbers as unconfirmed planning inputs; use the provider quote/order SKU as the model input.
- The +$1,500 SoC COB add-on is a project estimate; confirm whether per lot, slot, or chip, and what packaging, bonding, test, and shipping it includes.
- Price stitching, reticle assembly, submission, DRC, dicing, packaging, test, freight, and insurance as separate lines only when not already included in the slot/package quote.

### PTA — GF / AMF photonics MPW

- MPW, PDK/technology agreement, DRC iterations, package, optical interface, test, and logistics are quote-dependent.
- Keep the PTA process, run schedule, and platform-specific submissions separate from the wafer.space GF180 assumptions.
- Separate license/access rights, engineering support, manufacturing, package, and test charges if supplier documentation distinguishes them.

### PDB recurring BOM and one-time NRE

- Board component counts, PCB unit cost, assembly/test price, production quantity, test coverage, and yields are not supplied. Populate only from the released schematic/BOM and quotes.
- The BOM includes chip placeholders, PCB, power, connectors, passives, possible external memory, wire bonding, PCBA, board-test firmware, fixtures, and logistics; optional components should be removed or marked not applicable after architecture review.
- Separate recurring PCB cost from artwork, stencils, press-fit/tooling, pick-and-place programming, and test fixtures. Determine whether each fixture/tool is reusable and how costs are allocated to the planned board population.
- Avoid double-counting COB and later wire-bond/assembly charges; confirm the supplier package boundary in writing.

## ERP mapping and accounting guardrails

Use the [ERP mapping template](grxgpu_pdb_erp_account_mapping.csv) to map to the organization's actual account codes and dimensions. Leave account code/name blank until the chart of accounts is available. Possible dimensions include project, chip/product, route/foundry, MPW run, lot, board revision, cost type (recurring/NRE), phase (R&D/manufacturing/sales), grant, and customer. Align the dimensions to ERP capabilities and avoid creating duplicate accounts for costs better tracked by dimensions.

The mapping is a discussion aid only. Prepayments, R&D, inventory/WIP, licenses, equipment, NRE, revenue, and grants depend on applicable accounting guidance, contract facts, capitalization thresholds, and the entity's approved policy. ASC 606 revenue timing depends on transfer of control and customer terms. Tax treatment under IRC §§174/174A is separate from book accounting. Have the controller/accountant and tax advisor approve mapping and posting rules before using the model for journal entries, inventory valuation, or external reporting.

## Deferred work and quote/model completion checklist

The model can be used now to request quotes for defined line items and document assumptions, even if E-003 evidence is unavailable. Keep the distinction clear: use `TBD` for a numerical placeholder in a spreadsheet cell; use `TBA (deferred)` only for a consciously postponed investigation and link it to an E-003 deferral ID with an owner, trigger, affected gate, and resolution deadline. A cost placeholder is not a quote, budget approval, nor proof of affordability.


For each quote, record supplier/legal entity, quote ID, issue/expiry date, currency, tax, incoterms, quantity break, lead time, payment terms, included/excluded services, design acceptance conditions, cancellation/defer/refund rights, and reviewer. Store restricted quotes in controlled storage and put only a safe reference ID in shared documentation.

1. Resolve whether the GRX930 candidate is the PDB SoC; lock RTL/PDK and design revision.
2. Obtain SoC full-slot SKU, current price, packaging option, and route-specific acceptance quote.
3. Obtain GPU die-area fit estimate, allowed slot/stitch arrangement, quote, and submission approval.
4. Obtain AMF platform/run quote, agreement/PDK fee, package/test path, and run schedule.
5. Release a board architecture/schematic and quantity-controlled BOM; source PCB, components, assembly, test, and logistics quotes.
6. Determine delivered die counts, chip yields, board assembly/test yield, sample quantities, rework/scrap treatment, and warranty reserve assumptions.
7. Define shared MPW cost allocation across SoC/GPU (and only allocate to PTA if costs are genuinely shared); obtain finance approval.
8. Map categories to the ERP chart and dimensions; get accounting/tax approval for policy-sensitive treatments.
9. Enter low/base/high scenarios using documented assumptions; reconcile supplier commitments against quote and invoice actuals.

**Completion criterion:** The model is decision-ready only when route-specific quotes, design quantities/area, service inclusions, yields, BOM quantities, scenario assumptions, and ERP mappings are reviewed. Until then it is a structured request-for-quote and planning scaffold, not a budget or committed unit-cost estimate.
