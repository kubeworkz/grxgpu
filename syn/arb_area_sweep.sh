#!/usr/bin/env bash
# Sweep VX_stream_arb area across (NUM_INPUTS, NUM_OUTPUTS, DATAW, ARBITER).
# Flow: sv2v convert (all libs + wrapper) -> Yosys Nangate45 synth -> stat area.
# Usage: arb_area_sweep.sh [workdir]
set -euo pipefail

WORK="${1:-/tmp/arb_sweep}"
RTL=/home/ubuntu/grxgpu/hw/rtl
LIBS=$RTL/libs
SV2V=/home/ubuntu/tools/sv2v/bin/sv2v
YOSYS=/home/ubuntu/tools/oss-cad-suite/bin/yosys
LIB=/tmp/nangate45_lib/NangateOpenCellLibrary_typical.lib
TOP_SV=/tmp/arb_sweep_top.sv

mkdir -p "$WORK/converted" "$WORK/reports"

echo "=== sv2v converting libs + wrapper ==="
SV2V_ARGS=(-I "$RTL" -I "$LIBS" --top arb_sweep_top)
for f in "$LIBS"/*.sv; do
    SV2V_ARGS+=("$f")
done
SV2V_ARGS+=("$TOP_SV")
"$SV2V" "${SV2V_ARGS[@]}" > "$WORK/converted/arb_all.v" 2> "$WORK/converted/sv2v.log" || {
    echo "sv2v failed"; tail -20 "$WORK/converted/sv2v.log"; exit 1; }
echo "converted: $(wc -l < "$WORK/converted/arb_all.v") lines"

# --- Sweep definitions: name:NI:NO:DW:ARB:STICKY:OUT_BUF ---
CONFIGS=(
    "ports2:2:1:64:R:0:0"
    "ports4:4:1:64:R:0:0"
    "ports8:8:1:64:R:0:0"
    "ports16:16:1:64:R:0:0"
    "ports32:32:1:64:R:0:0"
    "ports64:64:1:64:R:0:0"
    "width32:16:1:32:R:0:0"
    "width64:16:1:64:R:0:0"
    "width128:16:1:128:R:0:0"
    "width256:16:1:256:R:0:0"
    "width512:16:1:512:R:0:0"
    "mux16:16:16:64:R:0:0"
    "mux8x2:8:2:64:R:0:0"
    "prio16:16:1:64:P:0:0"
    "prio32:32:1:64:P:0:0"
    "sticky16:16:1:64:R:1:0"
    "buf16:16:1:64:R:0:1"
)

echo "=== synthesizing ==="
declare -A AREA
for cfg in "${CONFIGS[@]}"; do
    IFS=':' read -r name NI NO DW ARB STK OB <<< "$cfg"
    echo "--- $name (NI=$NI NO=$NO DW=$DW ARB=$ARB STK=$STK OB=$OB) ---"
    cat > "$WORK/synth_$name.ys" <<EOF
read_liberty -lib $LIB
read_verilog -sv $WORK/converted/arb_all.v
chparam -set NI $NI -set NO $NO -set DW $DW -set ARB "$ARB" -set STK $STK -set OB $OB arb_sweep_top
hierarchy -check -top arb_sweep_top
proc; opt
fsm; opt
memory; opt
memory_map; opt
alumacc; wreduce; share; opt
techmap; opt
dfflibmap -liberty $LIB
abc -markgroups -D 1.25 -liberty $LIB
tee -o $WORK/reports/stat_$name.rpt stat -liberty $LIB -top arb_sweep_top
EOF
    if ! "$YOSYS" -q -s "$WORK/synth_$name.ys" > "$WORK/reports/yosys_$name.log" 2>&1; then
        echo "FAILED: $name (see reports/yosys_$name.log)"
        AREA[$name]="FAILED"
        continue
    fi
    a=$(grep -E "Chip area for top module" "$WORK/reports/stat_$name.rpt" | tail -1 | sed -E "s/.*: *([0-9.]+).*/\1/")
    AREA[$name]="$a"
    echo "  area: $a um^2"
done

echo ""
echo "=== SUMMARY (Nangate45, um^2) ==="
printf "%-12s %4s %4s %5s %3s %6s %5s %12s\n" name NI NO DW ARB STK OB area
for cfg in "${CONFIGS[@]}"; do
    IFS=':' read -r name NI NO DW ARB STK OB <<< "$cfg"
    printf "%-12s %4s %4s %5s %3s %6s %5s %12s\n" "$name" "$NI" "$NO" "$DW" "$ARB" "$STK" "$OB" "${AREA[$name]}"
done