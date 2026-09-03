#!/usr/bin/env python3
"""Remove synthesized stub modules and fix cell references in Yosys netlist."""
import re, sys

def fix_netlist(path):
    with open(path) as f:
        content = f.read()

    stub_names = ['VX_csa_tree', 'VX_ks_adder', 'VX_lzc', 'VX_popcount',
                  'VX_wallace_mul', 'VX_pipe_register']

    # Step 1: Remove all stub module definitions
    for sn in stub_names:
        # Match: module \$paramod...VX_stubname ... endmodule
        pattern = re.compile(
            r'^module\s+\\?\$paramod[^\n]*\\' + sn + r'[^\n]*\(.*?\n.*?endmodule\s*\n',
            re.MULTILINE | re.DOTALL
        )
        before = content
        content = pattern.sub('', content)
        removed = len(before) - len(content)
        if removed > 0:
            print(f"  Removed {sn} module definition ({removed} chars)")

    # Step 2: Fix cell type references
    # Cell refs look like: \$paramod$hash\VX_stubname  inst_name (
    for sn in stub_names:
        # Match: \$paramod...hash\VX_stubname
        pattern = r'\\?\$paramod[^\s(]*\\' + sn + r'(?:\\N=s32[^\s(]*)?'
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, sn, content)
            print(f"  Fixed {len(matches)} cell references to {sn}")

    with open(path, 'w') as f:
        f.write(content)

    # Verify
    remaining = re.findall(r'\\?\$paramod[^\s]*\\VX_', content)
    if remaining:
        print(f"WARNING: {len(remaining)} mangled references remain!")
        for r in remaining[:5]:
            print(f"  {r[:70]}")
    else:
        print("All mangled references cleaned!")

if __name__ == '__main__':
    fix_netlist(sys.argv[1] if len(sys.argv) > 1 else 'out/tfr_synth.v')
