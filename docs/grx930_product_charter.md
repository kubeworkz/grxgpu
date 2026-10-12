# GRX930 v1 Product Charter — Decision Draft

**Status:** Ready for product-scope decision; platform and commercial facts still require confirmation
**Decision requested:** Approve a narrowly scoped edge-inference accelerator definition and a time-boxed validation phase. This is **not** approval to freeze RTL, commit to a foundry run, or call the design production-ready.
**Version:** 0.1 — 2026-10-10

## 1. Executive decision

Define the first GRX930 product as an **embedded, quantized edge-inference accelerator module**: a small SoC combining the GRX930 RISC-V control CPU with one 8×8 systolic NPU, using external DDR. Target **batch-1, low-latency inference**. Use INT8 as the required v1 compute path; retain INT4 as an optional efficiency mode gated on model-quality and hardware validation. Keep UART/JTAG for lab bring-up and recovery, not as the assumed customer data interface.

Do **not** scope v1 as a discrete graphics GPU, a PCIe accelerator card, an HBM product, a multi-GPU system, or the 128-core G100. Those introduce separate memory, packaging, software, validation, and commercial programs. The checked-in GRX930 report describes one 8×8 NPU and single-core simulation evidence; it says multi-core behavior is only partially verified. The prior one-control-CPU plus one-NPU scope was the conservative baseline for this charter. The GRXGPU E-001 product brief now proposes four RV64 cores plus one NPU as a product target; sponsor ratification and multi-core validation are still pending, so this proposal does not imply validated four-core capability. See [GRX930 v1 Product Brief](grx930_v1_product_brief.md).

**Recommended authorization now:** approve a 4–6 week product/engineering validation sprint to close the decisions and evidence listed in §8. At its end, hold a go/no-go review for target-PDK feasibility and product RTL hardening. No tapeout date or cost is endorsed by this charter.

## 2. Product definition

| Item | Proposed v1 definition | Status |
|---|---|---|
| Product | Embedded edge-inference accelerator module / SoC | Recommended; decision requested |
| Primary buyer/use | OEM or embedded-system integrator needing local inference under a constrained power/latency envelope | Market hypothesis; validate with named customer |
| Workload class | Quantized embedded local/on-device inference, batch size 1; fixed, published v1 model/operator set | Recommended |
| Compute | One GRX930 8×8 systolic NPU plus four RV64 CPU cores as the current E-001 candidate | Product-target proposal in [GRX930 v1 Product Brief](grx930_v1_product_brief.md); sponsor approval and multi-core validation required |
| Required precision | INT8 inference | Proposed required mode |
| Optional precision | INT4, only for models meeting quality and correctness gates | Stretch; no promise until validated |
| External memory | DDR attached to the module/SoC using a selected, supported controller and PHY | External DDR direction chosen; exact generation/IP not provided |
| Host/product interface | Production host/control interface is an open decision; UART/JTAG are for debug/recovery only | Must select before architecture freeze |
| Form factor/package | Embedded board/module; exact package, connector, and thermal solution follow the FPGA and package feasibility work | Open |
| Software | Stable model-loading and command ABI, firmware/runtime, reference kernels and diagnostic/recovery flow | Required product scope; not yet demonstrated by the checked-in firmware |
| Out of scope | Graphics/display, CUDA compatibility, PCIe card, HBM, chiplets, multi-GPU, broad operator coverage, safety certification | Explicitly deferred unless customer evidence changes the charter |

## 3. Target workloads and benchmark strategy

### Product acceptance workload

Use **MLPerf Tiny Visual Wake Words (VWW)** as the interim engineering baseline under the pinned, internal-only [GRX930 VWW evaluation protocol](grx930_vww_evaluation.md), while, before architecture freeze, selecting **one paid-customer or design-partner model** as the primary product-acceptance workload. The protocol identifies a source snapshot but explicitly does not claim official v1.3 conformance or a completed GRX930 run. VWW is a reproducible engineering comparison only; it does not stand in for customer validation or product acceptance. It must have a named model/version, input dimensions, preprocessing, quantization method, supported operators, accuracy reference, representative data set, expected batch/concurrency, and end-to-end latency target. The customer/workload is not yet known, so this charter does not invent a product performance claim.

### Engineering benchmark set

Use **MLPerf Tiny Visual Wake Words (VWW)** as the selected interim engineering baseline under the [evaluation protocol](grx930_vww_evaluation.md), plus the customer model once identified. VWW is for reproducible engineering comparison only and does not replace customer acceptance. MLPerf Tiny includes keyword spotting, visual wake words/person detection, image classification, anomaly detection, and streaming wake word. It reports quality and single-inference latency/energy; streaming adds continuous operation and duty-cycle behavior. The Tiny suite is a baseline, not a substitute for the selected customer's workload or a complete product spec ([MLPerf Tiny benchmark](https://mlcommons.org/benchmarks/inference-tiny/), [MLPerf Tiny v1.4 results overview](https://mlcommons.org/2026/07/mlperf-tiny-v1-4-results/)). Confirm benchmark version, rules, and current task availability before publishing comparison claims.

### Required quality and performance measures

Report end-to-end measurements from input-ready to output-ready, including preprocessing, data movement, CPU work and DDR traffic. Publish both accelerator-block figures and full-module/system figures, and label the power boundary clearly.

| Metric | Proposed acceptance rule | Value to ratify |
|---|---|---|
| Model quality | INT8 must meet the primary model's pre-agreed quality threshold versus its FP32 reference; default proposal: no more than **1.0 percentage point** loss for accuracy metrics, or an application-specific equivalent for non-accuracy metrics. INT4 must pass its own threshold to be enabled. | Dataset, metric and threshold per model |
| Correctness | 100% of golden test vectors pass; deterministic integer kernels match the specified reference exactly unless the numerical contract explicitly allows otherwise. | Golden vectors and tolerance policy |
| Latency | P50/P95/P99 batch-1 end-to-end latency reported under the declared input and thermal conditions; P99 must meet the customer's service target. | Numeric customer P99 target |
| Energy | Joules/inference and sustained module power measured at the module input; compare against a named CPU-only baseline at equivalent model quality. | Power cap and minimum energy advantage |
| Reliability | Run the customer workload and regression suite continuously for 24 hours at the approved operating point with no incorrect outputs, hangs, or unrecovered faults. | Test conditions and fault policy |
| Thermal | No thermal throttling or violation of component/package limits during sustained workload at specified ambient and airflow. | Ambient, cooling, and package limits |
| Benchmark disclosure | Publish model, quantization, quality, latency, energy/power boundary, software revision, clock, memory configuration and measurement method. | Required for any external claim |

The 1.0-point quality threshold and 24-hour soak are **proposed starting criteria**, not existing GRX930 results or industry certifications. Ratify or replace them with the design partner before using them as release gates.

## 4. System and software contract

### Required v1 system path

1. Secure, diagnosable boot into firmware; provide a documented recovery path.
2. Load a supported quantized model and parameters into external DDR with bounds/error checking.
3. Submit work through a versioned command ABI; execute DMA and NPU operations without CPU/NPU cache incoherence.
4. Return results, status, performance counters and useful error codes to the host/controller.
5. Recover from malformed commands, timeout, reset and failed model load without requiring board power cycling where the hardware permits.

The exact production host interface is a blocking design decision. UART remains a bring-up/debug path. Pick an interface based on the module's actual integrator and board architecture; do not imply PCIe or a host ABI is already implemented.

### Software deliverables before pilot

- Versioned firmware/command ABI and compatibility policy.
- Model import/quantization path, supported operator list, reference implementation, and clear behavior for unsupported operators.
- Runtime or integration library for the selected board/host.
- Diagnostics, performance counters, watchdog/timeout handling, firmware update and recovery procedures.
- Reproducible toolchain/build and golden-vector suite tied to RTL and firmware revisions.

The checked-in [GRX930 firmware README](../grx930/firmware/README.md) lists the ELF loader, TCU/DXA initialization, interrupts, multi-core support, cache configuration and memory protection as TODOs. These need to be reconciled against the current implementation before treating the host-to-inference path as product-complete.

## 5. Product architecture boundaries

### Include in v1

- One NPU compute block with INT8 required and INT4 conditional.
- RV64 control CPU subsystem (four cores are the E-001 product-target proposal; validate before freeze), local control/status registers, DMA path and external DDR interface.
- Only the cache/coherency features required to keep CPU, DMA and NPU results correct for the chosen workload.
- Debug/test access, reset/clocking, observability, production test hooks and error reporting designed in from the start.
- FPGA-prototype board/module and the minimum firmware/runtime needed for the target workload.

### Defer unless validated by customer economics

- Additional CPU/NPU cores or clusters beyond the proposed four-core control subsystem.
- Graphics pipeline, display controller, rasterization and ray tracing.
- HBM, advanced 2.5D/3D packaging, chiplets/UCIe.
- PCIe Gen6 or any high-speed host link without chosen IP and compliance plan.
- General CUDA/HIP compatibility, arbitrary GPU workloads and multi-tenant scheduling.
- Functional-safety certification or security certification not required by the target market.

## 6. Engineering exit criteria

A gate is passed only with archived artifacts, not a plan or a tool installation.

### Gate A — physical FPGA proof

- Record exact FPGA board and device, RTL commit, constraints, tool versions, bitstream checksum, firmware and test-data revisions.
- Boot the actual board and run model load → DDR/DMA → NPU → result readback for every required precision and supported shape.
- Run multi-tile customer-like workload, repeated launches, stalls/backpressure, concurrent CPU/DMA traffic, reset/recovery and invalid-command cases.
- Pass all golden vectors and model-quality threshold; report P50/P95/P99, sustained throughput, full-module power and temperature under stated conditions.
- Measure timing closure and operating frequency on the chosen board; do not substitute a sub-block FPGA synthesis result.

### Gate B — target-PDK feasibility

- Record exact foundry, process/node, PDK revision, license/use rights, standard-cell libraries/corners, RC/extraction data, design rules and signoff tools.
- Confirm actual SRAM macros/compiler, memory test/repair support, IO/pad/ESD, PLL/clock/reset, scan/JTAG, and required DDR controller/PHY IP are licensable, deliverable and compatible with package.
- Run synthesis and physical feasibility with real memory and interface abstracts. Report full top-level area, timing by agreed corners, congestion, workload-based power, die estimate, IO/pad overhead and thermal/package feasibility.
- Close all critical unknowns with written supplier/foundry/OSAT answers. A PDK copy or generic synthesis result alone does not pass this gate.

### Gate C — RTL freeze / tapeout authorization

- Product workload regressions pass on reference and RTL simulators; no open critical correctness issue.
- DMA/cache coherency and concurrency are proven at the selected core count. If not, v1 remains single-core/single-NPU.
- Protocol assertions/formal checks, corner cases, error/recovery, DFT/MBIST and scan strategy reviewed; coverage closure accepted by the verification owner.
- Full physical signoff is clean or has written foundry-approved waivers: MCMM setup/hold, extracted timing, power integrity, EM/IR, thermal, DRC/LVS, antenna, scan and manufacturing test.
- Independent design, verification, physical-design and product owners approve the freeze; budget includes package, test, characterization and a planned corrective revision.

### Gate D — pilot / production release

- Silicon bring-up passes boot, memory, DMA, NPU, stress, thermal and reset/recovery tests on production-intent boards.
- Customer model quality, P99 latency, energy/power, reliability and software compatibility meet the ratified targets.
- Pilot yield, test time, failure-analysis process, unit economics, supplier capacity, lifecycle support and customer acceptance meet pre-agreed thresholds.

## 7. Business and release constraints

No market size, price, NRE, production volume, gross-margin target, customer commitment, or foundry slot has been supplied. These are **charter blockers**, not values to fill from generic tapeout estimates. Before target-PDK implementation funding is approved, the product owner should supply:

- Named design partner/customer and written workload/use-case evidence.
- Target unit price/cost ceiling, initial and annual volume range, and minimum gross margin.
- NRE, engineering headcount, schedule owner, package/board/test budget, and one-revision contingency.
- Target launch window and support/lifecycle obligations.
- Supplier confirmations for foundry, PDK rights, memory/PHY IP, package/OSAT, and test capacity.

## 8. Decisions for the 4–6 week charter-validation sprint

| Decision / artifact | Proposed owner | Due from sprint | Current status |
|---|---|---|---|
| Confirm edge-inference module vs broader GPU scope | Product sponsor | Signed product scope and explicit exclusions | User-selected direction: edge inference |
| Select primary customer model and quality/latency target | Product + design partner | Model card, representative data, quality and P99 target | Open |
| Confirm quantization and v1 precision | ML/software + RTL | INT8 acceptance; INT4 include/defer decision | Proposed INT8 required, INT4 conditional |
| Choose CPU/NPU/core count | RTL + verification + product sponsor | Four-core + one-NPU product-target decision, validated in integrated RTL/FPGA or explicitly revised by sponsor | Four RV64 cores selected as E-001 direction; multi-core evidence and sponsor sign-off open |
| Identify external DDR generation/controller/PHY | SoC + sourcing | Part/IP, bandwidth/capacity, license and package feasibility | External DDR chosen; exact solution open |
| Select production host/control interface | Product + SoC | Interface, ABI, board path and test approach | Open; UART/JTAG debug only |
| Confirm PDK and manufacturing route | Physical design + legal/sourcing | Foundry/node/revision/rights, signoff decks, MPW/production path, quote/slot | User reports PDK ready; identity/rights unverified here |
| Confirm FPGA and run status | FPGA lead | Board/device, bitstream, actual workload results, timing/power report | User reports FPGA ready; exact details/results unverified here |
| Approve product economics and funding | Product sponsor + finance | Target price/cost/volume, NRE and re-spin reserve | Open |
| Go/no-go for next stage | Executive sponsor | Signed review against evidence above | Not yet authorized |

## 9. Known evidence and limits

The [GRX930 readiness report](../grx930/doc/grx930_tapeout_readiness.md), dated 2026-09-11, records 18 GEMM cases and four UART tests passing in a Verilated single-core setup, but also says the cases were limited to small shapes, four-core coherency was unverified, FPGA timing/bitstream was not done, and no GRX930 ASIC synthesis report existed. The user reports that an FPGA and PDK are ready; the [initial E-002 workspace evidence manifest](grx930_evidence_manifest.md) records that exact device/revision, physical-board workload measurements, license rights, and target-PDK reports have not been independently verified in this worktree. Update the evidence ledger with approved artifacts before any gate is claimed passed.

The older [G100 ASIC tapeout plan](grxgpu_g100_tapeout_plan.md) and broad Vortex GPU design are not the GRX930 product definition. Their area, schedule, shuttle, cost, and HBM assumptions must not be carried into this charter without current supplier quotes and target-PDK implementation data. This document authorizes no tapeout, purchase, supplier commitment, or publication of performance claims.

## 10. Review outcome

**Recommended decision:** approve the proposed product category and the 4–6 week validation sprint; keep the product-target proposal at four RV64 cores plus one 8×8 NPU, external DDR, and INT8 batch-1 inference pending sponsor approval and multi-core evidence. Require the sprint's named workload, exact platform facts, interface choice, target metrics, and business case before approving RTL freeze or target-PDK implementation.

**Approver:** ____________________  **Date:** __________
**Product sponsor:** ____________________  **Engineering lead:** ____________________

## References

- [GRX930 tapeout readiness report](../grx930/doc/grx930_tapeout_readiness.md)
- [GRX930 firmware README](../grx930/firmware/README.md)
- [GRX930 production compute silicon plan](grx930_production_gpu_plan.md)
- [MLPerf Tiny benchmark](https://mlcommons.org/benchmarks/inference-tiny/)
- [MLPerf Tiny v1.4 results overview](https://mlcommons.org/2026/07/mlperf-tiny-v1-4-results/)
