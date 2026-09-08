#!/usr/bin/env python3
"""Remove leftover RUNTIME_ASSERT arguments from DXA source files."""
import re, os
os.chdir("/tmp/dxa_synth")

files_to_fix = ["VX_dxa_watchdog.sv", "VX_dxa_setup.sv", "VX_dxa_completion.sv"]

for fname in files_to_fix:
    with open(fname) as f:
        lines = f.readlines()
    
    new_lines = []
    skip_next = 0
    for i, line in enumerate(lines):
        if skip_next > 0:
            skip_next -= 1
            # Check if this line ends the macro arguments (has closing paren+semicolon or just closing paren)
            stripped = line.strip()
            if stripped.endswith('))') or stripped.endswith('))\n'):
                continue
            # Still inside multi-line argument
            continue
        
        # Check for leftover RUNTIME_ASSERT argument lines
        stripped = line.strip()
        if stripped.startswith('"') and ('%s' in stripped or '%t' in stripped or '%0d' in stripped or '%0h' in stripped):
            # This is a leftover printf-style format string from RUNTIME_ASSERT
            # Count parens to find end of multi-line args
            depth = 0
            for c in stripped:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
            if depth < 0 or '))' in stripped:
                # Single line, skip it
                continue
            else:
                # Multi-line, skip until closing
                skip_next = 1
                continue
        
        # Also check for lines like: ("DXA K-major requires rank ≤ 2, ...")
        if stripped.startswith('("') or stripped.startswith('('):
            # Could be a leftover from RUNTIME_ASSERT
            depth = 0
            for c in stripped:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
            if '))' in stripped or depth <= 0:
                continue
            else:
                skip_next = 1
                continue
        
        new_lines.append(line)
    
    with open(fname, 'w') as f:
        f.writelines(new_lines)
    
    removed = len(lines) - len(new_lines)
    print(f"  {fname}: removed {removed} lines")
