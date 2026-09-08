#!/bin/bash
cd /tmp/dxa_synth
SYNLIG=~/tools/synlig/synlig/synlig
DEFS="-DVX_CFG_XLEN=32 -DVX_CFG_MEM_ADDR_WIDTH=32 -DVX_CFG_L1_LINE_SIZE=64 -DVX_CFG_NUM_DXA_CORES=2 -DVX_CFG_DXA_QUEUE_SIZE=4 -DVX_CFG_L1_MEM_PORTS=1 -DVX_CFG_LMEM_LOG_SIZE=15 -DVX_CFG_LMEM_NUM_BANKS=1 -DRUNTIME_ASSERT="
PKGS="VX_define.vh VX_platform.vh vx_gpu_pkg_stub.sv VX_tcu_pkg.sv VX_dxa_pkg.sv VX_mem_bus_if.sv VX_dcr_bus_if.sv VX_txbar_bus_if.sv VX_execute_if.sv VX_result_if.sv VX_dxa_req_bus_if.sv VX_dxa_worker_req_if.sv vortex_stubs.sv"
YOSYS_DOCKER="docker run --rm -v /tmp/dxa_synth:/work openroad/ubuntu24.04 yosys"

# Modules to synthesize individually
MODULES="VX_dxa_watchdog VX_dxa_completion VX_dxa_dispatch VX_dxa_req_arb VX_dxa_desc_table"

for mod in $MODULES; do
    echo "=== $mod ECP5 ==="
    # First parse with Synlig
    $SYNLIG -p "read_systemverilog $DEFS -I. $PKGS ${mod}.sv; hierarchy -top $mod; write_rtlil /work/${mod}.il" 2>/dev/null
    if [ -f "/tmp/dxa_synth/${mod}.il" ]; then
        # Then map to ECP5
        $YOSYS_DOCKER -p "read_rtlil /work/${mod}.il; synth_ecp5 -top ${mod}; stat" 2>&1 | grep -E 'Number of|errors' | head -10
    else
        echo "  RTLIL generation failed"
    fi
    echo ""
done
