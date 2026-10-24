# TCU TFR multiplier OOC elaboration matrix

All cases use `USE_DSP=0` and the same one-multiplier module boundary. Baseline is the staged Wallace-tree implementation; candidate is the staged inferred-multiply implementation. Cell counts are generic pre-mapping Yosys cells, not physical area. The reusable runner is [profile_tfr_wmul_ooc_matrix.sh](../../tools/profile_tfr_wmul_ooc_matrix.sh); full run logs, scripts, and per-case validation are in the ignored build output at `build32/g100-slang-exact-128c/run-20261022/wmul-cost-probe-20261024/ooc-matrix-20261024-140452`.

| Configuration | N×M | Lanes | Shared B | P | Baseline wall (s) | Candidate wall (s) | Wall change | Baseline peak RSS (MiB) | Candidate peak RSS (MiB) | Baseline cells | Candidate cells |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_mantissa | 11×11 | 1 | 0 | 22 | 25.394 | 15.845 | -37.6% | 105.5 | 75.9 | 1972 | 1 |
| fp8_pair | 4×4 | 2 | 0 | 8 | 12.455 | 11.623 | -6.7% | 76.3 | 76.4 | 442 | 2 |
| mx_nv_fp4_pair | 2×2 | 2 | 0 | 4 | 18.703 | 16.310 | -12.8% | 76.3 | 76.1 | 78 | 2 |
| nvfp4_scale | 4×4 | 1 | 0 | 8 | 18.859 | 12.749 | -32.4% | 76.4 | 76.2 | 221 | 1 |
| nvfp4_shared_scale_terms | 4×8 | 2 | 1 | 12 | 10.941 | 11.872 | +8.5% | 76.6 | 76.5 | 2 | 2 |

These are the five distinct `USE_DSP=0` parameter tuples instantiated under `hw/rtl/tcu/tfr`: FP16/TF32 mantissa, FP8 two-product, MXFP4/NVFP4 2×2 pairs, NVFP4 scale-factor multiply, and NVFP4 shared scale-factor terms. Duplicate tuples are run once. Some cases are conditionally compiled by TCU format configuration; the matrix covers the source-supported tuples. Integer I4's explicit multiplier-module instances are in its `USE_DSP=1` branch, so they are not part of this LUT-path comparison.

Each baseline/candidate pair passed hierarchy checking, generated non-empty RTLIL, and used identical staged headers and wrapper files; the only changed source file was `VX_tcu_tfr_wmul.sv`. Per-case `staging.validation.txt`, `run.status`, logs, and structures preserve the evidence.

Small-case wall-time changes are noisy because frontend/tool startup dominates. Generic-cell counts show the candidate retains multiply cells rather than expanding equal-width products into Wallace-tree logic. The 4×8 shared-B tuple already has no such Wallace tree in the baseline and therefore shows no structural reduction. These measurements do not establish mapped area, timing, or PPA.
