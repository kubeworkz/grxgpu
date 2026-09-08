#!/usr/bin/env python3
"""Replace SV part-select (+:) operators with explicit bit slicing."""
import re, os

os.chdir("/tmp/dxa_synth")

files_to_fix = ["VX_dxa_setup.sv", "VX_dxa_smem_wr.sv"]

for fname in files_to_fix:
    with open(fname) as f:
        content = f.read()
    
    original = content
    
    # Match: signal[complex_base +: width] or signal[complex_base -: width]
    # The base can contain +, -, (, ), variables, numbers
    # The width is typically a simple identifier or number
    # Pattern: word_or_dotted [ ... +: word ] or word_or_dotted [ ... -: word ]
    
    def replace_part_select(match):
        full = match.group(0)
        signal = match.group(1)
        base_part = match.group(2).strip()
        width_part = match.group(3).strip()
        op = match.group(4)
        
        if op == '+':
            # base +: width  →  [base+width-1:base]
            return f"{signal}[({base_part})+({width_part})-1:({base_part})]"
        else:
            # base -: width  →  [base-width+1:base]
            return f"{signal}[({base_part})-({width_part})+1:({base_part})]"
    
    # Use a more robust approach: find [ then scan for +: or -: then ]
    # This handles nested brackets in base expressions
    result = []
    i = 0
    while i < len(content):
        # Look for signal[... +: ...] or signal[... -: ...]
        # Find a word/dotted-identifier followed by [
        m = re.match(r'(\w+(?:\.\w+)*)\[', content[i:])
        if m:
            signal = m.group(1)
            bracket_start = i + m.end()
            # Scan for matching ] accounting for nested brackets
            depth = 1
            j = bracket_start
            found_plus_colon = False
            found_minus_colon = False
            colon_pos = -1
            while j < len(content) and depth > 0:
                if content[j] == '[':
                    depth += 1
                elif content[j] == ']':
                    depth -= 1
                elif depth == 1:
                    if content[j:j+2] == '+:':
                        found_plus_colon = True
                        colon_pos = j
                        j += 1  # skip :
                        break
                    elif content[j:j+2] == '-:':
                        found_minus_colon = True
                        colon_pos = j
                        j += 1  # skip :
                        break
                j += 1
            
            if (found_plus_colon or found_minus_colon) and j < len(content):
                # Find the closing ]
                while j < len(content) and content[j] != ']':
                    j += 1
                if j < len(content):
                    base = content[bracket_start:colon_pos]
                    width = content[colon_pos+2:j]
                    op = '+' if found_plus_colon else '-'
                    
                    if op == '+':
                        replacement = f"{signal}[({base.strip()})+({width.strip()})-1:({base.strip()})]"
                    else:
                        replacement = f"{signal}[({base.strip()})-({width.strip()})+1:({base.strip()})]"
                    
                    result.append(replacement)
                    i = j + 1
                    continue
        
        result.append(content[i])
        i += 1
    
    content = ''.join(result)
    
    if content != original:
        with open(fname, 'w') as f:
            f.write(content)
        count = original.count('+:') + original.count('-:')
        print(f"  {fname}: replaced {count} part-select operators")
    else:
        print(f"  {fname}: no changes needed")
