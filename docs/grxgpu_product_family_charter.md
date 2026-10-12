# GRXGPU Product Family Charter — Decision Draft

**Status:** Portfolio scope proposed; product, interface, commercial, and platform facts remain to be ratified
**Decision requested:** Adopt GRXGPU as the umbrella product family for the four compute tracks below, and authorize definition of one modular development PCB that can demonstrate their integration. This is not approval for RTL freeze, a foundry commitment, or a claim that the products are production-ready.
**Version:** 0.1 — 2026-10-10

## 1. Portfolio thesis

GRXGPU is a family of **heterogeneous, RISC-V-centered compute products** sharing a development and software integration platform:

1. **GRX930 CPU/NPU SoC:** a proposed four-core RV64 host/control subsystem coupled to the GRX930 systolic NPU for embedded inference.
2. **G100 digital GPU:** a programmable, SIMT/GPGPU product based on Vortex, targeted at parallel compute and—only where product requirements justify it—graphics.
3. **PTA photonic tensor accelerator:** a distinct electro-photonic tensor-compute product, initially treated as a separately addressable module attached to the platform.
4. **GRXGPU development PCB:** a common bring-up and system-validation platform that hosts the CPU/NPU SoC and provides modular attachment, power, memory, control, and debug paths for the G100 and PTA implementations.

The portfolio is **not one monolithic chip** by default. Share system contracts and board infrastructure where useful; keep the three accelerator implementations independently testable and independently revisable. A single PCB is an integration vehicle, not proof that the products belong on one die or package. In particular, the photonic compute path must include its electronic control, data movement, optical source, conversion/readout, calibration, and package boundaries—not only the photonic core.

## 2. Product-family architecture (proposed)

| Track | Proposed role | First demonstrator | Boundary and status |
|---|---|---|---|
| **GRX930 CPU/NPU** | Low-power embedded control and inference | Four-core RV64 system plus one NPU executing a named quantized model | Proposed SoC on the development PCB. Four-core integration, product memory/host interface, and hardware measurements require confirmation. Existing checked-in GRX930 evidence is primarily single-core Verilator testing; see [readiness report](../grx930/doc/grx930_tapeout_readiness.md) and [GRX930 v1 charter](grx930_product_charter.md). |
| **G100 GPU** | Programmable SIMT/GPGPU compute, with graphics a separate scope decision | Configurable Vortex implementation on FPGA or a smaller ASIC configuration; validate a useful end-to-end workload | Separate accelerator endpoint on the development platform. The repository's G100 document is explicitly a paper design / implementation target, not a completed flagship chip ([G100 architecture](designs/gpu_chip_design.md)). Do not use the 128-core/HBM targets as v1 commitments. |
| **PTA photonic accelerator** | Tensor operations where system-level optical compute demonstrates an advantage for selected workloads | Independently addressable electro-photonic module or measured prototype connected to the board | Separate product track and module boundary initially. Compute method, optical/electrical partition, memory/weights, source, conversions, calibration, software, and useful precision must be proven. No PTA RTL, package, or product performance is asserted by this charter. |
| **Development PCB** | Bring-up, cross-product orchestration, performance/energy comparison, and integration-risk discovery | Modular carrier with GRX930 CPU/NPU, external memory, debug/control, and attach points for G100 and PTA | Board architecture is a proposed integration platform, not a production board. High-speed link choices and whether G100/PTA attach directly, by mezzanine, or by external instrument/module remain open until bandwidth and physical constraints are measured. |

### Product naming and relationship

Use **GRXGPU** for the portfolio/platform, and retain **GRX930**, **G100**, and **PTA** as distinct product or program names. The GRX930 document remains the child charter for the CPU/NPU product; it does not define G100 or PTA. Decide whether “GRX930” names the CPU/NPU SoC, the NPU block, or the existing overall platform before publishing external collateral.

## 3. Development PCB: first system definition

### Board purpose

The board should answer one central question: **can the four tracks cooperate through a stable software and data-movement contract, and do they improve the intended workloads at the whole-system level?** It must support repeatable comparison and debugging, not just demonstrate that each block can toggle.

### Proposed board organization

- **Baseboard host:** GRX930 four-core RV64 CPU/NPU SoC as the initial boot/control authority, if the current RTL and FPGA mapping support that configuration. Include JTAG/debug, reset/clock control, boot/recovery, console, telemetry, and safe power measurement points.
- **Memory:** attach the exact external DDR device/controller supported by the selected SoC/FPGA implementation. Specify capacity, bandwidth, ECC/parity policy, topology, and which agents can access it. Keep separate local memories visible in software; never imply a shared coherent address space before proving it.
- **G100 connection:** provide a replaceable FPGA/accelerator module path with sufficient memory and host bandwidth for the selected validation workload. Select the physical connector and protocol after measuring required throughput, available FPGA transceivers, latency, and board signal integrity. Do not assume PCIe or a specific generation is implemented.
- **PTA connection:** use a replaceable photonic module or lab interface that accounts for optical coupling/source, control, detector/readout, calibration, thermal sensing, and data conversion. The board should permit electrical control/data and optical-path measurement; the PTA may require an external laser or instrument during early prototypes.
- **Power and thermal:** instrument the baseboard and each module independently. Define rails, sequencing, current limits, cooling, sensor placement, and safe shutdown before connecting optical sources or high-power compute modules.
- **Observability:** expose timestamps, command/event IDs, queue occupancy, DMA bytes, accelerator busy time, errors, clocks, module temperatures, and calibrated power measurements with a common trace format.
- **Expansion:** prefer replaceable modules over routing all unproven high-speed interfaces onto the first PCB. Preserve a direct-probe/lab mode for G100 and PTA bring-up.

### Board acceptance gates

1. Power sequencing, reset, boot, recovery, JTAG, clocks, and telemetry are repeatable across cold and warm starts.
2. Each module can run its own correctness suite independently before any heterogeneous integration test.
3. A common host job can select an allowed engine, transfer a buffer, launch work, observe completion/error, and retrieve results with no hidden host round-trips.
4. Shared-memory or zero-copy claims are made only after coherency, ordering, cache maintenance, and ownership rules are tested. Otherwise, use explicit copies and measure their cost.
5. Report per-engine and whole-board latency, throughput, energy, and temperature on the same input/output workload and with the full data-movement path included.
6. Simultaneous activity on CPU/NPU, G100, and PTA is a later stress gate; it must not block initial independent module bring-up.

The staged acceptance workload, run matrix, and proposed correctness/latency/energy gates are specified in the [GRXGPU first development-board demo](grxgpu_first_board_demo.md).

## 4. Shared platform contract

The family should share a **system API**, not force all compute engines into one ISA or execution model.

- **Device discovery:** stable product/engine IDs, capability/version registers, precision and shape limits, memory ranges, and fault state.
- **Job model:** versioned submit/complete/error descriptors; explicit dependencies and timeouts; no implicit global synchronization.
- **Buffer contract:** ownership, alignment, addressability, cache/coherency behavior, copy requirements, and lifetime rules documented per endpoint.
- **Model/artifact packaging:** versioned graph/weights/metadata with declared quantization, layout, required operators, and engine placement constraints. Host dispatch may choose among eligible engines; unsupported layers fall back only if the software explicitly supports and measures that behavior.
- **Runtime decomposition:** shared host-side orchestration and tracing; engine-specific drivers/runtimes for RISC-V/NPU, Vortex/G100, and PTA. Do not promise framework or binary compatibility before a tested implementation exists.
- **Numerical contract:** per-operator supported types, rounding/saturation, accumulation semantics, accuracy tolerance, determinism, and cross-engine fallback rules.
- **Security and isolation:** initially single trusted workload unless MMU/IOMMU, memory isolation, reset, and fault containment are validated. No multi-tenant/security certification claim by default.

## 5. Workload and product requirements

Select at least one **portfolio workload suite** with: (a) an embedded batch-1 model for CPU/NPU, (b) a parallel SIMT workload for G100, and (c) a tensor workload suitable for PTA evaluation. Identify customer/design partner, model/version, representative inputs, preprocessing, quality reference, concurrency, memory footprint, and success thresholds. The PTA workload must include data loading, optical programming/calibration and output readback costs.

Use an appropriate public benchmark as a comparison point, not the product spec by itself. MLPerf Tiny provides embedded inference tasks and quality/latency/energy reporting; its suite is not a substitute for named customer models ([MLPerf Tiny](https://mlcommons.org/benchmarks/inference-tiny/)). For larger systems, benchmark rules and the full-system power boundary must be selected explicitly. Photonic-core-only operation counts must not be compared against full-board digital energy or latency as if boundaries match.

| Metric | Family rule | Numeric target |
|---|---|---|
| Correctness/quality | Every engine passes its own reference vectors; end-to-end model quality meets the design-partner threshold | Set per named workload |
| Latency | Report P50/P95/P99 end-to-end, including data transfer, setup, synchronization, programming and conversion costs | Set per workload and operating mode |
| Throughput | Report sustained completed jobs/sec or tokens/sec under defined batch/concurrency, not peak MACs alone | Set per workload |
| Energy | Report joules/job and sustained watts at both module and whole-board boundaries, including memory and required photonic support equipment | Set per workload |
| Reliability | Repeatable long-duration workload and recovery under defined thermal/power conditions; record all errors and resets | Ratify before pilot |
| Interoperability | Host API, buffer/ordering rules, and model placement behave consistently across module revisions | Versioned acceptance tests |

No numeric performance, power, cost, or availability target is asserted because no customer model, market, board BOM, or measured integrated result has been provided. Avoid marketing TOPS/W or latency figures until the setup, precision, dataflow, and system boundary are published.

## 6. Track-specific exit criteria

### GRX930 CPU/NPU

- Verify the actual four-core RTL/SoC configuration and coherency under simultaneous CPU, DMA, and NPU traffic.
- Run representative multi-tile models against golden output on the physical FPGA/board; collect timing closure, DDR behavior, module power and thermal data.
- Freeze the boot, model-load, memory ownership, command ABI, interrupts/timeouts, error recovery, debug and update paths.
- Close target-PDK area/timing/power feasibility using the actual SRAM, DDR controller/PHY, IO, clock/reset and DFT strategy.

### G100 digital GPU

- Convert the paper-scale architecture into a tiered implementable product spec: first demonstrator, scalable configuration, and optional flagship; delete or label aspirational capabilities until RTL and IP exist.
- Demonstrate selected kernels/workloads on FPGA/RTL with exact correctness, defined timing and resource reports. Keep SimX/RTL parity and FPGA system integration as separate evidence.
- Choose whether v1 is compute-only GPGPU or also graphics; define software/runtime/API compatibility narrowly and test it.
- Close memory bandwidth, host interface, power, die area, test and package feasibility before flagship configuration lock.

### PTA photonic accelerator

- Select the initial optical-compute mechanism and supported numeric representation; define optical versus electronic operations and output accuracy.
- Measure end-to-end data path: host/memory → scheduling/encoding → optical source/modulation → photonic compute → detection/readout/conversion → digital post-processing/result memory.
- Define laser source and service boundary, modulator/detector/readout electronics, calibration strategy, temperature drift handling, optical coupling/loss, test access, module package and software API.
- Start as a distinct board-attached module; consider GPU package integration only after a measured workload/system benefit and a credible thermal, memory, test and package plan.
- Establish repeatable per-workload quality, latency and joules/job with the laser, drivers, conversions, control, memory and calibration costs inside the declared boundary.

Public photonic-compute demonstrations and vendor products show hybrid optical/electronic systems and module/card form factors, but vendor claims are not independent validation. No universally adopted PTA compute interface or benchmark was identified in the reviewed sources. Relevant orientation: [review of photonic-electronic integrated circuits](https://arxiv.org/html/2403.14806v2), [MIT photonic processor demonstration](https://news.mit.edu/2024/photonic-processor-could-enable-ultrafast-ai-computations-1202), [Lightelligence PACE2 product description](https://www.lightelligence.ai/products/photon-computing/pace2), [Q.ANT product announcement](https://qant.com/press-releases/q-ant-launches-first-commercial-photonic-processor-for-energy-efficient-high-performance-computing-and-real-time-ai-applications/). These establish examples and integration questions, not GRXGPU performance or readiness.

## 7. Portfolio roadmap and funding gates

| Stage | Outcome | Exit evidence / decision |
|---|---|---|
| **0. Portfolio charter closure** | Named use case, customer, business, and system concept | Confirm four product-track definitions; decide whether CPU+NPU is one SoC and which “GRX930” name means; choose board users/workloads, host API, top-level memory strategy, numeric product targets, owners, funding and exclusions. |
| **1. Development PCB architecture** | Schematic-level platform and module boundaries | Measured bandwidth/latency budgets per link; connector/protocol selection; power/thermal budget; memory/coherency map; board test/bring-up plan; development board BOM and scope approved. |
| **2. Independent track demonstrators** | Each engine validated without cross-engine ambiguity | CPU/NPU board test; G100 FPGA/RTL workload test; PTA measured module/test fixture. Each has versioned source/artifacts and correctness, latency, power and thermal results. |
| **3. Common runtime integration** | Shared job/buffer/trace contract works on board | Reproducible workload dispatched to each eligible engine; transfer and synchronization costs measured; fallback and error behavior tested; no unsubstantiated zero-copy claims. |
| **4. Product architecture / PDK feasibility** | Each sellable SKU is physically and commercially feasible | Actual target PDK/IP rights, memory and PHY IP, package/OSAT, DFT, signoff tools, full-system PPA and cost/supply estimates confirmed per product. PTA packaging and laser supply separately closed. |
| **5. Silicon and system signoff** | Independent design freezes for each chip/module | Verification/coverage and DFT exit; multi-corner physical closure; foundry-qualified DRC/LVS/antenna, extraction, power integrity, thermal and manufacturing tests. One track cannot inherit another's signoff. |
| **6. Pilot and release** | Customer-validated, supply-supported product(s) | Bring-up and field workload pass; quality/performance/power targets met; pilot yield/test/unit economics, supplier capacity, software support and customer acceptance approved. |

Schedule and NRE remain **TBD** pending people, design maturity, supplier quotes, PDK rights and foundry/package route. The GRX930 readiness report's old target estimates and the G100 tapeout document's shuttle/area assumptions are not portfolio commitments; refresh them from current evidence and supplier offers.

## 8. Governance, owners, and risks

| Workstream | Accountable role | Blocking output |
|---|---|---|
| Portfolio/product | Product sponsor | Customer, markets, SKU ladder, business case, target requirements, exclusions |
| CPU/NPU | SoC/RTL lead | Four-core integration evidence, DDR/host path, firmware and inference results |
| G100 | GPU architecture/RTL lead | Implementable configuration, workload proof, graphics-vs-compute scope |
| PTA | Photonics lead | Optical architecture, measured end-to-end workload, calibration/package/service plan |
| Development PCB | Board/system lead | Interface and memory map, schematic, power/thermal, module test and debug plan |
| Software | Runtime/compiler lead | Common orchestration contract, per-engine drivers, supported models/operators |
| ASIC/operations | Physical design + sourcing + test | PDK and IP rights, signoff path, package/OSAT/test capacity, cost and schedule |

**Top portfolio risks:** (1) attempting four production chips before validating one usable system; (2) conflating the GRX930 NPU, Vortex G100 paper design, and PTA into a single maturity claim; (3) development-board bandwidth, memory ownership, power or cooling insufficient for simultaneous engines; (4) proprietary/unsourced memory, PHY, photonic, packaging or signoff IP discovered late; (5) software fragmentation across dissimilar engines; (6) incomparable energy/performance claims that omit data movement or PTA support equipment; (7) no customer, price, volume, NRE or re-spin reserve.

Mitigate by keeping modules replaceable, narrowing the first integrated board demo, instrumenting all data/power paths, freezing API versions, and requiring evidence gates per track. Do not take on multi-die production packaging or HBM solely to make the family architecture diagram look unified.

## 9. Immediate decisions for portfolio review

1. Approve **GRXGPU** as the umbrella and **GRX930 / G100 / PTA** as distinct tracks, or provide preferred naming.
2. Confirm whether the intended GRX930 device is a **quad-core RV64 + NPU on one SoC** or separate CPU/NPU components.
3. Choose the first system workload/customer and provide model, input, quality, latency, power and memory targets.
4. Confirm the development PCB's FPGA/ASIC status, exact devices, existing connectors, memory, measured bandwidth, power rails, and what has actually been run.
5. Decide whether G100 and PTA attach as replaceable modules to the first PCB, and identify available FPGA/photonic demonstrators and interface constraints.
6. Name owners and approve discovery/board-design resources; provide NRE, sample-volume and re-spin budget boundaries.
7. Decide the boundary between public family charter and confidential foundry/PDK/IP data; do not put restricted PDK details into a public repository.

## 10. Production execution plan

The staged portfolio roadmap above is expanded into accountable SKU-level evidence gates, a 4–6 week decision sprint, and release criteria in the [GRXGPU Production Readiness Plan](grxgpu_production_plan.md). Use that plan to coordinate production work; it does not authorize tapeout or assert any product is already production-ready.

## 11. Review outcome

**Recommended decision:** approve the four-track GRXGPU portfolio and a modular shared development-board architecture as the program direction, with the CPU/NPU SoC as the first boot/control anchor. Keep G100 and PTA independently attachable and independently gated. Authorize system/board interface definition and evidence collection next; do **not** yet authorize a production ASIC tapeout or claim a finished commercial GPU family.

**Approver:** ____________________  **Date:** __________
**Product sponsor:** ____________________  **System lead:** ____________________

## References

- [GRX930 v1 product charter](grx930_product_charter.md)
- [GRX930 tapeout readiness report](../grx930/doc/grx930_tapeout_readiness.md)
- [Vortex G100 architecture design](designs/gpu_chip_design.md)
- [GRX930 production compute silicon plan](grx930_production_gpu_plan.md)
- [GRXGPU production readiness plan](grxgpu_production_plan.md)
- [MLPerf Tiny benchmark](https://mlcommons.org/benchmarks/inference-tiny/)
- [Photonic-electronic integration review](https://arxiv.org/html/2403.14806v2)
- [IEEE P3112 status (EDA/photonic design formats; active PAR, not a published PTA interface)](https://standards.ieee.org/ieee/3112/10794/)
