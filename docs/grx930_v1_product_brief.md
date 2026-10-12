# GRX930 v1 Product Brief — E-001 Draft

**Status:** Draft for product-sponsor review; E-001 is in progress and is **not closed**.
**Version:** 0.1 — 2026-10-10
**Parent:** [GRXGPU Production Readiness Plan](grxgpu_production_plan.md)
**Backlog:** [Engineering Task List, E-001](grxgpu_engineering_task_list.md)

## 1. Candidate product direction

| Decision | Current direction | Evidence / status |
|---|---|---|
| First production candidate | GRX930 embedded edge-inference accelerator for local/on-device inference | Selected for planning; sponsor approval remains pending. |
| Buyer segment | Embedded OEM / system integrator | Target segment selected; no named customer or design partner identified. |
| Compute scope | Four RV64 CPU cores plus one GRX930 8×8 systolic NPU | Selected as product-scope direction. This is **not** a claim of four-core integration, coherency, or physical-board validation. Existing readiness evidence is primarily single-core simulation; four-core behavior remains a release blocker. |
| Workload class | Customer/design-partner inference model for product acceptance; MLPerf Tiny Visual Wake Words (VWW) as interim engineering baseline | VWW selected for reproducible engineering work only. It is not customer acceptance; benchmark artifact/version and customer model/data/operators/metric remain open. |
| Batch / precision | Batch-1; INT8 is the proposed required v1 precision | Keep INT8 as the initial requirement direction, pending sponsor/customer ratification and VWW/customer-model quality evidence. INT4 remains conditional and outside the initial commitment. |
| Product interface | Production host interface not selected | Open. UART/JTAG are proposed for lab bring-up/recovery only, not accepted as the shipped data interface. |
| Memory | External DDR direction | Type, capacity, bandwidth, controller/PHY, topology and package are open. |
| Product category exclusions | Graphics/display, G100-class GPGPU, HBM/chiplets and multi-GPU are not in the candidate scope | Proposed exclusions from the existing child charter; sponsor must ratify or revise them. |

## 2. Customer, workload, and quality

The target deployment is **embedded, local/on-device edge inference** for an embedded OEM or system integrator. No organization or design partner has been named or committed. Product acceptance is intended to use a customer/design-partner model; none has yet been identified.

Use **MLPerf Tiny Visual Wake Words (VWW)** as the interim engineering workload under the pinned, internal-only protocol in [GRX930 VWW Engineering Evaluation](grx930_vww_evaluation.md). This pins the MLCommons `tiny` development snapshot and available reference model identities, but is not an official v1.3 reproduction or a completed GRX930 run. The exact evaluation-corpus/label hashes, model SHA-256, hardware/software identities and operator mapping must be recorded before a run is called reproducible. VWW does not establish market fit, customer acceptance, a release quality threshold, or performance claims. The product-acceptance model remains open until a design partner supplies or approves it.

Before E-001 can close, the sponsor and customer/design partner must provide or approve:

- Named organization and target deployment/use case.
- Interim engineering baseline artifact/version, license/provenance, input dimensions, representative dataset, MLPerf Tiny rules/version, and reproducible harness for VWW.
- Customer model name/version, license/provenance, input dimensions, representative dataset and workload mix.
- Preprocessing, quantization method, supported operators and CPU-versus-NPU partition.
- Quality reference and metric, with an approved tolerance for INT8; INT4 is separately gated if retained.
- Customer-model batch/concurrency and memory footprint, plus a reproducible golden/reference implementation.
- End-to-end P50/P95/P99 latency target and measurement boundary.

Until a customer model and acceptance criteria are approved, there is **no customer acceptance workload, ratified quality target, or product performance claim**. VWW is an interim engineering baseline only, not a substitute for a design-partner acceptance model.

## 3. Product envelope — open decisions

| Requirement | Current value/status | Required decision/evidence |
|---|---|---|
| Host/product interface | TBD | Select interface, board topology and compatibility/driver contract. UART/JTAG remain lab-only proposals. |
| External memory | DDR direction; generation, capacity, bandwidth, controller/PHY TBD | Workload-derived bandwidth/capacity and package/IP evidence. |
| Core count | Four RV64 cores selected as product direction | Integrated RTL/FPGA evidence for boot, scheduling, interrupts, shared memory/coherency and concurrent CPU/DMA/NPU load. If not feasible, return to sponsor for a scope decision; do not silently reduce cores. |
| NPU | One 8×8 systolic array; INT8 proposed required mode | Confirm current RTL/top, supported shapes, command path, numeric semantics and target workload coverage. |
| Power / thermal | TBD | Maximum sustained and peak module/system power, ambient/cooling, throttling and reliability conditions. |
| Form factor / package | Embedded module/SoC direction; TBD | Board/module boundary, package, IO, connector, cooling and installation constraints. |
| Unit economics | Target price/cost, initial and annual volumes, margin TBD | Finance/product-approved target ranges and sourcing assumptions. |
| Launch and lifecycle | TBD | Target launch window, support duration, updates, repair/returns and supplier lifecycle expectations. |

Do not replace TBD entries with generic market or tapeout estimates. Every numeric requirement must record its source, owner, measurement method and ratification status.

## 4. Candidate v1 boundaries

**Included as the current planning direction:** four RV64 CPU cores, one GRX930 8×8 NPU, external DDR, INT8 batch-1 inference, boot/control and the minimum model-load, DMA, execution, result, diagnostics and recovery path required by the selected customer workload.

**Proposed exclusions requiring sponsor confirmation:** graphics/display, general-purpose GPGPU, HBM, chiplets, multi-GPU, broad framework/operator compatibility, and unvalidated INT4 product claims.

The four-core choice is a product requirement to validate, not permission to assume multi-core correctness. Do not freeze RTL or claim product acceptance until concurrency, cache/DMA ownership, reset, failure recovery and the required operating point pass the approved matrix. If the four-core target misses feasibility, document a change proposal and get an explicit product decision.

## 5. E-001 closure checklist

E-001 closes only when all required fields below are complete in a versioned brief and signed by the named product sponsor and required engineering/finance approvers.

| Closure item | Status |
|---|---|
| Candidate SKU and four-core + one-NPU scope | Direction selected; sponsor signature pending |
| INT8 required-mode direction | Proposed required; sponsor/customer ratification and quality validation open |
| Deployment and buyer segment | Embedded local/on-device edge inference; embedded OEM/system integrator selected; named customer/design partner open |
| Interim engineering workload | MLPerf Tiny VWW pinned in [evaluation protocol](grx930_vww_evaluation.md); upstream source is not verified as the v1.3 official code and local corpus/model hashes remain open |
| Customer acceptance workload and model quality metric | Open; blocks closure |
| Ratified P99 latency, power/thermal and memory targets | Open; blocks closure |
| Host interface, form factor and support/lifecycle | Open; blocks architecture authorization |
| Price/cost, volume and funding envelope | Open; blocks business authorization |
| Approved exclusions and release assumptions | Proposed; sponsor confirmation pending |
| Named approver and signed product brief | Open; blocks closure |

**Current decision:** proceed with discovery and evidence collection against this candidate direction. Do not treat this draft as product authorization, an RTL freeze, a funding commitment, a tapeout decision, or evidence that the four-core design has been validated.

## Approval

**Product sponsor:** ____________________  **Date:** __________
**Engineering lead:** ____________________  **Date:** __________
**Finance / commercial approver:** ____________________  **Date:** __________
**Customer/design partner (if applicable):** ____________________  **Date:** __________
