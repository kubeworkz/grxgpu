#!/usr/bin/env python3
"""
expand_interfaces.py FINAL — Put expanded wires in module body, not port list.
This avoids all comma/semicolon issues.
"""
import re, sys

IF_SIGNALS = {
    'VX_mem_bus_if': [
        ('req_valid', 'output', 'logic'),
        ('req_data', 'output', '[63:0]'),
        ('req_ready', 'input', 'logic'),
        ('rsp_valid', 'input', 'logic'),
        ('rsp_data', 'input', '[63:0]'),
        ('rsp_ready', 'output', 'logic'),
    ],
    'VX_execute_if': [
        ('valid', 'input', 'logic'),
        ('data', 'input', '[511:0]'),
        ('ready', 'output', 'logic'),
    ],
    'VX_result_if': [
        ('valid', 'output', 'logic'),
        ('data', 'output', '[511:0]'),
        ('ready', 'input', 'logic'),
    ],
    'VX_dispatch_if': [
        ('valid', 'input', 'logic'),
        ('data', 'input', '[511:0]'),
        ('ready', 'output', 'logic'),
    ],
    'VX_commit_if': [
        ('valid', 'output', 'logic'),
        ('data', 'output', '[511:0]'),
        ('ready', 'input', 'logic'),
    ],
    'VX_lsu_sched_if': [
        ('req_valid', 'output', 'logic'),
        ('req_data', 'output', '[255:0]'),
        ('req_ready', 'input', 'logic'),
        ('rsp_valid', 'input', 'logic'),
        ('rsp_data', 'input', '[255:0]'),
        ('rsp_ready', 'output', 'logic'),
    ],
}

IF_PATTERN = re.compile(
    r'(VX_(?:mem_bus_if|execute_if|result_if|dispatch_if|commit_if|lsu_sched_if))'
    r'\s*\.\s*\w+\s+(\w+)(?:\s*\[([^\]]+)\])?\s*,?\s*$'
)

def expand(content):
    lines = content.split('\n')
    expanded = {}
    module_expanded = {}  # port_list_end_idx -> {inst_name: if_type}
    to_remove = set()
    current_module_ifs = {}

    for i, line in enumerate(lines):
        stripped = line.strip()
        m = IF_PATTERN.match(stripped)
        if m:
            current_module_ifs[m.group(2)] = m.group(1)
            expanded[m.group(2)] = m.group(1)
            to_remove.add(i)
            continue
        if stripped.startswith(');') and current_module_ifs:
            module_expanded[i] = current_module_ifs.copy()
            current_module_ifs = {}

    # Build output: remove interface lines, add wires AFTER );
    result = []
    for i, line in enumerate(lines):
        if i in to_remove:
            continue  # remove interface port line
        result.append(line)
        if i in module_expanded:
            # Insert expanded wires after );
            indent = '    '
            for ename, etype in module_expanded[i].items():
                for sig_name, direction, width in IF_SIGNALS[etype]:
                    result.append(f'{indent}{direction} {width} {ename}__{sig_name};')

    content = '\n'.join(result)

    # Replace member accesses
    for inst_name in sorted(expanded.keys(), key=len, reverse=True):
        ename = re.escape(inst_name)
        content = re.sub(rf'\b{ename}\.(\w+)', rf'{inst_name}__\1', content)
        content = re.sub(rf'\b{ename}\[([^\]]+)\]\.(\w+)',
                         rf'{inst_name}__\2[\1]', content)

    return content, expanded

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        content = f.read()
    content, expanded = expand(content)
    with open(sys.argv[2], 'w') as f:
        f.write(content)
    print(f"Expanded {len(expanded)} interfaces:")
    for n, t in sorted(expanded.items()):
        print(f"  {n}: {t}")
