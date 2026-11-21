# T-IF-10a — CP ring encoder/decoder round-trip (L0)

**Result: PASS at L0 — host wire conformance only. No T0 CP or device
evidence.** This is a test-level result, not a G3 gate result.

**Prepared by:** engineering agent supporting the G100-T0 program; not an
approver and not a signatory.
**Selection:** T-IF-10a is the next host-only interface test. It covers the
CP ring's 4-byte header, all 11 mandatory opcodes, the profile trailer, and a
five-command line without needing the G-3 revision, ECC S0, a T0 board, or a
T0 CP.

## Run identity

| Field | Value |
|---|---|
| Test ID | `T-IF-10a` |
| Contract row | IF-10 — CP ring 64 B lines, 4 B header, at most 5 commands/line, 1 queue, 11 mandatory opcodes, capability-gated `0x0B`/`0x0C`; no fault channel |
| Source commit | `8d41bf8ec29738cfefd96702850b54b1c8b003da` |
| Source tree | `ff7b74939bd97e2778090c04167fc466be20389a` |
| T0 configuration hash | N/A — no T0 image; the host test uses the generated `build32/hw/VX_config.vh`, SHA-256 `8ca973adb8b59e63c97da418fc3030f4c2e22a5be39fb661a775d8af445961f0` |
| Tier | L0 — host simulation |
| Seed | N/A — fixed wire vectors, no random input |

## Toolchain and build stamp

| Item | Identity |
|---|---|
| Simulator | `Icarus Verilog version 12.0 (stable)` |
| Build stamp | No product or T0 image was built. The testbench and the RTL decoder copy were compiled directly by Icarus from the pinned sources below; the source hashes plus the simulator version are the build identity. |
| Runner | `run.sh`, SHA-256 `3ba613727dc5d2991acd770f1267c837f2a0aaf9be444ff04c7efda9e0ecafa5` |
| Testbench | `tb.sv`, SHA-256 `ba18380613a28172c930116486a38eb91d0d89e5ac6e161d209fc95d5b2d5fdb` |
| Package under test | [`hw/rtl/cp/VX_cp_pkg.sv`](../../../../../hw/rtl/cp/VX_cp_pkg.sv), SHA-256 `52c1d58f2421ec590071a108145854c717285aa2e3868647733f6db9a9301180` |
| Original decoder | [`hw/rtl/cp/VX_cp_unpack.sv`](../../../../../hw/rtl/cp/VX_cp_unpack.sv), SHA-256 `9cbea90ce3843d4308690c23133eaa0149ff80d065339fa7041d3567026b5de1` |
| Icarus decoder copy | `VX_cp_unpack_icarus.sv`, SHA-256 `db42a6b39e682313c318359a02c2f33e74b0270caa0c3fcf70f74cd2d73c7dba` |
| Include macros | [`hw/rtl/VX_define.vh`](../../../../../hw/rtl/VX_define.vh), SHA-256 `3429928bdb40b5178603855203a802da0178c7e968b7dc580a5c3f859cead252` |
| Generated config | `build32/hw/VX_config.vh`, SHA-256 `8ca973adb8b59e63c97da418fc3030f4c2e22a5be39fb661a775d8af445961f0` |
| Generated types | `build32/hw/VX_types.vh`, SHA-256 `3ddda2b27d17c9b98aa57f67fc924fb7739fd864a88d77d871cccddd12e8757a` |

## Command and tier

```text
wsl -e bash -lc 'cd docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-10a && bash run.sh > /tmp/t-if-10a.log 2>&1; rc=$?; cp /tmp/t-if-10a.log run.log; exit $rc'
```

Exit status: `0`. Tier: L0, host only. No T0 CP, board, ECC, or G-3 path.
The WSL-side temporary log avoids the Windows redirect truncation observed
while preparing this evidence; `run.log` is the copied raw output.

The testbench writes a 64-byte line using the package's own
`cmd_size_bytes()` and the frozen header/trailer layout, then drives the real
`VX_cp_unpack` decoder. It also checks each size against a separate hard-coded
11-opcode table, so a wrong package size cannot round-trip consistently with
itself. It checks opcode, flags, reserved header word, each carried argument
byte, profile trailer, returned size, and that encoding does not touch bytes
beyond the command. The five-command case uses five profiled NOPs (60 B) and
confirms the remaining 4 B stay untouched.

## Icarus adaptation

Icarus 12 rejects `automatic` variables declared inside the RTL
`always_comb`. The filed `VX_cp_unpack_icarus.sv` is a copy of the original
with only the `automatic` qualifiers removed, the `off` initialization made an
explicit assignment (so it is re-evaluated each time), and a header note
added. A diff against the CRLF-normalized original contains only those
changes. The combinational decode logic is otherwise unchanged.

Icarus also emits non-fatal `constant selects in always_* processes` notes;
the run completes with exit 0.

## Raw log

Filed as [`run.log`](run.log), 2,529 bytes, SHA-256
`f768a6bc20ecf480353673711ed9ceb6a800078c114b657ab3bf08b2133fb2a8`.
The log contains the simulator identity, source hashes, build command, all
test output, and the simulator's non-fatal adaptation notes; it is unedited.

## Result against the criterion

| Check | Measured |
|---|---|
| Mandatory opcodes | 11/11, `0x00`–`0x0A` |
| Round-trip cases | 26 checks: 10 unprofiled non-NOP cases, 11 profiled cases, and 5 commands in one line; the testbench asserts this count |
| NOP handling | NOP is tested profiled (`F_PROFILE`); an unprofiled zero-header NOP is separately confirmed to be the padding sentinel |
| Command sizes | `4/28/28/28/20/20/12/8/20/28/12` for `0x00`–`0x0A`, plus 8 B when profiled; independently checked against the testbench table and matched `cmd_size_bytes()` |
| Argument carry | Only the declared payload bytes compared; FENCE's 4-byte arg0 and NOP's no-arg form handled explicitly |
| Five-command line | 5 × profiled NOP = 60 B, five decodes, 4 B untouched pad |
| Mismatches | 0 |

**PASS at L0** for the host wire round-trip, with 0 mismatches.

## Accountable owner and date

**Software/runtime lead** — accountable owner for IF-10. Record prepared by
the engineering agent, 2026-11-21; not an approval or signature.

## Open deviations and carries

- **Testbench encoder, RTL decoder.** The encoder is the L0 conformance
  testbench; the decoder is the real `VX_cp_unpack` via the Icarus copy. The
  production runtime encoder was not instrumented.
- **No T0 CP.** T0-A instantiates no CP, so this is software/wire conformance,
  not device evidence.
- **T-IF-10b remains OPEN.** Rejection of a sixth command in one line is not
  exercised here.
- **T-IF-10c remains OPEN.** Capability gating for optional opcodes `0x0B` and
  `0x0C` is not exercised here.
- **G-3 remains OPEN.** Fault channel, byte-exact DMA tail, and FENCE
  semantics are revision-gated and not tested.
- **IF-10 overall remains OPEN** until T-IF-10b/c and the CP integration
  evidence exist. No G3 result is claimed.

## Reproduction

From the repository root, with the source tree at the identity above:

```text
wsl -e bash docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-10a/run.sh
```

The runner creates and removes a temporary `.vvp`; it writes no build
artifacts into the repository. Re-running reproduces 11 opcodes and 26
round-trip checks. No frozen G2 file, v1 contract file, or source RTL is
modified by this record.
