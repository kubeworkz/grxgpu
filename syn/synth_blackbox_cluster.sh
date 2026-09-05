#!/usr/bin/env bash
# =============================================================================
# GRX G100 Blackbox Cluster Synthesis (Yosys + Nangate45)
#
# WHY: The full 16-core (or 128-core) Vortex synthesizes to a single flat
# module after sv2v inlining, and Yosys's single-threaded `hierarchy` pass
# cannot elaborate it (2h+ and still in AST frontend, then OOM/timeout).
#
# FIX: Source-level blackbox. Stub out VX_core's body (same module signature,
# empty internals) BEFORE conversion, so sv2v inlines an empty core and only
# the socket/cluster fabric (L1s, L2, arbiters, crossbars, graphics/DXA glue)
# remains to synthesize. The core's own logic area is recovered by difference:
#
#     VX_core logic = Full_1_socket - BB1_socket_fabric
#     Cluster total = BB16_cluster_fabric + 16 * VX_core logic
#
# RESULTS (Nangate45, liberty area, RAM blackboxed, Sep 2026):
#   VX_core logic alone          :  434,146 um2  (0.434 mm2)
#   1-socket fabric (no core)    :  179,465 um2  (0.179 mm2)
#   16-socket cluster fabric     : 11,698,076 um2 (11.698 mm2)
#   16-core CLUSTER total        : 18,644,409 um2 (18.644 mm2)
#   G100 8 clusters (logic only) : 149,155,270 um2 (149.155 mm2)
#
# NOTE: Nangate45 is a 45nm library. Scaling to 28nm multiplies area by
# (28/45)^2 = 0.387 (cluster ~7.2 mm2, G100 logic ~57.8 mm2 @28nm).
# RAM macros (VX_dp_ram_asic / VX_sp_ram_asic) are blackboxed: their area
# is NOT included; add the SRAM estimate separately.
#
# USAGE:
#   This script documents the exact flow. It expects pre-generated,
#   macro-expanded SV source trees (1-socket and 16-socket) with the real
#   VX_core.sv replaced by syn/VX_core_stub.sv, converted to flat Verilog
#   via sv2v (hierarchy gets inlined), then synthesized by Yosys.
#
#   Yosys invocation (use the oss-cad-suite REAL path - the ~/tools/yosys
#   symlink breaks the wrapper's loader):
#     /home/ubuntu/tools/oss-cad-suite/bin/yosys -q -l yosys.log synth_host2.ys
#
#   IMPORTANT Yosys gotcha: `stat -tech cmos` crashes with
#   `std::out_of_range: map::at` on $paramod-derived cell types. Drop
#   `-tech cmos` (-width is fine); liberty area still prints.
# =============================================================================
set -euo pipefail

# --- Configuration -----------------------------------------------------------
LIB=/tmp/nangate45_lib/NangateOpenCellLibrary_typical.lib
YOSYS=${YOSYS:-/home/ubuntu/tools/oss-cad-suite/bin/yosys}

synth_one() { # $1 = name (bb1|bb16), $2 = sv2v'd flat verilog, $3 = workdir
    local name=$1 src=$2 work=$3
    mkdir -p "$work/reports"
    cat > "$work/synth_host2.ys" <<EOF
read_liberty -lib $LIB
read_verilog -sv $work/no_mem/VX_dp_ram_asic.v
read_verilog -sv $work/no_mem/VX_sp_ram_asic.v
read_verilog -I $work/src $work/$src
hierarchy -check -top Vortex
proc; opt
fsm; opt
memory; opt
memory_map; opt
alumacc; wreduce; share; opt
techmap; opt
dfflibmap -liberty $LIB
abc -markgroups -D 1.25 -liberty $LIB
tee -o $work/reports/stat.rpt stat -liberty $LIB -top Vortex
write_verilog -noattr -noexpr $work/reports/mapped.v
write_json $work/reports/netlist.json
EOF
    (cd "$work" && nohup "$YOSYS" -q -l yosys.log synth_host2.ys > synth.log 2>&1 &)
    echo "launched $name: pid $!"
}

echo "See header comment for flow documentation and measured results."
echo "Run synth_one for each fabric-only source tree (core stubbed)."
