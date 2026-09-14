#!/usr/bin/env python3
"""
Fix: Preserve `define lines from the HEADER section in flatten_tcu.py.
The HEADER defines are needed for Surelog to resolve macros like CLOG2, VX_CFG_*.
"""
import re

# Read the flatten_tcu.py file
with open('syn/flatten_tcu.py', 'r') as f:
    content = f.read()

# Find the HEADER section and extract the defines
header_start = content.find('HEADER = """')
header_end = content.find('"""', header_start + 12)
header_section = content[header_start:header_end]

# Extract all `define lines from the HEADER
header_defines = []
for line in header_section.split('\n'):
    stripped = line.strip()
    if stripped.startswith('`define '):
        header_defines.append(stripped)

print(f"Found {len(header_defines)} defines in HEADER:")
for d in header_defines:
    print(f"  {d}")

# Modify strip_preprocessor_blocks to preserve HEADER defines
# The fix: add a parameter to pass HEADER defines, and keep them
old_function = '''def strip_preprocessor_blocks(content):
    """Strip preprocessor directives but KEEP their bodies.
    ifdef=keep, ifndef=skip, elsif/else=flip, define/undef/include=remove.
    """
    lines = content.split("\\n")
    result = []
    stack = []  # 'keep' or 'skip'

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Track preprocessor state but REMOVE all directive lines from output
        if stripped.startswith("`ifdef "):
            stack.append('keep')
            i += 1
            continue
        elif stripped.startswith("`ifndef "):
            stack.append('skip')
            i += 1
            continue
        elif stripped.startswith("`elsif ") or stripped.startswith("`else"):
            if stack:
                stack[-1] = 'skip' if stack[-1] == 'keep' else 'keep'
            i += 1
            continue
        elif stripped.startswith("`endif"):
            if stack:
                stack.pop()
            i += 1
            continue
        elif stripped.startswith("`define ") or stripped.startswith("`undef ") or stripped.startswith("`include "):
            i += 1
            continue
        elif stack and stack[-1] == 'skip':
            i += 1
            continue

        result.append(line)
        i += 1

    return "\\n".join(result)'''

new_function = '''def strip_preprocessor_blocks(content, preserve_defines=None):
    """Strip preprocessor directives but KEEP their bodies.
    ifdef=keep, ifndef=skip, elsif/else=flip, define/undef/include=remove.
    
    preserve_defines: list of `define lines to keep (from HEADER).
    """
    if preserve_defines is None:
        preserve_defines = []
    
    lines = content.split("\\n")
    result = []
    stack = []  # 'keep' or 'skip'

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Track preprocessor state but REMOVE all directive lines from output
        if stripped.startswith("`ifdef "):
            stack.append('keep')
            i += 1
            continue
        elif stripped.startswith("`ifndef "):
            stack.append('skip')
            i += 1
            continue
        elif stripped.startswith("`elsif ") or stripped.startswith("`else"):
            if stack:
                stack[-1] = 'skip' if stack[-1] == 'keep' else 'keep'
            i += 1
            continue
        elif stripped.startswith("`endif"):
            if stack:
                stack.pop()
            i += 1
            continue
        elif stripped.startswith("`define ") or stripped.startswith("`undef ") or stripped.startswith("`include "):
            # Keep HEADER defines
            if stripped in preserve_defines:
                result.append(line)
            i += 1
            continue
        elif stack and stack[-1] == 'skip':
            i += 1
            continue

        result.append(line)
        i += 1

    return "\\n".join(result)'''

# Replace the function
if old_function in content:
    content = content.replace(old_function, new_function)
    print("✓ Replaced strip_preprocessor_blocks function")
else:
    print("✗ Could not find the old function - checking if already modified...")
    # Check if the new function is already there
    if 'preserve_defines' in content:
        print("✓ Function already has preserve_defines parameter")
    else:
        print("✗ Need manual fix")

# Now find where strip_preprocessor_blocks is called in transform()
# and pass the preserve_defines parameter
old_call = 'content = strip_preprocessor_blocks(content)'
new_call = 'content = strip_preprocessor_blocks(content, preserve_defines=HEADER_DEFINES)'

if old_call in content:
    content = content.replace(old_call, new_call)
    print("✓ Updated strip_preprocessor_blocks call in transform()")

# Add HEADER_DEFINES constant near the top of the file (after HEADER)
# Find where to insert it
header_end_marker = '"""'
insert_pos = content.find(header_end_marker, content.find('HEADER = """') + 12) + 3

# Check if HEADER_DEFINES already exists
if 'HEADER_DEFINES' not in content:
    define_list = '\n'.join([f'    "{d}",' for d in header_defines])
    header_defines_code = f'''

# Extracted `define lines from HEADER (to preserve through preprocessing)
HEADER_DEFINES = [
{define_list}
]
'''
    content = content[:insert_pos] + header_defines_code + content[insert_pos:]
    print("✓ Added HEADER_DEFINES constant")

# Write the fixed file
with open('syn/flatten_tcu.py', 'w') as f:
    f.write(content)

print("\nDone! flatten_tcu.py updated to preserve HEADER defines.")
