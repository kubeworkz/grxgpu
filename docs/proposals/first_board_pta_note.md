# grxcp → grxgpu: the PTA against the demo's Gate F, and three things we need

2026-10-13. A one-page cover for §10 of
[first_board_reconciliation.md](first_board_reconciliation.md), written against your
first-board demo draft and your workload and data intake worksheet, version 0.2. It is a
proposal and a request. It changes nothing of yours.

## Where the PTA stands

We ran a stand-in for the demo's canary in a model: a 64-64-64-16 classifier with its
last layer on a 128 × 64 PTA tile and its first two layers exact. **The classifier and
its data are ours, not yours, and no device ran anything.** With our light source over
the tile and the output range fitted to the manifest, on the first 1,000 vectors of
MNIST, Fashion-MNIST and inverted MNIST:

| Gate F, as the demo draft proposes it | Proposed bound | The model |
|---|---|---|
| Normalized rms error of FC3's raw outputs | 1.0% | 5.22 to 5.48% of the reference's rms, which is 1.67 to 1.99% of its largest value |
| Largest error of FC3's raw outputs | 2.0% of the reference's full scale | 11.40, 10.16 and 12.76%, a mean over runs of 10,000 vectors |
| Class agreement with the declared reference | 99.5% of 1,000 vectors | 99.33, 96.17 and 98.66%; 8, 0 and 0 runs of 25 reach 99.5% |

So the proposed thresholds are not met in the model, on any of the three data sets. Most
of the error is the tile's own, before any source is lit. A wider output range, a ninth
converter bit and the light source each move a data set's rms error by a quarter at the
most (§10.5 to §10.7).

## Where it is pinned

Your worksheet says it had no GRXCP commit to cite and found no `pta_mnist` artifact.
These are the revisions, both on `main`:

- `kubeworkz/grx930` at `e8aa995d48a2`: the harness, `c930/sim/pta_mnist.c` and
  `pta_mnist.sh`, and its design note, `c930/doc/pta_error_model_design_note.md` §5. The
  four runs are `SHAPE=chain sim/pta_mnist.sh MNIST_DIR WORK_DIR` with `chain`,
  `chainfit`, `chainbit` and `chainlit`.

- `kubeworkz/grxcp` at `74881a39855e`: `docs/designs/pta_board_chain.py`,
  `pta_board_range.py`, `pta_board_bits.py` and `pta_board_lit.py`. Each holds every
  run's figures and checks them against the tables the harness printed. `python3
  docs/designs/pta_board_lit.py` runs its checks on the standard library alone.

- The trained networks and the per-run output lines are in neither repository. The
  harness trains the networks from fixed seeds and writes the lines, and nobody outside
  GRXCP has reproduced them.

## What would help

1. **The frozen canary, when it exists**: its weights, biases and scales, the 1,000
   inputs and FC3's expected outputs, with their digests. We will run it through the
   same model in place of the stand-in and replace every figure in §10. Until then every
   figure we give you is a stand-in's.

   *On 2026-10-14 the owner fixed the canary's data set, MNIST pooled to 8 × 8, and its
   first two layers, trained with FC3 by grx930's harness (§10.12). The acceptance set
   is the first 1,000 test images, in file order. §10.12 has their digests, and the
   values for your manifest's fields.*

   *And the same day the canary was trained and run through the model (§10.13). Seed 1's
   network is the canary. Lit and fitted, it is 5.09% of the reference's rms off on the
   first 1,000 vectors, and its class is the declared reference's on 99.42% of them. At
   the gate it behaves as the stand-in did.*

   *And the same day its golden tensors were written (§10.14). The owner ruled that
   FC3's declared reference is the converter's codes, and allowed one output scale fixed
   at calibration. The tensors and a candidate manifest are in GRXCP's
   `docs/designs/canary/`.*

2. **Two readings of Gate F that are yours to fix.** What "normalized" divides by: the
   reference's rms or its full scale. Our figure is over 5% one way and under 2% the
   other. And whether a vector is one shot or an average: part of the PTA's error is
   fixed between calibrations and does not average away (§10.7).

   *Since 2026-10-13, §10.8 has figures for the first of these: with nothing but its
   8-bit converter the PTA is 0.71 to 1.04% of the reference's rms off. And it asks a
   third: whether the declared reference may carry one output scale for the PTA.*

   *Answered on 2026-10-13, as a recommendation: over the reference's rms, and one shot
   a vector (§10.9). The freeze's owner is Gridworkz, and ruled the same day (§10.10):
   that normaliser and the single shot stand, the 1.0% becomes a band set from the
   frozen classifier's run, and the freeze is on 2026-11-25.*

   *And on 2026-10-14 one output scale was run (§10.11). On the first 1,000 vectors,
   with no light source, it takes the PTA from 4.52, 4.67 and 4.24% of the reference's
   rms to 3.18, 3.46 and 3.21%, and with the source from 5.22, 5.48 and 5.31 to 4.87,
   5.30 and 5.19%. It moves no class. Whether the reference carries it is still the
   owner's to rule, and §10.11 has what we would rule.*

3. **A ruling on §10.3, §10.5 and §10.7 before any acceptance run**, as your worksheet's
   §5 asks of every threshold. We propose a band and not a ceiling for the rms, a
   largest-error bound written for an engine with noise, bounds stated against the
   reference, and the 99.5% set after the frozen classifier has been through the model.

If it is useful, we can fill the PTA column of your worksheet's §4.2 and §5 from these
pinned sources, as a proposal.
