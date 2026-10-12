# GRXGPU First Development-Board Demo

**Name:** Three-Engine Inference Chain
**Status:** Proposed engineering acceptance spec; numerical targets below are recommendations to ratify before test execution.
**Purpose:** Prove the four-core CPU/NPU system can orchestrate a real job through the GRX930 NPU, G100, and PTA, return a correct result, and measure complete-system latency and energy. This is an integration demonstrator, not a product benchmark or production-readiness claim.

## 1. The demo in one sentence

Run a versioned, fixed-weight, three-layer classifier as one submitted job: four RV64 CPU cores prepare and schedule a batch, the GRX930 systolic NPU computes layer 1, the G100 computes layer 2, the PTA computes layer 3, and the CPU performs the inter-layer activation/quantization and final classification; compare the result with a bit-accurate CPU reference and compare latency/energy against matched ablations on the same board.

All four blocks must participate in the full-chain configuration. The CPU-only and partial-chain configurations below are controls, not substitutes for the full demo.

## 2. Workload contract

### Fixed canary model

Use a small, deterministic MLP for the heterogeneous board-integration test. Separately, use MLPerf Tiny Visual Wake Words (VWW) as the interim GRX930 product engineering baseline; neither workload implies a customer model or framework is supported.

| Layer | Logical operation | Assigned engine | Proposed format |
|---|---|---|---|
| Input | 16 vectors × 64 signed features; input and weights versioned and checksummed | Four-core RV64 CPU prepares/scales the batch | int8 input |
| FC1 | 64 → 64, bias, activation | GRX930 8×8 systolic NPU | int8 × int8, int32 accumulation; specified requantization |
| Inter-layer 1 | ReLU and activation scale conversion | RV64 CPU cores | deterministic integer reference |
| FC2 | 64 → 64, bias, activation | G100 digital GPU | int8 where supported; otherwise record the chosen format and reference rounding contract |
| Inter-layer 2 | ReLU and conversion to the PTA's declared input representation | RV64 CPU cores | explicit scale/format conversion |
| FC3 | 64 → 16 logits | PTA | PTA-native supported representation; conversion, optical programming, and readout included |
| Result | 16 logits per input, argmax/class ID, status and trace | Four-core RV64 CPU | compare with golden output |

The dimensions are an **initial common-matrix proposal**, not a claim that the current NPU, G100 bitstream, or PTA supports those exact shapes. Before freezing vectors, confirm each engine's operand format, tile dimensions, alignment, command path and memory bounds. If a PTA cannot execute 64×16 directly, pad/map it in the adapter and validate only the 16 logical logits. If a current engine lacks INT8, use its supported format and pin a separate golden reference for that conversion path. Do not silently emulate PTA on the CPU and count that as a PTA pass.

Weights, biases, scales, inputs, expected intermediate tensors and expected final outputs are generated once, checked into or archived with the test bundle, and identified by a manifest/checksum. Keep a small hand-computable set for debugging and a fixed **1,000-input** acceptance set. The CPU golden model runs the identical declared rounding, saturation and conversion rules; a separate high-precision reference measures model-quality loss.

### CPU participation

All four RV64 cores must be online and identified in the run manifest. The runtime pins/assigns work so the CPU demonstrably performs command orchestration, parallel input preparation, inter-layer conversion/activation, and final output validation. Per-core retired instructions or equivalent activity counters must show nonzero useful work on every core in the full-chain run. The CPU-only baseline also uses the same four cores and software implementation; it must not be a single-core strawman.

### End-to-end boundary

**Warm-job latency starts** when the host/runtime submits a job descriptor with the 16 input vectors available in the declared host-visible memory and **ends** when all 16 final results and the completion status are visible to the caller. Include dispatch/queueing, all required CPU work, transfers/DMA, inter-engine synchronization, activation/format conversion, PTA programming if per-job, PTA readout/conversion, and completion reporting. Do not assume shared coherent memory: use the actual buffer ownership/copy protocol and count all bytes and copy time.

Also report **cold-start latency/energy** from a defined power-on or module-reset state through model/weight loading, PTA setup/calibration if required, first completed batch and result readback. Cold and warm results are separate; cold startup is not hidden inside a warm number. Clearly say whether external lab laser, controller, or measurement equipment is required.

## 3. Run matrix and fair controls

Run these four configurations on the same physical board and software release:

| ID | Path | What it isolates |
|---|---|---|
| **C0 CPU-4** | All three layers and preprocessing/postprocessing on the four-core RV64 CPU; accelerator modules remain attached and powered in their defined idle state | Matched full-graph reference for speed/energy comparisons |
| **C1 NPU** | FC1 on GRX930 NPU; remaining layers on CPU | NPU contribution and CPU↔NPU handoff |
| **C2 NPU+G100** | FC1 on NPU, FC2 on G100, FC3 on CPU | G100 contribution and second handoff |
| **C3 Full chain** | FC1 on NPU, FC2 on G100, FC3 on PTA | Required three-engine demo and total system effect |

Additionally run **single-engine diagnostics** for each accelerator's assigned layer against the same layer on CPU. These explain stage-level results but do not replace C0–C3 end-to-end comparisons.

Hold board revision, input/weight checksums, clock/power settings, compiler/runtime/firmware/driver revisions, memory placement, cooling, and ambient conditions constant. Randomize configuration order where practical and repeat each configuration in at least **30 measured trials** after warm-up; each trial processes all 1,000 fixed inputs. Report per-job p50/p95/p99, throughput, bytes transferred, per-stage timing, board/module energy, temperatures and run-to-run spread. Retain raw traces/logs and define timeout handling before running.

## 4. Correctness and quality gates

### Gate F — functional integration (hard pass/fail)

- **100% of 1,000 inputs complete** in C0–C3; no lost, duplicated, reordered, timed-out or unacknowledged job/result.
- CPU goldens and all deterministic digital-stage outputs match the bit-accurate integer/fixed-format reference exactly, after the specified saturation and conversion points.
- PTA FC3 raw outputs meet both proposed numerical criteria versus its declared-format reference: normalized RMS error ≤ **1.0%** and maximum absolute error ≤ **2.0% of the reference full-scale output**. Define full scale from the frozen golden manifest; no near-zero relative-error metric.
- Final class ID agrees with the declared reference for at least **99.5%** of the 1,000 vectors; separately report top-1 agreement and high-precision model-quality score. If the PTA integration cannot meet the output criteria, integration is not accepted by loosening them after the run: investigate the precision/calibration path and ratify a revised tolerance against a named workload before retest.
- Each intermediate tensor and final result includes job ID, engine ID, format/scale ID and checksum or equivalent trace evidence. No unverified copy/coherency assumption.
- All four CPU cores show nonzero useful work in C3. The NPU, G100 and PTA each show hardware/module activity attributable to the corresponding layer; host emulation does not count.

The 1.0%/2.0% PTA tolerances and 99.5% class agreement are **proposed prototype thresholds**, not existing PTA capability or a customer quality claim. Freeze them with the PTA numeric format, model and validation owner before qualification.

### Gate L — measurable latency and integration bound

Latency must be measured at the caller-visible boundary in §2. For every configuration publish the complete latency distribution and p99 confidence/spread, not only accelerator kernel time.

- **Integration pass:** C3 p99 warm-job latency is finite, repeatable, and no greater than **2.0× C0 p99** at equal correctness/quality; no trial exceeds the predeclared job timeout. This permits the first board demo to pass even if the serial chain has not yet shown a product advantage.
- **Product-value target:** C3 p95 warm-job latency is at least **20% lower** than C0 p95 (C3/C0 ≤ 0.80) at equal quality. This is a separate stretch/go-no-go gate for claiming the full chain is faster; failure does not erase a functional integration pass.
- **Cold path:** report cold-start time independently, including model load and PTA calibration/programming. Ratify an absolute cold-start budget after the target board and PTA setup time are measured; do not infer it from warm latency.

Report C1–C3 against C0 and per-layer accelerator vs CPU timings. If C3 is slower, report the transfer, queue, conversion, calibration or execution component responsible rather than omitting it.

### Gate E — energy and measurement quality

Measure energy and performance over the **same run interval**. The primary boundary is wall input to the complete development-board system, including the GRX930 module/FPGA, G100 FPGA/module, PTA, external memory, host/control logic, fans/cooling, and any laser/controller/instrument necessary to execute C3. If wall measurement is not technically possible for the lab setup, use calibrated, synchronized rail measurements for every board/module and all external PTA support equipment; document what is excluded and do not call it whole-system energy.

- Keep all attached modules and cooling in equivalent power/idle states for C0–C3. Do not subtract idle power for the primary result. Report component-rail energy separately as diagnostic data.
- **Integration pass:** C3 energy per completed 16-input batch is fully measured, repeatable, and accompanied by joules/input and average/peak watts; 100% of counted batches pass Gate F. No minimum advantage is implied by measurement alone.
- **Product-value target:** C3 whole-system joules per correctly completed batch is at least **20% lower** than C0 (C3/C0 ≤ 0.80) at equal quality and the same board boundary. If PTA external equipment is needed, its energy is included.
- Rejected/failed runs, warm-up policy, meter location/model/calibration, sample rate, timestamps, ambient temperature, board clocks, and the energy integration window are recorded. Do not combine latency from one run with energy from another.

The 20% latency and energy targets are **recommended go/no-go targets for a product-value claim**, not measured GRXGPU results. If the team wants different thresholds, approve them before seeing results and preserve both the original and revised rationale in the report.

## 5. Reliability and evidence package

Before declaring the demo complete:

1. Complete a 24-hour soak at the approved operating point with repeating C3 jobs: zero silent corruption, hangs, lost completions or unrecovered module faults. Transient errors must be counted and have a defined recovery outcome.
2. Repeat cold boot/reset and model reload **100 times**; verify discovery, accelerator reinitialization, checksums and first-result correctness each time.
3. Run at least one negative test per interface: invalid descriptor, out-of-range buffer, missing/late completion or module timeout. Confirm bounded error reporting and recovery without corrupting the next valid job.
4. Preserve source/build IDs, board/module revision, firmware/runtime/G100/PTA versions, bitstream hashes, compiler flags, model/vector checksums, configurations, test outputs, traces, latency distributions, raw power logs, temperature logs and any calibration artifact.
5. Publish two verdicts: **Integration demonstrated** (Gate F + measurement completeness + reliability passed) and **Product-value target met** (Gate L/E relative targets passed). Never conflate them.

## 6. Sequencing and dependencies

Run in increasing integration order:

1. Prove C0 CPU-4 and each engine's individual layer diagnostic on the board.
2. Pass C1, then C2, then C3; retain a known-good result at every step.
3. Pass functional correctness before accepting performance or energy data.
4. Only after the independent and chained runs pass, test simultaneous unrelated workloads or thermal/power contention.

**Blockers to resolve before starting measured qualification:** exact four-core RV64 implementation and board access; available GRX930 NPU and G100 bitstream; PTA module/format/API and whether its laser/readout equipment can be metered; actual memory and interconnect path; available power instrumentation; and approval of the proposed thresholds. The checked-in GRX930 readiness report still records only small, single-core Verilator GEMM evidence and says four-core coherency and real-board timing were open at report time. Newer physical FPGA/PDK results must supersede that record with artifact references before the demo is called board-validated.

## 7. Benchmarking and claims

This is a **custom demonstrator**, not an MLPerf submission. Use MLPerf-style discipline—fixed workload/version, correctness/quality checks, declared scenarios, reproducible logs and a consistent system power boundary—but do not label results MLPerf compliant without following the exact versioned rules. Official MLPerf Edge documentation describes system power at the wall for benchmark power reporting; its stated measurement boundary and scenario rules should be checked against the applicable current round ([MLPerf Inference: Edge](https://mlcommons.org/benchmarks/inference-edge/), [MLPerf Inference rules](https://raw.githubusercontent.com/mlcommons/inference_policies/master/inference_rules.adoc)).

## 8. Review checklist

- [ ] Confirm four-core SoC/FPGA identity and all four CPU cores active.
- [ ] Confirm NPU/G100/PTA shape, format and memory compatibility; freeze adapters and golden outputs.
- [ ] Confirm PTA source, calibration and measurement boundary.
- [ ] Freeze model, 1,000 inputs, weights, reference, timeout, run order and software/bitstream IDs.
- [ ] Approve the proposed PTA correctness tolerances and 20% latency/energy product-value targets before collecting results.
- [ ] Confirm calibrated power meters, timestamps, thermal setup and raw-data retention.
- [ ] Assign RTL/FPGA, runtime, PTA, board/power, and independent result-review owners.

**Approval to run qualification:** ____________________  **Date:** __________
**Workload/model revision:** ____________________  **Board revision:** ____________________

## References

- [GRXGPU product-family charter](grxgpu_product_family_charter.md)
- [GRX930 v1 product charter](grx930_product_charter.md)
- [GRX930 tapeout readiness report](../grx930/doc/grx930_tapeout_readiness.md)
- [GRX930 firmware README](../grx930/firmware/README.md)
- [MLPerf Inference: Edge](https://mlcommons.org/benchmarks/inference-edge/)
- [MLPerf Inference rules](https://raw.githubusercontent.com/mlcommons/inference_policies/master/inference_rules.adoc)
