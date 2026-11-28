# G100-T0 G2 Frozen Golden Workload — `sgemm_tcu_wg_dxa`

**Workload ID:** `G100-T0-G2-SGEMM-1.0`
**Status:** **FROZEN** 2026-11-21 for the G2 interface freeze. The data is the
authoritative CPU reference corpus; no T0 device run is recorded yet.
**Gate record:** [G2 gate record](gate-record.md).
**Source pin:** `ff550c27570f17b0c8242be42257043d3de4ffa7`,
tree `cf6b2f8657fcba985dd9007fa403231c3d800301`.
**Why this workload:** it is the only compute path approved by the G0
engineering authorization, exercised by the TCU and DXA, and already present in
the regression tree.

---

## 1. Frozen identity

| Field | Frozen value |
|---|---|
| Application | `tests/regression/sgemm_tcu_wg_dxa` |
| Kernel | `kernel.cpp` (`TGM_KERNEL` unset) |
| Operation | C[M,N] = A[M,K] × B[K,N], row-major |
| Dimensions | M = 64, N = 64; K = 64 and K = 512 |
| Input type | FP16 (`ITYPE=fp16`) |
| Output type | FP32 (`OTYPE=fp32`) |
| WGMMA register count | `WGMMA_NRC=16` |
| Warps | 4 (= `VX_CFG_ISSUE_WIDTH`) |
| CTA tile M | 16 = warps × xtileM (xtileM=4) |
| Tile N | 16 (xtileN) |
| Tile K | 8 (xtileK=4 × fp16 i_ratio=2) |
| Grid | 4 × 4 CTAs |
| Block | 16 × 1 threads |
| FP32 ULP budget | K=64: 40; K=512: 114 (= max(12, ceil(5·√K))) |
| Required mismatches | 0 beyond the ULP budget |

The ULP comparator is the workload's integer distance between positive FP32
bit patterns, `abs(int32(expected) - int32(actual))`. The budget covers the
hardware's FP32 accumulation rounding; it is not a tolerance for a missing
tile, a dropped product, or a wrong result class.

---

## 2. Configuration identity

Golden data fixes the **mathematics**, not the cluster count. The device run
that consumes it must use the frozen T0 configuration:

```text
CONFIGS='-DVX_CFG_NUM_CLUSTERS=1 -DVX_CFG_NUM_CORES=16 -DVX_CFG_NUM_WARPS=4 -DVX_CFG_NUM_THREADS=4 -DVX_CFG_ISSUE_WIDTH=4 -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_EXT_TCU_ENABLE -DVX_CFG_EXT_DXA_ENABLE -DVX_CFG_TCU_WGMMA_ENABLE -DWGMMA_NRC=16'
```

| Field | Resolved value |
|---|---|
| XLEN | 32 |
| Clusters × cores | 1 × 16 |
| Warps × threads × issue width | 4 × 4 × 4 |
| TCU | 4 blocks × 4 lanes, TFR, FP16 + WGMMA |
| DXA | 2 cores, 2 memory ports |
| LMEM / ICache / DCache | 16 KB / 16 KB / 16 KB per core |
| L2 / L3 | disabled |
| Clock | 400 MHz target |

Resolver output: [proposed-config.txt](../g100-t0-g1-audit-2026-11-20/proposed-config.txt),
SHA-256 `cd5336232fa98454009574121e0b25cc98feb3530a50675874ba98738c154cda`.
This remains the G1 proposed configuration; G2 freezes the workload and the
golden data, not the device build. G3 must produce a build stamp for the same
`CONFIGS`.

**Kernel variants.** The default Makefile builds `WGMMA_RS` +
`WGMMA_DXA_DOUBLE_BUFFER`; the Verilated RTL path uses `WGMMA_SINGLE_BUFFER=1`.
Both variants compute the same C and MUST be compared to the same corpus. The
T0 target is the double-buffered variant because the T0 configuration has two
DXA workers.

---

## 3. Source and dependency pins

| Path | SHA-256 |
|---|---|
| `tests/regression/sgemm_tcu_wg_dxa/main.cpp` | `423b63677ab54f4f57dee8731e1ec2643780e52d1e5a7e2345003106b9cfea88` |
| `tests/regression/sgemm_tcu_wg_dxa/common.h` | `6946f87e76b9126d976ed9ef4ef35e7a779028bdf20084ccf7ed0b23db06c51c` |
| `tests/regression/sgemm_tcu_wg_dxa/kernel.cpp` | `3a1bbf546ca2b292824f4040666d90e9ee90b3cee0b8b1090160d985d643408b` |
| `tests/regression/sgemm_tcu_wg_dxa/Makefile` | `3aa417211fe1d613243238723b980aefa14fbd21fc02dda8385d9b9eeca089f5` |
| `sw/common/rvfloats.cpp` | `3f6708ef36bfad94d532dd2c7b15cadfb3e4466502383e6e1b4f4e68a74a6301` |
| `sw/common/softfloat_ext.cpp` | `beb1e13fb3a55278d904fabb99104b732d91cfd7c94e733782966169eb1be197` |
| `sw/common/tensor_cfg.h` | `95d4e3029635f6c15de6719d238d5f6521ae8e209ad174c526ee0b41b1fdfb8b` |
| `third_party/softfloat/build/Linux-x86_64-GCC/softfloat.a` | `f16bec3e8a32ab256cc3a5706c1f52b497d31ba7f7d0a59ad31b846adc66eb34` |

The four workload files are byte-identical at the T0 pin and at the golden
generation checkout. `rvfloats.cpp`, `softfloat_ext.cpp`, `tensor_cfg.h` and the
softfloat archive are the conversion/reference dependencies; their hashes make
the generator reproducible.

---

## 4. Input and reference semantics

The workload generates inputs in-process and never reads these files. The
frozen contract is therefore the **generation algorithm plus the exact bytes**:

1. `std::srand(50)` once per process.
2. Generate A row-major, then B row-major, each element
   `float(rand()) / RAND_MAX` converted to FP16 by `rv_ftoh_s(bits, 0, NULL)`
   (round-to-nearest-even). `rand()` is the glibc generator; the pinned host
   is Ubuntu 24.04, glibc 2.39.
3. Reference C: for each (m,n), accumulate in `double` the FP32-rounded product
   `float(A[m,k]) * float(B[k,n])`, then round the final sum once to FP32.
   This is the `matmul_cpu` FP32 path in `main.cpp`.

A run on a different libc or a different `rv_ftoh_s` build does not generate
the same A/B. A G3 runner MUST hash its generated A and B and match the values
below **before** comparing C; otherwise a libc mismatch is misreported as a
compute failure.

The CPU reference is runnable without a device:

```sh
g++ -std=c++17 -O2 -ffp-contract=off -fno-fast-math \
  -Isw/common -Ithird_party/softfloat/source/include \
  docs/evidence/g100-t0-g2-2026-11-21/golden/gen_golden.cpp \
  sw/common/rvfloats.cpp sw/common/softfloat_ext.cpp \
  third_party/softfloat/build/Linux-x86_64-GCC/softfloat.a -o /tmp/gen_golden
/tmp/gen_golden 64  docs/evidence/g100-t0-g2-2026-11-21/golden/g100t0_sgemm_m64n64k64
/tmp/gen_golden 512 docs/evidence/g100-t0-g2-2026-11-21/golden/g100t0_sgemm_m64n64k512
```

Toolchain used for the freeze: Ubuntu 24.04.3 under WSL2, `g++ (Ubuntu
13.3.0-6ubuntu2~24.04.1) 13.3.0`, glibc 2.39, Linux 6.18.33.2, x86_64.

---

## 5. Frozen corpus

Files are raw little-endian: A and B are `uint16` FP16 bits, C is `uint32`
IEEE FP32 bits, all row-major with the dimensions in the file name. They are
tracked in [`golden/`](golden/).

| File | Shape | Bytes | SHA-256 |
|---|---|---:|---|
| `g100t0_sgemm_m64n64k64_A.fp16` | 64 × 64 | 8,192 | `985ef83fe0802e90a08fe2023822dc0b31e83aeb66df9051f688c3e694b468a8` |
| `g100t0_sgemm_m64n64k64_B.fp16` | 64 × 64 | 8,192 | `ad975434b9327b5dfe37f36e7e09e703253dce2bb80ece322797a17ff9356270` |
| `g100t0_sgemm_m64n64k64_C.fp32` | 64 × 64 | 16,384 | `73a1a0eacd81d64cd451919493da3d9187f418b563e4c52b1f6a8ba68b5ad240` |
| `g100t0_sgemm_m64n64k512_A.fp16` | 64 × 512 | 65,536 | `70dcc14a134e620c9b5d4be7dbbd01a64e6bb5efdf4fa8b6f432533bd735cfac` |
| `g100t0_sgemm_m64n64k512_B.fp16` | 512 × 64 | 65,536 | `59fb1324bbfcff9c943fa7ab25b4a2ce0db7be7dec2787eb41c71d4552759cb9` |
| `g100t0_sgemm_m64n64k512_C.fp32` | 64 × 64 | 16,384 | `d07043551fa7efeae970533f5e86c02af8062ab5bed82e38c68e161fe67628c9` |

The corpus plus generator and verifier are covered by
[`golden/SHA256SUMS`](golden/SHA256SUMS). Generator SHA-256 is
`8ae98a8c455dabc5e58f6354bff60c2f39e1103194adf07a045e3bfef5a54dc6`;
independent verifier SHA-256 is
`eab681ac4bbcc599e5764933171df0404134f1c0066407f9dd3b28def1cff6f4`.

### Verification performed at freeze

1. **Determinism:** regenerating both K values with the same command produced
   byte-identical A, B and C (`cmp` on all six files).
2. **Independent semantics:** `golden/verify_golden.py` reimplements the glibc
   `rand()` sequence and uses NumPy's FP16/FP32 conversions and a
   float64-accumulated reference. It reports `A diff=0 B diff=0 C diff=0` and
   `max ULP=0` for both K values; the output is
   [`golden/verify.log`](golden/verify.log). The glibc implementation was
   checked against the known first outputs for `srand(1)`
   (`1804289383, 846930886, 1681692777`).
3. **Dimensions:** file sizes match the declared shapes; C contains 4,096 FP32
   words for both K values.

The independent check uses NumPy 2.5.4 on Python 3.14 (Windows) and does not
link the workload's softfloat path, so agreement is evidence about the corpus,
not a restatement of the generator.

---

## 6. Device-run contract (for G3 and later)

A T0/G3 run MUST record:

- source commit and tree, build stamp, compiler/linker flags, toolchain;
- the exact `CONFIGS` above and the resolved `VX_config.h`;
- the kernel variant (`WGMMA_RS` + double buffer, or single buffer);
- generated A/B hashes matching §5, and the C hash after download;
- the ULP budget and the number of mismatches (must be 0);
- raw SimX/rtlsim log and exit status.

The device output C is **not** expected to be byte-identical to the golden C;
it must satisfy the ULP budget. Equality of A/B is exact and required.

The golden corpus is frozen for `G100-T0-G2-SGEMM-1.0`. Any change to the
generator, libc, dimensions, types, seed, reference, or tolerance creates a new
workload ID and a new gate-record entry; the existing files and hashes are not
edited.

---

## 7. Unsupported operations and shapes

The frozen workload does not cover, and v1 does not claim:

- `M % 16 != 0`, `N % 16 != 0`, or `K % 8 != 0` at the frozen 4-warp /
  `WGMMA_NRC=16` configuration;
- input/output types other than FP16→FP32 (the app has other type paths, but
  they are not frozen here);
- the TGM kernel (`TGM_KERNEL` set), sparse modes, or multicast;
- graphics, ray tracing, or any excluded extension;
- host-driven CP DMA, QMD launch, interrupts, multi-queue concurrency;
- T0-B halt/resume, OpenOCD, or GDB;
- product host/DRAM/HBM execution.

A shape or type outside this list is rejected by the workload's own checks
(`M % cta_M`, `N % tileN`, `K % tileK`) or is outside the frozen contract; it
is not a silent pass.
