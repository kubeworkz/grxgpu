# T-IF-08a — DXA host descriptor encoder/decoder equivalence (L0)

**Result: PASS at L0 — software conformance only. No RTL or T0 device
evidence.** This is a test-level result, not a G3 gate result.

**Prepared by:** engineering agent supporting the G100-T0 program; not an
approver and not a signatory.
**Selection:** T-IF-08a is the next host-only interface test after T-IF-14a.
It exercises the production `program_2d`, `set_layout`, and
`set_tile_geometry` encoder for the frozen A/B descriptor shapes and needs
neither the G-3 revision, ECC S0, nor a board.

## Run identity

| Field | Value |
|---|---|
| Test ID | `T-IF-08a` |
| Contract row | IF-08 — 16 descriptor slots × 24 DCRs, 64-bit base, host encoders match RTL, write-only from host |
| Source commit | `c12d3aee5ad855fd80bec76f3d67ab4df580b6c9` |
| Source tree | `27c8316d7e8b5aae4f85c87b7ac0c05d7386af88` |
| T0 configuration hash | `cd5336232fa98454009574121e0b25cc98feb3530a50675874ba98738c154cda` (resolver hash carried from G1; no T0 image built) |
| Tier | L0 — host unit bench |
| Seed | N/A — fixed descriptors, no random input |

## Toolchain and build stamp

| Item | Identity |
|---|---|
| Compiler | `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0` |
| Build stamp | No product image or RTL image was built. The host harness was compiled from the pinned source hashes below; those hashes plus the compiler identity are the build identity for this run. |
| Runner | `run.sh`, SHA-256 `d69d5ed0ec68ce2df1c004bf8c76708b2fa4d3889dd0cc9e1e6ff7ef407d094b` |
| Test source | `main.cpp`, SHA-256 `9275008fe148dc4d2926c7891af1acd340fd1a8d58858568b1d832311e1eb0d5` |
| Runtime stub | `stub/vortex.h`, SHA-256 `981a8b306367f9ad3650a5c162500214adbd6caf8442a70523a9739761cd0b27` |
| Encoder under test | [`sw/runtime/include/dxa.h`](../../../../../sw/runtime/include/dxa.h), SHA-256 `349f9e1e9309705cd209d4263edad21ff9ef1e73c9677740a560d94b113f7543` |
| Meta field map | [`sw/common/dxa_meta.h`](../../../../../sw/common/dxa_meta.h), SHA-256 `b172820148530228a925d96252141e55c6ba3d84a9c7375fb0bc49f46d93089d` |
| DCR ABI constants | [`sw/VX_types.h`](../../../../../sw/VX_types.h), SHA-256 `1647fdc48564b48b06adde771ea9c6039ef49a759801726819855447d1730ac8` |
| RTL field widths | [`hw/rtl/dxa/VX_dxa_pkg.sv`](../../../../../hw/rtl/dxa/VX_dxa_pkg.sv), SHA-256 `efc15a7873a1244e8fd93088e5e21a2cedad7e48dc311046143e20210f8bf37b` |

## Command and tier

```text
wsl -e bash docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-08a/run.sh \
  > docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-08a/run.log 2>&1
```

Exit status: `0`. Tier: L0, host only. No Verilator, no T0-A top, no board.

The harness compiles the production header with a minimal runtime stub that
captures `vx_dcr_write` calls. It drives the frozen workload geometry
(M=N=64, `WGMMA_NRC=16`, FP16, 4 warps × 4 threads): A is row-major with
`tile0=8`, `tile1=16`; B is `BLOCK_MAJOR` with `tile0=16`, `tile1=8` and
`tcN=2`. Each K case checks the full A write list, the full B write list, the
B layout meta rewrite, and the B tile-geometry write. The expected words are
written from `VX_types.h` offsets and the `VX_dxa_pkg.sv` field widths, not
computed with the encoder's own packing helpers. The decoder reads the
captured words back by offset and compares base, sizes, stride, rank, element
size, layout, ESTRIDE fields, tile words, and `cfill`.

## Raw log

Filed as [`run.log`](run.log), 1,639 bytes, SHA-256
`007335ac157cfa96b5453cc5bb4a8b6783af1474066fcd42f417e5b08bfce992`.
The log contains the compiler identity, source hashes, build command, and
test output; it is unedited.

## Result against the criterion

| Check | Measured |
|---|---|
| Frozen descriptors covered | A row-major and B `BLOCK_MAJOR`, each at K=64 and K=512 |
| DCR writes | 44 expected writes (10 A + 10 B + 1 layout + 1 tile geometry per K), 44 captured |
| Decoded descriptor checks | 8 checks (A decode and B decode per K, B layout decode, B tile-geometry decode), 0 mismatches |
| Base/address width | 64-bit base split across LO/HI; both test bases above 32 bits |
| Slot addressing | A at slot 0 (`0x100`), B at slot 1 (`0x118`), stride 24 DCRs |
| Meta | rank 2, FP16 element-size encoding 1, A layout 0, B layout 3 (`0x6A`) |
| Tile words | A `0x00100008`; B `0x00080010`; B `ESTRIDE2=2` (`tcN`) |

**PASS at L0** for host encoder/decoder equivalence on this shape table,
with 0 mismatches.

## Accountable owner and date

**Software/runtime lead** — accountable owner for IF-08. Record prepared by
the engineering agent, 2026-11-21; not an approval or signature.

## Open deviations and carries

- **No RTL decode or consumption.** The test proves the host encoder emits
  the ABI words defined by `VX_types.h` and `VX_dxa_pkg.sv`; it does not
  instantiate `VX_dxa_desc_table`/`VX_dxa_core` or prove RTL readback.
- **T-IF-08b remains OPEN.** Slot isolation (writing slot n leaves n±1
  unchanged) and all 16 slots in use are not exercised here.
- **G-4 remains OPEN.** DXA has no path to the T0 test SRAM; no device
  descriptor consumption is claimed.
- **T0 has no DXA.** This is software conformance, not T0 device evidence.
- **IF-08 overall remains OPEN** until the RTL and slot-isolation evidence
  exists; only the L0 host half is recorded here.

## Reproduction

From the repository root, with the source tree at the identity above:

```text
wsl -e bash docs/evidence/g100-t0-g3-2026-11-21/runs/T-IF-08a/run.sh
```

The runner creates and removes a temporary binary; it writes no build
artifacts into the repository. Re-running against the same source and
compiler reproduces the 44-write/8-decode result. No frozen G2 file, v1
contract file, or RTL is modified by this record.
