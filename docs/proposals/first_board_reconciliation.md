# Reconciling the First Development Board — the Charter's Modular Carrier and GRXCP's Board Plan

**Status:** Proposal. No RTL and no code requested. It asks for edits to three draft
documents (§8) and for five rulings (§6), and for nothing to be built. *Amended
2026-10-13:* §10 is new, and §5.1, §5.2, §6 and §7 point to it where it changes them.
*And again the same day:* §10.5 is new, and withdraws §10.3's first item as it stood.
*And a third time:* §10.6 is new, and takes two words out of §10.5's second item.
*And its third item was settled the same day:* the PTA's converter stays at 8 bits.
*And a fourth time:* §10.7 is new, and has the same layer with a light source over it.
*And a fifth:* §10.8 is new, and says what the PTA's error at that layer is made of.
*And a sixth:* §10.9 and §10.10 are new: the reply to the note, the freeze's named
owner, and what the owner ruled. Two of §6's five rulings are made by it.
*And a seventh, 2026-10-14:* §10.11 is new: what one output scale buys at Gate F, and
what GRXCP recommends for the ruling §10.10 left open.
*And an eighth, the same day:* §10.12 is new: the canary's data set and its first two
layers, as the owner ruled them.
*And a ninth:* §10.13 is new: the canary trained, and run through the model.
*And a tenth:* §10.14 is new: the canary's golden tensors, and the owner's rulings on
FC3's declared reference and the output scale.
*And an eleventh, 2026-10-15:* §10.15 is new: Gate F's band, its class and its tail, as
the owner ruled them from the canary's model run.
*And a twelfth:* §10.16 is new: the canary's freeze package, and the review the owner
has asked of you.
*A one-page cover for §10 is in [first_board_pta_note.md](first_board_pta_note.md).*
**Decision behind it:** on 2026-10-11 the program chose the charter's modular layout
for the first development board. GRXCP's in-package arrangement stays as the later
board.
**Scope:** `docs/grxgpu_product_family_charter.md` and
`docs/grxgpu_engineering_task_list.md`, each version 0.1 of 2026-10-10, and
`docs/grxgpu_first_board_demo.md`, which carries no version (read, not changed).
They were read on 2026-10-11 as drafts in the team's working tree and are not yet
on a branch of this repository, so this proposal quotes what it answers and does
not link to it. Nothing here patches grxgpu.
**Baseline:** grxgpu `main` at `1d761117f`; GRXCP `main` at `c789929`; grx930 `main`
at `8a0723f`.
**Origin:** GRXCP's board plan (`docs/designs/board_program_plan.md`), decisions B1
to B17, and its interface control document (`docs/designs/board_icd.md`). The PTA's
register map is `docs/designs/pta_chiplet_regmap.md` there. Its error model and its
calibration engine are in grx930 (`c930/doc/pta_error_model_design_note.md`).
**Related:** [pta_chiplet_host_path.md](pta_chiplet_host_path.md) and
[pta_weight_set_policies.md](pta_weight_set_policies.md), both written for the
arrangement that §3.2 moves to the later board.

---

## 1. What this is, and why now

Two sets of documents now describe "the board", and they describe different boards.

The charter and its first-board demo were written without GRXCP's plan in view, and
are careful about it: they mark the PTA's compute method, its numeric format, its
calibration and its interface as things still to be selected or proven. GRXCP's
plan has settled most of those over the last three weeks, on paper and in a model,
for a board the charter does not draw. Neither set mentions the other. Before
either team builds to its own, they have to be one.

The program has chosen: **the charter's layout is the first board.** This proposal
does three things with that.

1. It sets out where the two boards differ, and what each difference becomes
   (§2, §3).
2. It gives the charter the PTA facts it lists as open and that are decided (§4).
3. It says how the demo's PTA gates read from the PTA's side, what would have to
   be defined before anyone could pass or fail them, and what we can and cannot
   yet say (§5).

**What it is not evidence of.** There is no PTA. Everything GRXCP and grx930 hold
about one is a decision on paper or a measurement in a model, and §4 says which is
which. Nothing below claims a photonic device, a measured module or a product
figure.

---

## 2. The two boards

| | GRXCP's board plan, on `main` | The charter and the demo, drafts of 2026-10-10 |
|---|---|---|
| Layout | Two packages: the GRX930, and a GPU package holding the G100 die and the PTA chiplet (B1) | A carrier with the GRX930 SoC as host, and the G100 and the PTA as separately attachable modules |
| Where the PTA sits | Inside the GPU package, joined to the G100 die by UCIe (B4) | Its own module on the board |
| Who drives the PTA | The G100: its driver owns the PTA's registers, and a copy engine feeds the tile from GPU memory (B4, B7, B9) | The CPU: it converts the G100's output and hands FC3 to the PTA |
| CPU to GPU | CXL 2.0 over a PCIe 5.0 x16 link, the GRX930 as host and the G100 as a Type-2 device (B3) | Open: "Do not assume PCIe or a specific generation is implemented" |
| The board before silicon | An FPGA platform with CXL hard IP, the PTA on it as the error-model tile (B6) | A modular carrier; FPGA or ASIC status to be confirmed (charter §9, item 4) |
| What stands in for the PTA | The error-model tile, by name, with a bit in a register that says so | A physical module; "host emulation does not count" |
| Calibration | Every six minutes while the tile runs (B15) | A cold-start cost: "PTA setup/calibration if required" |
| What the PTA is held to | Points of accuracy lost on a named workload | A raw-output error and a class agreement |

The first five rows are layout. The decision settles them, and §3 says how. The
last three are not layout and no decision settles them: they are §3.5 and §5.

---

## 3. What each difference becomes

### 3.1 Where the PTA sits

**First board: its own module**, as the charter has it. GRXCP's B1 and B4 become the
later board's.

The charter already allows for that later board: "consider GPU package integration
only after a measured workload/system benefit and a credible thermal, memory, test
and package plan". GRXCP's plan is that arrangement worked through as far as paper
goes: the split of packages, what the interface chip holds, the link's sizing, a
floorplan bound.

**Asked:** that the charter's PTA row and its §6 name the in-package chiplet as the
arrangement the module is expected to become, and require that the module's
interface not foreclose it. Concretely that is one register map and one GEMM
contract for both attachments (§3.3).

### 3.2 Who drives it

**First board: the host CPU submits FC3 to the PTA module**, as the demo draws it.

GRXCP's B7, the PTA's registers as MMIO behind the GPU's CXL.io function, and B9,
the PTA as a device whose parent is its GPU with its operands in GPU memory, become
the later board's. So does what was asked of the G100 in
[pta_chiplet_host_path.md](pta_chiplet_host_path.md): a DCR range, one command and
one capability bit.

**Nothing in that proposal is needed for the first board, and nothing in it is
withdrawn.** No number it asks for has to be assigned now. It is the path the later
board uses, and it should not be built ahead of that board on this one's account.
[pta_weight_set_policies.md](pta_weight_set_policies.md) is in the same position.

On GRXCP's side the change is small and is ours. The PTA driver ends in three
hooks: read a register, write one, and submit a GEMM and learn how it ended. On the
later board the calls that proposal asks for would fill them. On the first board a
transport from the GRX930 host does (§7).

### 3.3 One register map, two attachments

The PTA's register block already exists in three places, laid out the same in each.

| Where | State |
|---|---|
| On the c930 core, at `0x4000_0100` | Built, in RTL |
| The chiplet's window | Drafted, for a page of the GPU's BAR |
| Behind GRXCP's C model of the chiplet, the "twin" | Built; GRXCP's driver and runtime are gated against it |

It carries what the charter's shared platform contract asks of every engine (§4,
"Device discovery: stable product/engine IDs, capability/version registers,
precision and shape limits ... and fault state"):

| Register | What it says |
|---|---|
| `PTA_ID` | A magic, "PTA", and the map's version |
| `PTA_CAPS0` | The tile's rows and columns, and its operand and accumulator widths |
| `PTA_CAPS1` | Which impairments are built, how many weight banks, and the widest activation, weight and ADC settings |
| `PTA_CAPS2` | The shot rate as built; whether the calibration engine and the activation stage are present; and bit 31, "this is the twin and not silicon" |

**Asked:** that this map be the PTA's discovery contract on the first board,
whatever bus it is reached over. If something in it is wrong for the charter's
purposes we would rather hear that than see a second map specified.

### 3.4 Links

**First board: the charter's rule stands.** The connector and the protocol are
chosen after the traffic is measured, and B3's CXL 2.0 over PCIe 5.0 is the later
board's. Two facts for whoever sizes the PTA module's link.

- **The demo's traffic is nothing.** FC3 at a batch of 16 is 1,024 bytes of
  activations in and 256 sums out, a job.
- **The demo is not the sizing case.** GRXCP's link model (`pta_chiplet_link.py`,
  the board plan's step X2) has a 4096 × 4096 layer at a batch of 64, on the
  128 × 64 tile at 1 GS/s, needing 130 GB/s in and 8 GB/s out. That is a model's
  prediction and has been measured on no hardware.

A connector chosen on the demo's kilobyte will carry the demo and not the product.

**Asked:** that the board's PTA link decision record which of the two it was sized
for.

### 3.5 What the PTA module is, on the first board

The charter's first demonstrator for the PTA is an "Independently addressable
electro-photonic module or measured prototype connected to the board". The demo
adds: "Do not silently emulate PTA on the CPU and count that as a PTA pass", and
"host emulation does not count".

There is no photonic module, and the task list's E-303 rightly files one under
discovery. What exists:

| | What it is | Where | State |
|---|---|---|---|
| The error model | The contract a tile's arithmetic is held to: its quantisers, receiver and shot noise, weight programming error, drift and crosstalk | grx930, the design note's §4, with a C reference | Built |
| An emulated tile | The c930's 8 × 8 array with that model in its datapath | grx930, RTL | Built, and held to the C reference (the note's gates P0 to P6) |
| A calibration engine | The probes and trims that hold a drifting tile | grx930, RTL | Built, and agrees with the C reference cell for cell (gates P7 to P9) |
| The chiplet's twin | The model behind the chiplet's register map, at 128 × 64 | GRXCP, C | Built. **No RTL at that geometry** |
| A physical tile | | | None |

Read strictly, the demo's full chain cannot be run until E-303 delivers, and the
charter's Stage 3, the common runtime on the board, waits with it.

**Proposed: a third category beside "PTA" and "host emulation", a PTA stand-in.**
It is the emulated tile on its own module, an FPGA, behind the PTA's register map
and reached over the module's real link, reporting `PTA_CAPS2[31]`. It is separate
hardware doing FC3's arithmetic under the PTA's contract, so it exercises
everything the integration gates test: discovery, the job and buffer contract, the
format conversion, completion, faults, and the soak. It is not a photonic device,
and so:

- it may pass Gate F's integration items and the reliability package;
- its raw outputs are checked exactly and not to a tolerance (§5.1);
- its latency and energy are an FPGA's, and are reported as a stand-in's;
- C3's product-value targets in Gates L and E are **not evaluable** on it;
- the run manifest records the bit, and no report calls the run a PTA result.

This is GRXCP's own rule, applied to the board: an emulation is allowed when a
property reports it, and never behind an interface that implies hardware.

**A gap, stated.** The emulated tile exists in RTL at the c930's 8 × 8 and not at
the chiplet's 128 × 64. A stand-in at the working geometry is RTL that nobody has
built and nobody owns. An 8 × 8 one would run FC3 as 16 tiles and give an 8 × 8
tile's numbers, which are not a 128 × 64 tile's: each tile's sums pass a converter
of their own. Either way the reference names its geometry.

---

## 4. What the charter lists as open, and what is decided

The charter's PTA exit criteria (§6) begin: "Select the initial optical-compute
mechanism and supported numeric representation". For the first board those are
settled in GRXCP's plan. **Every row below is a decision on paper, costed in a
model. None is a device, and none has been measured on one.**

| The charter asks for | Decided | Where |
|---|---|---|
| The compute mechanism | A bank of ring weights lit by a comb; a weight is signed by a balanced pair of photodiodes | B12, B13 |
| The photonic platform | Thin-film lithium tantalate, a Pockels material | B5 |
| The geometry | 128 inputs by 64 outputs a shot | B10 |
| The shot rate | 1 GS/s | B11 |
| The numeric representation | 8-bit operands. Weights are 6-bit codes held behind an 8-bit DAC, activations 6-bit, and each column has an 8-bit ADC | B14, B16 |
| The error budget, "version 2" | Receiver noise within a quarter of an LSB of that 8-bit ADC, rms; 30 photons per such LSB; weight programming error of 1 LSB of an 8-bit weight, rms; crosstalk between neighbouring inputs of 2% | B14 |
| The optical and electronic split | The interface chip holds the converters, the resident weights, the activation buffers, the accumulation and the calibration engine | B4 |
| Calibration and drift | Every six minutes: a trim for each cell and a read of the comb's lines, 70.0 µs at the most, one part in 5.1 million | B15, and `pta_chiplet_calibration.md` §3 |
| The source | Noise within 1% rms a shot for the lines together and 5% for a line on its own; lines level to 20%, read at each calibration and corrected on the weights | B16 |
| The software view | A GEMM-only device behind capability registers, whose results are reported as analog and never silently | B9, and GRXCP's `AGENTS.md` §3 |
| The networks | Trained for the tile: eight epochs with noise of 10% on the sums | B17 |

**What the tile costs, in the unit it is budgeted in:** points of accuracy lost
against the same network on its host. On the working tile at version 2, for five
networks a data set of B17's kind, each 784-100-10 with both layers on the tile:

| | MNIST | Fashion-MNIST | MNIST, inverted |
|---|---|---|---|
| As budgeted | 0.14 ± 0.04 | 0.53 ± 0.07 | 0.47 ± 0.06 |
| At the end of a six-minute cycle, with the source lit | 0.20 ± 0.04 | 0.63 ± 0.09 | 0.82 ± 0.09 |

**Measured in a model**, by grx930's harness, and held in GRXCP's
`docs/designs/pta_reference_rows.py`.

**For the demo's FC3**, which the demo leaves as a "PTA-native supported
representation":

- 64 → 16 fits one 128 × 64 tile. It is one shot a vector and sixteen a batch.
- The conversion before it is a truncation. The G100's int8 output after the ReLU
  is not negative, and the tile takes its top 6 bits, which is the contract's
  quantiser.
- Its weights are 6-bit, and **should be trained for the tile**. On the one bright
  workload we have, a network that was not loses 0.71 ± 0.10 of a point as budgeted
  where B17's lose 0.47 ± 0.06. On the other two the difference cannot be seen.
- A fixed-weight classifier's weights are resident. They are programmed once, in
  the cold path, and not for each job.

---

## 5. The demo's gates, from the PTA's side

### 5.1 Gate F: the raw outputs

The demo holds FC3's raw outputs to "normalized RMS error ≤ 1.0% and maximum
absolute error ≤ 2.0% of the reference full-scale output", against "its
declared-format reference". Three things.

**For a stand-in the check can be exact, and should be.** The error model is
deterministic in its seed. A reference built from the capability registers, the
seed and the GEMM's index reproduces a conforming tile's output bit for bit. That
is how GRXCP gates the twin today: 4,164 results, each equal to the model, in
`tests/libs/test_grxblas_pta_chiplet.cpp`. It was also the gate GRXCP's plan held
its own first board to. So for a stand-in the proposal is zero differing outputs
and no tolerance. That is stricter than 1%, and it is the only check that tells a
correct emulated tile from a broken one that happens to land close.

**For a physical module a tolerance is right, and it is a band.** No seed
reproduces a device's noise. What is bounded then is the module against its
budget, above and below. GRXCP's rule (`AGENTS.md` §4) is that a bound on an
analog error is a prediction: an error far under the prediction is as much a sign
of a wrong measurement as one over it.

**The 1.0% has no unit yet.** The demo normalises the largest error by full scale,
and does not say what the RMS is normalised by. In the unit grx930's harness
reports, the rms error of a layer's sums over the rms of the reference's, a PTA
layer at version 2 is at 7 to 8%:

| | MNIST | Fashion-MNIST | MNIST, inverted |
|---|---|---|---|
| The last layer's own error, rms over rms | 7.4% | 7.9% | 7.1% |

That is B17's networks on the tile as budgeted, 25 runs a data set, read from the
lines grx930's `refrows` sweep wrote. It is **measured in a model**. Its reference
has unquantised activations, so the figure includes the 6-bit quantiser as well as
the noise. Against full scale it would be smaller, by the ratio of a layer's rms
output to its full scale, and we have not computed that ratio for any network, the
demo's least of all. **So we cannot say whether the tile passes 1.0% and 2.0%, and
neither can the demo as it is written.**
*Since 2026-10-13 a stand-in for the demo's classifier has been run (§10). On three of
four readings of the 1.0% the tile as budgeted is over it in every data set's mean, and
on every reading it is over the 2.0% in every run.*

**Asked:** that the demo name the normaliser. ~~We would propose the reference's own
rms, which does not move with how much headroom a format leaves.~~ *It does move with
which vectors are frozen. §10.3 proposes the declared output format's own step.*

### 5.2 Gate F: class agreement

The demo asks that the final class agree with the reference on at least 99.5% of
1,000 vectors. From the same runs, the class the tile gives against the class the
network's host gives:

| | MNIST | Fashion-MNIST | MNIST, inverted |
|---|---|---|---|
| Agreement with the host | 99.3% | 96.4% | 98.2% |

These are not the demo's classifier. They have two layers on the tile where the
demo has one of three, ten classes where it has sixteen, and 784 inputs where it
has 64. Nothing we hold says the demo's classifier passes 99.5% or fails it. What
the table does say is that 99.5% is not something the PTA meets as a matter of
course, and that it turns on the workload more than on the tile: the same tile is
at 96.4% and at 99.3%.
*Those figures are against the network's host. The demo holds the class to its
declared reference's, and §10.2 has that, for a stand-in of the demo's own shape.*

**Asked, and offered:** freeze the classifier's weights and its 1,000 inputs, or
give us FC1 and FC2 and let FC3 be trained as B17 has it. grx930's harness will
then run it through the error model at version 2 before the thresholds are
ratified. The demo's own rule is that thresholds are approved before results are
seen and are not loosened after. A model's figure in hand beforehand is what makes
a threshold a prediction.

### 5.3 Calibration is in the warm path

The demo counts "PTA setup/calibration if required" in the cold start and nowhere
else. B15 has the tile calibrated every six minutes for as long as it runs. Three
things follow.

- **Warm latency.** A job that meets a calibration waits for it. At the chiplet's
  rates that is 70.0 µs at the most. It is bounded, and the warm boundary should
  declare it. On a stand-in the engine's time is the FPGA's, not that figure.
- **The soak.** Twenty-four hours cross 240 calibrations, so the soak is the first
  test at the level of a system that B15's interval has had. Its "defined recovery
  outcome" should say what a calibration that fails is: the engine raises
  `DRIFT_ALARM` in the status register when a trim cannot reach what it measured.
- **Energy.** It is one part in 5.1 million. That is worth a line, so that it is
  stated and not omitted.

### 5.4 Gates L and E

The boundary the charter draws for the PTA's energy, with the laser, the drivers,
the converters, the control and the calibration inside it, is the one GRXCP's plan
budgets within. It has the interface chip at 0.64 to 4.18 W at version 2, derived
from a published survey of converters, and a laser of watts: B5 has 0.7 to 7 W for
the working tile at version 1's light, and version 2 asks twice the light.
**Neither is a measurement, and no figure in joules a batch exists for the demo.**

One piece of arithmetic on those decisions, offered as that and no more. FC3 at a
batch of 16 is sixteen shots, which is 16 ns of the tile's time at 1 GS/s. At that
size what the PTA spends on a batch is its standing power for as long as the job
is on the board. So the demo's shape tests the integration, which is its stated
purpose, and cannot by itself make the PTA's case or unmake it. The charter's §5
already asks separately for "a tensor workload suitable for PTA evaluation", and
that is the right place for the case.

On a stand-in, Gates L and E are not evaluable for the PTA at all (§3.5).

---

## 6. What this asks you to rule on

1. **The stand-in** (§3.5). Whether an emulated tile on its own FPGA module, behind
   the PTA's register map and reporting that it is a model, may take the PTA's
   place in the first board's integration runs, with the limits listed there.
2. **The register map** (§3.3). Whether the PTA's existing map is its discovery
   contract on the first board.
3. **Gate F's raw check** (§5.1). The normaliser for the RMS error; and, for a
   stand-in, equality with the seeded reference in place of a tolerance. *§10.3 adds
   what we would propose for the 1.0% and for the 2.0%. Ruled on 2026-10-13 for the
   normaliser and for the 1.0%, which becomes a band: §10.10.*
4. **FC3's weights** (§5.2). Who trains them, and whether they are trained for the
   tile. *Ruled on 2026-10-13: grx930's harness, for the tile (§10.10).*
5. **The PTA module's link** (§3.4). Which bus it is from the GRX930 host. That is
   yours and the board lead's to choose, and we need it to write the transport.

---

## 7. What GRXCP and grx930 owe as a result

Ours to do, and listed here so that it is on record and not assumed.

| What | Whose | State |
|---|---|---|
| The decision recorded in GRXCP's board plan, as B18: the first board is the charter's, and B1, B3, B4, B6, B7 and B9 are the later board's | GRXCP | Recorded alongside this proposal |
| A first-board section in the interface control document | GRXCP | Waits on §6, question 5 |
| A transport for the driver's three hooks from the GRX930 host, and the PTA's parent device on a host-attached module | GRXCP, grx930 | Waits on §6, question 5 |
| The demo's classifier run through the error model at version 2 | grx930's harness, GRXCP | Waits on §6, question 4. *A stand-in for it was run on 2026-10-13: §10. Question 4 was ruled the same day (§10.10), and it now waits on the canary's data set and its first two layers* |
| A stand-in at 128 × 64, in RTL | Unowned | Waits on §6, question 1 |

---

## 8. Edits asked of the three drafts

| Document | Where | Edit |
|---|---|---|
| Charter | §2, the PTA row; §6, PTA | Cite GRXCP's board plan for what is decided (§4 here), marked as decisions in a model. Name the in-package chiplet as the later arrangement the module must not foreclose |
| Charter | §3, "PTA connection" | Add the stand-in as a named, limited option, if §6's first question is ruled yes |
| Charter | §4, "Device discovery" | Name the PTA's register map |
| Charter | §6, PTA | "No PTA RTL ... is asserted" is right of a product. An emulated tile and a calibration engine do exist in grx930's RTL, and saying so costs the sentence nothing |
| Demo | §2, FC3's row | The format of §4 here: 6-bit weights trained for the tile, 6-bit activations, an 8-bit ADC, one 128 × 64 tile, and the geometry named in the golden manifest |
| Demo | §2, "End-to-end boundary" | Calibration every six minutes is in the warm path, and bounded |
| Demo | §4, Gate F | Name the RMS normaliser. For a stand-in, equality with the seeded reference. Ratify the tolerance and the 99.5% after the classifier has been run through the model |
| Demo | §4, Gates L and E; §5, item 5 | C3 on a stand-in gives "integration demonstrated" and cannot give "product-value target met" |
| Task list | E-303, E-401 | E-401 may proceed on a stand-in before E-303 delivers, within those limits |

---

## 9. What this is not

**A photonic device, or evidence of one.** Every PTA figure here is a decision or a
model's output, and each says so where it stands.
**A claim that the PTA fails the demo's gates, or passes them.** §5 says what would
have to be defined and run before either could be said.
**A design for the first board's links.** That is the charter's Stage 1 and the
board lead's.
**A withdrawal of anything already proposed.** The two earlier PTA proposals
describe the later board and stand for it.
**A change to grxgpu.** It asks for rulings and for edits to drafts, and patches
nothing.

---

## 10. Addendum, 2026-10-13: a stand-in for the demo's classifier

§5 said we could not tell whether the tile passes Gate F, and offered to run the demo's
classifier through the error model once it exists. It does not exist yet. So grx930's
harness was given a way to run a network that is only partly on the tile
(kubeworkz/grx930#67), and **a stand-in for the classifier was run: ours, not yours.**
It is here so that the thresholds can be set with a model's figure in hand. Every figure
below is **measured in a model**, and every one moves with the classifier, as the three
columns show.

**What was run.** A 64-64-64-16 classifier, trained by grx930's harness on the three
data sets GRXCP uses: MNIST, Fashion-MNIST and MNIST with its pixels inverted, each
image pooled from 28 × 28 to 8 × 8, which is 64 inputs. It has sixteen outputs, of which
ten are ever a label. FC1 and FC2 are computed exactly, as a digital engine has them.
FC3 runs on one 128 × 64 tile at version 2 (§4), one shot a vector. Its declared-format
reference is the exact product of FC2's output at the tile's 6 bits and FC3's weights.
Five networks trained for the tile as B17 has it, and five draws of the tile's noise,
which is 25 runs a data set; on the first 1,000 test images, the size of your acceptance
set, and on all 10,000.

**Where it is not your classifier.** Its weights are 6 bits where the demo's are int8.
Its data are ours. The NPU and the G100 are taken as exact, and the conversions between
layers are the harness's own rescale. And no light source is modelled: GRXCP's source
rows (B16) would add to every figure here. *They are modelled since the same day:
§10.7.*

### 10.1 Gate F's raw error

| As budgeted, the first 1,000 images | MNIST | Fashion-MNIST | MNIST, inverted | Gate F asks |
|---|---|---|---|---|
| rms error, % of the reference's rms | 4.52 | 4.67 | 4.24 | 1.0%, of what it does not say |
| % of the largest the reference is | 1.72 | 1.42 | 1.54 |  |
| % of the converter's full scale, 127 steps | 1.40 | 1.12 | 1.22 |  |
| in steps of the 8-bit converter | 1.78 | 1.42 | 1.55 |  |
| Largest error, % of the largest the reference is | 7.69 | 7.53 | 7.16 | 2.0% |
| % of the converter's full scale | 6.24 | 5.96 | 5.67 |  |
| in the run's own rms errors | 4.5 | 5.3 | 4.6 |  |

**The tile is about a step and a half of its output converter off its declared format.**
1.42 to 1.78 steps rms, of an 8-bit converter. With no noise at all it is off by 0.29 of
a step, which is the converter's rounding. That figure does not move with the test
vectors, and the next three do.

**So the 1.0% is passed or failed by what it is divided by.** Four readings, and the
runs of the 150 on the first 1,000 images, both kinds of network, that are within 1.0%
on each:

| The rms error, as a share of | As budgeted | Runs of 150 within 1.0% |
|---|---|---|
| The reference's own rms | 4.2 to 4.9% | 0 |
| The largest value the reference takes in the test set | 1.4 to 1.8% | 0 |
| The output converter's full scale, 127 steps | 1.1 to 1.4% | 25 |
| Its whole span, 254 steps | 0.56 to 0.70% | 150 |

The demo says to "define full scale from the frozen golden manifest". If that is the
largest value the reference takes, it is the second row, and it moves with which vectors
were frozen. If it is the output format's own range, it is the third or the fourth.

**The 2.0% on the largest error is met by no run, on any reading.** As budgeted the
largest error of a run's 16,000 outputs is 7.2 to 8.4% of the largest value the
reference takes, 5.2 to 6.2% of the converter's full scale and 2.6 to 3.1% of its span.
The least any of the 300 runs has is 6.1% of the largest the reference takes.

**It could not be, for an analog engine, while it is twice the rms bound.** A largest
error is a tail. Here it is 4.5 to 5.3 of the run's own rms errors, and the largest of
16,000 figures with Gaussian noise on them sits about 4.4 rms out. A digital engine,
whose error is bounded by its rounding, meets a largest-error bound at twice its rms
bound: the format alone has 0.42 to 0.71% where nothing is clipped. A noisy one does
not, and the more outputs are looked at the further out its largest is.

**And one clipped output looks like a very large error.** The harness sets the output
converter's range on 1,000 training images, to pass all but one sum in ten thousand. 5
of the 30 networks then have a reference that reaches past the converter's full scale
somewhere in the 10,000 test images, and 2 in the first 1,000. With no noise at all,
their largest error is 2.2 to 24.1% of the largest the reference takes. That is a fault
in how the range was set, and not noise. A range that clips nothing costs a larger step.
~~We did not run one.~~ *Run the same day: §10.5.*

### 10.2 Gate F's class agreement

The demo holds the final class to "the declared reference". We take that as the class
the declared-format reference gives, and report the class the high-precision host gives
beside it, as the demo asks.

| The first 1,000 images | MNIST | Fashion-MNIST | MNIST, inverted | Gate F asks |
|---|---|---|---|---|
| The tile as budgeted gives its declared reference's class on | 99.49% | 96.85% | 99.10% | 99.5% |
| Runs of 25 at 99.5% or more | 13 | 0 | 1 |  |
| The least of any run | 99.1% | 95.3% | 98.6% |  |
| The format alone, with no noise, gives that class on | 99.76% | 98.58% | 99.64% |  |
| Networks not trained for the tile, as budgeted | 99.25% | 96.01% | 98.80% |  |
| The tile as budgeted gives the high-precision host's class on | 99.34% | 96.46% | 98.79% |  |
| How often the declared reference is right | 96.52% | 84.76% | 94.38% |  |
| How often the high-precision host is right, of 10,000 | 97.09% | 83.82% | 95.39% |  |

**On one data set of three the stand-in is at the gate, and a draw decides which side.**
On pooled MNIST the mean is 99.49% and 13 runs of 25 pass. On the other two it is under,
by 2.6 points on Fashion-MNIST and 0.4 on the inverted set.

**A tile with no noise fails 99.5% on one of them.** The format alone differs from its
declared reference by the converter's rounding and by what it clips. That moves the
class on 0.24, 1.42 and 0.36% of the first 1,000 images.

**It turns on the classifier's margins.** The same tile is at 99.5% and at 96.9%. And
training for the tile's noise, as B17 does, is worth 0.18, 0.86 and 0.38 of a point on
10,000 images, on the same raw error: 4.2 to 4.7% of the reference's rms against 4.3 to
4.8%.

### 10.3 What we would now propose for Gate F

These replace what §5.1 proposed, which was to normalise by the reference's own rms. The
thresholds are yours. What follows is what we would set them against.

1. **State the rms bound in steps of the PTA's declared output format**, or as a share
   of that format's full scale, with the full scale written as a number in the golden
   manifest. It then does not move with which vectors were frozen. The model's figure
   for a tile at version 2 is 1.42 to 1.78 steps rms, which is 1.12 to 1.40% of a
   127-step full scale.

   *Withdrawn as it stands, 2026-10-13. It does not move with the vectors, and it does
   move with the range: a bound in steps is met by declaring a wider one. §10.5 has the
   runs and what replaces it.*

2. **Make it a band.** A module that measures far under the model's figure is as likely
   to be a wrong measurement as one that measures over it (GRXCP `AGENTS.md` §4).

3. **Restate the largest-error bound for an engine with noise.** Either as a multiple of
   the rms bound that fits the number of outputs checked: here the largest of a run's
   16,000 outputs is 4.12 to 6.35 of that run's rms errors, with 3 runs of 150 past six
   and none past seven. Or as a count of outputs allowed past a stated error.

4. **Check clipping by itself, and require none.** The golden manifest's full scale
   should be at least the largest value the reference takes, and a clipped output should
   fail as a range fault, not be averaged into an error figure. *And no wider than that:
   §10.5 has what a bit of headroom costs.*

5. **Set the 99.5% after the frozen classifier has been through the model**, and require
   FC3's weights to be trained for the tile. This is §6's fourth question, and it now
   has a size.

**For a stand-in none of this changes §5.1's first point.** An emulated tile is
deterministic in its seed, and is checked for equality with its seeded reference, with
no tolerance.

### 10.4 What this is not

**Your classifier, or a pass or a fail of it.** It is a network of the same shape on
data sets we had. **A device.** Every figure is a model's. **The chain.** FC1 and FC2
are exact here. **A lit tile.** No source noise is in these figures. *§10.7 has them
lit.* **A remedy.**
Nothing here makes the largest error smaller: it says where it comes from. **A
prediction we got right.** Twelve were written down before the runs, for these networks,
and four held as written. The ones that failed put the largest error too low and
Fashion-MNIST's class agreement too high.

**Where it is held.** grx930 `c930/doc/pta_error_model_design_note.md` §5, "The first
board's last layer", and `sim/pta_mnist.sh ... chain`. GRXCP
`docs/designs/pta_board_chain.py`, which holds every run's figures, reproduces the
harness's tables cell for cell, and asserts each figure quoted here. The harness trains
its own networks. Running yours needs its weights in the harness's format, which is a
small converter that nobody has written.

### 10.5 The range that clips nothing (added 2026-10-13)

§10.1 found that one clipped output reads as an error of 2 to 24%, and said a range that
clips nothing had not been run. It has now (kubeworkz/grx930#68). It is the same
stand-in, ours and not yours, **measured in a model**, with everything §10.4 says of it.

**What was run.** The output converter's range set as the demo says, from the golden
manifest: the smallest step at which the largest value the declared-format reference
takes, over the vectors that are run, fits the converter's 127 codes. And the same with
one bit of headroom, so that the largest fits 63. Both against the range the harness had
been setting on training images.

**What a wider range costs, as it is modelled.** GRXCP budgets the tile's noise in LSB
of the output converter: the receiver's at a quarter of an LSB, the light at thirty
photons an LSB. A converter's range is hardware, and an output is brought inside it by
turning the light or the gain down. So a wider range is a larger LSB and more noise in
the output's own units. A converter with one more bit at the same LSB is the other way
to buy range. That is a hardware choice, and ~~is not modelled here~~ *was run the same
day: §10.6.*

| The reference networks, as budgeted: MNIST, Fashion-MNIST, inverted | Range from training images | Fitted to the manifest | One bit of headroom |
|---|---|---|---|
| Networks of five whose step grows | none | 1, 2, 0 | 5, 5, 5 |
| Most outputs clipped in a run, of 160,000 | 27, 161, 0 | 0, 0, 0 | 0, 0, 0 |
| Largest error, the most in any run, % of the largest reference value | 8.97, 24.05, 8.59 | 8.97, 8.95, 8.59 | 12.70, 11.84, 11.40 |
| rms error, % of the reference's rms | 4.46, 4.67, 4.18 | 4.64, 5.05, 4.18 | 5.75, 6.75, 5.23 |
| rms error, in steps of its own converter | 1.83, 1.43, 1.60 | 1.67, 1.15, 1.60 | 1.03, 0.77, 1.00 |
| rms error, % of its own converter's full scale | 1.44, 1.13, 1.26 | 1.32, 0.91, 1.26 | 0.81, 0.61, 0.79 |
| The declared reference's class, % of 10,000 images | 99.59, 96.78, 99.23 | 99.55, 96.20, 99.23 | 99.26, 93.20, 98.83 |
| On the first 1,000: runs of 25 at 99.5% or more | 13, 0, 1 | 13, 0, 1 | 3, 0, 0 |
| Top-1 accuracy, % | 96.97, 83.47, 95.19 | 96.95, 83.35, 95.19 | 96.85, 82.41, 95.02 |

**Fitted to the manifest, nothing clips.** Not one output, in any of the 600 fitted
runs, with the tile's noise or without it. Fitting changes the step of 5 networks of 30
on 10,000 images and of 2 on the first 1,000, by one bit each. A tile with no noise is
then off by half a step at the most, 0.40 to 0.77% of the largest reference value, and
is inside the 2.0% in every run.

**It does not bring a tile with noise inside the 2.0%.** The largest error is then the
noise's alone: 7.2 to 8.4% in a data set's mean and 9.7% at the most, where it was
24.1%. The least any of the 300 runs has is 6.1%. §10.3's third item stands by itself
now.

**Where the fit was needed it costs a fifth more error.** A network whose step grew by a
bit has 1.20 to 1.24 times the rms error it had. Its class agreement goes with it: on
10,000 images the three data sets are at 99.55, 96.20 and 99.23%, where they were at
99.59, 96.78 and 99.23%.

**Headroom is not free.** One bit more than fits costs every network 1.21 to 1.38 times
its fitted rms error. Class agreement falls to 99.26, 93.20 and 98.83%, and top-1
accuracy by 0.10, 0.94 and 0.17 of a point. On pooled MNIST's first 1,000 images the
runs at 99.5% go from 13 of 25 to 3. A noiseless tile that only rounds twice as coarsely
is at 99.59, 95.31 and 99.43%.

**And a wider range reads better as a share of full scale.** The table's fifth and sixth
rows fall from left to right while its fourth rises. Of the 150 runs as budgeted, both
kinds of network, 20, 45 and 150 are within 1.0% of the converter's full scale as the
range grows, and none is within 1.0% of the reference's rms at any of the three. A bound
in steps, or as a share of full scale, is met by declaring a wider range, with a tile
that is worse.

**What this changes in §10.3.**

1. **Its first item is withdrawn as it stood.** It asked for the rms bound in steps of
   the declared output format. That is safe only if the range is not the engine's to
   choose.

2. **Fix the output range in the golden manifest, by rule**: the smallest step at which
   the largest value the reference takes fits the format, and no wider. Then nothing
   clips, and the range is not a free parameter. This sharpens the fourth item.

   *"And no wider" is taken back, 2026-10-13. A wider range at the same step costs no
   error. §10.6 has the runs and what is left of this item.*

3. **State the rms bound against the reference**, its rms or its largest value. With the
   range fixed by the rule above a bound in steps says the same thing, and may be given
   beside it. The model's figures for a tile at version 2 with a fitted range, on the
   first 1,000 images of the networks trained for the tile: 4.24 to 4.85% of the
   reference's rms, 1.47 to 1.72% of its largest value, 1.27 to 1.78 steps.

4. **The second, third and fifth items stand**: a band and not a ceiling, a
   largest-error bound written for an engine with noise, and the 99.5% set after the
   frozen classifier has been through the model.

**What this is not.** A range a board could set without its golden manifest: this one is
fitted to the very vectors it is then run on, which is what the demo describes. A
converter with more bits. A remedy for the largest error. And of nine predictions
written before these runs, four held: the cost of a bit of range was put at 1.3 to 1.5
times and is 1.2 where the fit needs it and 1.3 for a spare one, and what a spare bit
does to the class was put too low. It is held in grx930's design note §5, "The first
board's last layer, with a range that clips nothing", and in GRXCP's
`docs/designs/pta_board_range.py`.

### 10.6 A converter with one more bit (added 2026-10-13)

§10.5 said that a converter with one more bit at the same LSB was the other way to buy a
range that clips nothing, and that we had not modelled it. grx930 has now run it
(kubeworkz/grx930#69): the same stand-in classifier, tile, noise and draws, with the
PTA's output converter given nine bits in place of eight. A ninth bit can be spent two
ways, and both were run.

- **On range, at the same LSB.** The step stays what the engine's own rule gave it from
  training images, and the converter has 255 codes where it had 127. Each output gets
  the light it had and the noise it had. The receiver in front of the converter has to
  stay linear over twice the signal.

- **On finer steps, over the fitted range.** The range is §10.5's, fitted to the
  manifest, in steps half the size. The receiver is asked for nothing new. Where the fit
  had to widen the range, each output still gets half the light, as it does with eight
  bits.

| The reference networks, as budgeted: MNIST, Fashion-MNIST, inverted | 8 bits, range from training images | 8 bits, fitted to the manifest | 9 bits, the same LSB | 9 bits, the fitted range |
|---|---|---|---|---|
| Most outputs clipped in a run, of 160,000 | 27, 161, 0 | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| Largest error, the most in any run, % of the largest reference value | 8.97, 24.05, 8.59 | 8.97, 8.95, 8.59 | 8.97, 8.65, 8.59 | 8.61, 8.95, 8.87 |
| rms error, % of the reference's rms | 4.46, 4.67, 4.18 | 4.64, 5.05, 4.18 | 4.46, 4.67, 4.18 | 4.57, 4.91, 4.12 |
| rms error, % of the converter's full scale | 1.44, 1.13, 1.26 | 1.32, 0.91, 1.26 | 0.72, 0.56, 0.63 | 1.29, 0.88, 1.23 |
| Class agreement with the declared reference, % | 99.59, 96.78, 99.23 | 99.55, 96.20, 99.23 | 99.59, 96.78, 99.23 | 99.57, 96.63, 99.26 |
| The same on the first 1,000 vectors, % | 99.49, 96.85, 99.10 | 99.49, 96.60, 99.10 | 99.49, 96.85, 99.10 | 99.50, 97.01, 99.14 |
| Runs of 25 at 99.5% or more, on those | 13, 0, 1 | 13, 0, 1 | 13, 0, 1 | 15, 0, 3 |

**Spent on range, nothing clips and the error does not change.** No output is clipped in
any of 600 runs, where 70 of the same 600 clipped with eight bits. 530 of those runs are
the 8-bit run exactly: every one in which the 8-bit converter had clipped nothing. The
five networks of thirty that had clipped have 0.995 to 1.000 times the rms error they
had, where the fit of §10.5 left them with 1.20 to 1.24 times. Nothing is fitted and no
manifest is read to set it. The largest reference value is 0.66 of the converter's full
scale at the most. That is room in these thirty networks, and not a guarantee.

**Spent on finer steps, the rounding halves and the fit's cost stays.** The declared
format alone is then 0.38 to 0.64% of the reference's rms off, where fitted with eight
bits it was 0.76 to 1.27%. With noise, every network has 0.97 to 0.99 times the rms
error it has fitted with eight. The five networks whose range the fit widened still have
1.17 to 1.20 times the error they have with the bit spent on range. Class agreement
gains 0.02 ± 0.01, 0.43 ± 0.10 and 0.03 ± 0.02 of a point over the 8-bit fit.

**Neither moves the largest error.** With the bit spent on range it is 7.2 to 8.4% of
the largest reference value in a set's mean and 9.7% at the most, and no run of 300 is
within 2.0%. It is the noise's, as §10.1 and §10.5 found, and a converter's width does
nothing for it.

**And as a share of the converter's full scale, the wider converter passes with the same
error.** With nine bits at the same LSB the rms error is 1.43 to 1.83 steps, as it was
with eight, and that is 0.56 to 0.72% of a full scale twice as large. All 150 runs are
within 1.0% of the converter's full scale, where 20 were, and none is within 1.0% of the
reference's rms, as none was. This is §10.5's reason for stating the bound against the
reference, seen from the other side.

**What this changes in §10.5.**

1. **Two words of its second item are taken back: "no wider".** For a converter of a
   given width a wider range is a larger step, and a larger step costs error. A range
   that is wider at the same step costs none. A manifest sees the declared format and
   cannot tell which of the two an engine did. With the bound stated against the
   reference there is also nothing to gain by declaring a wider range. So the manifest
   needs only what §10.3's fourth item asked: the declared range holds the largest value
   the reference takes, and a clipped output is a range fault.

2. **Its first and third items stand.** A bound in steps or as a share of full scale
   stays withdrawn, and the rms bound is stated against the reference, its rms or its
   largest value.

3. **Gate F should not assume the ninth bit.** ~~Whether the PTA's interface chip
   carries one is not decided on our side.~~ By GRXCP's own models it costs up to twice
   the converter's power, and it needs a receiver whose linear range we have not priced.
   The model's figures on the first 1,000 vectors, for the networks trained for the
   tile, are 4.24 to 4.67% of the reference's rms with the bit spent on range and 4.24
   to 4.85% with eight bits and a fitted range.

   *Settled the same day: it carries none. GRXCP keeps the PTA's output converter at 8
   bits (its decision B14). The figures to set Gate F against are then the 8-bit ones
   with a fitted range: 4.24 to 4.85% of the reference's rms here, and the rest in
   §10.5's third item. What §10.6 found stands, and is not acted on.*

   *Those are with no source. §10.7's first item has them lit, and replaces them.*

**What this is not.** A classifier of yours, or a chip: everything §10.4 says. A range
that holds by rule. A model of the receiver, which is where the range has to come from.
A remedy for the largest error. And of ten predictions written before these runs, seven
held: the three that did not said the rms error would never be over what it was, where
one set's is by a thousandth of a percent, put one set's largest error a hundredth too
high, and put what finer steps do for Fashion-MNIST's class agreement at a quarter of
what it is. It is held in grx930's design note §5, "The first board's last layer, with a
converter of one more bit", and in GRXCP's `docs/designs/pta_board_bits.py`.

### 10.7 The same layer with a light source (added 2026-10-13)

Every figure in §10 so far is for a tile with its own noise and no light source
modelled, and §10.1 and §10.4 say so. grx930's harness could not light a tile that held
only one of a network's layers. It now can (kubeworkz/grx930#70), and this is the same
stand-in with GRXCP's source over it as we hold a source (our B16): its noise within 1%
rms a shot for the lines together and 5% for a line on its own, and its lines level to
20%, read at a calibration and corrected on the weights. The PTA's output converter is
the 8-bit one (our B14).

| The reference networks, as budgeted: MNIST, Fashion-MNIST, inverted | No source | The source | The source, range fitted to the manifest |
|---|---|---|---|
| rms error, % of the reference's rms | 4.46, 4.67, 4.18 | 5.18, 5.34, 5.27 | 5.33, 5.66, 5.27 |
| Largest error, a mean over the runs, % of the largest reference value | 8.02, 11.53, 7.44 | 11.91, 14.91, 12.76 | 11.40, 10.16, 12.76 |
| Class agreement with the declared reference, % | 99.59, 96.78, 99.23 | 99.44, 96.45, 98.89 | 99.41, 95.90, 98.89 |
| On the first 1,000 vectors: rms error, % of the reference's rms | 4.52, 4.67, 4.24 | 5.22, 5.35, 5.31 | 5.22, 5.48, 5.31 |
| class agreement, % | 99.49, 96.85, 99.10 | 99.33, 96.41, 98.66 | 99.33, 96.17, 98.66 |
| runs of 25 at 99.5% or more | 13, 0, 1 | 8, 0, 0 | 8, 0, 0 |

**The source adds a seventh to the rms error.** A network has 0.98 to 1.40 times the rms
error it had with no source, 1.14 in the mean of thirty. The largest error grows by
more: 9.4 to 14.9% of the largest reference value in a set's mean, where it was 7.2 to
11.5%. No run is within 2.0%, or within 1.0% on the rms.

**Class agreement falls by a sixth to a third of a point**: by 0.15, 0.33 and 0.34. On
the first 1,000 vectors 8, 0 and 0 runs of 25 are at 99.5%, where 13, 0 and 1 were.

**Part of what it adds is not noise.** Where a line of the source is dim, the weights it
lights are raised to correct it, and a weight already at full scale cannot be raised. In
these networks that is 1 to 11% of FC3's weights. What they are short by is the same in
every shot until the lines are read again. The source's noise is new each shot. Of what
the source adds, squares for squares, the shared 1% is 1.00, 1.00 and 1.00% of the
reference's rms, a line's own 5% is 1.74, 1.60 and 1.98, and the lines' level, read and
corrected, is 1.60, 1.93 and 2.40. Left uncorrected the lines' level alone would be
6.51, 6.84 and 7.73.

**One limit of the model matters here.** It adds the source's share after the converter,
and it corrects the weights before it. So its converter sees sums that a chip's would
not, and clips a few of them. The figures above are means over all runs. The largest
errors in runs with a clipped output are the model's order as much as a source's, and
grx930's note gives them apart.

**What this changes in §10.**

1. **The figures to set Gate F against are the lit ones.** §10.5's third item and the
   note under §10.6's third gave them with no source. With the source and a range fitted
   to the manifest, on the first 1,000 vectors of the networks trained for the tile:
   5.22 to 5.48% of the reference's rms, 1.67 to 1.99% of its largest value, and class
   agreement of 99.33, 96.17 and 98.66%.

2. **Repeating a measurement will not average all of the error away.** Part of the PTA's
   error is fixed between calibrations. A gate that averages shots should expect a
   floor, and a gate that compares two runs of one calibration will see less scatter
   than the error.

3. **The rest of §10.3, §10.5 and §10.6 stands**: a band and not a ceiling, a
   largest-error bound written for an engine with noise, the bound stated against the
   reference, a range that holds the largest reference value, and the 99.5% set after
   the frozen classifier has been through the model.

**What this is not.** A classifier of yours, or a chip: everything §10.4 says. A source
through a single photodiode, a drifted tile, or a cycle of calibrations: this is the
source over the tile as budgeted. A remedy: three ways to keep a weight clear of full
scale are known to us and none has been run. And of eleven predictions written before
these runs, two held; most of the rest put the source's cost too high. It is held in
grx930's design note §5, "The first board's last layer, with a light source switched
on", and in GRXCP's `docs/designs/pta_board_lit.py`.

### 10.8 What the PTA's error is made of (added 2026-10-13)

§10 gives the PTA's error at FC3 as one figure. This is the same stand-in with the
tile's four sources of error one at a time, each alone and each left out, with no light
source and with §10.7's (kubeworkz/grx930#71). Nothing in grx930's harness was changed
to run it. Ten thousand vectors, in a model.

| The reference networks, no light source: MNIST, Fashion-MNIST, inverted | rms error, % of the reference's rms | rms error, % of the largest reference value | Largest error, a mean over the runs, % of the largest reference value | Class agreement with the declared reference, % |
|---|---|---|---|---|
| The 8-bit output converter alone | 0.71, 1.04, 0.76 | 0.25, 0.28, 0.27 | 2.14, 7.22, 0.47 | 99.85, 98.49, 99.73 |
| with crosstalk between neighbouring rows, 2% | 3.52, 3.42, 3.10 | 1.24, 0.93, 1.10 | 4.87, 9.02, 3.46 | 99.79, 98.29, 99.58 |
| with shot noise, 30 photons an LSB | 2.66, 3.15, 2.72 | 0.94, 0.86, 0.97 | 5.57, 10.00, 4.94 | 99.64, 97.18, 99.35 |
| with receiver noise, 0.25 LSB | 0.94, 1.35, 1.00 | 0.33, 0.37, 0.36 | 2.69, 7.75, 1.18 | 99.82, 98.01, 99.66 |
| with weight programming error, 1 LSB of an 8-bit weight | 0.94, 1.15, 1.01 | 0.33, 0.31, 0.36 | 3.00, 7.67, 1.57 | 99.81, 98.35, 99.67 |
| All four: the tile of §10.1 | 4.46, 4.67, 4.18 | 1.57, 1.27, 1.48 | 8.02, 11.53, 7.44 | 99.59, 96.78, 99.23 |
| All but the crosstalk | 2.80, 3.30, 2.88 | 0.98, 0.90, 1.02 | 5.80, 10.14, 5.27 | 99.60, 96.81, 99.28 |
| All but the shot noise | 3.63, 3.57, 3.24 | 1.28, 0.97, 1.15 | 5.44, 9.41, 4.15 | 99.74, 97.80, 99.52 |
| All but those two | 1.12, 1.44, 1.20 | 0.39, 0.39, 0.43 | 3.25, 7.90, 1.84 | 99.78, 97.92, 99.60 |

The crosstalk and the shot noise are 89 to 93% of the squared error, and with no light
source the four add as independent errors do, to within 0.6%. Three things in it bear on
Gate F.

1. **A 1.0% bound over the reference's rms is at an 8-bit converter's own rounding.**
   With nothing but its converter the PTA is 0.71, 1.04 and 0.76% of the reference's rms
   off, and 120 of 150 runs are within 1.0%. With the crosstalk and the shot noise both
   removed, the two small sources take it to 1.12, 1.44 and 1.20%, and no run is within.
   So if "normalized" divides by the reference's rms, the converter alone uses 71 to
   104% of the bound, and what it leaves for all four sources is less than the two small
   ones need. If it divides by the largest reference value, the tile as it stands is
   1.57, 1.27 and 1.48%, and without the crosstalk 0.98, 0.90 and 1.02%, with 80 of 150
   runs within 1.0%. This is the second request of
   [first_board_pta_note.md](first_board_pta_note.md), with figures.

2. **Most of the crosstalk is a gain, and a class does not see it.** The crosstalk is
   the largest source of rms error, and removing it raises class agreement by 0.01, 0.03
   and 0.05 of a point. Removing the shot noise raises it by 0.15, 1.02 and 0.29. In the
   model the crosstalk makes every output of FC3 2.2 to 2.8% too large. A light source
   corrected on the weights (§10.7) makes them 0.5 to 2.3% too small, by more where more
   weights are held at full scale. Gate F's two bounds on raw outputs see both of those.
   Its class bound sees neither. **A question for you:** may the declared reference
   carry one output scale for the PTA, fixed at calibration, as it carries a declared
   format? Or are raw outputs compared with none? We have not measured what one scale
   would buy at the gate, and ask before we do.

3. **Two of the PTA's errors partly cancel, and a gate should not pass on that.** One
   swells the outputs and the other shrinks them. With the light source on, the PTA is
   nearer its reference with the crosstalk than without it on two of the three data
   sets: 5.34% of the reference's rms against 5.97, and 5.27 against 6.02. On MNIST it
   is further, 5.18 against 4.98. A board measured whole can then look better than its
   parts, and worse when one of the two is fixed. With a common scale taken out of the
   outputs, the PTA is worse with the crosstalk on all three.

**What stands.** §10.3 and §10.5 to §10.7 as they are, and §10.7's first item still has
the figures to set Gate F against.

**What this is not.** A classifier of yours, or a chip: everything §10.4 says. A
device's crosstalk: the model's is the same fraction of each neighbouring row
everywhere, and a chip's need not come out as a gain. A gain measured against your
declared reference: the harness fits it against the network as a digital host runs it.
An output with its scale taken out and then put through Gate F: none was run. Of ten
predictions written before these runs, five held. It is held in grx930's design note §5,
"The first board's last layer, its budget a row at a time", and in GRXCP's
`docs/designs/pta_board_budget.py`.

### 10.9 The reply to the note, and who owns the freeze (added 2026-10-13)

[first_board_pta_note.md](first_board_pta_note.md) asked three things of you. A reply
came on 2026-10-13. It says of itself that it is a recommendation and not an approved
change, and that the demo draft and the worksheet it read are still unratified. It is
recorded here so that it is not only in a message, with what it settles and what it
leaves.

**What the reply recommends.**

1. **Gate F's normaliser.** The rms of the PTA's output less the reference's, over the
   rms of the reference's output, on the frozen and ordered 1,000 vectors. One PTA shot
   a vector, and no averaging over repeats. Repeat-to-repeat variation is reported
   apart, since some of the error is fixed between calibrations. The largest-error check
   is kept apart.

2. **FC3 in the frozen canary.** 6-bit activations and 6-bit weights trained for the
   tile, the PTA's 8-bit ADC, and one 128 × 64 tile. Int8 weights cut to six bits are
   not to stand in for them: nobody has modelled that.

3. **The freeze had no owner and no date.** E-005 names roles and no person.

**The owner.** Decided on 2026-10-13: **Gridworkz is the named owner of the freeze**, of
the canary's workload and of Gate F's thresholds.

**What GRXCP says to it.**

1. **The normaliser and the single shot are what we would choose.** §10.5's third item
   asks for the bound stated against the reference, its rms or its largest value, and
   this is the first of the two. It does not move with the output range, and every
   figure in §10 is of one shot.

2. **Under that normaliser the 1.0% has to be looked at again.** On the first 1,000
   vectors, FC3 with nothing but its 8-bit converter is 0.74, 1.02 and 0.79% of the
   reference's rms off. The tile as budgeted is 4.52, 4.67 and 4.24%, and lit with its
   range fitted 5.22, 5.48 and 5.31% (§10.7). With the crosstalk and the shot noise both
   removed it is 1.12, 1.44 and 1.20% on 10,000 vectors (§10.8). So the converter alone
   uses 74 to 102% of the bound as drafted, and the tile as modelled is over four times
   it. We propose a band in its place, set after the frozen classifier has been through
   the model (§10.3).

3. **The canary's format is the stand-in's own.** §10's figures are of the right shape.
   They are a stand-in's until the frozen weights and vectors exist.

4. **Repeat-to-repeat variation is ours to report**, from the model's draws, and is not
   in §10 yet.

**What it left with the owner.** The rms bound under that normaliser. Whether the
declared reference may carry one output scale for the PTA, which §10.8 asks and the
reply does not answer. Who trains FC3 (§6, question 4). And the freeze's date. §10.10
has what the owner ruled on each.

**What this is not.** A ruling: the reply recommends, and this section records it. A
change to grxgpu.

### 10.10 What the freeze's owner ruled (added 2026-10-13)

§10.9 left the reply's reading and four more things with the freeze's owner. Gridworkz
ruled on them the same day: the first four as GRXCP had recommended, and the date as its
own to set. Four are rulings, and one is put off until a run exists.

1. **Gate F's normalised rms error** is the rms of the PTA's output less the
   reference's, over the rms of the reference's output, on the frozen and ordered 1,000
   vectors. One PTA shot a vector, with no averaging over repeats. Repeat-to-repeat
   variation is reported apart, and the largest-error check is kept apart. That is the
   reply's recommendation as §10.9 has it.

2. **The 1.0% is replaced by a band**, set after the frozen classifier has been through
   the model. GRXCP proposes the band from that run and the owner rules it. No figure
   for it exists until then, and §10.9 has why 1.0% could not be it.

3. **Whether the declared reference carries one output scale for the PTA is not ruled.**
   It waits on a run that fits the gain against the declared reference and takes it out,
   which grx930 and GRXCP owe (§10.8). Until it is ruled the draft's comparison of raw
   outputs stands.

4. **FC3 is trained by grx930's harness**, the one that trained the stand-in: for the
   tile, and in the format of §10.9. Two things have to be fixed first, the canary's
   data set and its first two layers. The harness trains a network whole today. It has
   no way to train FC3 alone over two layers it is given, and which of the two the
   canary wants is part of fixing those layers.

5. **The freeze is on 2026-11-25.** The canary's workload and Gate F's thresholds are
   frozen by then, and Gridworkz owns it.

**What follows, in order.** The canary's data set and its first two layers are fixed.
FC3 is trained. The frozen classifier is run through the model, and the band is proposed
from that run and ruled. All of it is before 2026-11-25, and none of it has a date of
its own yet.

| Document | Where | Edit |
|---|---|---|
| Demo | §4, Gate F | The normaliser and the single shot of item 1. A band in place of the 1.0%, its figures to follow the frozen classifier's run |
| Demo | §2, FC3's row | Trained by grx930's harness, for the tile |
| Task list | E-005 | Gridworkz as the freeze's owner, and 2026-11-25 as its date. The reply would have PTA technical and verification sign-off beside the owner |

| What GRXCP and grx930 owe for it | Whose | State |
|---|---|---|
| FC3 trained for the canary | grx930's harness, GRXCP | Trained on 2026-10-14, with FC1 and FC2 (§10.13). Its golden tensors were written the same day (§10.14) |
| The frozen classifier through the model, and a band proposed from it | grx930's harness, GRXCP | Run on 2026-10-15, and the band ruled (§10.15) |
| A run with the gain fitted against the declared reference and taken out | grx930's harness, GRXCP | Run on 2026-10-14 (§10.11). Item 3 was ruled the same day: one scale (§10.14) |
| Repeat-to-repeat variation, reported apart | GRXCP | Reported on 2026-10-15 (§10.15): 0.043 points on one source |

**What this is not.** A threshold: no figure for the band exists. A ruling on the output
scale. A ruling on the 2.0% for the largest error or on the 99.5% for the class: §10.3's
proposals for those two stand as proposals. A change to grxgpu: the demo draft and E-005
are yours, and are not patched here.

### 10.11 What one output scale buys at Gate F (added 2026-10-14)

§10.10's third item waits on a run that fits the gain against the declared reference and
takes it out. This is that run (kubeworkz/grx930#72), on the same stand-in, in a model.
grx930's harness now gives FC3's outputs one scale, fixed at calibration: the
least-squares slope of the declared reference on the PTA's outputs, with no offset, over
1,000 vectors the network was not trained on and Gate F is not judged on, run through
the same tile after the gate's. The gate's figures are then taken again with the outputs
times that scale. It is applied on the host's side, exactly.

| The reference networks, the first 1,000 vectors: MNIST, Fashion-MNIST, inverted | rms error, % of the reference's rms | rms error, % of the largest reference value | Largest error, a mean over the runs, % of the largest reference value | Class agreement with the declared reference, % |
|---|---|---|---|---|
| The tile of §10.1, no light source: raw outputs | 4.52, 4.67, 4.24 | 1.72, 1.42, 1.54 | 7.69, 7.53, 7.16 | 99.49, 96.85, 99.10 |
| its outputs times one scale | 3.18, 3.46, 3.21 | 1.21, 1.05, 1.17 | 5.69, 6.15, 5.33 | 99.49, 96.85, 99.10 |
| With §10.7's light source and the range fitted: raw outputs | 5.22, 5.48, 5.31 | 1.99, 1.67, 1.93 | 10.43, 9.49, 11.31 | 99.33, 96.17, 98.66 |
| its outputs times one scale | 4.87, 5.30, 5.19 | 1.86, 1.61, 1.89 | 10.89, 8.96, 11.04 | 99.33, 96.17, 98.66 |

1. **With no light source it takes off about half the squared error, and with one an
   eighth at the most.** The scale is 0.969, 0.970 and 0.973 with no light source: the
   crosstalk's gain, which the scale is the inverse of to within a hundredth. It takes
   the tile from 4.46, 4.67 and 4.18 to 3.13, 3.46 and 3.14% of the reference's rms on
   10,000 vectors, 0.43 to 0.51 of the squared error. With §10.7's source it is 0.984,
   1.000 and 1.003, because the source had already taken gain off (§10.8), and it takes
   the tile from 5.18, 5.34 and 5.27 to 4.84, 5.16 and 5.15%, 0.05 to 0.13 of the
   squared error.

2. **It is the tile's, not the vectors'.** Fixed on 1,000 other vectors, the scale is
   within 0.0016 of the one the test vectors would fit themselves in every run with no
   light source, and 0.0041 with one. It cannot be tuned to the gate's vectors, and
   there is nothing to be had from trying.

3. **It moves no class.** One scale on every output changes which is the largest only
   through the biases. The class agreement is the same with it and without, to 0.004 of
   a point, and with no light source in every run.

4. **It does not bring the PTA within 1.0%.** No run of the 150 is within 1.0% of the
   reference's rms with it, with the source or without. Its largest error is 10.9, 9.0
   and 11.0% of the largest reference value with the source, where §10.3 proposes a
   bound written for an engine with noise. The band §10.10 puts in place of the 1.0% is
   set on figures of this size whatever is ruled here.

**What GRXCP recommends for §10.10's third item.** The ruling is the owner's. We would
rule:

- **The declared reference may carry one output scale for FC3**, a single number for all
  its outputs, fixed once at calibration and applied to the PTA's outputs on the host's
  side before Gate F compares them.

- **It is fixed on a calibration set of its own**, declared and frozen with the workload
  on 2026-11-25, and never on the gate's 1,000 vectors.

- **Gate F reports its rms and largest error both with the scale and without it**, and
  the band that replaces the 1.0% is set on the figure with it.

Why. A gain common to every output is what a calibration is for, and it does not move a
class. Fixed on other vectors it is a property of the tile and not of the vectors, so it
cannot flatter the gate. With the source on it buys 0.34, 0.18 and 0.13 of a point, so
it does not decide whether the board passes; it keeps a gain a calibration removes from
being counted against the PTA. Reporting both keeps the raw figure in view.

**What this is not.** A ruling: the third item of §10.10 is still the owner's. A scale
written into a chip: the model applies it exactly, and writing it into the weights or
the converter's codes rounds, which is not modelled. A scale an output, or with an
offset. A drifted tile. A classifier of yours: every figure is the stand-in's,
everything §10.4 says. Of ten predictions written before these runs, seven held. It is
held in grx930's design note §5, "The first board's last layer, with one scale on its
outputs", and in GRXCP's `docs/designs/pta_board_scale.py`.

### 10.12 The canary's data set and its first two layers (added 2026-10-14)

§10.10's fourth item left two things to fix before grx930's harness could train FC3: the
canary's data set and its first two layers. The owner, Gridworkz, ruled both on
2026-10-14, as GRXCP recommended.

**What was ruled.**

1. **The data set is MNIST, each image pooled to 8 × 8.** It is the set every figure in
   §10 was modelled on, and the one on which the stand-in gave its declared reference's
   class most often.

2. **grx930's harness trains all three layers in one run.** FC1 and FC2 at eight bits
   and with no tile noise, FC3 at six bits and trained for the tile. FC1 and FC2 are not
   trained elsewhere.

3. **FC2's int8 output becomes FC3's 6-bit activation by the PTA contract's quantiser**,
   (x + 2) >> 2, held at 31. That is the decision record's "top-six-bit quantizer"
   pinned to one rule: it rounds half up, as every figure in §10 did.

**What fills the canary manifest's fields for them.** These are proposed values for your
draft manifest, which this proposal does not edit:

| Manifest field | Value |
|---|---|
| `workload.dataset.name` | MNIST, each image pooled to 8 × 8 |
| `source_uri_or_archive` | `https://ossci-datasets.s3.amazonaws.com/mnist/`, PyTorch's mirror of the four original files. Archive MD5s: `train-images-idx3-ubyte.gz` `f68b3c2dcbeaaa9fbdd348bbdeb94873`, `train-labels-idx1-ubyte.gz` `d53e105ee54ea40749a09fcbcd1e9432`, `t10k-images-idx3-ubyte.gz` `9fb629c4189551a2d022fa330f9573f3`, `t10k-labels-idx1-ubyte.gz` `ec29112dd5afa0611ce80d1b7f02629c`: the ones torchvision lists |
| `version_or_snapshot` | The original files. Content SHA-256 after gunzip: `train-images-idx3-ubyte` `ba891046e6505d7aadcbbe25680a0738ad16aec93bde7f9b65e87a2fc25776db`, `train-labels-idx1-ubyte` `65a50cbbf4e906d70832878ad85ccda5333a97f0f4c3dd2ef09a8a9eef7101c5`, `t10k-images-idx3-ubyte` `0fa7898d509279e482958e8ce81c8e77db3f2f8254e26661ceb7762c4d494ce7`, `t10k-labels-idx1-ubyte` `ff7bcfd416de33731a308c3f266cc351222c34898ecbeaf847f06e48f7ec33f2` |
| `license_and_usage_terms` | CC BY-SA 3.0, copyright Yann LeCun and Corinna Cortes, as Keras's documentation states them |
| `retrieval_date_utc` | 2026-10-14 |
| `split_name` | Acceptance: the first 1,000 images of the test file, in file order |
| `sample_id_source` | `mnist-t10k-NNNNN`, the image's index in the test file: `mnist-t10k-00000` to `mnist-t10k-00999` |
| `preprocessing_revision` | The middle 24 × 24 of each 28 × 28 image in 3 × 3 blocks, each block's mean rounded half up, (2s + 9) div 18; then (127p + 127) div 255, from 0 to 127, stored as signed int8 |
| `intended_classes` | The digits 0 to 9 on outputs 0 to 9. Outputs 10 to 15 are trained toward no class. The class is the largest of all 16 outputs, the lowest index on a tie |
| `acceptance_order` | File order, as above |
| `graph` FC1 and FC2 `format` | Weights round(128w), held to −128 … 127; activations 0 … 127; sums in int32; an int32 bias in the sum's units added before the ReLU; after it, a shift right by the layer's power of two, rounded half up, held at 127. A layer's shift is the smallest at which no more than one positive sum in 10,000, on the first 10,000 training images, is held |
| FC3 `activation_conversion.exact_integer_mapping_scale_saturation_and_rounding` | (x + 2) >> 2, held at 31: FC2's 0 … 127 to FC3's 0 … 31, rounded half up |
| `training.training_data_split_and_digest` | The first 54,000 images of the training file |
| `training.validation_split_and_digest` | The last 6,000 images of the training file, never trained on. The first 1,000 of them fix an output scale, if one is ruled (§10.11) |
| `training.test_acceptance_split_and_digest` | As `split_name` |

**What was checked the same day.** The four files were fetched from the mirror above.
Their archive MD5s are torchvision's, and their content is byte for byte the copy every
model run used. A script written apart from grx930's harness pools all 70,000 images to
the harness's own pooled files, byte for byte. No acceptance vector is, byte for byte, a
training or held-out vector, and none repeats within the thousand. None is all zero.
Every digit is there, 85 to 126 times. In jobs of 16 the thousand is 62 full jobs and
one of eight. The acceptance tensors come to these digests, and the canary's golden
generation has to give the same bytes:

| Artifact | Bytes | SHA-256 |
|---|---|---|
| `ordered_inputs_int8`, [1000, 64], row-major | 64,000 | `d968e50d76c4c3bfe3b0d0020db73fc0a1bade8f794cba389216f0777f0f23c4` |
| `ordered_labels`, [1000], one unsigned byte each | 1,000 | `d14ba0a1a3818edefa35518ed001ece84b7ac0eabe9394551c73928493175d3f` |
| The ordered ids, one `mnist-t10k-NNNNN` and a newline each | 17,000 | `81e4e1694930066d6e678be2ac3b828a0677756e8dc0632048e605541c754711` |

**What follows.** grx930's harness needs two changes before it trains the canary. Today
it gives every layer one weight width, and it puts the tile's noise on every layer's
sums as a network trains. The canary needs a width per layer, and the noise on FC3
alone. And a rule for which trained network is the canary has to be written down before
any is trained. GRXCP recommends seed 1's, with the other four seeds' reported beside
it, so that no network is chosen on its results. Then FC3 is trained, the golden tensors
are generated, and the frozen canary is run through the model.

**What is still open.** FC3's declared reference. Is it the exact sum before the 8-bit
converter, as every figure in §10 has it? Or is it the converter's codes, as your
manifest draft words it ("exact integer accumulator/ADC behavior")? On the first, the
converter's own rounding is part of what Gate F reads: 0.74% of the reference's rms on
the stand-in's first 1,000 MNIST vectors. On the second it is not. This belongs to the
golden generation, and GRXCP will bring it with a recommendation. The output scale
(§10.11), the band, the 2.0% and the 99.5% are where §10.10 left them.

**One correction.** The decision record, the demo, the golden plan and the manifest of
2026-10-14 spell the owner's name "Gridworz". It is **Gridworkz**.

**What this is not.** A frozen canary: no network is trained, and no golden tensor
exists. A change to your drafts: the manifest's fields are proposed here, for you to
copy. Device evidence of any kind.

### 10.13 The canary, trained and run through the model (added 2026-10-14)

§10.12 fixed the canary's data set and its first two layers. grx930's harness has now
trained it (kubeworkz/grx930#73). FC1 and FC2 are the host's, at eight bits, with no
tile noise as they train. FC3 is at six bits, trained with noise of a tenth of its sums'
rms. All three train in one run from the same seed's 8-bit network. Five networks were
trained, seeds 1 to 5, and seed 1's is the canary: the owner ruled that before any was
trained, so it was not chosen on its results. Each was run through the model as §10.11
ran the stand-in: 250 runs, in a model.

| MNIST, the first 1,000 vectors | The canary, seed 1 | Its five networks | The stand-in's five (§10) |
|---|---|---|---|
| rms error, % of the reference's rms: the tile of §10.1, no light source | 4.61 | 4.53 | 4.52 |
| with §10.7's light source and the range fitted | 5.09 | 5.34 | 5.22 |
| the same, its outputs times one scale (§10.11) | 4.64 | 5.05 | 4.87 |
| rms error, % of the largest reference value, lit and fitted | 1.95 | 2.03 | 1.99 |
| Largest error, % of the largest reference value, lit and fitted | 9.33 | 10.48 | 10.43 |
| Class agreement with the declared reference, %: no light source | 99.74 | 99.56 | 99.49 |
| lit and fitted | 99.42 | 99.39 | 99.33 |

1. **At the gate the canary is the stand-in.** Network for network, the canary recipe's
   five networks less the stand-in's of the same seeds differ by +0.007 ± 0.016 of the
   reference's rms on the first 1,000 vectors with no light source, and +0.117 ± 0.048
   lit and fitted. No difference of rms or of the largest error is clear in any row. So
   §10's figures on MNIST stand for the canary's.

2. **The canary itself is 5.09% of the reference's rms off, lit and fitted, on the first
   1,000 vectors.** That is with §10.7's light source, the board's own case. Its class
   is the declared reference's on 99.42% of them, and on 99.74% with no light source.

3. **What the recipe gives up is a tenth of a point.** On the host the five are 96.76 to
   97.16% right on MNIST's test images, where the stand-in's were 96.87 to 97.40. On the
   first 1,000 vectors no difference of accuracy or class agreement is clear.

4. **It does not bring the PTA within 1.0%.** No run with the tile's errors in it is
   within 1.0% of the reference's rms, and none is within 2.0% on the largest error. The
   band that replaces the 1.0% is set from the frozen canary's run.

**What follows.** The canary's golden tensors: its weights and inputs as int8 and
six-bit bytes, the references of each stage, and their digests, as your
golden-generation plan lays out. Before that, one thing to settle: whether FC3's
declared reference is the exact sum before the 8-bit converter, as every figure here has
it, or the converter's codes (§10.12). And the output scale of §10.11 is still the
owner's to rule.

**What this is not.** A frozen canary: no golden tensor exists. The NPU's and the G100's
output: FC1 and FC2 run on the host here, exactly, at eight bits, which is §10.12's
contract for them. Device evidence of any kind. It is held in grx930's design note §5,
"The first board's canary", and in GRXCP's `docs/designs/pta_board_canary.py`, which
reproduces the harness's tables and checks every figure here.

### 10.14 The canary's golden tensors (added 2026-10-14)

§10.12 left FC3's declared reference open, and §10.11 the output scale. The owner ruled
both on 2026-10-14, as GRXCP recommended, before any golden tensor was written:

1. **FC3's declared reference is the 8-bit converter's codes**: FC3's exact sum, rounded
   half up at the layer's step and held to −128 … 127. That is your manifest draft's
   "exact integer accumulator/ADC behavior". A PTA with the format alone is then its
   reference exactly. §10's figures read the sum before the converter, so they are not
   figures against this reference.

2. **One output scale for FC3 may be applied**: a single number for all sixteen outputs,
   fixed once at calibration on the first 1,000 of the 6,000 held-out training images
   and never on the 1,000 acceptance vectors. Gate F is reported with it and without it,
   and the band is set on the figure with it. That settles §10.10's third item.

3. **The golden bundle is kept in GRXCP's repository**, `docs/designs/canary/`.

grx930's harness has written the canary's golden tensors (kubeworkz/grx930#74), stage by
stage as your golden-generation plan's §4 lays them out:

| The plan's name | File | Shape and type | What it is | SHA-256 |
|---|---|---|---|---|
| `ordered_inputs_int8` | `inputs_int8.bin` | [1000, 64] int8, 0 to 127 | The acceptance vectors, as FC1 takes them | `d968e50d76c4c3bf…` |
| `fc1_relu_int8` | `fc1_relu_int8.bin` | [1000, 64] int8, 0 to 127 | FC1's output: bias, ReLU, rescale | `783a3c1fda87b90d…` |
| `fc2_relu_declared_format` | `fc2_relu_int8.bin` | [1000, 64] int8, 0 to 127 | FC2's output, the same way | `b6011ac171d74f06…` |
| `pta_activation_inputs_6bit` | `fc3_act_codes_u8.bin` | [1000, 64] uint8, 0 to 31 | FC3's activation codes, min((x + 2) >> 2, 31) | `97ac9af24a121a58…` |
| `fc3_exact_sums` | `fc3_sums_int32.bin` | [1000, 16] int32 | FC3's exact sums, in its codes' units | `96ea597da2f06fb8…` |
| `fc3_declared_format_reference` | `fc3_codes_int8.bin` | [1000, 16] int8 | The 8-bit converter's codes: Gate F's reference | `b86134167b678210…` |
| `declared_reference_class_ids` | `class_ids_u8.bin` | [1000] uint8 | The largest of code × 512 + bias, the first on a tie | `657f175602ed7a0c…` |
| `high_precision_logits` | `highprec_logits_f64.bin` | [1000, 16] float64 | The trained network in double precision | `1e4370308cd0e9c2…` |
| `calibration_fc3_reference` | `cal_fc3_codes_int8.bin` | [1000, 16] int8 | The same codes on the calibration set, for the scale | `e2c6c346d4978d79…` |

Beside them are the three layers' integer weights and biases; the pixels, labels and
ordered ids of both sets; and the canary's network file with the 8-bit network it was
trained from. That makes 23 artifacts of 730,780 bytes. Each has its length and SHA-256
in a candidate manifest written to your template's fields, and in a `SHA256SUMS`. The
manifest's canonical SHA-256 is
`b5dd1bebaee44eea1f766f83b76f23352187e580153c7d564bec52a41b5c9e63`. That digest is of
the keys sorted with no whitespace; with only integers and ASCII in the manifest, that
is RFC 8785's form.

**How it was checked**, against your plan's §5:

- Corpus: the acceptance inputs, labels and ids are §10.12's digests. The calibration
  set's inputs and labels were worked out apart from the harness, from MNIST's own
  files.

- Arithmetic: GRXCP's checker, `docs/designs/pta_board_canary_golden.py`, is written
  apart from the harness. It holds its own arithmetic to cases worked by hand at every
  rounding, saturation and tie boundary. Then it works out every integer tensor again
  for all 2,000 vectors, byte for byte, and the double-precision logits from the
  network's file, to the last bit.

- Replay: the tile with its format alone gives every code; 0 of 32,000 differ. No code
  is held at the converter's range.

- Determinism: written twice, the same byte for byte; and written again after a change
  to the harness's self-test, the same.

- Planted errors: 21 in the harness's new code, 23 in the checker, and a byte changed in
  each of the bundle's 25 files, the manifest and `SHA256SUMS` among them. All are
  caught.

**What it says of the canary.** FC3's codes on the acceptance vectors run from −96 to
67, none near the converter's range. With the declared format the canary is right on
96.60% of them, the trained network in double precision on 96.80%, and the two give the
same class on 99.20%. No vector of either thousand has a tie for the largest output, so
the tie rule is held by cases built for it.

**What your plan asks that this does not have yet.** The freeze's approval: the manifest
is revision 0.1-candidate, `freeze_approval` is pending, and the band, the tail rule and
the class threshold are null. A pinned environment: the manifest records the compiler,
the C library and the harness's source digests, but no lockfile. Validation reports
inside the bundle: they are GRXCP's checker and its output. FC1 and FC2 run by the NPU
and the G100 against their stage references. And the model run of the frozen canary
against these codes, from which GRXCP proposes the band.

**What this is not.** A frozen canary. A band, or any PTA run against these codes.
Device evidence of any kind. It is held in grx930's design note §5, "The first board's
canary, its golden tensors", and in GRXCP's board plan (B21).

### 10.15 Gate F's band, its class and its tail (added 2026-10-15)

§10.10 left the band for after the frozen classifier had been through the model, and
left the 99.5% and the 2.0% as proposals. The canary has now been through it, against
the converter's codes of its golden tensors (§10.14). The owner ruled all three on
2026-10-15, as GRXCP recommended:

1. **Gate F's band is 2.5% to 7.3%** on the per-run rms error over the reference's rms,
   with the output scale; both edges are inside it. It replaces the 1.0%.

2. **The class: at least 98.5%** of the 1,000 vectors give the reference's class, from
   the scaled outputs with their biases. It replaces the 99.5%, which a board at its
   budget would fail on most runs.

3. **The tail: at most 16 of a run's 16,000 outputs 17 or more codes off**, with the
   scale. It replaces the 2.0% on the largest error, which a noisy engine cannot meet.

4. **A band set per board is an open question.** It is taken up once a board exists and
   its source has been measured, under the manifest's change control.

**Where they come from.** grx930's harness ran the canary (kubeworkz/grx930#76) 1,000
times a row: its budget with no source and lit, lit at 0.4 to 1.4 times every row of the
budget, and lit on ten sources a hundred times each. GRXCP wrote the rule down before
the run. The upper edge is the worst draw lit at the budget, rounded up to a tenth of a
point, and the lower edge the best draw at 0.6 of the budget, rounded down. The class is
the worst lit draw at the budget, and the tail the fewest codes at which that row's
worst draw has at most 16 outputs off. In a model:

| The canary, 1,000 draws a row, with the scale | rms error, % of the reference's rms: mean | sd | least | most | Passes all three, % |
|---|---|---|---|---|---|
| as budgeted | 3.32 | 0.02 | 3.26 | 3.38 | 100.0 |
| as budgeted, lit | 5.18 | 0.53 | 4.04 | 7.21 | 100.0 |
| lit, 0.4 of the budget | 2.22 | 0.16 | 1.91 | 2.88 | 5.2 |
| lit, 0.6 of the budget | 3.12 | 0.27 | 2.57 | 4.26 | 100.0 |
| lit, 0.8 of the budget | 4.10 | 0.40 | 3.26 | 5.69 | 100.0 |
| lit, 1.2 of the budget | 6.28 | 0.68 | 4.79 | 8.79 | 91.6 |
| lit, 1.4 of the budget | 7.42 | 0.83 | 5.53 | 10.41 | 44.3 |

**What a board should expect.** A board whose PTA meets its budget passed on every draw
the model made. A reading under 2.5% is more likely a wrong measurement than so good a
tile: at 0.4 of the budget only 5.2% of draws pass. But a tile 20% over its budget still
passes on 91.6% of draws. Most of the spread is which state of B16's source a board has,
and the band has to cover them all. So the gate catches gross faults and wrong
measurements, not a fine shortfall. That is why a band set per board is left open.

**Repeat to repeat, reported apart**, as §10.10 ruled. On one source the figure moves
0.043 points from repeat to repeat; ten sources' means are 0.497 points apart.

**What it asks of your drafts:**

| Document | Where | Edit |
|---|---|---|
| Demo | §4, Gate F | The 1.0% replaced by a band of 2.5% to 7.3% on the per-run rms error over the reference's rms, with the output scale fixed at calibration |
| Demo | §4, Gate F | The 99.5% replaced by 98.5%: the class of the scaled outputs, with their biases, against the reference's class |
| Demo | §4, Gate F | The 2.0% on the largest error replaced by the tail: at most 16 of a run's 16,000 outputs 17 or more codes off, with the scale |
| Demo | §4, Gate F | A source the calibration refuses, a line all but dark, is a calibration fault and not a Gate F result |
| Manifest | `gate_f` | Filled: GRXCP's `docs/designs/canary/manifest.json`, revision 0.2-candidate, carries the three and names the runs |

The manifest's canonical SHA-256 at revision 0.2-candidate is
`238177b0d4cf1e101b973e4cf8d503d792e520018a2b81f0eef17857a94680cf`. No artifact changed
from 0.1-candidate; the change record says so.

**What this is not.** A board's measurement, or device evidence of any kind. A band for
another network, or for a source other than B16's. The freeze's approval, which is still
2026-11-25. It is held in grx930's design note §5, "The first board's canary, its band",
and in GRXCP's board plan (B22, and §8, question 11), where
`docs/designs/pta_board_band.py` works every figure out again from the runs.

### 10.16 The canary's freeze package, and your review of it (added 2026-10-15)

Your golden-generation plan asks for more than the tensors. It wants the generation
scripts, a pinned environment, the exact commands and the test reports packaged with the
manifest. It wants the package verified by extracting it to a clean directory and
regenerating every tensor byte for byte. And it wants every field of the manifest
template filled from what exists, the rest left empty, so that a freeze review fails
closed. That package now exists:

| In GRXCP's `docs/designs/canary/` | What it is |
|---|---|
| The 23 artifacts | As §10.14 lists them: the tensors, the networks and the ids |
| `CONTRACT.md` | The numerical contract: every step's arithmetic, rounding, saturation and order, the files' encodings, and Gate F as ruled |
| `harness/` | grx930's four sources at a98656d, which made the tensors and the band's runs |
| `environment.lock` | The environment they were made in: Ubuntu 24.04.3, gcc 13.3.0, glibc 2.39, Python 3.12.3, and 26 packages at their exact versions |
| `regenerate.sh` | Makes the canary again from `harness/` and MNIST's four archives, and holds every tensor, network and id list to the folder's own |
| `reports/` | The corpus worked out apart; how the tensors were made; the checker's report; the regeneration; the band; the planted errors |
| `manifest.json` | Revision 0.3-candidate, on every field of your template; canonical SHA-256 `edeeb9df7f42cf74…` |
| `SHA256SUMS` | Every file above, and the manifest |

**Regenerated from nothing.** `regenerate.sh` was run from a copy of the folder, in an
empty directory, on MNIST's archives as fetched. In 248 seconds it trained the recipe's
five networks and wrote the tensors, and all 23 artifacts came out the folder's own,
byte for byte.

**Checked, and failing closed.** GRXCP's checker
(`docs/designs/pta_board_canary_golden.py`) holds every file in the folder to the
manifest's length and SHA-256. It holds the harness to the digests the manifest and
`regenerate.sh` both pin, then works every tensor out again apart from the harness. With
`--freeze` it lists every field still empty or pending, every blocker, and every
approval not given, and fails while any is left. Errors were planted in all of it, and
every one was caught. That is 11 in the checker; 41 ways of spoiling the folder, among
them a harness source changed with its manifest entry made to match; and 11 ways of
leaving one thing open in an otherwise ready manifest.

**What the owner ruled on 2026-10-15**, as GRXCP recommended:

1. **FC1 on the GRX930 NPU and FC2 on the G100 are tested against their stage references
   in integration, after the freeze.** The freeze fixes the workload, its tensors and
   its thresholds, and none of them depends on an engine. So the freeze on 2026-11-25
   does not wait on a board.

2. **You are the independent reviewer** of the numerical contract and the reference
   implementation. You wrote the plan and the template and did not generate the bundle.

3. **The stand-in's implementation path, owner and schedule is not part of the canary's
   freeze.** It belongs to the stand-in's own plan (§6, ruling 1). The manifest says so
   in place of an empty field.

**What the review asks of you.** Read `CONTRACT.md` against your plan's §3 and §5, and
against the reference implementation: `golden_image()` in `harness/pta_mnist.c`, and
GRXCP's checker. Run the checker and `regenerate.sh` yourselves. Then send GRXCP the
reviewer's name, the date, and anything the review found. GRXCP records them in
`approval.independent_reviewer` and the change record, and makes the next revision for
any finding. After that only Gridworkz's approval is open. Today `--freeze` names nine
open items:

- `freeze_approval`: pending

- `freeze_date_utc`: empty

- `approval.approved_by`: empty

- `approval.approval_timestamp_utc`: empty

- `approval.independent_reviewer`: empty

- freeze blocker: the numerical contract and the reference implementation reviewed by
  the grxgpu team, and the reviewer named in approval.independent_reviewer

- freeze blocker: the freeze approved by Gridworkz, on or before 2026-11-25

- `manifest_status`: candidate_not_frozen, not frozen

- `approval.status`: not_frozen, not frozen

**To check it yourselves**, from a GRXCP checkout:

```
python3 docs/designs/pta_board_canary_golden.py
python3 docs/designs/pta_board_canary_golden.py --freeze
bash docs/designs/canary/regenerate.sh MNIST_GZ_DIR NEW_EMPTY_DIR
```

**What this is not.** The freeze, which is Gridworkz's on or before 2026-11-25. Device
evidence of any kind. A change to your drafts: the template's fields are filled in
GRXCP's manifest, for your review.
