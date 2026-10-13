# G100 1×4 Discovery Run Record — 2026-10-13

- **Record status:** `run-passed-pending-review`
- **Run class:** SimX and Verilated rtlsim; four separate same-kernel-variant correctness checks
- **Comparison/parity group ID:** `g100-1x4-wgmma-db-k64-k512`. The SimX and rtlsim runs here both used the double-buffered `WGMMA_RS` + `WGMMA_DXA_DOUBLE_BUFFER` kernel at both K values. All four matched instruction counts and passed the host reference; cycle counts differ, so this is a same-kernel correctness/cycle-comparison group, not cycle parity.
- **Purpose:** Check host-reference correctness of the proposed FP16-input/FP32-output `sgemm_tcu_wg_dxa` experiment at M=N=64, K=64 and K=512 under the approved discovery topology.
- **Source owner / operator:** Kubeworkz / Codebuff agent
- **Independent reviewer / review date:** OPEN
- **Date:** 2026-10-13 (local host date)

## Source and configuration

| Item | Identity / result |
|---|---|
| Repository | `https://github.com/kubeworkz/grxgpu` |
| Commit / root tree | `ff5790806973a1586478531c3d6710a0fa614384` / `9ecc11da261a4f7ad952761d6d6768e54086d7bd` |
| Checkout | Clean Linux-native clone at `/home/kubew/g100-build-ff579080`; detached at the pinned commit. Root worktree remained clean during source runs. |
| Configuration | RV32, 1 cluster × 4 cores, 4 warps, 8 threads, issue width 4, L2 enabled, 2 DXA cores, TCU+DXA+WGMMA enabled, NRC=16. Full resolver output: [resolved-config.txt](resolved-config.txt), SHA-256 `e8434432378156e106a12b6a97f9a647592b462d78fdee9523fad8ca08d3ae71`. |
| SimX kernel defines | `WGMMA_RS` + `WGMMA_DXA_DOUBLE_BUFFER`. |
| rtlsim kernel defines | Same `WGMMA_RS` + `WGMMA_DXA_DOUBLE_BUFFER` defines; runtime build includes `SIMULATION` and `SV_DPI`. This double-buffered RTL variant is not the Makefile's documented default rtlsim invocation; the single-buffered runs remain separately retained as independent correctness checks. |
| Submodules | `cocogfx` e5a599b8c002ec9d792bbb691ac8563bb3fa7372; `cvfpu` 355c388ed0899643d41194aed22d3bd2c09e84b3 with nested common_cells 6aeee85d0a34fedc06c14f04fd6363c9f7b4eeea, fpu_div_sqrt_mvp 86e1f558b3c95e91577c41b2fc452c86b04e85ac, flexfloat 28be2d4fbf41b38fc37763bb6e90a1c88f6aaa61; `hardfloat` aaf5736dffa521603b681fd5853760c671446c85; `ramulator` e62c84a6f0e06566ba6e182d308434b4532068a5; `softfloat` b51ef8f3201669b2288104c28546fc72532a1ea4. |
| Ramulator FetchContent | yaml-cpp `yaml-cpp-0.7.0`, commit 0579ae3d976091d7d664aa9d2527e0d0cff25763; spdlog `v1.11.0`, commit ad0e89cbfb4d0c1ce4d097e134eb7be67baebb36; argparse `v2.9`, commit 997da9255618311d1fcb0135ce86022729d1f1cb. These were fetched by the pinned Ramulator CMake configuration. |
| Host | Ubuntu 24.04.3 LTS under WSL2, Linux kernel 6.18.33.2-microsoft-standard-WSL2, x86_64; GCC/G++ 13.3.0, GNU Make 4.3, Python 3.12.3, CMake 3.29.6. |
| Vortex tools | Vortex LLVM/Clang 20.1.8, commit 4c836512a60c0b965bb298104e084cd0f07ca962; Verilator 5.046 (2026-02-28, revision v5.046-55-g1264184fb). |
| Configure | Fresh `build32`; `../configure --xlen=32 --tooldir="$HOME/tools"`. Used already-installed tools; the pinned source did not have `ci/toolchain_install.sh`, and the toolchain was not reinstalled. |
| Generated artifacts | host executable SHA-256 `49acd485c6c9c3cb06e33d4ce21964f96efc80bd5036c5f2487c1f904764502a`; kernel.elf `ae5cf29074925b6c340657fca8fef24ba11405b5cb57867b5f2b58792433d532`; kernel.vxbin `205412bae00edfb8734d8b17ffc65bdae575a704be2641e1578908057e497e4c`; `libsimx.so` `cb8a1311a9bba5d0e03745c0f4f25f189904b1c5e0c1bb48f6e7456aa66281cf`; `librtlsim.so` `73ae5349ce23d713b02e028ba0271a5c21e2104304a07da0b41bbc0e5659a70f`; `libramulator.so` `8ebfe0d7ec93f72a5b79c8a9f1a51002f33a3933b93f4490101f972e76a05986`; SoftFloat archive `f16bec3e8a32ab256cc3a5706c1f52b497d31ba7f7d0a59ad31b846adc66eb34`. |

## Commands and results

All commands were executed from `build32/` in the clean pinned checkout with:

```sh
CONFIGS='-DVX_CFG_NUM_CLUSTERS=1 -DVX_CFG_NUM_CORES=4 -DVX_CFG_NUM_WARPS=4 -DVX_CFG_NUM_THREADS=8 -DVX_CFG_ISSUE_WIDTH=4 -DVX_CFG_L2_ENABLE -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_EXT_TCU_ENABLE -DVX_CFG_EXT_DXA_ENABLE -DVX_CFG_TCU_WGMMA_ENABLE -DWGMMA_NRC=16'
```

| Check | Exact make invocation | Exit | Result |
|---|---|---:|---|
| SimX K=64, double-buffered | `CONFIGS="$CONFIGS" make -C tests/regression/sgemm_tcu_wg_dxa run-simx OPTS='-m 64 -n 64 -k 64'` | 0 | `PASSED!`; `PERF: instrs=21808, cycles=13984, IPC=1.559`; elapsed 137 ms. |
| rtlsim K=64, double-buffered | `CONFIGS="$CONFIGS" make -C tests/regression/sgemm_tcu_wg_dxa run-rtlsim OPTS='-m 64 -n 64 -k 64'` | 0 | `PASSED!`; `PERF: instrs=21808, cycles=15807, IPC=1.380`; elapsed 106404 ms. |
| SimX K=512, double-buffered | `CONFIGS="$CONFIGS" make -C tests/regression/sgemm_tcu_wg_dxa run-simx OPTS='-m 64 -n 64 -k 512'` | 0 | `PASSED!`; `PERF: instrs=153968, cycles=85346, IPC=1.804`; elapsed 958 ms. |
| rtlsim K=512, double-buffered | `CONFIGS="$CONFIGS" make -C tests/regression/sgemm_tcu_wg_dxa run-rtlsim OPTS='-m 64 -n 64 -k 512'` | 0 | `PASSED!`; `PERF: instrs=153968, cycles=98812, IPC=1.558`; elapsed 308605 ms. |

Each workload was checked against the regression host FP32 reference, and the app printed `PASSED!`. The inputs were generated by the app using its fixed `std::srand(50)` flow; generated input/output bytes were not saved or hashed, so binary-level input/golden replay is still OPEN.

For both K values, the double-buffered SimX and rtlsim variants retired the same number of instructions and independently passed the host reference; rtlsim took 1,823 more cycles at K=64 (+13.0%) and 13,466 more cycles at K=512 (+15.8%) than SimX. This is observed cycle divergence, not parity. No tolerance is asserted, and the counts are not evidence of FPGA timing or performance.

## Build attempts and warnings

- Initial clean SimX attempt stopped during simulator compilation because the Ramulator source checkout did not yet contain its CMake FetchContent dependencies (`spdlog/spdlog.h` missing). This attempt has no workload result. The pinned `make -C third_party ramulator/libramulator.so` fetched/built the dependencies and succeeded on retry.
- First rtlsim build command exceeded the 600-second shell wait and ended by SIGHUP during Verilator generation. It is retained as [rtlsim-k64-initial-timeout.log](rtlsim-k64-initial-timeout.log); this was not treated as a test result. The original single-buffered K=64/K=512 rtlsim checks are separately retained as `rtlsim-k64.log` and `rtlsim-k512.log`. A subsequent same-kernel double-buffered rtlsim rebuild completed after about 39 minutes; K=64 and K=512 both passed and are retained in the comparison logs cited below.
- The successful Verilator 5.046 build emitted six warnings: two `PINCONNECTEMPTY`, one `WIDTHTRUNC` in `VX_dxa_unit.sv:143`, and three `UNUSEDSIGNAL` in the same source. The logs retain them; no warnings were suppressed for this run.

Raw output for the original four variant-specific checks and resolver data are in this directory. [SHA256SUMS](SHA256SUMS) covers those original logs/config and failed attempts. The same-kernel double-buffered comparison logs are retained here as [SimX K=64](g100-simx-k64-db.log), [rtlsim K=64](g100-rtlsim-k64-db.log), [SimX K=512](g100-simx-k512-db.log), and [rtlsim K=512](g100-rtlsim-k512-db.log); their SHA-256 values are in [g100-db-run-sha256.txt](g100-db-run-sha256.txt). The corresponding test Makefile build line in each log records the kernel defines. The separate Ramulator timeout/retry build logs are also retained.

## Bounded disposition

These results establish eight local correctness passes for the proposed discovery experiment only (four original variant-specific checks and four same-kernel double-buffered checks), on pinned Vortex commit `ff579080...`, the exact recorded 1×4 resolver config, this WSL2/toolchain environment, and the exact workloads shown. Both backends match retired instruction counts at K=64/K=512, but measured cycle counts differ and no parity tolerance is asserted. The runs are **run-passed-pending-review**, not independently reproduced or sponsor-ratified acceptance results. They do not establish cycle parity, FPGA fit/timing, board behavior, production readiness, customer suitability, final SKU requirements, funding, tapeout, or silicon evidence. The worktree under test is not a branch of the primary Windows checkout; all raw evidence and this record are preserved in this workspace for review.
