#!/usr/bin/env python3
"""
preprocess_for_synth.py — Comprehensive TCU flattening + preprocessing pipeline.

Usage:
    python3 preprocess_for_synth.py <input.sv> <output.sv>
"""
import re
import sys

def fix_all_casts(text):
    def is_sized_literal(s):
        return bool(re.match(r'^[bhod][0-9a-fA-F_xX]+$', s))
    result = []
    i = 0
    while i < len(text):
        m = re.match(r"([A-Za-z_]\w*|\d+)'", text[i:])
        if m:
            rest_start = i + len(m.group(0))
            if rest_start < len(text) and text[rest_start] == '(':
                depth = 1
                j = rest_start + 1
                while j < len(text) and depth > 0:
                    if text[j] == '(': depth += 1
                    elif text[j] == ')': depth -= 1
                    j += 1
                if depth == 0:
                    inner = text[rest_start + 1 : j - 1]
                    result.append(f'({inner})')
                    i = j
                    continue
            elif rest_start < len(text):
                m3 = re.match(r'[A-Za-z_]\w*|\d+', text[rest_start:])
                if m3:
                    word = m3.group(0)
                    if not is_sized_literal(word):
                        result.append(word)
                        i = rest_start + len(word)
                        continue
        result.append(text[i])
        i += 1
    return ''.join(result)

def fix_sized_literals(text):
    text = re.sub(r"(?<!')(?<![a-zA-Z_0-9])b([01xX])(?![a-zA-Z_0-9])", "1'b\\1", text)
    text = re.sub(r"(?<!')(?<![a-zA-Z_0-9])d(\d+)(?![a-zA-Z_0-9])", "1'd\\1", text)
    return text

def fix_stray_commas(text):
    lines = text.split('\n')
    result = []
    for line in lines:
        if line.strip() == ',':
            continue
        result.append(line)
    text = '\n'.join(result)
    text = re.sub(r'\n\s*,\s*\n', '\n', text)
    text = re.sub(r',(\s*\);)', r'\1', text)
    return text

def fix_empty_portlists(text):
    text = re.sub(r',\n\s*\n(\s*\);)', r'\n\1', text)
    return text

def fix_hash_parens(text):
    lines = text.split('\n')
    result = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.endswith(')') and not stripped.endswith('),'):
            if stripped.startswith('.') or '=' in stripped:
                if i + 1 < len(lines):
                    next_stripped = lines[i+1].strip()
                    if re.match(r'^\w+\s*\(', next_stripped) and not next_stripped.startswith('.'):
                        result.append(line + ')')
                        continue
        result.append(line)
    return '\n'.join(result)

def fix_empty_ifs(text):
    lines = text.split('\n')
    result = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^\s*if\s*\(', stripped) and not stripped.endswith('begin'):
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines) and lines[j].strip() in ('end', 'end else', 'end else begin'):
                result.append(line + ' begin end')
                continue
        result.append(line)
    return '\n'.join(result)

def relocate_expanded_wires(text):
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped == ');':
            expanded = []
            j = i + 1
            while j < len(lines):
                ns = lines[j].strip()
                if re.match(r'^(output|input)\s+', ns) and '__' in ns and ns.endswith(';'):
                    expanded.append(lines[j])
                    j += 1
                elif ns == '' or ns.startswith('//'):
                    j += 1
                else:
                    break
            if expanded:
                if result:
                    prev = result[-1].rstrip()
                    if not prev.endswith(',') and not prev.endswith('('):
                        result[-1] = prev + ','
                for k, ew in enumerate(expanded):
                    ew_fixed = ew.rstrip().rstrip(';')
                    if k < len(expanded) - 1:
                        ew_fixed += ','
                    result.append('    ' + ew_fixed.strip())
                i = j
                result.append('    );')
                continue
        result.append(line)
        i += 1
    return '\n'.join(result)

def preprocess(input_sv, output_sv):
    with open(input_sv) as f:
        text = f.read()
    
    text = '`define MAX(a,b) ((a) > (b) ? (a) : (b))\n' + text
    text = fix_all_casts(text)
    # Direct fix for any remaining casts
    text = re.sub(r"int'\(", '(', text)
    text = fix_sized_literals(text)
    text = re.sub(r'function\s+automatic\s+\[[^\]]*\]\s+\w+\s*\([^)]*\)[^;]*;.*?endfunction', '', text, flags=re.DOTALL)
    text = fix_hash_parens(text)
    text = fix_stray_commas(text)
    text = fix_empty_portlists(text)
    text = fix_empty_ifs(text)
    text = text.replace('(""))', '("")')
    text = re.sub(r'`(?!define|ifdef|endif|else|include|undef|ifndef|pragma)\(', '(', text)
    BT = chr(96)
    text = text.replace(BT + '(', '(')
    text = relocate_expanded_wires(text)
    
    with open(output_sv, 'w') as f:
        f.write(text)
    
    print(f"  Written {len(text)} bytes, {text.count(chr(10))+1} lines to {output_sv}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: preprocess_for_synth.py <input.sv> <output.sv>")
        sys.exit(1)
    preprocess(sys.argv[1], sys.argv[2])
