# A Host Path to the PTA Chiplet — Its Registers as a DCR Range, a GEMM as One Command

**Status:** Proposal. No RTL requested. It asks for three numbers to be assigned,
and then for an Emulation CP implementation behind a capability bit — the staging
`CMD_DRAW` took. **Amended 2026-10-04 (§9):** the GEMM is also asked for as a
member of the runtime's command list, so that a network is one doorbell.
**Amended again (§10):** the chiplet's activation stage, so that nothing has to
be launched between a network's layers.
**Scope:** `VX_types.toml`, `sim/common/cmd_processor.{h,cpp}`,
`sim/simx/processor.cpp`, `sw/runtime/include/vortex2.h`, `sw/runtime/common/`
(read, not changed). Nothing here patches grxgpu.
**Baseline:** grxgpu `main` at `7e740129d`; GRXCP `main` at `b851143`.
**Origin:** GRXCP's board plan (`docs/designs/board_program_plan.md`), step S4 and
decisions B4, B7 and B9. The chiplet's register map is
`docs/designs/pta_chiplet_regmap.md` there, its digital twin is
`src/backends/pta_chiplet/`, and the gap this answers is
`docs/designs/cuda_mapping.md` 7.41.
**Related:** [command_processor.md](../designs/command_processor.md), whose
mechanisms this reuses. [pta_weight_set_policies.md](pta_weight_set_policies.md),
written for a tile inside a cluster: GRXCP's board plan has since moved the tile
to a chiplet behind a port, and §7 says where that proposal's answer lands here.

---

## 1. What this asks, and why now

GRXCP's board plan puts the photonic tile on a chiplet of its own beside the G100,
reached from the GPU over a die-to-die link and fed from device memory by a copy
engine (its decision B4). The plan lists that port and the engine behind it as
things owed to you as proposals. **This is neither.** It is the piece in front of
both: how a host tells the G100 to do something with the chiplet.

GRXCP has built everything on its side of that line: a driver for the chiplet's
register map, a device in its runtime, and a grxBLAS route that sends an int8 GEMM
to the tile. All of it ends in three function pointers.

| GRXCP's hook | What it stands in for |
|---|---|
| Read a 32-bit register at an offset | A call in `vortex2.h` that reaches the chiplet's registers |
| Write one | The same |
| Submit a GEMM and learn how it ended | A command the G100 carries to the chiplet |

Only a model fills them, through a test seam, because there is nothing in
`vortex2.h` to call. With nothing attached GRXCP enumerates no PTA device, on any
machine, and that is where it stays until this is answered.

**The ask is three things.**

1. **A range of DCR addresses** for the chiplet's register map. No new opcode and
   no new API: `vx_enqueue_dcr_read` and `vx_enqueue_dcr_write` reach it (§3).
2. **One command**, a GEMM on the chiplet with its operands in device memory: one
   opcode, one descriptor, one enqueue call (§4).
3. **One capability bit**, so a runtime can tell a CP that decodes these from one
   that does not.

**Why before any hardware.** The numbers are yours to pick and not ours: an
address in your DCR space, an opcode in your enum, a bit in your capability word.
Until they exist GRXCP's driver is written against function pointers and can be
held to nothing but a model it attaches itself. And the Emulation CP is where a
wrong choice is cheap to change. An RTL mirror comes with the port, later, and
should inherit a format that software has already run.

**What it would be evidence of.** There is no chiplet. What would sit behind the
command processor is a model of one, and it says so in a register (§5). A stack
that runs end to end on SimX against it shows that the software uses the map and
the command correctly. It says nothing about a photonic device.

---

## 2. What the G100 already has

Read out of this repo rather than assumed, because most of what this needs is
already here.

**Ordered register access.** The CP is the single control plane, and
`CMD_DCR_WRITE` and `CMD_DCR_READ` are commands in the same ring as everything
else, with `vx_enqueue_dcr_write` and `vx_enqueue_dcr_read` in front of them. A
register access through them is ordered against a launch or a copy in the same
queue by construction.

**An address space with room.** `VX_DCR_ADDR_BITS = 12` and
`VX_DCR_DATA_BITS = 32`. The ranges `VX_types.toml` assigns:

| Range | Owner |
|---|---|
| 0x000–0x002 | base |
| 0x010–0x024 | KMU |
| 0x040–0x060 | TEX |
| 0x060–0x06A | raster |
| 0x080–0x097 | OM |
| 0x0A0–0x0A7 | RTU |
| 0x100–0x280 | DXA descriptors |

Everything from 0x280 up is unassigned, and we found no DCR address defined
outside that file.

**Routing by range, with one case that is not broadcast.** In SimX,
`ProcessorImpl::dcr_write` sends the KMU's range to the KMU and broadcasts every
other address to every cluster; `dcr_read` asks each cluster in turn. A chiplet's
range wants the KMU's treatment: one target, and no broadcast.

**Commands that point at a descriptor.** `OP_LAUNCH_QMD` (0x0B) and `OP_DRAW`
(0x0C) are 12-byte commands whose `arg0` is the address of a resident descriptor.
Both are in the Emulation CP only, both are announced by a bit in `CP_DEV_CAPS`
(26 and 25), and the runtime falls back when the bit is clear. That is exactly the
pattern §4 asks for, so it needs no new mechanism.

**A resource held until the work ends.** `VX_cp_launch` holds the KMU grant until
`busy` falls, so a queue serialises its own launches. A GEMM on a tile is the same
shape: start it, wait, retire.

**A clock that composes.** The Emulation CP advances one `tick()` a cycle. The
chiplet's twin has a clock that only its own `pta_twin_run()` advances. One call a
tick is all its timing needs.

**Three things found in passing**, none of them ours to fix:

- `command_processor.md` §2 gives `CMD_DRAW` as 8 bytes; `decode_cmd` returns 12
  for `OP_DRAW`.
- Its §6 puts `SUPPORTS_DRAW` in `GPU_DEV_CAPS`; the Emulation CP and
  `device.cpp` have it in `CP_DEV_CAPS`, at 0x008.
- Its §10, item 12, still lists a DCR reservation at 0x080–0x0BF as never added.
  OM and the RTU are there now.

---

## 3. Part one: the registers

**The proposal.** A window of DCR addresses for each PTA instance, where

```
DCR address = base + instance × stride + (register offset >> 2)
```

The chiplet's map is 32-bit registers at 4-aligned byte offsets, so a register is
one DCR and its value fits a DCR's data exactly. The map's last register today is
at offset 0x0F0, word 60. We would suggest **a base of 0x400 and a stride of 0x100
words**, which is four times what the map uses and leaves four instances below
0x800. The board has one chiplet (B4), and the stride is there so that a second
needs no new map. Both numbers are yours to assign.

**What an access means.** A `CMD_DCR_WRITE` into the window is a write of that
register and a `CMD_DCR_READ` is a read of it. The read's tag is not used. A word
the map does not define reads zero and ignores writes, which is the map's own
rule. A window with no chiplet behind it reads zero throughout. GRXCP's driver
finds a chiplet by reading `PTA_ID` at offset 0 and checking its magic and
version, and it treats zero as nothing there, so no instance count has to be
published anywhere.

**What this buys: ordering.** GRXCP's map was written for a page of a BAR, and had
to lean on the bus for one guarantee: that a read of the window orders behind
earlier writes to it. A ring gives that and something the bus could not. A
configuration write enqueued before a GEMM takes effect before it, and a status
read enqueued after it sees its result, because they are in one queue. The map
says that changing configuration under a running GEMM is a driver bug. Here a
driver cannot write that bug within one queue.

**What it costs.** A register read becomes a ring command, a doorbell, a poll of
`Q_SEQNUM` and an MMIO read of `Q_LAST_DCR_RSP`, where a page of a BAR would be
one MMIO read. `Q_LAST_DCR_RSP` is one slot a queue, so reads do not batch: each
is its own doorbell. GRXCP reads about twenty registers to report the device. That
is paid when properties are queried and not once a GEMM, so we think it is the
right trade.

**The alternative, and why we did not ask for it.** GRXCP's documents today say
the window is a page of the GPU's BAR, reached directly. On your side that is a
third decode region in each AFU (XRT splits its AXI-Lite on bit 12 and gives
0x1000–0x1FFF to the CP's regfile), a seventh and eighth function in the transport
HAL (`cp_reg_read` and `cp_reg_write` reach the regfile and nothing else), and an
access that is out of band from the ring, which hands the ordering back to the
driver. It also puts a second control path beside the CP, which
`command_processor.md` describes as the single one. If you prefer the page all the
same, GRXCP's driver does not care: its hooks take an offset and a value. If you
take the DCR range, GRXCP changes its map's §1 and its board interface document to
say so.

**In RTL, either way,** the access has to cross the die-to-die link to reach the
chiplet, and nothing yet says how. That is not asked for here. One consequence is
worth knowing now: a DCR read that crosses a link takes many cycles, so the
backpressure `command_processor.md` §10, item 4, lists as open on the DCR proxy
becomes a prerequisite for the mirror.

---

## 4. Part two: the work

**The proposal.** `CMD_PTA_GEMM`: 12 bytes, `arg0` the address of a descriptor in
device memory, as `OP_LAUNCH_QMD` and `OP_DRAW` are. 0x0D is the next opcode the
Emulation CP does not use. The descriptor is 64 bytes, little-endian:

| Offset | Field | Written by | Meaning |
|---|---|---|---|
| 0x00 | `size_version` | host | [15:0] the descriptor's size, 64; [31:16] its version, 1 |
| 0x04 | `target` | host | [7:0] the PTA instance; [15:8] the weight bank; [31:16] flags, zero in version 1 |
| 0x08 | `format` | host | 0: int8 operands, int32 results. Others reserved |
| 0x0C | `M` | host | Shots: the rows of the activation matrix |
| 0x10 | `K` | host | Inputs a shot sums |
| 0x14 | `N` | host | Outputs a shot yields |
| 0x18 | `act_addr` | host | `M × K` operands, row-major, contiguous |
| 0x20 | `wgt_addr` | host | `K × N` operands, row-major, contiguous |
| 0x28 | `out_addr` | host | `M × N` results, row-major, contiguous |
| 0x30 | `status` | CP | 0 until the command ends, then how it ended (below) |
| 0x34 | `gemm_index` | CP | `PTA_GEMM_CT` as this GEMM started |
| 0x38 | `saturations` | CP | The GEMM's ADC saturations, 64 bits |

**What it computes.** `out[m][n] = Σ act[m][k] · wgt[k][n]` over `k`, as the tile
computes it, configured as its registers stand when the command starts. The map
already says that configuration takes effect at the next GEMM start. A product larger than
the tile is walked by the chiplet, which holds the accumulation across tiles (B4).
The host does not tile it. Each result is the low 32 bits of its accumulator,
which is what the c930's tile writes today.

**The addresses** are device addresses in the GPU's memory, under whatever
translation `CMD_MEM_COPY` gets. The chiplet has no memory of its own. In GRXCP it
is a device whose operands are allocated on its parent GPU (B9), so the operands
are already where this command looks for them.

**How a command ends.** It always retires, and `status` says how:

| `status` | Meaning | Results |
|---|---|---|
| 1 | Done | Written |
| 2 | Refused: the tile cannot do this as it is configured (an impairment it does not build, a bank it does not have). `PTA_IRQ_STATUS.ERR` is raised | Untouched |
| 3 | Lost: a reset of the chiplet discarded it | Untouched |
| 4 | Not issued: the CP could not use the descriptor (no such instance, a version or format it does not know) and sent the chiplet nothing | Untouched |
| 5 | Not run: it asked to run only after a success, and the command before it did not end done (§9) | Untouched |

The first three are what the twin reports today. The rule behind them is the map's:
a command the device cannot honour is refused and never dropped, because silence
is untestable across a link. GRXCP's gate holds its driver to that: a refused GEMM
reported as a success is one of the errors it was planted with and caught.

**Why the command reports its own index.** Each of a chiplet's GEMMs runs on a seed
derived from `PTA_SEED` and the GEMM's index, so a result is reproducible only by
someone who knows the index it took. Reading `PTA_GEMM_CT` beforehand gives that
in one queue and stops giving it the day there are two.

**The resource.** A fifth one, `RES_PTA`, held from the command's start until the
chiplet reports its end, as the KMU's is for a launch. Four things follow.

- **The ring is the queue.** A second GEMM waits in the ring, not on the chiplet.
  GRXCP's map has an open question about the depth of a queue on the chiplet,
  which the GPU's dispatcher would have to know. At this interface there is no
  depth: the chiplet is given one command at a time.
- **A calibration is backpressure.** A command that reaches a calibrating tile
  starts when the calibration ends. Nothing is dropped, and nothing completes
  silently.
- **Completion is the command's event.** A driver does not poll `PTA_STATUS` for
  work. GRXCP's completion test today is two-part, "the GPU's queue is empty, and
  one read of `PTA_STATUS` shows neither BUSY nor CAL_BUSY", and for a GEMM it
  reduces to waiting on the event. Polling remains for a calibration the driver
  asked for.
- **The cost, stated plainly.** An engine waiting on one resource runs nothing
  else. With `NUM_QUEUES = 1`, which is today's default and all the Emulation CP
  models, a kernel launch waits behind a GEMM on the tile, and a GEMM behind a
  launch. Running the GPU and the chiplet at once needs a second queue, which is
  `command_processor.md` §10, item 6. Until then GRXCP's dispatch model has to
  assume the two are serial, and it will.

In RTL `cp_resource_e` is two bits and has four values, so a fifth widens it.

**The call.** A sketch of its shape, with the names yours to choose:

```c
typedef struct {
    uint32_t    instance, bank;
    uint32_t    format;                   // 0: int8 operands, int32 results
    uint32_t    M, K, N;
    vx_buffer_h act;  uint64_t act_off;   // M × K int8
    vx_buffer_h wgt;  uint64_t wgt_off;   // K × N int8
    vx_buffer_h out;  uint64_t out_off;   // M × N int32
} vx_pta_gemm_info_t;

typedef struct {
    uint32_t status;        // 1 done, 2 refused, 3 lost, 4 not issued, 5 not run
    uint32_t gemm_index;
    uint64_t saturations;
} vx_pta_gemm_result_t;

vx_result_t vx_enqueue_pta_gemm(vx_queue_h q,
                                const vx_pta_gemm_info_t* info,
                                vx_pta_gemm_result_t*     host_result,
                                uint32_t          n_wait_events,
                                const vx_event_h* wait_events,
                                vx_event_h*       out_event);
```

The runtime builds the descriptor, as it does a draw's, and copies the three
result fields to `host_result` before the event signals. With the capability bit
clear the call returns "not supported". There is no fallback to stream in its
place, which is the one way this differs from `vx_enqueue_draw`.

§9 asks for the same GEMM as a member of a command list. That is the form GRXCP
expects to use for anything with more than one layer, and this call is the list
of one.

---

## 5. What sits behind it in a simulator

GRXCP's digital twin of the chiplet: `pta_chiplet_twin.{h,c}`, C99 and the
standard library, in front of grx930's `pta_tile_model.c`, the reference grx930
holds its RTL to bit for bit. It is a register file, a clock and the calibration
contract around that model, and it adds no arithmetic of its own. It maps onto the
two parts one to one.

| Here | The twin |
|---|---|
| A DCR write or read in the window | `pta_twin_write32` / `pta_twin_read32`, at `(addr − base) << 2` |
| `CMD_PTA_GEMM` starting | `pta_twin_submit` |
| `tick()` | `pta_twin_run(t, 1)` |
| The command retiring | Its status leaving "pending" |

**It reports that it is a model.** `PTA_CAPS2[31]` is set on the twin and clear on
silicon, and GRXCP's device reports `GRX_BACKEND_MODEL` from it. Nothing that runs
through it can be mistaken downstream for a chiplet working.

**What it does for time.** A GEMM occupies the twin for
`programmings × PTA_TW + shots × PTA_TS` of its own cycles, both registers. That
is a timing a test can set, and it is not a prediction of a chiplet's.

**Two ways to carry it,** and the choice is yours. Vendor the twin and the model,
as GRXCP vendors grx930's model. Or add hooks beside `vortex_dcr_write` and
`vortex_start`, leave them null by default, and clear the capability bit when they
are. We would suggest the hooks: they keep a photonic model out of the command
processor, and a backend that links nothing loses nothing.

The twin comes with its own gate: 156 checks, and three builds with one rule
removed each, which the gate has to fail.

---

## 6. Staging, and what this does not ask

1. **Assign the numbers**: the DCR base and stride, the opcode, the capability
   bit. That alone lets GRXCP write its side against something real.
2. **The Emulation CP**, behind the bit: decode the range, decode the command,
   in the ring and as a step of a bundle (§9). SimX first.
3. **GRXCP replaces its three hooks** with `vx_enqueue_dcr_read`,
   `vx_enqueue_dcr_write` and the new call. Its host round trip goes: today the
   operands are copied out of GPU memory to reach the twin and the results copied
   back, where this command reads and writes them in place.
4. **The RTL mirror**, with the port. Not asked for here. It needs the link's wire
   format, which nobody has written, and the DCR proxy's backpressure (§3).

**The acceptance test for step 2 exists.** GRXCP's gate for the route is
`tests/libs/test_grxblas_pta_chiplet.cpp`: eight cases on a 256 × 64 tile, 4,164
results through `grxblasGemmEx`, each equal bit for bit to the error model built
from what the device reports and nothing else. It runs today with the twin
attached through GRXCP's seam. Run against SimX with the twin behind the command
processor, it is the same test of the same arithmetic through your path.

**Not asked for:**

- RTL of any kind, the UCIe port, or the copy engine behind it.
- A path from a kernel to the chiplet. No ISA extension and no instruction reaches
  it. This is the host's path only.
- Interrupts. The chiplet has an interrupt line and the CP's `irq` is not yet
  wired to a host (`command_processor.md` §10, item 10), so a driver reads
  `PTA_IRQ_STATUS` when it wants to know.
- A fast path for polling a calibration. It is a `CMD_DCR_READ` a poll.

---

## 7. Open, and yours to answer

1. **The numbers.** Base and stride, opcode, capability bit. We suggested 0x400
   and 0x100, 0x0D, and bit 27 of `CP_DEV_CAPS`, the next above `SUPPORTS_QMD`.
2. **DCR range or BAR page** for the registers (§3). We recommend the range.
3. **Hooks or a vendored model** in the simulators (§5). We suggest hooks.
4. **What a malformed command does.** §4 has it retire with status 4. The queue
   also has `Q_ERROR` at 0x12C, and we found nothing in the Emulation CP that
   sets it, so we do not know your convention for it.
5. ~~**Where the result goes.**~~ *Withdrawn by §9.* §4 writes three fields back
   into the descriptor in device memory, and this asked whether a host slot would
   be better. A host slot holds one result and a list has many, so the descriptor
   it is.
6. **One queue.** Whether serial GPU and chiplet work is acceptable until
   multi-queue lands, or whether this is a reason to bring it forward.
7. **Weights that stay resident.** Version 1 names the weights in every command
   and the tile programs them every time. GRXCP's plan is heading toward weights
   that stay on the chiplet across commands. Your weight-set proposal recommended
   that software declare a weight slot in the launch descriptor and hardware
   enforce it. `target`'s bank field is that slot, and the flags beside it are
   where "this bank already holds these weights" would go. We have not defined
   that flag, because nothing has measured what it saves on the chiplet.
8. **Counting bytes.** If the unit counted what it moved each way, GRXCP's link
   model (`docs/designs/pta_chiplet_link.py`) could be checked against a run
   instead of against itself. Useful, and not part of step 2.
9. **The grant across a chain, once there is more than one queue** (§10). A
   layer that holds its operands for the next needs that next command to be the
   chiplet's next. With one queue it is. With several it is the arbiter's to
   keep.

---

## 8. What we recommend

**Assign the three numbers now, and build the Emulation CP half when it suits
you.** Concretely:

- Registers as a DCR range, routed to one target as the KMU's are. No opcode, no
  API, no change to any AFU.
- The GEMM as one descriptor command behind a capability bit, with its RTL mirror
  deferred, as `CMD_DRAW`'s is.
- That command as a member of the runtime's command list from the start (§9), so
  that a network of GEMMs is one doorbell and one completion.
- The model behind hooks that are null by default, so that a build without it is
  unchanged and advertises nothing.

**What this does not settle:** what a command is on the wire between the G100 and
the chiplet. GRXCP's board interface document lists that as owed by your port and
the chiplet's owners together, and it still is. This proposal narrows it. With the
host's half fixed, the wire has one command to carry and three ways for it to end.

**Reviewers:** this is a GRXCP proposal handed over for your judgement, under the
one-directional dependency in GRXCP's `AGENTS.md` §2. Everything in §2 was read
from your `main` at the baseline above; if any of it is stale, that is the first
thing to tell us. The twin and its gate are `src/backends/pta_chiplet/` in GRXCP.
The twin is C99 and the standard library, and its gate is one C++ file.

---

## 9. Amendment, 2026-10-04: more than one GEMM a doorbell

**What changed our mind.** GRXCP's dispatch model (`docs/designs/pta_dispatch.py`
there, its board plan's step S3) priced a GEMM on the chiplet against the same
GEMM on the G100. On the plan's own assumptions the chiplet's time for a small
network is microseconds: the two layers of GRXCP's reference network, at a batch
of 64, are 3.74 µs of tile and link. Nothing measured in this program gets a
command to a device for less. The one host round trip that has been measured, the
c930's to its own NPU, is 10.9 µs. So a call that takes one GEMM and returns is a
design in which the round trip is the cost, and §4 proposed exactly that call.

**What the G100 already has, and §4 did not use.** Read out of this repo:

- `vx_enqueue_commands` submits an ordered list as one ring batch. In
  `vortex2.h`'s words, "the runtime writes every command into the CP ring, rings
  the doorbell once, and polls completion once at the end".
- `vx_enqueue_draw` packs the same list into a resident descriptor and submits
  one `CMD_DRAW`, falling back to the ring batch where the CP does not decode it.
- `vx_command_t` has two members: a launch and a DCR write.
- In the Emulation CP a bundle's step is executed by `exec_inline_cmd_`. A launch
  waits for its drain, a DCR write, a DCR read and a cache flush apply inline, and
  anything else is a no-op.

So the mechanism for a network in one round trip exists. What is missing is a
GEMM on the chiplet as a member of the list. We wrote §4 without having read
that part of the header, and this section is the correction.

**The ask is three things.**

1. **A third member of `vx_command_t`**, `VX_COMMAND_PTA_GEMM`, carrying §4's
   info and result pointers and legal in both calls. In `vx_enqueue_commands`
   each one becomes a `CMD_PTA_GEMM` in the ring, which needs nothing beyond §4.
   A register write to the chiplet between two GEMMs is a member already: it is
   a DCR write (§3).
2. **`CMD_PTA_GEMM` as a bundle step.** `exec_inline_cmd_` starts it, and the
   walk waits for the chiplet to end it as it waits for a launch to drain.
3. **One flag in the descriptor: only after success.** Bit 16 of `target`, the
   first of its flags. A command with it set runs only if the PTA command before
   it in the same queue ended done, or if there is none before it. Otherwise it
   ends at once with status 5, "not run", and its results are untouched. Without
   the flag, a layer whose input was refused would run on whatever was in memory
   and report done.

**What it settles in §7.** Question 5, where the result goes: in the descriptor,
as §4 has it. A host slot holds one result and a list has many.
`Q_LAST_DCR_RSP` shows what one slot costs: after a bundle with several
`CMD_DCR_READ` steps, only the last response can be read. If the runtime
allocates a list's descriptors side by side, one read after the batch fetches
every result.

**A hazard this makes worth stating.** The Emulation CP retires an opcode it does
not know as a NOP, in the ring ("Unknown opcode — retire as NOP") and in a bundle
(the default arm of `exec_inline_cmd_`). A command processor without this
proposal would therefore complete a list of GEMMs having run none of them. The
capability bit is what prevents that. The descriptor is what catches it if the
bit is ever wrong: `status` is zero until the CP writes it, so a status still
zero after its command has retired means the command never ran. The runtime has
to report that as a failure and never as a success.

**What it does not give.** Two things, and the second is the larger.

- One layer's results still go to GPU memory and come back as the next layer's
  operands.
- Whatever turns one layer's sums into the next layer's operands is a kernel
  launch in the same list. The list saves that launch's round trip and none of
  its time on the device.

Keeping a network on the chiplet from its first operand to its last result needs
the chiplet's activation stage. GRXCP's plan puts one there. Its register map has
a presence bit for it and no registers, and its twin does not model it. So this
proposal cannot say what such a command computes, and does not try. It reserves
the flag bits the command would need and defines none of them:

| Bit of `target` | Reserved for |
|---|---|
| 17 | Activations are the previous command's results, through the activation stage |
| 18 | Results stay on the chiplet |
| 19 | The bank already holds these weights (§7, question 7) |

A version 1 command processor ends a descriptor with any of the three set as
status 4.

*§10 defines bits 17 and 18, and moves what 17 means.* Bit 19 is still reserved.

**What it is worth,** on GRXCP's model, for that reference network at a batch of
64. The host's round trip is taken as the c930's measured 10.9 µs, which is a
stand-in: nobody has measured yours. The launch between the two layers is 6.9 to
30.5 µs on the device, GRXCP's own simx figures on other kernels, and its
arithmetic is not priced.

| How it is submitted | Round trips | Total | The chiplet is |
|---|---|---|---|
| §4 as first proposed: a GEMM, the launch, a GEMM | 3 | 43.4 to 67 µs | 9% to 6% |
| This amendment: one list | 1 | 21.6 to 45.1 µs | 17% to 8% |
| One list, with that step on the chiplet | 1 | 14.7 µs | 26% |

The list removes two round trips, 21.8 µs on these figures, whatever the launch
costs. The last row is why the activation stage is the next thing to specify. It
is GRXCP's to specify first, in its own register map, and it would come to you
as a further amendment and not as part of this one.

**For reviewers of the amendment.** Nothing in §1 to §8 is withdrawn except
question 5 of §7. The three numbers to assign are the same three. The Emulation
CP work grows by one `vx_command_t` member, one arm of `exec_inline_cmd_` with
its wait, and one flag.

---

## 10. Amendment, 2026-10-04: the activation stage

**What changed.** §9 reserved two flag bits for a GEMM that takes the previous
one's results and keeps its own on the chiplet, and defined neither, because
GRXCP's register map had a presence bit for the chiplet's activation stage and
nothing that said what the stage computes. It says now
(`docs/designs/pta_chiplet_regmap.md` §8 in GRXCP), and GRXCP's twin runs it.
This section defines the two bits and asks for what they turned out to need: a
third bit and three fields.

**What the stage computes.** For each of a GEMM's `M × N` complete sums, with
the bias of its output `n`:

```
v = max(sum + bias[n], 0)
v = round(v / 2^shift)              a half rounds up
a = min(v, 2^(bits-1) - 1)
```

A bias, a ReLU, a rescale back to an operand, and the operand's clamp. It is the
step GRXCP's reference network takes between its layers. **The chiplet computes
it. Nothing here asks the G100 to.** The command processor carries six more
facts to the chiplet and brings one back.

**The flags,** in `target`:

| Bit | Name | Meaning |
|---|---|---|
| 16 | only after success | §9 |
| 17 | from held | This command's activations are the operands the PTA command before it held. `act_addr` is not read |
| 18 | hold | The operands this command produces stay on the chiplet for the next PTA command. `out_addr` is not written. Needs bit 20 |
| 19 | | Still reserved, for resident weights |
| 20 | activate | The results go through the stage. What the command produces is operands, not sums |

Bit 17 has moved since §9 reserved it. §9 put the stage on the command that takes
the operands. It belongs on the one that produces them, whose bias and shift it
uses. So taking them is a flag with nothing to configure, and asking for the
stage is a flag of its own.

**Bit 20 without bit 18** writes `M × N` operands to `out_addr`, in the operand
format that `format` names, one byte each in format 0, where the command would
have written sums. That buffer can be the next command's `act_addr` as it
stands. So bit 20 alone removes the kernel launch between two layers, which §9
said a list could not. Bit 18 also removes the intermediate's two crossings of
the link.

**Version 2 of the descriptor** is 80 bytes: version 1's 64, unchanged, and
then

| Offset | Field | Written by | Meaning |
|---|---|---|---|
| 0x40 | `act` | host | [5:0] the shift, 0 to 62; [13:8] the operand's width in bits, clamp included, 2 to the tile's `DIN_W`; the rest zero |
| 0x44 | `clips` | CP | Outputs the stage clamped |
| 0x48 | `bias_addr` | host | `N` signed 64-bit values in the sums' own units, or zero for no bias |

`size_version` says 80 and 2. A version 1 descriptor is still valid and asks
nothing of the stage. A command processor that decodes only version 1 ends a
version 2 descriptor as status 4, as §4 already has it.

**Held operands are the next command's or nobody's.** That is the chiplet's
rule. The command processor does not have to enforce it, only not to break it.
Any PTA command's start takes the held operands or discards them. A command
between two layers leaves nothing for the second, and so does a layer that was
refused. A calibration between two layers does not take them. Three things
follow here.

- A command with bit 17 that finds nothing held, or finds operands that are not
  its `M × K`, ends as status 2, refused. It never runs on what an earlier
  network left behind.
- So a held chain does not need bit 16: the chiplet refuses the second layer if
  the first did not end done. Bit 16 is still what protects a chain whose
  operands go through GPU memory.
- **With more than one queue, a chain has to keep the PTA resource.** Two queues
  taking turns at `RES_PTA` would put one queue's command between another's two
  layers, and the second layer would be refused. That fails safe, and it fails.
  When multi-queue arrives, a command that ends holding should keep the grant
  for its queue until that queue's next PTA command has started. With one queue,
  which is today, there is nothing to do. §7, question 9.

**What is refused** is the chiplet's to decide, and the command processor needs
to know none of it. GRXCP's map has the list: a flag on a chiplet without the
stage, bit 18 without bit 20, a shift or a width out of range, more operands to
hold than the chiplet has room for, and bit 17 with nothing held or the wrong
shape. Each ends as status 2 with the results untouched. The command processor
ends as status 4 only what it cannot parse itself.

**How a runtime knows.** Two facts, from two places. Whether the chiplet has the
stage, and how many operands it can hold, are in the chiplet's own `PTA_CAPS2`,
bit 17 and bits [24:20], read through the DCR window of §3. Whether the command
processor decodes version 2 is yours to advertise. We would suggest one more bit
of `CP_DEV_CAPS`, 28, beside §7's 27.

**In a simulator** the twin takes all of it as it stands.

| Here | The twin |
|---|---|
| Bit 20, activate | `PTA_TWIN_CMD_ACT` |
| Bit 18, hold | `PTA_TWIN_CMD_HOLD` |
| Bit 17, from held | `PTA_TWIN_CMD_FROM_HELD` |
| `act` | `act_shift` and `act_bits` |
| `bias_addr` | `bias` |
| `clips` | `clips` |

Its build has one more number, how many operands the stage can hold. Zero builds
a chiplet without the stage, and that is what a simulator should default to
until a caller asks for one.

**The call.** `vx_pta_gemm_info_t` gains the flags, the shift, the width, and a
bias buffer with its offset. `vx_pta_gemm_result_t` gains the clip count.
Nothing else in the API moves.

**What it is worth.** The row §9's table could not ask for, on the same figures
and the same stand-in for the host's round trip:

| How it is submitted | Round trips | Total | The chiplet is |
|---|---|---|---|
| §9: one list, a launch between the layers | 1 | 21.6 to 45.1 µs | 17% to 8% |
| This: one list, the step on the chiplet | 1 | 14.7 µs | 26% |

With the operands returned and not held it is a tenth of a microsecond more.

**What GRXCP has shown, and has not.** The twin's gate holds a network kept on
the chiplet to the same network brought out at every layer, element for
element, with every impairment the tile builds enabled, on an 8 × 8 tile through
three layers and on a 256 × 64 tile at the reference network's shape. A program
beside it compiles grx930's accuracy harness into itself and holds the stage to
the harness's own code on four networks. Two twins that are each wrong in one
way fail the gate. Three things are not shown:

- **No accuracy figure for a held network.** The networks in those checks are
  random. The reference network, trained, held on the chiplet, has not been run.
- **Nothing with noise against the harness.** The harness and the twin cut a
  layer into different GEMMs and each GEMM draws from its own seed, so with
  noise they are different runs. Under noise the held network is compared only
  with itself brought out.
- **The stage's time.** The twin gives it none. That takes the stage to sit in
  the shot's own pipeline, one unit a column, which is a requirement GRXCP has
  put on the chiplet and not something anyone has measured.

**For reviewers of this amendment.** Nothing in §1 to §9 is withdrawn. The three
numbers to assign are the same three, and one more capability bit if you take
the suggestion. The Emulation CP work grows by a descriptor 16 bytes longer,
three flags passed through to the model, a bias vector read from device memory,
and one count written back.
