# GRXGPU / PTA source-of-truth map

**Status:** Working ownership proposal for the G100–PTA integration program. Dave Cook is the named PTA technical owner; this does not approve a product specification, supplier, budget, tapeout, or release. Review and ratify remaining component/board and integration ownership where marked open.

## Rule of record

Each artifact has one authoritative home. Component repositories own implementation and raw component evidence; GRXGPU owns the G100–PTA integration contract, integration build/tests, and portfolio decisions. Consumers pin immutable revisions and link evidence; they do not copy mutable source trees or logs. A manifest entry is a pointer and claim record, not evidence that a gate passed.

## Ownership by artifact

| Artifact / decision | Authority | Keep here / link here |
|---|---|---|
| G100 architecture implementation, Vortex RTL, simulators, compiler/runtime/driver, and component regressions | **GRXGPU** | Source and tests live here. The G100 product scope and evidence disposition are summarized in the [G100 brief](grxgpu_g100_product_brief.md) and [G100 evidence manifest](grxgpu_g100_evidence_manifest.md). |
| PTA device architecture, photonic/electronic partition, numerical/error model, calibration algorithms, component RTL/models, and raw prototype measurements | **GRXCP/PTA** — [canonical public repository](https://github.com/kubeworkz/grxcp); PTA technical owner: **Dave Cook** | Pin implementation/model evidence to immutable GRXCP revisions below. Keep source and primary measurements in GRXCP or controlled measurement storage. GRXGPU records only the G100-facing requirements and integration disposition. |
| G100 ↔ PTA interface and integration implementation: GPU-side interface RTL/driver, address/command/data contract, integration build, and combined-path tests | **GRXGPU**; accountable integration owner: **to be confirmed** | The interface-control document and integration acceptance evidence live here. Changes to PTA-owned internals flow through a reviewed proposal/revision in GRXCP; do not silently fork component code. Dave Cook's named assignment is PTA technical ownership, not portfolio approval or an assumed GRXGPU integration assignment. |
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

## Verified GRXCP/PTA source pin

At the 2026-10-18 lookup, GitHub's `main` endpoint for the canonical public [`kubeworkz/grxcp`](https://github.com/kubeworkz/grxcp) repository resolved to immutable commit [`9667adec5e8f07a5415a2832a1622ee9c93d87ab`](https://github.com/kubeworkz/grxcp/commit/9667adec5e8f07a5415a2832a1622ee9c93d87ab), root tree `bd518a4bd4c8fe9d3d5365d1e5af3020c6e76bc7`. Use the full commit/tree IDs as the current evidence pin; `main` is only the lookup reference and may move.

| Pinned artifact | Immutable path/blob ID | Evidence boundary |
|---|---|---|
| PTA register map | [`docs/designs/pta_chiplet_regmap.md`](https://github.com/kubeworkz/grxcp/blob/9667adec5e8f07a5415a2832a1622ee9c93d87ab/docs/designs/pta_chiplet_regmap.md), blob `469b272bf2a6b5ea4e67619122b863fd4bb35b98` | Design/interface evidence, not proof of a hardware implementation. |
| PTA program plan | [`docs/designs/pta_program_plan.md`](https://github.com/kubeworkz/grxcp/blob/9667adec5e8f07a5415a2832a1622ee9c93d87ab/docs/designs/pta_program_plan.md), blob `666488bb9f6a613ff1e89d257ef88b21229fe274` | Contains C930/NPU FPGA synthesis work; its `xc7a200tfbg484-1` reference is not a PTA stand-in target selection. |
| PTA board transport | [`docs/designs/pta_board_transport.md`](https://github.com/kubeworkz/grxcp/blob/9667adec5e8f07a5415a2832a1622ee9c93d87ab/docs/designs/pta_board_transport.md), blob `e76a3c6aa3cf1e66efaee23bc2ecb6c89bd42664` | Records a CXL 2.0 Type-1 / PCIe 5.0 design decision and model; explicitly says no module, root port, or driver implementation exists. |
| PTA module queue model | [`src/backends/pta_chiplet/pta_chiplet_module.c`](https://github.com/kubeworkz/grxcp/blob/9667adec5e8f07a5415a2832a1622ee9c93d87ab/src/backends/pta_chiplet/pta_chiplet_module.c), blob `607d6cf4c5c0471e70d9554a0d7bd9631a8c08e0` | C model, not synthesizable PTA RTL or a board image. |
| PTA digital twin | [`src/backends/pta_chiplet/pta_chiplet_twin.c`](https://github.com/kubeworkz/grxcp/blob/9667adec5e8f07a5415a2832a1622ee9c93d87ab/src/backends/pta_chiplet/pta_chiplet_twin.c), blob `3cdcb3201c84890044338f59f27232f485c07b21` | Software model. The pinned README states there is no chiplet/hardware path. |

**Transport and FPGA target findings:** the pinned PTA board-transport document records a first-board link decision of CXL 2.0 Type-1 over a PCIe 5.0 PHY from the GRX930 host, but explicitly says no module, root port, or driver code exists; this is a design/model, not a working hardware path. It says the stand-in builder is open and no 128×64 RTL exists. No board or FPGA part is selected for the standalone PTA stand-in. The `xc7a200tfbg484-1` occurrence in the PTA program plan is for the C930/NPU synthesis baseline; U55C references elsewhere in this workspace are G100 targets, not a PTA stand-in selection. Keep the target as **not selected** until an accountable implementation/board decision names the board, part, tools, constraints, resources, and schedule.

## Current open ownership inputs

- Confirm that the pinned GRXCP `main` snapshot above is the intended component baseline for the integration; use a newer reviewed immutable commit if implementation work is based on another revision. Dave Cook is the PTA technical owner; the pinned source identifies the PTA backend/twin/module model, not a standalone PTA RTL tree.
- Select the canonical board/PDB repository and accountable integration/board owner; separately assign the FPGA stand-in implementation lead and target.
- Confirm interface-change approvers and validate implementation feasibility/details for the recorded CXL 2.0 Type-1 / PCIe 5.0 transport decision; it is a design/model, not a hardware path today.
- Populate and review [the integration manifest template](grxgpu_integration_manifest.template.json) before declaring a reproducible cross-project baseline.
