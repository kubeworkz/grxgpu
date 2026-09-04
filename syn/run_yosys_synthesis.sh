#!/bin/bash
# Full GRX G100 synthesis via Docker ORFS
# Uses sv2v → Yosys flow (the existing Vortex synthesis approach)
set -euo pipefail

GRXGPU_HOME="${GRXGPU_HOME:-/home/ubuntu/grxgpu}"
WORK="/tmp/synth_g100"
DOCKER_IMAGE="openroad/orfs:latest"

# Configuration: single cluster, N cores
NUM_CLUSTERS="${NUM_CLUSTERS:-1}"
NUM_CORES="${NUM_CORES:-4}"
XLEN=32
CLOCK_FREQ=800

mkdir -p "$WORK/src" "$WORK/reports"

echo "=== Step 1: Generate SV sources ==="
cd "$GRXGPU_HOME"

# Build the defines string
DEFINES="-DVX_CFG_XLEN=$XLEN"
DEFINES="$DEFINES -DSYNTHESIS -DASIC -DYOSYS"
DEFINES="$DEFINES -DVX_CFG_NUM_CLUSTERS=$NUM_CLUSTERS -DVX_CFG_NUM_CORES=$NUM_CORES"

# Generate XCONFIGS from TOML
XCONFIGS=$(python3 ci/gen_config.py \
  --config="$GRXGPU_HOME/VX_config.toml" \
  --cflags="$DEFINES -DVX_CFG_XLEN=$XLEN" 2>/dev/null || echo "")

echo "XCONFIGS length: ${#XCONFIGS}"

# Generate the source file list via gen_sources.sh
bash hw/scripts/gen_sources.sh \
  -P "-DVX_CFG_XLEN=$XLEN -DSYNTHESIS -DASIC -DYOSYS -DVX_CFG_NUM_CLUSTERS=$NUM_CLUSTERS -DVX_CFG_NUM_CORES=$NUM_CORES" \
  -C "$WORK/src" 2>&1 | tail -20

# Count generated sources
SRC_COUNT=$(ls "$WORK/src"/*.sv 2>/dev/null | wc -l)
echo "Generated $SRC_COUNT SV sources"

echo "=== Step 2: Convert SV → V with sv2v (Docker) ==="
# Use Docker with sv2v installed
docker run --rm \
  -v "$WORK":/work \
  -v "$GRXGPU_HOME":/grxgpu \
  "$DOCKER_IMAGE" bash -c '
set -euo pipefail
cd /work

# Install sv2v
if ! command -v sv2v >/dev/null 2>&1; then
  echo "sv2v not found, building from Yosys..."
  # sv2v is a standalone tool; use Yosys read_verilog -sv instead
fi

# List sources
echo "Source count: $(ls src/*.sv 2>/dev/null | wc -l)"

# Convert SV to V using Yosys sv2v equivalent
# Actually, Yosys 0.68 can read SV directly with read_verilog -sv
# But the $bits() issue persists. Let us try the read_verilog -defer -sv approach.
echo "=== Attempting Yosys synthesis ==="

# Find the Nangate45 liberty
LIB="/OpenROAD-flow-scripts/flow/platforms/nangate45/libs/NangateOpenCellLibrary_typical.lib"
if [ ! -f "$LIB" ]; then
  LIB=$(find / -name "NangateOpenCellLibrary_typical.lib" 2>/dev/null | head -1)
fi
echo "Liberty: $LIB"

# Also look for the 28nm library
LIB28=$(find /grxgpu/hw/syn/libs -name "*.lib" 2>/dev/null | head -5)
echo "28nm libs: $LIB28"

# Create the Yosys script
cat > synth.ys << YSEOF
verilog_defaults -add -sv
verilog_defaults -add -I /grxgpu/hw/rtl
verilog_defaults -add -I /grxgpu/hw/rtl/libs
verilog_defaults -add -I /grxgpu/hw/rtl/interfaces
verilog_defaults -add -I /grxgpu/hw/rtl/core
verilog_defaults -add -I /grxgpu/hw/rtl/mem
verilog_defaults -add -I /grxgpu/hw/rtl/cache
verilog_defaults -add -I /grxgpu/hw/rtl/tcu
verilog_defaults -add -I /grxgpu/hw/rtl/tcu/tfr
verilog_defaults -add -I /grxgpu/hw/rtl/dxa
verilog_defaults -add -I /grxgpu/hw/rtl/gfx
verilog_defaults -add -I /grxgpu/hw/rtl/tex
verilog_defaults -add -I /grxgpu/hw/rtl/raster
verilog_defaults -add -I /grxgpu/hw/rtl/om
verilog_defaults -add -I /grxgpu/hw/rtl/fpu
verilog_defaults -add -I /grxgpu/sw
verilog_defaults -add -I /work/src
verilog_defaults -add -D VX_CFG_XLEN=32
verilog_defaults -add -D VX_CFG_XLEN_32
verilog_defaults -add -D SYNTHESIS
verilog_defaults -add -D ASIC
verilog_defaults -add -D YOSYS
verilog_defaults -add -D VX_CFG_NUM_CLUSTERS=1
verilog_defaults -add -D VX_CFG_NUM_CORES=4
YSEOF

# Add all defines from XCONFIGS (first 100 macros)
for def in $XCONFIGS; do
  echo "verilog_defaults -add $def" >> synth.ys
done

# Add liberty
echo "read_liberty -lib \"$LIB\"" >> synth.ys

# Add all source files
for f in src/*.sv; do
  echo "read_verilog -defer \"$f\"" >> synth.ys
done

# Add synthesis commands
cat >> synth.ys << YSEOF2
hierarchy -check -top Vortex
proc; opt
fsm; opt
memory; opt
memory_map; opt
alumacc; wreduce; share; opt
techmap; opt
dfflibmap -liberty "$LIB"
abc -markgroups -D 1.25 -liberty "$LIB"
tee -o reports/stat.rpt stat -liberty "$LIB" -top Vortex -width -tech cmos
write_verilog -noattr -noexpr mapped.v
write_json netlist.json
YSEOF2

mkdir -p reports
yosys -s synth.ys -l reports/yosys.log 2>&1
RC=$?

echo "=== Results ==="
if [ $RC -eq 0 ]; then
  cat reports/stat.rpt
else
  echo "Yosys failed with exit code $RC"
  cat reports/yosys.log | tail -40
fi
'

echo "=== COMPLETE ==="
