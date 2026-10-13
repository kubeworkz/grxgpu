# GRXGPU Production Readiness Plan

**Status:** Execution-plan proposal; no tapeout, supplier commitment, or production-readiness claim is authorized by this document.
**Version:** 0.2 — 2026-10-13
**Portfolio context:** [GRXGPU Product Family Charter](grxgpu_product_family_charter.md)

## 1. Executive recommendation

The current E-001 product-scope draft selects **four RV64 CPU cores plus one 8×8 NPU** for embedded, local/on-device edge inference. Interim engineering work will use **MLPerf Tiny Visual Wake Words (VWW)** under the [pinned GRX930 evaluation protocol](grx930_vww_evaluation.md), while the customer/design-partner acceptance model and ratified customer workload remain open. This updates the earlier one-control-CPU proposal in the child charter; it remains a product target, not validated multi-core capability. See the [GRX930 v1 Product Brief](grx930_v1_product_brief.md); E-001 remains open pending customer, workload, operating-envelope, commercial, and sponsor approval inputs. The [E-002 evidence manifest](grx930_evidence_manifest.md) is an initial local inventory only; source, FPGA, PDK, and toolchain facts still require owner verification.

Bring GRXGPU to production as a **portfolio of independently gated products**, not as one all-or-nothing chip. Make the **GRX930 edge-inference SoC** the first production candidate, subject to customer and business validation. Advance **G100** as a separately scoped programmable-compute product, and keep **PTA** at measured-prototype stage until its end-to-end system value is demonstrated. A board demo that connects the engines is useful evidence, but does not replace any product's silicon, software, qualification, or supply gates.

Do not start a production tapeout schedule from paper estimates. The GRX930 records report small-shape Verilator results but list physical-board timing/power, larger workloads, multi-core behavior, and target-process synthesis as open evidence; the product charter also says FPGA/PDK identity and rights need confirmation. G100's architecture remains a design target and its tapeout document contains assumptions that must be refreshed. PTA's compute, optical/electronic boundary, and package remain to be proven. Treat these records as a baseline to audit, not proof that any gate has passed.

**Production claim rule:** release each SKU by its own name only after it passes its own acceptance and manufacturing gates. The umbrella GRXGPU portfolio may be called production only for the specific released SKU(s); never infer production readiness for G100 or PTA from GRX930 qualification, or vice versa.

## 1.1 Artifact and project ownership

This GRXGPU repository is the **portfolio control plane**, not a mirror of every component project. It owns portfolio scope and go/hold/stop decisions, cross-product dependencies, shared acceptance policy, the working gate/task ledger, and concise evidence summaries. Component projects own their implementation and primary technical evidence:

| Track / artifact | System of record | GRXGPU portfolio copy |
|---|---|---|
| GRX930 SoC RTL, firmware, build scripts, source-bound simulation/build logs, FPGA/board results, and ASIC implementation evidence | GRX930 source repository and its dedicated Freebuff project | Link to pinned revisions and reviewed evidence; retain only short status/claim-boundary summaries here. Continue GRX930 build and test iteration in that project, not this portfolio worktree. |
| G100 RTL/architecture implementation, compiler/runtime/driver, Vortex regressions and parity, FPGA/AFU and implementation reports | GRXGPU/Vortex source repository; product-specific G100 evidence package | Own G100 production requirements, gate status and cross-track dependencies here; raw build outputs and run logs remain with the source/evidence owner. |
| PTA optical/electronic design, chiplet implementation, calibration/control models, and prototype measurements | GRXCP/PTA component project and controlled measurement storage | Own product-stage decisions and digital-comparison/system-level acceptance policy here; link to the measured source artifacts. |
| Development board design, BOM/assembly, board-level interfaces, bring-up, and shared-system measurements | Designated PDB/board project when its canonical repository is selected; until then, retain the evidence in its named owner-controlled location | Record the integration contract and gate summary; do not establish a second board artifact tree in this repository. |
| Portfolio requirements, cross-SKU release decisions, shared gate policy and task dependencies | This GRXGPU production plan and [engineering task list](grxgpu_engineering_task_list.md) | Authoritative here. Per-SKU specifications and component verification details remain with their track. |
| PDK/IP rights, supplier quotes and restricted signoff collateral | Access-controlled records maintained by the named legal/sourcing/physical-design owner; public checklist/status in the [E-003 matrix](grxgpu_e003_manufacturing_matrix.md) | Store only cleared status, safe references and gate impact; never copy restricted content or credentials here. |

The [GRX930 Linux baseline run record](grx930_production_baseline_linux_run_2026-10-13.md) in this worktree is a dated, scoped evidence summary of one local clean-export run, not the home for further GRX930 build iteration. Keep it as a historical reference; new GRX930 runs, raw logs and technical follow-up belong in the GRX930 project, with this plan updated only when reviewed evidence changes a portfolio gate.

### Gate evidence ownership

| Gate | Portfolio record here | Primary evidence owner |
|---|---|---|
| G0 product authorization | Approved SKU, requirements and decision record | Product sponsor/customer/finance |
| G1 baseline | Cross-track inventory and blockers | Each component owner for source, tools and tests; board owner for board evidence |
| G2 architecture | Portfolio boundaries and cross-product dependencies | System architect for the shared ICD; each component owner for internal interfaces |
| G3 functional/software hardening | Acceptance matrix status and cross-track risks | Track verification/software owners for component results; designated board/PDB owner for end-to-end integration |
| G4 PDK/IP/business feasibility | Public checklist status and hold points | Legal/sourcing/physical design/test/finance owners; restricted records stay access-controlled |
| G5 implementation/signoff | Gate disposition and link to signed result | Product-specific physical-design, verification and test owners |
| G6 tapeout authorization | Go/hold/stop and approval references | Named executive/product/engineering/finance decision-makers in controlled governance records |
| G7–G8 silicon, pilot and release | Product-specific release state and outstanding risks | Product quality/operations/customer and silicon/firmware/test owners |

**Evidence linking rule:** keep one primary copy of each raw artifact. Portfolio summaries cite the product, source commit/tree or archive digest, configuration, artifact path or controlled-record ID, reviewer/date, and the exact claim supported. Do not copy mutable logs or generated build trees between projects. If an artifact must be mirrored for review, label the copy, preserve its checksum, and identify the authoritative original. A gate is not passed merely because a link exists.

## 2. What “production-ready” means

Use the [reviewer-ready E-003 Manufacturing and PDK Closure Checklist](grxgpu_e003_closure_checklist.md) to assess shared manufacturing evidence and separate GRX930, GRXGPU, and PTA routes. A checklist pass is limited to the named product/revision/route and is not tapeout or production authorization.

A product is ready for production only when all of the following are true for its declared SKU and market:

- A named buyer/use case, supported workload set, product requirements, quality/performance/power limits, target cost/volume, and lifecycle/support commitments are approved.
- The product-intent hardware and complete software path pass archived acceptance tests on the intended board/package, with measured results and no open critical defects.
- The exact process, licensed IP, package, production test, supplier capacity, and cost model are confirmed in writing; target-process implementation and signoff have passed.
- First-silicon characterization, pilot yield/reliability, customer acceptance, and corrective-revision policy meet predeclared criteria.
- Firmware, runtime, tools, diagnostics, compatibility/versioning, update and recovery processes have named maintainers and a supported release process.

Numeric limits, sample sizes, qualification conditions, cost thresholds, and dates are **TBD until product and supplier facts are supplied**. Do not copy proposed demonstrator thresholds or old shuttle cost/schedule estimates into a production commitment.

## 3. Program sequence and decision gates

Each gate produces an evidence package and a recorded **go / hold / stop** decision. Work may run in parallel only where the dependency is explicit; passing a later-looking gate does not waive an earlier product decision.

| Gate | Outcome | Required exit evidence | Accountable roles |
|---|---|---|---|
| **G0 — Product authorization** | Choose the first sellable SKU and its market | Signed product brief naming buyer/design partner, use case, acceptance workload, quality and P99 latency target, power/thermal envelope, memory/host interface, target cost/volume, launch and support assumptions. Confirm or revise the E-001 four-RV64-core/one-NPU product target; keep graphics/HBM/chiplets out unless separately justified. | Product sponsor, customer/design partner, finance |
| **G1 — Baseline and evidence audit** | Establish what exists and reproduces | Exact source revision, board/device, FPGA image, toolchain, firmware, PDK/revision and license status recorded in a controlled evidence manifest. Reproduce current simulation results; run the actual board workload if a board is available. Separate “built,” “simulated,” “runs on FPGA,” and “measured on target board.” Findings and blockers are reviewed by independent owners. | Program lead, RTL/FPGA leads, verification |
| **G2 — Product architecture and interface freeze** | Bound the v1 deliverable | Approved system diagram and ICD covering host, memory/DDR, DMA, addressability/coherency, command ABI, reset/clock, debug, boot/update/recovery, package, power and thermal. Named workload has a runnable CPU reference and frozen golden data. Unsupported operators, error handling, timeout and compatibility behavior are specified. | Product, system/SoC, software, board |
| **G3 — Functional and software hardening** | Prove the selected design before physical implementation | Product regression passes on reference and RTL models; board regression passes where hardware exists. Include multi-tile and maximum-size transfers, repeated/concurrent launches, backpressure, reset/recovery, malformed commands, boundary addresses and failure injection. Coherency is proven for the selected core count; otherwise reduce the supported core count. Assertions/formal checks and coverage gaps are reviewed; critical defects are closed. Runtime/firmware, supported-model path, diagnostics, update/recovery and reproducible builds are release candidates. | RTL, verification, firmware/runtime, security as required |
| **G4 — PDK, IP, package and business feasibility** | Prove that this exact SKU can be manufactured and funded | Written confirmation of commercial rights and access for exact PDK and signoff decks; standard-cell and SRAM macros; IO/ESD, clock/reset, DFT, controller/PHY, package/OSAT, probe/test, EDA and foundry route. Target-PDK estimates include memories, pads, DFT, IO/PHY, package and thermal. Cost, schedule, capacity, yield assumptions, NRE and re-spin reserve are reviewed. No critical dependency remains an undocumented assumption. | Physical design, legal/sourcing, test, finance |
| **G5 — Target-process implementation and design signoff** | Deliver a tapeout-quality design | Frozen RTL/netlist and reviewed change control; MCMM timing closure, extracted parasitics, congestion, power integrity/EM, thermal, foundry-deck DRC/LVS/antenna, scan/MBIST and production test collateral pass or have written foundry-approved waivers. Gate-level/DFT tests and final GDS/checksums are archived. Independent design, verification, physical-design, test and product signoff is recorded. | Physical design, verification, DFT/test, independent reviewers |
| **G6 — Tapeout authorization** | Make an explicit irreversible manufacturing decision | G0–G5 evidence is complete; residual risks, accepted waivers, funding, foundry slot, package, test plan, bring-up board, sample count, customer plan and corrective-revision budget are approved by named decision-makers. No schedule pressure or demo pass substitutes for approval. | Executive sponsor, product, engineering, finance |
| **G7 — First silicon and characterization** | Demonstrate functioning, characterized A0 hardware | Controlled bring-up: JTAG/recovery boot, clocks/reset, memory/IO, DMA, compute golden vectors, diagnostics and stress. Characterize across required voltage/temperature/frequency and workload conditions; record power, thermal, yield observations and errata. Decide fix/workaround/re-spin from measured root cause. | Silicon bring-up, RTL, firmware, test, package |
| **G8 — Pilot and production release** | Qualify and support the shipped SKU | Ratified qualification matrix and sample sizes pass; customer workload/quality/SLA targets pass; pilot yield, test time, failure analysis, reliability, supply capacity, unit economics, software release/support and customer acceptance meet their pre-approved limits. Manufacturing, firmware and driver versions are traceable to lots. | Product, quality, operations/sourcing, customer, support |

## 4. Track plans and stop conditions

### GRX930 — first production candidate

Use the existing [GRX930 v1 product charter](grx930_product_charter.md) and [production compute silicon plan](grx930_production_gpu_plan.md) as the detailed child plans. Prioritize a narrow embedded-inference SKU: four RV64 CPU cores plus one 8×8 NPU, external DDR and required INT8 batch-1 path, as selected in the [GRX930 v1 Product Brief](grx930_v1_product_brief.md). Treat four cores as a product target, not validated hardware capability; multi-core boot, coherency, concurrency, FPGA operation and target-PDK feasibility remain explicit blockers.

1. Close G0–G2 around one named customer model, exact module/host contract and product operating envelope; explicitly ratify or revise the four-core/one-NPU target.
2. Reconcile the [readiness report](../grx930/c930/doc/grx930_tapeout_readiness.md) with current source and board evidence. Extend beyond the reported small single-tile Verilator sweep: larger multi-tile cases, sustained and concurrent CPU/DMA/NPU traffic, reset/error recovery, target DDR, repeated launches and actual physical-board measurements.
3. Audit the firmware/software gaps against the shipped-path requirement; the [firmware README](../grx930/c930/sw/firmware/README.md) still lists major integration items as TODOs. Do not call UART echo or GEMM simulation a production host/runtime path.
4. Pass target-PDK feasibility with actual macros/IP, complete top-level area/timing/power, package/IO/DFT and test plan before authorizing physical implementation.
5. The selected candidate is four RV64 cores; prove boot, coherency and interference at that count before architecture freeze. If the evidence fails, return a scope change to the sponsor rather than treating four cores as validated.

**Hold/stop:** no customer workload or product envelope; inaccessible/uncleared PDK rights or missing memory/PHY/signoff IP; unresolved correctness/coherency faults; or target-PDK results outside ratified limits means hold, reduce scope, or stop—never silently relax the acceptance target.

### G100 — separate digital GPU product

The [G100 architecture](designs/gpu_chip_design.md) is a paper design/implementation target, not a production specification. First decide whether the initial G100 SKU is compute-only GPGPU or includes graphics. Define one implementable configuration and workload; keep the 128-core/HBM/PCIe flagship assumptions out of commitments until target-PDK, package, bandwidth and software feasibility prove them. The [G100 tapeout plan](grxgpu_g100_tapeout_plan.md) contains useful engineering measurements alongside aspirational architecture, proxy synthesis estimates, and historical foundry/cost/schedule assumptions; distinguish these categories and refresh each claim against current artifacts and supplier evidence.

**Focused next work in this portfolio project:** bound the candidate and its evidence; do not duplicate component builds or imply that G100 has been funded as a tapeout program.

1. Resolve E-301 to one product hypothesis: compute-only or graphics, one configuration actually represented by the current Vortex source/config, one runnable workload, and explicit host/memory/software boundary. Compute-only is the conservative investigation baseline; product scope still requires sponsor ratification.
2. Establish one immutable evidence baseline: source revision, config overrides, build tools, workload/golden output, and raw result locations. Classify each claim as implemented and reproduced, simulation-only, FPGA-measured, mapped-synthesis proxy, paper target, or supplier-confirmed.
3. Reproduce functional and model-parity evidence using the repository's supported regression gates. Use `xrt` when proving complete RTL/AFU integration; `rtlsim` alone is not full integration. Report FPGA timing/resource results separately from simulation and distinguish measured target-process results from open-library or proxy synthesis.
4. Screen physical feasibility for that same configuration, including logic, on-chip memories, interconnect, host/memory PHY, clocking, DFT, package and test. Reconcile area and memory figures internally and against the actual candidate; the 128-core/HBM flagship and old shuttle figures are not acceptance targets or commitments.
5. Only after the product brief, reproducible workload, and feasibility screen are reviewed should the sponsor decide whether to fund G100-specific G4/G5 work, reduce scope, or defer it. No G100 tapeout schedule or purchase follows from this planning focus.

- Close host link, memory, driver/runtime, compiler/operator coverage, reset/isolation, production test and package as a G100-specific contract.
- Do not enter G5 until the actual target-process implementation includes realistic SRAM, IO, PHY, DFT and interconnect, and meets the G100 product brief.

**Hold/stop:** no bounded SKU/workload; critical dependence on unsourced HBM/PHY/package/software; inability to reproduce RTL results; inconsistent area/memory accounting; or no credible area/timing/power margin means shrink the configuration or defer silicon.

### PTA — measured-prototype gate before product commitment

Treat PTA as a separate module/product track, not an assumption in GRX930 or G100 signoff. Start from a reproducible physical prototype and a declared optical/electronic contract. The existing [weight-set policy proposal](../gen10/docs/proposals/pta_weight_set_policies.md) is a proposal, not product qualification.

- Freeze the initial computation and numeric representation, supported workload, programmable-weight behavior, precision/error budget and software-visible API.
- Measure the complete path: input and weight movement, encoding/programming, optical source and modulation, compute, detection/readout/conversion, calibration, thermal control, post-processing and result transfer.
- Demonstrate repeatable output quality, latency, energy and stability on a fixed workload, including the laser/source, control and measurement equipment required in the intended product boundary.
- Establish module package/coupling, calibration drift, serviceability, test access and supplier route before any production ASIC/package commitment.

**Hold/stop:** no repeatable hardware compute, no system-level benefit over the matched digital baseline, unstable calibration/quality, or unpriced/unsourced optical support components means remain research/prototype-only. Do not count a CPU emulation or core-only optical metric as product success.

## 5. Shared development board and software integration

Use the [Three-Engine Inference Chain](grxgpu_first_board_demo.md) as a controlled integration experiment, not a release gate for every SKU. Confirm engine capability before freezing its proposed tensor shapes, formats and thresholds. Bring up and qualify each module independently first; add common orchestration after per-engine tests pass.

The common platform work should provide versioned device/capability discovery, job submit/complete/error semantics, explicit buffer ownership/alignment/coherency rules, timeout/reset behavior, trace IDs and per-engine adapters. Use explicit copies until zero-copy/coherent sharing is proven. Measure whole-board latency, joules/job, bytes, thermal behavior and failures; include the full data path and PTA support equipment. A shared demo API is not permission to force identical ISA/runtime internals or to claim all tracks production-ready.

## 6. First 4–6 week execution sprint

The GRX930 charter already recommends a 4–6 week validation sprint. Use that as the first decision window; do not mistake it for a full tapeout schedule.

| Timing | Deliverable | Owner(s) |
|---|---|---|
| **Week 1** | Name executive/product/engineering decision owners; pick GRX930 as first candidate or explicitly choose another; obtain customer/design-partner workload and constraints; classify public versus controlled PDK information. | Product sponsor, program lead, customer |
| **Weeks 1–2** | Evidence manifest: exact RTL/source baseline, FPGA board/device and bitstream status, firmware/runtime state, tool versions, PDK/revision/rights, package/IP/supplier status; link each claim to an artifact or mark it unverified. | Engineering leads, sourcing/legal |
| **Weeks 2–4** | Reproduce available simulation and board tests; run gap-based workload/driver checks that the current platform supports; produce defect/risk backlog and first system/host/memory interface draft. No fabricated pass claims if hardware or credentials are unavailable. | RTL/FPGA, verification, software, system |
| **Weeks 4–6** | Review the signed product brief, acceptance matrix, feasibility/IP matrix, top risks, budget and evidence ledger; record go/hold/stop for G2/G3 planning. Establish a resource-loaded schedule only after dependencies, staffing and supplier dates are known. | Program lead, product, technical owners, finance |

**Sprint exit:** a decision package with named SKU/workload, current fact-vs-assumption ledger, reproducible baseline, prioritized verification plan, IP/supply blockers, owners and funded next-stage proposal. If those inputs remain unavailable, the correct result is **hold**, not a guessed tapeout date.

## 7. Program governance and evidence control

Apply the ownership and gate-evidence contract in §1.1: component projects own raw implementation evidence; this repository owns the portfolio ledger and decision trail.

- Maintain one revisioned requirements/acceptance matrix per SKU and one portfolio dependency map. Every numeric threshold has an owner, source, measurement method and ratification status.
- Store evidence with source revision, test configuration, tool versions, input checksums, logs, raw measurements and reviewer. Preserve failures and waived results; never overwrite golden baselines without review.
- Track open issues by severity, owner, due gate and disposition. No open critical correctness, security, safety, manufacturability or supply blocker at the relevant release gate.
- Use change control after architecture/RTL freeze: every change gets impact analysis and affected-gate regression. Keep first-silicon re-spin as a funded risk.
- Keep proprietary PDK, foundry, customer and supplier material in approved controlled storage; public repository documents should contain only information cleared for publication.
- Reassess schedule, NRE, staffing and yield after supplier quotes and implementation evidence. The project plan intentionally makes no cost, date, performance or production-volume promise.

## 8. Engineering task list

The gate-level roadmap is broken into prioritized tasks, dependencies, owner roles, and evidence-based done criteria in the [GRXGPU Engineering Task List](grxgpu_engineering_task_list.md). Use it as the working backlog; named owners and due dates remain to be assigned during sprint kickoff.

## 9. Immediate decisions requested

1. Confirm that GRX930 edge inference is the first production candidate and identify its product sponsor/customer path.
2. Select the named acceptance workload and ratify quality, latency, power, memory, host and cost requirements.
3. Provide verifiable FPGA, source, firmware/runtime and PDK status artifacts; clarify commercial rights and who can approve use.
4. Name accountable owners for SoC/RTL, verification, software, physical design, test, board, sourcing and product.
5. Approve the first 4–6 week evidence sprint and budget; explicitly withhold tapeout approval until G6.
6. Review the G100 E-301 scope/evidence package and decide whether to fund G100-specific engineering or keep it at discovery; the current G100 focus is portfolio planning, not resource or tapeout authorization. Decide PTA resourcing separately.
## References

- [GRXGPU Engineering Task List](grxgpu_engineering_task_list.md)
- [GRXGPU Product Family Charter](grxgpu_product_family_charter.md)
- [GRXGPU First Development-Board Demo](grxgpu_first_board_demo.md)
- [GRX930 v1 Product Charter](grx930_product_charter.md)
- [GRX930 Production Compute Silicon Plan](grx930_production_gpu_plan.md)
- [GRX930 Tapeout Readiness Report](../grx930/c930/doc/grx930_tapeout_readiness.md)
- [GRX930 Firmware README](../grx930/c930/sw/firmware/README.md)
- [G100 Architecture Design](designs/gpu_chip_design.md)
- [G100 Tapeout Plan](grxgpu_g100_tapeout_plan.md)
- [PTA Weight-Set Policy Proposal](../gen10/docs/proposals/pta_weight_set_policies.md)
