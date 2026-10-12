# GRXGPU Engineering Task List

**Status:** Proposed backlog; tasks are unassigned until named owners accept them.
**Version:** 0.1 — 2026-10-10
**Parent:** [GRXGPU Production Readiness Plan](grxgpu_production_plan.md)
**Planning horizon:** First 4–6 week evidence sprint, followed by gated engineering work. No tapeout date is implied.

## How to use this list

- `[ ]` means not yet evidenced as complete; do not check a task off because it is planned, simulated on a different configuration, or reported verbally.
- **P0** blocks product definition or trustworthy baseline. **P1** is required for the GRX930 FPGA/product proof. **P2** is required before target-process implementation/tapeout approval. **P3** is first-silicon, pilot, and production release work. **TRACK** is parallel discovery for G100 or PTA and does not block GRX930 unless the product decision changes.
- Owner entries are **roles**, not assignments. Program leadership must put a named person and due date on each task before execution.
- Every evidence artifact should record source revision, configuration, tools, inputs/checksums, logs/results, reviewer, and date. Store controlled PDK/customer/supplier material only in approved private storage; link to an access-controlled record rather than checking it into this repository.
- `Blocked` is an acceptable status. Record the blocker and decision needed; do not invent a pass or silently weaken an acceptance threshold.

## A. First 4–6 week sprint — unblock scope and establish facts

### [ ] E-001 — Authorize the first SKU and product envelope — **P0 / G0**

**Working draft:** [GRX930 v1 Product Brief](grx930_v1_product_brief.md). Candidate direction is four RV64 cores plus one NPU, but E-001 remains open until the customer/workload, targets, commercial inputs and sponsor approval are documented.

- **Owner:** Product sponsor + customer/design-partner lead + finance
- **Depends on:** None
- **Work:** Confirm GRX930 edge inference as the first production candidate or record the alternative. Name the buyer/design partner; record embedded local/on-device inference as the selected deployment; designate MLPerf Tiny VWW as an interim engineering baseline (not customer acceptance; detailed under E-009); and obtain the supported customer workload/model, required quality, P99 latency, sustained power/thermal envelope, memory capacity/bandwidth, host/product interface, target unit cost/volume, launch window, and support expectations. Record the selected four-core plus one-NPU scope as a product target, not a validation claim; keep graphics/HBM/chiplets explicitly out unless approved.
- **Done when:** A signed, versioned product brief names every item above, distinguishes measured facts from targets, and has a named approver. Numeric release targets are ratified rather than copied from the demo proposal.

### [ ] E-002 — Establish the current source and hardware baseline — **P0 / G1**

- **Owner:** Program lead + GRX930 RTL/FPGA leads
- **Depends on:** E-001 can proceed in parallel, but scope may be provisional
- **Working evidence:** Initial workspace audit is recorded in [GRX930 E-002 Source and Hardware Evidence Manifest](grx930_evidence_manifest.md); it is a draft inventory, not E-002 closure.
- **Work:** Reconcile the manifest with the authoritative source repository, FPGA board/device, bitstream, firmware, tools, and available logs. Obtain missing RTL/project and PDK/IP evidence through their owners. Explicitly record artifacts absent from this worktree and who must provide them.
- **Done when:** A reviewed evidence manifest has one row per claim/artifact and labels it `documented`, `reproduced`, `physical-board measured`, `unverified`, or `blocked`; it includes checksums/revisions where applicable and no status is inferred from a plan or an instantiated-but-idle core.

### [ ] E-003 — Verify PDK rights and manufacturing inputs — **P0 / G1, G4**

- **Owner:** Sourcing/legal + physical-design lead
- **Depends on:** E-001
- **Working tracker:** [Redacted E-003 PDK Rights and Manufacturing Inputs Matrix](grxgpu_e003_manufacturing_matrix.md); use the [reviewer-ready E-003 closure checklist](grxgpu_e003_closure_checklist.md) for product/route evidence review and sign-off. Gridworkz is assigned as project DRI across E003-D01–D06 and accepted the target dates on 11 Oct 2026; Kubeworkz is the separate deferral approver and has approved none of the six deferrals as of that date. Evidence is due on the accepted targets: D01 Oct 23, D02 Oct 30, D03 Nov 13, D04–D06 Nov 20, 2026. The GF180 purchase deadline is Dec 9, 2026 and is not spending authorization. A proposed deferral does not change a due date until approved; `TBD` remains for unknown model values. Deferral is not waiver or gate closure. See the [PDB project manifest](grxgpu_pdb_project_manifest.md) for the supplied route split. The [PDB BOM](grxgpu_pdb_bom.csv), [cost model](grxgpu_pdb_cost_model.md), and [ERP account-mapping template](grxgpu_pdb_erp_account_mapping.csv) are planning workpapers, not quotes, approved budget, or posting instructions.
- **Work:** In controlled storage, verify foundry/node/PDK revision, permitted commercial use, libraries/corners/RC data, DRC/LVS/antenna/extraction decks, SRAM/compiler, IO/ESD, clock/reset, DFT, DDR controller/PHY, package/OSAT, test access, foundry route/slot, and tool licenses. Separate received, licensed, compatible, and still-quoted items. Reconcile any local flow or PDK artifacts that point to another process.
- **Done when:** An access-controlled IP/manufacturing matrix and the [E-003 closure checklist](grxgpu_e003_closure_checklist.md) identify the product/revision/route, owner, evidence source, delivery/rights status, compatibility, lead time, cost/quote status, reviewer disposition, and unresolved blocker for each critical item. If items must be deferred, record each as `TBA (deferred)` with named project DRI, deferral approver, contributors, target date, trigger, and affected gate. This permits an administrative deferral checkpoint only; it does not close E-003 or authorize any gated purchase, signoff, or tapeout. The public repository contains no confidential PDK files or restricted details.

### [ ] E-004 — Reproduce the checked-in simulation baseline — **P0 / G1**

- **Owner:** Verification lead + GRX930 RTL lead
- **Depends on:** E-002 and access to runnable RTL/test sources
- **Work:** Rebuild the documented Verilator SoC/test path from a clean, identified revision; rerun available UART and GEMM cases; archive exact commands, tool versions, test vectors and logs. Record failures and unsupported cases instead of editing historical results.
- **Done when:** Another engineer can reproduce the same reported pass/fail outcomes from the manifest, and the evidence report clearly limits claims to the tested single-core/model configuration and sizes.

### [ ] E-005 — Freeze the acceptance workload and numerical contract — **P0 / G0–G2**

- **Owner:** ML/software lead + customer/design partner + verification lead
- **Depends on:** E-001
- **Work:** Select the named acceptance model and representative data; define preprocessing, quantization, required operators, supported tensor shapes/layouts, reference semantics, quality metric, rounding/saturation, golden-vector generation, and test-set governance. Define target metrics and measurement boundaries for latency, throughput, energy, temperature and reliability.
- **Done when:** A reviewed workload specification and versioned golden-data manifest exist; reference outputs regenerate deterministically; all proposed thresholds have an owner, measurement method, and approval status.

### [ ] E-006 — Decide the v1 system boundary and interface contract — **P0 / G2**

- **Owner:** System/SoC architect + board lead + firmware/runtime lead
- **Depends on:** E-001, E-002, E-005
- **Work:** Specify selected core count, boot/control authority, host interface, DDR type/capacity/controller/PHY, address map, DMA reachability, coherency/ownership, command ABI, buffer lifecycle, interrupt/polling/timeouts, reset/recovery, debug, clock/power/thermal limits, and package/module boundary.
- **Done when:** Product and engineering sign an interface-control document and system diagram. Each interface has a defined producer/consumer, width/rate/latency requirement or a clearly marked open measurement, reset/error behavior, and verification owner.

### [ ] E-007 — Audit firmware and runtime against the product path — **P0 / G1–G3**

- **Owner:** Firmware/runtime lead
- **Depends on:** E-002, E-006
- **Work:** Compare actual firmware and host-driver sources with the shipped path: boot/recovery, bounded model loading, real hardware register/DMA/TCU setup, submit/completion/error ABI, watchdog/timeouts, interrupts if needed, diagnostics/perf counters, versioning, update, and behavior for invalid requests. Reconcile every TODO in the README against current source and tests.
- **Done when:** A feature-by-feature matrix cites implementation and test evidence or creates a scoped issue with dependency/owner. UART demo behavior is not counted as the product host path unless UART is explicitly selected for the SKU.

### [ ] E-009 — Freeze and run the GRX930 VWW engineering evaluation — **P0 / G1–G3**

- **Owner:** ML/software lead + GRX930 firmware/runtime + verification lead
- **Depends on:** E-002, E-004, and evaluation-corpus acquisition; NPU-offload measurements additionally depend on E-006 and actual operator support.
- **Work:** Follow the [GRX930 VWW evaluation protocol](grx930_vww_evaluation.md). Pin the exact upstream commit/rules/model; verify the published model MD5 and record local SHA-256; archive and hash the actual image/label corpus; document the unresolved VWW test-set overlap caveat; lock preprocessing, class order/tie behavior, runtime, system under test, and evaluation/performance configurations. Establish CPU/reference accuracy first; run NPU-offload only where the supported graph can execute without concealed emulation. Collect single-stream per-image correctness, inference-only and product-end-to-end latency, and explicitly scoped energy results.
- **Done when:** A versioned manifest contains actual SHA-256 values and all tool/board/firmware/RTL/model/data/config identities; no placeholder remains for the claimed run; frozen-corpus accuracy and repeated timing results are archived; an independent engineer reproduces them. If the corpus labels cannot be established or GRX930 hardware/NPU path is unavailable, mark the affected sub-stage blocked and do not claim a benchmark pass or official MLPerf result.

### [ ] E-008 — Build the product verification and acceptance matrix — **P0 / G2–G3**

- **Owner:** Verification lead + firmware/runtime lead
- **Depends on:** E-004, E-005, E-006
- **Work:** Map each product requirement to a reference test, RTL test, FPGA/board test, target-PDK check, or manufacturing test. Include golden checks, supported shape/precision matrix, maximum DMA length/address boundaries, stalls/backpressure, repeated/concurrent requests, reset, malformed commands, recovery, coherency, thermal/power and long-run reliability.
- **Done when:** Every ratified requirement has a test ID, method, pass threshold, environment, artifact location, and responsible reviewer; gaps are explicit and prioritized. No proposed demo gate is represented as an approved product gate without ratification.

## B. GRX930 engineering proof — only after scope and baseline are established

### [ ] E-101 — Create a reproducible build and test entry point — **P1 / G1–G3**

- **Owner:** Build/release engineer + RTL lead
- **Depends on:** E-002, E-004
- **Work:** Pin or record tool versions and inputs; provide clean build/test commands for firmware, simulation and the selected FPGA flow; archive generated artifacts and checksums; separate configuration variants to prevent stale build reuse.
- **Done when:** A clean environment can build the selected configuration and run its smoke/regression suite using documented commands; outputs identify the exact RTL, firmware, tool and configuration revisions.

### [ ] E-102 — Establish physical FPGA bring-up and operating point — **P1 / G1–G3**

- **Owner:** FPGA lead + board/system lead
- **Depends on:** E-002, E-003, E-006, E-101
- **Work:** Build/program the actual target board; verify boot, reset, JTAG/debug, clocks, memory and UART/host access. Run the product-critical load → DMA/DDR → NPU → result path on hardware. Capture constraints, synthesis/P&R timing, resource use, clock, board revision, bitstream checksum, measured power and temperature.
- **Done when:** An independent reviewer can reproduce a board acceptance run from the manifest; the required workload passes its golden/quality checks at the ratified operating point; timing margin and power/thermal conditions are reported from physical hardware.

### [ ] E-103 — Extend NPU verification to multi-tile and product-like workloads — **P1 / G3**

- **Owner:** NPU RTL lead + verification lead
- **Depends on:** E-005, E-008, E-101
- **Work:** Extend beyond the reported M≤8, N≤12, K≤16 simulation sweep to the named model and multi-tile GEMM (include K=64/128/256 or larger where required). Exercise tails/non-square dimensions, supported INT8 behavior, accumulation/requantization, prefetch, C accumulation, address limits, and repeated launches.
- **Done when:** All selected golden vectors and product workload checks pass in the reference and RTL flows for the full supported shape matrix; raw logs and exact numerical contract are archived; unsupported shapes are rejected clearly rather than returning silent bad results.

### [ ] E-104 — Prove DMA/cache coherency and selected core-count behavior — **P1 / G3**

- **Owner:** SoC/RTL lead + verification lead
- **Depends on:** E-006, E-008, E-103
- **Work:** Stress CPU, DMA and NPU concurrently with overlapping and disjoint buffers, multi-cache-line bursts, ordering/fences, repeated writes/readback, and contention. Test every core participating in v1. If multi-core is not in product scope, test the selected single-core configuration and document why other instantiated cores are excluded.
- **Done when:** No stale/corrupted output, deadlock, lost completion or ownership violation occurs in the defined randomized and directed suite; assertions/scoreboards cover the chosen coherency contract; multi-core claims are made only if multi-core tests pass.

### [ ] E-105 — Verify error handling, bounds, reset and recovery — **P1 / G3**

- **Owner:** Firmware/runtime + SoC RTL + verification
- **Depends on:** E-006, E-007, E-008
- **Work:** Inject malformed descriptors, illegal opcodes/formats, out-of-range/unaligned DMA, maximum and zero lengths, timeouts, backpressure, reset during idle/busy/fault, and failed model loading. Check command queue recovery and that a subsequent valid job succeeds.
- **Done when:** Each case returns the specified status within its timeout, causes no out-of-bounds memory access or silent corruption, and leaves the device in a documented recoverable state; tests run in the appropriate simulation and hardware environments.

### [ ] E-106 — Close product firmware/runtime gaps — **P1 / G3**

- **Owner:** Firmware/runtime lead + SoC/RTL lead
- **Depends on:** E-006, E-007, E-008
- **Work:** Implement only the gaps confirmed in E-007: bounded ELF/model loader or agreed artifact loader, hardware TCU/DMA initialization, selected interrupt/polling path, command ABI, status/error handling, cache policy and recovery/update flow. Add host-side driver/runtime and diagnostics for the selected production interface.
- **Done when:** An automated host test loads the frozen workload, submits it through the specified ABI, reads correct output/status, exercises an injected failure and recovers without manual register pokes or power cycling (unless the product contract explicitly requires it).

### [ ] E-107 — Add protocol assertions and close verification coverage — **P1 / G3**

- **Owner:** Verification lead + RTL owners
- **Depends on:** E-008, E-103, E-104, E-105
- **Work:** Add/check assertions for AXI/ready-valid, FIFO bounds, DMA response ordering, cache invalidation, reset, command queue, and applicable barriers. Review functional coverage against the acceptance matrix; classify exclusions and unresolved failures.
- **Done when:** Assertions run in CI or the documented verification flow; all critical requirement bins are covered or have signed waivers; no open critical correctness defect remains; regression evidence is tied to the release candidate revision.

### [ ] E-108 — Measure full-system FPGA PPA and thermal behavior — **P1 / G3–G4**

- **Owner:** FPGA/board lead + power/thermal engineer
- **Depends on:** E-102, E-005, E-006
- **Work:** Measure target-clock timing margin, resource utilization, memory bandwidth, board/module power, and temperature on the named workload under declared ambient/cooling conditions. Include host, memory and required peripherals in the declared measurement boundary.
- **Done when:** Raw reports and calibrated instrument/method details are archived; results meet the ratified FPGA/product envelope or a reviewed scope/architecture change is proposed.

## C. Product architecture and ASIC readiness — gated on G0–G3

### [ ] E-201 — Complete target-process IP and package closure — **P2 / G4**

- **Owner:** Physical design + sourcing/legal + package/test leads
- **Depends on:** E-003, E-006
- **Work:** Close every critical foundry/IP matrix item for the frozen SKU, including real SRAM macros/models, IO/ESD, clock/reset, DDR/controller/PHY, DFT, extraction, signoff decks, package/OSAT, probe/test and commercial rights.
- **Done when:** Written supplier/foundry evidence confirms availability, rights, compatibility, delivery timeline, support, and quoted cost; no critical IP is represented by a generic black box or assumed “included” without confirmation.

### [ ] E-202 — Run target-PDK synthesis and full-product feasibility — **P2 / G4**

- **Owner:** Physical-design lead + RTL lead
- **Depends on:** E-003, E-006, E-201, E-107
- **Work:** Synthesize the selected GRX930 top using actual target libraries and realistic SRAM/IO/PHY abstracts; estimate area, timing/corners, congestion, workload power, clocking, pads, DFT, package, and thermal. Identify false paths/exceptions and black-box assumptions.
- **Done when:** Versioned reports cover the product top rather than an isolated block, reconcile all excluded/abstracted area and power, meet agreed margin targets or present a reviewed reduction/rework proposal, and are accepted by an independent physical-design reviewer.

### [ ] E-203 — Define DFT, observability and production test — **P2 / G4–G5**

- **Owner:** DFT/test lead + RTL lead
- **Depends on:** E-006, E-201
- **Work:** Specify scan/JTAG, SRAM MBIST/repair strategy, clock/reset test, test modes, boundary/IO test as applicable, coverage targets, production vectors, debug visibility, and test time/yield data requirements.
- **Done when:** DFT architecture and test plan are reviewed against the package/pad map and production test access; representative insertion/coverage evidence exists in the target flow; no test-critical observability gap remains.

### [ ] E-204 — Freeze product RTL and establish change control — **P2 / G5**

- **Owner:** Engineering/program lead + RTL + verification + product owners
- **Depends on:** E-001–E-008, E-101–E-108, and E-201–E-203; target-process synthesis and DFT evidence are mandatory before tapeout freeze.
- **Work:** Create a signed RTL baseline, known-issues list, requirement traceability, reproducible release build, source/artifact checksums, waiver list, and post-freeze change-impact policy.
- **Done when:** All required gate evidence is attached to the baseline; there are no open critical defects; independent owners approve freeze; any later change requires explicit impact analysis and affected regression reruns.

### [ ] E-205 — Complete physical implementation and signoff — **P2 / G5**

- **Owner:** Physical-design lead + signoff owners
- **Depends on:** E-201, E-202, E-203, E-204
- **Work:** Complete floorplan, place/route, extraction, MCMM timing, signal integrity, IR/EM, thermal, DRC/LVS/antenna, scan/MBIST checks, gate-level regression and final GDS generation using the approved foundry flow.
- **Done when:** Required corners and foundry decks pass, or any exception has a written foundry-approved waiver; final reports, netlists, GDS and checksums are archived and independently signed off.

### [ ] E-206 — Prepare tapeout and first-silicon decision package — **P2 / G6**

- **Owner:** Program lead + executive/product sponsor + finance + engineering leads
- **Depends on:** E-001, E-201–E-205
- **Work:** Review residual technical risks, supplier slot, full NRE/funding, package/test, bring-up board, samples, customer plan and at least one corrective-revision reserve. Prepare go/hold/stop recommendation.
- **Done when:** Named approvers sign the G6 decision with all required evidence and residual risks. This task records authorization; it does not trigger a foundry order or tapeout without explicit authorization.

## D. G100 and PTA parallel tracks — discovery only until separately funded

### [ ] E-301 — Bound the first G100 SKU and workload — **TRACK / G0–G2**

- **Owner:** G100 product/architecture lead
- **Depends on:** Portfolio resource decision; no dependency on GRX930 tapeout
- **Work:** Decide compute-only versus graphics, choose one implementable configuration and supported workload, host/memory boundary, software/API scope, power/area targets and a realistic FPGA/ASIC milestone. Audit aspirational architecture and historical tapeout assumptions against code, tools, IP and current supplier evidence.
- **Done when:** A G100-specific product brief and evidence ledger clearly distinguish implemented RTL, simulator-only behavior, FPGA results, paper targets, and unresolved dependencies; product sponsor decides fund/defer.

### [ ] E-302 — Establish G100 functional, parity and FPGA evidence — **TRACK / G1–G3**

- **Owner:** G100 RTL/verification/FPGA leads
- **Depends on:** E-301
- **Work:** Select the canonical workload suite; run relevant regression and SimX/RTL model-parity checks; separately validate FPGA resource/timing closure and full accelerator interface. Use `xrt` for AFU/full RTL integration where that is the target, not only `rtlsim`.
- **Done when:** Exact configurations and logs are reproducible, correctness/parity criteria pass, FPGA timing/resource limits meet the G100-specific brief, and discrepancies are triaged rather than hidden by wider tolerances.

### [ ] E-303 — Specify and measure a physical PTA prototype — **TRACK / G0–G3**

- **Owner:** Photonics lead + system/measurement lead
- **Depends on:** Portfolio resource decision and a declared candidate workload
- **Work:** Define compute/numeric representation and optical/electrical boundary; build a fixed reference and repeatable prototype test. Measure data/weight movement, programming, source/laser, modulation, optical compute, detection/readout, conversion, calibration, thermal behavior and post-processing. Compare with matched digital system boundaries.
- **Done when:** Archived repeated measurements demonstrate output quality, stability, latency and joules/job for the full intended system boundary; optical support equipment, package/coupling, calibration drift, test and supply blockers are quantified. Otherwise record hold/research-only.

## E. Integration, first silicon and pilot — after independent track gates

### [ ] E-401 — Validate the shared development-board integration demo — **P1 after standalone modules pass**

- **Owner:** Board/system + software integration leads
- **Depends on:** E-005, E-006, E-102, E-106, plus independent G100/PTA readiness if those engines are claimed in the demo
- **Work:** Run the versioned workload and C0–C3 matrix from the [first-board demo spec](grxgpu_first_board_demo.md). First confirm actual engine shapes/formats and ratify prototype thresholds. Measure complete caller-visible latency, bytes/copies, per-stage timing, energy, temperature, and errors; retain raw traces.
- **Done when:** Each claimed configuration passes its frozen correctness gates and required repeated trials; all participants show real activity; latency/energy boundaries include transfers, conversions and PTA support equipment; results are reported without treating demo completion as production qualification.

### [ ] E-402 — Bring up and characterize first silicon — **P3 / G7**

- **Owner:** Silicon bring-up + RTL + firmware + test + package
- **Depends on:** E-206 and silicon/package delivery
- **Work:** Execute pre-written JTAG/recovery, clock/reset, memory/IO, DMA, compute-golden, diagnostic, stress, voltage/frequency/temperature and power/thermal characterization; triage errata by root cause.
- **Done when:** The ratified characterization matrix passes or has documented failure disposition; all measurements and errata are tied to device/lot and firmware/RTL revisions; re-spin decision is reviewed.

### [ ] E-403 — Qualify pilot manufacturing and release operations — **P3 / G8**

- **Owner:** Quality + operations/sourcing + product + support
- **Depends on:** E-402 and customer acceptance criteria
- **Work:** Run agreed reliability/qualification matrix and sample sizes; establish production test, yield tracking, failure analysis, supplier capacity, lot traceability, software/firmware release, update/recovery and lifecycle support.
- **Done when:** Pre-approved yield/test/reliability/economic/customer thresholds pass; supply and support plans are committed; release authority signs a SKU-specific production decision. A pass for one SKU does not release the other tracks.

## Immediate sequencing

1. Start **E-001 through E-009** as the 4–6 week evidence sprint; mark externally blocked items honestly.
2. Begin **E-101** once the authoritative source/toolchain is identified; then execute E-102–E-108 in dependency order.
3. Run E-201–E-206 only after the product scope and functional evidence support the investment decision.
4. Run E-301–E-303 only with explicit parallel-track resources; do not let them obscure GRX930 blockers.
5. Run integration, silicon, and pilot tasks only after the appropriate standalone module gates pass.

## Review cadence and task acceptance

At each weekly review, report task ID, named owner, target date, status (`not started`, `in progress`, `blocked`, `done`), dependency changes, artifact link, and gate impact. A task is `done` only when its stated acceptance evidence is reviewed and archived. Record go/hold/stop at the gate review; do not convert an open blocker into a schedule estimate.
