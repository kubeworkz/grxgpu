# G100 Source / Configuration / Workload Evidence Manifest

**Status:** Source/config/workload reproduction specification for discovery. The proposed RV32 1×4 experiment was built and run locally on the pinned source; eight host-reference invocations passed—four original variant-specific checks plus four additional same-kernel comparison checks—pending independent review. This is not a sponsor-ratified product configuration or acceptance result.
**Version:** 0.7 — 2026-10-13
**Reproducibility state:** Source identity, submodule identities, resolved configuration, original single-buffered rtlsim and double-buffered SimX logs, plus same-kernel double-buffered SimX/rtlsim comparison logs are recorded. Independent review, generated input/output hashes, exact dependency/tool bundle closure, a supported parity tolerance, and FPGA implementation evidence remain open. The resolved settings are experiment parameters, not ratified product requirements.
**Execution disposition:** All eight local correctness invocations (K=64/K=512 across SimX and rtlsim, for single-buffered rtlsim and same-kernel double-buffered builds) exited 0 and printed `PASSED!`; see the [dated run record](evidence/g100-discovery-2026-10-13/run-record.md), raw logs and checksums. For the double-buffered same-kernel comparison, retired instruction counts match but cycles differ; this is not a parity pass. The runs are pending independent review. Historical reports remain separately classified and are not evidence for these invocations.
**Scope approval:** [G100 Product Brief](grxgpu_g100_product_brief.md) — Kubeworkz approved compute-only discovery scope on 2026-10-13 only. This manifest does not authorize funding, purchases, tapeout, or production claims.
**Task linkage:** E-301 (scope/evidence inventory) and E-302 (future run and FPGA evidence).

## 1. Reproducibility boundary

This file pins what can be verified from the current GRXGPU Git tree and records a **proposed experiment** configuration/workload. The attached run record establishes that this candidate configuration built and that SimX and rtlsim variants passed the specified host-reference correctness runs in the recorded environment. A same-kernel double-buffered comparison also completed for K=64 and K=512: instructions match, but cycle counts differ. It does not establish cycle parity, FPGA fit or timing, board behavior, or customer-workload suitability; nor does it make the experiment settings product requirements or acceptance criteria. A path hash identifies the checked-in bytes; it is not itself a test result.

**Authoritative content location:** this GRXGPU Git repository. Raw generated binaries, logs, timing reports, waveforms, and board measurements belong in the canonical GRXGPU/Vortex engineering evidence workflow. Add their durable paths/IDs and hashes here only after the runs exist and have been reviewed.

## 2. Source identity — pinned repository snapshot

| Field | Value | Status |
|---|---|---|
| Repository | [GRXGPU source repository](https://github.com/kubeworkz/grxgpu) | Observed origin in current checkout |
| Branch | `e004/supplied-baseline-evidence` | Mutable ref; informational only |
| Commit | [`ff5790806973a1586478531c3d6710a0fa614384`](https://github.com/kubeworkz/grxgpu/commit/ff5790806973a1586478531c3d6710a0fa614384) | Pinned Git commit |
| Root tree | `9ecc11da261a4f7ad952761d6d6768e54086d7bd` | Pinned Git tree |
| Included source scope | Vortex repository content needed by the named test/build definitions; see path/blob table below | Hashes pinned for selected tracked inputs only, not a complete toolchain/dependency closure |
| Submodules / external dependencies | All Git submodules and nested submodules were initialized at the commits recorded in the [dated run record](evidence/g100-discovery-2026-10-13/run-record.md); Ramulator's pinned CMake fetched its tagged yaml-cpp/spdlog/argparse dependencies. Exact portable toolchain/dependency bundle closure remains **OPEN**. | Local configured build succeeded with the environment recorded in the run record |
| Worktree status | Other unrelated modified/untracked files are present | They are not part of commit `ff579080`; do not substitute working-tree versions for pinned blobs |
| Independent source review | **OPEN** | No independent reviewer is recorded |

A clean export for this source scope is the Git commit above, not the mutable worktree. The repository commit ID pins every tracked file in its tree; the path table below highlights the configuration/test inputs relevant to the discovery hypothesis.

### Relevant path hashes

SHA-256 values below are over the committed Git blob bytes as exported by `git show HEAD:<path>`; working-tree copies can differ due to line-ending conversion. Git blob IDs are also provided for direct commit-content identification.

| Path | Git blob (commit `ff579080`) | SHA-256 of committed bytes | Relevance |
|---|---|---|---|
| `VX_config.toml` | `b2be4082f1fff8eb8ecee13b495ae4dab3c24a02` | `b932c482b62d8c40894f0628f5fbb3a50530cd0d74f6d4fb1964d6763d031f9f` | Contains repo defaults and a commented 8×16 G100 flagship preset; defaults are not the four-core candidate. |
| `tests/regression/sgemm_tcu_wg_dxa/Makefile` | `2bfd6f3c9862332e1f53381f41304693d090dfa1` | `3aa417211fe1d613243238723b980aefa14fbd21fc02dda8385d9b9eeca089f5` | Enables TCU/DXA; documents double-buffered WGMMA as SimX-validated and says Verilated RTL/FPGA normally uses `WGMMA_SINGLE_BUFFER=1`; double buffering requires at least two DXA cores. A separate same-kernel double-buffered rtlsim check was run and is recorded below. |
| `tests/regression/sgemm_tcu_wg_dxa/common.h` | `d86fad1d477fdd9a0fb1d4b6097e20b09be79c76` | `6946f87e76b9126d976ed9ef4ef35e7a779028bdf20084ccf7ed0b23db06c51c` | Default `ITYPE=fp16`, `OTYPE=fp32`, `WGMMA_NRC=8`; defines double-buffer stage stride helper. |
| `tests/regression/sgemm_tcu_wg_dxa/main.cpp` | `9c76f4924797b73850e0b9d626e8a0c64bc8536b` | `423b63677ab54f4f57dee8731e1ec2643780e52d1e5a7e2345003106b9cfea88` | Host test parameters, capability guards, generated input/reference, completion timeout and correctness comparison. |
| `tests/regression/sgemm_tcu_wg_dxa/kernel.cpp` | `48cf38ffe8608a2b3d99a992e85aacebf4839b87` | `3a1bbf546ca2b292824f4040666d90e9ee90b3cee0b8b1090160d985d643408b` | WGMMA/DXA kernel source; Makefile defines select its single/double-buffer paths. |
| `tests/regression/common.mk` | `1a83b922f023d68b143cb5e29d921f3714ecfb43` | `c5f242146a859cfae0be68ba0987019b9de213088063e2cb92d1d741a89106ee` | Common build and test conventions/dependencies. |
| `config.mk.in` | `db6ed846a3569b3b9834f559edd472b0264e6990` | `7a0074de17585ddf609ee48808bc30c8b7a4df9774699a64e049e60085f2cb9f` | Build configuration template and tool paths. |
| `ci/gen_config.py` | `f27fce268da6f7a9f80201f3e41d1db1d6295cd8` | `4ae8207a5468a346b2d6856765b266e2024b8720d8ddc79782832813405480e9` | Canonical resolver used to confirm generated configuration values below. |
| `ci/blackbox.sh` | `e8135c703d0e33c028c0d6ad91560446cfd92893` | `29692dcbfd4332dc9178a81db5a46a3192f993189f7391391574cdb6fe45886c` | Documents CLI-to-macro mapping; the direct make invocation below avoids ambiguity about Make variables. |
| `sw/common/tensor_cfg.h` | `8ab90ed47114a3e7e2878c1ef884f3e40ddf6cdc` | `8a654f8dad6bec5004c043b469bbf7cab2d2d688de5ae42cc8c2250a6e040d72` | Resolves WGMMA host geometry from threads, input type, and NRC. |
| `sw/runtime/simx/Makefile` | `65ec2c4c7a2e5cd88795af8a9d7680af0ab73825` | `eefd2bab7846916f5d102a61ace6855f05e47361e03ad5594da6c975b0173630` | Propagates CONFIGS to SimX runtime. |
| `sim/simx/Makefile` | `2e935fd9bbd368d5843b37a659391c44c76d595d` | `69c1bd7541fbe115c09831c2ae3a301be1842fc05f0a936ec65a5d627cd994cd` | Builds SimX with the resolved configuration. |
| `sim/rtlsim/Makefile` | `2ef0d54a58d7c7721a77127f4184217a1999d6ff` | `445bef351320714af552e5c5f60e1533d9c5a0e8d20627c5c73883e8ec7e6def` | Adds the RTL simulation flags and resolves the same Vortex configuration. |
| [`ci/testcases/dxa.yaml`](../ci/testcases/dxa.yaml) | `d23d6eb882683578b60f98e3c21352836b2062e5` | `e9ab516ea95a085d7338671d39fcfefe68b79ba4672b68a7a3741fa32ddae19f` | Contains DXA/WGMMA cases including model-parity coverage; the local working file is modified and is explicitly not the pinned CI definition. |

**Hash-generation command:** for example, `git show ff5790806973a1586478531c3d6710a0fa614384:VX_config.toml | sha256sum`. Each SHA-256 above was computed directly from the committed blob, not the mutable working-tree copy.

## 3. Proposed experiment configuration — resolved and locally exercised; not sponsor-ratified

The sponsor approved investigating a compute-only **one cluster × four cores** topology with TCU and DXA enabled, and evaluating `sgemm_tcu_wg_dxa` at K=64 and K=512 as candidate discovery tests. This does not ratify every implementation setting below as a product configuration or acceptance criterion. The repository defaults are 8 clusters × 16 cores, 4 warps, 4 threads, and L2 disabled; the commented flagship preset is not the discovery experiment. The table below records one reproducible proposed experiment, resolved against `VX_config.toml` and the canonical `ci/gen_config.py` at commit `ff579080`; each explicit setting is an experiment choice unless marked as part of the approved scope.

### Build-time inputs

For an executable reproduction of this proposed experiment (not a sponsor-ratified product configuration), use an isolated clean checkout/worktree at the pinned commit, configure a fresh RV32 build tree, and run the test commands from that generated build directory. The primary working checkout may contain unrelated edits; do not build from it. From the clean pinned source root on a supported Linux/WSL build host:

```sh
git worktree add --detach ../grxgpu-g100-ff579080 ff5790806973a1586478531c3d6710a0fa614384
cd ../grxgpu-g100-ff579080
mkdir -p build32 && cd build32
../configure --xlen=32 --tooldir="$HOME/tools"
```

The pinned commit used for the recorded run does not contain `ci/toolchain_install.sh`; the successful run used the preinstalled toolchain versions recorded in the [run record](evidence/g100-discovery-2026-10-13/run-record.md). On a fresh host, follow the repository setup docs and provision/build the toolchain using a matching supported source procedure before running the app. Re-run `../configure --xlen=32 --tooldir="$HOME/tools"` when the source/config or build-participating files change. Record actual tool/dependency versions because their installation bundle is not pinned by the source commit. Use this single base CONFIGS value for the candidate runs and resolver check:

```sh
CONFIGS='-DVX_CFG_NUM_CLUSTERS=1 -DVX_CFG_NUM_CORES=4 -DVX_CFG_NUM_WARPS=4 -DVX_CFG_NUM_THREADS=8 -DVX_CFG_ISSUE_WIDTH=4 -DVX_CFG_L2_ENABLE -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_EXT_TCU_ENABLE -DVX_CFG_EXT_DXA_ENABLE -DVX_CFG_TCU_WGMMA_ENABLE -DWGMMA_NRC=16'
```

From source root, the pinned resolver check is `ci/gen_config.py --config=VX_config.toml --cflags='-DVX_CFG_XLEN=32 -DVX_CFG_NUM_CLUSTERS=1 -DVX_CFG_NUM_CORES=4 -DVX_CFG_NUM_WARPS=4 -DVX_CFG_NUM_THREADS=8 -DVX_CFG_ISSUE_WIDTH=4 -DVX_CFG_L2_ENABLE -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_EXT_TCU_ENABLE -DVX_CFG_EXT_DXA_ENABLE -DVX_CFG_TCU_WGMMA_ENABLE -DWGMMA_NRC=16'`. It resolves the hardware values without building or running a test. The test Makefile appends `-DWGMMA_RS -DWGMMA_DXA_DOUBLE_BUFFER` unless `WGMMA_SINGLE_BUFFER=1` is supplied; it also ensures TCU/DXA/WGMMA are enabled and supplies 4 warps / ISSUE_WIDTH if missing. They are already explicit here. `-DVX_CFG_L2_ENABLE` is the canonical input spelling (also exposed by `blackbox.sh --l2cache`); the generator emits `VX_CFG_L2_ENABLED=1`. Do not pass `_ENABLED=1` as a substitute config input.

| Resolved field | Value | Source/meaning |
|---|---|---|
| XLEN / driver build tree | RV32 / `build32` | parity gate and repo testing convention |
| `VX_CFG_NUM_CLUSTERS` × `VX_CFG_NUM_CORES` | `1 × 4` (4 total cores) | discovery-scope topology; cores are per cluster |
| `VX_CFG_SOCKET_SIZE` | `1` | TOML default; not overridden |
| `VX_CFG_NUM_THREADS` / `VX_CFG_NUM_WARPS` / `VX_CFG_ISSUE_WIDTH` | `8 / 4 / 4` | proposed experiment settings; app launches ISSUE_WIDTH warps |
| `VX_CFG_SIMD_WIDTH` / `VX_CFG_NUM_TCU_LANES` / `VX_CFG_NUM_TCU_BLOCKS` | `8 / 8 / 4` | resolver expressions from threads and issue width |
| `VX_CFG_L2_ENABLE` / generated `VX_CFG_L2_ENABLED` | enabled / `1` | explicit override; default L2 is disabled |
| `VX_CFG_L2_SIZE` / `VX_CFG_L2_NUM_BANKS` | `1,048,576` bytes / `1` | TOML default size; resolver result for the selected topology |
| `VX_CFG_EXT_TCU_ENABLED` / `VX_CFG_EXT_DXA_ENABLED` | `1 / 1` | required extensions |
| `VX_CFG_TCU_TYPE` / `VX_CFG_TCU_WGMMA_ENABLED` / `VX_CFG_TCU_FP16_ENABLED` | `TFR / 1 / 1` | TOML defaults and explicit WGMMA enable |
| `VX_CFG_NUM_DXA_CORES` / `VX_CFG_DXA_MEM_PORTS` | `2 / 2` | proposed worker setting; two workers required by fused A+B double-buffered fetch |
| App-level `ITYPE` / `OTYPE` / `WGMMA_NRC` | `fp16 / fp32 / 16` | `common.h` type defaults plus explicit NRC; not VX hardware macros |
| Kernel pipeline | Double-buffered WGMMA + `WGMMA_RS` on both SimX and rtlsim for the comparison group; the documented single-buffered rtlsim configuration was also run separately | Run-passed-pending-review; same-kernel correctness checks passed, instruction counts match, and cycles differ. No cycle-parity result is claimed |
| L3, graphics | disabled | TOML defaults; outside the approved compute-only scope |
| Remaining hardware config inputs | no extra candidate overrides | resolved from pinned TOML; full generated output is reproducible using the resolver command above |
| Board/FPGA part/constraints | **OPEN** | no candidate board selected or demonstrated |

The resolver output was checked, then this proposed configuration was configured and built in a clean Linux-native checkout at the pinned commit. The local correctness outcomes and environment are recorded in the [dated run record](evidence/g100-discovery-2026-10-13/run-record.md). These runs do not establish cycle parity, independent reproduction, FPGA timing/resource closure, or a fully pinned portable tool/dependency bundle; those remain **OPEN**.

## 4. Proposed workload and acceptance boundary — discovery runs recorded; acceptance remains open

The pinned [DXA CI definitions](../ci/testcases/dxa.yaml) contain a separate `model_parity-wgmma-dxa` case at M=N=128, K=64, threads=32, warps=8, ISSUE_WIDTH=4, NRC=16. The commands below propose M=N=64 and K=64/512 as one runnable discovery experiment; those dimensions/settings make the commands concrete and are not sponsor-ratified product requirements or acceptance criteria. They are not the same case as CI. The pinned test Makefile documents double-buffered WGMMA as the SimX path and says the Verilated rtlsim/FPGA path normally uses `WGMMA_SINGLE_BUFFER=1`. The original single-buffered rtlsim checks follow that guidance. A separate same-kernel comparison was also run with the Makefile's double-buffered defaults on both backends; both passed host-reference correctness with matching instruction counts but different cycles. Neither group is a cycle-parity assertion.

**CI definition caveat:** the pinned `model_parity-wgmma-dxa` entry does not set `WGMMA_SINGLE_BUFFER=1`; the generic parity runner executes both drivers using the case CONFIGS. That appears inconsistent with the Makefile comment prescribing the single-buffer variant for rtlsim. The source definitions alone do not establish whether the CI case intentionally tests the double-buffer RTL path, is stale, or is expected to fail. Do not treat its presence as evidence of a supported/running parity path. Resolve this source/test-definition mismatch and inspect the actual effective app/kernel build flags before making a parity claim or using the CI case as the reproduction procedure.

From `build32/`, following a successful configure and dependency setup as above, the four exact invocations below produced the original discovery results. They are recorded for reproducibility, **not approved as product acceptance tests and not a parity assertion**. Outcomes are in the [dated run record](evidence/g100-discovery-2026-10-13/run-record.md). A separately recorded same-kernel comparison uses default double-buffered defines for both backends; see that run record for commands and logs.

```sh
CONFIGS='-DVX_CFG_NUM_CLUSTERS=1 -DVX_CFG_NUM_CORES=4 -DVX_CFG_NUM_WARPS=4 -DVX_CFG_NUM_THREADS=8 -DVX_CFG_ISSUE_WIDTH=4 -DVX_CFG_L2_ENABLE -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_EXT_TCU_ENABLE -DVX_CFG_EXT_DXA_ENABLE -DVX_CFG_TCU_WGMMA_ENABLE -DWGMMA_NRC=16' make -C tests/regression/sgemm_tcu_wg_dxa run-simx OPTS='-m 64 -n 64 -k 64'
CONFIGS='-DVX_CFG_NUM_CLUSTERS=1 -DVX_CFG_NUM_CORES=4 -DVX_CFG_NUM_WARPS=4 -DVX_CFG_NUM_THREADS=8 -DVX_CFG_ISSUE_WIDTH=4 -DVX_CFG_L2_ENABLE -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_EXT_TCU_ENABLE -DVX_CFG_EXT_DXA_ENABLE -DVX_CFG_TCU_WGMMA_ENABLE -DWGMMA_NRC=16' make -C tests/regression/sgemm_tcu_wg_dxa run-simx OPTS='-m 64 -n 64 -k 512'
CONFIGS='-DVX_CFG_NUM_CLUSTERS=1 -DVX_CFG_NUM_CORES=4 -DVX_CFG_NUM_WARPS=4 -DVX_CFG_NUM_THREADS=8 -DVX_CFG_ISSUE_WIDTH=4 -DVX_CFG_L2_ENABLE -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_EXT_TCU_ENABLE -DVX_CFG_EXT_DXA_ENABLE -DVX_CFG_TCU_WGMMA_ENABLE -DWGMMA_NRC=16' make -C tests/regression/sgemm_tcu_wg_dxa WGMMA_SINGLE_BUFFER=1 run-rtlsim OPTS='-m 64 -n 64 -k 64'
CONFIGS='-DVX_CFG_NUM_CLUSTERS=1 -DVX_CFG_NUM_CORES=4 -DVX_CFG_NUM_WARPS=4 -DVX_CFG_NUM_THREADS=8 -DVX_CFG_ISSUE_WIDTH=4 -DVX_CFG_L2_ENABLE -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_EXT_TCU_ENABLE -DVX_CFG_EXT_DXA_ENABLE -DVX_CFG_TCU_WGMMA_ENABLE -DWGMMA_NRC=16' make -C tests/regression/sgemm_tcu_wg_dxa WGMMA_SINGLE_BUFFER=1 run-rtlsim OPTS='-m 64 -n 64 -k 512'
```

Each app target compiles the host app and kernel and rebuilds the requested runtime with the listed hardware CONFIGS. The two SimX builds use the Makefile's double-buffered WGMMA defaults; the two original rtlsim builds explicitly set `WGMMA_SINGLE_BUFFER=1`, selecting the documented single-buffered RTL path. The separate same-kernel comparison rebuilt the workload with double-buffered defaults for rtlsim as well. The rtlsim model adds `-DSIMULATION -DSV_DPI`. The source `main.cpp` derives CTA warps from `VX_CFG_ISSUE_WIDTH`, validates runtime core/thread capabilities and workload tiling, generates inputs with `std::srand(50)`, computes a CPU FP32 reference, and prints `PASSED!`/returns 0 only if comparison errors are zero. The original variant-specific runs are separate correctness checks; the same-kernel comparison reports cycle differences and does not assert parity.

| Field | Proposed experiment / status |
|---|---|
| Regression app and source | `sgemm_tcu_wg_dxa`; `kernel.cpp` selected (`TGM_KERNEL` unset) |
| Proposed dimensions | M=64, N=64, K=64 and M=64, N=64, K=512; for NT=8, FP16, NRC=16, `tensor_cfg.h` resolves xtileM=8, xtileN=16, tileK=8; CTA_M=32 and these dimensions satisfy host divisibility checks |
| Input/output types | FP16 / FP32 (`common.h` defaults) |
| Input generation | Host-generated after `std::srand(50)`; exact bytes still depend on host C library and are not archived here |
| Reference and comparator | CPU FP32 reference in `main.cpp`; per-output ULP budget `max(12, ceil(5*sqrt(K)))`; zero mismatches required to print `PASSED!` and return 0 |
| Driver/kernel variants | Original checks: SimX double-buffered and rtlsim single-buffered; separate same-kernel comparison: double-buffered on both drivers. All K values passed host-reference correctness. Same-kernel retired-instruction counts match, but cycles differ; no parity claim |
| CI definition (not this experiment) | pinned model-parity case uses M=N=128, K=64; its shape/config differs and it does not pass `WGMMA_SINGLE_BUFFER=1`. This conflicts with the Makefile comment describing the Verilated RTL variant; effective flags/support status remain **OPEN** |
| Golden/input hashes | **OPEN** — runtime-generated buffers were not archived/pinned; the app reported host-reference correctness. |
| Result/log/exit code | **Recorded:** all eight invocations exited 0 and printed `PASSED!`; see [run record and retained logs](evidence/g100-discovery-2026-10-13/run-record.md). Pending independent review. |
| Performance, cycles, timing, resources | Simulated instruction/cycle summaries are recorded per run; no cross-driver parity claim or FPGA timing/resource measurement. FPGA evidence remains **OPEN**. |
| Customer use / quality / SLA | **OPEN — engineering discovery correctness workload only** |

### Historical results kept separate

The [G100 tapeout plan](grxgpu_g100_tapeout_plan.md) describes K=64/K=512 rtlsim results and a 128-core SimX K=16…512 sweep. Those remain **historical report claims** until exact source/config/tool/input identities and raw logs are independently pinned and reproduced. They are not reruns under this commit's manifest, not FPGA closure, and not customer acceptance evidence.

## 5. E-301 / E-302 completion checklist

Before E-301 can close, record named product/engineering owners, approved discovery requirements versus TBD values, source/config/workload identities, risk/feasibility classification, and a separate fund/defer decision for any work beyond the currently approved discovery boundary.

The local run record is linked above and is marked `run-passed-pending-review`, not an E-302 closeout. Before any E-302 pass is recorded, independently review/reproduce the relevant claims and complete remaining evidence using the copyable template in §6, including:

- exact source commit and clean-tree/archive identity, plus any overlay/test-only source hashes;
- resolved config/macros, driver/backend, `CONFIGS`, `ARGS`, compiler flags, and whether WGMMA double buffering is enabled;
- toolchain/dependency versions and platform, including host OS/kernel and relevant simulator/runtime versions;
- exact workload dimensions, types, seed/input/golden hashes, reference/tolerance and output comparison;
- complete command, exit status, raw immutable log path/hash, observed correctness result, and any warnings/failures;
- for FPGA, exact part/board, constraints, generated bitstream checksum, synthesis/P&R reports, timing coverage, utilization, and physical versus simulated measurement boundary;
- named independent reviewer and date.

Use supported Vortex regressions and model-parity gates; a successful build alone does not prove the requested behavior. The attached local run record documents eight correctness passes and one same-kernel cycle comparison with measured divergence; this manifest asserts **no independently reproduced, accepted, parity, FPGA, or production pass** until the applicable artifacts are reviewed and approved.

## 6. E-302 run-record template

Copy this record once per independently invoked `(source snapshot, resolved configuration, workload/inputs, execution target)` tuple. Do not combine SimX and RTL/FPGA into one run record; link comparable records with a shared parity or comparison ID. Use `N/A — reason` for inapplicable fields and `OPEN` when evidence is not yet available. Preserve failed, timed-out, and superseded attempts as separate records rather than overwriting them. `run-passed-pending-review` means only that the recorded commands exited and stated checks met their criteria; it is not an accepted/reproduced claim before independent review. `reviewed-reproduced` must identify exactly which claim the reviewer accepted.

### Copyable run record

````markdown
### E-302 run: <unique ID>

- **Record status:** `planned | blocked | run-failed | run-passed-pending-review | reviewed-reproduced`
- **Run class:** `SimX | rtlsim | xrt-hw_emu | xrt-hw | FPGA implementation-only`
- **Comparison/parity group ID:** <ID or N/A>
- **Purpose / claim under test:** <bounded statement; distinguish correctness, parity, timing/resource, or board behavior>
- **Run owner / operator:** <name>
- **Independent reviewer / review date:** <name/date or OPEN>
- **Start/end time (UTC):** <timestamps>

#### A. Source and build inputs

| Item | Exact identity / value | Artifact reference + SHA-256 | Status |
|---|---|---|---|
| Source repository / remote | <URL or repository identity> | <...> | <...> |
| Commit and root tree | <full IDs> | <...> | <...> |
| Export/archive | <clean checkout, archive format/path> | <archive SHA-256> | <...> |
| Worktree status | <clean or complete modified/untracked path list> | <diff/patch hash if applicable> | <...> |
| Source overlays/generated inputs | <path, origin, reason; include every non-commit input> | <per-file SHA-256> | <...> |
| Submodules/dependencies | <URL + exact commit/version for each> | <lock/manifest hash> | <...> |
| Build-tree/configure identity | <build directory, XLEN, configure command, config stamp> | <config stamp and generated header hashes> | <...> |
| Hardware configuration input | <literal CONFIGS and any command-line shape overrides> | <saved command/hash> | <...> |
| Resolved configuration | <full resolver output, not only selected macros> | <output file SHA-256> | <...> |
| Kernel/application build defines | <including WGMMA_NRC, WGMMA_RS/SS, WGMMA_DXA_DOUBLE_BUFFER or single-buffer choice> | <compile command/log hash> | <...> |
| Compiler/linker flags | <complete effective flags, including XLEN/target and optimization> | <build log hash> | <...> |
| Built artifacts | <host executable, kernel ELF/VXBIN, runtime/simulator or FPGA image> | <each artifact SHA-256> | <...> |

#### B. Workload, inputs, and expected behavior

| Item | Exact identity / value | Artifact reference + SHA-256 | Status |
|---|---|---|---|
| Application/test source | <path(s) and commit/blob identity> | <...> | <...> |
| CI/test harness identity | <category/case ID, runner revision and invocation, or N/A with reason> | <case/runner source hashes> | <...> |
| Workload parameters | <app, M/N/K or full arguments, launch/grid/block, repetition count> | <...> | <...> |
| Data types and memory layout | <input/accumulator/output types, alignment/layout> | <...> | <...> |
| Input generation | <generator source/version, seed, RNG/runtime, generation command> | <generator and generated input hashes> | <...> |
| Golden/reference | <reference implementation/version and generation method> | <reference source + output hashes> | <...> |
| Correctness rule | <exact comparator, tolerance/ULP rule, required error count> | <test source/report hash> | <...> |
| Expected result | <specific pass criteria; do not use an unqualified “works”> | <...> | <...> |

#### C. Execution environment and exact commands

- **Execution backend/target:** <SimX / Verilator rtlsim / xrt emulation / physical FPGA>
- **Host OS/kernel/architecture:** <...>
- **CPU, RAM, relevant host limits:** <...>
- **Tool versions:** <compiler, Python, Verilator, simulator/runtime, FPGA tools, and versions/commits>
- **Dependency/tool installation identity:** <pinned bundle, container/image digest, or complete setup record>
- **Relevant environment variables:** <names and non-secret values; never include credentials>
- **Build command(s), from stated working directory:**
  ```sh
  <literal command(s), including CONFIGS, make target, variables and clean/rebuild choices>
  ```
- **Execution command(s), from stated working directory:**
  ```sh
  <literal command(s), including driver, workload args, timeout and repetition>
  ```
- **Exit status for each command:** <integer; retain each stage separately>
- **Warnings/errors:** <count/category and disposition; link full unedited output>

#### D. Results and retained artifacts

| Result/artifact | Value or immutable path | SHA-256 | Interpretation/status |
|---|---|---|---|
| Complete build log(s) | <...> | <...> | <...> |
| Complete run log(s) | <...> | <...> | <...> |
| Correctness output | <error count, PASS/FAIL text, comparator summary> | <...> | <...> |
| Retired instructions / cycles | <per driver and measurement interval; N/A with reason> | <raw counter/log hash> | <...> |
| Performance counters / timing | <counter set, units, collection method; distinguish simulated cycles from measured time> | <...> | <...> |
| Other generated outputs | <waveforms, traces, CSV, reports, crash dumps> | <per-artifact SHA-256> | <...> |
| Build outcome | `success | failed | incomplete | blocked`; state whether required artifacts were produced | <build-log hash> | <...> |
| Execution outcome | `pass | fail | incomplete | blocked`; exact observed behavior, separately from build outcome | <run-log hash> | <...> |
| Deviations / anomalies | <difference from planned source/config/command, or none> | <patch/log hash> | <...> |

Keep raw logs unedited and immutable; summaries do not replace them. Record failed and timed-out runs, including their exit codes and the first useful error. `run-passed-pending-review` is not a reproduced/accepted result until the independent reviewer signs the evidence and the exact pass claim is bounded to this record.

#### E. RTL-simulation fields (complete for `rtlsim`)

- **RTL simulator and version/build:** <e.g., Verilator version, executable digest>
- **Effective RTL parameters / generated `.vh` hash:** <...>
- **DPI/runtime libraries and versions:** <...>
- **Simulation defines/options/thread count:** <include `SIMULATION`, `SV_DPI`, tracing/perf settings>
- **RTL elaboration/build result and exit status:** <...>
- **Functional result:** <...>
- **SimX comparison record ID, if parity is claimed:** <ID or N/A>

#### F. FPGA implementation / board fields (complete when FPGA evidence is claimed)

- **Evidence scope:** `synthesis-only | place-and-route | bitstream | hardware execution`; do not promote one stage to another.
- **Device:** <vendor, exact part, package, speed grade>
- **Board:** <model, revision, serial or controlled inventory ID; N/A for implementation-only>
- **Top/configuration:** <top module, clusters/cores, enabled blocks, memory/interface scope>
- **Constraints:** <clock periods, I/O constraints, exception files, source and SHA-256>
- **FPGA toolchain:** <vendor tool, exact version/build, license feature if relevant>
- **Build scripts and literal commands:** <...>
- **Implementation outputs:** <bitstream/image path and SHA-256; N/A if not generated>
- **Utilization:** <LUT/ALM, FF, BRAM/URAM, DSP and other relevant resources; report tool values and denominators>
- **Timing:** <clock targets, WNS/TNS, failing endpoints, unconstrained paths, timing-coverage summary, report hashes>
- **Build/implementation logs and exit status:** <immutable paths + SHA-256>
- **Hardware execution (only if performed):** <programming transcript, device/runtime/driver versions, exact workload, board boot/status, correctness output, measured clock/power/thermal methodology and raw captures>
- **Simulation-versus-board boundary:** <state explicitly which measurements are simulated, post-route estimates, or physical observations>
- **Limitations / unclosed paths:** <...>
````

### Comparison-group record

For any SimX↔RTL parity claim, add one group summary after the individual records:

| Field | Value |
|---|---|
| Group ID / linked run IDs | <...> |
| Same source, resolved config, workload arguments, input bytes, kernel defines? | <yes/no; enumerate justified differences> |
| Retired-instruction counts | <SimX, rtlsim, exact match?> |
| Cycle counts and comparison formula | <SimX, rtlsim, denominator, absolute/relative delta> |
| Allowed tolerance and its source | <case definition/default; cite or explicitly label newly proposed> |
| Functional and parity disposition | <separate results; exact instruction match does not imply cycle parity> |
| Reviewer / date | <...> |
| Raw comparison script/output and hashes | <...> |

For FPGA evidence, link the FPGA implementation or board-execution record to its own SimX and/or `rtlsim` records when comparing them. Report implementation closure, RTL-simulation correctness, model parity, and board execution as separate claims with separate evidence. Missing raw artifacts, a nonzero command exit, a dirty/unknown source snapshot, incomplete timing coverage, or a reviewer gap must remain visible as `incomplete`, `blocked`, or `failed`; it must not be summarized as a pass.
