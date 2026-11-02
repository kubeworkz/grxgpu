# G100 Production Baseline — One Configuration, Its Arithmetic, and the Gaps That Remain

**Status:** Proposal. It reconciles the numbers and proposes the first tapeout
configuration. It does not approve a SKU, a customer, a budget, a supplier, a
process, or a tapeout.
**Date:** 2026-10-31
**Scope:** [G100 architecture](../designs/gpu_chip_design.md),
[G100 tapeout plan](../grxgpu_g100_tapeout_plan.md),
[G100 product brief](../grxgpu_g100_product_brief.md),
[G100 evidence manifest](../grxgpu_g100_evidence_manifest.md), and the G100 half
of [the PTA host path](pta_chiplet_host_path.md).
**What it answers:** the product brief's open action "reconcile G100
tapeout-plan area/memory estimates and classify claims", and the tapeout plan's
§7 questions where the answer is an engineering decision rather than a supplier
fact.

---

## 1. Summary

1. **Three machines are called G100.** The architecture specification, the
   tapeout plan, and the discovery run describe 2,048, 16 and 32 threads per SM
   respectively. They cannot share an area estimate or a tapeout schedule until
   one is chosen.
2. **The ~72 mm² die is the small one.** Counted with its 512 KB register
   file, it is internally consistent for a 128-core machine at the
   repository-default 4 warps × 4 threads — 16 threads per SM — with 6 MB of
   SRAM and no L2. It is not the architecture specification's 128-SM,
   2,048-thread flagship.
3. **The flagship's memory alone is up to 336 mm² at 28 nm.** That is 4.7× the
   tapeout plan's entire die, before logic, pads, or PHY. A 28 nm version would
   need a full reticle and the advanced-node PHYs the design assumes; it is not
   a shuttle part, and the flagship remains an advanced-node target.
4. **The same 6 MB is costed four ways.** The plan's own sections give ~13 mm²,
   ~25 mm², ~50 mm² and 100 mm² for the same six megabytes. Only the first is
   consistent with the 0.25 µm²/bit 6T SRAM assumption the die estimate uses.
5. **The tapeout plan has no host or DRAM interface.** A die with no PCIe, no
   DDR and no HBM can be brought up over JTAG and run from its own SRAM, but it
   is a test chip, not the product the plan's first-silicon table implies.
6. **The PTA chiplet has no G100 port, and this baseline does not add one.**
   The first board attaches the PTA to the GRX930 host. The later in-package
   arrangement needs a die-to-die port whose rate is a significant fraction of
   the die edge, not a register window.

The proposal is **G100-T0**: one cluster × 16 cores, the only configuration
with a measured logic area and a working RTL path, at ~10.8 mm² with ECC, pads
and a 256 KB test SRAM.
It is a bring-up die. A product die needs a host interface and a wider SM, and
neither exists in RTL today.

---

## 2. Three designs, one name

The configuration values below are resolved from `VX_config.toml` with
`ci/gen_config.py`, not inferred from prose.

| | Architecture spec | Tapeout plan | Discovery run |
|---|---|---|---|
| Clusters × cores | 8 × 16 = 128 | 8 × 16 = 128 | 1 × 4 |
| Warps per SM | 64 | 4 | 4 |
| Threads per warp (SIMD width) | 32 | 4 | 8 |
| Resident threads per SM | 2,048 | 16 | 32 |
| Issue width | 4 | 4 | 4 |
| Architectural registers per thread | 32 int + 32 FP | 64 | 64 |
| Register file per SM | 256 KB specified, 512 KB as the RTL sizes it | 4 KB | 8 KB |
| L1 / shared per SM | 256 KB unified carve-out | 16 KB LMEM + 16 KB ICache + 16 KB DCache | same |
| L2 | 8 MB per cluster, 64 MB total | none | 1 MB total |
| On-chip memory, all SMs | 160 MB | 6.6 MB | ~1.2 MB |
| Die area | not estimated | 72 mm² at 28 nm | none |

**Why the tapeout plan is the 4 × 4 machine.** The plan's 434,146 µm² core area
comes from the blackbox cluster flow in `syn/synth_blackbox_cluster.sh`, which
does not override `VX_CFG_NUM_WARPS` or `VX_CFG_NUM_THREADS`; both take the
`VX_config.toml` defaults of 4. `syn/run_yosys_synthesis.sh` likewise overrides
only the cluster and core counts. The plan's own text never states the warps and
threads behind the number, which is how the two machines came to share an area
table.

**The register file is 512 KB, not 256 KB, in this RTL.** `VX_gpu_pkg.sv` sets
`REG_TYPES = 1 + VX_CFG_EXT_F_ENABLED` and `NUM_REGS = REG_TYPES × 32`. With F
enabled, each thread owns 64 architectural registers, so 2,048 threads need
131,072 registers (512 KB), not the 65,536 (256 KB) the architecture table
states. The 256 KB figure is what a 32-register-per-thread file would be. A
production baseline must decide whether integer and floating-point registers
share one file or split; today they split, and the table understates the RTL.

---

## 3. What is in the memory budget

| Design | Caches and scratchpad | Register file | L2 | Graphics caches | Total |
|---|---|---|---|---|---|
| Architecture | 32 MB L1/shared | 32 MB (doc) / 64 MB (RTL) | 64 MB | — | 128–160 MB |
| Tapeout plan | 6 MB (LMEM + ICache + DCache) | 512 KB | none | 60 KB | 6.6 MB |
| Discovery | 192 KB | 32 KB | 1 MB | — | ~1.2 MB |
| **G100-T0** | **768 KB** | **64 KB** | none | none | **832 KB** |

Two omissions mattered. The tapeout plan's "Total SRAM: ~6.1 MB" counted the
three per-core arrays and the graphics caches but not the register file; 512 KB
is small beside six megabytes, and it was still a missing row. Its §1.2 and §2.2
now carry it, and their totals read 6.5 MB embedded and ~6.6 MB overall. Its
graphics caches are counted although `VX_CFG_EXT_TEX_ENABLE`,
`VX_CFG_EXT_RASTER_ENABLE`, `VX_CFG_EXT_OM_ENABLE` and `VX_CFG_EXT_RTU_ENABLE`
are all false in the default configuration, and the sponsor-approved discovery
scope is compute-only. A compute-only baseline has no reason to carry 60 KB of
graphics caches.

---

## 4. The same 6 MB, four times

The tapeout plan quotes four different areas for its six megabytes. They are
not four estimates of one quantity; they use different storage densities.

| Where | What it says | Implied density | Area for 6 MB |
|---|---|---|---|
| §2.1, "all custom 6T SRAM" | ~13 mm² | 0.25 µm²/bit | 12.6 mm² |
| §2.1, "hybrid" | ~25 mm² | ~0.50 µm²/bit | 25.2 mm² |
| §2.1, "all ORRAM" | ~50 mm² | 1.04 µm²/bit | 52.3 mm² |
| §8.2, "6 MB total" | 100 mm² | 1.99 µm²/bit | 100.2 mm² |

The §2.3 die estimate uses the first, and it should: the large arrays are
foundry 6T macros. The hybrid row is then ~13 mm², not 25, because 6 MB of 6T
plus 60 KB of ORRAM is 12.6 + 0.5. The §8.2 figure is twice even the plan's own
ORRAM density (960 Kbit/mm² at 28 nm, which is 1.04 µm²/bit). It should be
deleted or marked as a 130 nm measurement, not a 28 nm estimate.

The adopted model for this proposal:

- foundry 6T SRAM: **0.25 µm²/bit** (the plan's own assumption; a 0.15 µm²/bit
  dense bitcell would reduce every SRAM figure below by 40%);
- DFF-based ORRAM: **1.04 µm²/bit** at 28 nm;
- logic: Nangate45 area × **0.39** for the 45 → 28 nm scaling the plan already
  uses;
- no PHY, pad ring, clock tree, power grid or routing overhead. Those are added
  separately, and none of the plan's figures include them.

---

## 5. What each design costs at 28 nm

Memory is calculated from the bit counts in §3; logic from the one measured
cluster.

| Design | Logic @28 nm | Memory @28 nm | Total | 4 mm² tiles |
|---|---|---|---|---|
| G100-T0 (16 cores, 4 × 4) | 7.3 mm² | 1.7 mm² | **~9.0 mm²** | 3 |
| Tapeout plan (128 cores, 4 × 4) | 58.2 mm² | 13.8 mm² | **~72 mm²** | 18 |
| Architecture (128 SMs, 64 × 32) | ≥58 mm² lower bound | 336 mm² | **≥394 mm²** | 99 |

The middle row reproduces the plan's die: 71 mm² as published, 72 once its
512 KB register file is counted. That is the finding, not a correction: the
plan is right about its own machine and wrong to call that machine the
architecture specification's G100. The bottom row uses only the
memory, plus the plan's scaled logic as a floor; the flagship SM is eight times
wider than the measured core, so real logic is larger, not smaller.

**Shuttle arithmetic.** At the plan's own $40K–$60K per 4 mm² tile:

| Design | Tiles | First shuttle | Note |
|---|---|---|---|
| G100-T0 | 3 | $120K–$180K | One tile is too small; three carry the die plus scribe |
| Tapeout plan | 18 | $720K–$1.08M | Not the $40K–$60K budget in §3.3 |
| Architecture | 99 | $4.0M–$5.9M | A full-reticle share, not a shuttle tile |

These are unit arithmetic on a historical price, not a quote. The point is the
order of magnitude: the plan's $50K–$100K budget buys one or two 4 mm² tiles,
and its own die is eighteen of them.

**Two smaller contradictions in the same section.** The "single 16-core cluster
(~20 mm² @28 nm incl. SRAM)" sentence is the unscaled 45 nm figure
(18.64 + 1.57 = 20.2); at 28 nm the same cluster is ~8.8 mm². And the "22 mm²
at 28 nm can handle 15–20 W" in §5.1 and §7 belongs to neither die: §2.3 says
72 mm², and 22 mm² is not a configuration in the document.

---

## 6. G100-T0: the proposed first tapeout

The first silicon should be the only configuration that has both a measured
logic area and a working RTL path. That is the 16-core, 4 × 4 cluster the
tapeout plan already synthesizes and the discovery runs already exercise at
1 × 4.

| Parameter | Value | Why |
|---|---|---|
| Clusters × cores | 1 × 16 | The measured cluster; no inter-cluster fabric |
| Socket size | 1 | Matches `syn/` and the blackbox flow |
| Warps × threads | 4 × 4 | The measured core; changing either invalidates 434K µm² |
| Issue width / SIMD | 4 / 4 | Resolved from the defaults |
| TCU | 4 blocks × 4 lanes, FP16 + WGMMA | The implemented tensor path |
| DXA | 2 cores | Required by the double-buffered WGMMA path |
| LMEM / ICache / DCache | 16 KB / 16 KB / 16 KB per core | The measured inventory |
| L2 | disabled | Not in the measured area or the RTL path |
| Graphics | disabled | Compute-only discovery scope |
| ECC | SECDED 64+8 on all three arrays | Production SRAM does not ship without it |
| Clock | 400 MHz target, 800 MHz stretch | 400 is the platform model; neither is closed by STA |
| Power envelope | 10 W | Package and thermal budget; no activity-based estimate exists |
| Host interface | none; JTAG bring-up | No host RTL or PHY exists (§7) |
| Die | ~10.8 mm² with ECC, pads, clock tree, 256 KB test SRAM | 9.0 mm² + 0.2 ECC + 0.6 test SRAM + ~1 mm² overhead |
| Package | QFN-128 | JTAG, clock, reset and a debug bus; the wide memory port is not bonded |

T0 adds a 256 KB test SRAM at the cache hierarchy's memory side and a JTAG
bridge to it. Without one, the DXA has no source for tiles and the TCU can only
run from what the debugger writes into LMEM. The repository's resolved
configuration exposes no top-level memory port — `VX_MEM_PORTS` resolves to 0
with L3 disabled — so this needs an explicit attachment point: new RTL, or a
corrected port expression, decided before layout. The 9.0 mm² arithmetic in §5
excludes the test SRAM; the die row above includes it. The manufacturing-test
and bring-up items are in
[the T0 tapeout checklist](../grxgpu_g100_t0_tapeout_checklist.md); the TAP, DM
and SBA bridge are specified in
[the T0 JTAG specification](g100_t0_jtag_debug.md).

What T0 proves: the 16-core cluster boots, the TCU and DXA run a GEMM from
LMEM, scan and MBIST pass, ECC reports and corrects, and the RTL matches SimX
at a scale larger than the discovery runs. What it does not prove: a product
workload, a host path, DRAM, graphics, or any frequency above the one STA
closes.

The 128-core, 4 × 4 configuration is a second candidate at ~72 mm² and 18
tiles. It has eight times the cores and no additional evidence behind it; its
cluster fabric was synthesized, but a 128-core die has never been placed,
routed or timed. T0 is the cheaper way to find out whether the flow closes
before spending eighteen tiles on it.

---

## 7. Gaps the arithmetic does not close

Each row is a production-design gap, not a planning inconvenience. "Closed"
means this proposal settles the engineering question; it does not mean the
evidence exists.

| ID | Gap | State after this proposal | Closes when |
|---|---|---|---|
| P01 | Three configurations share the name | Reconciled in §2; T0 proposed in §6 | Sponsor ratifies one |
| P02 | Memory inventory and die arithmetic | Closed in §3–§5 | — |
| P03 | MPW tile and budget | Closed in §5: 18 tiles, not one | Supplier quote for the actual tile shape |
| P04 | SRAM strategy | 6T for the large arrays, ORRAM for the 60 KB only if graphics returns | PDK confirms the compiler and macros |
| P05 | Clock target | 400 MHz for T0, 800 MHz stretch | Target-library STA on the placed netlist |
| P06 | Power and thermal | 10 W envelope only; no switching activity | VCD-based estimate on the target library |
| P07 | Host interface | Absent from RTL and the plan; T0 is JTAG-only | PCIe controller + PHY selected and integrated |
| P08 | DRAM interface | Absent; T0 runs from SRAM | DDR/LPDDR controller + PHY selected |
| P09 | DFT: scan, compression, MBIST, JTAG | Scan/MBIST requirements in §8; the TAP, DM and SBA are specified in [the T0 JTAG spec](g100_t0_jtag_debug.md); no RTL | Scan insertion, MBIST RTL and JTAG RTL land |
| P10 | ECC and RAS | SECDED specified for T0; no RTL | ECC RTL + error-reporting registers |
| P11 | Floorplan and package | No floorplan; QFN assumed | Placed die and pin list |
| P12 | PTA die-to-die port | Excluded from T0 (§9) | A G100 SKU with a D2D PHY, or the module stays host-attached |
| P13 | PDK rights, foundry slot, cost | Not assessed | Controlled supplier evidence |
| P14 | Evidence review | Discovery runs still `run-passed-pending-review` | Independent reproduction |

Three documentation errors in the tapeout plan are corrected alongside this
record. Its §1.1 said "Barriers 128/core"; `VX_CFG_NUM_BARRIERS` is 8, the
barrier unit is cluster-wide (`VX_gbar_unit`, one arrival bit per core), and
`VX_CFG_MAX_BAR_EVENTS` is 32 in-flight events per core. Neither §1.2 nor §2.2
included the register file; both now carry its 512 KB and the corrected totals.
Its graphics-cache inventory listed three of the four arrays —
`VX_CFG_RTCACHE_SIZE` was missing — and reconciled at three different totals:
52 KB of rows, 32 KB in prose, 84 KB stated. It now lists all four and totals
60 KB, which is what its ~0.5 mm² allowance always implied.

---

## 8. Testing and reliability for T0

The production documents describe functional validation but no manufacturing
test. A first tapeout needs four things before layout:

- **Scan.** Every state element in the 16 cores and fabric on scan chains, with
  compression. The cluster is ~9.9M cells; uncompressed chains make test time a
  packaging problem, not a tester problem.
- **MBIST.** March C- over the 48 arrays (16 cores × 3). At 100 MHz and 16K
  words the run is tens of milliseconds per array; the requirement is the
  controller and the repair decision, not the time.
- **JTAG.** A TAP with IDCODE, boundary scan and access to the debug module, so
  a blank die can be clocked, reset and read before any code runs.
- **ECC.** SECDED on each 64-bit word: eight check bits, 12.5% area overhead,
  ~0.2 mm² on T0. A correctable error increments a counter; an uncorrectable
  one raises a fault the debug path can read. Without this, first silicon cannot
  distinguish a soft error from a logic bug.

None of these exists in the RTL today. They are the difference between a design
that can be tested and one that can only be simulated.

---

## 9. The PTA chiplet on this baseline

G100-T0 has no die-to-die port, and the first board does not need one: the
[reconciliation](first_board_reconciliation.md) §3.1–§3.2 put the PTA on the
GRX930 host as a CXL 2.0 Type-1 device and left the in-package arrangement to
the later board.

The later board's decision B4 asks for a different G100. It needs:

1. a D2D controller and PHY on the G100 edge;
2. enumeration and a register window for the PTA (the host-path proposal's DCR
   range at `0x400`, stride `0x100`, command `0x0D` and capability bit 27 are
   still unassigned; the DCR map ends at `0x280`);
3. a copy-engine path from device memory to the chiplet, which is DXA plus a
   new port, not DXA alone;
4. a completion and fault path back through the command processor.

The link is not a rounding error. The board plan's model for a 4096 × 4096
layer at batch 64 needs **130 GB/s in and 8 GB/s out**. At 32 GT/s and 16 lanes,
one UCIe module carries 64 GB/s per direction, so the inbound path is three
modules — roughly 192 GB/s — before any margin. At 16 GT/s it is five. That is
a wide edge, a package with a bridge, and a PHY that no 28 nm library in this
record provides. Announced UCIe PHYs target advanced nodes; the 28 nm baseline
and the B4 arrangement are in tension, and a 28 nm G100 cannot resolve it by
adding a register window.

Two consequences for the chiplet track:

- **Keep the PTA host-attached for the first board**, as ruled. The G100 side
  needs nothing, and the chiplet's host path is the GRX930's CXL.
- **The chiplet's next buildable artifact is the 128 × 64 stand-in, not a G100
  port.** The emulated tile exists at the c930's 8 × 8 and the twin exists in C
  at 128 × 64; the RTL at the working geometry is still unowned
  ([reconciliation](first_board_reconciliation.md) §3.5). Building it behind
  the existing register map exercises discovery, the job contract, completion
  and faults without inventing a die-to-die interface that the 28 nm baseline
  cannot carry.

---

## 10. What this changes in the existing documents

The same change adds a revision note to the tapeout plan and the architecture
specification, and closes the product brief's reconciliation action. The
substantive edits:

| Document | Edit |
|---|---|
| [Tapeout plan](../grxgpu_g100_tapeout_plan.md) | Header note: the area/memory/cost figures are September 2026 planning estimates for a 4 × 4 machine, not the architecture specification; use this proposal for the inventory |
| [Architecture](../designs/gpu_chip_design.md) | §2 note: the table is a paper target for an advanced node; its on-chip memory alone is up to 336 mm² at 28 nm and is not the tapeout plan's die |
| [Product brief](../grxgpu_g100_product_brief.md) | §6 reconciliation row: arithmetic closed, configuration ratification open |
| This proposal | Adopted as the reconciliation record for P01–P03 |

The historical numbers stay in place. Rewriting a September estimate to match
an October finding would erase the evidence that the two machines were ever
confused, and the next reader would have no way to tell which figures were
measured and which were inherited.

---

## 11. What this does not decide

- **A SKU, a customer, or a market.** T0 is an engineering die; it is not
  sellable and is not proposed as one.
- **Funding or a foundry slot.** The tile arithmetic shows what a shuttle
  costs; it does not authorize one.
- **A process.** 28 nm is the plan's assumption. The flagship needs an advanced
  node, and no node has been selected.
- **A host interface.** Choosing PCIe Gen3 x8 and DDR4-2400 for a product die
  is a separate proposal with its own RTL, PHY and area.
- **The PTA's compute mechanism.** Nothing here changes the optical/electronic
  boundary or the error budget.

The next decision is the sponsor's: ratify T0 as the first tapeout, or fund the
host interface and the wider SM that a product die needs. The arithmetic says
those are different programs, and the current documents describe both under one
name.
