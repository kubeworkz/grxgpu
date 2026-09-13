#!/bin/bash
set -e
ROOT=~/grxgpu
OUTDIR=~/grxgpu/syn/out
mkdir -p $OUTDIR

echo "=== Yosys version ==="
~/miniforge3/bin/yosys --version

echo "=== Starting TCU synthesis ==="

# Write Yosys commands
cat > $OUTDIR/synth.ys << 'YOSEOF'
# Read configuration headers with defines
read_verilog -IROOT/hw -DSYNTHESIS -DYOSYS ROOT/hw/VX_config.vh
read_verilog -IROOT/hw -DSYNTHESIS -DYOSYS ROOT/hw/VX_types.vh

# Packages (deferred)
read_verilog -defer ROOT/hw/rtl/VX_gpu_pkg.sv
read_verilog -defer ROOT/hw/rtl/tcu/VX_tcu_pkg.sv

# TCU RTL
read_verilog ROOT/hw/rtl/tcu/VX_tcu_unit.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_core.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_wgmma.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_uops.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_tbuf.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_abuf.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_bbuf.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_agu.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_dsm.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_meta.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_mx_scale.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_sp_mux.sv
read_verilog ROOT/hw/rtl/tcu/VX_tcu_lockstep.sv

# TFR sub-modules
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_fedp_tfr.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_acc.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_align.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_classifier.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_exc_reduce.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_lane_mask.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_max_exp.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_f16.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_f4.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_f8.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_i4.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_i8.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_join.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_norm_round.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_pipe_register.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_shared_mul.sv
read_verilog ROOT/hw/rtl/tcu/tfr/VX_tcu_tfr_wmul.sv

# Synthesis
hierarchy -top VX_tcu_unit -check
synth -flatten -run begin:fine
stat

# Output
write_verilog -noattr ROOT/syn/out/tcu_synth.v
write_json ROOT/syn/out/tcu_synth.json
YOSEOF

# Fix ROOT paths in the generated script
sed -i "s|ROOT|$ROOT|g" $OUTDIR/synth.ys

echo "Running Yosys..."
~/miniforge3/bin/yosys -s $OUTDIR/synth.ys 2>&1 | tee $OUTDIR/synth.log

echo "=== Synthesis complete ==="
echo "Results in: $OUTDIR"
