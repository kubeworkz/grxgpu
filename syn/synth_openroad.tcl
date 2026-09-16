# GRX G100 OpenROAD Synthesis Script
# Uses sv_elaborate (slang-based) to handle SystemVerilog features like $bits()

# Read technology library
read_liberty /libs/Nangate45_typ_noclk.lib

# Read all RTL sources with include paths
# Packages first
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw /grxgpu/hw/VX_types.vh
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw /grxgpu/hw/VX_config.vh
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl /grxgpu/hw/rtl/VX_gpu_pkg.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl /grxgpu/hw/rtl/VX_trace_pkg.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/tcu /grxgpu/hw/rtl/tcu/VX_tcu_pkg.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/dxa /grxgpu/hw/rtl/dxa/VX_dxa_pkg.sv

# Cache modules
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache_bank.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache_data.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache_tags.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache_mshr.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache_repl.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache_init.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache_flush.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache_amo.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache_bypass.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache_cluster.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_cache_wrap.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_amo_alu.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/cache /grxgpu/hw/rtl/cache/VX_amo_unit.sv

# Core modules
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_core.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_fetch.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_decode.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_issue.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_issue_slice.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_execute.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_commit.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_scheduler.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_scoreboard.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_operands.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_alu_unit.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_alu_int.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_alu_muldiv.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_lsu_unit.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_lsu_slice.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_lsu_agu.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_lsu_scheduler.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_csr_unit.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_csr_data.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_sfu_unit.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_bar_unit.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_mem_unit.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_opc_unit.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_ibuffer.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_split_join.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_ipdom_stack.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_cta_dispatch.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_dispatcher.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_decompressor.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_dcr_arb.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_dcr_data.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_dcr_flush.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_lane_dispatch.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_lane_gather.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_pe_switch.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_kmu_arb.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_txbar_arb.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_uop_packld.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/core /grxgpu/hw/rtl/core/VX_uop_sequencer.sv

# TCU modules
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/tcu /grxgpu/hw/rtl/tcu/VX_tcu_core.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/tcu /grxgpu/hw/rtl/tcu/VX_tcu_agu.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/tcu /grxgpu/hw/rtl/tcu/VX_tcu_abuf.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/tcu /grxgpu/hw/rtl/tcu/VX_tcu_bbuf.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/tcu /grxgpu/hw/rtl/tcu/VX_tcu_dsm.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/tcu /grxgpu/hw/rtl/tcu/VX_tcu_lockstep.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/tcu /grxgpu/hw/rtl/tcu/VX_tcu_meta.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/tcu /grxgpu/hw/rtl/tcu/VX_tcu_mx_scale.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/tcu /grxgpu/hw/rtl/tcu/VX_tcu_sp_mux.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/tcu /grxgpu/hw/rtl/tcu/VX_tcu_wgmma.sv

# DXA modules
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/dxa /grxgpu/hw/rtl/dxa/VX_dxa_core.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/dxa /grxgpu/hw/rtl/dxa/VX_dxa_addr_gen.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/dxa /grxgpu/hw/rtl/dxa/VX_dxa_completion.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/dxa /grxgpu/hw/rtl/dxa/VX_dxa_desc_table.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/dxa /grxgpu/hw/rtl/dxa/VX_dxa_dispatch.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/dxa /grxgpu/hw/rtl/dxa/VX_dxa_gmem_req.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/dxa /grxgpu/hw/rtl/dxa/VX_dxa_req_arb.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/dxa /grxgpu/hw/rtl/dxa/VX_dxa_setup.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl -I /grxgpu/hw/rtl/dxa /grxgpu/hw/rtl/dxa/VX_dxa_smem_wr.sv

# KMU
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl /grxgpu/hw/rtl/VX_kmu.sv

# Socket and cluster
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl /grxgpu/hw/rtl/VX_socket.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl /grxgpu/hw/rtl/VX_cluster.sv

# Top-level
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl /grxgpu/hw/rtl/Vortex.sv
read_verilog -sv -DVX_CFG_XLEN=32 -DVX_CFG_XLEN_32 -I /grxgpu/hw -I /grxgpu/hw/rtl /grxgpu/hw/rtl/Vortex_axi.sv

# Use sv_elaborate to handle SystemVerilog features
puts "=== Elaborating design with slang ==="
sv_elaborate -top Vortex_axi

# Synthesize
puts "=== Synthesizing ==="
synthesize

# Print statistics
puts "=== Statistics ==="
stats

# Write gate-level netlist
write_verilog /out/grxgpu_g100_synthesized.v

puts "=== Done ==="
exit
