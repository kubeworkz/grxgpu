#!/usr/bin/env bash
set -euo pipefail

ROOT=$(pwd)
G2="$ROOT/docs/evidence/g100-t0-g2-2026-11-21/golden"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/t-if-14a.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

echo "T-IF-14a corpus regeneration"
echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "tier: L0"
echo "seed: 50"
echo "workload source pin: ff550c27570f17b0c8242be42257043d3de4ffa7"
echo "workload tree: cf6b2f8657fcba985dd9007fa403231c3d800301"
echo "T0 config hash: cd5336232fa98454009574121e0b25cc98feb3530a50675874ba98738c154cda"
echo "generator: $G2/gen_golden.cpp"
sha256sum "$G2/gen_golden.cpp"
g++ --version | awk 'NR==1'
ldd --version | awk 'NR==1'
uname -r

echo "--- build ---"
g++ -std=c++17 -O2 -ffp-contract=off -fno-fast-math \
  -I"$ROOT/sw/common" -I"$ROOT/third_party/softfloat/source/include" \
  "$G2/gen_golden.cpp" \
  "$ROOT/sw/common/rvfloats.cpp" \
  "$ROOT/sw/common/softfloat_ext.cpp" \
  "$ROOT/third_party/softfloat/build/Linux-x86_64-GCC/softfloat.a" \
  -o "$WORK/gen_golden"

echo "--- generate ---"
"$WORK/gen_golden" 64 "$WORK/g100t0_sgemm_m64n64k64"
"$WORK/gen_golden" 512 "$WORK/g100t0_sgemm_m64n64k512"

echo "--- compare to frozen hashes ---"
grep -E 'g100t0_sgemm_m64n64k(64|512)_[ABC]\.' "$G2/SHA256SUMS" > "$WORK/SHA256SUMS"
(cd "$WORK" && sha256sum -c SHA256SUMS)

echo "--- byte compare ---"
for f in A.fp16 B.fp16 C.fp32; do
  cmp "$WORK/g100t0_sgemm_m64n64k64_$f" "$G2/g100t0_sgemm_m64n64k64_$f"
  cmp "$WORK/g100t0_sgemm_m64n64k512_$f" "$G2/g100t0_sgemm_m64n64k512_$f"
  echo "cmp $f: identical"
done

echo "--- regenerated hashes ---"
sha256sum "$WORK"/g100t0_sgemm_m64n64k64_* "$WORK"/g100t0_sgemm_m64n64k512_*

echo "--- frozen corpus check ---"
(cd "$G2" && sha256sum -c SHA256SUMS)
echo "T-IF-14a regeneration and hash match: PASS"
