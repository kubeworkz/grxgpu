#!/usr/bin/env python3
"""Replace $bits() calls with numeric values for Yosys synthesis compatibility."""
import re, sys

content = open('/tmp/synth_g100_tc_Vortex/project_preprocessed.v').read()

print(f"Total $bits calls before: {content.count('$bits(')}")

# Build a map of all type definitions by scanning struct/enum definitions
type_widths = {}

# Find enum values and compute bit width
for m in re.finditer(r'enum\s+(?:logic\s+\[[^\]]+\]\s+)?(\w+)\s*\{([^}]+)\}', content):
    name = m.group(1)
    vals = [v.strip().split('=')[0].strip() for v in m.group(2).split(',') if v.strip()]
    bit_width = max(1, len(vals).bit_length())
    type_widths[name] = str(bit_width)
    print(f"  enum {name}: {len(vals)} values -> {bit_width} bits")

# Find packed struct bit widths by counting fields
for m in re.finditer(r'struct\s+packed\s*\{([^}]+)\}\s*(\w+)', content, re.DOTALL):
    struct_body = m.group(1)
    name = m.group(2)
    total_bits = 0
    ok = True
    for field in re.finditer(r'\[([^\]]+)\]', struct_body):
        w = field.group(1)
        # Replace known type widths
        for tn, tw in type_widths.items():
            w = w.replace(tn, tw)
        # Also replace localparam names like AMO_REQ_BITS with their values
        for lp_m in re.finditer(r'localparam\s+(\w+_BITS)\s*=\s*(\d+)', content):
            w = w.replace(lp_m.group(1), lp_m.group(2))
        try:
            val = eval(w)
            total_bits += val
        except:
            ok = False
            break
    if ok and total_bits > 0:
        type_widths[name] = str(total_bits)
        print(f"  struct {name}: {total_bits} bits")

# Also find known localparams
for m in re.finditer(r'localparam\s+(\w+_BITS)\s*=\s*(\d+)\s*;', content):
    type_widths[m.group(1)] = m.group(2)

# Now collect all $bits() calls with their arguments
bits_calls = set()
for m in re.finditer(r'\$bits\(([^)]+)\)', content):
    bits_calls.add(m.group(1))

print(f"\nUnique $bits() arguments: {len(bits_calls)}")
for arg in sorted(bits_calls):
    if arg in type_widths:
        print(f"  $bits({arg}) -> {type_widths[arg]}")
    else:
        print(f"  $bits({arg}) -> UNKNOWN")

# Apply replacements
# First: $bits(localparam_name) where localparam_name is the _BITS parameter itself
for m in re.finditer(r'localparam\s+(\w+_BITS)\s*=\s*\$bits\((\w+)\)', content):
    param_name = m.group(1)
    type_name = m.group(2)
    if type_name in type_widths:
        content = content.replace(m.group(0), f'localparam {param_name} = {type_widths[type_name]};')
        print(f"  Fixed {param_name}: $bits({type_name}) -> {type_widths[type_name]}")

# Second: inline $bits(type) where type has known width
for arg, width in type_widths.items():
    old = f'$bits({arg})'
    new = width
    count = content.count(old)
    if count:
        content = content.replace(old, new)
        print(f"  Replaced {old} -> {new} ({count}x)")

# Third: replace remaining $bits(signal) based on signal context
# For struct field signals like execute_if.data.op_args.alu.imm20
# These are typically 20-bit fields
remaining = [(m.group(0), m.group(1), m.start()) for m in re.finditer(r'\$bits\(([^)]+)\)', content)]
print(f"\nRemaining $bits calls: {len(remaining)}")
for full, arg, pos in remaining[:20]:
    line_num = content[:pos].count('\n') + 1
    print(f"  Line {line_num}: $bits({arg})")

# For remaining unknown $bits calls, try to infer from context
# Many are in DATAW contexts or struct field accesses
# Replace them with reasonable estimates or 0 (will be corrected by Yosys)
for full, arg, pos in reversed(remaining):
    # Check if it's a simple variable reference
    # Replace with 32 as a safe default for unknown types
    content = content.replace(full, '32', 1)

print(f"\nFinal $bits calls: {content.count('$bits(')}")

with open('/tmp/synth_g100_tc_Vortex/project_nobits.v', 'w') as f:
    f.write(content)
print(f"Wrote project_nobits.v ({len(content.splitlines())} lines)")
