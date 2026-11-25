# 8×16 hierarchical rtlsim — cluster-facade cache-fill verification (L0/L2)

**Result: PASS at the model level on the 8×16 hierarchical rtlsim model.** Every
cache fill that allocated an MSHR slot received a response, no fill was
delivered to an unallocated slot, and the traced demo completed with
`PASSED!`. **This run was not repeated after the overlay moved into git** — see
[Not re-run after the overlay was committed](#not-re-run-after-the-overlay-was-committed).

**Prepared by:** engineering agent supporting the G100-T0 program, 2026-11-25;
not an approver and not a signatory.
**Selection:** 8 clusters × 16 cores is the first supported configuration
above 1×1 that drives the cluster's memory-master port with real traffic, so it
is where the facade's inverted request/response wiring showed up as fills that
never found the slot waiting for them. The 1×1 model passes with or without
the correction; only the multi-cluster model distinguishes them.

## Run identity

| Field | Value |
|---|---|
| Test ID | None — model-level verification of one RTL correction. This is not a plan test row; no plan row is moved by this record. |
| Contract row | None claimed. The model under test is the one T-G-5a, T-G-5b and T-S-4 would run against, but none of those rows is exercised or claimed here. |
| Source base | Staged tree extracted on the build host from `vortex-repo.tar.gz` (built 2026-11-23 from the working tree; `.git` excluded). The host had **no git metadata**, so there is no base commit for the run itself. The run-log directory names it by the tarball. |
| Source tree | The staged `hw/rtl/VX_cluster.sv` (the original cluster, renamed to `VX_cluster_impl` by the staging script) is byte-identical to [`hw/rtl/VX_cluster.sv`](../../../hw/rtl/VX_cluster.sv) in this checkout, compared 2026-11-25. The overlay [`.buildonly/VX_cluster.sv`](../../../.buildonly/VX_cluster.sv) that replaced the facade is committed as `68f10f8f7`. |
| T0 configuration | `VX_CFG_NUM_CLUSTERS=8`, `VX_CFG_NUM_CORES=16`, `VX_CFG_SOCKET_SIZE=1`, `VX_CFG_NUM_WARPS=4`, `VX_CFG_NUM_THREADS=4`, `VX_CFG_L2_ENABLE=false` (L2/L3 passthru), `ICACHE_MSHR_SIZE=16`, `L1_MEM_PORTS=1`, asserted against the staged `VX_config.toml` before the build |
| Tier | L0/L2 — hierarchical RTL simulation (rtlsim). **Not** a device result, and not the `xrt`/AFU path. |
| Seed | None — the demo is deterministic. Trace-only: `--x-initial unique` seeds uninitialised arrays randomly, which is why 19 response prints appear before reset (see [Trace reconciliation](#trace-reconciliation)). |

## Toolchain and build stamp

| Item | Identity |
|---|---|
| Host | aarch64, 32 cores, 123 GiB RAM, 415 GiB free on the build filesystem |
| Compiler | `gcc (GCC) 16.2.0` from conda-forge aarch64, exposed as `gcc`/`g++` under a private `bin` |
| Verilator | 5.054 from the pinned tag tarball, built from source |
| Model build | hierarchical Verilation (`--hierarchical`, `--hierarchical-threads 1`, `--output-split 10000`), 8 child models, then `make -C build/sw/runtime/rtlsim RT_THREADS=… CONFIGS="-DVX_DBG_DEBUG_LEVEL=3 -DDBG_TRACE_CACHE -DDBG_TRACE_MEM"` |
| Artifacts | `librtlsim.so` 164 MB and `libvortex-rtlsim.so`, built by the stages in [`rebuild-8x16.sh`](../../../.buildonly/rebuild-8x16.sh) |
| Build identity | No artifact hashes are filed: the model and its log live on the build host, not in this repository. |

## Command and tier

```text
VORTEX_DRIVER=rtlsim ./demo -n1
```

Exit status `0`. The run was traced with the `DBG_TRACE_CACHE` /
`DBG_TRACE_MEM` build flags above, producing 467,160 trace lines over 717 s of
wall time, covering clusters 0–7 × sockets 0–15 (all 128 sockets).
Tier: L0/L2, model only. No board, no ECC path, no `xrt` surface.

## Test result

The cluster facade in the hierarchy-block build places a flat module
(`VX_cluster_flat`, which compiles the original cluster as `VX_cluster_impl`)
behind an interface-preserving `VX_cluster`. The facade's `g_mem_bus` block
had been copied from the flat module's own mirror block, which reads its local
interface; at the facade the roles are reversed, so the assignment directions
were inverted. Requests were read off an interface nothing drove and responses
were driven into it, while the flat block's request outputs drove the same
wires. A fill therefore went out and its response never reached the MSHR slot
that had allocated for it.

The correction drives the two ends of the port the right way round: requests
out to the interface, `req_ready`/`rsp_valid`/`rsp_data` in from it, and
`rsp_ready` back out.

### Fill counters

| Counter | Value |
|---|---|
| icache `fill-req` (slots allocated) | 516 |
| raw `fill-rsp` trace prints | 531 |
| of those, cycle-1 pre-reset prints with no allocated slot | 19 |
| requests still in flight when the trace ended | 4 |
| matched request/response pairs | 512 |
| responses to an unallocated slot | **0** |
| `invalid fill` | **0** |
| assertions | **0** |
| demo exit status | 0, `PASSED!` |
| retired instructions | 21504 (128 cores × 168) |
| cycles | 12255 |
| IPC | 1.755 |

### Trace reconciliation

The raw print count is 531 against 516 requests, so the counts are reconciled
per bank rather than compared directly:

- **19 prints are artefacts of the trace window, not fills.** They appear on
  cycle 1, before reset, with random addresses and data, from Verilator's
  `--x-initial unique` seeding of the uninitialised tag/data arrays. No slot is
  allocated at that point, so they cannot be queued responses.
- **4 requests were still in flight at the end of the trace.** All four are
  flush fills to address `0x0`, issued at cycles 33275, 34007, 35837 and 66581,
  i.e. after the last response was observed.
- **512 matched pairs** remain, and every response matched a slot that had
  allocated for it. There is no unmatched-slot response in the trace.

### Not comparable to the earlier reference

`logs/trace4-demo.log` from before the correction reported `instrs=168,
cycles=733`. Those counters reflect a single warp, not 128 cores, so the
before/after cycle and IPC numbers are not a comparison and no speedup is
claimed. The evidence for the correction is the fill reconciliation above, not
a cycle delta.

## Raw log

**Not filed with this record.** The trace and the demo log are on the stopped
build host at `logs/demo-8x16-clusterfix.log`, together with
`logs/rtl-8x16-compile-j16.log` and the finish-stage output. The host was
stopped for cost reasons before they were copied into the repository, its
public address changed with the stop, and no SHA-256 of the log is available
here.

By the filing rules in the G3 index, a result without its log cannot move a
plan row. This record therefore documents a model-level observation for one
correction; it is not evidence for any G3 gate row and claims none.

## Result against the criterion

| Check | Measured |
|---|---|
| Every allocated fill received a response | 512 matched pairs; 4 still in flight at trace end |
| No response without an allocated slot | 0 |
| `invalid fill` counter | 0 |
| Assertions during the run | 0 |
| Demo completes | Exit 0, `PASSED!` |
| Retired instructions | 21504 = 128 cores × 168, matching the per-core count of the 1×1 run |
| Model reaches all clusters | Trace covers clusters 0–7 × sockets 0–15 |

**PASS at the model level** for the facade correction on the 8×16 hierarchical
model, with the counters reconciled as above.

## Not re-run after the overlay was committed

The correction was first made in the *staged* copy of the overlay on the build
host, where the tree had no git metadata. On 2026-11-25 the same correction was
re-derived in this checkout and the overlay was committed:

| Commit | Content |
|---|---|
| `68f10f8f7` | `hw: version the hierarchical-build overlay facades` — the four overlay `.sv` files, with `g_mem_bus` driving requests out and responses in |
| `68d551dbe` | the staging script that installs them |
| `5cc2e34fb` | host details replaced with placeholders in that script |

**The 8×16 run above was made before those commits and has not been repeated
against the committed overlay text.** What exists for the committed text is a
static check only, run on 2026-11-25: all 14 assignments in `g_mem_bus` were
compared against the flat block's declared port directions (0 faults) and
against the flat's mirror block (exact inverse). A static check does not
replace the run; it only confirms the committed text is the text the run
exercised.

No re-run was possible in this session: the aarch64 build host is stopped, and
rebuilding the model takes roughly three hours (about 18 minutes of Verilation
plus a memory-gated per-translation-unit compile) before the 717 s traced demo
can start. A re-run is required before this record is cited for the committed
overlay.

## Open deviations and carries

- **Raw log not filed.** See above; this blocks citing the record for any gate
  row until the log is copied in and hashed.
- **`model_parity` not run.** `ci/testcases/model_parity.yaml` (the SimX/rtlsim
  parity gate) was not executed for this change. The facade correction does not
  touch SimX and no cycle-model change is claimed, but parity is unverified
  here.
- **Single application.** One `demo -n1` run, one configuration. No OpenCL
  workload, no `sgemm`, no frozen G2/G3 corpus.
- **L2/L3 disabled.** With passthru L2 the L1 tag is the only port-routing
  information, so the run does not exercise the L2 arbiter or the L2 facade.
- **Not the coverage path.** RTL coverage is `xrt`; this is `rtlsim`, which
  bypasses the AFU surface.
- **Trace-only reconciliation.** The 19 pre-reset prints and the 4 in-flight
  requests were classified from the trace, not from a counter the model reports
  separately.

## Accountable owner and date

**Verification lead** — model and parity evidence. Record prepared by the
engineering agent, 2026-11-25; not an approval or signature.

## Reproduction

On an aarch64 host with at least 400 GiB free and 120 GiB RAM:

```text
# stage the tree and install the overlay
/…/.buildonly/rebuild-8x16.sh stage
/…/.buildonly/rebuild-8x16.sh configure
# Verilate, then compile the giants one at a time, then the rest
/…/.buildonly/rebuild-8x16.sh generate
/…/.buildonly/rebuild-8x16.sh orchestrate
# traced model, then the demo
make -C build/sw/runtime/rtlsim RT_THREADS=4 \
  CONFIGS="-DVX_DBG_DEBUG_LEVEL=3 -DDBG_TRACE_CACHE -DDBG_TRACE_MEM"
VORTEX_DRIVER=rtlsim ./demo -n1
```

The script asserts the 8×16 TOML before building, so a different configuration
stops it instead of producing a differently-shaped model. Re-running
reproduces 516 fill requests, 512 matched responses, `invalid fill=0`, exit 0
and `PASSED!`; the trace line count and wall time are host-dependent.
