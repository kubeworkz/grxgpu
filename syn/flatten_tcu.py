#!/usr/bin/env python3
"""
Flatten TCU modules (top-level + TFR) into a single Yosys-compatible file.
Applies the same Phase A transforms as flatten_tfr_v2.py.
"""
import re, sys, os

# Phase A transforms (from flatten_tfr_v2.py)
def phase_a_transform(content):
    """Apply all Phase A Yosys compatibility transforms."""

    # Resolve VX_tcu_pkg:: qualified function calls
    pkg_funcs = {
        'tcu_fmt_is_fp8': lambda m: '(%s == 4 || %s == 5)' % (m.group(1), m.group(1)),
        'tcu_fmt_is_fp16': lambda m: '(%s == 2 || %s == 3)' % (m.group(1), m.group(1)),
        'tcu_fmt_is_int': lambda m: '(%s >= 16)' % m.group(1),
        'tcu_fmt_is_bfloat': lambda m: '(%s == 3)' % m.group(1),
        'tcu_fmt_is_tf32': lambda m: '(%s == 1)' % m.group(1),
        'tcu_fmt_is_signed_int': lambda m: '(%s == 16 || %s == 17 || %s == 19)' % (m.group(1), m.group(1), m.group(1)),
        'tcu_fmt_is_mx': lambda m: '(%s == 8 || %s == 9 || %s == 10 || %s == 11)' % (m.group(1), m.group(1), m.group(1), m.group(1)),
    }
    for fname, replacer in pkg_funcs.items():
        content = re.sub(r'VX_tcu_pkg::' + fname + r'\((\w+)\)', replacer, content)

    # Strip STATIC_ASSERT (multi-line with nested parens)
    content = re.sub(r'`STATIC_ASSERT\s*\([^)]*(\([^)]*\))*[^)]*\)\s*;?', '', content, flags=re.DOTALL)

    # Strip $display
    content = re.sub(r'\$display\s*\([^)]*\)\s*;', '', content)

    # Strip $write
    content = re.sub(r'\$write\s*\([^)]*\)\s*;', '', content)

    # Strip UNUSED_* macros
    content = re.sub(r'`UNUSED_\w+\s*\([^)]*\)\s*;?', '', content)

    # Strip STRING type parameters
    content = re.sub(r'parameter\s+`STRING\s+\w+\s*=\s*"[^"]*"\s*,?\s*', '', content)
    content = re.sub(r'parameter\s+`STRING\s+\w+\s*=\s*"[^"]*"\s*\)', ')', content)

    # Strip ALL `ifdef/`ifndef blocks line-by-line (handles nested blocks)
    lines = content.split('\n')
    out_lines = []
    depth = 0
    skip_depth = -1
    for line in lines:
        stripped = line.strip()
        # Handle indented preprocessor directives
        if stripped.startswith('`ifdef ') or stripped.startswith('`ifndef '):
            depth += 1
            if skip_depth < 0:
                skip_depth = -1
            else:
                pass
        elif stripped == '`else' or stripped.startswith('`else ') or stripped.startswith('`elsif '):
            if depth > 0 and skip_depth < 0:
                # Start skipping the 'else' branch
                skip_depth = depth
            elif depth > 0 and skip_depth == depth:
                # End of else branch, resume
                skip_depth = -1
        elif stripped.startswith('`endif'):
            if skip_depth == depth:
                skip_depth = -1
            depth = max(0, depth - 1)
        elif skip_depth < 0:
            out_lines.append(line)
    content = '\n'.join(out_lines)

    # Replace always_ff with always
    content = content.replace('always_ff', 'always')

    # Replace always_comb with always @*
    content = content.replace('always_comb', 'always @*')

    # Replace always_latch with always @*
    content = content.replace('always_latch', 'always @*')

    # Replace logic type
    content = re.sub(r'\blogic\b', 'wire', content)

    # Replace typedef struct packed
    content = re.sub(r'typedef\s+struct\s+packed\s*\{([^}]+)\}\s*(\w+)\s*;',
                     lambda m: '// typedef %s removed\n// struct fields: %s' % (m.group(2), m.group(1)), content)

    # Resolve VX_tcu_pkg:: constants
    tcu_consts = {
        'TCU_FP32_ID': '0', 'TCU_TF32_ID': '1', 'TCU_FP16_ID': '2',
        'TCU_BF16_ID': '3', 'TCU_FP8_ID': '4', 'TCU_BF8_ID': '5',
        'TCU_MXFP8_ID': '8', 'TCU_MXBF8_ID': '9', 'TCU_MXFP4_ID': '10',
        'TCU_NVFP4_ID': '11', 'TCU_I32_ID': '16', 'TCU_I8_ID': '17',
        'TCU_U8_ID': '18', 'TCU_I4_ID': '19', 'TCU_U4_ID': '20',
        'TCU_FMT_WIDTH': '5', 'TCU_EXP_BITS': '10',
    }
    for const, val in tcu_consts.items():
        content = content.replace('VX_tcu_pkg::' + const, val)

    # Resolve VX_gpu_pkg:: constants
    gpu_consts = {
        'TCU_MAX_INPUTS': '16', 'NUM_THREADS': '4',
    }
    for const, val in gpu_consts.items():
        content = content.replace('VX_gpu_pkg::' + const, val)

    # Replace $bits() with computed widths
    content = re.sub(r'\$bits\(\w+\)', '32', content)

    # Remove `include directives
    content = re.sub(r'`include\s+"[^"]*"', '', content)

    # Backtick-escape TCU_* constants for define macros
    for const in tcu_consts:
        content = re.sub(r'\b' + const + r'\b', '`' + const, content)

    # Strip FORCE_BUILTIN_ADDER macro (used inline)
    content = re.sub(r'`FORCE_BUILTIN_ADDER\s*\([^)]*\)', '(1)', content)

    return content


def find_genvar_blocks(text):
    """Find all genvar blocks in a module body."""
    blocks = []
    pattern = re.compile(
        r'for\s*\(\s*genvar\s+(\w+)\s*=\s*(\d+)\s*;\s*\w+\s*<\s*(\w+)\s*;\s*\+\+\w+\)\s*begin\s*:\s*(\w+)',
        re.MULTILINE
    )
    pos = 0
    while pos < len(text):
        m = pattern.search(text, pos)
        if not m:
            break
        blocks.append(m)
        pos = m.start() + 1
    return blocks


def flatten_tcu(tcu_dir, tfr_dir, output_path):
    """Flatten TCU + TFR modules into a single Yosys-compatible file."""

    # Collect all SV files
    tcu_files = []
    tfr_files = []

    # TCU top-level modules (excluding pkg)
    for f in sorted(os.listdir(tcu_dir)):
        if f.endswith('.sv') and f != 'VX_tcu_pkg.sv':
            tcu_files.append(os.path.join(tcu_dir, f))

    # TFR modules
    for f in sorted(os.listdir(tfr_dir)):
        if f.endswith('.sv'):
            tfr_files.append(os.path.join(tfr_dir, f))

    print("TCU files: %d" % len(tcu_files))
    print("TFR files: %d" % len(tfr_files))

    # Read and combine all files
    combined = []
    for f in tcu_files + tfr_files:
        with open(f) as fh:
            content = fh.read()
            # Strip includes
            content = re.sub(r'`include\s+"[^"]*"', '', content)
            combined.append("// === %s ===\n%s" % (os.path.basename(f), content))

    all_content = '\n'.join(combined)

    # Apply Phase A transforms
    all_content = phase_a_transform(all_content)

    with open(output_path, 'w') as f:
        f.write(all_content)

    # Count modules
    modules = re.findall(r'^module\s+(\w+)', all_content, re.MULTILINE)
    print("Flattened %d modules -> %s" % (len(modules), output_path))
    print("  File size: %d bytes" % len(all_content))

    return output_path


if __name__ == '__main__':
    tcu_dir = os.path.expanduser('~/grxgpu/hw/rtl/tcu')
    tfr_dir = os.path.join(tcu_dir, 'tfr')
    output = sys.argv[1] if len(sys.argv) > 1 else '/tmp/tcu_flat.sv'
    flatten_tcu(tcu_dir, tfr_dir, output)
