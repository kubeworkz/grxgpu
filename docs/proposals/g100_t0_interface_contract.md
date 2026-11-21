# G100-T0 v1 Interface Contract — System Diagram and ICD

**Status:** **Approved v1.0**, 2026-11-21. The G2 approval record is
[the G2 gate record](../evidence/g100-t0-g2-2026-11-21/gate-record.md).
Approval freezes the T0 engineering interfaces; it does not authorize a
product, purchase, or tapeout.
**Gate:** G2 — product architecture and interface freeze.
**Scope:** the G100-T0 engineering die and the interfaces needed to boot,
debug, load, and run it. Product-die interfaces are explicitly excluded.
**Baseline:** [G100 production baseline](g100_production_baseline.md) §6;
[G0 engineering authorization](../grxgpu_g100_g0_authorization.md);
[G1 evidence audit](../grxgpu_g100_t0_g1_evidence_audit.md).
**Normative terms:** **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are used in
their usual requirements sense. A row marked **open measurement** is a frozen
interface with an unmeasured numeric limit, not an unfrozen interface.

---

## 1. What v1 freezes, and what it excludes

v1 freezes the **T0 engineering boundary**: a JTAG-only bring-up die with
on-die SRAM and no product host or DRAM interface. That is the machine the
baseline and G0 authorize. It does not freeze a sellable SKU, and it does not
invent a PCIe, HBM, DDR, NVLink, or graphics interface that the RTL does not
have.

| In v1 | Out of v1 |
|---|---|
| 5-wire JTAG TAP/DTM, RISC-V Debug 0.13 T0-A subset | PCIe, CXL, NVLink, any host DMA path |
| 32-bit SBA reads/writes to the 256 KB test SRAM | T0-B halt/resume, abstract commands, GDB |
| Boot/reset sequencer and KMU launch | Firmware update, secure boot, authenticated debug |
| 1 cluster × 16 cores, TCU + DXA, 16 KB LMEM/ICache/DCache per core | L2/L3, multi-cluster, 128-core product die |
| 256 KB test SRAM at `0x8000_0000` | DRAM/HBM controller or PHY, memory DIMM interface |
| QFN-128 planning package, unbonded memory | Pin-number assignment and package selection |
| 400 MHz core target, 10 MHz TCK target | 800 MHz stretch, DVFS, clock or power gating policy |
| SECDED as a T0 requirement (not implemented) | ECC status window decode before S0 signoff |
| CP command-ring ABI as a software contract | A CP instantiated in T0-A |
| `sgemm_tcu_wg_dxa` K=64/K=512 golden workload | Customer acceptance, product benchmark, graphics |

Product host, DRAM/HBM, coherency, and update/recovery interfaces remain
**TBD** and MUST NOT be represented as frozen by this document. They are listed
in §12 so the gap is explicit rather than implied.

---

## 2. Frozen system diagram

Figure 1 is the v1 die boundary. Solid paths exist in `hw/rtl/dbg/`; the
DXA-to-test-SRAM path is a required part of v1 but is not wired in the current
T0 island, so it is marked *required-new*.

```text
                    G100-T0 die — QFN-128, memory ports unbonded
 ┌─────────────────────────────────────────────────────────────────────────┐
 │  jtag_tck / jtag_tms / jtag_tdi / jtag_tdo / jtag_trst_n                 │
 │        │                                                                │
 │   ┌────▼─────┐   DMI 41 b    ┌────────────┐   SBA 32 b    ┌───────────┐  │
 │   │ TAP/DTM  │  TCK→clk CDC  │ DM 0.13    │──────────────►│ 2:1       │  │
 │   │ 5-bit IR │──────────────►│ T0-A subset│               │ arbiter   │  │
 │   └──────────┘               └────────────┘               └─┬───────┬─┘  │
 │                                                             │       │    │
 │   clk 400 MHz ──────────────────────────────────────────────┘       │    │
 │   reset ────────────────────────────────────────────────────────────┘    │
 │                                                                     ▼    │
 │   boot_en ─► boot sequencer ── 20 DCR writes ──► KMU         ┌──────────┐ │
 │                                                  │          │ 256 KB   │ │
 │                                                  ▼          │ test SRAM│ │
 │   ┌──────────── 1 cluster × 16 cores ────────────────┐      │ 0x8000…  │ │
 │   │ 4 warps × 4 threads, issue width 4               │      └────┬─────┘ │
 │   │ TCU 4 blocks × 4 lanes, DXA 2 workers            │           │       │
 │   │ LMEM / ICache / DCache 16 KB per core            │◄──────────┘       │
 │   │ core I/D cache-side ports ─► core attach ─► arbiter               │
 │   └───────────────────────┬──────────────────────────┘                  │
 │                           └── DXA GMEM port ──► test SRAM  [required-new]│
 └─────────────────────────────────────────────────────────────────────────┘
```

Two evidence boundaries are part of the freeze:

1. **T0-A island (verified):** `VX_t0_dbg_top` instantiates the TAP, DTM, DM,
   SBA, arbiter, test SRAM, boot sequencer, KMU, core attachment, and **one**
   `VX_core`. The JTAG testbench boots a toolchain-built image on that core.
2. **T0 die target (not yet integrated):** the 16-core cluster, its L1/L2
   memories, and the DXA path to the test SRAM. v1 freezes the target; G3 owns
   the integration and verification evidence.

The system diagram is frozen at the **interface** level. Implementations may
change only through §14 change control.

---

## 3. Interface register

Each interface has a producer, consumer, fixed width/rate or an explicitly open
measurement, defined reset/error behavior, and a verification owner role.

| ID | Interface | Producer → consumer | Width / rate / limit | Reset and error behavior | Verify (role) | State |
|---|---|---|---|---|---|---|
| IF-01 | JTAG pins | probe → TAP | 5 pins; TCK ≤10 MHz target; 3.3 V CMOS | `TRST_n` resets TAP only; no authentication | Bring-up lead | Implemented, simulated |
| IF-02 | DMI | DTM → DM | 41 b scan; 7-bit address; one outstanding | busy → `dmistat=3`; unsupported address → status 2 | Verification lead | Implemented, simulated |
| IF-03 | SBA | DM → arbiter | 32 b address/data; one outstanding; 4 B accesses | `sberror` 1/2/3/4/7; timeout 1024 core cycles | Verification lead | Implemented, simulated |
| IF-04 | Test SRAM | arbiter → SRAM | 512 b data, 64 B line, 64 b byte-enable; 4096 lines | OOB currently returns zeros — see G-2 | Verification lead | Implemented; OOB behavior non-conforming |
| IF-05 | Core I/D attach | core → arbiter | I: 4 B; D: 8 B × `DCACHE_NUM_REQS`; widened to 64 B | stalled core is reset by `ndmreset`; no bus error | Verification lead | Implemented, single core |
| IF-06 | Boot/KMU DCR | boot sequencer → KMU | 20 × 32 b writes; start pulse; 1024-cycle timeout | timeout → `boot_error`; no retry | Bring-up lead | Implemented, simulated |
| IF-07 | DXA GMEM | DXA → memory | 64 B lines; 1 beat/cycle; ≤8 in flight; 16-entry queue | watchdog assertion, no software error status | Verification lead | RTL exists; T0 attach **required-new** |
| IF-08 | DXA descriptor | host → DCR table | 16 slots × 24 DCRs; 64 b base | none; descriptor is write-only from host | Software lead | Implemented in RTL/SimX |
| IF-09 | TCU/LMEM | DXA/TCU → LMEM | 1 LMEM word/cycle; DXA priority 0, TCU priority 1 | barrier tx completion; no error status | Verification lead | Implemented |
| IF-10 | CP ring (software) | host runtime → CP | 64 B lines; 4 B header; ≤5 commands/line; 1 queue default | no CP fault channel — see G-3 | Software lead | Defined; not in T0-A |
| IF-11 | Clock/reset | board → die | 400 MHz target (open measurement); TCK 10 MHz | async reset; `core_reset = reset \| ndmreset \| ~boot_en` | Bring-up lead | Defined; STA open |
| IF-12 | Power/thermal | board → package | 10 W design case; Tj/θJA open measurement | none; no throttle or shutdown | Power/thermal lead | Defined; unmeasured |
| IF-13 | Package | die → board | QFN-128; no bonded memory; pin groups fixed, numbers TBD | thermal pad; no fan assumed | Package/board lead | Boundary frozen; selection open |
| IF-14 | Golden workload | host CPU → reference | M=N=64; K=64/512; FP16→FP32 | zero ULP failures beyond budget | Verification lead | Frozen, CPU-only |

---

## 4. Host and debug interface (T0-A)

### 4.1 Pins and TAP

The T0-A host interface is the five JTAG pins. There is no PCIe, no host
mailbox, no interrupt, and no DMA from a host.

| Signal | Direction | Domain | Requirement |
|---|---|---|---|
| `jtag_tck` | in | TCK | ≤10 MHz bring-up target; static TAP |
| `jtag_tms` | in | TCK | sampled on rising edge |
| `jtag_tdi` | in | TCK | sampled on rising edge |
| `jtag_tdo` | out | TCK | changes on falling edge |
| `jtag_trst_n` | in | async | resets TAP only; tie high if absent |

The IR is 5 bits. IDCODE is `0x00100001` (version 0, part `0x0100`,
manufacturer `0x000`) and is **provisional**: the manufacturer field changes
when a JEDEC JEP106 ID is assigned and the part field changes when the SKU is
named. BYPASS, DTMCS, and DMI are mandatory. EXTEST/SAMPLE are optional at
custom IR codes and exist only if the pad library provides boundary-scan cells;
otherwise both decode to BYPASS and board interconnect is tested by loopback.

### 4.2 Debug module and SBA

DMI is 41 bits: `op[1:0]`, `data[33:2]`, `address[40:34]`. T0-A implements the
RISC-V Debug 0.13 registers listed in the [JTAG specification](g100_t0_jtag_debug.md)
§4 — DMCONTROL, DMSTATUS, HARTINFO, ABSTRACTCS, COMMAND, ABSTRACTAUTO, SBCS,
SBADDRESS0, SBDATA0. Abstract commands are refused with `cmderr=2`; halt,
resume, and GDB are T0-B and not in v1.

SBA rules frozen by v1:

- 32-bit physical address, 32-bit data, `sbaccess=2` only.
- A write to SBDATA0 starts a write to SBADDRESS0; a write to SBADDRESS0
  starts a read only when `sbreadonaddr=1`.
- One access outstanding. A second access while `sbbusy` sets `sbbusyerror`
  and is dropped.
- `sberror` is sticky, write-1-to-clear: 1 timeout, 2 bad address, 3
  alignment, 4 unsupported size, 7 other.
- The SBA window is `0x8000_0000`–`0x8003_FFFF` exactly. The comparator and the
  SRAM decoder MUST continue to describe the same 256 KB.
- A response timeout is 1024 core cycles. The timeout returns `sberror=1` and
  enters a drain state; the current unbounded drain is a known deviation (§13,
  G-1).

The host flow is fixed: TAP reset → IDCODE → DTMCS → `dmactive=1` →
`ndmreset=1` → SBA write of the image at `0x8000_0000` → SBA read-back compare
→ `ndmreset=0` → poll the image's result word. The loader MUST verify every
word it writes; a partial load is not a pass.

### 4.3 No product host

v1 has **no** host-visible doorbell, queue register, interrupt, or shared
memory. A product host interface remains TBD under §12. T0 cannot be used to
claim PCIe, CXL, NVLink, or driver interoperability.

---

## 5. Memory, DRAM/HBM, and addressability

### 5.1 Address map

| Range | Size | Responder | v1 behavior |
|---|---|---|---|
| `0x0000_0000`–`0x7FFF_FFFF` | — | none | Unmapped. SBA MUST return `sberror=2`; core access MUST NOT silently succeed |
| `0x8000_0000`–`0x8003_FFFF` | 256 KB | test SRAM | Boot image, arguments, results; 64 B lines, byte enables |
| `0x8004_0000`–`0x800F_FFFF` | — | none | Unmapped |
| `0x8010_0000`–`0x8010_FFFF` | 64 KB | reserved | ECC status window **only if S0/D9 is accepted**; not implemented |
| `0x8011_0000`–`0xFFFF_FFFF` | — | none | Unmapped |

DCR space is separate and 12 bits wide. KMU DCRs occupy `0x010`–`0x023`; DXA
descriptor DCRs occupy `0x100`–`0x27F` (16 slots at stride 24). A DCR access
does not alias the memory map.

### 5.2 Alignment and access size

- SBA accesses are 4 B and MUST be word-aligned. SBA converts each word to one
  512-bit line beat; it is not a performance path.
- The test SRAM is line-oriented: reads return 64 B; writes update the bytes
  selected by the 64-bit byte-enable and return a response.
- Core fetches are 4 B and core data accesses are 8 B wide at the attachment.
  The attachment widens a request to a line and selects the addressed word on
  the response.
- DXA base addresses and row strides MUST be consistent with the 64 B GMEM
  line and the element size. The descriptor does not carry a base-address
  alignment field; software MUST align.

### 5.3 No DRAM/HBM and no coherency protocol

T0 has **no** DRAM, HBM, L2, L3, IOMMU, or hardware cache-coherency protocol.
The test SRAM is the only memory. The T0-A island instantiates no L1 cache;
the core's cache-side ports are attached directly, so an SBA read after a
completed core store sees the stored data because there is no intervening
cache.

The contract is therefore:

1. The core MUST be held in `ndmreset` while the host rewrites the boot image
   or its arguments over SBA. The hardware does not enforce this today
   (security review F-4); software enforcement is mandatory until G3 adds an
   interlock.
2. SBA and core traffic MUST NOT be treated as concurrent. The arbiter
   serializes one outstanding request and grants SBA first; there is no
   fairness guarantee.
3. `ndmreset` does **not** clear the SRAM. A reloading host MUST overwrite the
   region it trusts; retained data is readable over SBA (F-5).
4. No device-side fence, cache flush, or atomic operation is part of the T0
   memory contract. The product CP's cache-flush command is defined in §8 but
   is not exercised by T0-A.
5. Product coherency is **not frozen**. It must be proven for the selected core
   count under G3/E-104 before any product claim.

---

## 6. DMA and DXA

### 6.1 T0 has no host DMA

There is no CP DMA engine, no host memory port, and no device-to-host copy in
T0-A. The only data movement into T0 is SBA stores; the only compute data
movement is core fetch/load/store and DXA GMEM reads.

### 6.2 DXA contract

DXA is a cluster-scoped, asynchronous GMEM→LMEM copy engine: two workers at
the T0 configuration, 16 descriptor slots, a 16-entry request queue, and at
most 8 in-flight GMEM reads per worker. There is no software→global path.
Multicast and K-major/block-major layouts are part of the DXA design, but the
frozen workload uses two 2-D descriptors and block-major B.

| Field | Frozen value |
|---|---|
| ISA | `INST_SFU_DXA` (`custom0`, `funct7=3`), `MISA` bit 10 |
| Descriptor storage | DCR `0x100 + slot*24`, 16 slots |
| Base address | 64-bit physical, split LO/HI; DXA bypasses per-core MMU |
| Rank | 1–5; frozen workload uses 2 |
| Element size | 1, 2, 4, 8 B; frozen workload uses 2 (FP16) |
| Tile sizes | 16-bit per dimension; `tile0/tile1` for 2-D |
| Row stride | `stride0_bytes`; frozen A `K*2`, B `N*2` |
| OOB | clamp plus constant fill (`cfill`); software sets 0 unless required |
| Layout | row-major, K-major, flat, or block-major; B uses block-major |
| Completion | LMEM-side barrier transaction (`tx`); no DCR status bit |
| Error | watchdog assertion only; no recoverable error code |

DXA descriptor programming is a host/DCR operation: the runtime's
`vortex::dxa::program_2d`, `set_layout`, and `set_tile_geometry` are the
normative encoders ([DXA host API](../../sw/runtime/include/dxa.h)). The RTL
descriptor is `dxa_desc_t` in `hw/rtl/dxa/VX_dxa_pkg.sv`; the host META field
widths and offsets are in `sw/common/dxa_meta.h` and MUST match the RTL.

**T0 reachability requirement (required-new).** DXA's GMEM port MUST reach the
test SRAM window `0x8000_0000`–`0x8003_FFFF`; otherwise the T0 GEMM cannot use
DXA tiles at all. The current T0 top has no DXA port: `VX_t0_dbg_top` connects
only the core I/D ports and SBA to the arbiter. Adding the DXA path (and its
arbitration with SBA/core) is a v1 requirement and a G3 verification item, not
an implemented feature.

### 6.3 CP DMA (product software path)

The CP's `CMD_MEM_WRITE/READ/COPY` DMA transfers in ≤4 KB INCR chunks. v1
requires byte-exact tails for unaligned lengths. The current RTL rounds the
transfer up to a 64 B multiple and drives all byte-enables, which is a known
non-conformance (§13, G-3). No T0 path uses CP DMA.

---

## 7. Command ABI

Two command surfaces are frozen. They are not interchangeable.

### 7.1 T0 boot ABI (implemented)

A blank T0 core has no command queue. The boot sequencer writes 20 KMU DCRs
and pulses `start`:

| DCR | Offset | Value at boot |
|---|---|---|
| `KMU_STARTUP_ADDR0/1` | `0x010/0x011` | `0x8000_0000`, 0 |
| `KMU_KERNEL_ENTRY0/1` | `0x012/0x013` | `0x8000_0000`, 0 |
| `KMU_STARTUP_ARG0/1` | `0x014/0x015` | 0 |
| `KMU_BLOCK_DIM_X/Y/Z` | `0x016–0x018` | 4, 1, 1 |
| `KMU_GRID_DIM_X/Y/Z` | `0x019–0x01B` | 1, 1, 1 |
| `KMU_LMEM_SIZE` | `0x01C` | 0 |
| `KMU_BLOCK_SIZE` | `0x01D` | 4 |
| `KMU_WARP_STEP_X/Y/Z` | `0x01E–0x020` | 0 |
| `KMU_CLUSTER_DIM_X/Y/Z` | `0x021–0x023` | 1, 1, 1 |

`boot_en=0` holds the core in reset. `boot_done` means the KMU accepted the
launch; completion is observed by polling a result word the image writes.
`boot_error` is asserted after 1024 cycles without the expected busy edge.
There is no retry and no command queue recovery.

### 7.2 CP ring ABI (frozen software contract; not in T0-A)

The product host path uses a host-memory ring of 64 B lines. The first 4 B of a
command is:

```text
{ reserved[15:0], flags[7:0], opcode[7:0] }
```

The mandatory v1 opcodes are NOP `0x00`, MEM_WRITE `0x01`, MEM_READ `0x02`,
MEM_COPY `0x03`, DCR_WRITE `0x04`, DCR_READ `0x05`, LAUNCH `0x06`, FENCE
`0x07`, EVENT_SIGNAL `0x08`, EVENT_WAIT `0x09`, and CACHE_FLUSH `0x0A`.
LAUNCH_QMD `0x0B` and DRAW `0x0C` are optional capability-gated commands and
are **not** required for v1; a host MUST test the corresponding capability bit
before issuing them. On-wire layouts are the ones encoded by
`sw/runtime/common/device.cpp` and decoded by `hw/rtl/cp/VX_cp_pkg.sv`; the
[command processor design](../designs/command_processor.md) is the normative description.

Queue registers are the CP AXI-Lite map: globals `0x000–0x024`, per-queue
blocks at `0x100 + qid*0x40`, doorbell commit on `Q_TAIL_HI`, completion
seqnum at `Q_SEQNUM`, last DCR read at `Q_LAST_DCR_RSP`. The host runtime
programs the ring/head/completion addresses, sets `CP_REG_CTRL`, writes the
ring, rings the doorbell, and polls the seqnum.

Compatibility and error rules:

1. The `vortex2.h` handle/function shape is the locked v1 software API
   ([runtime API design](../designs/vortex_runtime_api.md)); new capability is additive.
2. `CMD_FENCE` is **not** an ordering primitive in v1: the RTL engine retires
   it immediately. Software MUST NOT rely on it. A launch is followed by
   `CMD_CACHE_FLUSH`, and the runtime's host-side event ordering is the
   supported barrier.
3. `CMD_EVENT_WAIT` is defined but not driven by the host runtime on a single
   in-order ring; wait-before-signal can deadlock. v1 software MUST use
   host-side events, not device-side waits.
4. v1 has no CP fault channel and no recoverable command error. Malformed
   commands and unsupported opcodes are outside the contract; a host-facing
   product MUST NOT ship until a fault/error report is added under a later
   revision (G-3).
5. There is no interrupt in v1. Completion is polling only.

T0-A does not instantiate a CP and cannot exercise this ABI. It is frozen so
the software and product-host work has a stable target, not because T0 proves
it.

---

## 8. Boot, reset, debug, and recovery

### 8.1 Reset domains

| Source | Resets | Does not reset |
|---|---|---|
| Power-on `reset` | TAP/DTM, DM, SBA, arbiter, SRAM control, boot, KMU, core | SRAM contents |
| `jtag_trst_n` | TAP/IR only | DM, core, SRAM |
| `dmactive=0` | DM state | TAP, core, SRAM |
| `ndmreset` | core, KMU, boot sequencer | TAP, DM, SRAM |
| `boot_en=0` | core only | debug island |

`core_reset = reset | ndmreset | ~boot_en`. `ndmreset` MUST be released only
after the image is loaded and verified. The SRAM survives every reset; a host
MUST reload or scrub it before trusting a new image.

### 8.2 Boot sequence

The board supplies rails and clock, asserts reset, then releases reset with
`boot_en=1`. The sequencer writes the 20 KMU DCRs, pulses start, waits for
`busy`, and reports `boot_done` or `boot_error`. The core enters at
`0x8000_0000` with grid 1×1×1 and one block of `VX_CFG_NUM_THREADS` threads.
There is no firmware, no ROM, and no second-stage loader.

### 8.3 Debug scope

v1 includes T0-A only: TAP, DTM, DM, SBA, `ndmreset`, and memory access.
Halt/resume, abstract register access, breakpoints, OpenOCD, and GDB are T0-B
and excluded. Any claim of OpenOCD/GDB support in v1 is false.

Debug is unauthenticated. Physical access to the five JTAG pins is equivalent
to arbitrary RV32I code execution on the core. T0 is a lab bring-up die; the
port MUST be fused off or removed before any die runs untrusted images.

### 8.4 Recovery and update

Recovery is: hold `ndmreset`, reload the image over SBA, verify the word count
and checksum, release `ndmreset`. There is no in-field update, no A/B image,
no rollback, and no secure recovery. Product update/recovery is TBD (§12).

---

## 9. Clocks, power, and thermal

| Item | Frozen value | Evidence status |
|---|---|---|
| Core clock | 400 MHz target (2.5 ns) | Planning/SoC model; no target-library STA |
| Core clock stretch | 800 MHz explicitly **not** in v1 | Paper target only |
| JTAG TCK | ≤10 MHz bring-up target | Static TAP; CDC/pad timing not closed |
| Clock domains | one core `clk` + TCK | TAP/DTM in TCK; DM/SBA/SRAM/core in `clk`; DMI is the only CDC |
| Power design case | 10 W | Package/thermal planning value; no activity-based estimate |
| Supply rails | core and IO, voltages TBD | Package/PDK unselected |
| Junction temperature | open measurement | No θJA, ambient, or measured silicon |
| Cooling | no fan assumed; bring-up heatsink allowed | Package/board assumption |
| Throttling/DVFS | none in v1 | Not implemented |

The 10 W value is a **design case**, not a measured limit. A heatsink is
allowed; a fan is not assumed. The thermal pad of the QFN package is part of the
power/thermal boundary. G3 must record the actual ambient, θJA, and junction
temperature; G4 must confirm them for the selected package.

---

## 10. Package boundary

The v1 package boundary is **QFN-128, memory ports unbonded**. Pin numbers and
the final package drawing are assigned at package selection (G4); the functional
groups are frozen now:

| Group | Minimum signals | Notes |
|---|---|---|
| JTAG | TCK, TMS, TDI, TDO, TRST_N | 5 pins; 3.3 V CMOS |
| Clock/reset | `clk`, `reset` | 400 MHz target; async reset |
| Boot | `boot_en` | strap; 0 holds core in reset |
| Test | `test_mode` | DFT isolation; required at the die, not in the T0-A island top |
| Status/debug | `boot_busy`, `boot_done`, `boot_error`, `ndmreset`, `core_reset` | Recommended for bring-up observability |
| Power/ground | core and IO rails, thermal pad | Count TBD |
| Memory | none bonded | `VX_MEM_PORTS=0` at the T0 configuration |
| High-speed | none | No PCIe/DDR/HBM/NVLink pins |

The QFN-128 choice is a planning assumption, not a supplier-selected package.
If the memory port is bonded, the package becomes BGA with a different pin
budget; that is a scope change under §14, not a v1 option.

---

## 11. Error handling, timeouts, and unsupported behavior

| Condition | v1 required behavior | Current conformance |
|---|---|---|
| SBA bad address | `sberror=2`, no memory change | Implemented |
| SBA misaligned | `sberror=3` | Implemented |
| SBA unsupported size | `sberror=4` | Implemented |
| SBA no response | `sberror=1` after 1024 cycles, then recover | Timeout implemented; drain is unbounded (G-1) |
| DMI while busy | returned `op=3`, sticky `dmistat=3`, no hang | Implemented |
| DMI unsupported address | status 2, no hang | Implemented |
| Boot does not start/complete | `boot_error` after 1024 cycles | Implemented |
| SRAM access outside window | error, not silent zeros | **Non-conforming**: returns zeros (G-2) |
| DXA watchdog | assertion in simulation; no software error | Implemented as assertion only |
| CP malformed command | no v1 behavior; host path blocked | No fault channel (G-3) |
| CP DMA unaligned tail | byte-exact transfer | **Non-conforming**: 64 B rounding (G-3) |
| Reset during SBA transaction | next access succeeds, no stale response | Not fully tested (G-1) |

The "G-" identifiers are the closure items in §13. They are G3 hardening
items, not reasons to weaken the frozen interface.

---

## 12. Explicitly TBD interfaces (not frozen by v1)

These are required for a product die and are **not** satisfied by T0:

1. **Product host**: PCIe/CXL/NVLink controller and PHY, BAR/MMIO map, MSI-X
   or polling contract, IOMMU, driver ownership.
2. **DRAM/HBM**: controller, PHY, capacity, ECC, refresh, address interleave,
   training, and fault policy.
3. **Product coherency**: CPU/device ownership, cache maintenance, atomics,
   and the selected core-count proof.
4. **Product boot/update**: ROM, signed image, A/B update, rollback, secure
   debug lifecycle, recovery without JTAG.
5. **Package/process**: selected PDK, SRAM/IO libraries, package, pinout, and
   signal integrity.
6. **Power/thermal limits**: measured activity power, θJA, Tj max, ambient,
   cooling, and throttling policy.
7. **Product command ABI extensions**: QMD/DRAW capability, fault reporting,
   interrupts, multi-queue concurrency.

Any document that presents one of these as part of G100-T0 v1 is wrong.

---

## 13. Open conformance items carried into G3

| ID | Item | Blocks | Closure |
|---|---|---|---|
| G-1 | SBA drain has no timeout; reset during transaction untested | Robust debug | Bound drain; add reset-recovery test |
| G-2 | Out-of-window SRAM access returns zeros | Defined error behavior | Return an error or assert the OOB path |
| G-3 | CP has no fault channel; DMA tail rounds to 64 B; FENCE is a NOP | Product host path | Add fault status, byte-exact tail, real fence or remove from contract |
| G-4 | DXA has no path to the test SRAM | T0 GEMM via DXA | Add and verify the DXA GMEM attach |
| G-5 | 16-core T0 top and cluster memories are not integrated | T0 die | Integrate and verify the 1×16 cluster |
| G-6 | ECC RTL absent; test-SRAM/three-array protection decisions unsigned | RAS | Close the ECC S0 decisions and implement |
| G-7 | 400 MHz/10 W not closed by STA or measurement | Power/clock | Target-library STA and board measurement |
| G-8 | Package/pinout and PDK unselected | Manufacturing | G4 closure |

---

## 14. Change control and approval

This is v1.0. After the v1.0 approval, a change to any frozen row MUST be
proposed as a revision with:

1. the interface ID and old/new behavior;
2. affected producer, consumer, software, and verification owner;
3. impact on the golden workload and all G2 evidence;
4. re-verification plan and gate impact.

Editorial changes that do not alter behavior may be made without a revision.
A new host, memory, coherency, or package interface is a **v2** boundary, not
an edit to v1.

**Approval.** Gridworkz approved v1.0 for all five roles (Product,
System/SoC, Software, Board, and Verification) on 2026-11-21; the signatures
and disposition are in the
[G2 gate record](../evidence/g100-t0-g2-2026-11-21/gate-record.md). The
approval freezes the T0 engineering interfaces only and does not change the
commercial G0 hold, G4 purchases, G5 implementation, G6 tapeout, or production
release.
