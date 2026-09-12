#!/usr/bin/env python3
"""
expand_interfaces.py v3 — Post-process flat TCU SV file.

Strategy:
- Replace SV interface port declarations with flat wire declarations
- Replace ifname.signal with ifname__signal
- Replace ifname.data.field with ifname__data__field (flatten nested struct)
- Replace ifname.data.header.field with ifname__data__header__field
- Replace .ifname(ifname) instantiation connections with individual port wiring

The data signals are declared as wide logic vectors. Yosys will
optimize away unused bits.
"""
import re, sys


def expand_interfaces(content):
    lines = content.split('\n')
    result = []
    expanded = {}  # inst_name → if_type

    for line in lines:
        stripped = line.strip()
        indent = line[:len(line) - len(line.lstrip())]

        # Match: VX_<type>.<modport> <inst_name> [<dim>],
        m = re.match(
            r'(VX_(?:mem_bus_if|execute_if|result_if|dispatch_if|commit_if))'
            r'\s*\.\s*\w+\s+(\w+)(?:\s*\[([^\]]+)\])?\s*,?\s*$',
            stripped
        )
        if m:
            if_type = m.group(1)
            inst_name = m.group(2)
            dim = m.group(3)
            expanded[inst_name] = if_type

            if if_type == 'VX_mem_bus_if':
                for sig in ['req_valid', 'req_ready', 'rsp_valid', 'rsp_ready']:
                    result.append(f'{indent}logic {inst_name}__{sig};')
                result.append(f'{indent}logic [63:0] {inst_name}__req_data;')
                result.append(f'{indent}logic [63:0] {inst_name}__rsp_data;')
            elif if_type in ('VX_execute_if', 'VX_result_if'):
                result.append(f'{indent}logic {inst_name}__valid;')
                result.append(f'{indent}logic {inst_name}__ready;')
                result.append(f'{indent}logic [511:0] {inst_name}__data;')
            elif if_type in ('VX_dispatch_if', 'VX_commit_if'):
                result.append(f'{indent}logic {inst_name}__valid;')
                result.append(f'{indent}logic {inst_name}__ready;')
                result.append(f'{indent}logic [511:0] {inst_name}__data;')
            continue

        result.append(line)

    content = '\n'.join(result)

    # ─── Step 2: Expand member accesses (longest name first) ───
    for inst_name in sorted(expanded.keys(), key=len, reverse=True):
        if_type = expanded[inst_name]
        ename = re.escape(inst_name)

        if if_type == 'VX_mem_bus_if':
            for sig in ['req_valid', 'req_ready', 'rsp_valid', 'rsp_ready']:
                content = re.sub(rf'\b{ename}\.{sig}\b', f'{inst_name}__{sig}', content)
            # req_data.field → req_data__field
            content = re.sub(rf'\b{ename}\.req_data\.(\w+)',
                             f'{inst_name}__req_data__\\1', content)
            content = re.sub(rf'\b{ename}\.rsp_data\.(\w+)',
                             f'{inst_name}__rsp_data__\\1', content)
        elif if_type in ('VX_execute_if', 'VX_result_if', 'VX_dispatch_if', 'VX_commit_if'):
            content = re.sub(rf'\b{ename}\.valid\b', f'{inst_name}__valid', content)
            content = re.sub(rf'\b{ename}\.ready\b', f'{inst_name}__ready', content)
            # data.field → data__field (flatten nested struct)
            content = re.sub(rf'\b{ename}\.data\.(\w+)',
                             f'{inst_name}__data__\\1', content)

    # ─── Step 3: Handle instantiation connections ───
    # .port_name(ifname) where ifname is expanded → comment out
    # These will be connected by matching port names in sub-modules
    lines = content.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        m = re.match(r'\s*\.(\w+)\s*\(\s*(\w+)\s*\)', stripped)
        if m and m.group(2) in expanded:
            result.append(f'{line.rstrip()}  // IF-EXPANDED')
            continue
        result.append(line)

    return '\n'.join(result), expanded


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: expand_interfaces.py <input.sv> <output.sv>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        content = f.read()

    content, expanded = expand_interfaces(content)

    with open(sys.argv[2], 'w') as f:
        f.write(content)

    print(f"Expanded {len(expanded)} interfaces:")
    for name, iftype in sorted(expanded.items()):
        print(f"  {name}: {iftype}")
