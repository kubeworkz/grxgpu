# 8×16 hierarchical rtlsim — cluster-facade cache-fill observation (unfiled)

**Status: UNFILED OBSERVATION — no PASS is claimed.** One traced 8×16
hierarchical rtlsim run completed with `PASSED!`, and every fill in it that
completed matched an allocated MSHR slot. The raw log is not in this
repository, and the run has not been repeated against the overlay as
committed. Under the filing rules of the G3 index, a result without its log
cannot move a plan row, so this record reports no gate result and is not
evidence for one.

**Prepared by:** engineering agent supporting the G100-T0 program, 2026-11-25;
not an approver and not a signatory.
**Selection:** 8 clusters × 16 cores is the first supported configuration
above 1×1 that drives the cluster's memory-master port with real traffic. The
1×1 model builds and passes with the facade wired either way, so only a
multi-cluster model can distinguish the correction.

## How to read the claims here

Each claim carries one of three markers:

- **observed** — read from the run, its trace, or a file in this checkout.
- **inferred** — a reading of the evidence that another explanation could also
  fit. The inference is stated, not hidden.
- **unverified** — could not be checked in this session and is not relied on.

## Run identity

| Field | Value |
|---|---|
| Test ID | None — model-level observation of one RTL correction. No plan row is moved by this record. |
| Contract row | None claimed. The model under test is the one T-G-5a, T-G-5b and T-S-4 would run against, but none of those rows is exercised or claimed here. |
| Source base | **observed (host)**: staged tree extracted on the build host from `vortex-repo.tar.gz`, built 2026-11-23 from the working tree with `.git` excluded. The host had no git metadata, so there is no base commit for the run itself. |
| Source tree | **observed**: the staged `hw/rtl/VX_cluster.sv` (the original cluster, which the staging script renames to `VX_cluster_impl`) is byte-identical to [`hw/rtl/VX_cluster.sv`](../../../hw/rtl/VX_cluster.sv) in this checkout, compared 2026-11-25 from the tarball. |
| Overlay identity | **inferred, not verified**: the overlay that the host ran is the correction committed as `68f10f8f7`. The host was unreachable when the correction was re-derived here, so the committed file was not diffed against the staged copy that the run used; only the direction correction itself is known to be the same. |
| T0 configuration | **observed, two sources.** Asserted by the staging script against the staged TOML: `NUM_CLUSTERS=8`, `NUM_CORES=16`, `SOCKET_SIZE=1`, `NUM_WARPS=4`, `NUM_THREADS=4`, `L2_ENABLE=false`. Read from `VX_config.toml` and the resolved headers in this checkout, not asserted at build time: `VX_CFG_ICACHE_MSHR_SIZE = 16` ([`VX_config.toml:197`](../../../VX_config.toml)) and `VX_CFG_L1_MEM_PORTS`, which is an expression ([`VX_config.toml:232`](../../../VX_config.toml)) that resolves to `1` for this configuration. |
| Tier | L0/L2 — hierarchical RTL simulation (rtlsim). **Not** a device result, and not the `xrt`/AFU path. |
| Seed | None — the demo is deterministic. Uninitialised state is not: the rtlsim build passes `--x-initial unique --x-assign unique` ([`sim/rtlsim/Makefile:140`](../../../sim/rtlsim/Makefile)), so uninitialised arrays start at random values. |

## Toolchain and build stamp

| Item | Identity |
|---|---|
| Host | **observed (session, unfiled)**: aarch64, 32 cores, 123 GiB RAM, 415 GiB free on the build filesystem |
| Compiler | **observed**: `gcc (GCC) 16.2.0` from conda-forge aarch64, exposed as `gcc`/`g++` under a private `bin`; the staging script refuses any other version |
| Verilator | **observed**: 5.054 from the pinned tag tarball, built from source |
| Model build | **observed**: hierarchical Verilation (`--hierarchical`, `--hierarchical-threads 1`, `--output-split 10000`), 8 child models, then the runtime driver rule in `build/sw/runtime/rtlsim` with `CONFIGS="-DVX_DBG_DEBUG_LEVEL=3 -DDBG_TRACE_CACHE -DDBG_TRACE_MEM"` |
| Artifacts | **observed (host)**: `librtlsim.so` 164 MB and `libvortex-rtlsim.so` |
| Build identity | No artifact hashes are filed: the model, its stamp and its log stayed on the build host. |

## Command and tier

**observed (host):**

```text
VORTEX_DRIVER=rtlsim ./demo -n1
```

Exit status `0`. Traced with the cache/memory trace flags in the build above,
which produced 467,160 trace lines over 717 s of wall time and covered
clusters 0–7 × sockets 0–15 (all 128 sockets). Both figures are from the
session that watched the run; the log itself is unfiled.
Tier: L0/L2, model only. No board, no ECC path, no `xrt` surface.

## What the correction is

The hierarchy-block build places a flat module (`VX_cluster_flat`, which
compiles the original cluster as `VX_cluster_impl`) behind an
interface-preserving `VX_cluster`. The facade's `g_mem_bus` block had been
copied from the flat module's own mirror block, which reads its local
interface. At the facade the roles are reversed, so every assignment ran the
wrong way: requests were read off an interface nothing drove, while the flat
module's request outputs drove the same wires and its response inputs were
driven from the interface.

Consequence, **inferred** from that wiring rather than observed directly: a
fill left the cache and its response never reached the MSHR slot that had
allocated for it, so the requester waited forever. The 1×1 model does not
expose it because both models build; only traffic across clusters does.

The correction drives the two ends of the port the right way round: requests
out to the interface, `req_ready`/`rsp_valid`/`rsp_data` in from it, and
`rsp_ready` back out.

## Fill counters

**observed** from the trace and the demo output:

| Counter | Value |
|---|---|
| icache `fill-req` (slots allocated) | 516 |
| raw `fill-rsp` trace prints | 531 |
| of those, cycle-1 prints before reset with no allocated slot | 19 |
| requests with no response in the trace | 4 |
| matched request/response pairs | 512 |
| responses matched to an unallocated slot | **0** |
| `invalid fill` counter | **0** |
| assertions | **0** |
| demo exit status | 0, `PASSED!` |
| retired instructions | 21504 (128 cores × 168) |
| cycles | 12255 |
| IPC | 1.755 |

The claim this supports is narrow: **512 fills completed and each matched a
slot that had allocated for it, with no invalid fill and no assertion.** It is
not "every fill received a response" — 4 requests received none in the trace
window.

## Trace reconciliation

The raw print count is 531 against 516 requests, so the counts are reconciled
per bank rather than compared directly.

**The 19 cycle-1 prints. observed:** they appear at cycle 1, before reset
releases, carry random addresses and data, and have no allocated slot. The
rtlsim build seeds uninitialised state randomly (`--x-initial unique
--x-assign unique`), so the tag and data arrays hold random values until reset
clears them. **inferred:** that the prints are those pre-reset array contents
being emitted by the trace hook. An alternative would be 19 real responses
arriving on cycle 1, which no allocation could explain.

**The 4 unresponded requests. observed:** no response matched them anywhere in
the trace, and their addresses are `0x0`, issued at cycles 33275, 34007, 35837
and 66581. **inferred, two parts:** (a) that they are cache flush fills rather
than fetches — the address and the late cycles suggest a flush, but the trace
alone does not identify the requester; (b) that they were still outstanding
when the trace ended rather than dropped. The trace cannot separate
"outstanding" from "lost", and reading them as outstanding is consistent with
the 512 matched pairs and the clean `invalid fill` counter, nothing stronger.

**512 matched pairs. observed:** each response matched a slot that had
allocated for it; 516 − 4 outstanding = 512.

## Reference log without a comparison

An earlier log (`logs/trace4-demo.log`) reported `instrs=168, cycles=733`.
That log is not filed, and its configuration is not established from the run
record that survives — so **no before/after comparison is drawn**, and no
speedup is claimed. The evidence for the correction is the fill reconciliation
above, not a cycle delta. The 21504 instructions are exactly 128 × 168, i.e.
each of the 128 cores retired the same 168 instructions the earlier run
reported for its single core, which is a consistency check on the model's
shape, not a performance claim.

## Raw log

**Not filed with this record.** The trace and the demo output are on the
stopped build host under `logs/` (`demo-8x16-clusterfix.log`,
`rtl-8x16-compile-j16.log`, and the finish-stage output). The host was stopped
for cost before they were copied into the repository, its public address
changed with the stop, and no SHA-256 of any of them is available here.

This is the single largest gap in the record: every number above is a reading
of a log that a reviewer cannot open. Until that log is copied in and hashed,
the counters should be treated as **reported, not independently checkable**,
and the record cannot be cited for any gate row.

## Result against the criterion

| Check | Measured | Mark |
|---|---|---|
| A completed fill always matched an allocated slot | 512 matched pairs | observed |
| A response without an allocated slot | 0 | observed |
| `invalid fill` counter | 0 | observed |
| Assertions during the run | 0 | observed |
| Demo completes | exit 0, `PASSED!` | observed |
| Retired instructions | 21504 = 128 × 168 | observed |
| All clusters exercised | clusters 0–7 × sockets 0–15 | observed |
| Requests outstanding at trace end | 4 | observed |
| Those 4 are outstanding rather than lost | — | inferred |

**Observed pass in the traced run, unfiled.** The counters are consistent with
the correction working at 8×16. They do not constitute a filed result, and no
PASS status is asserted for this record.

## Not re-run after the overlay was committed

The correction was first made in the *staged* copy of the overlay on the build
host, where the tree had no git metadata. On 2026-11-25 the same correction
was re-derived in this checkout and the overlay was committed:

| Commit | Content |
|---|---|
| `68f10f8f7` | `hw: version the hierarchical-build overlay facades` — the four overlay `.sv` files, with `g_mem_bus` driving requests out and responses in |
| `68d551dbe` | the staging script that installs them |
| `5cc2e34fb` | host details replaced with placeholders in that script |

**The 8×16 run above predates those commits and has not been repeated against
the committed overlay text.** For the committed text there is a static check
only, run 2026-11-25: all 14 assignments in `g_mem_bus` were compared against
the flat block's declared port directions (0 faults) and against the flat's
mirror block (exact inverse).

**What that static check does and does not show.** It shows the committed text
encodes the direction correction consistently. It does **not** show the
committed text is byte-identical to the staged file the run exercised — that
comparison needed the host, which was unreachable — and it is not a substitute
for running the model.

No re-run was possible in this session: the build host is stopped, and
rebuilding the model takes roughly three hours (about 18 minutes of Verilation
plus a memory-gated, one-at-a-time compile of the giant translation units)
before the 717 s traced demo can start.

## Open deviations and carries

- **Raw log not filed, no hash.** Blocks citing this record for any gate row.
- **Committed overlay not proven identical to the run's.** See the Overlay
  identity row and the static-check note above.
- **No re-run.** Required before the committed overlay is cited.
- **`model_parity` not run.** `ci/testcases/model_parity.yaml` (the SimX/rtlsim
  parity gate) was not executed for this change. The correction does not touch
  SimX and no cycle-model change is claimed, but parity is unverified.
- **Single application, single configuration.** One `demo -n1` run. No OpenCL
  workload, no `sgemm`, no frozen G2/G3 corpus.
- **L2/L3 disabled.** With passthru L2 the L1 tag is the only port-routing
  information, so the run does not exercise the L2 arbiter or the L2 facade.
- **Not the coverage path.** RTL coverage is `xrt`; this is `rtlsim`, which
  bypasses the AFU surface.
- **Reconciliation is trace-derived.** The 19 pre-reset prints and the 4
  unresponded requests were classified from the trace, not from a counter the
  model reports separately.
- **Cycle/IPC figures uncomparable.** No earlier run of this configuration with
  a filed log exists, so 12255 cycles and IPC 1.755 stand alone.

## Accountable owner and date

**Verification lead** — model and parity evidence. Record prepared by the
engineering agent, 2026-11-25; not an approval or signature.

## Reproduction

**Unverified** — this was not executed in this session. On an aarch64 host with
at least 400 GiB free and 120 GiB RAM, the stages in
[`rebuild-8x16.sh`](../../../.buildonly/rebuild-8x16.sh) reproduce the shape of
the run:

```text
/…/.buildonly/rebuild-8x16.sh stage
/…/.buildonly/rebuild-8x16.sh configure
/…/.buildonly/rebuild-8x16.sh generate
/…/.buildonly/rebuild-8x16.sh orchestrate
make -C build/sw/runtime/rtlsim RT_THREADS=<same value the model was built with> \
  CONFIGS="-DVX_DBG_DEBUG_LEVEL=3 -DDBG_TRACE_CACHE -DDBG_TRACE_MEM"
VORTEX_DRIVER=rtlsim ./demo -n1
```

`RT_THREADS` must equal the Verilation `-j` value baked into the model's
`rtlsim_config.stamp`; a different value makes the driver regenerate and wipe
the model directory. The script asserts the 8×16 TOML before building, so a
different configuration stops it instead of producing a differently-shaped
model.

What a re-run should show, **inferred from the run recorded here and therefore
to be confirmed rather than assumed**: 516 fill requests, 512 matched
responses, 4 unresponded requests at the end of the trace, `invalid fill=0`,
exit 0, and `PASSED!`. Trace line count and wall time are host-dependent.
