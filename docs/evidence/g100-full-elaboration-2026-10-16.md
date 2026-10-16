# G100 full-top Vortex elaboration attempt (2026-10-16)

## Result

The configured full-top Vortex RTL source-generation stage **passed** for the 128-core feasibility candidate. The native SystemVerilog Synlig/Surelog frontend began elaborating the complete hierarchy, but was **stopped after 45m at session cutoff**. It reached approximately 4.1 GB RSS and wrote a 102,207,810-byte frontend log, still expanding FPU/TCU hierarchy. It was interrupted with SIGINT; `frontend.exit` records `-2`. This is not an elaboration pass; no hierarchy check, `check -assert`, synthesis, mapping, area, or timing result is claimed.

## Identity and configuration

The run used the current mutable worktree at commit `09a0f021637329113bd03d8caac32bc191b9338e`. The worktree is dirty, with pre-existing relevant changes in `hw/rtl/core/VX_kmu_arb.sv`, `hw/rtl/dxa/VX_dxa_smem_wr.sv`, and `hw/scripts/gen_sources.sh`; it is not an immutable upstream/source pin. Generated artifacts are under ignored `build32/` and are isolated from tracked files.

Candidate configuration: XLEN=32; 8 clusters × 16 cores = 128 cores; socket size 4; 64 warps/core; 32 threads/warp; L2 enabled at 8 MiB/cluster; TCU + DXA, including TF32/FP8/INT8/MX/sparse/WGMMA defines. Synthesis defines were `SYNTHESIS`, `ASIC`, `YOSYS`. Exact command/config are captured in [run.json](../../build32/g100_elaboration_20261016/run.json).

## Source generation

Upstream Vortex Yosys target `gen-sources` completed through `hw/scripts/gen_sources.sh` and Verilator preprocessing. It staged 269 regular files (254 `.sv`, 8 `.vh`, 3 `.h`, two metadata files, plus two `.v` wrappers; counts depend on whether counting extensions separately), including a non-empty 6,059-byte `Vortex.sv`. Four empty preprocessed `.sv` modules are configuration-gated units. Raw source-generation log: [sourcegen log](../../build32/g100_full_elab_20261016_sourcegen.log). Output tree: `build32/hw/syn/yosys/build_g100_full_128c_20261016_Vortex/src/`.

## Full hierarchy frontend attempt

The command input in [frontend.ys](../../build32/g100_elaboration_20261016/frontend.ys) reads the complete ordered list of 256 preprocessed `.sv`/`.v` files (packages then interfaces then other units), links Surelog UHDM, then requests `hierarchy -check -top Vortex`, `prep -top Vortex`, `check -assert`, `stat`, and RTLIL/JSON outputs. The ordered list SHA-256 is `8dd1eb5201a6218b6b41835a897682055930e0ea14c3b9fa12be9950e6fbdbb3`; script SHA-256 is `74ab8c34bc7f5c496a9b88606a84c366d6727ce85b397fb1909c20ca39b25764`.

- Yosys: 0.46, commit `e97731b9dda91fa5fa53ed87df7c34163ba59a41`.
- Synlig source: `fd4b2bd9510c02c4cf42f8c4c6468c5c0a7dd9e6`.
- Surelog source requested from observed WSL: `37ce1bbf98ca26ba2e18603a271b55ac05e121d5`; binary banner `1.82`.
- The Yosys process remained actively expanding generated hierarchy at the 45-minute cutoff. It was interrupted with SIGINT. Exit status `-2`; raw output and partial Surelog intermediates are retained. No completion status or successful elaboration is claimed.

Raw frontend log: [frontend.log](../../build32/g100_elaboration_20261016/frontend.log). Surelog intermediate data is retained in ignored `build32/g100_elaboration_20261016/slpp_all/`. No generated RTLIL/JSON output was verified. Do not infer success from the source-generation pass or intermediate generate messages.

## Portable toolchain status

A commit-pinned flake is provided in [flake.nix](../../tools/g100-sv-toolchain/flake.nix), with the resolved [flake.lock](../../tools/g100-sv-toolchain/flake.lock) and setup instructions in [README.md](../../tools/g100-sv-toolchain/README.md). The lock pins Yosys, Synlig, Surelog, and Nixpkgs; the Nixpkgs pin (`9b696460ac78b5ccfc17c854d8c976f20456e943`) is a deliberate new lock basis, not a recovered historical pin for the WSL binaries. Synlig's recorded submodule pointers at its pinned revision point to different Yosys/Surelog commits, so the derivation replaces those submodule checkouts with the explicitly pinned source inputs.

The lock was generated from a temporary Linux Git checkout and copied to the worktree. All four locked revisions and NAR hashes were inspected, and `nix-instantiate --parse flake.nix` passed. The actual derivation evaluation/build remains **unverified**: Nix 2.18 could not access the configured daemon socket from this WSL user, and a local-store override could not create its state directory under `/nix`. No successful toolchain build or cross-version compatibility is claimed. The Synlig 0.46 + Surelog 1.82 pairing therefore still requires a build check on a usable Linux Nix host.

## Reproduction and next action

On a Linux Nix host with the repository's source/submodules available:

1. From `tools/g100-sv-toolchain/`, run `nix --extra-experimental-features 'nix-command flakes' build --no-link --print-out-paths` (the lock is already included).
2. Verify `yosys -V`, Surelog banner, plugin loading, and a small SV test before using it on Vortex.
3. Configure an out-of-tree Vortex build, generate the exact 128-core source tree with the documented `EXTRA_CONFIGS`, and run the ordered full-top frontend script under a bounded supervisor that retains logs, exit status, wall time, and peak RSS.
4. Only claim elaboration if the hierarchy check and `check -assert` finish, with unresolved modules limited to documented SRAM black boxes. Mapping and area are separate gates.

Detailed raw inputs, paths, run notes, and limitations are recorded in [run.json](../../build32/g100_elaboration_20261016/run.json). This run is an internal feasibility frontend attempt only, not a GF180 mapped result or production signoff.
