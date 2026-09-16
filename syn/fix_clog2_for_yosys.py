#!/usr/bin/env python3
"""Replace CLOG2/LOG2UP macro calls with direct $clog2 for Yosys compatibility."""
import re

with open('/tmp/tcu_struct.sv') as f:
    content = f.read()

def replace_clog2(text):
    result = []
    i = 0
    while i < len(text):
        m = re.search(r'`(CLOG2|LOG2UP)\s*\(', text[i:])
        if not m:
            result.append(text[i:])
            break
        result.append(text[i:i+m.start()])
        start = i + m.end() - 1
        depth = 1
        j = start + 1
        while j < len(text) and depth > 0:
            if text[j] == '(':
                depth += 1
            elif text[j] == ')':
                depth -= 1
            j += 1
        arg = text[start+1:j-1]
        result.append(f'$clog2({arg})')
        i = j
    return ''.join(result)

content = replace_clog2(content)

# Replace the macro definitions to avoid re-expansion
content = content.replace('`define CLOG2(x) ($clog2(x))', '`define CLOG2(x) (x)')
content = content.replace('`define LOG2UP(x) ($clog2(x))', '`define LOG2UP(x) (x)')

with open('/tmp/tcu_ys.sv', 'w') as f:
    f.write(content)
print(f'Done: {content.count("$clog2")} $clog2 calls in output')
