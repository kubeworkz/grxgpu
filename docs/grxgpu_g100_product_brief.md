# G100 Product Brief and Evidence Ledger — Discovery Scope Decision

**Status:** Sponsor-approved discovery scope only; not funding approval, final SKU approval, or a production specification.
**Version:** 0.3 — 2026-10-13
**Portfolio context:** [GRXGPU Production Readiness Plan](grxgpu_production_plan.md) · [Engineering Task List, E-301/E-302](grxgpu_engineering_task_list.md)
**System of record:** GRXGPU/Vortex source and its canonical engineering evidence workflow. This portfolio brief records scope and evidence disposition; it is not a copy of RTL, raw logs, or build outputs.

## 1. Sponsor decision and scope boundary

**Decision: APPROVED — discovery scope only.** On 2026-10-13, **Kubeworkz (product sponsor)** approved using a compute-only G100 demonstrator as the bounded discovery baseline: investigate one cluster × four cores with TCU and DXA enabled, and use `sgemm_tcu_wg_dxa` at K=64/K=512 as candidate engineering correctness/integration tests. This records the user-selected sponsor decision in this interaction; it does not assert that the candidate has been built, reproduced, or accepted as a customer workload.

The approved discovery boundary excludes graphics, 128-core scale, HBM, PCIe 6.0, NVLink, and any ASIC process/package choice from this baseline. This is **not** approval of a final SKU, customer workload, technical requirements, schedule, staffing, project funding, supplier engagement, purchase, foundry slot, tapeout, or production release. The source revision, source-level candidate configuration, and proposed workload arguments are recorded in the linked manifest; dependencies, actual build/run, generated input/golden hashes, FPGA evidence, and ratified acceptance thresholds remain open.

**Decision record**

| Field | Recorded decision |
|---|---|
| Approver | Kubeworkz — product sponsor |
| Decision date | 2026-10-13 |
| Outcome | Approve the recommended G100 discovery scope described above |
| Authority granted | Use that scope as the E-301 discovery baseline for product/evidence definition |
| Explicitly not authorized | Funding or resource allocation; final SKU/customer acceptance; supplier/PDK commitments; purchases; ASIC implementation/tapeout; production claims |
| Outstanding | Named technical owners, canonical source/config/workload manifest, fund/defer resource decision beyond this discovery scope |

Treat the historical tapeout plan and architecture values as hypotheses/evidence leads, not as requirements or commitments. A later scope or funding decision must be separately recorded and attributable.

## 2. Candidate product envelope

| Field | Discovery scope / current candidate | Status / required decision |
|---|---|---|
| Discovery category | Programmable digital SIMT/GPGPU compute accelerator based on Vortex | Accepted for discovery only; final commercial category, buyer and product definition remain open. |
| Initial configuration | Investigate one cluster × four cores with TCU + DXA enabled | This topology/extension combination defines the discovery scope only. Exact implementation settings in the manifest are provisional reproduction choices, not sponsor-ratified product requirements; successful build/run is unverified. |
| Graphics | Excluded from this compute-only discovery baseline | Sponsor-approved discovery exclusion; not a final product decision. Reopen only through a separately recorded scope decision supported by a defined workload and implementation evidence. |
| Primary workload | Investigate `sgemm_tcu_wg_dxa` at K=64 and K=512 | Approved as candidate discovery test points only; M/N=64 in the manifest's proposed commands is a source/test-default selection, not a sponsor-ratified dimension. This is not a named customer workload, product benchmark, or acceptance threshold. Pin inputs/golden hashes, precision and numerical tolerance before claiming a reproduced outcome. |
| Software/API scope | Existing Vortex kernel/runtime path for the chosen workload; this is not a commitment to CUDA binary compatibility | Pin the exact compiler/runtime, host interface, command ABI, memory ownership, supported operators, and APIs in the candidate brief; all remain TBD pending source/config and sponsor decisions. |
| Memory boundary | Use the memory configuration actually exercised by the selected Vortex build; specify host memory, device/global memory, local/shared memory and transfers | TBD pending a runnable product-path configuration and interface owner. HBM3e is not assumed. |
| FPGA target | TBD; select an available board/device only after full-configuration mapping and interface needs are checked | No whole-G100 FPGA timing/resource closure is established by sub-block estimates. |
| ASIC/technology | No process selected for this candidate | Historical TSMC 28 nm assumptions are not current supplier evidence or approval. |
| Power, thermal, area, frequency, memory bandwidth | TBD | Ratify only after workload boundary, target implementation and measurement method are agreed. No old paper/shuttle estimates are acceptance limits. |
| Customer / market / volume / launch / support | TBD | Not covered by the discovery-scope approval; requires a separate E-301 decision and evidence. No commercial facts are asserted here. |

## 3. Evidence vocabulary

- **Reproduced:** rerun against identified source, configuration and inputs; exact command, tools, raw output and result are retained and reviewed.
- **Historical report:** a result is described in an existing report, but this brief has not independently rerun it or validated its full provenance.
- **Proxy / extrapolation:** partial synthesis or a model-based estimate; not full-chip FPGA closure or target-process PPA.
- **Paper target:** an architecture aspiration without implementation evidence for the claimed product configuration.
- **Supplier-confirmed:** written current evidence for the exact product, process, IP, package or commercial term. No supplier-confirmed G100 entries are established by this brief.
- **Open / not established:** required evidence is missing, not tied to a configuration, or awaiting a decision. Absence here is not proof the evidence does not exist elsewhere.

## 4. Evidence ledger

| ID | Claim / evidence area | Classification and current disposition | Primary reference and limitation | Required next evidence |
|---|---|---|---|---|
| G100-E01 | 128-core (8×16) flagship architecture, HBM3e, PCIe 6.0/NVLink, 2 GHz and broad graphics/tensor feature set | **Paper target.** Do not treat as an implementable or approved v1 configuration. | [G100 architecture design](designs/gpu_chip_design.md) explicitly labels itself a paper design/implementation target; it describes new host/memory/link capabilities. | Select a source/config that exists; enumerate implemented versus absent blocks and revise the product boundary. |
| G100-E02 | One-cluster × four-core TCU/DXA WGMMA tests at K=64 and K=512 | **Historical report; not reproduced for this brief.** The tapeout plan reports rtlsim passes and bit-identical SimX/rtlsim behavior for named cases. The pinned test Makefile now documents different kernel variants for its SimX double-buffered path and Verilated RTL/FPGA single-buffered path; the historical parity claim must not be read as proving this exact current-source variant pair is cycle-parity comparable. | [G100 tapeout plan](grxgpu_g100_tapeout_plan.md), §§2 and 10; current variant split is documented in the [pinned evidence manifest](grxgpu_g100_evidence_manifest.md) and source Makefile. Results lack a source/config/run bundle link with checksums in this brief. | Re-run each documented mode from canonical Vortex source with variant-specific config/build defines and retain commit, tool versions, exact commands, inputs/golden hashes, raw logs and independent review. Any parity claim must use demonstrably identical kernel defines and inputs. |
| G100-E03 | 128-core SimX TGM double-buffer sweep, K=16…512 | **Historical report; simulation-only as reported.** Five cases are described as passing with `NUM_DXA_CORES=2`; this is not FPGA or silicon evidence. | [G100 tapeout plan](grxgpu_g100_tapeout_plan.md), §2. Exact immutable run provenance and raw artifacts are not established here. | Reproduce after E-301 pins the config and workload; add the selected supported parity/RTL integration checks. |
| G100-E04 | ECP5/Artix resource counts and full-G100 fit statements | **Partial synthesis measurements plus extrapolation; full configuration closure not established.** Reported sub-block data can inform experiments but do not prove full-system FPGA fit. | [G100 tapeout plan](grxgpu_g100_tapeout_plan.md), §§10.5–10.10. The plan itself notes omitted scheduler/LSU/cache/fabric work in places and multiple resource estimates/configurations. | Synthesize and implement the exact chosen top/config; include all enabled blocks, memories, clocks and interfaces; provide tool logs, board/part, constraints, utilization and timing coverage. Reconcile differences between estimates. |
| G100-E05 | Nangate45/Yosys logic area scaled to a 28 nm flagship and total die area | **Open-library proxy and extrapolation, not target-process PPA.** | [G100 tapeout plan](grxgpu_g100_tapeout_plan.md), §2. The plan records blackboxed memories and omitted inter-cluster fabric; its legacy SRAM estimates conflict materially with later area summaries (for example, ~13 mm² versus ~100 mm² for 6 MB). | Reconcile arithmetic/configuration and memory inventory first; then use the actual target libraries, macros, floorplan and signoff assumptions if/when authorized. |
| G100-E06 | HBM3e, PCIe 6.0, NVLink/NVLink-C2C, large L2 and full graphics path | **Not established for the candidate.** The architecture document identifies major interfaces as new/design targets; no complete G100 system-interface result is linked here. | [G100 architecture design](designs/gpu_chip_design.md), §§2–3, 8 and 11. | Freeze one realistic host/memory boundary and demonstrate its complete data path; obtain separate supplier/IP evidence before any ASIC claim. |
| G100-E07 | TSMC 28 nm HPC+ MPW date, cost, SRAM availability, schedule and package assumptions | **Historical planning assumptions, not supplier-confirmed.** They are not commitments or budget authority. | [G100 tapeout plan](grxgpu_g100_tapeout_plan.md), §§3 and 6; the plan contains dated shuttle estimates that require fresh written quotes and rights checks. | Keep TBD until named sourcing/legal owners provide current written route, rights, quote, capacity and delivery evidence in controlled records. |
| G100-E08 | Production readiness, customer suitability and release targets | **Not established.** No approved customer workload, quality/latency/power target, complete driver/runtime contract, package, target-process signoff or production qualification is claimed by this brief. | Portfolio gates in the [production plan](grxgpu_production_plan.md); open choices in this draft. | Ratify product requirements; complete G0–G8 evidence for the exact SKU. |

## 5. E-301/E-302 exit package

See the linked [G100 source/config/workload evidence manifest](grxgpu_g100_evidence_manifest.md) for the tracked Git revision, hashes of relevant build/test definitions, a source-resolved **proposed experiment configuration** (not a sponsor-ratified product configuration), and proposed workload commands. It pins repository inputs only; it does not record a completed build or run.

Before E-301 is marked done, attach or link:

1. Recorded sponsor approval of the compute-only discovery baseline is complete (decision table above). A separate resource/funding decision remains open; this scope approval does not satisfy it.
2. Name product/engineering owners and complete the versioned brief, marking each requirement **proposed**, **ratified**, or **TBD**.
3. Evidence manifest pinning source revision, all configuration overrides, tools, workload/input/golden-output hashes, and authoritative raw-result locations.
4. Evidence ledger that separates reproduced behavior, historical simulation claims, FPGA measurements, proxy synthesis, paper targets, supplier-confirmed facts, and unresolved blockers.
5. Explicit host/memory/software boundary, candidate area/power limits or a recorded TBD decision, and dependencies for full-system integration.

E-302 is a subsequent evidence task, not implied complete by this brief: reproduce the canonical workload and parity checks, then separately prove full accelerator-interface and target-FPGA timing/resource behavior for the chosen configuration. Follow Vortex [testing guidance](testing.md) and the [model-parity case definition](../ci/testcases/model_parity.yaml); use `xrt` when the claimed target is full RTL/AFU integration, as required by the [production plan](grxgpu_production_plan.md).

## 6. Decisions and open actions

| Decision / action | Accountable role (unassigned) | Status |
|---|---|---|
| Approve or revise compute-only discovery candidate and exclude/retain graphics | Kubeworkz — product sponsor | Approved for discovery baseline only, 2026-10-13; final SKU decision remains open |
| Confirm exact Vortex source/config and board/device candidate | G100 architecture/RTL + FPGA leads | Open |
| Ratify whether to use the proposed workload dimensions, reference/tolerance, and separate driver-specific kernel variants as acceptance criteria | Product/software + verification leads | Open; the current tests are discovery experiments only |
| Define host, memory, runtime/API and buffer-ownership boundary | System/software leads | Open |
| Ratify area/power/thermal/frequency requirements or record TBD | Product + system + FPGA/physical-design leads | Open |
| Reconcile G100 tapeout-plan area/memory estimates and classify claims | Physical-design + RTL/verification reviewers | Open |
| Obtain current restricted supplier/PDK/IP/package facts if ASIC work is funded | Sourcing/legal + physical-design leads | Not assessed; controlled records required |
| Decide whether to allocate resources beyond the approved discovery baseline; record next gate | Named sponsor | Pending; no funding or tapeout implied |

**Current disposition:** The sponsor-approved discovery boundary is recorded, but E-301 remains **in progress** pending named technical owners, an immutable source/config/workload manifest, completion of the evidence review, and a separate resource/fund-defer decision. E-302 reproduction, complete FPGA closure, supplier confirmation and production gates remain open or unverified. This brief records scope approval only; it is not validation, final SKU approval, funding, tapeout authorization, or an external product claim.
