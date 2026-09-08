#!/usr/bin/env python3
"""Concatenate all DXA sources into a single file for Yosys synthesis."""
import re, os

os.chdir("/tmp/dxa_synth")

files = [
    "VX_platform.vh",
    "VX_define.vh",
    "vx_gpu_pkg_stub.sv",
    "VX_tcu_pkg.sv",
    "VX_dxa_pkg.sv",
    "VX_dxa_addr_gen.sv", "VX_dxa_watchdog.sv", "VX_dxa_desc_table.sv",
    "VX_dxa_setup.sv", "VX_dxa_completion.sv", "VX_dxa_dispatch.sv",
    "VX_dxa_gmem_req.sv", "VX_dxa_smem_wr.sv", "VX_dxa_worker.sv",
    "VX_dxa_req_arb.sv", "VX_dxa_core.sv", "VX_dxa_unit.sv",
    "vortex_stubs.sv",
]

out = []
for f in files:
    try:
        with open(f) as fh:
            content = fh.read()
        # Strip backtick preprocessor directives that Yosys can't handle
        content = re.sub(r'^\s*`include.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*`define.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*`ifdef.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*`ifndef.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*`endif.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*`else.*$', '', content, flags=re.MULTILINE)
        out.append(f"// === {f} ===")
        out.append(content)
        print(f"  {f}: {len(content)} chars")
    except Exception as e:
        print(f"  SKIP {f}: {e}")

with open("dxa_flat_all.sv", "w") as fh:
    fh.write("\n".join(out))
print(f"Written dxa_flat_all.sv: {sum(len(l) for l in out)} chars")
