#!/usr/bin/env python3
"""Replace MAP_AOS_SOA macro calls with inline generate loops."""
import re, sys

path = sys.argv[1] if len(sys.argv) > 1 else '/home/ubuntu/grxgpu/hw/rtl/tcu/tfr/VX_tcu_fedp_tfr.sv'

# First restore original file
import subprocess
subprocess.run(['git', 'checkout', '--', path], cwd='/home/ubuntu/grxgpu')

with open(path) as f:
    content = f.read()

counter = [0]
def replace_macro(m):
    counter[0] += 1
    idx = counter[0]
    full = m.group(0)
    # Extract args manually to handle braces
    # `MAP_AOS_SOA(var, size, lhs, rhs)
    args_start = full.index('(') + 1
    # Find the matching close paren
    depth = 0
    args_end = args_start
    for i in range(args_start, len(full)):
        if full[i] == '(':
            depth += 1
        elif full[i] == ')':
            if depth == 0:
                args_end = i
                break
            depth -= 1
    args_str = full[args_start:args_end]
    
    # Split by comma, respecting braces
    args = []
    current = ''
    brace_depth = 0
    for ch in args_str:
        if ch in '({[':
            brace_depth += 1
            current += ch
        elif ch in ')}]':
            brace_depth -= 1
            current += ch
        elif ch == ',' and brace_depth == 0:
            args.append(current.strip())
            current = ''
        else:
            current += ch
    args.append(current.strip())
    
    if len(args) != 4:
        print("WARNING: expected 4 args, got %d: %s" % (len(args), args))
        return m.group(0)
    
    var, size, lhs, rhs = args
    ivar = '__i_%d' % idx
    label = 'g_map_aos_%d' % idx
    # Use word boundary replacement
    new_lhs = re.sub(r'\b' + re.escape(var) + r'\b', ivar, lhs)
    new_rhs = re.sub(r'\b' + re.escape(var) + r'\b', ivar, rhs)
    return ('for (genvar %s = 0; %s < (%s); %s++) begin : %s\n'
            '        assign %s = %s;\n'
            '    end' % (ivar, ivar, size, ivar, label, new_lhs, new_rhs))

content = re.sub(
    r'`MAP_AOS_SOA\([^)]*(?:\([^)]*\))*[^)]*\)',
    replace_macro,
    content
)

with open(path, 'w') as f:
    f.write(content)
print("Replaced %d MAP_AOS_SOA calls" % counter[0])
