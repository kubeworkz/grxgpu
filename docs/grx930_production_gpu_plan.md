# GRX930 Production Compute Silicon Plan

**Purpose:** turn the GRX930 work into a credible first production silicon program, with explicit evidence gates between FPGA validation, ASIC tapeout, and volume product. This is a planning baseline, not a tapeout commitment or an assertion that the design is already production-ready.

## Executive recommendation

Treat the first product as an **edge/inference accelerator (NPU)** built around the GRX930 systolic array, unless a named customer and workload justify a broader GPU. The current GRX930 readiness report describes an 8×8 systolic NPU, RV64 core, DMA and UART; it reports 18 GEMM cases passing in Verilator, while multi-core validation, FPGA timing/board results, large multi-tile GEMM and ASIC synthesis are still listed as gaps ([GRX930 readiness report](../grx930/doc/grx930_tapeout_readiness.md)). That is a valuable starting point, but it is not yet evidence for a general-purpose, graphics-capable GPU product.

Do not make the paper-scale G100 target the first chip. Its own architecture document labels it a design target, and the older tapeout plan's large 128-core/HBM assumptions need a fresh feasibility review. A small, testable first ASIC is the lower-risk way to establish silicon, packaging, manufacturing-test and software capability before deciding whether to scale out.

The user reports that a PDK and FPGA are now ready. Accept those as program inputs, but close Gate 1 below with their exact identity and reproducible evidence. The checked-in readiness report still says no FPGA bitstream or GRX930 ASIC synthesis report; the GRX930 folder in this checkout contains documentation, firmware and a Verilator makefile, not the referenced `c930/rtl` source tree. Refresh the record before treating those older status statements as current.

## Product decisions to make first

A short product charter must answer these before RTL is frozen:

1. **Product category:** embedded inference accelerator, PCIe accelerator card, or general-purpose graphics/GPGPU. Recommendation: start with inference; graphics and a full CUDA-like platform are a separate scope.
2. **Named workload/customer:** model(s), batch sizes, precisions, operator coverage, latency/throughput target, and what runs on the CPU versus NPU.
3. **Product envelope:** target market, unit cost/volume, power and thermal limits, memory capacity/bandwidth, form factor, and acceptable software/OS support.
4. **Host and memory interfaces:** select actual controller/PHY IP and package early. For a first edge product, prefer a proven external DDR solution over HBM unless the workload requires HBM bandwidth and the team has a funded advanced-package path. A host link (UART for bring-up only, or a production interface such as PCIe) must be an explicit product choice.
5. **Process and manufacturing route:** exact foundry, node, PDK revision/rights, shuttle versus dedicated run, package/OSAT, test provider, and funding owner.
6. **First-silicon scope:** choose the smallest die that can demonstrate the customer-critical path: boot → host command → DMA/memory → NPU GEMM → result readback. Decide explicitly whether the first revision is one core or multi-core; do not assume the 4-core instances are validated just because they elaborate.

If the goal is a discrete gaming/graphics GPU, stop at this gate and create a separate product charter for graphics pipeline completeness, display output, memory bandwidth, host interface, driver/API compatibility, board design and ecosystem. The GRX930 NPU plan does not deliver those by implication.

## Phased roadmap and exit gates

Schedule ranges are placeholders for planning only. Re-estimate after the product charter, staffing, PDK access and foundry slot are confirmed. A re-spin is a planned risk, not an exceptional event.

| Phase | Indicative window | Main outputs | Exit gate (measurable evidence) |
|---|---:|---|---|
| **0. Product charter** | 2–4 weeks | Product requirements, first workload suite, business case, interface and SKU decisions | Named workload/customer; quantitative latency, throughput, power, memory, cost and volume targets; signed decision on NPU vs GPU and first-chip scope. |
| **1. Baseline and FPGA proof** | 2–6 weeks | Reproducible source/build manifest; board image; FPGA bring-up and workload report | Exact RTL commit, board/FPGA part, constraints, tool versions and PDK identity recorded. Automated boot/DMA/GEMM/result checks pass on physical FPGA at the target operating point. Multi-tile and error/recovery cases pass; timing and power are measured, not inferred from simulation. |
| **2. Foundry, IP and package feasibility** | 2–8 weeks, parallel | Foundry/IP matrix; package and memory interface plan; cost/schedule and capacity quotes | Written confirmation of rights and availability for the exact PDK/revision, libraries and PVT corners, extraction and signoff decks, SRAM compiler/macros, IO/ESD/pad cells, PLL/clock/reset strategy, required PHY/controller IP, package/assembly and production test. No critical block remains “assumed available.” |
| **3. Product RTL and verification hardening** | 2–5 months | Frozen v1 architecture; integrated RTL; verification and DFT plans | Product-critical regressions pass on reference simulation and RTL; no unresolved critical functional issues. Multi-core/coherency behavior is proven if multi-core is in scope. Reset, backpressure, DMA bounds, malformed commands, ECC/error response and recovery are tested. Assertions/formal checks cover key protocols; coverage closure is reviewed. Scan/JTAG, SRAM BIST/repair strategy, observability and production test access are designed in. |
| **4. Target-PDK feasibility and PPA** | 2–4 months, iterative | Synthesized and placed critical blocks; floorplan; power/area/timing model | Actual target PDK and real SRAM/PHY abstracts are used. Reports show area, congestion, timing at agreed clocks/corners, workload-based power, SRAM inventory and package/thermal feasibility. All product targets have documented margin and a credible die-size estimate. Black-box logic and unmodeled IO/memory costs are explicitly accounted for. If it misses, reduce scope or revise targets before proceeding. |
| **5. Full physical implementation and signoff** | 3–6+ months | Routed design, extracted netlist, signoff package and manufacturing test collateral | RTL/netlist freeze; MCMM setup/hold closure at all agreed corners; extracted timing and signal-integrity review; power integrity/IR-drop and EM checks; thermal review; foundry-deck DRC/LVS and antenna checks clean or formally waived by the foundry; scan/MBIST and test vectors verified; gate-level/DFT regression passes; final GDS and checksums archived. Independent signoff review approves tapeout. |
| **6. First silicon and bring-up** | Foundry/package dependent | A0 devices, bring-up board, characterization and errata log | Pre-written bring-up sequence works through JTAG/recovery boot; memory and DMA diagnostics pass; NPU output matches golden vectors over the full precision/shape battery; sustained workload meets the charter's performance/power limits; thermal, reset, clock and stress tests pass. Failures are triaged into RTL, timing, package, process or software root causes. Decide re-spin versus next revision from measured data. |
| **7. Pilot and production qualification** | Market and supplier dependent | Production test flow, pilot lots, qualified software/board, support and supply plan | Agreed qualification matrix and sample sizes pass for the target market; yield, test time, failure analysis and unit economics meet predeclared targets; OSAT/foundry capacity and long-term supply are committed; board/firmware/driver updates and customer acceptance are complete. Only then call the product production-ready. |

## Non-negotiable technical workstreams

### Verification and design maturity

- Promote the FPGA regression into a versioned product acceptance suite; keep golden data and expected tolerances reviewed.
- Add multi-tile K=64/128/256+ workloads, concurrent DMA/CPU traffic, repeated launches, maximum transaction sizes, stalls, reset during/after operation, and invalid-command/error injection.
- For multi-core scope, prove cache/DMA coherency and synchronization under concurrent load. The current report explicitly says this is not yet established at 4-core scale.
- Use formal assertions for ready/valid, AXI, cache invalidation, FIFO bounds, barrier and reset invariants. Formal is complementary to simulation, not a claim of whole-chip equivalence.
- Establish reproducible build/test artifacts and a change-control policy before RTL freeze. No unreviewed feature work after the freeze; fixes require impact analysis and retest.

### ASIC implementation and signoff

A PDK being available is not the same as a production flow being ready. Confirm licensed use, correct corner models, LEF/Liberty/RC data, foundry-qualified SRAM macros, IO and ESD, clocking, reset, test cells, DRC/LVS/antenna decks, extraction, package rules and a supported signoff path. The Vortex synthesis guide documents flows for NanGate, ASAP7 and SAED14; that does not prove the GRX930 design is integrated with the claimed production PDK or that its flow produces foundry-accepted GDS ([synthesis analysis](synthesis_analysis.md)).

Use real SRAM macros in implementation estimates. DFF-based memory estimates and open educational libraries are useful for architecture experiments but cannot stand in for the selected process's area, timing, power, yield or signoff models. Include scan, MBIST, debug access, clock/reset test, pad ring, decaps, seal ring, IO, PHYs and package escape in the full die/package budget.

### Software and product integration

A production accelerator needs more than an RTL compute block: a stable host command/memory ABI, production boot/update/recovery path, runtime/driver, compiler/operator support for target workloads, diagnostics, performance counters, error reporting, versioning and compatibility policy. Decide what unsupported operators do (CPU fallback, compiler error, or library implementation) and test it. UART is suitable for lab bring-up, not automatically for the shipped host interface.

### Memory, package and external links

Treat memory and package selection as architecture, not a late physical-design detail. JEDEC's HBM3 standard describes a tightly coupled distributed interface; the actual HBM3E stack/speed grade and availability must be confirmed with the chosen supplier ([JEDEC HBM3](https://www.jedec.org/standards-documents/docs/jesd238b01), [Micron HBM3E product information](https://www.micron.com/products/memory/hbm/hbm3e)). TSMC's CoWoS description illustrates the package integration dependency for HBM ([TSMC CoWoS](https://3dfabric.tsmc.com/english/dedicatedFoundry/technology/cowos.htm)). Do not put HBM or a chiplet link on v1 without a sourced PHY/IP, package budget, test strategy and funding. UCIe is relevant only if the chosen architecture actually uses die-to-die chiplets ([UCIe specifications](https://www.uciexpress.org/specifications)).

If PCIe is selected, obtain the current controlled specification and compliance requirements from PCI-SIG early, then budget electrical, protocol, board-channel and interoperability validation. Public PCI-SIG material notes that preliminary PCIe 6.x testing is not the same as Integrators List eligibility; verify the current official path before setting a certification milestone ([PCIe 6.0 specification](https://pcisig.com/pci-express-6.0-specification), [PCI-SIG specifications](https://pcisig.com/specifications)).

## Risk register (initial)

| Risk | Why it matters | Mitigation / stop condition |
|---|---|---|
| Product scope expands from NPU to flagship GPU | Graphics, HBM, high-speed host links and software substantially change the design and organization | Freeze a narrow first SKU and workload. Treat broader GPU as a separately funded follow-on. |
| PDK access mistaken for tapeout authorization or signoff readiness | PDK may lack commercial rights, required IP, qualified SRAM, complete decks or a supported manufacturing route | Close Phase 2 using written foundry/EDA/IP/OSAT confirmations before committing architecture or dates. |
| FPGA claim is based only on bitstream generation | Does not prove board operation, real DDR behavior, target clock, power or product workload | Require an automated physical-board acceptance report with measured clock, power and repeatable workloads. |
| Multi-core/DMA correctness is under-tested | Coherency and contention bugs can silently corrupt results | Keep v1 single-core until the multi-core gate is actually passed; add stress and fault tests. |
| PPA estimates exclude memory, PHY, IO, DFT or package | Can invalidate area, cost, power and schedule after RTL is frozen | Use target-PDK macros and complete die/package budget at Phase 4; no tapeout approval from synthesis-only estimates. |
| First silicon fails or misses performance | A0 is a learning vehicle; re-spin risk is real | Add scan/JTAG/trace, recovery boot, test modes, characterization vectors and budget for at least one corrective revision. |
| Software is not product-ready | Correct silicon can still fail customer workloads or deployment | Validate compiler/runtime/operator coverage and update/diagnostic paths against the named workload before pilot. |

## Decision package for the next review

Bring a one-page answer to each of these, with owner and evidence:

- What exact PDK/foundry, revision, node, license scope and tapeout route do we have?
- Which FPGA board/part is available, and what workload has actually run on it at what clock and measured power?
- Is the first product an edge NPU, PCIe accelerator, or graphics/GPGPU—and which customer workload selects it?
- What is v1: one core or multiple, external memory type/capacity, host interface, package and power target?
- Which controller/PHY, SRAM, clock, IO, ESD, DFT, package and signoff IP are already contracted versus merely planned?
- What are the funded NRE, engineering team, foundry slot, sample count and re-spin reserve?
- Who has authority to approve RTL freeze and tapeout, and what objective results block either decision?

## External standards and manufacturing references

- [JEDEC JESD47 — stress-test-driven qualification of integrated circuits](https://www.jedec.org/standards-documents/docs/jesd-47g)
- [GlobalFoundries GlobalShuttle MPW program](https://gf.com/manufacturing/services/multi-project-wafer-program/)
- [EUROPRACTICE fabrication services](https://europractice-ic.com/services/fabrication/)

These are starting references, not confirmation that a particular foundry, shuttle, PDK, package or qualification route is available to this program. Confirm the actual terms with the selected suppliers.
