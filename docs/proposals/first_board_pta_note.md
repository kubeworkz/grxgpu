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
| Largest error of FC3's raw outputs | 2.0% of the reference's full scale | 11.40, 10.16 and 12.76%, the mean of 25 per-run maxima on 10,000 vectors |
| Class agreement with the declared reference | 99.5% of 1,000 vectors | 99.33, 96.17 and 98.66%; 8, 0 and 0 runs of 25 reach 99.5% |

These stand-in summaries are well outside the draft's candidate values, but are not an
acceptance result for the frozen canary or a device. Gridworz's 2026-10-14 decision says
the draft's 1.0% RMS ceiling and 2.0% pointwise maximum are not approved physical
acceptance limits; 99.5% remains a candidate pending modeling of the actual canary.
Most of the error is the tile's own, before any source is lit. A wider output range, a
ninth converter bit and the light source each move a data set's rms error by a quarter
at the most (§10.5 to §10.7).

The largest-error figures above are means of per-run maxima across five reference
networks and five noise draws per data set. They are not the single worst output across
all runs; §10.7 reports the observed extremes and clipping separately. The RMS and
class-agreement entries are for the first 1,000 vectors.

## Where it is pinned

The evidence is pinned to immutable revisions:

- [`kubeworkz/grx930` merge commit `e8aa995d48a2065f911b50bfc839c41d8d366edb`](https://github.com/kubeworkz/grx930/commit/e8aa995d48a2065f911b50bfc839c41d8d366edb), which merges [PR #70](https://github.com/kubeworkz/grx930/pull/70), adds the harness changes in `c930/sim/pta_mnist.c` and `pta_mnist.sh`, and records the experiment in `c930/doc/pta_error_model_design_note.md` §5. The documented command from `c930/` is `SHAPE=chain sim/pta_mnist.sh DIR WORK chainlit`; `chain`, `chainfit` and `chainbit` are the comparison modes. The PR changes only those three source/documentation files: it does not commit trained networks or raw per-run logs. The harness writes generated data, networks and results under the supplied work directory.

- [`kubeworkz/grxcp` merge commit `74881a39855e334f16ad5f62c09c09f4c9e41b88`](https://github.com/kubeworkz/grxcp/commit/74881a39855e334f16ad5f62c09c09f4c9e41b88) includes [`pta_board_chain.py`](https://github.com/kubeworkz/grxcp/blob/74881a39855e334f16ad5f62c09c09f4c9e41b88/docs/designs/pta_board_chain.py), [`pta_board_range.py`](https://github.com/kubeworkz/grxcp/blob/74881a39855e334f16ad5f62c09c09f4c9e41b88/docs/designs/pta_board_range.py), `pta_board_bits.py` and [`pta_board_lit.py`](https://github.com/kubeworkz/grxcp/blob/74881a39855e334f16ad5f62c09c09f4c9e41b88/docs/designs/pta_board_lit.py). These scripts preserve the reported figures and check the generated summary tables against those embedded records. I ran `python3 docs/designs/pta_board_lit.py` from a temporary checkout of that exact revision; it ended with “All checks pass.” This verifies consistency of the preserved figures and summaries, not the original harness run.

The GRX930 raw run outputs and trained networks are not present in the pinned public source revision, and the GRXCP checker is not an independent rerun. The classifier and datasets remain GRXCP's stand-in, not the frozen GRXGPU canary; no physical device was tested.

Gridworz's subsequent [first-board PTA decision](first_board_gridworz_decision_2026-10-14.md) approved the shot-level RMS method and reporting requirements, but left the physical RMS band, tail limit and class-agreement target pending the actual frozen-canary model assessment.

## What would help

1. **The frozen canary, when it exists**: its weights, biases and scales, the 1,000
   inputs and FC3's expected outputs, with their digests. We will run it through the
   same model in place of the stand-in and replace every figure in §10. Until then every
   figure we give you is a stand-in's.

2. **Two readings of Gate F that are yours to fix.** What "normalized" divides by: the
   reference's rms or its full scale. Our figure is over 5% one way and under 2% the
   other. And whether a vector is one shot or an average: part of the PTA's error is
   fixed between calibrations and does not average away (§10.7).

3. **A ruling on §10.3, §10.5 and §10.7 before any acceptance run**, as your worksheet's
   §5 asks of every threshold. We propose a band and not a ceiling for the rms, a
   largest-error bound written for an engine with noise, bounds stated against the
   reference, and the 99.5% set after the frozen classifier has been through the model.

If it is useful, we can fill the PTA column of your worksheet's §4.2 and §5 from these
pinned sources, as a proposal.
