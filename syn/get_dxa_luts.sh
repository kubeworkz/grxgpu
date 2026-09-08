#!/bin/bash
cd /tmp/dxa_synth
SYNLIG=~/tools/synlig/synlig/synlig
DEFS="-DVX_CFG_XLEN=32 -DVX_CFG_MEM_ADDR_WIDTH=32 -DVX_CFG_L1_LINE_SIZE=64 -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_DXA_QUEUE_SIZE=4 -DVX_CFG_L1_MEM_PORTS=1 -DVX_CFG_LMEM_LOG_SIZE=15 -DVX_CFG_LMEM_NUM_BANKS=1 -DRUNTIME_ASSERT="
PKGS="VX_define.vh VX_platform.vh vx_gpu_pkg_stub.sv VX_tcu_pkg.sv VX_dxa_pkg.sv VX_mem_bus_if.sv VX_dcr_bus_if.sv VX_txbar_bus_if.sv VX_execute_if.sv VX_result_if.sv VX_dxa_req_bus_if.sv VX_dxa_worker_req_if.sv vortex_stubs.sv"

for mod in VX_dxa_watchdog VX_dxa_completion VX_dxa_dispatch VX_dxa_req_arb VX_dxa_desc_table; do
    echo "=== $mod ==="
    $SYNLIG -p "read_systemverilog $DEFS -I. $PKGS ${mod}.sv; hierarchy -top $mod; synth_ecp5 -top ${mod}; stat" 2>&1 | grep -A30 "Number of cells:" | tail -25
    echo ""
done
