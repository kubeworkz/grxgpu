# G100-T0 G1 Evidence Audit — Source, Configuration, Tool, Workload and Golden Identities

**Status:** Audit started 2026-11-20. **G1 is not passed.** A clean T0 source
snapshot and a proposed configuration can be identified, but there is no
G100-T0 execution record, golden-output archive, independent review, or parity
result.
**Gate:** G1 — Baseline and evidence audit ([production plan](grxgpu_production_plan.md)).
**Scope:** G100-T0 engineering die: one cluster × 16 cores, 4 warps × 4
threads, TCU + DXA, 16 KB LMEM/ICache/DCache per core, no L2, no graphics,
SECDED ECC, 256 KB test SRAM, JTAG bring-up.
**Commercial disposition:** **UNCHANGED — HOLD.** This audit does not change the
[G0 engineering authorization](grxgpu_g100_g0_authorization.md), commercial G0,
or the holds on G4 purchases, G5 implementation, G6 tapeout, and production
release.
**Parent records:** [G100 product brief](grxgpu_g100_product_brief.md) ·
[G100 evidence manifest](grxgpu_g100_evidence_manifest.md) ·
[T0 baseline](proposals/g100_production_baseline.md) ·
[T0 tapeout checklist](grxgpu_g100_t0_tapeout_checklist.md).

## 1. Audit disposition

| Area | Pinned identity or current state | G1 disposition |
|---|---|---|
| Source | T0 commit `ff550c27570f17b0c8242be42257043d3de4ffa7`, root tree `cf6b2f8657fcba985dd9007fa403231c3d800301` | Identity pinned; no T0 build or freeze tag |
| Configuration | Proposed `CONFIGS` below; resolver output SHA-256 `cd5336232fa98454009574121e0b25cc98feb3530a50675874ba98738c154cda` (LF-stored) | Proposed only; not frozen or exercised |
| Toolchain | Discovery toolchain recorded; no T0 build/tool bundle | **OPEN** for T0 |
| Workload | `sgemm_tcu_wg_dxa`, M=N=64, K=64/512, FP16→FP32, NRC=16 | Source pinned; no T0 invocation |
| Golden output | None archived; discovery runs printed `PASSED!` only | **ABSENT** |
| Independent review | No named reviewer or review date | **OPEN** |
| SimX↔rtlsim parity | Discovery instruction counts match; cycles differ; no tolerance | **NOT ESTABLISHED** |
| FPGA/board | No T0 FPGA image, board, constraints, or timing evidence | **OPEN** |
| ECC | SECDED is a T0 baseline requirement; no ECC RTL or bench exists at the T0 pin, and the CI/checklist claims that said otherwise were corrected 2026-11-20. Closure is scoped in the [ECC closure plan](proposals/g100_t0_ecc_closure_plan.md), whose S0 assumptions were audited against this pin on 2026-11-20; the plan proposes the status block and demux inside `VX_t0_dbg_top`, a 64 KB readout window, SBA-only writes and TSRAM-only T0-A evidence. The gate record is the [S0 decision signoff](evidence/g100-t0-ecc-s0-2026-11-20/signoff.md) | **BLOCKED — requirement unimplemented; references corrected; S0 signoff unsigned** |
| Overall G1 | Identity work started; required evidence is incomplete | **NOT PASSED** |

## 2. Source identity

The T0 source is pinned to the published remote branch tip. The local checkout
has unpublished CI/documentation commits beyond the T0 pin and a dirty worktree;
neither is part of the T0 source pin or a substitute for a clean checkout.

| Field | Value | Status |
|---|---|---|
| Repository | [GRXGPU source repository](https://github.com/kubeworkz/grxgpu) | Observed origin |
| Pinned source commit | [`ff550c27570f17b0c8242be42257043d3de4ffa7`](https://github.com/kubeworkz/grxgpu/commit/ff550c27570f17b0c8242be42257043d3de4ffa7) | Immutable commit; not a T0 freeze tag |
| Root tree | `cf6b2f8657fcba985dd9007fa403231c3d800301` | Pinned Git tree |
| Branch / remote ref | `ci/runner-health-retries`; `origin/ci/runner-health-retries` = same commit | Mutable ref; informational |
| Commit date | 2026-11-19 22:37:47 -0500 | Observed |
| T0 source history | T0 JTAG/debug RTL and testbench added in `adaac4a93`; the pinned tip also contains later CI-only changes | Informational |
| Local HEAD | Current checkout HEAD (`git rev-parse HEAD`); commits ahead of the T0 pin: `git rev-list --count origin/ci/runner-health-retries..HEAD` | Not the T0 source |
| Local worktree | 28 modified/untracked paths overall; the T0 debug/test paths are unchanged, but other dirty RTL libraries are excluded by using the clean pin | Dirty; do not build from it |
| T0 delta from discovery pin | 14 files, 2,513 insertions under `hw/rtl/dbg/` and `hw/unittest/t0_dbg/` | T0 debug path added |
| Discovery evidence pin | `ff5790806973a1586478531c3d6710a0fa614384`, tree `9ecc11da261a4f7ad952761d6d6768e54086d7bd` | Applies to the earlier 1×4 discovery evidence only |
| T0 source review | No independent source review recorded | **OPEN** |

**Path hashes.** These SHA-256 values are over committed Git blob bytes at
`ff550c275`, not the mutable worktree. The T0 workload files and resolver are
byte-identical at local HEAD and the T0 pin.

| Path | SHA-256 | Relevance |
|---|---|---|
| `VX_config.toml` | `b932c482b62d8c40894f0628f5fbb3a50530cd0d74f6d4fb1964d6763d031f9f` | Configuration inputs |
| `ci/gen_config.py` | `4ae8207a5468a346b2d6856765b266e2024b8720d8ddc79782832813405480e9` | Canonical resolver |
| `hw/rtl/dbg/VX_t0_dbg_top.sv` | `d1852333ba56a59409b114170b6f12444132847faa0bf1d5a36f842af58a7f94` | T0 JTAG/debug top |
| `hw/rtl/dbg/VX_t0_boot.sv` | `e63d8047cfe9e0819f0dc52da663a762cef967929051bc81591175c09ec5511d` | T0 boot sequencer |
| `hw/rtl/dbg/VX_t0_core_attach.sv` | `cef2f207848501e8ef6c0dbbd0f998b77156df885470bc81e5a25667ceacdd9a` | Core-side attachment |
| `hw/rtl/dbg/VX_t0_test_sram.sv` | `4e8c042761b973573c39069a643bed7efed5ccbd1e94122fd869fab5ab3bcfbd` | 256 KB test SRAM |
| `hw/rtl/dbg/VX_jtag_tap.sv` | `143817788541bbbac726509abf0134d82e8e45fde571b3d49f49cbafbaf5396c` | TAP |
| `hw/rtl/dbg/VX_dm.sv` | `554fc603839ed43e2f45fe767fd108ad53ee6fe8246380be6a9923d40b51fa27` | Debug module |
| `hw/unittest/t0_dbg/main.cpp` | `40c0d5ecd917bdcb48ac9c1ce73354532f760678d82e47a24dd0997fe00c7901` | T0 JTAG testbench |
| `hw/unittest/t0_dbg/Makefile` | `ca9a5199b623b673bc0d82fde401458244039ec4a4fb9d4db80ed115d6f4c06f` | T0 test build |
| `ci/testcases/unittest.yaml` | `15d4476121a2cde1dad0cc56e09fc0ff252eef0400909fcbc0f3c196f86e4caf` | `hw-t0` CI definition |
| `tests/regression/sgemm_tcu_wg_dxa/main.cpp` | `423b63677ab54f4f57dee8731e1ec2643780e52d1e5a7e2345003106b9cfea88` | Workload and reference |
| `tests/regression/sgemm_tcu_wg_dxa/common.h` | `6946f87e76b9126d976ed9ef4ef35e7a779028bdf20084ccf7ed0b23db06c51c` | Types and defaults |
| `tests/regression/sgemm_tcu_wg_dxa/kernel.cpp` | `3a1bbf546ca2b292824f4040666d90e9ee90b3cee0b8b1090160d985d643408b` | WGMMA/DXA kernel |
| `tests/regression/sgemm_tcu_wg_dxa/Makefile` | `3aa417211fe1d613243238723b980aefa14fbd21fc02dda8385d9b9eeca089f5` | Workload build |

**ECC reference investigation (2026-11-20).** The T0 baseline requires SECDED on
LMEM, ICache and DCache, and `ci/testcases/unittest.yaml` at the T0 pin names
`hw/rtl/libs/VX_ecc_secded.sv`, `VX_ecc_ctrl.sv`, `VX_ecc_ram.sv` and benches
`hw/unittest/ecc` / `hw/unittest/ecc_ram`. None of those paths is tracked at the
T0 pin, and `git log --all --oneline -- <paths>` returns no commit that ever
added them. There is no implementation to restore.

The references entered the tree in `ac4382f21` (2026-11-10, an ancestor of the
T0 pin). That commit added the `hw-ecc` and `hw-ecc-ram` catalog entries and
rewrote the tapeout checklist to say the codec, counters and ECC bank RAM
existed and that LMEM's banks used them. Its changed-file list contains no ECC
RTL or testbench: the only ECC-related changes are `ci/testcases/unittest.yaml`
and `docs/grxgpu_g100_t0_tapeout_checklist.md`. The same catalog hunk appears
in `73d19ba3d` on `backup/pre-rebase-73d19ba3d`, which is not an ancestor of
the T0 pin, so the claim was carried across without the implementation ever
landing. The commit
message describes the checklist change as recording "the current ECC coverage".

Resolution applied and committed on 2026-11-20: the two ECC catalog entries are
removed, the checklist's ECC status, repository-inventory row and blocker are
corrected to "no ECC RTL", and the baseline now states that the test SRAM is
outside the three-array SECDED scope. The correction does not manufacture
missing evidence: ECC remains an unimplemented T0 requirement and a G1 blocker.

**Test-SRAM scope.** `VX_t0_test_sram.sv` was added in `adaac4a93` (2026-11-01),
one day after the 2026-10-31 baseline. It is a plain 4096 × 512-bit register
array with byte-enable writes, behind the JTAG bridge. The baseline's SECDED
requirement covers LMEM, ICache and DCache; the test SRAM is bring-up storage,
not one of the three functional arrays, so its lack of ECC is consistent with
the baseline as written. It is still unprotected: a bit flip in a boot image
loaded over SBA can prevent bring-up. The closure plan recommends protecting it
with the same SECDED wrapper (64+8 per lane, byte-enable RMW) because T0-A has
no other array through which the ECC path and counters can be exercised in
silicon, with per-lane parity as the fallback; the decision remains open pending
S0 signoff. If S0 accepts the recommendation or the parity fallback, T0-A
counter evidence would be TSRAM-only; a recorded deferral leaves T0-A with no
ECC-bearing array. The three-array counters can only be simulation evidence
until a cluster build exists.

The path table above pins the T0 blob of `ci/testcases/unittest.yaml`
(`15d4476121a2cde1dad0cc56e09fc0ff252eef0400909fcbc0f3c196f86e4caf`), which
contains the false entries. The LF-normalized SHA-256 of the corrected worktree
file is
`fd395ecd801870f899dd0594229c640ab357d49ef181c5baf055b0246d126662`
(uncommitted); a future T0 source pin must include it.

**Commands used:** `git log --all --oneline -- hw/rtl/libs/VX_ecc_secded.sv
hw/rtl/libs/VX_ecc_ctrl.sv hw/rtl/libs/VX_ecc_ram.sv hw/unittest/ecc
hw/unittest/ecc_ram` (no output), `git ls-tree -r ff550c275 -- hw/rtl/libs
hw/unittest`, `git show --stat ac4382f21`, and
`git merge-base --is-ancestor 73d19ba3d ff550c275` (exit 1).

## 3. Configuration identity

This is a **proposed** T0 configuration derived from the T0 baseline and the
repository defaults. It has been resolved, but not frozen, built, or exercised.

```text
CONFIGS='-DVX_CFG_NUM_CLUSTERS=1 -DVX_CFG_NUM_CORES=16 -DVX_CFG_NUM_WARPS=4 -DVX_CFG_NUM_THREADS=4 -DVX_CFG_ISSUE_WIDTH=4 -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_EXT_TCU_ENABLE -DVX_CFG_EXT_DXA_ENABLE -DVX_CFG_TCU_WGMMA_ENABLE -DWGMMA_NRC=16'
```

The resolver command adds the XLEN input required by `gen_config.py`:

```sh
python ci/gen_config.py --config=VX_config.toml \
  --cflags='-DVX_CFG_XLEN=32 -DVX_CFG_NUM_CLUSTERS=1 -DVX_CFG_NUM_CORES=16 -DVX_CFG_NUM_WARPS=4 -DVX_CFG_NUM_THREADS=4 -DVX_CFG_ISSUE_WIDTH=4 -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_EXT_TCU_ENABLE -DVX_CFG_EXT_DXA_ENABLE -DVX_CFG_TCU_WGMMA_ENABLE -DWGMMA_NRC=16'
```

| Field | Resolved value | Boundary |
|---|---|---|
| XLEN / driver tree | RV32 / `build32` | Not yet built for T0 |
| Clusters × cores | 1 × 16 | T0 topology |
| Warps / threads / issue width | 4 / 4 / 4 | T0 baseline |
| SIMD width / OPCs | 4 / 1 | Resolver result |
| TCU | 4 lanes, 4 blocks, TFR, FP16 + WGMMA | T0 baseline |
| DXA | 2 cores, 2 memory ports | Required by WGMMA double buffering |
| LMEM | 16 KB (`LOG_SIZE=14`, 4 banks) | T0 baseline |
| ICache / DCache | 16 KB / 16 KB | T0 baseline |
| L2 / L3 | Disabled (`0` / `0`) | T0 baseline |
| Graphics | TEX, raster, OM, RTU disabled | Compute-only baseline |
| Platform clock | 400 MHz | Planning value; no STA |
| DSMEM | `VX_CFG_EXT_DSMEM_ENABLED=1` | TOML default; T0 intent not ratified |
| Test SRAM | 256 KB, 4096 × 512 bits, no ECC | RTL, not a resolver field |

**Configuration identity artifact:** [proposed-config.txt](evidence/g100-t0-g1-audit-2026-11-20/proposed-config.txt),
SHA-256 `cd5336232fa98454009574121e0b25cc98feb3530a50675874ba98738c154cda`,
6,006 bytes with LF endings (the Windows capture's trailing CRLF hashed
`7824b5185203543cc4637ae7950b526caad856f99283f624dd825679e53f41e4`), resolver
exit 0 on 2026-11-20 using CPython 3.14.0 and
`ci/gen_config.py` at the pinned hash. This is a reproducible resolver output,
not a T0 build stamp or a frozen configuration.

## 4. Tool identity

No G100-T0 build has been run for this audit, so no T0 toolchain bundle is
pinned. The only complete tool/environment identity available is the earlier
1×4 discovery run. Using it for T0 would be an assumption until a T0 build
repeats it.

| Field | Discovery-run identity | T0 status |
|---|---|---|
| Host | Ubuntu 24.04.3 LTS under WSL2, Linux 6.18.33.2-microsoft-standard-WSL2, x86_64 | Not yet repeated for T0 |
| C/C++ | GCC/G++ 13.3.0 | Not yet pinned for T0 |
| Build tools | GNU Make 4.3; Python 3.12.3; CMake 3.29.6 | Not yet pinned for T0 |
| Vortex LLVM/Clang | 20.1.8, commit `4c836512a60c0b965bb298104e084cd0f07ca962` | Not yet pinned for T0 |
| Verilator | 5.046 (2026-02-28, revision `v5.046-55-g1264184fb`) | Not yet pinned for T0 |
| Submodules | cocogfx `e5a599b8c002ec9d792bbb691ac8563bb3fa7372`; cvfpu `355c388ed0899643d41194aed22d3bd2c09e84b3` with nested common_cells `6aeee85d0a34fedc06c14f04fd6363c9f7b4eeea`, fpu_div_sqrt_mvp `86e1f558b3c95e91577c41b2fc452c86b04e85ac`, flexfloat `28be2d4fbf41b38fc37763bb6e90a1c88f6aaa61`; hardfloat `aaf5736dffa521603b681fd5853760c671446c85`; ramulator `e62c84a6f0e06566ba6e182d308434b4532068a5`; softfloat `b51ef8f3201669b2288104c28546fc72532a1ea4` | Not yet pinned for T0 |
| Portable dependency closure | **OPEN** | **OPEN** |
| T0 build/configuration stamp | None | **ABSENT** |
| T0 built artifacts | None | **ABSENT** |

## 5. Workload identity

The workload source is pinned, but every recorded execution below is the earlier
1×4 discovery experiment. There is no 1×16 T0 invocation.

| Field | Value | Status |
|---|---|---|
| Application | `tests/regression/sgemm_tcu_wg_dxa` | Source pinned |
| Kernel | `kernel.cpp` (`TGM_KERNEL` unset) | Pinned by path hash |
| Dimensions | M=64, N=64; K=64 and K=512 | Proposed T0 workload |
| Types | FP16 input, FP32 output and reference | `common.h` defaults |
| Tensor geometry | `WGMMA_NRC=16`; ITYPE=fp16, OTYPE=fp32 | Pinned |
| Kernel pipeline | Proposed Makefile default: `WGMMA_RS` + `WGMMA_DXA_DOUBLE_BUFFER`; single-buffer rtlsim choice unresolved | **Not selected or run for T0** |
| Input generation | App-generated after `std::srand(50)` | Exact bytes not retained |
| Reference | CPU FP32 reference in `main.cpp` | Source pinned |
| Comparator | Per-output ULP budget `max(12, ceil(5*sqrt(K)))`; zero mismatches required | Source pinned |
| Proposed commands | `make -C tests/regression/sgemm_tcu_wg_dxa run-simx` and `run-rtlsim` with `OPTS='-m 64 -n 64 -k 64'` / `-k 512'` | **Not run for T0** |
| T0 execution result | None | **ABSENT** |
| T0 JTAG test | `hw/unittest/t0_dbg`, CI ID `hw-t0`, xlen 32, `make -C hw/unittest run-t0` | Test exists; single-core debug bench, not a 1×16 array test; no raw T0 log or reviewer linked |

The T0 JTAG test is a bring-up test for the TAP/DTM/DM/SBA path and the 256 KB
test SRAM. Its testbench instantiates one `VX_core`, not the 1×16 T0 array, so
it does not establish full T0 cluster integration. It is not the
`sgemm_tcu_wg_dxa` compute workload and does not substitute for a T0 compute
run.

## 6. Golden-output identity

**Golden-output identity is absent.** The discovery runs generated inputs and a
host reference at runtime, compared them in-process, and printed `PASSED!`.
Neither the input bytes nor the reference/output bytes were archived or hashed.
The same is true for T0: there is no T0 input file, golden vector, output file,
or replay command.

| Identity | Current state |
|---|---|
| Input tensors A/B | Generated by `main.cpp` after `std::srand(50)`; no file or SHA-256 |
| Host FP32 reference | Computed in `main.cpp`; no retained output or SHA-256 |
| Comparator result | `PASSED!` on stdout; no machine-readable result retained |
| Golden manifest | **ABSENT** |
| Replayable golden | **ABSENT** |

A G1-grade T0 run must freeze the exact input and reference bytes, their
SHA-256 values, the host library/RNG identity, the compiler/linker flags, the
command, and the raw output. `PASSED!` alone is a test outcome, not a golden
output identity.

## 7. Independent review gaps

| Review item | Current state |
|---|---|
| Discovery run record | `run-passed-pending-review`; independent reviewer/date **OPEN** |
| T0 source review | No independent source reviewer recorded |
| T0 configuration review | No reviewer; `CONFIGS` not frozen |
| T0 workload review | No reviewer; no T0 run |
| Golden-output review | No golden data to review |
| T0 JTAG test evidence | No raw log, checksum, or reviewer linked |
| G1 evidence package | Not assembled or reviewed |

The T0 commit message reports a clean Verilator T0 test pass in 1m24.9s, but
that is a commit narrative, not retained evidence. It is not treated as an
independent or G1-accepted result here.

## 8. Parity gaps

The only same-kernel comparison is the earlier 1×4 discovery pair. It is not a
T0 parity result and is not a parity pass.

| K | SimX cycles | rtlsim cycles | Delta | Retired instructions | Parity disposition |
|---:|---:|---:|---:|---:|---|
| 64 | 13,984 | 15,807 | +1,823 (+13.0%) | 21,808 both | Cycles differ; no tolerance |
| 512 | 85,346 | 98,812 | +13,466 (+15.8%) | 153,968 both | Cycles differ; no tolerance |

Additional parity gaps:

- No supported cycle tolerance has been ratified for this workload.
- The pinned `model_parity-wgmma-dxa` definition uses M=N=128, K=64, 32 threads,
  8 warps, and does not set `WGMMA_SINGLE_BUFFER=1`; the workload Makefile says
  the Verilated RTL/FPGA path normally uses the single-buffer variant. The
  intended CI variant and supported parity path remain unresolved.
- There is no G100-T0 SimX/rtlsim pair, no T0 cycle comparison, and no T0
  review of the 1×4 cycle divergence.
- There is no board/FPGA result, post-route timing, utilization, or
  simulation-to-hardware correlation.

## 9. Required to close G1

1. Use a clean checkout/tag of the T0 source pin; record the export/archive
   identity and confirm no T0 source overlays.
2. Freeze the exact T0 `CONFIGS`, resolve it from that checkout, and archive the
   resolver output with the build stamp. Resolve the `EXT_DSMEM` intent and the
   absent ECC implementation before calling the configuration frozen.
3. Build T0 with a pinned toolchain/dependency bundle and retain complete build
   logs, artifact hashes, and the effective compiler/linker flags.
4. Run the T0 `sgemm_tcu_wg_dxa` workload at K=64 and K=512, plus the `hw-t0`
   JTAG test; retain raw logs, exit statuses, input/reference/output hashes, and
   the exact commands.
5. Implement the SECDED codec, counters, ECC bank RAM and testbenches; protect
   LMEM/ICache/DCache and provide T0 ECC evidence — or record a reviewed
   descope. The false CI/checklist references are corrected, but there is no
   ECC implementation to test, and the test-SRAM protection decision is open,
   with the plan recommending SECDED. The ordered work, gates and test-SRAM
   recommendation are in the
   [ECC closure plan](proposals/g100_t0_ecc_closure_plan.md), whose S0
   assumptions were audited against this pin on 2026-11-20. The plan proposes
   the status block and demux inside `VX_t0_dbg_top`, a 64 KB window with
   line-granular reads and total decode, SBA-only writes and TSRAM-only T0-A
   evidence, with the three-array counters to be proven in their own benches;
   these choices remain unsigned. S0 closes only when the [S0 decision
   signoff](evidence/g100-t0-ecc-s0-2026-11-20/signoff.md) is signed. This item
   closes only when that plan's exit criteria are met.
6. Obtain an independent reviewer who is not the author to review/reproduce the
   source, configuration, tools, workload, golden data, and T0 results.
7. Establish a supported parity definition and run a same-source,
   same-configuration, same-input SimX/rtlsim comparison. Keep correctness,
   cycle parity, FPGA closure, and board behavior as separate claims.
8. Keep FPGA/board evidence separate and do not infer it from simulation.

**G1 disposition:** audit started; **not passed**. The commercial G0 hold and
all G4/G5/G6/production holds remain unchanged.
