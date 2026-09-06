#!/usr/bin/env bash
# Standalone comparison: VX_mem_bus_arb (L2 shape 32->2 x 630b) with
# DATA_OOB=0 (inline 630b through the arb) vs DATA_OOB=1 (54b control
# through the arb + 576b data plane through a bufferless switch).
# Reuses the same sv2v + Yosys Nangate45 flow as arb_area_sweep.sh.
set -euo pipefail

WORK="${1:-/tmp/oob_arb}"
RTL=/home/ubuntu/grxgpu/hw/rtl
LIBS=$RTL/libs
MEM=$RTL/mem
SV2V=/home/ubuntu/tools/sv2v/bin/sv2v
YOSYS=/home/ubuntu/tools/oss-cad-suite/bin/yosys
LIB=/tmp/nangate45_lib/NangateOpenCellLibrary_typical.lib
TOP_SV=/tmp/oob_arb_top.sv

mkdir -p "$WORK/converted" "$WORK/reports"

echo "=== sv2v converting ==="
SV2V_ARGS=(-I "$RTL" -I "$LIBS" -I "$MEM" --top oob_arb_wrap \
    -DVX_CFG_XLEN=32 \
    -DVX_CFG_EXT_TCU_ENABLE \
    -DVX_CFG_EXT_DXA_ENABLE \
    "$RTL/VX_gpu_pkg.sv" \
    "$MEM/VX_mem_bus_if.sv" \
    "$MEM/VX_mem_bus_arb.sv")
for f in "$LIBS"/*.sv; do
    SV2V_ARGS+=("$f")
done
SV2V_ARGS+=("/tmp/oob_arb_wrap.sv" "/tmp/oob_arb_top.sv")
"$SV2V" "${SV2V_ARGS[@]}" \
    > "$WORK/converted/oob_all.v" 2> "$WORK/converted/sv2v.log" || {
        echo "sv2v failed"; tail -20 "$WORK/converted/sv2v.log"; exit 1; }
echo "converted: $(wc -l < "$WORK/converted/oob_all.v") lines"

for oob in 0 1; do
    name="oob$oob"
    echo "--- DATA_OOB=$oob ---"
    cat > "$WORK/synth_$name.ys" <<EOF
read_liberty -lib $LIB
read_verilog -sv $WORK/converted/oob_all.v
chparam -set DATA_OOB $oob oob_arb_wrap
hierarchy -check -top oob_arb_wrap
proc; opt
fsm; opt
memory; opt
memory_map; opt
alumacc; wreduce; share; opt
techmap; opt
dfflibmap -liberty $LIB
abc -markgroups -D 1.25 -liberty $LIB
tee -o $WORK/reports/stat_$name.rpt stat -liberty $LIB -top oob_arb_wrap
EOF
    if ! "$YOSYS" -q -s "$WORK/synth_$name.ys" > "$WORK/reports/yosys_$name.log" 2>&1; then
        echo "FAILED: $name"; tail -8 "$WORK/reports/yosys_$name.log"; continue
    fi
    a=$(grep -E "Chip area for top module" "$WORK/reports/stat_$name.rpt" | tail -1 | sed -E "s/.*: *([0-9.]+).*/\1/")
    echo "  area: $a um^2"
done

echo ""
echo "=== SUMMARY (Nangate45, 32->2 x 630b L2 arb) ==="
a0=$(grep -E "Chip area for top module" "$WORK/reports/stat_oob0.rpt" | tail -1 | sed -E "s/.*: *([0-9.]+).*/\1/")
a1=$(grep -E "Chip area for top module" "$WORK/reports/stat_oob1.rpt" | tail -1 | sed -E "s/.*: *([0-9.]+).*/\1/")
echo "DATA_OOB=0 (inline 630b): $a0 um^2"
echo "DATA_OOB=1 (54b + switch): $a1 um^2"
python3 -c "print(f'delta: {(float('$a1')-float('$a0'))/float('$a0')*100:+.1f}%')" 2>/dev/null || echo "delta: see above"