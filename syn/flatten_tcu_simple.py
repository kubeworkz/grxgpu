#!/usr/bin/env python3
"""
Flatten TFR + simple TCU modules for Yosys ECP5 synthesis.
Excludes modules that need VX_mem_bus_if, tcu_tbuf_req_t, tcu_header_t.
"""
import re, sys, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/grxgpu"
OUT  = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tcu_simple.sv"

TCU_DIR = os.path.join(ROOT, "hw/rtl/tcu")
TFR_DIR = os.path.join(TCU_DIR, "tfr")

# Only modules with 0 complex dependencies
SIMPLE_MODULES = [
    "VX_tcu_mx_scale.sv",
    "VX_tcu_lockstep.sv",
    "VX_tcu_dsm.sv",
    "VX_tcu_meta.sv",
    "VX_tcu_sp_mux.sv",
    "VX_tcu_uops.sv",
]

TFR_MODULES = [
    "VX_tcu_tfr_wmul.sv",
    "VX_tcu_tfr_shared_mul.sv",
    "VX_tcu_tfr_mul_join.sv",
    "VX_tcu_tfr_mul_f16.sv",
    "VX_tcu_tfr_mul_f8.sv",
    "VX_tcu_tfr_mul_f4.sv",
    "VX_tcu_tfr_mul_i8.sv",
    "VX_tcu_tfr_mul_i4.sv",
    "VX_tcu_tfr_classifier.sv",
    "VX_tcu_tfr_align.sv",
    "VX_tcu_tfr_max_exp.sv",
    "VX_tcu_tfr_lane_mask.sv",
    "VX_tcu_tfr_exc_reduce.sv",
    "VX_tcu_tfr_norm_round.sv",
    "VX_tcu_tfr_acc.sv",
    "VX_tcu_tfr_pipe_register.sv",
    "VX_tcu_fedp_tfr.sv",
]

ALL_MODULES = TFR_MODULES + SIMPLE_MODULES

# Import the flatten infrastructure
sys.path.insert(0, os.path.dirname(__file__))
from flatten_tcu import HEADER, transform, hoist_gen_scoped

def main():
    all_modules = []
    seen_modules = set()

    for mod_file in ALL_MODULES:
        if mod_file in TFR_MODULES:
            fpath = os.path.join(TFR_DIR, mod_file)
        else:
            fpath = os.path.join(TCU_DIR, mod_file)

        if not os.path.exists(fpath):
            print(f"  WARNING: {mod_file} not found, skipping")
            continue

        with open(fpath) as f:
            content = f.read()

        lines = content.split('\n')
        mod_start = 0
        for idx, line in enumerate(lines):
            if re.match(r'\s*module\s+', line):
                mod_start = idx
                break

        m = re.match(r'\s*module\s+(\w+)', lines[mod_start])
        if not m:
            continue
        mod_name = m.group(1)
        if mod_name in seen_modules:
            continue
        seen_modules.add(mod_name)

        mod_body = '\n'.join(lines[mod_start:])
        mod_body = transform(mod_body)
        mod_body = hoist_gen_scoped(mod_body)
        all_modules.append(mod_body)

    with open(OUT, 'w') as f:
        f.write(HEADER)
        f.write('\n\n')
        for mod in all_modules:
            f.write(mod)
            f.write('\n\n')

    print(f"Flattened {len(all_modules)} modules -> {OUT}")
    print(f"  File size: {os.path.getsize(OUT)} bytes")


if __name__ == '__main__':
    main()
