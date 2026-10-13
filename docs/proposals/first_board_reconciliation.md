# Reconciling the First Development Board — the Charter's Modular Carrier and GRXCP's Board Plan

**Status:** Proposal. No RTL and no code requested. It asks for edits to three draft
documents (§8) and for five rulings (§6), and for nothing to be built. *Amended
2026-10-13:* §10 is new, and §5.1, §5.2, §6 and §7 point to it where it changes them.
*And again the same day:* §10.5 is new, and withdraws §10.3's first item as it stood.
*And a third time:* §10.6 is new, and takes two words out of §10.5's second item.
*And its third item was settled the same day:* the PTA's converter stays at 8 bits.
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
   what we would propose for the 1.0% and for the 2.0%.*
4. **FC3's weights** (§5.2). Who trains them, and whether they are trained for the
   tile.
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
| The demo's classifier run through the error model at version 2 | grx930's harness, GRXCP | Waits on §6, question 4. *A stand-in for it was run on 2026-10-13: §10* |
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
rows (B16) would add to every figure here.

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
are exact here. **A lit tile.** No source noise is in these figures. **A remedy.**
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

**What this is not.** A classifier of yours, or a chip: everything §10.4 says. A range
that holds by rule. A model of the receiver, which is where the range has to come from.
A remedy for the largest error. And of ten predictions written before these runs, seven
held: the three that did not said the rms error would never be over what it was, where
one set's is by a thousandth of a percent, put one set's largest error a hundredth too
high, and put what finer steps do for Fashion-MNIST's class agreement at a quarter of
what it is. It is held in grx930's design note §5, "The first board's last layer, with a
converter of one more bit", and in GRXCP's `docs/designs/pta_board_bits.py`.
