#!/usr/bin/env python3
"""Strip entire RUNTIME_ASSERT blocks from DXA source files."""
import os, re
os.chdir("/tmp/dxa_synth")

files_to_fix = ["VX_dxa_watchdog.sv", "VX_dxa_setup.sv", "VX_dxa_completion.sv"]

for fname in files_to_fix:
    with open(fname) as f:
        content = f.read()
    
    # Pattern: RUNTIME_ASSERT followed by arguments that may span multiple lines
    # The macro is: `RUNTIME_ASSERT(cond, (fmt, args...))
    # In the source it appears as:
    #   `RUNTIME_ASSERT(cond, (
    #       "format string",
    #       arg1, arg2))
    # We need to match from `RUNTIME_ASSERT to the closing ))
    
    # Find all RUNTIME_ASSERT blocks
    pattern = r'`RUNTIME_ASSERT\([^)]*\([^)]*\)[^)]*\)'
    
    # Use a more robust approach: find RUNTIME_ASSERT and delete until balanced parens
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '`RUNTIME_ASSERT' in line:
            # Count parens to find end of the block
            depth = 0
            j = i
            found_end = False
            while j < len(lines):
                for c in lines[j]:
                    if c == '(':
                        depth += 1
                    elif c == ')':
                        depth -= 1
                if depth <= 0 and j > i:
                    found_end = True
                    break
                if depth <= 0 and j == i and lines[j].count(')') >= lines[j].count('('):
                    # Single line
                    found_end = True
                    break
                j += 1
            # Skip lines i through j (inclusive)
            i = j + 1
            continue
        
        # Also strip RUNTIME_ASSERT that was already partially deleted (leftover args)
        stripped = line.strip()
        if stripped.startswith('"') and ('%s' in stripped or '%t' in stripped or '%0d' in stripped or '%0h' in stripped):
            # This is a leftover format string from a deleted RUNTIME_ASSERT
            # Skip until closing ))
            j = i
            depth = 0
            while j < len(lines):
                for c in lines[j]:
                    if c == '(':
                        depth += 1
                    elif c == ')':
                        depth -= 1
                if '))' in lines[j] or (depth <= 0 and j > i):
                    break
                j += 1
            i = j + 1
            continue
        
        new_lines.append(line)
        i += 1
    
    removed = len(lines) - len(new_lines)
    with open(fname, 'w') as f:
        f.write('\n'.join(new_lines))
    print(f"  {fname}: removed {removed} lines")
