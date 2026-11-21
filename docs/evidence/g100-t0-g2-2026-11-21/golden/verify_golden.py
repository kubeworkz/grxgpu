#!/usr/bin/env python3
"""Independently verify the frozen G2 SGEMM corpus.

This reimplements the glibc rand() sequence, the FP16 conversion and the
FP32/double reference without linking the workload's softfloat path. It is a
cross-check of gen_golden.cpp, not a second copy of it.

Usage: python verify_golden.py
"""

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
M, N = 64, 64
RAND_MAX = 2147483647
SIZES = {64: (8192, 8192, 16384), 512: (65536, 65536, 16384)}


def glibc_rand(seed, count):
    state = [0] * 31
    state[0] = seed
    for i in range(1, 31):
        state[i] = (16807 * state[i - 1]) % RAND_MAX
    fptr, rptr = 3, 0

    def step():
        nonlocal fptr, rptr
        state[fptr] = (state[fptr] + state[rptr]) & 0xFFFFFFFF
        value = (state[fptr] >> 1) & 0x7FFFFFFF
        fptr = (fptr + 1) % 31
        rptr = (rptr + 1) % 31
        return value

    for _ in range(310):
        step()
    return [step() for _ in range(count)]


def main():
    failures = 0
    for k in sorted(SIZES):
        prefix = HERE / f"g100t0_sgemm_m64n64k{k}"
        a_size, b_size, c_size = SIZES[k]
        a = np.fromfile(f"{prefix}_A.fp16", dtype="<u2")
        b = np.fromfile(f"{prefix}_B.fp16", dtype="<u2")
        c = np.fromfile(f"{prefix}_C.fp32", dtype="<f4")
        if (a.nbytes, b.nbytes, c.nbytes) != (a_size, b_size, c_size):
            print(f"K={k}: size mismatch")
            failures += 1
            continue

        values = glibc_rand(50, M * k + k * N)

        def to_f16(value):
            quotient = np.float32(value) / np.float32(RAND_MAX)
            return np.float16(quotient).view(np.uint16)

        expected_a = np.array([to_f16(v) for v in values[: M * k]], dtype=np.uint16)
        expected_b = np.array([to_f16(v) for v in values[M * k :]], dtype=np.uint16)

        af = a.reshape(M, k).view(np.float16).astype(np.float32)
        bf = b.reshape(k, N).view(np.float16).astype(np.float32)
        reference = np.zeros((M, N), dtype=np.float64)
        for i in range(k):
            product = (af[:, i][:, None] * bf[i, :][None, :]).astype(np.float32)
            reference += product.astype(np.float64)
        expected_c = reference.astype(np.float32).reshape(-1)

        a_diff = int((a != expected_a).sum())
        b_diff = int((b != expected_b).sum())
        c_diff = int((c.view(np.uint32) != expected_c.view(np.uint32)).sum())
        max_ulp = int(
            np.max(
                np.abs(
                    c.view(np.uint32).astype(np.int64)
                    - expected_c.view(np.uint32).astype(np.int64)
                )
            )
        )
        print(f"K={k}: A diff={a_diff} B diff={b_diff} C diff={c_diff} max ULP={max_ulp}")
        failures += int(a_diff or b_diff or c_diff)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
