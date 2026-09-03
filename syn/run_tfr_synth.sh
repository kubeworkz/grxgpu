#!/bin/bash
# Preprocess GRXGPU RTL for Yosys synthesis:
# 1. Read VX_define.vh (pulls in config/types)
# 2. Read VX_gpu_pkg.sv and VX_tcu_pkg.sv (with $bits stripped)
# 3. Read all TCU/TFR RTL files
# 4. Feed to Yosys for synthesis
set -e

ROOT=~/grxgpu
OUTDIR=$ROOT/syn/out
mkdir -p $OUTDIR

export PATH=~/miniforge3/bin:$PATH

echo "=== Step 1: Preprocess packages (strip \$bits and assertions) ==="

# Create synthesis-compatible gpu_pkg
python3 << 'PYEOF'
import re

# Read VX_gpu_pkg.sv
with open("/home/ubuntu/grxgpu/hw/rtl/VX_gpu_pkg.sv") as f:
    src = f.read()

# Known $bits() replacements (computed from struct definitions)
replacements = {
    '$bits(amo_req_t)': '38',
    '$bits(mem_bus_attr_t)': '5',
    '$bits(amo_op_e)': '3',
    '$bits(lsu_header_t)': '128',
    '$bits(alu_args_t)': '256',
    '$bits(br_args_t)': '256',
    '$bits(fpu_args_t)': '256',
    '$bits(lsu_args_t)': '256',
    '$bits(csr_args_t)': '256',
    '$bits(wctl_args_t)': '256',
    '$bits(dxa_args_t)': '256',
    '$bits(tcu_args_t)': '256',
    '$bits(tex_args_t)': '256',
    '$bits(om_args_t)': '256',
    '$bits(raster_args_t)': '256',
    '$bits(gfxw_args_t)': '256',
    '$bits(op_args_t)': '256',
}

# Replace $bits() with known values
for old, new in replacements.items():
    src = src.replace(old, new)

# Strip any remaining $bits() with a warning
remaining = re.findall(r'\$bits\((\w+)\)', src)
for r in remaining:
    print(f"  WARN: Replacing unknown $bits({r}) with 32")
    src = src.replace(f'$bits({r})', '32')

# Replace PACKAGE_ASSERT with empty comments
src = re.sub(r'`PACKAGE_ASSERT\([^)]*\)', '/* assertion stripped for synth */', src)

with open("/tmp/VX_gpu_pkg_synth.sv", "w") as f:
    f.write(src)

print("  VX_gpu_pkg_synth.sv written ({} bytes)".format(len(src)))
PYEOF

echo "=== Step 2: Create Yosys synthesis script ==="

cat > $OUTDIR/tfr_synth.ys << YOSEOF
# TFR (Tensor Floating-point Reduction) synthesis
# The core compute engine for GRXGPU's tensor unit

# Include paths and defines
verilog_defaults -add -sv -I/home/ubuntu/grxgpu/hw -I/home/ubuntu/grxgpu/hw/rtl -DVX_CFG_XLEN=32 -DSYNTHESIS -DYOSYS

# Preprocessed packages
read_verilog /home/ubuntu/grxgpu/hw/rtl/VX_define.vh
read_verilog /tmp/VX_gpu_pkg_synth.sv
read_verilog -defer /home/ubuntu/grxgpu/hw/rtl/tcu/VX_tcu_pkg.sv

# TFR sub-modules (the actual compute engine)
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_fedp_tfr.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_acc.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_align.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_classifier.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_exc_reduce.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_lane_mask.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_max_exp.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_f16.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_f4.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_f8.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_i4.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_i8.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_mul_join.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_norm_round.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_pipe_register.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_shared_mul.sv
read_verilog /home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_tfr_wmul.sv

# Elaborate and check hierarchy
hierarchy -top VX_tcu_fedp_tfr -check

# Synthesis
synth -flatten -run begin:fine

# Statistics
stat

# Output
write_verilog -noattr /home/ubuntu/grxgpu/syn/out/tfr_synth.v
write_json /home/ubuntu/grxgpu/syn/out/tfr_synth.json
YOSEOF

echo "=== Step 3: Run Yosys synthesis ==="
yosys -s $OUTDIR/tfr_synth.ys 2>&1 | tee $OUTDIR/tfr_synth.log

echo "=== Done ==="
ls -la $OUTDIR/tfr_synth.*
