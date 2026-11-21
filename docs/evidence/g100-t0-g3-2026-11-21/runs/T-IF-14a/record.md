# T-IF-14a — Corpus Regeneration and Hash Match

**Test ID:** T-IF-14a. **Tier:** L0 (CPU reference only).
**Result:** PASS. This is a test-level result, not a G3 gate result.
**Contract row:** IF-14, `G100-T0-G2-SGEMM-1.0` identity and tolerances, in the
Approved v1.0 contract (SHA-256
`6eed0cc55917238346446f2fe5c36b8dc1324cad5d733af5f26f432a0b4bd38d`).
**Plan method:** [T-IF-14a row](../../../../proposals/g100_t0_g3_hardening_plan.md).
**Test owner:** Verification lead. **Run date:** 2026-11-21.
**Prepared by:** engineering agent; not an approver and not a signatory.
**Selection:** T-IF-14a is the highest-value host-only test available: it gates
every golden comparison and needs neither the G-3 revision, ECC S0, nor a
board. RTL/sim and board tests remain outside this run.

## Run identity

| Item | Value |
|---|---|
| Run commit | `d488657327389865d3e6a4efa4222d360d57fb0d` |
| Run tree | `2ffd1f20ec3192293e87a443cf0d76d77a0f8c69` |
| Workload source pin | `ff550c27570f17b0c8242be42257043d3de4ffa7` |
| Workload tree | `cf6b2f8657fcba985dd9007fa403231c3d800301` |
| T0 configuration hash | `cd5336232fa98454009574121e0b25cc98feb3530a50675874ba98738c154cda` |
| Generator | [`gen_golden.cpp`](../../../g100-t0-g2-2026-11-21/golden/gen_golden.cpp), SHA-256 `8ae98a8c455dabc5e58f6354bff60c2f39e1103194adf07a045e3bfef5a54dc6` |
| Toolchain | Ubuntu 24.04.3 under WSL2; `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`; glibc 2.39; Linux 6.18.33.2, x86_64 |
| Build stamp | No product image or RTL image was built. The host generator was rebuilt from the frozen source hash above; that hash is the build identity for this run. |
| Seed | 50 (`std::srand(50)` in the generator) |
| Command | `wsl -e bash docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-14a/run.sh > docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-14a/run.log 2>&1` |
| Runner | [`run.sh`](run.sh), SHA-256 `4fc9252eb7ad073b43080ec805058982ae8004b3032ece93c39267aecb9e41b1` |
| Raw log | [`run.log`](run.log), 2,205 bytes, SHA-256 `c2f5807469be9307a7b3d96eafce9c461712f635b4fa98747021a0430f12b111` |

## Result

The frozen generator was compiled without edits and run for K=64 and K=512.
The six regenerated A/B/C files matched the G2 manifest hashes exactly;
`sha256sum -c` reported `OK` for all six, and `cmp` reported byte-identical
files for all six. The regenerated C files are byte-identical to the frozen
C files, so the measured C bit difference is 0 and max ULP is 0 for this
CPU-to-frozen comparison.

| File | SHA-256 | Check |
|---|---|---|
| `g100t0_sgemm_m64n64k64_A.fp16` | `985ef83fe0802e90a08fe2023822dc0b31e83aeb66df9051f688c3e694b468a8` | OK |
| `g100t0_sgemm_m64n64k64_B.fp16` | `ad975434b9327b5dfe37f36e7e09e703253dce2bb80ece322797a17ff9356270` | OK |
| `g100t0_sgemm_m64n64k64_C.fp32` | `73a1a0eacd81d64cd451919493da3d9187f418b563e4c52b1f6a8ba68b5ad240` | OK |
| `g100t0_sgemm_m64n64k512_A.fp16` | `70dcc14a134e620c9b5d4be7dbbd01a64e6bb5efdf4fa8b6f432533bd735cfac` | OK |
| `g100t0_sgemm_m64n64k512_B.fp16` | `59fb1324bbfcff9c943fa7ab25b4a2ce0db7be7dec2787eb41c71d4552759cb9` | OK |
| `g100t0_sgemm_m64n64k512_C.fp32` | `d07043551fa7efeae970533f5e86c02af8062ab5bed82e38c68e161fe67628c9` | OK |

The run also rechecked the frozen corpus `SHA256SUMS` at the end: all nine
entries, including the generator, verifier, and verifier log, were `OK`.

## Open deviations

- **T-IF-14b is not run.** No SimX/RTL/device C comparison at a tier that runs
  all CTAs exists, so no device ULP result is claimed. The CPU-to-frozen C
  equality above does not substitute for T-IF-14b.
- **No G3 gate result.** This record closes only T-IF-14a's L0 corpus
  regeneration check. The other 74 test entries remain OPEN, including
  T-G-5c/T-G-5f, and G3 remains OPEN.
- **No G-3, ECC, or board dependency.** This run did not exercise the CP fault
  channel, ECC, or a board; those items remain subject to their own gates.
- **Build stamp.** A host generator build has no product image stamp; the
  frozen generator source hash is recorded instead.

## Reproduction

From the repository root:

```sh
wsl -e bash docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-14a/run.sh \
  > docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-14a/run.log 2>&1
```

The command exits 0 only when all six regenerated files match the frozen
hashes and `cmp` finds them identical.
