#!/usr/bin/env python3
"""Find lines with backtick-macro issues in the flat file."""
import re, sys

with open(sys.argv[1]) as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    # Look for remaining backtick-escaped identifiers that Yosys can't handle
    for m in re.finditer(r'`(\w+)', line):
        macro = m.group(1)
        # Skip our defines
        if macro in ('VX_CFG_XLEN', 'VX_CFG_NUM_THREADS', 'VX_CFG_NUM_WARPS',
                      'VX_CFG_NUM_TCU_LANES', 'CLOG2', 'LOG2UP', 'FORCE_BUILTIN_ADDER',
                      'MAP_AOS_SOA', 'UNUSED_PARAM', 'UNUSEDWire', 'STATIC_ASSERT',
                      'TRACING_OFF', 'TRACE', 'TRACE_ARRAY',
                      'ifdef', 'ifndef', 'endif', 'elsif', 'else', 'define', 'undef', 'include'):
            continue
        # Check for non-ASCII or problematic context
        context = line.rstrip()[:120]
        print(f"{i}: `{macro} -- {context}")
