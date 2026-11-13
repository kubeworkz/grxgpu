# G100-T0 Tapeout Checklist

**Status:** Working checklist for the proposed G100-T0 die. No item is complete
until its evidence is linked and reviewed; a plan, a simulation at another
configuration, or a vendor claim is not evidence.
**Date:** 2026-11-01
**Baseline:** [G100 production baseline](proposals/g100_production_baseline.md)
§6 — one cluster × 16 cores, 4 warps × 4 threads, 16 KB LMEM/ICache/DCache per
core, no L2, SECDED ECC, 256 KB test SRAM, 400 MHz, 10 W, ~10.8 mm², QFN-128.
**Scope:** scan, MBIST, ECC, floorplan, package, JTAG bring-up. The six areas
are independent workstreams but share one signoff; an unchecked item in any of
them blocks the tapeout package.

Every checked item records the RTL revision, tool name and version, the artifact
path and its hash, the reviewer, and the date. The roles below are roles, not
assignments, as in the [engineering task list](grxgpu_engineering_task_list.md).

---

## 0. Entry conditions

- [ ] **Configuration frozen.** The exact `CONFIGS` string and the resolved
  configuration are recorded; the die is built from the frozen revision only.
- [ ] **RTL freeze tag.** No RTL change after freeze without a change record and
  an affected-item regression.
- [ ] **PDK and library revision recorded.** Process, library corner, SRAM
  macros, IO cells and DRC/LVS decks are identified in controlled storage.
  *Currently unselected — this alone blocks every item below.*
- [ ] **Clock and voltage corners listed.** 400 MHz target, slow/typical/fast
  corners, voltage tolerance, temperature range.
- [ ] **Package decision recorded.** Memory ports not bonded (QFN-128) versus
  bonded (BGA); the floorplan and pin list depend on it.
- [ ] **Test-mode budget.** Test time, coverage targets and the tester interface
  are agreed before ATPG, not after.
- [ ] **Named reviewers.** DFT/test, physical design, package and bring-up
  reviewers are named; none is the author of the item they review.

---

## 1. Scan and ATPG

*Owner role: DFT/test lead.*

- [ ] **Scannable inventory.** Every state element in the 16 cores and cluster
  fabric is scannable except the RAM macros, clock-gating cells and any
  asynchronous reset synchronizers; the exceptions are listed with a reason.
- [ ] **Test-mode ports.** `scan_en`, `scan_clk`, `scan_rst` and the test-mode
  select are top-level ports; functional clock and reset are muxed only in test
  mode, and the mux is proven in gate-level simulation.
- [ ] **Scan insertion.** Chains inserted on the post-synthesis netlist, with
  chain count and lengths balanced; lockup latches on any mixed-clock boundary.
- [ ] **Chain integrity.** A flush test shifts a known pattern through every
  chain and compares; this runs before ATPG and on the first silicon.
- [ ] **Stuck-at ATPG.** Target ≥ 95% coverage, or a written, reviewed
  exception for every untested cell; the target is ratified before the run.
- [ ] **Transition ATPG.** Target ≥ 80% at the 400 MHz clock; launch/capture
  timing is checked against the slow corner.
- [ ] **Untestable list reviewed.** Each untestable fault is classified as
  redundant, blocked by a RAM, blocked by an analog block, or a real coverage
  gap; "untestable" is not accepted as a category by itself.
- [ ] **Gate-level simulation.** All patterns pass on the post-layout netlist
  with back-annotated delays; a single failing pattern is a stop item.
- [ ] **Test time.** Longest chain length × pattern count at the tester clock is
  recorded; target under 1 s, or the compression ratio is raised until it is.
- [ ] **Flow selected.** The repository's Yosys/OpenROAD flow contains no scan
  insertion or ATPG step. A production DFT flow is selected and its licence
  recorded; this is a blocker, not a schedule risk.

**Evidence:** inserted netlist, scan description (SPF/STIL), ATPG logs, coverage
report, untestable-fault report, gate-level log, reviewer signoff.

---

## 2. MBIST

*Owner role: DFT/test lead.*

- [ ] **Array inventory.** All 48 arrays (16 cores × LMEM, ICache, DCache) are
  listed with instance path, geometry, ports, clock and power domain.
- [ ] **Controller.** A March C- controller drives each array, or a shared
  controller with a mux; the address and data paths are test-mode only and do
  not add a functional path.
- [ ] **Algorithm.** March C- covers stuck-at, transition and coupling faults;
  address-decoder faults are covered by the address progression. Any additional
  algorithm is justified by the macro's fault model.
- [ ] **Clock.** MBIST runs from a divided clock (100 MHz target), independent
  of the core clock, so a core clock failure does not hide an array failure.
- [ ] **Fail signature.** The failing address, expected data and observed data
  are latched and readable over JTAG; a single "fail" bit is not sufficient for
  bring-up.
- [ ] **Repair decision.** If the PDK macros provide row/column redundancy, the
  fuse or register repair path is specified; if not, the no-repair decision and
  its yield impact are recorded.
- [ ] **ECC bypass.** ECC is bypassed or disabled during MBIST, and the bypass
  is proven not to leak into functional mode.
- [ ] **Gate-level simulation.** MBIST passes on the gate-level netlist with
  timing, including one injected failing bit that must be reported.
- [ ] **Post-silicon order.** MBIST runs before scan and before boot; a failing
  array is mapped to a physical location on the die for failure analysis.

**Evidence:** controller RTL, array map, algorithm description, GLS log, fail
signature transcript, repair decision, reviewer signoff.

---

## 3. ECC and error reporting

*Owner role: RTL/verification lead.*

- [ ] **SECDED on all three arrays.** 64 data bits + 8 check bits on LMEM,
  ICache and DCache; encode on write, decode on read. The code is Hsiao or
  equivalent, with the parity matrix recorded.
- [ ] **Correctable error.** Corrected data is returned, a counter increments,
  and the access does not stall; the counter is readable over JTAG.
- [ ] **Uncorrectable error.** A fault is raised, the address and syndrome are
  logged, and the core halts or traps per the ratified policy. Silent bad data
  is not an option.
- [ ] **Scrubbing.** Each array is read in the background at a defined rate, or
  the no-scrub decision is recorded with its reliability rationale.
- [ ] **Register file parity.** One bit per 32-bit register word, or a written
  waiver; the register file is the largest unprotected state on the die.
- [ ] **Fault injection.** Each bit of a 72-bit codeword is flipped in
  simulation: single-bit errors correct, double-bit errors flag, no false
  correction. The test is part of the regression, not a one-off.
- [ ] **Error counters.** Correctable and uncorrectable counts are sticky or
  clear-on-read by an explicit policy; both are visible to the debugger.
- [ ] **Area and timing.** 12.5% bit overhead and the encode/decode delay are
  accounted in the 10.8 mm² die estimate and the 400 MHz timing; the delta is
  reported, not absorbed silently.

**Evidence:** ECC RTL, parity matrix, injection regression log, counter map,
area/timing delta, reviewer signoff.

**Status (2026-11-05):** the codec and counters exist in
`hw/rtl/libs/VX_ecc_secded.sv` and `hw/rtl/libs/VX_ecc_ctrl.sv`;
`hw/rtl/libs/VX_ecc_ram.sv` wraps the bank RAM and LMEM's banks now use it,
with a read-modify-write cycle for byte-enable writes. The ICache and DCache
are still unprotected, the counters have no JTAG/CSR readout, and there is no
area/timing delta, so none of the items above is complete.

---

## 4. Floorplan

*Owner role: physical-design lead.*

- [ ] **Die size and aspect ratio.** ~10.8 mm² including the 256 KB test SRAM,
  pad ring and ECC; the actual size and the delta from the estimate are
  recorded. The test SRAM's attachment point is new RTL, not a port the current
  configuration already exposes.
- [ ] **Core array.** 16 cores in a 4 × 4 array, each with its own LMEM, ICache
  and DCache adjacent to it; no array is placed across the die from its core.
- [ ] **SRAM placement.** All 48 functional arrays plus the test SRAM are
  placed with their pins oriented toward the consuming logic; macro abutment
  and power-strap rules are checked.
- [ ] **Clock tree.** One 400 MHz domain, ICG cells (`VX_clockgate`) per core
  and cluster, skew and insertion delay targets set; the clock tree is built
  after the floorplan is stable, not before.
- [ ] **Power grid.** Core and IO supplies, IR-drop target (typically 5% of
  nominal), EM current limits and the number of metal layers are agreed; the
  10 W envelope is the design case.
- [ ] **Test SRAM and JTAG bridge.** The 256 KB test SRAM and the JTAG-to-memory
  bridge sit on the die edge next to the TAP, outside the core array, so test
  traffic does not cross the cluster fabric.
- [ ] **Pin placement.** JTAG, clock, reset and debug on one edge; power and
  ground on all edges; memory ports either unbonded or on a dedicated edge.
- [ ] **Congestion.** No channel narrower than the agreed minimum; SRAM pin
  access, power straps and the clock tree are checked together before routing.
- [ ] **DRC/LVS.** The assembled floorplan, with all macros, passes DRC and LVS
  before full place-and-route; a clean final GDS does not excuse a dirty
  floorplan.
- [ ] **Area reconciliation.** The placed area is compared with 7.3 mm² logic +
  1.9 mm² memory + 0.6 mm² test SRAM + pads; the difference is explained.

**Evidence:** floorplan database, placement report, clock-tree and IR-drop
reports, DRC/LVS logs, area reconciliation, reviewer signoff.

---

## 5. Package

*Owner role: package/board lead.*

- [ ] **Pin list.** JTAG (TCK, TMS, TDI, TDO, TRST), clock, reset, test-mode
  select, debug bus, core/IO supplies and grounds are enumerated with direction
  and voltage.
- [ ] **Memory-port decision.** The top-level memory interface is 512 bits wide
  per port, but the default T0 configuration resolves to **zero ports**
  (`VX_MEM_PORTS` follows the L3 port count, and L3 is disabled). Confirm
  whether zero ports is the intended topology or an expression bug. Either way
  the test SRAM needs an attachment point at the cache hierarchy's memory side;
  that is new RTL, not an existing port. If a wide port is bonded, the package
  is BGA with well over a thousand signals, not QFN. T0's baseline is *not
  bonded*. The decision is recorded before the pin list is frozen.
- [ ] **Package selection.** QFN-128 for the unbonded case: body size, pitch,
  thermal pad, and the number of spare pins for bring-up.
- [ ] **Power delivery.** Core and IO rails, decoupling, plane splits and the
  IR-drop budget from the package pins to the die pads.
- [ ] **Thermal.** 10 W design case, θJA, ambient and junction temperature; a
  bring-up heatsink is allowed, a fan is not assumed.
- [ ] **Pinout review.** The pinout is checked against the test board and the
  socket before the package is ordered; a swapped JTAG pin is a respin, not a
  board fix.
- [ ] **Models.** IBIS (and die/package parasitics if the memory ports are
  bonded) are delivered with the package for signal-integrity review.
- [ ] **Test board.** Schematic, BOM, power sequencing and JTAG header are
  reviewed with the pin list; the board is ordered with the package, not after.

**Evidence:** pin list, package drawing, thermal and IR-drop reports, IBIS,
board schematic, reviewer signoff.

---

## 6. JTAG bring-up

*Owner role: silicon bring-up lead.*

The TAP, DTM, DM and SBA register map are specified in
[the T0 JTAG specification](proposals/g100_t0_jtag_debug.md). T0-A is SBA-only
(load, read, reset); halt/resume and abstract commands are T0-B, because the
core has no debug hooks today.

- [ ] **TAP.** A 5-bit-IR TAP with IDCODE, BYPASS, DTMCS and DMI; EXTEST and
  SAMPLE/PRELOAD at custom IR codes only if the pad library provides
  boundary-scan cells. The IDCODE is recorded and matches the package. The
  T0-A TAP, DTM, DM, SBA and test SRAM live in `hw/rtl/dbg/` and are simulated
  by `hw/unittest/t0_dbg` in the `unittest` CI lane; the silicon transcript is
  still outstanding.
- [ ] **DTM and DM.** The RISC-V Debug 0.13 register map is implemented for the
  T0-A subset (DMCONTROL, DMSTATUS, HARTINFO, ABSTRACTCS, COMMAND, SBCS,
  SBADDRESS0, SBDATA0). Halt, resume and abstract register access are T0-B and
  are tested against OpenOCD only when they exist.
- [ ] **Memory access.** A JTAG-to-memory path reaches the test SRAM through
  the new memory-side bridge, so code and data can be loaded without a host or
  DRAM interface. The SBA register sequence and error codes are in the
  [T0 spec](proposals/g100_t0_jtag_debug.md) §4–§5; without the bridge the die
  can be identified but not run.
- [ ] **Reset behavior.** Power-on reset, JTAG reset and core reset are
  independent; the core comes out of reset at the boot sequencer's known entry,
  not executing uninitialized memory.
- [ ] **Load and run.** A minimal test image is written to the test SRAM over
  SBA, read back word-for-word, and released; the core boots from
  `0x8000_0000` and writes a result word that is read back over SBA. The
  transcript is retained. The boot sequencer and core-side attachment exist
  and the flow passes in simulation on the real `VX_core` with a toolchain-built
  image; the silicon run is still outstanding. The simulation image also walks
  a one and a zero through all 4096 lines (exhaustive 32-bit walking on every
  eighth line), and the JTAG test checks the DMI busy op=3/`dmistat=3` path.
- [ ] **Boundary scan.** EXTEST proves the board-to-die interconnect on the
  test board; a failing net is located before any functional test. If the pad
  library has no boundary-scan cells, record the exception and use a JTAG
  loopback instead.
- [ ] **OpenOCD and GDB.** T0-B only, once halt/resume exists. In T0-A the
  host tool's SBA transcript is the record; a checked-in OpenOCD config that
  fails on halt is not evidence.
- [ ] **Clock and reset sequencing.** The order of rail, clock, reset and JTAG
  is written down; a brown-out or a missing clock must not look like a TAP
  failure.
- [ ] **Failure signatures.** IDCODE mismatch, chain continuity failure, MBIST
  failure and DM timeout each have a first action; none is "power-cycle and
  retry".
- [ ] **Bring-up order.** IDCODE → boundary scan → MBIST → scan → ECC → DM →
  memory test → DXA/TCU GEMM. Each step has a pass criterion before the next
  starts.

**Evidence:** TAP/DM RTL, OpenOCD config, GDB transcript, boundary-scan log,
load-and-run transcript, bring-up procedure, reviewer signoff.

---

## 7. First-silicon bring-up order

1. **Rails and clocks.** All supplies in range, clock present at the expected
   frequency, reset released. No JTAG access until this is true.
2. **IDCODE.** Read the TAP IDCODE; a wrong value stops bring-up.
3. **Boundary scan.** EXTEST the board interconnect; locate opens and shorts.
4. **MBIST.** Run all 48 arrays; record pass/fail and failing addresses.
5. **Scan.** Run the chain-integrity flush, then the stuck-at patterns.
6. **ECC.** Inject a correctable and an uncorrectable error through the debug
   path; confirm the counters and the fault.
7. **Debug module.** Read DMSTATUS, set `ndmreset`, run an SBA write/read at
   the test SRAM base, clear `ndmreset`.
8. **Memory.** Write and read the test SRAM at the base, middle and last word,
   including byte-enable patterns; LMEM is not on the SBA path in T0-A.
9. **Compute.** Load a small GEMM into the test SRAM; the boot program copies
   it to LMEM and runs it through the TCU; compare against the host reference.
10. **DXA.** Fetch a tile from the test SRAM into LMEM, then run the GEMM again.

Each step's result is recorded against the same die serial and the same board.
A failure at step N stops the sequence; steps after it are not "not run", they
are blocked by a known fault.

---

## 8. Exit criteria

- [ ] All six sections have linked evidence and a named reviewer.
- [ ] Every waiver is listed with its rationale, owner and expiry; a waiver
  without an expiry is an open item.
- [ ] No critical item is unchecked. A critical item is one whose failure
  prevents bring-up or invalidates the test plan.
- [ ] The tapeout package contains the final GDS with checksum, the gate-level
  netlist, the scan description, the MBIST/ECC test firmware, the test program,
  the pin list and the bring-up guide.
- [ ] The package, test board and bring-up plan are ordered/booked; a die
  without a way to test it is not taped out.
- [ ] Independent design, DFT, physical-design, package and bring-up signoffs
  are recorded. Self-signoff is not signoff.

---

## 9. What exists in the repository today

| Area | RTL | Flow | Gap |
|---|---|---|---|
| Scan | No scan ports or chains | No DFT step in `syn/` | Insertion, ATPG, GLS |
| MBIST | No controller | No generator | Controller, array map, repair decision |
| ECC | SECDED codec, counters, ECC bank RAM with byte-enable RMW; LMEM protected (`hw/rtl/libs/`); benches `hw/unittest/ecc`, `hw/unittest/ecc_ram` | ICache/DCache unprotected, no JTAG counter map | Wrap ICache/DCache, counter map, area/timing |
| JTAG | TAP, DTM, DM, SBA, boot, attachment, arbiter and test SRAM (`hw/rtl/dbg/`) | CI-run Verilator TB (`hw/unittest/t0_dbg`) with a toolchain-built image; no DFT or GLS | Gate-level, board |
| Clock/reset | `VX_clockgate`, `VX_reset_relay`, single top-level clock/reset | Synthesis only | Clock tree, reset sequencing, test muxing |
| Floorplan | — | OpenROAD available | Placement, power grid, pin placement |
| Package | — | — | Pin list, package selection, test board |

The functional RTL is not the gap. The gap is that none of the manufacturing
and bring-up infrastructure exists yet, and each item above is on the critical
path to a tapeout package.

---

## 10. Blockers

1. **PDK and library unselected.** No DRC/LVS deck, no SRAM macros, no IO cells,
   no timing corners. Every item in this checklist is provisional until E-003
   closes.
2. **No DFT flow.** The open-source flow has no scan insertion, ATPG or MBIST;
   a production flow and its licence must be selected.
3. **JTAG is RTL-tested but not silicon-proven.** The T0-A TAP/DM/SBA path
   exists and passes its Verilator testbench; it has no gate-level run, no
   board transcript and no T0-B halt/resume.
4. **ECC covers LMEM only.** `VX_ecc_ram` encodes on write and corrects on
   read, and a byte-enable write pays one read-modify-write cycle to recompute
   its check bits. ICache and DCache still store unprotected words, and the
   error counters have no JTAG/CSR readout.
5. **Core-side path is simulated, not built.** `VX_t0_core_attach` and
   `VX_t0_boot` now wire the real `VX_core` instruction/data ports and boot a
   toolchain-built image in simulation. The full cluster's L1/L2 is not
   instantiated, and there is no gate-level or silicon run.
6. **Package decision depends on the memory-port bond-out**, which depends on
   whether T0 is a test die or the first product die. The baseline assumes test
   die; a product die changes the pin list and the package.

None of these is a reason to relax an item. They are the reason the tapeout
date is not set by the September 2026 shuttle schedule.
