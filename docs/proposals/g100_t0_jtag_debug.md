# G100-T0 JTAG TAP, Debug Module and Memory Bridge

**Status:** T0-A implemented in `hw/rtl/dbg/` and verified by
`hw/unittest/t0_dbg` — load/read, DMI busy, full-array walking and real-core
boot with a GNU-toolchain RV32I image. T0-B (halt, resume, abstract commands, GDB)
remains specification only.
**Date:** 2026-11-01
**Baseline:** [G100-T0 tapeout checklist](../grxgpu_g100_t0_tapeout_checklist.md)
§6 and [G100 production baseline](g100_production_baseline.md) §6.
**What it must make possible:** a blank die is identified and its 256 KB test
SRAM is loaded and read back over the five JTAG pins, with no host or DRAM
interface. Running the loaded image uses the boot sequencer and the core-side
attachment of §5.6; simulation runs the image on the real `VX_core`.
**What it is not:** trace, triggers, authentication, secure debug, or multi-hart
run control. A security review of the path as built is
[g100_t0_debug_security_review.md](g100_t0_debug_security_review.md).

---

## 1. Staging

The T0 die needs two different things from its debug path, and they have very
different costs.

| | T0-A — first silicon | T0-B — after bring-up |
|---|---|---|
| TAP, DTM, DMI | Yes | Yes |
| SBA read/write of the test SRAM | Yes | Yes |
| `ndmreset` and core release | Yes | Yes |
| Hart halt/resume | No | Yes |
| Abstract register/memory commands | No | Yes |
| Breakpoints and GDB | No | Yes |
| OpenOCD `riscv` target | No | Yes |
| Host tool | Small SBA loader | OpenOCD + GDB |

T0-A is the scope of this document's required RTL. T0-B depends on a core debug
interface that the Vortex RTL does not have today: a search of `hw/rtl/` finds
no `dcsr`, `dpc`, halt request or debug-mode state. Adding it changes the
scheduler and fetch path, and is specified in §8 but not required for the first
tapeout.

This staging is deliberate. It makes the SRAM load/read path independent of
run-control, so a failure in the core debug hooks cannot block first-silicon
memory test, and a failure in the TAP cannot be confused with a core bug.

---

## 2. Top-level interface

| Signal | Direction | Domain | Notes |
|---|---|---|---|
| `jtag_tck` | in | TCK | 10 MHz bring-up target; TAP is static at this rate |
| `jtag_tms` | in | TCK | sampled on the rising edge |
| `jtag_tdi` | in | TCK | sampled on the rising edge |
| `jtag_tdo` | out | TCK | changes on the falling edge |
| `jtag_trst_n` | in | async | resets the TAP only; optional, tie high if absent |
| `clk` | in | core | 400 MHz target |
| `reset` | in | core | functional reset; does not reset the DM when `dmactive` |
| `test_mode` | in | core | scan/DFT isolation strap; 0 in functional use. The JTAG bridge does not depend on it |

The TAP, IR/DR shift registers and DTMCS run in the TCK domain. The DM, SBA
master, bridge, arbiter and test SRAM run in the core clock domain. The DMI
request/response handshake is the only crossing; it uses a stable-data,
two-flop-synchronized valid/ready protocol, not a combinational path.

**IDCODE, BYPASS and DTMCS must work with the core clock stopped.** They do not
touch the core domain. A DMI access with the core clock stopped returns
`dmistat=3` (busy) rather than hanging the TAP.

---

## 3. TAP

The TAP is the standard 16-state IEEE 1149.1 machine. The IR is **5 bits** and
resets to IDCODE, which is what `vortex.cfg` already declares
(`jtag newtap ... -irlen 5`).

| IR | Register | DR length | Required |
|---|---|---|---|
| `0x00` | BYPASS | 1 | Yes |
| `0x01` | IDCODE | 32 | Yes |
| `0x10` | DTMCS | 32 | Yes |
| `0x11` | DMI | 41 | Yes |
| `0x1F` | BYPASS | 1 | Yes |
| `0x02` | EXTEST | BSR length | Optional, custom |
| `0x03` | SAMPLE/PRELOAD | BSR length | Optional, custom |

The RISC-V DTM assigns `0x00` to BYPASS; EXTEST and SAMPLE are not part of that
map. They are added at `0x02`/`0x03` only if the pad library provides
boundary-scan cells. If it does not, both decode to BYPASS and the board
interconnect test uses a JTAG loopback instead. The checklist's EXTEST item is
conditional on this.

**IDCODE.** `0x00100001`: version 0, part `0x0100`, manufacturer `0x000`, LSB 1.
The manufacturer field is provisional until a JEDEC JEP106 ID is assigned; the
part number is provisional until the SKU is named. The value is a parameter, not
a hard constant.

**DTMCS.** `version=1`, `abits=7`, `idle=0`, and the 32-bit layout is:

| Field | Bits | Value |
|---|---|---|
| `version` | `[3:0]` | 1 |
| `abits` | `[9:4]` | 7 |
| `dmistat` | `[11:10]` | 0, 1 or 3 |
| `idle` | `[14:12]` | 0 |
| `dmireset` | `[16]` | write 1 to clear `dmistat` |
| `dmihardreset` | `[17]` | write 1 to reset the DTM |

The simulator's `sim/simx/dtm/jtag_dtm.cpp` places `dmistat` at bit 18, which
is outside the field, and writes 1 for a failed access; the defined values are
2 (operation failed) and 3 (response busy). Both are simulator defects to fix
rather than a layout to copy.

**DMI.** 41 bits, least significant first:

```
[1:0]   op      0 = nop, 1 = read, 2 = write, 3 = reserved
[33:2]  data    32-bit DMI data
[40:34] address 7-bit DMI address
```

A DMI scan shifts in the previous response and shifts out the previous result;
the DTM must not issue a new request while one is outstanding. If the debugger
scans again before the response arrives, the returned `op` is 3 and the request
is dropped, not queued. `dmireset` clears the sticky status.

---

## 4. DTM and debug module

The DMI address map matches `sim/simx/dtm/debug_module.h`, so a register written
by the simulator's debugger means the same thing on the die.

| DMI | Register | T0-A fields |
|---|---|---|
| `0x04` | DATA0 | 32-bit abstract data (read/write, unused in T0-A) |
| `0x05`–`0x07` | DATA1–DATA3 | Not implemented; reads return 0, writes ignored |
| `0x10` | DMCONTROL | `dmactive`, `ndmreset`, `hartsel`; `haltreq`/`resumereq` write ignored in T0-A |
| `0x11` | DMSTATUS | `version=2`, `authenticated=1`; `allrunning` reflects `ndmreset` |
| `0x12` | HARTINFO | Optional; reads 0 (no program buffer, no dscratch) |
| `0x16` | ABSTRACTCS | `datacount=1`, `progbufsize=0`, `busy=0`, `cmderr=0` |
| `0x17` | COMMAND | Writes return `cmderr=2` (not supported) in T0-A |
| `0x18` | ABSTRACTAUTO | Reads 0 |
| `0x38` | SBCS | `sbversion=1`, `sbasize=32`, `sbaccess=2`, `sbbusy`, `sbbusyerror`, `sberror`, `sbreadonaddr` (writable, reset 0); `sbautoincrement=0`, `sbreadondata=0` |
| `0x39` | SBADDRESS0 | 32-bit physical address |
| `0x3C` | SBDATA0 | 32-bit read/write data |

Addresses not listed return DMI status 2 (not supported); they must not hang
the DMI.

**DM reset.** `dmactive=0` resets the DM to its reset values but not the TAP.
The debugger sets `dmactive=1` before using anything else. `ndmreset=1` resets
the core and the boot sequencer, not the DM, the TAP or the test SRAM.

**SBA behaviour.** T0-A implements 32-bit system-bus access:

- `sbasize=32`, `sbaccess=2`; other sizes are unsupported and set `sberror=4`.
- `sbreadonaddr` is writable, reset 0. With it set, a write to SBADDRESS0
  starts a read; the loader sets it 1 for the verify pass and 0 for the write
  pass, so an address write does not race the following data write.
- A write to SBDATA0 starts a write to SBADDRESS0.
- `sbbusy` is set when the request leaves the DM and cleared when the memory
  response returns; the host polls it, then checks `sberror` before using the
  data.
- `sberror` is sticky and write-1-to-clear: `1` timeout, `2` bad address,
  `3` alignment, `4` unsupported size, `7` other.
- `sbautoincrement=0` and `sbreadondata=0`; the host increments addresses.
- One access outstanding. A second access while `sbbusy` sets `sbbusyerror`
  and is dropped.

The exact bit positions of DMCONTROL, DMSTATUS, HARTINFO, ABSTRACTCS and SBCS
are the RISC-V Debug 0.13 definitions; the simulator's field lists are the
reference for which fields exist, not for their numeric positions.

---

## 5. Memory bridge and test SRAM

### 5.1 Address map

| Region | Base | Size | Responder |
|---|---|---|---|
| Test SRAM | `0x8000_0000` | 256 KB (`0x8000_0000`–`0x8003_FFFF`) | Test SRAM controller |
| Everything else | — | — | No responder; SBA returns `sberror=2` |

`0x8000_0000` is the kernel entry the existing debug flow already uses
(`docs/kernel_debugging.md` §"Key Addresses"), so a test binary linked there
needs no relocation.

### 5.2 Data path

```
  JTAG pins ─► TAP/DTM ─► DM ─► SBA master ─┐
                                            ├─► 2:1 mem_bus arbiter ─► test SRAM
  core memory port (512-bit, see note) ─────┘        (512-bit, 64 B line)
```

Both masters speak `VX_mem_bus_if` with `DATA_SIZE=64` (64 bytes, 512 bits) and
a 64-bit byte-enable. The SBA master is 32 bits wide and converts one word into
one 512-bit beat; it is not a performance path.

**The core-side port is not present in the T0 configuration.** With L3
disabled, `VX_MEM_PORTS` resolves to 0, so the core has no top-level memory
port. `VX_t0_core_attach` therefore takes the core's `icache_bus_if` and
`dcache_bus_if` ports directly and merges them into the arbiter's core port;
T0 does not need an L3 just to reach the SRAM.

### 5.3 SBA transaction

1. The SBA master aligns the 32-bit address to a 64-byte line and computes the
   byte offset within it.
2. It drives `req_valid`, `req_data.rw`, `req_data.addr = addr[31:6]`,
   `req_data.byteen = 64'hF << addr[5:0]`, and the 32-bit word placed in the
   lane selected by `addr[5:2]`.
3. `attr=0`, `tag=0`. The tag is not used for routing; the arbiter tracks the
   owner of the single outstanding request.
4. On `req_ready`, it waits for `rsp_valid`, captures the 512-bit line, and
   selects the word at `addr[5:2]` for a read.
5. Writes return a response with undefined data; the bridge ignores it.
6. If no response arrives within 1024 core cycles, the bridge sets a timeout,
   returns `sberror=1`, and drops the response if it arrives later.

### 5.4 Arbiter

A dedicated 2:1 mux, not `VX_mem_bus_arb`. The generic arbiter inserts the
granted port index into the tag, and the T0 bridge has no use for that bit;
more importantly, it allows several requests in flight, while the test SRAM
controller is single-outstanding. The T0 arbiter therefore serialises:

- it grants SBA input first when both request, else the core;
- it latches `owner` (0 = core, 1 = SBA) with the granted request and holds
  `req_ready` low on both inputs until that request's response returns;
- it routes the response to `owner` and ignores the returned tag.

This costs the core concurrency it does not need during bring-up: the SBA is
32 bits wide against a 512-bit line, and the boot image is loaded while the
core is in reset. If a later revision needs concurrent core traffic, replace
this block with a tagged queue; the SRAM controller's contract does not change.
The arbiter must never merge or reorder requests.

### 5.5 Test SRAM controller

- 4096 lines × 64 bytes = 256 KB, 512-bit data, 64-bit byte enables.
- `req_ready` is high when idle; one request at a time; `rsp_valid` is held
  until `rsp_ready`.
- Reads return the full line; writes update only the bytes selected by
  `byteen` and still return a response with the tag.
- The bus carries a 26-bit line address (`VX_CFG_MEM_ADDR_WIDTH=32` minus
  `CLOG2(64)`). The controller decodes `addr[25:12] == 14'h2000`; any other
  address is not its own. For T0 it is the only slave, so an out-of-range
  access returns zeros and sets a sticky `oob` flag that the SBA can read
  through a debug register if one is added later.
- The SRAM macro may be one 4096 × 512 array or 16 banks of 4096 × 32 with a
  512-bit read mux. The PDK choice is open; the byte-enable behaviour is not.

### 5.6 Boot release

A blank core has no code and no KMU launch, so the wrapper provides a small boot
sequencer. After `ndmreset` is released and `boot_en` is set, it:

1. writes `VX_DCR_KMU_STARTUP_ADDR0 = 0x8000_0000` and
   `VX_DCR_KMU_STARTUP_ADDR1 = 0`;
2. writes `VX_DCR_KMU_KERNEL_ENTRY0 = 0x8000_0000` and entry 1 = 0;
3. writes grid `1,1,1` and block `VX_CFG_NUM_THREADS,1,1` (one warp of 4
   threads in the default T0 configuration);
4. pulses `start` for one cycle, then waits for `busy` to rise and fall.

The sequencer is `hw/rtl/dbg/VX_t0_boot.sv`. It writes the same 20 DCRs the
runtime's launch path writes (including the block size, warp steps and
cluster dimensions, whose reset zeros otherwise stall the dispatcher), pulses
`start`, waits for the KMU's `busy` to rise and fall, and reports `boot_done`
or `boot_error` on timeout. `boot_done` means the KMU accepted the launch;
completion is observed by polling the result word the image writes.

`boot_en` is a strap; if it is 0 the core stays in reset, so T0-A boards strap
it high. It is not a substitute for `ndmreset`: `core_reset = reset | ndmreset
| ~boot_en`, and the sequencer only starts once both `ndmreset` is low and
`boot_en` is high.

The core's instruction and data ports share the single test-SRAM port through
`hw/rtl/dbg/VX_t0_core_attach.sv`. On the die the inputs are the core's
`icache_bus_if` and `dcache_bus_if` ports, which are word-granular: 4 B fetch
and 8 B data across `DCACHE_NUM_REQS` channels. The test SRAM is 64 B
line-oriented, so the attachment widens a request to a line, selects the
addressed word on the response, and round-robins fetch and data. Stores
complete at request acceptance; the attachment drains the SRAM's write
response instead of returning it, because the core's store path has no unmerge
buffer to release. When `core_reset` asserts mid-transaction it drains any
stranded response so the SBA stays usable while `ndmreset` is held.

The simulation instantiates the real `VX_core` with the KMU dispatch exposed
and the DCR, global-barrier and DXA buses tied off. It assembles and links
`hw/unittest/t0_dbg/t0_image.S` at `0x8000_0000` with the RISC-V GNU toolchain,
loads the flat binary over SBA, releases the core, and checks the result and
status words the image writes.

---

## 6. Software flow

### 6.1 TAP and SBA

The T0-A host tool drives TCK/TMS/TDI directly (FTDI MPSSE on the board, a
remote-bitbang socket in simulation). It performs:

```
TAP reset → IDCODE (must be 0x00100001) → DTMCS (abits=7)
→ DMI write dmcontrol.dmactive=1
→ DMI write dmcontrol.ndmreset=1 (hold core in reset)
→ SBCS.sbreadonaddr=0 → SBA writes of the test image at 0x8000_0000
→ SBCS.sbreadonaddr=1 → SBA reads and compare
→ DMI write dmcontrol.ndmreset=0 (release; the boot sequencer starts)
→ poll a result word the test writes
```

The test image is a raw binary linked at `0x8000_0000`; the loader writes it in
32-bit words and verifies by reading back. A word count and a checksum are
recorded so a partial load is not mistaken for a pass.

### 6.2 OpenOCD (T0-B only)

Once halt/resume and abstract commands exist, the same TAP works with OpenOCD:

```
transport select jtag
adapter speed 100
jtag newtap g100_t0 tap -irlen 5 -expected-id 0x00100001
target create g100_t0.riscv0 riscv -chain-position g100_t0.tap -coreid 0
riscv set_mem_access sysbus
riscv set_reset_timeout_sec 2
riscv set_command_timeout_sec 2
init
```

`riscv set_mem_access sysbus` makes OpenOCD use SBA for `load_image`, `mdw` and
`mww`; `halt`, `resume` and GDB breakpoints need T0-B. The simulator's
`vortex.cfg` stays on abstract access until the SimX DM grows SBA; otherwise
the same config must not be used for both.

---

## 7. RTL module plan

| Module | Responsibility | Rough size |
|---|---|---|
| `VX_jtag_tap.sv` | 16-state TAP, 5-bit IR, IDCODE/BYPASS/DTMCS/DMI, optional BSR | 2–3K gates |
| `VX_jtag_dtm.sv` | DMI shift, request/response CDC, sticky status | 1–2K gates |
| `VX_dm.sv` | DMI register file, `dmactive`/`ndmreset`, SBA control | 5–10K gates |
| `VX_dm_sba.sv` | SBA 32-bit master, address check, timeout, error codes | 2–3K gates |
| `VX_t0_mem_arb.sv` | 2:1 serialising mux, owner tracking, response routing | <1K gates |
| `VX_t0_test_sram.sv` | 512-bit `VX_mem_bus_if` slave, byte enables, SRAM macro wrapper | 1–2K gates + macro |
| `VX_t0_boot.sv` | KMU DCR sequence, `start` pulse, busy wait, timeout | <1K gates |
| `VX_t0_core_attach.sv` | Word↔line conversion and merge of the core's I/D channels | 1–2K gates |
| `VX_t0_dbg_top.sv` | Wrapper: pins, TAP, DM, bridge, arbiter, SRAM, boot | glue |

Estimated total: 0.02–0.05 mm² of logic plus the 256 KB SRAM (0.52 mm² at
0.25 µm²/bit), which is the 0.6 mm² already in the baseline's die row.

The T0-A subset is implemented in `hw/rtl/dbg/`: `VX_jtag_tap`, `VX_jtag_dtm`,
`VX_dm`, `VX_dm_sba`, `VX_t0_mem_arb`, `VX_t0_test_sram`, `VX_t0_boot`,
`VX_t0_core_attach` and the `VX_t0_dbg_top` wrapper, which also instantiates
the real `VX_kmu`. The wrapper's core-facing ports are the KMU dispatch bus and
the instruction/data memory ports; the simulation attaches a real `VX_core`
and runs a toolchain-built image.

---

## 8. T0-B: core debug hooks

The core has no debug mode. T0-B adds a `VX_dbg_if` between the DM and the
scheduler:

```
halt_req, resume_req, step, halted, running
pc, pc_we
gpr_addr, gpr_rdata, gpr_wdata, gpr_we
csr_addr, csr_rdata, csr_wdata, csr_we
halt_cause
```

The scheduler stops issuing on `halt_req`, drains inflight instructions, asserts
`halted`, and exposes the current warp's PC and GPR. `resume_req` clears the
halt and restarts fetch at `pc`. `step` executes one instruction and re-halts.
The DM then implements:

- COMMAND access-register (GPR and CSR) and access-memory;
- DPC and DCSR;
- breakpoints via the trigger module or an `ebreak` trap;
- `hartsel` over the 16 cores, with all cores halted for a first bring-up.

This is the largest new RTL item in the debug path, and it is deliberately not
on the T0-A critical path. Until it exists, OpenOCD can identify the TAP and
load memory but cannot halt or single-step the core.

---

## 9. Verification

**Simulation (Verilator).** `hw/unittest/t0_dbg` drives TCK/TMS/TDI directly and
passes on Verilator 5.020. From a configured build tree,
`make -C hw/unittest/t0_dbg run` builds and runs it; the boot image is built
with `$(RISCV_TOOLCHAIN_PATH)`. CI runs the same target through the `unittest`
catalog's `hw-t0` lane, pinned to xlen 32, on every push and pull request. The
test target uses `-Wno-fatal` for the standalone core's pre-existing RTL lint
warnings, as `sim/rtlsim` does, so they remain visible without failing the
build. It covers:

- TAP reset: IR=IDCODE, IDCODE value, BYPASS, DTMCS (`version=1`, `abits=7`).
- DMI: read/write every implemented register; an unimplemented address returns
  op=2 and latches `dmistat=2`; `dmireset` clears it. A second DMI access
  shifted while a request is pending returns op=3 and latches `dmistat=3`,
  which `dmireset` clears.
- SBA: word write/read at the base, mid-range and last word; adjacent words in
  one line survive each other's byte enables; a walking pattern across 32 lines
  spread over the 256 KB; address out of range (`sberror=2`); misaligned
  (`sberror=3`); unsupported size (`sberror=4`); timeout injection
  (`sberror=1`), with `sbbusy` held until the late response drains; the access
  after the drain succeeds.
- SRAM: a read returns one response per request; `dmactive=0` resets the DM but
  not the array.
- Arbiter and attachment: SBA and core traffic serialise; the attachment
  round-robins fetch and data channels and returns each response to its owner.
- Boot: the toolchain-built image is loaded over SBA, the core is released
  through `boot_en`/`ndmreset`, `VX_t0_boot` programs the KMU, the real
  `VX_core` fetches and executes the image, and the result and status words
  are read back over SBA. Also covered: `boot_en=0` holds the core in reset,
  `ndmreset` blocks and re-arms the boot, a stalled core times out with
  `boot_error`, and the SBA remains accessible while `ndmreset` is held.
- Full-array walk: every line gets a unique marker and a walking one/zero,
  with the bit position advancing with the line; every eighth line also gets
  the exhaustive 32-bit walking-one/walking-zero pattern. The image copies
  itself to the last 4 KB, which the walk has just covered, and tests its own
  original lines from the copy, so all 4096 lines are covered. Each of the
  four active lanes publishes its mismatch count; the restart and
  timeout-recovery boots use a minimal image so the exhaustive walk runs once.

Not yet covered by the testbench:

- the full cluster: the attachment sits at the core's cache-side I/D
  boundary, so the L1 caches, L2 and cluster fabric are not instantiated in
  the T0 island. The real `VX_core` is the same core the cluster uses;
- SystemVerilog assertions: the checks above are testbench comparisons, not
  SVA properties.

**Gate level.** TAP, DM, bridge and SRAM with SDF at 400 MHz core / 10 MHz TCK,
including the CDC paths. Not run yet.

**Board.** IDCODE, boundary scan (if fitted), SBA load and verify, core release,
result read; the same transcript on two boards to catch a socket or adapter
difference.

---

## 10. Open items

1. **Pad cells for boundary scan.** EXTEST/SAMPLE are optional until the pad
   library is known; if it has no BSC cells, the IR decodes to BYPASS and the
   board test uses loopback.
2. **Core debug hooks.** T0-B's `VX_dbg_if` does not exist; it is the largest
   new RTL item and is not required for the first tapeout.
3. **SimX parity.** The simulator's DM has abstract commands but no SBA. Either
   add SBA to `sim/simx/dtm/debug_module.cpp` or keep the two flows separate
   and document why; do not let one config silently mean two things.
4. **IDCODE fields.** Manufacturer 0x000 and part 0x0100 are placeholders until
   JEDEC and the SKU are assigned.
5. **TCK maximum.** 10 MHz is the bring-up target; the TAP is static, but the
   CDC and pad timing at 10 MHz must be closed.
6. **Adapter and connector.** The board's JTAG header and level shifting are
   package/board work; the TAP spec assumes 3.3 V CMOS and a 5-pin header.
7. **Test SRAM attachment.** Closed in RTL and simulation: the real `VX_core`
   `icache_bus_if`/`dcache_bus_if` ports connect to `VX_t0_core_attach`, and a
   GNU-toolchain RV32I image boots from the test SRAM and writes its result
   word. The attachment is at the core's cache-side boundary; the cluster's L1
   and L2 are not part of the T0 island. Gate-level and board runs remain.
