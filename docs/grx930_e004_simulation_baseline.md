# GRX930 E-004 Simulation Baseline

**Status:** E-004 remains **open / blocked on authoritative source identity and independent reproduction**. Clean Verilator builds and the full-SoC/UART/GEMM runs passed against the supplied dependency snapshot; the snapshot has no Git metadata or owner attestation, so this is reproduced snapshot evidence, not authoritative-source closure.
**Run date:** 2026-10-12 (follow-up to the 2026-10-11 candidate runs)
**Backlog:** [E-004 — Reproduce the checked-in simulation baseline](grxgpu_engineering_task_list.md)
**E-002 inventory:** [GRX930 Source and Hardware Evidence Manifest](grx930_evidence_manifest.md)

## 1. Source identity and claim boundary

The C930 tree is a copied, untracked source snapshot. The expected CPU dependency at `../rv64imac/RTL` is now present: 38 `.sv` source files, two `.sv.bak` backups, and one `.v` file (41 files total). The build wildcard `*.sv` includes the 38 `.sv` sources and excludes the backups and `.v` file. There is no nested `.git` metadata. The sorted-file SHA-256-list fingerprint of the 38 SystemVerilog files is `1b64a3531afc643e0462b92fb280ccd074cd4343b52f5028dc4728b8549698e4`; the fingerprint across all 41 files is `38f9b6fb7079998df23eece6ffaadd9bcc08c96886e961fd73d0a58aeb702170`. These digests identify the supplied snapshot, not its upstream origin, owner, or authoritative status. Builds and tests below use this supplied dependency snapshot and the present C930 files; they do not establish concurrent multicore correctness or product/board readiness.

E-004 can close only after the source owner confirms the authoritative CPU/SoC revision and dependencies, and another engineer independently reproduces the documented build, UART echo, and UART-GEMM cases against that baseline.

## 2. Four-core SoC suite on the supplied dependency snapshot

A clean Verilator generation was completed from `grx930/c930` with `make verilate-soc4 VERIL4_OUT=build/e004_authoritative_clean/verilator4`; Verilator 5.051 devel generated the four-core model from 38 CPU `.sv` files, 25 C930 SoC/NPU RTL files and two harness files. The WSL2 Ubuntu C++ build used g++ 13.3.0 (`-std=c++17 -O1 -pthread`) in the isolated output directory. Build log: [clean SoC Verilator build](../grx930/c930/build/e004_authoritative_clean_build.log), exit 0, SHA-256 `ef5a194e1357d9baeab57dca2462550f3cb0249c6067932b04f99e70955e8ba1`. The generated Verilator metadata is at [`Vc930_soc4_verilator__verFiles.dat`](../grx930/c930/build/e004_authoritative_clean/verilator4/Vc930_soc4_verilator__verFiles.dat). A clean `verilate-soc4` target generates RTL/C++ but does not compile/link/run the Linux executable by itself; those steps were performed separately. The final Linux executable SHA-256 is `3e4eb4e1d8d5c42b71dd0400123c82481226c641b5a7207857a95bcc96a77d6a`. It ran with the [boot image](../grx930/c930/sw/boot.hex) (SHA-256 `350f4980c33edd249de23aad95ff419808f6a9be1361ff13c76dedd2eda5fe05`), [phase-1 firmware](../grx930/c930/sw/tb4_phase1_fw.hex) (SHA-256 `670620b248fd225b9c0ff9f74d3e42b3bfb0609c683416ce89038a1d24f132ca`), and [phase-2 firmware](../grx930/c930/sw/tb4_phase2_fw.hex) (SHA-256 `3e4b5abf1e7dbb89fb08372c21b4b91a2a76274ed20f613b66659a2eff6a4091`) in the isolated output directory.

The suite execution command was:

```sh
./Vc930_soc4_verilator suite
```

Run log: [fresh four-core suite run](../grx930/c930/build/e004_authoritative_clean_suite_run.log) — exit 0, SHA-256 `567b6f6058c6e50672249208f274db18e76757e914098f22e92cde7fbe3463b4`. Phase 1 queued/drained four GEMMs in 1,853 cycles; phase 2 completed in 3,205 cycles. INT8, FP16, BF16 and INT4 error masks were all zero. The test firmware executes on CPU0, so this is not proof of concurrent four-core behavior. The original historical timeout remains unexplained.

The prior candidate-model rerun remains documented separately in the [E-002 manifest](grx930_evidence_manifest.md); do not conflate it with this fresh build against the supplied `rv64imac/RTL` snapshot.

## 3. Supplied-snapshot single-core UART and GEMM tests

A separate single-core UART model was generated with Verilator 5.051 devel (`v5.050-194-ga3553e7be`) using the same supplied 38-file CPU dependency snapshot, 25 C930 RTL files and two harness files. The Verilator generation command/source list is recorded in [`Vc930_soc_verilator__verFiles.dat`](../grx930/c930/build/e004_authoritative_uart/verilator/Vc930_soc_verilator__verFiles.dat), and the [UART model generation log](../grx930/c930/build/e004_authoritative_uart_verilate.log) has SHA-256 `cadc0d810a836be03f481890fb18e4cb738e38ba66b4e96bb231ac923bc26435`. Compilation with g++ 13.3.0 used `-std=c++17 -O1 -pthread` and the installed Verilator runtime; the final Linux executable SHA-256 is `af78b1dcea92b3bd1ee3810592d3994d111ecfffa4c6ec1526121617086a16b6`. Firmware HEX inputs were the archived images used in the earlier candidate-only runs; their SHA-256 values are `63750c981cfb65b6b6c45c272718823ada4642bb243826b9f9f3ba4b317d0b14` (echo) and `dce77ac43de9d8a01a5b9c6c1753965e93d86332ed5d271516645916b79ba675` (GEMM). The build wrapper references `sw/boot.hex`, which is absent when the copied model is run outside `c930/`; Verilator warns about that unused/missing init file. Firmware is loaded through the testbench preload port, and the boot banner and tests completed successfully.

### UART echo

Command:

```sh
./Vc930_soc_verilator firmware_uart_echo_test.hex
```

Run from the isolated model directory with the archived echo HEX input. Exit status 0. The 65-byte boot banner, PING/PONG, ECHO, VERSION, and unknown-command responses passed. Echo firmware has no GEMM command, so the testbench explicitly skips that sweep.

Raw output: [supplied-snapshot UART echo log](../grx930/c930/build/e004_authoritative_uart_echo_run.log) — SHA-256 `1544dd2e164bce2ffa315c884e641d69e8809c2188027c78368d9246994a056f`.

### UART GEMM sweep

Command:

```sh
./Vc930_soc_verilator firmware_uart_gemm_test.hex
```

Run from the isolated model directory with the archived GEMM HEX input. Exit status 0. The banner and UART protocol checks passed, followed by **18/18 GEMM cases**: ten INT8 shapes and two each for INT16, FP16, BF16 and INT4. Every case compares returned results against the testbench C reference.

Raw output: [supplied-snapshot UART-GEMM log](../grx930/c930/build/e004_authoritative_uart_gemm_run.log) — SHA-256 `187f569c8e814c5ce4876a93af3149a6579a8aad1fd6f7f494f171f2e3bc5c24`.

Both fresh UART-model generation and the four-core generation emitted non-fatal Verilator warnings, including multiple-driver and incomplete-case warnings in the supplied dependency / C930 RTL. They remain preserved in the generation logs. These are simulation results for the supplied, fingerprinted snapshot only; provenance and independent reproduction remain outstanding.

## 4. Remaining E-004 work

| Requirement | Current disposition | Evidence still needed |
|---|---|---|
| Supplied CPU snapshot identity | Directory inventory and content fingerprints recorded; no nested Git metadata | Source owner confirmation, original repository/branch/commit or archive provenance, and confirmation of which files (including backups) are supported inputs |
| Clean Verilator SoC build and full-SoC suite | Fresh model generation and WSL C++ compile completed; suite passed, all four masks zero | Independent rerun from a clean environment; confirm exact official source baseline and build recipe |
| UART echo | Passed on supplied CPU snapshot | Independent rerun against owner-confirmed source baseline |
| UART-GEMM | 18/18 passed on supplied CPU snapshot | Independent rerun against owner-confirmed source baseline |
| Independent reproduction | Not done | A second engineer reproduces results using the source identity and evidence manifest |

Do not overwrite or edit historical logs to create a pass. Append future run records with source commit/archive digest, dirty-tree status, exact RTL/firmware/vector digests, tool versions, commands, raw logs, exit status, outcome and reviewer. The dependency has now been supplied locally, but its provenance and owner status remain unverified; keep E-004 open until source identity is confirmed and another engineer independently reproduces the outcomes.
