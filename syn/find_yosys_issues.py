#!/usr/bin/env python3
"""Find Yosys-incompatible constructs in tcu_struct.sv."""
import re

with open("/tmp/tcu_struct.sv") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    # Check for stray backtick followed by identifier (macro reference not stripped)
    if '`' in line and not line.strip().startswith('`define'):
        stripped = line.strip()
        # Find backtick references
        for m in re.finditer(r'`(\w+)', stripped):
            macro = m.group(1)
            if macro not in ('ifdef', 'ifndef', 'endif', 'elsif', 'else', 'define',
                            'undef', 'include', 'CLOG2', 'LOG2UP', 'UP', '__MIN',
                            'VX_CFG_XLEN', 'VX_CFG_NUM_THREADS', 'VX_CFG_NUM_WARPS',
                            'VX_CFG_NUM_TCU_LANES', 'VX_CFG_ISSUE_WIDTH',
                            'VX_CFG_NUM_TCU_BLOCKS', 'VX_MEM_LMEM_BASE_ADDR',
                            'VX_CFG_LMEM_LOG_SIZE', 'VX_CFG_LMEM_NUM_BANKS',
                            'FORCE_BUILTIN_ADDER', 'UNUSED_PARAM', 'UNUSEDWire',
                            'STATIC_ASSERT', 'TRACING_OFF', 'TRACE_ARRAY',
                            'UNUSED_VAR', 'UNUSED_SPARAM', 'UNUSED_PIN',
                            'SFORMATF', 'STRING', 'SCOPE_IO_DECL', 'SCOPE_IO_BIND',
                            'SCOPE_IO_UNUSED', 'SCOPE_IO_SWITCH', 'MAP_AOS_SOA'):
                # Check if the macro has a '.' in its argument (Yosys can't handle this)
                pos = m.start()
                rest = stripped[pos:]
                paren_match = re.search(r'`(\w+)\s*\(', rest)
                if paren_match:
                    # Find matching paren
                    depth = 0
                    start = rest.find('(')
                    for j in range(start, len(rest)):
                        if rest[j] == '(':
                            depth += 1
                        elif rest[j] == ')':
                            depth -= 1
                            if depth == 0:
                                arg = rest[start+1:j]
                                if '.' in arg:
                                    print(f"Line {i}: macro `{macro}(...)` has '.' in argument: {arg[:60]}")
                                break
