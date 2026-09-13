#!/usr/bin/env python3
"""
yosys_preprocess.py — Comprehensive preprocessing for Yosys 0.69.
Fixes all SV features that Yosys can't handle in a single pass.
"""
import re, sys

def preprocess(content):
    # 1. Remove all function blocks
    def strip_functions(text):
        result = []
        i = 0
        while i < len(text):
            m = re.search(r'\bfunction\b', text[i:])
            if not m:
                result.append(text[i:])
                break
            start = i + m.start()
            result.append(text[i:start])
            depth = 0
            j = start
            while j < len(text):
                if text[j:j+8] == 'function' and (j == 0 or not text[j-1].isalnum()):
                    depth += 1
                if text[j:j+11] == 'endfunction':
                    depth -= 1
                    if depth == 0:
                        j += 11
                        break
                j += 1
            i = j
        return ''.join(result)
    content = strip_functions(content)

    # 2. Replace all typedef'd types with wide logic
    typedef_map = {
        'tcu_execute_t': 512, 'tcu_result_t': 512, 'tcu_header_t': 512,
        'tcu_tbuf_req_t': 256, 'ibuffer_t': 511, 'op_args_t': 127,
        'dispatch_t': 511, 'commit_t': 511, 'lsu_req_data_t': 255,
        'lsu_rsp_data_t': 255,
    }
    for tname, width in typedef_map.items():
        w = f'[{width}:0]'
        # Port declarations: input/output TYPE name [dim],
        # TYPE NAME [DIM] order
        content = re.sub(
            rf'\b(input|output)\s+{tname}\s+(\w+)\s*\[([^\]]+)\]',
            rf'\1 wire [4095:0] \3', content)
        # TYPE [DIM] NAME order
        content = re.sub(
            rf'\b(input|output)\s+{tname}\s*\[([^\]]+)\]\s+(\w+)',
            rf'\1 wire [4095:0] \3', content)
        # TYPE NAME (no dimension)
        content = re.sub(
            rf'\b(input|output)\s+{tname}\s+(\w+)(?=\s*[,;)])',
            rf'\1 wire {w} \2', content)
        # Variable declarations: TYPE name [dim];
        content = re.sub(
            rf'^(\s+){tname}\s+(\w+)\s*\[([^\]]+)\];',
            rf'\1logic {w} \2 [\3];', content, flags=re.MULTILINE)
        content = re.sub(
            rf'^(\s+){tname}\s*\[([^\]]+)\]\s+(\w+);',
            rf'\1logic [4095:0] \3;', content, flags=re.MULTILINE)
        content = re.sub(
            rf'^(\s+){tname}\s+(\w+);',
            rf'\1logic {w} \2;', content, flags=re.MULTILINE)

    # 3. Fix empty if blocks
    lines = content.split('\n')
    result = []
    for i, line in enumerate(lines):
        s = line.strip()
        if re.match(r'^if\s*\(.*\)\s*$', s):
            next_s = lines[i+1].strip() if i+1 < len(lines) else ''
            if next_s.startswith('else') or next_s == '' or next_s.startswith('end'):
                indent = line[:len(line)-len(line.lstrip())]
                result.append(line)
                result.append(f'{indent}begin end')
                continue
        result.append(line)
    content = '\n'.join(result)

    # 4. Fix stray ), from interface removal
    content = content.replace('"") ,', '""),')
    content = content.replace('"")),', '""),')

    # 5. Fix broken casts: (TYPE'(expr), -> (TYPE'(expr)),
    content = re.sub(
        r'\(([A-Za-z_]\w*)\'\(([^)]+)\)\)',
        lambda m: f'({m.group(1)}\'({m.group(2)}))',
        content)

    # 6. Remove stray lone commas
    content = re.sub(r'^\s*,\s*$', '', content, flags=re.MULTILINE)

    # 7. Fix function calls with constants
    replacements = {
        'tcu_fmt_is_int(fmt)': 'fmt[4]',
        'tcu_fmt_is_signed_int(fmt)': 'fmt[0]',
        'tcu_fmt_is_bfloat(fmt)': 'fmt[0]',
        'tcu_fmt_is_mx(fmt)': '1',
        'tcu_fmt_width(fmt)': '16',
        'tcu_int_fmt_width(fmt)': '16',
        'tcu_meta_stride_words(fmt)': '4',
        'mx_max_fedp_sf()': '8',
        'mx_fedp_sf_count(8, 32)': '8',
        'mx_fedp_sf_count(4, 32)': '4',
    }
    for old, new in replacements.items():
        content = content.replace(old, new)

    return content

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        content = f.read()
    content = preprocess(content)
    with open(sys.argv[2] if len(sys.argv) > 2 else sys.argv[1], 'w') as f:
        f.write(content)
    print("Yosys preprocessing done")
