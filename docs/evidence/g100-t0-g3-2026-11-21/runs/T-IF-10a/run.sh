#!/usr/bin/env bash
# T-IF-10a — CP ring wire encoder/decoder round-trip (L0).
# The real VX_cp_pkg/VX_cp_unpack are compiled with Icarus; no board or T0 CP.
set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(cd ../../../../.. && pwd)"
BUILD="$(mktemp -d "${TMPDIR:-/tmp}/t-if-10a.XXXXXX")"
trap 'rm -rf "$BUILD"' EXIT

echo "T-IF-10a CP wire round-trip evidence"
date -u '+utc: %Y-%m-%dT%H:%M:%SZ'

echo "--- simulator ---"
iverilog -V 2>&1 | awk 'NR==1'

echo "--- source hashes ---"
sha256sum tb.sv VX_cp_unpack_icarus.sv \
  "$ROOT/hw/rtl/cp/VX_cp_pkg.sv" \
  "$ROOT/hw/rtl/cp/VX_cp_unpack.sv" \
  "$ROOT/hw/rtl/VX_define.vh" \
  "$ROOT/build32/hw/VX_config.vh" \
  "$ROOT/build32/hw/VX_types.vh" |
  sed "s#$ROOT/##"

echo "--- build ---"
iverilog -g2012 \
  -I "$ROOT/hw/rtl" \
  -I "$ROOT/hw/rtl/cp" \
  -I "$ROOT/build32/hw" \
  -o "$BUILD/t-if-10a.vvp" \
  "$ROOT/hw/rtl/cp/VX_cp_pkg.sv" \
  VX_cp_unpack_icarus.sv \
  tb.sv

echo "--- run ---"
vvp "$BUILD/t-if-10a.vvp"
