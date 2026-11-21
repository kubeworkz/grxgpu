#!/usr/bin/env python3
"""Independently verify the G3 edge-shape SGEMM references.

This reimplements the glibc rand() sequence, the FP16 conversion and the
FP32/double reference without linking the generator's softfloat path. It checks
A and B exactly and C against the recorded ULP budget.

Usage: python verify_edge_golden.py
"""

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RAND_MAX = 2147483647
BUDGET = 15
SHAPES = [(16, 16, 8), (32, 16, 8)]


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
    for m, n, k in SHAPES:
        prefix = HERE / f"g100t0_g3_sgemm_m{m}n{n}k{k}"
        a = np.fromfile(f"{prefix}_A.fp16", dtype="<u2")
        b = np.fromfile(f"{prefix}_B.fp16", dtype="<u2")
        c = np.fromfile(f"{prefix}_C.fp32", dtype="<f4")
        if (a.size, b.size, c.size) != (m * k, k * n, m * n):
            print(f"{m}x{n}x{k}: size mismatch")
            failures += 1
            continue

        values = glibc_rand(50, m * k + k * n)

        def to_f16(value):
            quotient = np.float32(value) / np.float32(RAND_MAX)
            return np.float16(quotient).view(np.uint16)

        expected_a = np.array([to_f16(v) for v in values[: m * k]], dtype=np.uint16)
        expected_b = np.array([to_f16(v) for v in values[m * k :]], dtype=np.uint16)

        af = a.reshape(m, k).view(np.float16).astype(np.float32)
        bf = b.reshape(k, n).view(np.float16).astype(np.float32)
        reference = np.zeros((m, n), dtype=np.float64)
        for i in range(k):
            product = (af[:, i][:, None] * bf[i, :][None, :]).astype(np.float32)
            reference += product.astype(np.float64)
        expected_c = reference.astype(np.float32).reshape(-1)

        a_diff = int((a != expected_a).sum())
        b_diff = int((b != expected_b).sum())
        c_diff = int((c.view(np.uint32) != expected_c.view(np.uint32)).sum())
        ulp = np.abs(
            c.view(np.uint32).astype(np.int64)
            - expected_c.view(np.uint32).astype(np.int64)
        )
        max_ulp = int(ulp.max()) if ulp.size else 0
        over_budget = int((ulp > BUDGET).sum())
        passed = not (a_diff or b_diff or over_budget)
        print(
            f"{m}x{n}x{k}: A diff={a_diff} B diff={b_diff} "
            f"C exact diff={c_diff} max ULP={max_ulp} "
            f"over budget={over_budget} budget={BUDGET} "
            f"{'PASS' if passed else 'FAIL'}"
        )
        failures += 0 if passed else 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
