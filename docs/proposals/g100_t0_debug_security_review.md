# G100-T0 Debug Path — Security Review

**Status:** Review, not a design change. No RTL is modified by this document.
**Date:** 2026-11-03
**Scope:** `hw/rtl/dbg/` as built for T0-A — TAP, DTM, DM, SBA, arbiter, test
SRAM and boot sequencer — plus the host/tooling assumptions in the
[T0 debug design](g100_t0_jtag_debug.md).
**Reference model:** Tenstorrent's
[SystemSecurity.md](https://github.com/tenstorrent/tt-isa-documentation/blob/main/SystemSecurity.md),
used as an external checklist rather than as a description of our hardware.
**Method:** RTL reading and testbench inspection. No formal analysis, no fault
injection, no silicon. Findings are about reachability and failure modes, not
about exploitability on a lab bench.

---

## 1. Summary

1. **The T0 debug path is an unauthenticated code-execution interface, by
   construction.** JTAG reaches a 256 KB SRAM over SBA, `ndmreset` re-arms the
   boot sequencer, and the boot sequencer launches a fixed entry point inside
   that same SRAM. A probe therefore has write access to the image and control
   of the reset that launches it.
2. **That is the right trade for a first-silicon bring-up die**, and the design
   says so: authentication and secure debug are explicitly out of scope
   ([design](g100_t0_jtag_debug.md), header). What the design does not have is
   an off switch. Nothing in the block distinguishes a lab from a product.
3. **The containment that does exist is stronger than the model it is compared
   against.** The SBA window is a hard-wired 14-bit comparator equal to the
   SRAM size (`VX_dm_sba.sv:90`), and the SRAM decodes the same window
   independently (`VX_t0_test_sram.sv:51`). Unlike a NoC fence, it cannot be
   widened by anything running on the device, because nothing on the device can
   reach it.
4. **Ten findings, one of them structural.** The rest are robustness and
   bookkeeping: a drain state with no timeout, no write interlock, SRAM
   retention across reset, untested out-of-range behaviour, and one
   documentation divergence. There is no finding that requires reworking the
   block for T0; several must be closed before T0-B or any reuse outside
   bring-up.

## 2. What the path can reach

| Surface | Reach | Bounded by |
|---|---|---|
| DMI registers | DM control/status, SB address and data | 7-bit address; abstract commands refused (`VX_dm.sv:210`) |
| SBA read/write | `0x8000_0000`–`0x8003_FFFF`, 256 KB | Hard-wired compare against `addr[31:18] == 14'h2000` (`VX_dm_sba.sv:90`) |
| `ndmreset` | Core, KMU and boot sequencer reset | `DMCONTROL[1]` (`VX_dm.sv:180`); `core_reset` in `VX_t0_dbg_top.sv:214` |
| Boot | One launch at `0x8000_0000`, grid 1×1×1 | `ENTRY` parameter (`VX_t0_boot.sv:21`) |
| Core memory | Only through the attachment to the same SRAM | `VX_t0_core_attach.sv`; no DRAM, L2 or NoC in the T0 island |
| Host | None | No PCIe, no host mailbox, no DMA in T0 |

The two decoders agree: SBA's byte window `0x8000_0000`–`0x8003_FFFF` maps to
SRAM line addresses `0x2000_0000`–`0x2000_FFFF`, exactly the 4096 lines the
controller implements. A mismatch here would be the classic debug-bridge escape;
there isn't one today, and a test should keep it that way (§6).

## 3. Tenstorrent's model, applied

Their premise is that device code reaches every tile, so containment must come
from outside the chip: IOMMU, driver mappings, who may run code, reset policy.
Our T0 has almost none of those components, which makes the comparison short
but not useless.

| Their recommendation | Our T0 equivalent | Verdict |
|---|---|---|
| Enable the IOMMU | No host path exists on T0 | Not applicable yet; becomes the governing rule when debug moves to PCIe |
| Map only what the device needs | SBA window equals SRAM size; nothing else decodes | **Met**, and hard-wired |
| Treat device access as control | A probe can rewrite the image and re-boot it | **True, and documented** |
| Never trust what the device writes | The boot result word is read back over SBA and asserted by CI | Fine as a design test, not as attestation |
| Don't rely on on-chip fences | We rely on a comparator, not a fence; device code cannot re-point it | **Stronger than the model** |
| Tiles with clocks off hang everything | A lost SBA response hangs `ST_DRAIN` forever | **Not met** — see F-3 |
| Start every job on a clean device | SRAM contents survive `ndmreset`; DM state does not | **Not met** — see F-5 |

The useful transfer is not a mechanism but a habit: write down what device code
can reach, and make the answer smaller than "everything". Ours is already
smaller; it is simply not written down anywhere a security reviewer would look.

## 4. Findings

### F-1 — Critical, by design: JTAG is code execution on the core

**Evidence:** SBA writes the boot image's memory (`VX_dm_sba.sv:90`),
`DMCONTROL[1]` resets the core and KMU (`VX_dm.sv:180`,
`VX_t0_dbg_top.sv:214`), and `VX_t0_boot` relaunches `ENTRY`, which lies inside
that memory (`VX_t0_boot.sv:21`).
**Consequence:** physical access to five pins is enough to run arbitrary RV32I
code on the core, with no authentication, no lock and no audit trail. On a
shared lab bench or a board farm this is a code-execution path between users,
not just a debug feature.
**Status:** intended for T0. The design already excludes authentication; what
it does not yet state is that the block must be fused off or removed before any
die that runs untrusted images. See G-1 and G-3.

### F-2 — High: no lifecycle gate on the debug port

**Evidence:** `VX_jtag_dtm` accepts every DMI op unconditionally; `dmactive`
gates the DM's own state (`VX_dm.sv:145`) but not the port. There is no
`debug_disable` strap, no fuse input, and no top-level signal that could
distinguish product from bring-up.
**Nuance:** `DMSTATUS.authenticated = 1` (`VX_dm.sv:86`) is **correct** — the
spec requires that bit to be preset when a DM has no authentication. The
finding is the absence of a gate, not a false claim.
**Consequence:** a production die built from this RTL would ship with an open
DMI unless the block is physically removed. "We will not connect JTAG" is a
board decision, not a silicon one.

### F-3 — Medium: `ST_DRAIN` has no timeout, so one lost response wedges debug

**Evidence:** `ST_WAIT` times out after `TIMEOUT_CYCLES` and reports `sberror=1`
(`VX_dm_sba.sv:105-116`), then enters `ST_DRAIN`, which waits for
`rsp_valid` with no bound (`VX_dm_sba.sv:119-123`). `busy` stays high, and the
DM's `sbbusy` can only clear on `sba_done` or on a busy edge that will now
never occur.
**Consequence:** if the target never answers — a clock stopped mid-transaction,
a future SBA target that hangs, a reset that eats the response — SBA is dead
until chip reset. On T0 the SRAM always answers, so this is latent; it becomes
real the moment the bridge points at anything else.
**Fix:** bound `ST_DRAIN`, and make a second timeout return `sberror=1` with the
pipeline discarded rather than waiting for a response that may never come.

### F-4 — Medium: no interlock between SBA writes and a running core

**Evidence:** the arbiter gives SBA priority at any time (`VX_t0_mem_arb.sv:42`)
and the DM has no halt to gate it; `ndmreset` is the only way to stop the core.
Status reporting is honest — `allrunning`/`anyrunning` (bits 11/10) follow
`~ndmreset`, and `allhalted`/`anyhalted` (bits 9/8) stay 0, which is correct for
a DM that cannot halt — so a conformant host knows the core is running.
**Consequence:** nothing in hardware prevents a host from rewriting the
instruction stream while the core executes it. Correct tooling holds
`ndmreset` first; the invariant lives in the tool, not the block.
**Fix:** once halt exists (T0-B), refuse SBA writes unless the core is halted or
in reset, and make the refusal an `sberror` rather than silent corruption.

### F-5 — Medium: the SRAM array survives reset

**Evidence:** `VX_t0_test_sram.sv:41` resets control state only; `mem[]`
(`VX_t0_test_sram.sv:27`) is never cleared, and `ndmreset` does not touch it.
**Consequence:** an image, its arguments and any result word remain readable
over SBA after reset and after the next boot. On a board farm this leaks one
user's workload into the next session, and it makes "reset before reassignment"
untrue as a claim.
**Fix:** scrub on reset (4096 lines is cheap in hardware) or have the loader
overwrite the region before release and say so in the bring-up procedure.

### F-6 — Low: tags are ignored, so the path is only safe while single-outstanding

**Evidence:** the arbiter routes responses by its `owner` latch and explicitly
ignores the returned tag (`VX_t0_mem_arb.sv:51`; design §5.4 says the same);
SBA sends `tag = 0` (`VX_dm_sba.sv:60`).
**Consequence:** correct today because the SRAM is single-outstanding and the
arbiter serialises. If a later revision pipelines the memory — the design
already suggests a tagged queue — a late response can be delivered to the wrong
master. This is the mirror image of Tenstorrent's "responses go wherever the
request says": our safety comes from ordering, not from identity.
**Fix:** the tagged-queue replacement must check tags, and the arbiter's
single-outstanding assumption should be asserted in the testbench.

### F-7 — Low: out-of-range accesses return zeros, not an error

**Evidence:** the SRAM sets `oob` and returns zero data with a normal response
(`VX_t0_test_sram.sv:62-65`); `oob` is a testbench output
(`VX_t0_dbg_tb_top.sv:147`) that no test asserts on.
**Consequence:** a core fetch outside the window executes zeros instead of
trapping; a debugger sees a successful read of zeroes. Silent zero-fill is the
worst of the three possible answers.
**Fix:** turn `oob` into a bus error path, or at least assert it in the TB so an
escaped access fails loudly.

### F-8 — Low: the design document and RTL disagree on reset behaviour

**Evidence:** the design's interface table says functional `reset` "does not
reset the DM when `dmactive`" ([design](g100_t0_jtag_debug.md), §2), while
`VX_dm` clears `dmactive` and all DM state on `reset` (`VX_dm.sv:143-160`).
**Consequence:** RTL is the fail-safe direction — a system reset drops debug
rather than preserving it — but a host or a future T0-B implementation written
from the document would expect the opposite.
**Fix:** correct the document, or add the state-retention the table promises if
that is what T0-B needs.

### F-9 — Low: SBA can starve instruction fetch

**Evidence:** `VX_t0_mem_arb.sv:43` grants SBA whenever it requests.
**Consequence:** a host that hammers SBA stalls the core indefinitely. On T0
that is a debugging mistake, not an attack; it becomes a fairness bug in any
automated fuzz or regression loop that shares the port.
**Fix:** round-robin between SBA and the core, or bound consecutive SBA grants.

### F-10 — Info: `dmactive` and `ndmreset` written together

**Evidence:** the write handler takes the `ndmreset` bit only when the *old*
`dmactive` is set (`VX_dm.sv:180`).
**Consequence:** a single write of `dmactive=1, ndmreset=1` leaves `ndmreset`
unchanged; the second write works. Tools that write the register once will
misbehave. Low impact, easy to hit with a hand-written loader.

## 5. What is already right

- **Window equals memory.** The SBA comparator and the SRAM decoder describe
  the same 256 KB (`VX_dm_sba.sv:90`, `VX_t0_test_sram.sv:51`). This is the
  single most important property in the block and it is right.
- **No register path.** Abstract commands are refused with `cmderr=2`
  (`VX_dm.sv:210`), so there is no GPR read/write and no PC redirect primitive
  beyond rewriting the image and resetting.
- **Error codes instead of hangs.** Out-of-window, misaligned and unsupported-
  size accesses are distinguished (`VX_dm_sba.sv:88-96`), matching the design's
  documented mapping.
- **DMI busy detection.** A second access while one is pending returns
  `dmistat=3` rather than corrupting the first (`VX_jtag_dtm.sv`, `dr_update`
  path).
- **Status is honest.** Running/halted bits match the spec's layout (verified
  against OpenOCD's generated `debug_defines.h`: `authenticated`=7,
  `anyhalted`=8, `allhalted`=9, `anyrunning`=10, `allrunning`=11).
- **Fail-safe reset.** A functional reset drops DM state rather than preserving
  a live debug session across it.

## 6. Production gates

These are conditions on shipping this block, not defects to fix for T0.

| Gate | Requirement |
|---|---|
| **G-1** | A lifecycle input — fuse or strap — that leaves IDCODE and DTMCS visible but makes DMI unavailable, verified by test. |
| **G-2** | If debug must remain in a product, an authenticated unlock with a bounded attempt count; the spec's `authenticated` bit then reflects a real check. |
| **G-3** | No boot sequencer and no SRAM-as-reset-vector in production; the production reset vector comes from ROM, and the T0 SRAM is absent or unbacked. |
| **G-4** | SRAM scrubbed on reset, or the loader contract states it overwrites the region and the procedure enforces it. |
| **G-5** | SBA writes refused unless the core is halted or held in reset (arrives with T0-B halt). |
| **G-6** | Bounded `ST_DRAIN` with an error return (F-3). |
| **G-7** | Tag checking before any pipelined memory is attached (F-6). |
| **G-8** | Out-of-range becomes a bus error, not zeros (F-7). |
| **G-9** | The threat-model sentence — physical probe equals code execution — appears in the product security notes and the tapeout checklist. |

## 7. Tests worth adding now

1. **Out-of-window SBA access** returns `sberror=2` and does not disturb the
   SRAM (today untested; `oob` is never checked).
2. **Drain timeout**: a memory model that never responds must end in an error,
   not a hung `sbbusy`. Nothing exercises this today, which is the point of
   F-3.
3. **Reset during an SBA write**: after `ndmreset` and release, the next access
   succeeds and the previous transaction leaves no state behind.
4. **Retention**: document, then assert, what the array holds across
   `ndmreset` — first as current behaviour, then as the G-4 scrub.
5. **DMSTATUS invariant**: running bits equal `~ndmreset` and halted bits are
   zero, so a future halt implementation cannot silently change the meaning.

## 8. Limits of this review

- RTL reading only; no formal, no fault injection, no power or clock-domain
  analysis. A CDC fault in the DTM could change reachability and is not
  covered here.
- The DFT path (`test_mode`, scan chains) is out of scope; the TAP exposes no
  scan DR, but the package and board chain are not examined.
- The eventual PCIe/host debug path does not exist yet. When it does,
  Tenstorrent's first recommendation applies verbatim: the IOMMU and the
  driver's mappings become the boundary, not anything on the die.
- Tenstorrent's document describes a NoC-based architecture with device code
  that can reach every tile. It is used here as a checklist, not as a claim
  that the two designs share a threat model.

## 9. Related documents

- [G100-T0 JTAG debug design](g100_t0_jtag_debug.md) — the block under review.
- [G100-T0 tapeout checklist](../grxgpu_g100_t0_tapeout_checklist.md) — where
  G-1 and G-9 belong.
- [G100 production baseline](g100_production_baseline.md) — the configuration
  whose debug story this constrains.
