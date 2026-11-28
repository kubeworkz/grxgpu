# G100-T0 G3 Edge-Shape Workloads

**Status:** references generated; no device run and no T-G-5f result. T-G-5f
remains OPEN.
**Parent workload:** `G100-T0-G2-SGEMM-1.0` and its frozen corpus are
unchanged and remain the authority for M=N=64.
**Purpose:** CPU references for the two T-G-5f supported shapes that the frozen
generator cannot express: 16×16×8 and non-square 32×16×8.

---

## 1. Generator

[`gen_golden_dims.cpp`](golden/gen_golden_dims.cpp) is a
dimension-parameterized copy of the frozen
[`gen_golden.cpp`](../g100-t0-g2-2026-11-21/golden/gen_golden.cpp). It accepts
M, N and K and keeps the frozen generation semantics:

1. `std::srand(50)` once per process.
2. Generate A row-major, then B row-major, each element
   `float(rand()) / RAND_MAX` converted to FP16 by `rv_ftoh_s(bits, 0, nullptr)`.
3. Reference C: each product is rounded to FP32, accumulated in `double`, and
   the final sum rounded once to FP32.

The generator refuses M or N that is not a multiple of 16 and K that is not a
multiple of 8. Outputs are raw little-endian: A and B are `uint16` FP16 bits,
C is `uint32` IEEE FP32 bits, all row-major.

**Source SHA-256:**
`7167285a726436051a6986e287b93b3bcbac3df84b34396e787b482aec8e7703`

**Toolchain:** Ubuntu 24.04.3 under WSL2, `g++ (Ubuntu
13.3.0-6ubuntu2~24.04.1) 13.3.0`, glibc 2.39, Linux 6.18.33.2, x86_64.

**Build:**

```sh
g++ -std=c++17 -O2 -ffp-contract=off -fno-fast-math \
  -Isw/common -Ithird_party/softfloat/source/include \
  docs/evidence/g100-t0-g3-2026-11-21/golden/gen_golden_dims.cpp \
  sw/common/rvfloats.cpp sw/common/softfloat_ext.cpp \
  third_party/softfloat/build/Linux-x86_64-GCC/softfloat.a \
  -o /tmp/gen_golden_dims
```

**Generate:**

```sh
/tmp/gen_golden_dims 16 16 8 \
  docs/evidence/g100-t0-g3-2026-11-21/golden/g100t0_g3_sgemm_m16n16k8
/tmp/gen_golden_dims 32 16 8 \
  docs/evidence/g100-t0-g3-2026-11-21/golden/g100t0_g3_sgemm_m32n16k8
```

---

## 2. Workloads

| Workload ID | M×N×K | A | B | C | ULP budget |
|---|---|---:|---:|---:|---:|
| `G100-T0-G3-SGEMM-M16N16K8-1.0` | 16×16×8 | 16×8 | 8×16 | 16×16 | 15 |
| `G100-T0-G3-SGEMM-M32N16K8-1.0` | 32×16×8 | 32×8 | 8×16 | 32×16 | 15 |

Both shapes have K=8, so the budget is
`max(12, ceil(5·√8)) = max(12, 15) = 15`. The comparator is the frozen
manifest's integer distance between positive FP32 bit patterns,
`abs(int32(expected) - int32(actual))`, with zero mismatches beyond the budget.
A run must match A and B exactly before comparing C.

---

## 3. Artifact hashes

| Workload | File | Shape | Bytes | SHA-256 |
|---|---|---|---:|---|
| `G100-T0-G3-SGEMM-M16N16K8-1.0` | `g100t0_g3_sgemm_m16n16k8_A.fp16` | 16×8 | 256 | `a0f513b254f3cab97767396806492b6515e60ef35f7c0eff39613fd3895cddea` |
| `G100-T0-G3-SGEMM-M16N16K8-1.0` | `g100t0_g3_sgemm_m16n16k8_B.fp16` | 8×16 | 256 | `9e1d19961c6cdfef67a2fdeeeeb03b31ecd466d270693f3225ad98e0ac71e4f1` |
| `G100-T0-G3-SGEMM-M16N16K8-1.0` | `g100t0_g3_sgemm_m16n16k8_C.fp32` | 16×16 | 1,024 | `fc1aa52c905c25618fc5216b01b2b27137c140e33f2b6c87b0d963868ed6c0fd` |
| `G100-T0-G3-SGEMM-M32N16K8-1.0` | `g100t0_g3_sgemm_m32n16k8_A.fp16` | 32×8 | 512 | `8ed72433ca86f4de24490963f5e46493137aa29df5110468f26744f8efd4b6b8` |
| `G100-T0-G3-SGEMM-M32N16K8-1.0` | `g100t0_g3_sgemm_m32n16k8_B.fp16` | 8×16 | 256 | `04ea637b9625d87e558e34d9c3002d06e47675fd771e5fe6efbfb7ab0f275f71` |
| `G100-T0-G3-SGEMM-M32N16K8-1.0` | `g100t0_g3_sgemm_m32n16k8_C.fp32` | 32×16 | 2,048 | `0b8183bd2db98895a4a5791ca4d281c8bf82172c8c4972d138b0b86f03b44c38` |

The generator, all six files, the independent verifier, and its log are
covered by [`golden/SHA256SUMS`](golden/SHA256SUMS).

---

## 4. Validation performed

1. **Parity with the frozen generator.** The unchanged frozen
   `gen_golden.cpp` (SHA-256
   `8ae98a8c455dabc5e58f6354bff60c2f39e1103194adf07a045e3bfef5a54dc6`)
   and this copy were both run at M=N=64 for K=8 and K=24. `cmp` reported
   byte-identical A, B and C for both K values.
2. **Determinism.** Each edge shape was generated twice; the second A/B/C set
   was byte-identical to the tracked set.
3. **Frozen inputs.** `sha256sum -c` on the G2 corpus `SHA256SUMS` passed,
   including the frozen generator and verifier. No G2 file was edited.
4. **Dimensions.** File sizes match the declared shapes in the hash table.
5. **Independent CPU reference.**
   [`verify_edge_golden.py`](golden/verify_edge_golden.py) reimplements the
   glibc `rand()` stream, FP16 conversion and FP32/double reference with NumPy,
   without linking `rvfloats` or softfloat. It checks A and B exactly and C
   against the recorded 15-ULP comparator. Run with Python 3.14.0 and NumPy
   2.5.4, both shapes report A diff=0, B diff=0, C exact diff=0, max ULP=0,
   over budget=0 and exit 0; output is
   [`verify_edge.log`](golden/verify_edge.log). This check is separate from the
   generator-parity check above.

No device output exists and no device ULP comparison has run. These are CPU
references only; T-G-5f is not passed.

**Freeze rule.** A change to the generator, seed, libc, dimensions, types,
reference, or tolerance creates a new workload ID and new files. Existing
hashes are never edited.
