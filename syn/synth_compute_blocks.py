#!/usr/bin/env python3
"""Synthesize VX_alu_int for ECP5-85K."""
import subprocess, re, os, sys

YOSYS = os.path.expanduser("~/tools/synlig/synlig/synlig")
GRX = os.path.expanduser("~/grxgpu")

def read_file(path):
    with open(os.path.expanduser(path)) as f:
        return f.read()

def make_config():
    lines = ["`default_nettype wire"]
    cfg = {
        'NUM_THREADS': 16, 'XLEN': 32, 'NUM_LANES': 16, 'NW_WIDTH': 4,
        'NUM_WARPS': 16, 'NUM_TCU_BLOCKS': 2, 'NUM_TCU_LANES': 16,
        'ISSUE_WIDTH': 2, 'EXECUTE_DATA_W': 1024, 'RESULT_DATA_W': 512,
    }
    for k, v in cfg.items():
        lines.append(f"localparam {k} = {v};")
    lines.append("localparam ALU_TYPE_ARITH = 0;")
    lines.append("localparam ALU_TYPE_BRANCH = 1;")
    lines.append("localparam ALU_TYPE_MULDIV = 2;")
    return "\n".join(lines) + "\n"

# --- ALU Integer ---
def prepare_alu_int():
    src = read_file(f"{GRX}/hw/rtl/core/VX_alu_int.sv")
    # Strip includes and pragmas
    src = re.sub(r'`include[^\n]*\n', '', src)
    src = re.sub(r'`UNUSED_SPARAM[^\n]*\n', '', src)
    # Replace SV interface ports with flat wires
    src = src.replace(
        'VX_execute_if.slave     execute_if,',
        'input wire exec_valid, output wire exec_ready,\n'
        '    input wire [7:0] exec_op_type, input wire [1:0] exec_xtype,\n'
        '    input wire exec_is_w,\n'
        '    input wire [NUM_LANES-1:0][XLEN-1:0] exec_rs1,\n'
        '    input wire [NUM_LANES-1:0][XLEN-1:0] exec_rs2,\n'
        '    input wire [19:0] exec_imm20,\n'
        '    input wire [4:0] exec_rd,\n'
        '    input wire [NW_WIDTH-1:0] exec_wid,'
    )
    src = src.replace(
        'VX_result_if.master     result_if,',
        'output wire res_valid, input wire res_ready,\n'
        '    output wire [NUM_LANES-1:0][XLEN-1:0] res_data,\n'
        '    output wire [4:0] res_rd,\n'
        '    output wire [NW_WIDTH-1:0] res_wid,'
    )
    src = src.replace(
        'VX_branch_ctl_if.master branch_ctl_if',
        'output wire br_valid, output wire [1:0] br_taken, output wire [XLEN-1:0] br_target'
    )
    # Replace all execute_if.data.xxx references
    for old, new in [
        ('execute_if.data.op_args.alu.xtype', 'exec_xtype'),
        ('execute_if.data.op_args.alu.is_w', 'exec_is_w'),
        ('execute_if.data.op_args.alu.imm20', 'exec_imm20'),
        ('execute_if.data.op_type', 'exec_op_type'),
        ('execute_if.data.rs1_data', 'exec_rs1'),
        ('execute_if.data.rs2_data', 'exec_rs2'),
        ('execute_if.data.rd', 'exec_rd'),
        ('execute_if.data.wid', 'exec_wid'),
    ]:
        src = src.replace(old, new)
    # Replace result_if references
    src = src.replace('result_if.data.alu_result', 'res_data')
    src = src.replace('result_if.valid', 'res_valid')
    src = src.replace('result_if.ready', 'res_ready')
    src = src.replace('result_if.data.wb', 'res_wb')
    src = src.replace('result_if.data.rd', 'res_rd')
    src = src.replace('result_if.data.wdata', 'res_data')
    src = src.replace('result_if.data.eop', 'res_eop')
    # Add wb/eop defaults
    src = src.replace(
        'output wire [NW_WIDTH-1:0] res_wid,',
        'output wire [NW_WIDTH-1:0] res_wid,\n    output wire res_wb, output wire res_eop,'
    )
    src = "assign res_wb = 1;\nassign res_eop = 1;\n" + src
    return src

def synthesize(name, content, top):
    path = f"/tmp/synth_{name}.sv"
    with open(path, "w") as f:
        f.write(make_config() + "\n" + content)
    cmd = f"cd /tmp && {YOSYS} -p 'read_verilog -sv synth_{name}.sv; synth_ecp5 -top {top}; stat' 2>&1"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
    stats = {}
    for pat in [r'(LUT4)\s+(\d+)', r'(TRELLIS_FF)\s+(\d+)', r'(CCU2C)\s+(\d+)',
                r'(PFUMX)\s+(\d+)', r'(TRELLIS_DPR16X4)\s+(\d+)']:
        m = re.search(pat, r.stdout)
        if m:
            stats[m.group(1)] = int(m.group(2))
    print(f"\n=== {name} ({top}) ===")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    # Show errors if any
    errors = [l for l in r.stdout.split("\n") if "ERROR" in l]
    if errors:
        for e in errors[:5]:
            print(f"  ERR: {e}")
    return stats

if __name__ == "__main__":
    # TCU already measured
    tcu = {'LUT4': 179, 'TRELLIS_FF': 143, 'CCU2C': 12, 'PFUMX': 44, 'TRELLIS_DPR16X4': 16}

    # Synthesize ALU
    print("Synthesizing VX_alu_int...")
    try:
        alu = synthesize("alu_int", prepare_alu_int(), "VX_alu_int")
    except Exception as e:
        print(f"ALU failed: {e}")
        alu = {}

    # Summary
    NUM_TCU = 2  # G100: 2 TCU blocks per core
    NUM_ALU = 2  # G100: 2 ALU blocks per core

    total_lut = tcu.get('LUT4', 0) * NUM_TCU + alu.get('LUT4', 0) * NUM_ALU
    total_ff = tcu.get('TRELLIS_FF', 0) * NUM_TCU + alu.get('TRELLIS_FF', 0) * NUM_ALU
    total_bram = tcu.get('TRELLIS_DPR16X4', 0) * NUM_TCU

    print("\n" + "=" * 60)
    print("VX_core Compute Block — ECP5-85K")
    print("=" * 60)
    print(f"\n  {NUM_TCU}× TCU core: {tcu.get('LUT4',0)*NUM_TCU} LUT4, {tcu.get('TRELLIS_FF',0)*NUM_TCU} FF, {tcu.get('TRELLIS_DPR16X4',0)*NUM_TCU} BRAM")
    print(f"  {NUM_ALU}× ALU int:  {alu.get('LUT4',0)*NUM_ALU} LUT4, {alu.get('TRELLIS_FF',0)*NUM_ALU} FF")
    print(f"\n  TOTAL per core: {total_lut} LUT4, {total_ff} FF, {total_bram} BRAM")
    print(f"\n  ECP5-85K utilization (single core):")
    print(f"    LUT4:  {total_lut} / 84,160 = {total_lut*100/84160:.3f}%")
    print(f"    FF:    {total_ff} / 16,688 = {total_ff*100/16688:.3f}%")
    print(f"    BRAM:  {total_bram} / 1,080 = {total_bram*100/1080:.3f}%")
    print(f"\n  Full G100 (8 cores): {total_lut*8} LUT4, {total_ff*8} FF")
    print(f"  Full G100 utilization: {total_lut*8*100/84160:.2f}% LUT4, {total_ff*8*100/16688:.2f}% FF")
