#!/usr/bin/env python3
"""Post-process TCU flat file to fix orphaned syntax from ifdef stripping."""
import re, sys

def fix_flat(path):
    with open(path) as f:
        content = f.read()

    lines = content.split('\n')
    cleaned = []

    # Track multi-line $display/write/TRACE calls
    in_display = False
    for l in lines:
        s = l.strip()

        # Handle multi-line $display/write/TRACE
        if in_display:
            if ');' in s or s.endswith(';'):
                in_display = False
            continue

        # Skip stray ]) from ifdef stripping
        if s == '])':
            continue

        # Strip TRACE macros (always single-line)
        if '`TRACE' in s:
            continue
        # Skip $display/write lines and their arguments
        if '$display' in s or '$write' in s:
            if not (s.endswith(';') or ');' in s):
                in_display = True
            continue

        # Skip orphaned $display arguments
        if s.startswith('$time,') or s.startswith('INSTANCE_ID,'):
            continue

        cleaned.append(l)

    content = '\n'.join(cleaned)

    # Strip import statements
    content = re.sub(r'import\s+VX_gpu_pkg::\*\s*,\s*VX_tcu_pkg::\*\s*;', '', content)
    content = re.sub(r'import\s+VX_tcu_pkg::\*\s*;', '', content)
    content = re.sub(r'import\s+VX_gpu_pkg::\*\s*;', '', content)

    # Resolve VX_gpu_pkg:: constants
    gpu_consts = {
        'TCU_MAX_INPUTS': '16', 'NUM_THREADS': '4',
        'VX_CFG_ISSUE_WIDTH': '1', 'VX_CFG_LMEM_LOG_SIZE': '14',
        'VX_CFG_NUM_THREADS': '4', 'VX_CFG_NUM_WARPS': '4',
        'VX_MEM_LMEM_BASE_ADDR': '0',
    }
    for const, val in gpu_consts.items():
        content = content.replace('VX_gpu_pkg::' + const, val)

    # Replace UP(x) macro: max(x, 1)
    content = re.sub(r'`UP\(([^)]+)\)', r'((\1) > 0 ? (\1) : 1)', content)

    # Replace LOG2UP(x) with $clog2(x)
    content = re.sub(r'`LOG2UP\(([^)]+)\)', r'$clog2(\1)', content)

    # Replace $bits(x) with 32
    content = re.sub(r'\$bits\(([^)]+)\)', '32', content)

    # Convert automatic int/reg/wire to plain wire
    content = re.sub(r'\bautomatic\s+int\b', 'wire [31:0]', content)
    content = re.sub(r'\bautomatic\s+reg\b', 'reg', content)
    content = re.sub(r'\bautomatic\s+wire\b', 'wire', content)

    # Convert int'(x) casts to plain expression
    content = re.sub(r"int'\(([^)]+)\)", r'(\1)', content)

    # Convert typedef enums to localparams + wire
    def convert_enum(m):
        enum_body = m.group(1)
        type_name = m.group(2)
        pairs = re.findall(r'(\w+)\s*=\s*([^,}]+)', enum_body)
        localparams = []
        for vname, vval in pairs:
            localparams.append('localparam %s = %s;' % (vname, vval.strip()))
        return '\n'.join(localparams) + '\n    wire [0:0] %s;' % type_name
    content = re.sub(r'typedef\s+enum\s+(?:wire|logic\s*(?:\[[^\]]+\])?)\s*\{([^}]+)\}\s*(\w+)\s*;', convert_enum, content)

    # Convert type_name var_name; to wire [0:0] var_name; for enum types
    enum_types = re.findall(r'localparam \w+ = [^;]+;.*?wire \[0:0\] (\w+);', content, re.DOTALL)
    for tn in enum_types:
        content = re.sub(r'\b' + tn + r'\s+(\w+)\s*;', r'wire [0:0] \1;', content)

    # Strip UNUSED_* macros
    content = re.sub(r'`UNUSED_\w+\s*\([^)]*\)\s*;?', '', content)

    # Strip string parameters
    content = re.sub(r'parameter\s+`STRING\s+\w+\s*=\s*"[^"]*"\s*,?\s*', '', content)
    content = re.sub(r'parameter\s+`STRING\s+\w+\s*=\s*"[^"]*"\s*\)', ')', content)

    # Strip `include directives
    content = re.sub(r'`include\s+"[^"]*"', '', content)

    # Clean up empty if blocks left by stripping
    content = re.sub(r'if\s*\([^)]*\)\s*\n\s*end\n', '', content)

    with open(path, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    fix_flat(sys.argv[1] if len(sys.argv) > 1 else '/tmp/tcu_flat.sv')
