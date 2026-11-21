#!/usr/bin/env bash
# T-IF-08b — host DXA descriptor slot isolation (L0).
# Run from any directory; the caller captures stdout/stderr as run.log.
set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(cd ../../../../.. && pwd)"
CXX="${CXX:-g++}"
BUILD="$(mktemp -d "${TMPDIR:-/tmp}/t-if-08b.XXXXXX")"
trap 'rm -rf "$BUILD"' EXIT

echo "T-IF-08b host DXA slot-isolation evidence"
date -u '+utc: %Y-%m-%dT%H:%M:%SZ'

echo "--- compiler ---"
"$CXX" --version | awk 'NR==1'

echo "--- source hashes ---"
sha256sum main.cpp stub/vortex.h \
  "$ROOT/sw/runtime/include/dxa.h" \
  "$ROOT/sw/common/dxa_meta.h" \
  "$ROOT/sw/VX_types.h" \
  "$ROOT/hw/rtl/dxa/VX_dxa_pkg.sv" |
  sed "s#$ROOT/##"

echo "--- build ---"
"$CXX" -std=c++17 -O2 -Wall -Wextra -Werror \
  -I stub -I "$ROOT/sw/runtime/include" -I "$ROOT/sw/common" -I "$ROOT/sw" \
  main.cpp -o "$BUILD/t-if-08b"

echo "--- run ---"
"$BUILD/t-if-08b"
