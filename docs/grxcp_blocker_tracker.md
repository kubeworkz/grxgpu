# GRXCP PTA/GPU blocker tracker

**Snapshot:** 2026-10-18 (P0 ownership and target date updated from user input)<br>
**Basis:** [GRXCP team status update](grxcp_team_status_update.md) dated 2026-10-17, the [GPU-owner evidence packet](evidence/pta_gpu_owner_evidence_template.md), and the current PTA integration/design documents.

The PTA chiplet queue twin regression passed 120 checks, including exact capacity and 32-bit counter wrap. This is model evidence only. In this worktree, the Ramulator dependency and SimX backend subsequently built successfully with one job; that clears a local compile blocker, not RTL/model parity or any hardware/IP evidence gate.

## Priority and status rules

- **P0 — unblock the work:** name accountable individuals, give target dates, and resolve architecture inputs that determine implementation scope.
- **P1 — correctness/interface gates:** implementation and boundary evidence required before claiming a working GPU↔PTA path.
- **P2 — link characterization and downstream software evidence:** measurements or integration checks that depend on selected hardware/configuration and lower-level contracts.
- **BLOCKED:** required implementation, access, or evidence is missing. **OPEN:** a decision or design is unresolved. **IN PROGRESS:** evidence-producing work has started but closure criteria are unmet. A role is not a named owner; do not infer assignment or dates.

## Prioritized action register

| ID | Priority | Status | Workstream | Accountable owner roles | Named DRI / target |
|---|---|---|---|---|---|
| T0 | P0 | IN PROGRESS | Record owner acceptance, access, and evidence locations | Dave Cook (program lead, chiplet/EIC lead, board lead, GRX930 lead, and GPU lead); accepted DRI for all six P0-A interface responsibilities | Dave Cook / Dec 12, 2026 |
| T1 | P0 | OPEN | Freeze interface inputs and record decisions | Dave Cook (program lead, chiplet/EIC lead, board lead); system architect; GPU + GRX930 owners | Dave Cook / Dec 3, 2026 |
| T2 | P1 | BLOCKED | Lossless GPU command-processor (CP) ring | GPU runtime + RTL + verification owners | TBD |
| T3 | P1 | BLOCKED | PTA queue capacity, full behavior, BUSY/completion (Q2, Q3, Q4) | GPU dispatcher + EIC queue/status owners | TBD |
| T4 | P1 | OPEN | GPU BAR-to-EIC register transaction route | GPU BAR/bridge + EIC interface owners | TBD |
| T5 | P1 | BLOCKED | MSI-X capability, OS allocation, and ISR routing (Q1) | GPU driver/platform + IP owner | TBD |
| T6 | P2 | BLOCKED | UCIe CRC/retry proof and link data-window measurements (Q5) | GPU UCIe + EIC/link + board/test owners | TBD |
| T7 | P2 | OPEN | GRXCP PTA reporting/backend gates (S1–S2) | GRXCP runtime/backend + model/verification owners | TBD |

P0 items start first. T2 may proceed in parallel to diagnose the failing test and implement the agreed CP-ring contract. T3–T5 can proceed in parallel once the relevant owners/configurations are available. T6 requires selected endpoints and operating configuration. T7 depends on the CSR map and a runnable SimX parity path.

## P0 kickoff: intake and decision log

The board/PTA plans already record several **plan-level architectural choices**. Do not reopen these as undecided unless an accountable owner raises a formal change: B1/B3 separate CPU and GPU packages with CXL 2.0 over PCIe 5.0 x16 (GRX930 host, G100 Type-2 device); B2 selects DDR5 for CPU and GDDR6 for GPU on organic substrates; B4 attaches the PTA chiplet to the G100 over UCIe and places converters, resident weights, activation buffers, accumulation, calibration, and S_ACT on the EIC; B5 selects TFLT (TFLN fallback) and an off-package PM-fiber laser; B7 places PTA registers behind the GPU's CXL.io BAR; B8 selects NRZ. These are documented plan decisions, **not** proof that selected silicon/IP implements them. See [board program plan §2 and B8](../grxcp/docs/designs/board_program_plan.md#2-decisions-to-settle-first) and the [board ICD](../grxcp/docs/designs/board_icd.md).

The following intake entries are the P0 work to start now. Enter a named decision owner, responding technical owner, target date, evidence ID/path, and disposition in each row. `TBD` is intentionally not a decision or a pass.

| Intake | Status | Decision/input needed | What the documents currently say | Decision owner / evidence required | DRI / target / disposition |
|---|---|---|---|---|---|
| P0-A | IN PROGRESS | Record named workstream leads, accepted interface DRIs, confirmed access, and evidence locations | User identified **Dave Cook** as the program lead, chiplet/EIC lead, board lead, GRX930 lead, and GPU lead; the project-level organization is Gridworkz. Dave Cook accepts all six interface DRI responsibilities and confirms the access dependencies in the working roster below. Evidence locations and access details (provider, access level, and request/status) still need recording. | Dave Cook records evidence locations and the details of confirmed access for each interface; attach a dated owner matrix/acceptance. | Dave Cook / Dec 12, 2026; all six DRIs and access dependencies confirmed; evidence locations/access details to record. See working roster below. |
| P0-B | IN PROGRESS | Confirm board/demo scope and resource envelope | User decisions: GRX930's PTA is a development vehicle only, not a v1 product feature; plan one initial engineering prototype. Kit budget remains TBD pending supplier quotes. | Dave Cook records scope and prototype quantity; finance/program sponsor gathers and reviews supplier quotes before approving any budget. Evidence: this decision record, quote set and a dated approval; distinguish planning assumptions from commitments. | Dave Cook / Dec 3, 2026; 1 engineering prototype; budget TBD pending quotes |
| P0-C | OPEN | Validate provisional PTA geometry, batch, and optical shot-rate sizing point | The first-board canary specifies **test assumptions**, not a physical PTA: one logical 128×64 tile, batch 16 end-to-end, 64→16 FC3, 6-bit activations/weights, 8-bit output representation, one vector per shot. User selected a provisional sizing point of logical 128×64, batch 16, and 25 MS/s. This point still needs a definition of whether a “shot” counts one physical mesh firing or a logical vector (including tiling), plus precision mapping and weight residency/reload assumptions. Traffic is case-dependent; the payload-only model gives 1.20/0.40 GB/s in/out for one 64→16 vector shot, or 1.20/3.20 GB/s for one full 128-output vector shot at 25 MS/s, excluding weight loads and headers. If the full 6-KiB logical weight image is reloaded every 16-shot batch, add 9.60 GB/s inbound (modeled). The 57.6 GB/s/direction link is an assumption, not selected IP. Receiver/source feasibility, primitive and physical mesh dimensions remain unknown. See the [PIC/EIC owner-review agenda](grxcp_p0c_pic_eic_review_agenda.md), [reconciliation memo](grxcp_p0c_reconciliation_memo.md), [candidate operating-point table](grxcp_p0c_operating_points.csv), [proposed register v1.1 change record](grxcp_p0c_owner_register_v1.1_proposal.md), and [decision-record skeleton](grxcp_p0c_decision_record_skeleton.md). | Dave Cook (PIC/EIC and GPU workload/link authority). Evidence: define shot/batch and logical-to-physical mapping; approve/reject/correct the bounded candidate cases; state canary validity and any separate customer workload; source topology-specific geometry, precision mapping, receiver noise versus rate, detector count, optical loss/source budget, weight-update behavior and selected endpoint/link constraints. Keep model outputs labeled assumed/predicted until measured or sourced. | Dave Cook / Dec 12, 2026; supplied v1.1/register edits remain proposals pending controlled v1.0 and Dave's approval; provisional sizing point is not approved; validation and any requirement approval remain OPEN |
| P0-D | IN PROGRESS | Specify and verify the interface and software/hardware error model for the approved 2-D topology direction | Dave Cook approved a **2-D mesh topology** for scalability despite added complexity. His attached `2DMesh.txt` proposes local network interfaces, five-port routers, flit packetization, VC credit flow control, a D2D PHY, transient ECC/CRC with retry, and permanent-fault adaptive routing/spare-lane repair. These mechanisms remain proposals, not a frozen interface or implementation evidence; the existing ring-bank model does not validate an MZI mesh. Use the [architecture reconciliation record](grxcp_mesh_architecture_decisions.md) to align the proposal with the board UCIe/CXL plan while preserving the optical primitive and internal EIC-NoC choices as open; use the [mesh architecture review checklist](grxcp_mesh_architecture_review_checklist.md) for itemized evidence questions. | Dave Cook (chiplet/EIC lead) with named PIC/EIC, NoC, link/PHY, software, and verification owners. Evidence: owner-approved layered interface and fault/error contracts; selected UCIe IP/config mapping; protocol rules if an EIC-local NoC is selected; software-visible error/status behavior; topology-specific model/reference tests; and applicable RTL/model fault-injection, recovery, liveness, and end-to-end boundary tests. | Dave Cook / Dec 3, 2026; 2-D topology direction approved, interface/error-model closure in progress |
| P0-E | OPEN | Set EIC-local command queue capacity and active-slot accounting | Register map §7 leaves queue depth open; twin ring checks do not establish EIC IP capacity. | EIC queue owner + GPU dispatcher owner. Evidence: selected IP/configuration value in commands, whether executing work consumes a slot, and named accept/start/retire events. Implementation tests remain tracked under T3. | TBD |
| P0-F | OPEN | Confirm MSI-X offer and whether PTA causes share GPU vectors | Register map §7 leaves vector count and ownership open; two vectors (CP + aggregated PTA) are only the provisional target. | GPU PCIe/MSI-X IP owner + driver owner + EIC interrupt owner. Evidence: selected-function/IP capability export and an owner-approved vector/cause map; OS allocation and ISR proof remain under T5. | TBD |
| P0-G | OPEN | Decide the actual GPU BAR-to-EIC transaction route | B7 settles the high-level register window as MMIO in GPU CXL.io BAR; it does not specify the BAR bridge, named transport transaction, EIC decode, ordering, completion, or error path. | GPU BAR/bridge owner + EIC interface owner. Evidence: owner-approved address/transaction diagram and decision record; end-to-end traces remain under T4. | TBD |
| P0-H | OPEN | Baseline selected endpoint/IP/config revisions and source every interface number | Board ICD §7 leaves endpoint/part choices, UCIe lane/DFx details, and some board/link values unsourced; modeled 57.6 GB/s and 100 ns are not measured limits. | GPU, GRX930, chiplet, and board interface owners. Evidence: revision/config identity and source for each selected link rate/width/latency/credit/buffer value; every unsourced value remains explicitly an assumption/open item. | TBD |

### P0-A working interface DRI roster (accepted; access confirmed)

Dave Cook accepts all six interface DRI responsibilities listed below and confirms access to the listed artifacts, tools, and environments. Target date for each responsibility and the overall P0-A owner/access record: Dec 12, 2026. Evidence locations and the access provider/access level details are not yet recorded. Keep restricted supplier/IP material in its authorized location and link to controlled evidence rather than copying it here.

| Interface responsibility | Accepted DRI | Acceptance | Target date | Access confirmed / evidence location |
|---|---|---|---|---|
| PIC / optical compute | Dave Cook | Accepted | Dec 12, 2026 | CONFIRMED by Dave Cook: selected PIC topology/interface and photonic design data; optical model/reference vectors and sourced parameter or measurement data; authorized supplier/PDK materials where needed. Evidence locations TBD. |
| EIC / internal NoC | Dave Cook | Accepted | Dec 12, 2026 | CONFIRMED by Dave Cook: EIC RTL and selected IP/configuration; register, queue, interrupt, reset/clock, and boundary specifications; NoC specification and simulation/test environment if an internal NoC is selected. Evidence locations TBD. |
| GPU interface (BAR/control and GPU integration) | Dave Cook | Accepted | Dec 12, 2026 | CONFIRMED by Dave Cook: G100 RTL/runtime/driver source and build/test environment; selected BAR/bridge, MSI-X, and UCIe endpoint configuration/IP evidence; GPU integration test and trace artifacts. Evidence locations TBD. |
| UCIe / link / PHY | Dave Cook | Accepted | Dec 12, 2026 | CONFIRMED by Dave Cook: both endpoint adapter/PHY configuration and revision records; authorized UCIe IP documentation/tools; package/channel and board test setup; training, CRC/retry, telemetry, and fault-injection results. Evidence locations TBD. |
| Software / runtime | Dave Cook | Accepted | Dec 12, 2026 | CONFIRMED by Dave Cook: runtime/driver and firmware sources, approved CSR/register map and command contract; compiler/toolchain and SimX/model test setup; reproducible workload/reference vectors. Evidence locations TBD. |
| Verification / reliability | Dave Cook | Accepted | Dec 12, 2026 | CONFIRMED by Dave Cook: pinned RTL/model revisions and configs; testbench, simulator and any required licensed IP models; fault-injection/recovery environment; FPGA/board access where hardware-level evidence is required. Evidence locations TBD. |

**P0 sign-off rule:** T0 closes only after Dave Cook records accepted individual DRIs, target dates, dependencies, and evidence locations for all active workstreams and interfaces. P0-B has two recorded scope inputs: the GRX930 PTA is a development vehicle only, not a v1 product feature; the initial board quantity is one engineering prototype. The kit budget remains open pending supplier quotes and finance/program sponsor review. P0-D's topology direction is approved as a 2-D mesh by Dave Cook, with scalability as the stated goal despite higher implementation complexity. The attached `2DMesh.txt` contributes a high-level interface/fault proposal; the [architecture reconciliation record](grxcp_mesh_architecture_decisions.md) aligns it with the board-level G100/UCIe plan without deciding the optical primitive or assuming an internal EIC NoC, and the [mesh architecture review checklist](grxcp_mesh_architecture_review_checklist.md) tracks closure evidence. Detailed protocol, software-visible error model, selected UCIe-S IP/config mapping, and implementation/fault-injection evidence remain open. T1 closes only after the plan-level decisions are owner-confirmed or formally changed, every P0 intake item has a recorded decision or an explicitly approved hold with owner, rationale, due date, and gate impact, and the board ICD is owner-reviewed against its P0 criterion (each link has named owners at both ends and every numeric value has a source or is visibly OPEN/assumed). An approved hold is transparent tracking, not a technical pass; downstream T2–T6 gates remain open until their own evidence is verified.

## Actions and closure evidence


### T0 — Assign accountable people and evidence access (**P0 / IN PROGRESS**)

**Next action:** Dave Cook is the named program lead, chiplet/EIC lead, board lead, GRX930 lead, and GPU lead, accepts all six interface DRI responsibilities, and confirms their listed access dependencies. The P0-A/T0 target is Dec 12, 2026. Record evidence locations and the provider/access-level details for each interface and for T1–T7/P0-A–P0-H. Gridworkz remains the project organization. Keep GPU, EIC/chiplet, board, GRX930, and GRXCP responsibilities distinct.

**Close when:** Every active row has an accepted named DRI, target date, required platform/IP access, and an evidence location. Dave Cook's program, GPU, GRX930, chiplet/EIC, and board lead assignments plus acceptance of all six P0-A interface DRI roles and confirmation of their listed access dependencies are recorded; P0-A/T0 target is Dec 12, 2026. Record evidence locations and provider/access-level details; do not infer these from the access confirmation.

### T1 — Freeze interface inputs and unresolved decisions (**P0 / OPEN**)

**Recorded scope inputs:** The user selected the GRX930 PTA as a development vehicle only, excluded from v1 product-feature claims, and selected one engineering prototype as the initial development-kit quantity. The budget remains open pending supplier quotes and finance/program sponsor review under P0-B.

**Next action:** Use P0-A–P0-H above as the meeting agenda and decision log. Confirm the existing B1–B8 plan choices rather than reopening them by default; get owner decisions for actual scope, chiplet geometry/rate, EIC queue, MSI-X offer, BAR forwarding, and selected IP/config identities. P0-D's 2-D mesh choice is approved; use the attached note as input to an owner-approved interface/error contract. If an EIC-local packet NoC is selected, resolve its packet/flit and coordinate formats, routing/VC/credit handshakes, transient-error detection/retry, permanent-fault response, software-visible error/status behavior, and fault/liveness evidence. Separately resolve the UCIe-S boundary mapping and topology-specific model evidence; do not assume the optical compute fabric itself is packet-routed. Mark any other item not decidable yet as an approved hold with an accountable decision owner, rationale, date, and gate impact—never as implicitly closed.

**Evidence:** Owner-reviewed interface-control decision record with individual names, revision/configuration IDs, decision dates, source artifacts, and unresolved items. Cite the controlling specification/IP export for each selected value; label model estimates, assumptions, and placeholders as such.

**Close when:** B1–B8 are confirmed or formally superseded; every P0 intake item is decided or covered by an explicitly approved, bounded hold; the board ICD has named owners for each link endpoint and sourced-or-open disposition for every number. This closes the P0 decision/ownership package only—not implementation, MSI-X delivery, queue correctness, link measurements, or BAR end-to-end evidence. See the [PTA register map](../grxcp/docs/designs/pta_chiplet_regmap.md) §7 and [board plan](../grxcp/docs/designs/board_program_plan.md) §8.

### T2 — Prove a lossless GPU CP ring (**P1 / BLOCKED**)

**Current evidence:** RTL exposes monotonic consumer-head telemetry and `Q_HEAD_SNAP_LO/HI`. The recorded `cp_core` run failed on its first AXI-Lite capability read (`R` never asserted), before ring execution; current runtime appends at producer tail without checking free space against consumer head, and mid-command-line physical wrap is unsupported.

**Next action:** First root-cause the AXI-Lite test failure so ring behavior is actually exercised. Implement a documented capacity contract using coherent monotonic head/tail accounting and producer backpressure, or an explicitly approved all-or-nothing rejection policy. Do not claim the ring passed based on a test that exits before enqueue/retirement.

**Evidence:** Exact RTL/runtime revisions and passing focused tests for snapshot coherence under AXI read backpressure; exact-full stall/resume; 64-byte-line and physical wrap; oversized batch (>64 KiB) atomic rejection before tail commit or stable backpressure; delayed acceptance/retirement; concurrent producers; exactly-once ordered retirement and forward progress. Preserve command IDs, head/tail snapshots, retire sequence, errors, logs/waveforms, tool versions, and SHA-256.

**Close when:** All agreed cases pass on the same candidate RTL/runtime revisions; no overwrite, drop, duplicate, partial batch publication, false completion, or deadlock occurs; the contract and tests agree. Keep this GPU CP ring separate from the GPU dispatch queue and EIC/PTA-local queue.

### T3 — Close PTA queue capacity, overflow, BUSY, and completion contract (**P1 / BLOCKED, Q2, Q3, Q4**)

**Next action:** GPU dispatcher and EIC owners specify each queue independently (GPU CP ring, GPU dispatch queue, EIC-local queue, active execution): capacity in commands, whether active work consumes a slot, and enqueue/accept/start/complete/retire events. Choose and specify full behavior—backpressure with release condition or explicit rejection/error with safe retry. Specify `PTA_STATUS.BUSY` assertion/clear events across queued, active, completed-not-retired, calibration, reset refusal, and error states.

**Evidence:** Owner-approved contract and IP/config revision; implementation-level trace/waveform at idle, exact full, over-capacity, resume, calibration and reset-refusal transitions. Include accepted/queued/active/retired counts, command IDs, BUSY/CAL_BUSY and status reads, clock/reset domains, and coherent snapshot/CDC evidence. The existing 120-check twin run is supporting model evidence only.

**Close when:** Independent observations agree with declared capacities at the boundary; no command is silently lost, overwritten, duplicated, ambiguously retried, or falsely completed; eventual progress is shown. The implementation proves the completion test is GPU-side relevant queue empty **and one** coherent `PTA_STATUS` read showing BUSY and CAL_BUSY clear, with documented ordering.

### T4 — Specify and verify GPU BAR-to-EIC register forwarding (**P1 / OPEN**)

**Next action:** GPU BAR/bridge and EIC owners produce an approved address/transaction route from GPU CXL.io BAR request through BAR decode/bridge, the explicitly named transport/protocol transaction, EIC endpoint/address decode, and PTA register. Separately document the GPU-memory/copy-engine tensor-data route over UCIe mainband; do not infer either route from the other or assume sideband carries BAR traffic.

**Evidence:** Both diagrams identify address mapping, widths, endpoints, ordering/flush, completion, and error propagation. Attach transaction-ID traces for `PTA_ID` and safe-register read/write/readback, proving posted-write visibility before the ordering read completes and showing error behavior.

**Close when:** GPU and EIC interface owners approve the routes and the selected implementation passes read, write/readback, ordering, and error-propagation tests on the intended integration (simulation or board, clearly identified). A design diagram alone closes the route decision, not implementation validation.

### T5 — Prove MSI-X capability, allocation, and interrupt delivery (**P1 / BLOCKED, Q1**)

**Next action:** GPU driver/platform owner captures the selected function's PCI identity and MSI-X Table Size/configuration, then records requested versus granted OS vectors and IRQ-to-vector mapping. Verify XRT and OPAE separately; the status report says OPAE CP-completion routing is unconnected. The two-vector mapping (vector 0 CP, vector 1 aggregated PTA) remains provisional until supported by the selected function and owner approval.

**Evidence:** Raw PCI capability/configuration and vendor/IP export; driver build/source ID and allocation API/result, count, flags, return code, OS/kernel, BDF and vector mapping; controlled CP-completion and each PTA-cause test (`CAL_DONE`, `ERR`, `DRIFT_ALARM`, `SAT_THRESHOLD`) with handler identity, before/after status, masks, RW1C clearing, counter deltas, and no lost/duplicate/misattributed cause. Include raw artifact paths and SHA-256.

**Close when:** At least two vectors are demonstrated and allocated with approved routing, and controlled tests prove host handler delivery for every claimed interrupt path. If fewer than two are available, remain BLOCKED until a documented fallback is approved and tested. An internal pulse or PCI collector output alone does not prove OS allocation or ISR delivery.

### T6 — Verify UCIe CRC/retry and measure throughput, RTT, credits, buffers (**P2 / BLOCKED, Q5**)

**Next action:** GPU UCIe and EIC/link owners attach selected endpoint/adapter configuration and training evidence for protocol/FLIT mode, CRC, retry, negotiated lanes/rate, revisions, and status. Run CRC fault injection/recovery. Measure useful payload throughput in each direction and request/response RTT under unloaded and saturated/concurrent traffic, with geometry and workload recorded.

**Evidence:** Fault injection or vendor verification shows CRC detection, retry/recovery, counters/status and final payload integrity. Measurement packet records transaction sizes/distribution, concurrency, duration, temperature/voltage, timestamp endpoints, retries/errors, credits and buffer capacity at each boundary. Include raw logs and calculation script; calculate byte-window demand as measured payload bytes/s × selected design RTT, then validate against actual buffer/credit capacity using the observed payload distribution.

**Close when:** Selected implementation has verified CRC/retry behavior and repeated reproducible link measurements; the owner-approved latency/throughput target and buffer/credit budget are met or an explicit architecture decision changes them. Until measured, **57.6 GB/s and 100 ns remain assumptions**, not pass criteria.

### T7 — Complete GRXCP PTA reporting and model gates (**P2 / OPEN, S1–S2**)

**Next action:** Once the CSR map is stable and SimX is available, populate the specified device property from PTA CSRs, extend the vendored DPI shim, and make `grx-smi` report inactive/no-tile state honestly. The single-job SimX build succeeded in this worktree; no new PTA parity result is implied by that build.

**Evidence:** GRXCP NPU backend gate passes with every field sourced or reported unknown (`-1`); inactive/no-tile cases do not report stale CSR values; unsupported impairment bits are distinguishable from disabled implemented bits. Run bitwise comparison against deterministic PTA vectors and fixed-seed RTL-to-SimX parity; produce the distributional report against the agreed reference and preserve commands, revisions, configs, logs, and vector hashes.

**Close when:** S1 and S2 acceptance gates pass on identified revisions, golden data is only regenerated through reviewed procedure, and the report labels analog emulation accurately. Model/vector checks do not close physical-link or hardware/IP evidence gates.

## Update protocol

For each row, maintain: `status | named DRI | target date | dependency | next evidence-producing action | artifact ID/path + SHA-256 | reviewer | closure decision/date`. Update status only when evidence is attached; keep failed runs and superseded packets immutable. Do not copy confidential IP, credentials, or restricted supplier material into this repository—link to access-controlled evidence instead.

See the [full evidence packet template](evidence/pta_gpu_owner_evidence_template.md) and [Oct 17 status report](grxcp_team_status_update.md) for source detail and artifact requirements.
