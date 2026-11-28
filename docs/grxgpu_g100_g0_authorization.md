# G100 G0 Engineering Authorization

**Status:** Engineering-only G0 authorization recorded; commercial G0 remains on
**HOLD**.
**Gate:** G0 — Product authorization (engineering portion only)
**Date:** 2026-11-20
**Signatory:** Gridworkz — authorized G0 signatory
**Capacity:** G0 engineering signatory only. Gridworkz is not appointed as, and
does not replace, a product sponsor.
**Prior decision:** Kubeworkz — 2026-10-13 discovery scope; unchanged.
**Scope:** Compute-only G100 engineering baseline, with G100-T0 as the proposed
first tapeout.
**Parent records:** [G100 product brief](grxgpu_g100_product_brief.md) ·
[Production readiness plan](grxgpu_production_plan.md) ·
[G100 production baseline](proposals/g100_production_baseline.md)

> **Engineering only.** This record authorizes G1–G3 evidence work and G4
> manufacturing-feasibility work for the G100-T0 engineering baseline. It does
> not authorize a sellable SKU, a commercial product definition, a purchase, a
> foundry slot, physical implementation, tapeout, or production release.
>
> **Commercial G0: HOLD.** No external buyer/design partner, customer workload,
> quality or P99 target, product host/memory interface, target process/package,
> cost, volume, launch, or support commitment is established by this record.
>
> **No sponsor succession.** Gridworkz acts only as the authorized G0 signatory.
> The 2026-10-13 Kubeworkz discovery-scope decision is preserved unchanged;
> Kubeworkz remains the product sponsor of record for that decision. This record
> does not appoint Gridworkz as product sponsor or supersede Kubeworkz.

## 1. Decision

Gridworkz, solely in its capacity as the authorized G0 signatory, authorizes the
G0 engineering items in §3. This is an engineering authorization, not a product-
sponsor appointment or a commercial product approval. It does not assert that
G100-T0 is a sellable product, that an external customer has accepted it, or that
a foundry, package, price, volume, or launch date has been committed.

Where a G0 field has no current product or supplier fact, this record records it
as **TBD** rather than inferring a customer, commercial, or manufacturing
commitment. TBD is a hold disposition, not a waiver and not commercial approval.

## 2. Authority boundary

- **Engineering authority: GRANTED.** Gridworkz authorizes the G1–G3 evidence
  work and G4 manufacturing-feasibility work needed to evaluate the compute-only
  G100-T0 baseline.
- **Commercial G0: NOT GRANTED (HOLD).** The commercial product inputs listed in
  §5 remain unestablished. Do not mark commercial G0 complete or cite this
  record as a sellable-SKU approval.
- **Purchases and tapeout: NOT GRANTED (HOLD).** This record does not authorize
  G4 purchases, G5 implementation, G6 tapeout authorization, a foundry slot, or
  production release.
- **Sponsor role: UNCHANGED.** Kubeworkz is the product sponsor of record for the
  2026-10-13 discovery decision. Gridworkz is named here only as the authorized
  G0 signatory; no product-sponsor appointment or succession is made.

## 3. G0 engineering signatory block

| G0 item | Authorized engineering disposition | Boundary |
|---|---|---|
| Product category | Compute-only programmable GPGPU based on Vortex | Graphics is excluded. Reopening it requires a separate scope decision. |
| First implementation | **G100-T0 engineering die**: one cluster × 16 cores, 4 warps × 4 threads, TCU + DXA, 16 KB LMEM/ICache/DCache per core, no L2, no graphics, SECDED ECC, 256 KB test SRAM, JTAG bring-up, ~10.8 mm², QFN-128 planning package | T0 is a bring-up die, not the first sellable SKU. |
| Product-die direction | The 128-core, 4 × 4 compute-only configuration remains the next candidate; the 128-SM/2,048-thread architecture remains a paper target | Neither product die nor its HBM/PCIe/NVLink assumptions are authorized by this record. |
| Buyer / design partner | TBD; no external buyer or design partner is named | No external customer, market, or acceptance claim is established. |
| Use case | Bring-up and engineering validation of the TCU/DXA compute path | Not a customer workload or product benchmark. |
| Acceptance workload | `sgemm_tcu_wg_dxa` at K=64 and K=512 as the engineering correctness workload | M/N=64 and the current tolerance are test defaults, not ratified customer dimensions or acceptance limits. |
| Quality and P99 latency | TBD | No customer SLA or release-quality threshold is ratified. |
| Power, thermal, frequency, area | T0 engineering envelope: 400 MHz target, 10 W design case, ~10.8 mm² planned die | Engineering planning values, not measured silicon limits or product guarantees. |
| Memory and host interface | T0 uses JTAG plus the 256 KB test SRAM; no host, DRAM, HBM, PCIe, or NVLink interface | A product host and memory boundary remains TBD and requires new RTL, PHY, package, and software work. |
| Process, PDK, package | 28 nm-class process and QFN-128 are planning assumptions only; PDK, libraries, SRAM macros, IO, and package are unselected | No supplier right, quote, capacity, or foundry slot is authorized. |
| Cost, volume, launch, support | TBD | No price, unit volume, launch date, lifecycle, or support commitment is made. |
| Execution authority | Go for G1–G3 evidence work and G4 manufacturing-feasibility work | Hold for G4 purchases, G5 implementation, G6 tapeout authorization, and production release. |
| Named owners | TBD; this record does not assign a product sponsor or technical owners | E-301 remains open until ownership and the remaining evidence are recorded separately. |

## 4. Gate disposition

**Engineering G0: GO (limited).** Gridworkz authorizes only the engineering
baseline and the G1–G3/G4 feasibility work in §3.

**Commercial G0: HOLD — NOT AUTHORIZED.** The commercial inputs remain open,
including external buyer/design partner, customer workload, quality/P99 target,
product host and memory interface, target process/package, cost, volume, launch,
and support.

**G5/G6: HOLD — NOT AUTHORIZED.** No physical implementation, purchase, foundry
slot, tapeout, or production release is authorized.

## 5. Required before commercial G0 can leave HOLD

1. Name the G100 product, architecture, RTL/verification, software, physical
   design, DFT/test, package, and sourcing owners through the responsible
   program authority. This record does not make those assignments.
2. Ratify product-specific quality, power, thermal, area, and latency
   requirements to replace the T0 engineering envelope.
3. Define the product host, DRAM/HBM, DMA, coherency, command ABI, boot, debug,
   and software boundary.
4. Select the target process, PDK, SRAM/IO libraries, package, and supplier
   route, or record a funded deferral.
5. Record the external buyer/design partner, acceptance workload, cost, volume,
   launch, and support commitments.
6. Reconcile the T0 evidence package with the G1 baseline and complete the
   independent E-302 review.

## 6. Signature

**Authorized by:** Gridworkz — authorized G0 signatory

**Capacity:** G0 engineering signature only; not a product-sponsor appointment
or succession.

**Prior sponsor decision:** Kubeworkz — 2026-10-13 discovery scope; preserved
unchanged.

**Date:** 2026-11-20

**Decision:** GO for the G100-T0 engineering baseline through G4 feasibility;
HOLD for commercial G0, G4 purchases, G5 implementation, G6 tapeout, and
production release.

This record is the engineering portion of the G0 decision for the scope stated
above. It is not a commercial G0 pass and does not replace the G1 evidence audit,
G2 interface freeze, G3 hardening evidence, G4 manufacturing closure, or any
later gate approval.
