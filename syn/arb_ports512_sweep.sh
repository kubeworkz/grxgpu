#!/usr/bin/env bash
# Sweep VX_stream_arb port count at the cluster's real L2 request width (DW=512).
# Reuses the same sv2v + Yosys Nangate45 flow as arb_area_sweep.sh.
set -euo pipefail

WORK="${1:-/tmp/arb_sweep512}"
RTL=/home/ubuntu/grxgpu/hw/rtl
LIBS=$RTL/libs
SV2V=/home/ubuntu/tools/sv2v/bin/sv2v
YOSYS=/home/ubuntu/tools/oss-cad-suite/bin/yosys
LIB=/tmp/nangate45_lib/NangateOpenCellLibrary_typical.lib
TOP_SV=/tmp/arb_sweep_top.sv

mkdir -p "$WORK/converted" "$WORK/reports"

if [ ! -f "$WORK/converted/arb_all.v" ]; then
    echo "=== sv2v converting libs + wrapper ==="
    SV2V_ARGS=(-I "$RTL" -I "$LIBS" --top arb_sweep_top)
    for f in "$LIBS"/*.sv; do
        SV2V_ARGS+=("$f")
    done
    SV2V_ARGS+=("$TOP_SV")
    "$SV2V" "${SV2V_ARGS[@]}" > "$WORK/converted/arb_all.v" 2> "$WORK/converted/sv2v.log" || {
        echo "sv2v failed"; tail -20 "$WORK/converted/sv2v.log"; exit 1; }
    echo "converted: $(wc -l < "$WORK/converted/arb_all.v") lines"
fi

# --- Sweep: NI at DW=512, 1 output, round-robin, flat (MF=0) ---
CONFIGS=(
    "p2:2:1:512:R:0:0:0"
    "p4:4:1:512:R:0:0:0"
    "p8:8:1:512:R:0:0:0"
    "p16:16:1:512:R:0:0:0"
    "p24:24:1:512:R:0:0:0"
    "p32:32:1:512:R:0:0:0"
    "p64:64:1:512:R:0:0:0"
)

echo "=== synthesizing ==="
declare -A AREA
for cfg in "${CONFIGS[@]}"; do
    IFS=':' read -r name NI NO DW ARB STK OB MF <<< "$cfg"
    echo "--- $name (NI=$NI NO=$NO DW=$DW MF=$MF) ---"
    cat > "$WORK/synth_$name.ys" <<EOF
read_liberty -lib $LIB
read_verilog -sv $WORK/converted/arb_all.v
chparam -set NI $NI -set NO $NO -set DW $DW -set ARB "$ARB" -set STK $STK -set OB $OB -set MF $MF arb_sweep_top
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
        tail -5 "$WORK/reports/yosys_$name.log"
        AREA[$name]="FAILED"
        continue
    fi
    a=$(grep -E "Chip area for top module" "$WORK/reports/stat_$name.rpt" | tail -1 | sed -E "s/.*: *([0-9.]+).*/\1/")
    AREA[$name]="$a"
    echo "  area: $a um^2"
done

echo ""
echo "=== SUMMARY DW=512 (Nangate45, um^2) ==="
printf "%-8s %4s %6s %14s %12s\n" name NI DW area per-in-per-bit
for cfg in "${CONFIGS[@]}"; do
    IFS=':' read -r name NI NO DW ARB STK OB MF <<< "$cfg"
    a="${AREA[$name]}"
    if [ "$a" != "FAILED" ]; then
        per=$(python3 -c "print(f'{$a/$NI/DW:.3f}')")
    else
        per="--"
    fi
    printf "%-8s %4s %6s %14s %12s\n" "$name" "$NI" "$DW" "$a" "$per"
done