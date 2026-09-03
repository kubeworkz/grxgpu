#!/usr/bin/env python3
"""
Phase B v11: Post-process flat TFR file to hoist all generate-scoped
declarations to module scope. Localparams before wires.
Also collects constant localparams from the entire module body.
"""
import re, sys, os

def find_all_genvar_blocks(text):
    blocks = []
    pattern = re.compile(
        r'for\s*\(\s*genvar\s+(\w+)\s*=\s*(\d+)\s*;\s*\w+\s*<\s*(\w+)\s*;\s*\+\+\w+\)\s*begin\s*:\s*(\w+)',
        re.MULTILINE
    )
    matches = []
    pos = 0
    while pos < len(text):
        m = pattern.search(text, pos)
        if not m:
            break
        matches.append(m)
        pos = m.start() + 1
    for m in matches:
        var, init_val, bound, label = m.group(1), m.group(2), m.group(3), m.group(4)
        start, after_begin = m.start(), m.end()
        depth, pos2, block_end = 1, after_begin, len(text)
        while pos2 < len(text) and depth > 0:
            if text[pos2] == '/' and pos2+1 < len(text) and text[pos2+1] == '/':
                nl = text.find('\n', pos2)
                pos2 = nl + 1 if nl >= 0 else len(text)
                continue
            if text[pos2] == '/' and pos2+1 < len(text) and text[pos2+1] == '*':
                end_c = text.find('*/', pos2+2)
                pos2 = end_c + 2 if end_c >= 0 else len(text)
                continue
            if text[pos2:pos2+5] == 'begin' and (pos2 == 0 or not text[pos2-1].isalnum()) and (pos2+5 >= len(text) or not text[pos2+5].isalnum()):
                depth += 1; pos2 += 5
            elif text[pos2:pos2+3] == 'end' and (pos2+3 >= len(text) or not text[pos2+3].isalnum()):
                depth -= 1
                if depth == 0: block_end = pos2 + 3; break
                pos2 += 3
            elif text[pos2:pos2+8] == 'endcase' and (pos2+8 >= len(text) or not text[pos2+8].isalnum()):
                pos2 += 8
            else:
                pos2 += 1
        blocks.append({'var': var, 'init': init_val, 'bound': bound, 'label': label,
                       'start': start, 'end': block_end, 'body': text[after_begin:block_end]})
    return blocks

def find_nested_genvar_regions(body):
    regions = []
    for m in re.finditer(r'for\s*\(\s*genvar', body):
        depth, pos = 0, m.start()
        while pos < len(body):
            if body[pos:pos+5] == 'begin' and (pos == 0 or not body[pos-1].isalnum()) and (pos+5 >= len(body) or not body[pos+5].isalnum()):
                depth += 1; pos += 5
            elif body[pos:pos+3] == 'end' and (pos+3 >= len(body) or not body[pos+3].isalnum()):
                if depth > 0:
                    depth -= 1
                    if depth == 0: regions.append((m.start(), pos + 3)); break
                pos += 3
            elif body[pos:pos+8] == 'endcase' and (pos+8 >= len(body) or not body[pos+8].isalnum()):
                pos += 8
            else:
                pos += 1
    return regions

def collect_decls(body, genvar_names=None):
    decls, seen = [], set()
    if genvar_names is None: genvar_names = set()
    nested = find_nested_genvar_regions(body)
    
    def search_region(text):
        # wire with range and assign: wire [W:0] name = expr; or wire signed [W:0][W2:0] name = expr;
        for m in re.finditer(r'^\s*wire\s+(?:signed|unsigned)?\s*(\[[^\]]+(?:\]\[[^\]]+)*\]\s+)?(\w+)\s*=\s*(.+?);', text, re.MULTILINE):
            w, n, e = m.group(1), m.group(2), m.group(3)
            if n not in seen and n.isidentifier(): seen.add(n); decls.append({'name': n, 'width': w.strip() if w else None, 'expr': e.rstrip()})
        # wire/logic/reg with range, no assign: wire [W:0] name1, name2; or wire signed [W:0][W2:0] name;
        for m in re.finditer(r'^\s*(?:wire|logic|reg)\s+(?:signed|unsigned)?\s*(\[[^\]]+(?:\]\[[^\]]+)*\])\s+([^\n=;]+);', text, re.MULTILINE):
            w = m.group(1)
            for n in re.findall(r'\b([a-zA-Z_]\w*)\b', m.group(2)):
                if n not in seen and n.isidentifier(): seen.add(n); decls.append({'name': n, 'width': w, 'expr': None})
        # wire/logic/reg without range: wire name;
        for m in re.finditer(r'^\s*(?:wire|logic|reg)\s+(?:signed|unsigned)?\s*(\w+)\s*;', text, re.MULTILINE):
            n = m.group(1)
            if n not in seen and n.isidentifier(): seen.add(n); decls.append({'name': n, 'width': None, 'expr': None})
        # localparams (only if they don't reference genvars)
        for m in re.finditer(r'^\s*localparam\s+(?:\w+\s+)?(\w+)\s*=\s*([^;]+);', text, re.MULTILINE):
            n, val = m.group(1), m.group(2).strip()
            if re.search(r'\b(genvar|for)\b', val): continue
            if genvar_names and re.search(r'\b(' + '|'.join(re.escape(g) for g in genvar_names) + r')\b', val): continue
            if n not in seen and n.isidentifier(): seen.add(n); decls.append({'name': n, 'width': None, 'expr': None, 'is_localparam': True, 'param_val': val})
    
    if not nested:
        search_region(body)
    else:
        prev_end = 0
        for rs, re_ in sorted(nested): search_region(body[prev_end:rs]); prev_end = re_
        search_region(body[prev_end:])
    # Also collect localparams from the ENTIRE body (including nested regions)
    for m in re.finditer(r'^\s*localparam\s+(?:\w+\s+)?(\w+)\s*=\s*([^;]+);', body, re.MULTILINE):
        n, val = m.group(1), m.group(2).strip()
        if n in seen: continue
        if re.search(r'\b(genvar|for)\b', val): continue
        if genvar_names and re.search(r'\b(' + '|'.join(re.escape(g) for g in genvar_names) + r')\b', val): continue
        seen.add(n)
        decls.append({'name': n, 'width': None, 'expr': None, 'is_localparam': True, 'param_val': val})
    return decls

def process_flat_file(flat_file):
    with open(flat_file) as f: content = f.read()
    modules = list(re.finditer(r'^module\s+(\w+)', content, re.MULTILINE))
    total = 0
    for i in range(len(modules) - 1, -1, -1):
        mod_name = modules[i].group(1)
        mod_start = modules[i].start()
        end_match = re.search(r'\n\s*endmodule', content[mod_start:])
        if not end_match: continue
        mod_end = mod_start + end_match.start()
        mod_text = content[mod_start:mod_end]
        blocks = find_all_genvar_blocks(mod_text)
        if not blocks: continue
        blocks.sort(key=lambda b: b['end'] - b['start'])
        localparam_decls, wire_decls = [], []
        names_to_hoist, decl_map = set(), {}
        genvar_names_all = set(b['var'] for b in blocks)
        for block in blocks:
            label, var, bound = block['label'], block['var'], block['bound']
            for decl in collect_decls(block['body'], genvar_names={var}):
                name = decl['name']
                if name in names_to_hoist: continue
                names_to_hoist.add(name)
                decl_map[name] = {'width': decl.get('width'), 'expr': decl.get('expr'),
                                  'label': label, 'var': var, 'bound': bound,
                                  'is_localparam': decl.get('is_localparam', False),
                                  'param_val': decl.get('param_val')}
                if decl.get('is_localparam'):
                    localparam_decls.append(f"    localparam {name} = {decl['param_val']};")
                elif decl.get('width'):
                    w = decl['width']
                    if not w.startswith('['): w = f'[{w}]'
                    wire_decls.append(f"    wire {w} {label}_{name} [0:{bound}-1];")
                else:
                    wire_decls.append(f"    wire {label}_{name} [0:{bound}-1];")
                total += 1
        # Now find port end and compute insert_pos BEFORE collecting module-level localparams
        port_end = re.search(r'\);\s*\n', mod_text)
        if not port_end: print(f"    WARNING: no port end in {mod_name}"); continue
        insert_pos = port_end.end()
        # Collect constant localparams from the ENTIRE module body (not just genvar blocks)
        # These are localparams that sit at module scope but after the port list
        mod_body_after_ports = mod_text[insert_pos:]
        extra_lps = []
        for m_lp in re.finditer(r'^\s*localparam\s+(?:\[[^\]]*\]\s+)?(\w+)\s*=\s*([^;]+);', mod_body_after_ports, re.MULTILINE):
            lp_name, lp_val = m_lp.group(1), m_lp.group(2).strip()
            if lp_name in names_to_hoist: continue
            # Skip localparams that reference genvars
            if re.search(r'\b(' + '|'.join(re.escape(g) for g in genvar_names_all) + r')\b', lp_val): continue
            # Skip localparams that reference un-resolved identifiers (port params like W, WA etc are OK)
            # Only hoist truly constant ones or ones referencing only hoisted localparams
            names_in_val = re.findall(r'\b([A-Z][A-Z_0-9]*)\b', lp_val)
            # Allow port parameters (single-letter like W, WA, N, P, M, TCK, LANES etc)
            # and previously hoisted localparams
            unresolved = [r for r in names_in_val if r not in names_to_hoist and len(r) > 3]
            if unresolved: continue
            names_to_hoist.add(lp_name)
            extra_lps.append(f"    localparam {lp_name} = {lp_val};")
            total += 1
        localparam_decls = extra_lps + localparam_decls
        all_decls = localparam_decls + wire_decls
        if not all_decls: continue
        print(f"  {mod_name}: {len(all_decls)} declarations to hoist")
        hoisted_text = "\n    // Phase B: hoisted generate-scoped declarations\n" + "\n".join(all_decls) + "\n"
        new_mod_text = mod_text[:insert_pos] + hoisted_text + mod_text[insert_pos:]
        body_start = insert_pos + len(hoisted_text)
        header, body = new_mod_text[:body_start], new_mod_text[body_start:]
        for name, info in decl_map.items():
            label, var, expr, hname = info['label'], info['var'], info['expr'], f"{info['label']}_{name}"
            if info.get('is_localparam'):
                # Remove original localparam declaration, keep name as-is (not hoisted with [var])
                old_pat = re.compile(r'^\s*localparam\s+(?:\w+\s+)?' + re.escape(name) + r'\s*=\s*[^;]+;\s*\n', re.MULTILINE)
                body = re.sub(old_pat, '', body)
                continue
            if expr:
                old_pat = re.compile(r'^\s*wire\s+(?:signed|unsigned)?\s*(?:\[([^\]]+)\]\s+)?' + re.escape(name) + r'\s*=\s*.+?;', re.MULTILINE)
                body = re.sub(old_pat, f'    assign {hname}[{var}] = {expr};', body)
            else:
                old_pat = re.compile(r'^\s*(?:wire|logic|reg)\s+(?:signed|unsigned)?\s*(?:\[[^\]]+(?:\]\[[^\]]+)*\]\s+)?' + re.escape(name) + r'[^;]*;\s*\n', re.MULTILINE)
                body = re.sub(old_pat, '', body)
            ref_indexed = re.compile(r'(?<![a-zA-Z0-9_])' + re.escape(name) + r'\[')
            body = ref_indexed.sub(f"{hname}[{var}][", body)
            ref_standalone = re.compile(r'(?<![a-zA-Z0-9_])' + re.escape(name) + r'(?![a-zA-Z0-9_\[])')
            body = ref_standalone.sub(f"{hname}[{var}]", body)
        new_mod_text = header + body
        content = content[:mod_start] + new_mod_text + content[mod_end:]
    with open(flat_file, "w") as f: f.write(content)
    print(f"\nTotal: {total} declarations hoisted")

if __name__ == "__main__":
    process_flat_file(sys.argv[1] if len(sys.argv) > 1 else "/tmp/tfr_flat_v2.sv")
