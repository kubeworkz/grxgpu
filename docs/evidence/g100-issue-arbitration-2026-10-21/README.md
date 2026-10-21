# G100 Issue-Arbitration Evidence — 2026-10-21

This directory collects the targeted 1-cluster × 4-core `sgemm_tcu_wg_dxa` K=64 issue-arbitration run artifacts. The larger 256×256×64 test is diagnostic evidence, not a SimX/RTLSIM parity pass.

## Results

- SimX completed the 256×256×64 workload and reported correctness `PASSED!`, 347,968 instructions, 210,261 cycles, and IPC 1.655. See [simx-k64-instrumented.log](simx-k64-instrumented.log), [simx-k64-issue-arb-summary.txt](simx-k64-issue-arb-summary.txt), and the full [compressed SimX trace](simx-k64-issue-arb.log.gz).
- The first instrumented RTLSIM run exited 255: `vx_module_load_file(device, kernel_file, &module_)` returned `VX_ERR_INVALID_VALUE`. The exact rejecting validation/reservation check is not identified. [rtlsim-k64-module-load-failed.log](rtlsim-k64-module-load-failed.log) captures the failure.
- GDB later observed the module-loader reservation attempt at address `0x80000000` for `0x1280` bytes. It does not establish why the earlier run failed. See [rtlsim-k64-reservation-debug.log](rtlsim-k64-reservation-debug.log).
- A later raw 600-second retry loaded the image and started the device, then timed out (exit 124); its log ends at about 142k simulated cycles. The raw [module-loaded timeout log](rtlsim-k64-module-loaded-timeout.log.gz), [exit status](rtlsim-k64-module-loaded-timeout.exit.status), and a separate filtered [arbitration trace](rtlsim-k64-arb-events-timeout.log.gz) with its [exit status](rtlsim-k64-arb-events-timeout.exit.status) are included. The filtered trace reaches roughly 471k cycles and reports 347,968 accepted issue events, but ends before completion and has no correctness result. See the [run record](run-record.txt) for the distinction.
- A separate debugger-assisted 64×64×64 RTLSIM workload completed and reported `PASSED!` (21,808 instructions, 13,984 cycles). Its large [debug log](rtlsim-k64-64x64-debug-run.log.gz) is for the smaller workload only.

## Rebuilt image and provenance

The original [kernel ELF](kernel.elf) and freshly emitted [kernel VXBIN](rebuilt-kernel.vxbin) are archived here. The ELF is the regression build output; the VXBIN was emitted into the isolated RTLSIM run directory before execution. SHA-256 digests of both artifacts and all archived logs/status files are recorded in [SHA256SUMS](SHA256SUMS). The three large RTLSIM logs use deterministic gzip compression (`gzip -9 -n`); their listed digests cover the exact compressed files. These hashes identify archived bytes; they do not establish a clean source snapshot. The simulator/test tree was dirty during the runs, and independent review remains open.

`rtlsim-vcd-build-failed.log.gz` records a later attempt to rebuild RTLSIM with full VCD tracing; it failed because the remote filesystem ran out of space. This is a build failure, not workload evidence. `rtlsim_config.stamp.prior` preserves the previous configuration stamp used to distinguish the tracing rebuild attempt.
