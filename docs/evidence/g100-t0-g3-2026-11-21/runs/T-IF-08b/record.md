# T-IF-08b — DXA descriptor slot isolation (L0, host address map)

**Result: PASS at L0 — host address-map isolation only. No RTL or T0 device
evidence.** This is a test-level result, not a G3 gate result.

**Prepared by:** engineering agent supporting the G100-T0 program; not an
approver and not a signatory.
**Selection:** T-IF-08b is the natural companion to
[T-IF-08a](../T-IF-08a/record.md). It uses the same production encoder and
minimal runtime stub to write all 16 descriptor slots and to check that no
write crosses a slot boundary. It needs neither the G-3 revision, ECC S0, nor
a board.

## Run identity

| Field | Value |
|---|---|
| Test ID | `T-IF-08b` |
| Contract row | IF-08 — 16 descriptor slots × 24 DCRs, 64-bit base, host encoders match RTL, write-only from host |
| Source commit | `f48e95d16f0d9debdf06295fedb4d81d81474d46` |
| Source tree | `e2b793d0aa33ca140c520e7e1c5362b6418ef5c8` |
| T0 configuration hash | `cd5336232fa98454009574121e0b25cc98feb3530a50675874ba98738c154cda` (resolver hash carried from G1; no T0 image built) |
| Tier | L0 — host unit bench |
| Seed | N/A — fixed descriptors, no random input |

## Toolchain and build stamp

| Item | Identity |
|---|---|
| Compiler | `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0` |
| Build stamp | No product image or RTL image was built. The host harness was compiled from the pinned source hashes below; those hashes plus the compiler identity are the build identity for this run. |
| Runner | `run.sh`, SHA-256 `03e9885c2116525b28f4f7ac51636483fb630aea13e77882eb95126ebc443dbc` |
| Test source | `main.cpp`, SHA-256 `399ecd988968f357cba586b1d25549c1e71176f4cff57f20e1170b7fdf214d70` |
| Runtime stub | `stub/vortex.h`, SHA-256 `981a8b306367f9ad3650a5c162500214adbd6caf8442a70523a9739761cd0b27` |
| Encoder under test | [`sw/runtime/include/dxa.h`](../../../../../sw/runtime/include/dxa.h), SHA-256 `349f9e1e9309705cd209d4263edad21ff9ef1e73c9677740a560d94b113f7543` |
| Meta field map | [`sw/common/dxa_meta.h`](../../../../../sw/common/dxa_meta.h), SHA-256 `b172820148530228a925d96252141e55c6ba3d84a9c7375fb0bc49f46d93089d` |
| DCR ABI constants | [`sw/VX_types.h`](../../../../../sw/VX_types.h), SHA-256 `1647fdc48564b48b06adde771ea9c6039ef49a759801726819855447d1730ac8` |
| RTL field widths | [`hw/rtl/dxa/VX_dxa_pkg.sv`](../../../../../hw/rtl/dxa/VX_dxa_pkg.sv), SHA-256 `efc15a7873a1244e8fd93088e5e21a2cedad7e48dc311046143e20210f8bf37b` |

## Command and tier

```text
wsl -e bash docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-08b/run.sh \
  > docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-08b/run.log 2>&1
```

Exit status: `0`. Tier: L0, host only. No Verilator, no T0-A top, no board.

The harness models the 16 × 24 DCR map as a host register file initialized to
`0xdeadbeef`. Each slot is written through the production
`vortex::dxa::program_2d` with a distinct 64-bit base and alternating K=64/512
shapes. For each write it checks the exact ten-word write list, every word in
all fifteen other slots against a pre-write snapshot, and every one of the
fourteen target-slot words the encoder does not define against the sentinel.
A write outside `0x100`–`0x27f` fails immediately. After all sixteen writes it
reads back the complete 384-word map.

## Raw log

Filed as [`run.log`](run.log), 2,092 bytes, SHA-256
`d65e0f43b8cbf3643a390c18f2a47355c71c35fca112867ffc4363bcf3c2933d`.
The log contains the compiler identity, source hashes, build command, and
test output; it is unedited.

## Result against the criterion

| Check | Measured |
|---|---|
| Slots written | 16/16, each through `program_2d` |
| Descriptor writes | 160 writes (10 per slot); all ten expected words matched each time |
| Neighbor isolation | 5,760 words compared across all fifteen non-target slots per write; 0 changed |
| Target write-only behavior | 224 unwritten target-slot words checked against the sentinel; 0 changed |
| Full-map readback | 384 words checked simultaneously; 0 mismatches |
| Slot bases | `0x100 + 24*n`, n=0..15; slot 15 spans `0x268`–`0x27f`; its last written word is `0x27c` |
| Address spill | No write below `0x100` or above `0x27f`; no write outside the target slot |

**PASS at L0** for host descriptor slot isolation, with 0 mismatches. This
also proves all 16 slot addresses are reachable by the host encoder.

## Accountable owner and date

**Software/runtime lead** — accountable owner for IF-08. Record prepared by
the engineering agent, 2026-11-21; not an approval or signature.

## Open deviations and carries

- **No RTL slot isolation.** The host model decodes the DCR address map; it
  does not instantiate `VX_dxa_desc_table`, `VX_dxa_core`, or the L2 cluster.
  The T-IF-08b L2 arm remains OPEN.
- **No T0 device evidence.** T0 has no DXA, and G-4 (DXA-to-test-SRAM attach)
  remains OPEN. This run makes no device descriptor-consumption claim.
- **IF-08 overall remains OPEN.** T-IF-08a supplies the L0 encoder/decoder
  half; this record supplies the L0 host slot-isolation half. RTL consumption
  and RTL isolation are still required.
- **T-IF-08a's historical record** correctly said T-IF-08b was open when it
  was filed; this record is the later L0 host result. It does not amend that
  filed record.
- **No G3 result.** Only this test's L0 host criterion is recorded.

## Reproduction

From the repository root, with the source tree at the identity above:

```text
wsl -e bash docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-08b/run.sh
```

The runner creates and removes a temporary binary; it writes no build
artifacts into the repository. Re-running against the same source and
compiler reproduces 160 writes, 5,760 neighbor-word comparisons, 224
target-slot sentinel checks, and 384 readback words. No frozen G2 file, v1
contract file, or RTL is modified by this record.
