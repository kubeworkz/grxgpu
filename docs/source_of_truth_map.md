# GRXGPU / PTA source-of-truth map

**Status:** Working ownership proposal for the G100–PTA integration program. It does not approve a product specification, supplier, budget, tapeout, or release. Review and ratify ownership where marked open.

## Rule of record

Each artifact has one authoritative home. Component repositories own implementation and raw component evidence; GRXGPU owns the G100–PTA integration contract, integration build/tests, and portfolio decisions. Consumers pin immutable revisions and link evidence; they do not copy mutable source trees or logs. A manifest entry is a pointer and claim record, not evidence that a gate passed.

## Ownership by artifact

| Artifact / decision | Authority | Keep here / link here |
|---|---|---|
| G100 architecture implementation, Vortex RTL, simulators, compiler/runtime/driver, and component regressions | **GRXGPU** | Source and tests live here. The G100 product scope and evidence disposition are summarized in the [G100 brief](grxgpu_g100_product_brief.md) and [G100 evidence manifest](grxgpu_g100_evidence_manifest.md). |
| PTA device architecture, photonic/electronic partition, numerical/error model, calibration algorithms, component RTL/models, and raw prototype measurements | **GRXCP/PTA** (canonical repo URL and named owner to be recorded) | Keep source and primary measurements in GRXCP or controlled measurement storage. GRXGPU links to immutable revision/artifact IDs and records only the G100-facing requirements and integration disposition. |
| G100 ↔ PTA interface and integration implementation: GPU-side interface RTL/driver, address/command/data contract, integration build, and combined-path tests | **GRXGPU**, as the designated integration owner | The interface-control document and integration acceptance evidence live here. Changes to PTA-owned internals flow through a reviewed proposal/revision in GRXCP; do not silently fork component code. |
| GRX930 CPU/SoC/NPU RTL, firmware, and component verification | **GRX930** | Component builds and evidence remain with GRX930. GRXGPU records the pinned revision and only the claims needed by the chosen system integration. |
| Board schematics/layout, BOM, assembly, bring-up, and physical whole-board measurements | **Designated board/PDB project** (canonical repository not yet selected) | Until selected, GRXGPU may hold the cross-project ICD and manifest, but is not a second source for board design files or raw board evidence. |
| Cross-product requirements, G100–PTA integration baseline, portfolio gates, go/hold/stop decisions | **GRXGPU portfolio docs** | Use the [production plan](grxgpu_production_plan.md), [engineering task list](grxgpu_engineering_task_list.md), and the integration manifest template below. Product/supplier authority and named approvers remain governed separately. |
| PDK, supplier, customer, and restricted signoff evidence | **Access-controlled owner storage** | Record a safe controlled-record ID, owner, revision/hash if permitted, reviewer, and claim here; do not copy restricted contents into this repository. |

## Evidence and change rules

1. Pin each component by canonical repository, immutable commit, and tree ID. Branch names are descriptive only; do not use them as reproducibility pins.
2. Keep raw logs, waveforms, generated builds, and physical measurements with the project that produced them. Record durable artifact URI/controlled-record ID and SHA-256 when available.
3. A cross-project acceptance record names its exact source pins, config, tools, workload/input hashes, procedure, expected result, actual result, reviewer, date, and limitations. A link without this context is not a pass.
4. Label evidence as `planned`, `not_run`, `failed`, `passed_pending_review`, or `accepted`; never infer acceptance from a design document, simulation of a different revision, or a successful component-only run.
5. A change to a component-owned interface starts in that component's repo and is consumed here by pinning its reviewed revision. Integration-owned changes are developed and tested here. Coordinate interface-version changes before merging either side.
6. Until the board project and its accountable owner are selected, board-level acceptance remains `not_run` or `blocked`; do not substitute a simulation result for physical-board evidence.

## Current open ownership inputs

- Confirm the canonical GRXCP repository URL, PTA technical owner, and which source tree contains the authoritative chiplet RTL/model.
- Select the canonical board/PDB repository and accountable integration/board owner.
- Ratify the G100–PTA integration owner and interface-change approval path.
- Populate and review [the integration manifest template](grxgpu_integration_manifest.template.json) before declaring a reproducible cross-project baseline.
