#!/usr/bin/env bash
# T-IF-08a — host DXA encoder / descriptor-word equivalence (L0).
# Run from any directory; the raw stdout/stderr is captured by the caller as
# run.log. The temporary binary is removed on exit.
set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(cd ../../../../.. && pwd)"
CXX="${CXX:-g++}"
BUILD="$(mktemp -d "${TMPDIR:-/tmp}/t-if-08a.XXXXXX")"
trap 'rm -rf "$BUILD"' EXIT

echo "T-IF-08a host DXA encoder evidence"
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
  main.cpp -o "$BUILD/t-if-08a"

echo "--- run ---"
"$BUILD/t-if-08a"
