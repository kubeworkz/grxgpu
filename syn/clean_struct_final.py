#!/usr/bin/env python3
"""Clean orphaned ifdef fragments from the expanded struct file."""
import re, sys

def clean(content):
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip orphaned port connections (.sf_a, .sf_b) that appear outside any module instance
        # These are lines like "            .sf_a  (sf_a_r)," that follow a closing ");"
        if stripped.startswith('.sf_a') or stripped.startswith('.sf_b'):
            # Check if previous non-empty line ends with ");" — if so, this is orphaned
            prev_idx = len(result) - 1
            while prev_idx >= 0 and not result[prev_idx].strip():
                prev_idx -= 1
            if prev_idx >= 0 and result[prev_idx].strip().endswith(');'):
                i += 1
                continue

        # Skip duplicate VX_tcu_fedp_* module instantiations
        # If we see a module instantiation that follows another module instantiation
        # without a closing endmodule, it's an orphaned duplicate
        if re.match(r'\s*VX_tcu_fedp_\w+\s+#\(', stripped):
            # Check if previous non-empty line also looks like an instance body
            prev_idx = len(result) - 1
            while prev_idx >= 0 and not result[prev_idx].strip():
                prev_idx -= 1
            if prev_idx >= 0:
                prev_stripped = result[prev_idx].strip()
                # If previous line is ");" followed by orphaned ports, skip this duplicate
                if prev_stripped.endswith(');'):
                    # Check if there's a module instantiation before this one that hasn't been closed
                    # by looking for the pattern: module instance -> ); -> .port -> module instance
                    # This means the second instance is an orphaned duplicate
                    found_prev_instance = False
                    for j in range(len(result) - 1, max(0, len(result) - 5), -1):
                        if re.match(r'\s*\.\w+\s*\(', result[j].strip()):
                            found_prev_instance = True
                            break
                        if result[j].strip().startswith('VX_tcu_fedp_'):
                            break
                    if found_prev_instance:
                        i += 1
                        continue

        # Skip orphaned ternary fragments (lines starting with "is_wgmma ?" that are standalone)
        if stripped.startswith('is_wgmma ?') and stripped.endswith(':'):
            # Check if this is a standalone orphaned line
            prev_idx = len(result) - 1
            while prev_idx >= 0 and not result[prev_idx].strip():
                prev_idx -= 1
            if prev_idx >= 0:
                prev_stripped = result[prev_idx].strip()
                if prev_stripped.endswith(';') or prev_stripped.endswith('end'):
                    i += 1
                    continue

        result.append(line)
        i += 1

    return '\n'.join(result)


if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        content = f.read()
    cleaned = clean(content)
    with open(sys.argv[2], 'w') as f:
        f.write(cleaned)
    print(f"Cleaned: {sys.argv[1]} -> {sys.argv[2]}")
    print(f"  Removed {content.count(chr(10)) - cleaned.count(chr(10))} orphaned lines")
