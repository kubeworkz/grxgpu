#!/usr/bin/env python3
"""Add ALL missing macros to the flat TFR file"""
import re

with open("/tmp/tfr_flat.sv") as f:
    content = f.read()

# Comprehensive macro definitions
defines = """
// Yosys synthesis defines — all Vortex utility macros stubbed out
`define VX_CFG_XLEN 32
`define VX_CFG_NUM_THREADS 4
`define VX_CFG_NUM_WARPS 4
`define VX_CFG_NUM_TCU_LANES 4

`define STATIC_ASSERT(cond, msg)
`define FORCE_BUILTIN_ADDER  /* synthesis hint, ignore */
`define MAP_AOS_SOA(name) /* array mapping hint */
`define STRING(x) ""
`define TRACE(level, msg) /* trace */
`define TRACE_ARRAY(level, name, arr, sz) /* trace */
`define UNUSED_PARAM(x) /* unused */
`define UNUSED_PIN(x) /* unused */
`define UNUSED_SPARAM(x) /* unused */
`define UNUSED_VAR(x) /* unused */
`define CLOG(x) ($clog2(x))

"""

content = defines + content

# Strip remaining backtick-VX_CFG references
content = re.sub(r"`VX_CFG_NUM_THREADS", "4", content)
content = re.sub(r"`VX_CFG_NUM_WARPS", "4", content)
content = re.sub(r"`VX_CFG_NUM_TCU_LANES", "4", content)

with open("/tmp/tfr_flat.sv", "w") as f:
    f.write(content)

print(f"Updated: {len(content)} bytes")
