# GRX930 MLPerf Tiny VWW Engineering Evaluation

**Status:** Evaluation protocol and upstream source snapshot pinned; corpus, platform, and run evidence still need to be frozen. This is an internal engineering benchmark, not an MLPerf submission or product-acceptance workload.
**Version:** 0.1 — 2026-10-10
**Product brief:** [GRX930 v1 Product Brief](grx930_v1_product_brief.md)
**Backlog:** [Engineering Task List](grxgpu_engineering_task_list.md), E-009

## 1. Evaluation purpose and claim boundary

Use Visual Wake Words (VWW) as an interim, deterministic workload to evaluate the GRX930 batch-1 embedded inference path while a customer acceptance model is unavailable. Compare a four-core RV64 CPU-only reference path with the GRX930 NPU-enabled path on the same input corpus and declared hardware/software configuration.

Call this result **GRX930 VWW engineering evaluation, MLCommons `tiny` snapshot `4addd0fa08d216e20637637874e084895f289da4`**. Do not call this an official MLPerf result, a v1.3 result, or a reproduction of v1.3 rules/code: the pinned upstream rules file identifies itself as v1.2 (updated 2024-08-19 and marked not final), while MLCommons' public results identify v1.3 as the latest published VWW round and do not establish that this source commit is its submission code. A separate official repository discussion documents ambiguity in the VWW labeled evaluation set, including potential overlap with training data. The 80% top-1 target below is an upstream v1.2 reference, not a ratified GRX930 customer-quality gate.

## 2. Immutable upstream artifact lock

The paths below are all relative to the exact upstream commit [`4addd0fa08d216e20637637874e084895f289da4`](https://github.com/mlcommons/tiny/tree/4addd0fa08d216e20637637874e084895f289da4). The commit is an identifiable development snapshot, **not** asserted to be an official v1.3 release.

| Artifact | Pinned identity | Use |
|---|---|---|
| Rules | [`benchmark/MLPerfTiny_Rules.adoc`](https://raw.githubusercontent.com/mlcommons/tiny/4addd0fa08d216e20637637874e084895f289da4/benchmark/MLPerfTiny_Rules.adoc); document says Version 1.2, updated 2024-08-19, not final | Reference for Single Stream, closed/open division, metrics and equivalence constraints. |
| VWW model definition | [`benchmark/training/visual_wake_words/vww_model.py`](https://raw.githubusercontent.com/mlcommons/tiny/4addd0fa08d216e20637637874e084895f289da4/benchmark/training/visual_wake_words/vww_model.py) | MobileNetV1-style reference: 96×96 RGB, two outputs (person/no-person), α=0.25 configuration. |
| INT8 reference model | [`vww_96_int8.tflite`](https://raw.githubusercontent.com/mlcommons/tiny/4addd0fa08d216e20637637874e084895f289da4/benchmark/training/visual_wake_words/trained_models/vww_96_int8.tflite); published MD5 `f0b011416abee0343a5d130cb1f4c18f` | Primary INT8 model file identity. Verify this MD5 on acquisition and record a locally computed SHA-256 in the run manifest. |
| Float reference model | [`vww_96_float.tflite`](https://raw.githubusercontent.com/mlcommons/tiny/4addd0fa08d216e20637637874e084895f289da4/benchmark/training/visual_wake_words/trained_models/vww_96_float.tflite); published MD5 `c777d35ddb2ba1a6b9f2b72d9bc59728` | Float comparison/reference only; verify MD5 and record local SHA-256 if used. |
| Reference conversion | [`convert_vww.py`](https://raw.githubusercontent.com/mlcommons/tiny/4addd0fa08d216e20637637874e084895f289da4/benchmark/training/visual_wake_words/convert_vww.py) | Documents float conversion and full-INT8 conversion; includes a representative-dataset generator. Do not silently substitute its generated model for the pinned INT8 model. |
| Calibration image names | [`calibration_data.txt`](https://raw.githubusercontent.com/mlcommons/tiny/4addd0fa08d216e20637637874e084895f289da4/benchmark/training/visual_wake_words/calibration_data.txt) | Identity of listed calibration examples; use only if calibration is required and record the actual files and hashes. |
| Accuracy run configuration | [`tests_accuracy.yaml`](https://raw.githubusercontent.com/mlcommons/tiny/4addd0fa08d216e20637637874e084895f289da4/benchmark/runner/tests_accuracy.yaml), `vww01`, model `vww01`, `infer 1 0` | Reference snapshot configuration: one inference query and zero warmups in its accuracy stanza. Preserve as reference; do not imply it is the v1.3 official configuration. |
| Performance run configuration | [`tests_performance.yaml`](https://raw.githubusercontent.com/mlcommons/tiny/4addd0fa08d216e20637637874e084895f289da4/benchmark/runner/tests_performance.yaml), `vww01`, five loops, `infer 20 5` | Reference snapshot configuration only. The GRX930 engineering protocol below additionally specifies its own repeat count and reports it separately. |
| Dataset acquisition pointer | [`download_and_train_vww.sh`](https://raw.githubusercontent.com/mlcommons/tiny/4addd0fa08d216e20637637874e084895f289da4/benchmark/training/visual_wake_words/download_and_train_vww.sh) | Points to `vw_coco2014_96.tar.gz` hosted by Silicon Labs. The pinned script does not publish a digest for that archive. |
| Label generation | [`generate_y_labels.py`](https://raw.githubusercontent.com/mlcommons/tiny/4addd0fa08d216e20637637874e084895f289da4/benchmark/training/visual_wake_words/generate_y_labels.py) | Shows expected `y_labels.csv` format and class IDs; generated ordering depends on filesystem enumeration, so freeze the resulting file rather than regenerating silently. |

GitHub's API tree/blob SHA values are Git object IDs, not file SHA-256 values. Do not present them as checksums. The published model sidecars are MD5; the evaluation package must independently compute SHA-256 for the actual downloaded model, dataset archive, expanded/preprocessed corpus, labels, generated NPU image/binary, firmware, and evaluation executable/configuration.

## 3. Dataset and label freeze — explicit prerequisite

The pinned download script identifies the archive URL, but no official archive digest was found. The upstream runner configuration refers to `y_labels.csv`; the source repository's generator writes it from preprocessed `person` and `non_person` directories. An MLCommons repository issue records that COCO does not publish test-set annotations and describes use of 1,000 images that may also have appeared during training. Therefore:

1. Fetch data only from the pinned upstream acquisition pointer or an approved archived copy; record the final resolved URL, retrieval date, license/terms, byte size, and SHA-256 of the archive.
2. Record the exact preprocessing program and commit, dependencies, resize/interpolation, RGB order, pixel normalization, binary tensor encoding, class IDs, sorting/order, and all command-line options.
3. Freeze the actual evaluation images, their order/IDs, labels, and the resulting `y_labels.csv`. Calculate SHA-256 for the archive, expanded files or deterministic corpus bundle, ordered input manifest, and labels. Store those values in the run manifest; never regenerate a different split under the same evaluation ID.
4. Keep evaluation data out of training, quantization calibration, and tuning where the source permits. If the legacy VWW corpus cannot establish this separation, label the score **legacy VWW engineering accuracy with dataset-overlap caveat**, not a clean holdout, MLPerf-compliant result, or customer-quality proof.
5. Do not freeze any dataset digest in this plan until the bytes have actually been acquired and checked. E-009 remains open until the corpus and label hashes are recorded and reviewed.

## 4. GRX930 evaluation stages

### Stage A — reference and CPU-only baseline

- Run the pinned INT8 model through a trusted software reference on the selected GRX930 host/software environment. Validate model input/output tensor shapes, quantization scales/zero points, two-class ordering, and preprocessing equivalence against the pinned reference implementation.
- If an actual four-core GRX930 FPGA/system is not available, report this stage as a host/reference-only baseline. Do not substitute simulation or a different host CPU and label it a GRX930 board result.
- Use a single inference at a time (batch 1, Single Stream); preserve the frozen sample order and emit per-sample input ID, output logits/scores, predicted class, ground truth, status and checksum.

### Stage B — NPU-offload capability experiment

- First inspect the compiled graph and map every operator to NPU or CPU. The current repository evidence does not establish a full VWW graph compiler or complete Conv2D/depthwise operator support.
- Run only if the product RTL/FPGA interface can execute the required operation(s). Record the graph partition, all CPU fallbacks, transforms such as im2col, quantization changes, copies, synchronization, and operator-by-operator timing. Do not describe a partly offloaded or CPU-emulated graph as fully NPU-accelerated.
- The NPU path must preserve the pinned model's output semantics. Compare every sample's outputs to the reference under a frozen, justified numerical tolerance; report top-1 accuracy on the same frozen labels. Do not adjust quantization or quality tolerance after observing the test results without creating a new evaluation version and recording the reason.
- If graph coverage or model loading is not implemented, record the NPU stage as **blocked/not supported** and use VWW only for host/reference and preprocessing pipeline validation. Do not claim an NPU workload pass.

## 5. Two timing scopes, one fixed workload

Keep **benchmark-style inference latency** and **product end-to-end latency** distinct; neither should be mislabeled as official MLPerf timing.

1. **Inference-only engineering latency:** single-stream, batch-1 model invocation on already prepared input tensors. Record whether DMA/host-to-device transfer and completion polling are inside this interval. Use the upstream v1.2 rule as context: preprocessing/postprocessing are untimed there; exact GRX930 interval boundaries must be stated in every report.
2. **Product end-to-end latency:** start when the 96×96 input image is available in the declared host memory; stop when the class result/status is returned to the caller. Include image decode/resize/normalization, transfers, queueing, CPU fallbacks, NPU execution, synchronization and output conversion. This is the primary system metric for product evaluation.

For both CPU-only and NPU-enabled paths, hold constant the image order, software/model/data revisions, memory placement policy, board revision, cooling, ambient condition and declared power/clock settings. Do not cache answers or omit data movement from the end-to-end number.

## 6. Run protocol and measurements

1. Archive an untouched run directory for each configuration. Record the exact upstream SHA, rule-file contents/hash, runner/configuration hash, model MD5 verification and local SHA-256, corpus/label SHA-256, test binary/firmware/bitstream revisions, compiler/toolchain versions, SoC/FPGA part, core count, memory/cache configuration, clocks, power mode, host interface and environment.
2. Run accuracy first on every frozen evaluation sample exactly once per pass. Record per-sample scores and calculate top-1 using the pinned label mapping and explicit tie-breaking. Report count, correct count, percentage, skipped/errors, and reference-versus-device agreement. Any missing, duplicate or reordered sample is a failed run requiring diagnosis.
3. Run performance separately with at least 10 unmeasured warmups, then five full passes over the frozen sample list in deterministic order, one inference in flight. Record raw per-image inference-only and end-to-end latencies; publish p50/p95/p99, min/max, completed images/s, per-stage times, and run-to-run spread. Also archive the pinned upstream runner `vww01` configuration and its unmodified output if that runner is supported by the chosen board path.
4. For energy, use a calibrated meter and declared measurement points. Report joules/image and average/peak watts at both the module input and the whole-board boundary when instrumentation permits. State whether display/camera/host/other peripherals are excluded; do not compare accelerator-only energy to whole-board energy as if the scopes match.
5. Repeat a deterministic correctness pass after performance/energy collection. Retain raw logs and failure outputs. Do not discard outliers without a predeclared technical reason.
6. If comparing CPU-only and NPU-enabled operation on hardware, run the same image list, single-stream mode and same board/thermal settings. Randomize mode order across blocks if practical; report all runs, not only the best run.

The upstream v1.2 closed VWW target is **80% top-1 accuracy**. Report it only as an upstream reference checkpoint for this engineering snapshot; due to the non-final rules/version mismatch and labeled-set caveat, it is not a GRX930 product threshold or evidence of customer value. Customer quality, latency, power and reliability targets remain separately ratifiable.

## 7. Evaluation result manifest

Create one manifest per run containing, at minimum:

```text
run_id: GRX930-VWW-ENG-<revision>
claim_class: internal_engineering_only
upstream_repository: https://github.com/mlcommons/tiny
upstream_commit: 4addd0fa08d216e20637637874e084895f289da4
rules_file_version: 1.2 (upstream file says non-final)
reference_model: vww_96_int8.tflite
reference_model_md5_expected: f0b011416abee0343a5d130cb1f4c18f
reference_model_sha256_actual: <compute at acquisition>
dataset_archive_sha256: <compute; no upstream digest published>
preprocessed_corpus_sha256: <compute>
ordered_input_manifest_sha256: <compute>
labels_sha256: <compute>
label_count: <record>
board_and_device: <record>
rtl_commit_and_bitstream_sha256: <record>
firmware_runtime_compiler: <record>
core_count_memory_clocks_power_mode: <record>
graph_partition_and_cpu_fallbacks: <record>
accuracy_command_and_config_sha256: <record>
performance_command_and_config_sha256: <record>
preprocessing_and_tie_break: <record>
raw_logs_and_per_sample_outputs: <archive path and checksums>
```

No placeholder hash is a pass. A run is reproducible only after every required identity above is filled and an independent engineer can rerun it.

## 8. References and known limits

- [MLCommons Tiny source snapshot](https://github.com/mlcommons/tiny/tree/4addd0fa08d216e20637637874e084895f289da4)
- [MLPerf Tiny rules at pinned snapshot](https://raw.githubusercontent.com/mlcommons/tiny/4addd0fa08d216e20637637874e084895f289da4/benchmark/MLPerfTiny_Rules.adoc)
- [MLCommons Tiny v1.3 technical overview](https://mlcommons.org/2025/09/mlperf-tiny-v1-3-tech/)
- [MLCommons Tiny results overview](https://mlcommons.org/benchmarks/inference-tiny/)
- [VWW labeled test-set discussion in the official repository](https://github.com/mlcommons/tiny/issues/135)
- [Original MLPerf Tiny paper](https://arxiv.org/html/2106.07597v4)

Unresolved: canonical clean VWW evaluation-set identity and archive digest; exact source/code revision corresponding to official v1.3 results; GRX930 board/bitstream and four-core capability; operator coverage and NPU graph mapping; actual local model/corpus SHA-256 values; and customer model/quality criteria. Until resolved, this is a pinned reference snapshot and evaluation protocol, not a completed GRX930 benchmark run.
