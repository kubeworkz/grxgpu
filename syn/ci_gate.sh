#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Synthesis pipeline CI gate.
#
# Verifies the TCU synthesis preprocessing chain still produces SystemVerilog
# that Surelog elaborates cleanly:
#
#   Stage 0: syn/flatten_tcu.py --self-test
#            (nested-ifdef skip-region invariant — see that file's docstring;
#             this fix has been silently reverted by branch merges twice)
#   Stage 1: flatten_tcu.py + preprocess_for_synth.py + expand_struct_refs.py
#            + fix_tcu_core_interfaces.py + inline_all_functions.py
#            + synth_fixup.py
#   Stage 2: Surelog elaboration via synlig/yosys `read_systemverilog` —
#            gate FAILS if the summary shows [FATAL]/[SYNTAX]/[ERROR] > 0,
#            if the clean-summary line is missing, or if Surelog aborts.
#
# Tool resolution: uses $SYNLIG_BIN / $YOSYS_BIN if set, else common install
# paths, else PATH. Without synlig the gate degrades to Stage 0 only (CI
# installs the plugin, so the full gate always runs there).
#
# Debug hook: GATE_INPUT_SV=<file> skips Stage 1 and elaborates that file
# directly (used to test the failure path without touching tracked files).
#
# Exit codes: 0 = pass, 1 = any stage failed.
# -----------------------------------------------------------------------------
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FAILED=0

step() { echo ""; echo "=== $* ==="; }

# ---- Stage 0: flatten_tcu.py self-test --------------------------------------
step "Stage 0: flatten_tcu.py self-test (nested-ifdef invariant)"
if ! python3 "$ROOT/syn/flatten_tcu.py" --self-test; then
  echo "FAIL: flatten_tcu.py self-test failed"
  FAILED=1
fi

# ---- Tool resolution ----------------------------------------------------------
SYNLIG=""
for c in "${SYNLIG_BIN:-}" "$HOME/tools/synlig/synlig/synlig"; do
  if [ -n "$c" ] && [ -x "$c" ]; then SYNLIG="$c"; break; fi
done
if [ -z "$SYNLIG" ] && command -v yosys >/dev/null 2>&1; then
  # synlig binary absent, but the systemverilog plugin may be installed in yosys
  if yosys -p "plugin -i systemverilog" >/dev/null 2>&1; then
    SYNLIG="yosys-plugin"
  fi
fi

if [ -z "$SYNLIG" ]; then
  echo ""
  echo "WARNING: synlig/yosys systemverilog plugin not found —"
  echo "         running self-test only (reduced coverage)."
  if [ "$FAILED" -ne 0 ]; then
    echo ""; echo "SYNTH GATE: FAIL"; exit 1
  fi
  echo ""; echo "SYNTH GATE: PASS (self-test only)"; exit 0
fi

# ---- Stage 1: preprocessing pipeline ------------------------------------------
if [ -n "${GATE_INPUT_SV:-}" ]; then
  INPUT_SV="$GATE_INPUT_SV"
  echo ""; echo "=== Stage 1 skipped (GATE_INPUT_SV=$INPUT_SV) ==="
else
  step "Stage 1: 6-stage preprocessing pipeline"
  INPUT_SV="$WORK/tcu_inlined.sv"
  if python3 "$ROOT/syn/flatten_tcu.py" "$ROOT" "$WORK/tcu_flat.sv" &&
     python3 "$ROOT/syn/preprocess_for_synth.py" "$WORK/tcu_flat.sv" "$WORK/tcu_pre.sv" &&
     python3 "$ROOT/syn/expand_struct_refs.py" "$WORK/tcu_pre.sv" "$WORK/tcu_struct.sv" &&
     python3 "$ROOT/syn/fix_tcu_core_interfaces.py" "$WORK/tcu_struct.sv" "$WORK/tcu_ifix.sv" &&
     python3 "$ROOT/syn/inline_all_functions.py" "$WORK/tcu_ifix.sv" "$WORK/tcu_inlined.sv" &&
     python3 "$ROOT/syn/synth_fixup.py" "$WORK/tcu_inlined.sv"; then
    :
  else
    echo "FAIL: preprocessing pipeline error"
    FAILED=1
  fi
fi

# ---- Stage 2: Surelog elaboration ---------------------------------------------
step "Stage 2: Surelog elaboration (read_systemverilog -top VX_tcu_core)"
LOG="$WORK/surelog.log"

if [ "$SYNLIG" = "yosys-plugin" ]; then
  YOSYS_CMD=(yosys -p "plugin -i systemverilog; read_systemverilog -top VX_tcu_core $INPUT_SV; proc")
else
  YOSYS_CMD=("$SYNLIG" -p "read_systemverilog -top VX_tcu_core $INPUT_SV; proc")
fi

if ! "${YOSYS_CMD[@]}" >"$LOG" 2>&1; then
  echo "FAIL: elaboration tool exited non-zero — tail of log:"
  tail -20 "$LOG"
  FAILED=1
fi

# Normalize the summary block: "[  FATAL] : 0" -> "[FATAL]:0"
summary=$(grep -E '^\[' "$LOG" 2>/dev/null | grep -E '\] *:' | tr -d ' ' || true)

echo "Surelog summary (FATAL/SYNTAX/ERROR):"
echo "$summary" | grep -E '^\[(FATAL|SYNTAX|ERROR)\]' || true

# Any nonzero counter fails.
if echo "$summary" | grep -qE '^\[(FATAL|SYNTAX|ERROR)\]:[1-9]'; then
  echo "FAIL: Surelog reported non-zero FATAL/SYNTAX/ERROR — offending lines:"
  grep -E 'FATAL|SYNTAX|ERROR' "$LOG" | grep -v '^\[ *[A-Z]' | head -20
  FAILED=1
fi

# The clean-summary line must be present (guards against truncated runs).
if ! echo "$summary" | grep -qE '^\[(FATAL|SYNTAX|ERROR)\]:0'; then
  echo "FAIL: Surelog summary block missing or incomplete (truncated run?)"
  tail -10 "$LOG"
  FAILED=1
fi

# Explicit parse-abort marker.
if grep -q 'Error when parsing design' "$LOG" 2>/dev/null; then
  echo "FAIL: Surelog aborted while parsing the design"
  FAILED=1
fi

# ---- Result -------------------------------------------------------------------
echo ""
if [ "$FAILED" -ne 0 ]; then
  echo "SYNTH GATE: FAIL"
  exit 1
fi
echo "SYNTH GATE: PASS"
