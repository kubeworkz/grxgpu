# Implementation Request: 128×64 FPGA PTA Stand-In

**Status:** Draft request; Dave Cook is the PTA technical owner; stand-in implementation lead and schedule are unassigned, FPGA target is not selected, and host/module link is not yet hardware-implemented. The pinned GRXCP design records CXL 2.0 Type-1 over PCIe 5.0 as the first-board link decision, but only at design/model level.
**Request date:** 2026-10-14
**Sponsor / approval authority:** Gridworz.
**Scope:** First-board Three-Engine Inference Chain integration and reliability testing only.
**Decision basis:** [Gridworz PTA decision](first_board_gridworz_decision_2026-10-14.md) and [first-board demo](../grxgpu_first_board_demo.md).

This request translates the approved stand-in category into assignable engineering work. It does not assert that a stand-in exists, authorize procurement or external commitments, set a product schedule, or authorize physical PTA qualification. The FPGA stand-in may demonstrate integration and reliability only; report its timing/energy as FPGA stand-in results, not as photonic PTA performance or product-value evidence.

## 1. Request and proposed owners

**Requested outcome:** Design, implement, integrate, and verify an independently addressable FPGA module that provides a deterministic 128-row × 64-column PTA stand-in through the agreed PTA register/GEMM contract and the selected real host-to-module link.

| Responsibility | Proposed accountable role | Assignment |
|---|---|---|
| PTA technical ownership | Dave Cook | **Named PTA technical owner; does not by itself assign stand-in implementation** |
| RTL, FPGA image, and implementation manifest | PTA RTL/FPGA implementation lead | **Named owner TBD — must accept before work is scheduled** |
| Register/GEMM API and host-side transport | PTA driver/runtime lead | **Named owner TBD** |
| Carrier/link and physical/module integration | Board/system integration lead | **Named owner TBD** |
| Golden model, assertions, scoreboards, and acceptance report | Verification lead | **Named owner TBD; independent reviewer TBD** |
| Scope, workload freeze, and final stand-in acceptance | Gridworz | Sponsor / approval authority per the decision record |

Program leadership must record named assignees, availability, due dates, and a change-controlled request revision before implementation begins. Gridworz's workload-freeze authority is not an engineering implementation assignment.

## 2. Scope and interface boundary

### Required behavior

- Implement one logical 128×64 tile. The first-board canary's FC3 operation is 64→16 and fits within that tile; the stand-in must return the 16 logical outputs required by that operation. Any broader supported shapes, padding, masking, and maximum transaction sizes must be specified and tested before being advertised.
- Implement the agreed PTA discovery/register map and GEMM command semantics, subject to interface review against the selected first-board attachment. Keep register width, alignment, byte order, reset values, RO/RW/W1C behavior, errors, command acceptance, completion, and timeout semantics explicit in the interface control document.
- Expose truthful capabilities for geometry, formats, and implemented operations. Set `PTA_CAPS2[31]` to indicate that the endpoint is a model/stand-in. The host must be able to discover this before submitting work.
- Use the approved integration assumptions for the canary: 6-bit activations, tile-trained 6-bit weights, and 8-bit output ADC representation. Pin scaling, conversion, bias placement, integer widths, rounding, saturation, output range, and argmax behavior to the frozen declared-format contract and golden manifest. Do not substitute int8 FC3 weights truncated to six bits.
- Produce deterministic outputs for the approved seed/configuration and return explicit status for invalid commands, unsupported configurations, range violations, reset, and failed/incomplete work.
- Be independently addressable as an FPGA module and reachable over the real selected board/module link. A host-process implementation, hidden software service, or CPU fallback does not satisfy this request.

### Explicitly out of scope

- Photonic device physics, optical components, analog error/noise behavior, or claims that the FPGA reproduces silicon performance.
- PTA physical-device RMS/tail acceptance, product latency/energy targets, and any photonic qualification or production claim.
- Treating the documented CXL 2.0 / PCIe 5.0 design as implemented hardware. Its architectural decision is recorded, but module/root-port/driver realization and validation remain open; a replacement link requires a separate reviewed board decision.
- Procurement, vendor commitments, manufacturing, or a claim that any chosen FPGA board/platform is already available.

## 3. Platform shortlist and decisions required before implementation freeze

The sourced candidate comparison is in [PTA FPGA stand-in platform options](pta_fpga_platform_options_2026-10-18.md). Its current recommendation is **not selected**: investigate the Agilex 7 I-Series R-Tile kit as the strongest CXL/Gen5 candidate, but do not treat it as approved or procured until the exact Type-1 IP, GRX930 host/root-port support, Linux path, physical link and availability are confirmed. U55C and Arty A7 are not established options for the recorded CXL path. The comparison is an engineering shortlist, not a purchase authorization.

## 4. Prerequisites and decisions required before implementation freeze

- [ ] Gridworz confirms this request's revision and integration-only scope; this is not physical-PTA qualification authorization.
- [ ] Named engineering owner(s), independent reviewer, due dates, and available FPGA/board resources are recorded.
- [ ] Select the FPGA board/part for the PTA stand-in and record the decision ID, availability, vendor tool version, platform package, clock/reset plan, resource limits, constraints, and reproducible build environment. The canonical GRXCP snapshot [`9667adec5e8f07a5415a2832a1622ee9c93d87ab`](https://github.com/kubeworkz/grxcp/commit/9667adec5e8f07a5415a2832a1622ee9c93d87ab) does not select a stand-in target: its [PTA board-transport design](https://github.com/kubeworkz/grxcp/blob/9667adec5e8f07a5415a2832a1622ee9c93d87ab/docs/designs/pta_board_transport.md) says the builder is open and no 128×64 RTL exists. Its `xc7a200tfbg484-1` reference is in a C930/NPU synthesis flow, not a PTA target decision; U55C references identify G100 work. Numeric timing/resource targets remain TBD until a PTA target is chosen and approved.
- [ ] Validate and implement the recorded first-board link decision—CXL 2.0 Type-1 over PCIe 5.0 from the GRX930 host—or approve a superseding decision. The pinned GRXCP design is explicit that no module, root port, or driver code exists. Freeze electrical/protocol details, addressability, reset, clock crossings, error recovery, and connector/carrier boundary from the selected implementation; the design document alone is not working hardware evidence.
- [ ] Register map and GEMM contract revision for this attachment are reviewed and frozen, including the meaning and reset behavior of `PTA_CAPS2[31]`.
- [ ] Canary model, trained-for-tile FC3 weights, scales, 1,000 ordered vectors, declared-format reference outputs, and SHA-256 hashes are materialized and approved using the [golden-generation plan](../grxgpu_first_board_canary_golden_plan.md). The current plan is incomplete; stand-in acceptance against the actual canary is blocked until this package exists.
- [ ] A deterministic seeded reference implementation and an independent checker/scoreboard are identified and version-pinned.

Any unresolved prerequisite is a planning blocker; it must not be replaced with a guessed board, threshold, owner, or schedule. The CXL 2.0 Type-1 / PCIe 5.0 first-board transport is the recorded design decision, not a verified hardware path. Specifically, neither Arty A7-200T / `xc7a200t` nor U55C is an approved PTA stand-in target on the evidence presently pinned.

## 5. Required deliverables

1. **Interface-control document:** register map, GEMM request/completion ABI, capabilities, formats/scales, buffers/ownership, alignment and address map, reset/clock, backpressure, invalid-command behavior, timeouts, errors, and recovery. Record the selected real module link and its board-specific evidence.
2. **Numerical and behavioral specification:** 128×64 logical geometry and implemented suboperations; operation order; 6-bit activation/weight interpretation; accumulator width and overflow; ADC code mapping; rounding/ties; saturation/range; seed behavior; output ordering; and deterministic semantics. Link it to the frozen declared-format reference and canary manifest.
3. **FPGA implementation:** synthesizable RTL or documented hardware description, board/platform project, constraints, memory/streaming architecture, reset and CDC treatment, register block, image-generation scripts, and bitstream/programming artifact. Any resource/timing result must name the exact part, tool, constraints, and build identity.
4. **Host integration:** driver/runtime adapter using the actual module link, capability discovery, model-status enforcement, command submit/complete/error handling, buffer ownership/transfer, bounded timeout, and recovery. It must refuse to represent an endpoint with `PTA_CAPS2[31]=1` as physical PTA silicon.
5. **Verification package:** unit tests for control/register semantics; directed numeric, boundary, and error tests; deterministic randomized tests with recorded seeds; assertions/scoreboards; module-link tests; end-to-end tests; exact commands, tool versions, raw logs, outputs, and checksums.
6. **Release manifest and handoff:** source revision, dependency/tool versions, board/part and image identity, interfaces, configuration, frozen input/weight/reference hashes, test results, known limitations, resource/timing reports, programming and recovery instructions, named reviewers, and dated acceptance disposition.

## 6. Acceptance checks

Acceptance is scoped to this named stand-in revision and target. The signed report must distinguish **built**, **simulated**, **implemented on FPGA**, **programmed**, and **exercised over the physical module link**; a result at one level does not imply the next.

### A. Interface and identity

- [ ] Host discovers the agreed map/version, 128×64 tile dimensions, supported formats/operations, and actual capability values by reading the endpoint; values agree with the implementation manifest.
- [ ] `PTA_CAPS2[31]` is set for the stand-in and observed by the host before work submission. Reports, UI/log labels, and manifests identify results as FPGA stand-in results.
- [ ] Register access and GEMM commands use the agreed alignment, endianness, ordering, response, and error semantics over the real selected link; there is no hidden host-only completion path or CPU computation fallback.
- [ ] Reset, busy/rejected submit, invalid opcode/format/shape/address, timeout, and link/error behavior return bounded, documented statuses. After recovery, a subsequent valid command completes correctly.

### B. Numerical correctness

- [ ] Directed vectors cover zero, positive/negative boundaries as permitted by the declared contract, activation/weight extrema, accumulator boundaries, rounding ties, saturation, output-range boundaries, and the specified logical 64→16 FC3 mapping.
- [ ] With the approved deterministic seed and frozen canary package, all 1,000 ordered acceptance vectors complete; every one of the 16 logical outputs per vector is bit-exact to the seeded declared-format reference. Required result: **zero differing outputs out of 16,000**, with no tolerance.
- [ ] Run the independent checker on raw serialized outputs; record exact hashes and evidence of output ordering. No vector is dropped, reordered, replaced, averaged, or excluded after observing results. Any clipping, missing output, duplicate output, or mismatch fails the run.
- [ ] A second execution with the same frozen inputs/configuration/seed is byte-identical. If the API permits a seed change, verify the declared seed semantics independently; repeatability at a fixed seed remains required.
- [ ] All transferred intermediate/final values carry the required job/engine/format identity and checksum or equivalent trace evidence.

### C. FPGA implementation and real-link integration

- [ ] Clean, scripted build completes for the frozen FPGA target from the pinned source/configuration; final image hash, tool versions, constraints, and build logs are retained.
- [ ] Implementation reports include resource utilization and timing against pre-approved target-specific limits. Those limits must be filled and approved before implementation acceptance; this request invents no frequency or device-fit target.
- [ ] Image is programmed on the identified FPGA board/module and discovered by the host over the real selected module link; logs identify board revision, module/link setup, image hash, and firmware/driver revision.
- [ ] Full C3 path invokes the stand-in for FC3 through that link, sees `PTA_CAPS2[31]`, returns the exact 1,000-vector golden results, and attributes activity to the FPGA endpoint. Host-only emulation does not count.
- [ ] Reliability run exercises repeated launches, backpressure, reset while idle/busy where supported, and at least one interface fault/timeout followed by successful recovery. Record the approved run count/duration before execution; the demo's broader 24-hour soak and 100 reset/reload cycle criteria remain separate board-demo acceptance checks.

### D. Claim and handoff controls

- [ ] Reviewer confirms all reported results are labeled **stand-in** and make no photonic-device, physical PTA RMS/tail, optical latency/energy, or PTA product-value claim.
- [ ] Named implementation owner, independent reviewer, Gridworz decision, unresolved issues, and artifact locations are recorded. No qualification or production authorization is inferred from passing these stand-in checks.

**Implementation disposition:** ☐ Accepted for integration/reliability use ☐ Rejected ☐ Blocked

**Stand-in source/image revision and hashes:** __________________________________

**Target board/part and host-link decision ID:** ________________________________

**Independent reviewer and date:** ____________________________________________

**Gridworz approval ID/date:** _________________________________________________

## 7. Schedule and change control

**PTA technical owner:** Dave Cook.

**Stand-in implementation lead:** TBD until a named PTA RTL/FPGA implementation lead accepts.

**Target board/part and link selection date:** TBD; no PTA stand-in FPGA target is currently selected.

**Implementation milestones and due dates:** TBD after implementation owner and platform are assigned.

**Qualification authorization:** Not granted by this request.

Changes to geometry, register/GEMM contract, seed/reference behavior, numerical encoding, actual module link, board/part, or acceptance package require a new reviewed request/release revision and rerun of affected checks. Preserve prior manifests, images, hashes, and results; do not silently relabel a different configuration as the accepted stand-in.
