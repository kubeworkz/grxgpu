#!/usr/bin/env python3
"""
Complete TCU synthesis pipeline:
1. Read all TCU + TFR SV files
2. Strip includes, resolve packages
3. Strip ifdef blocks (debug/trace -> remove entirely, functional -> keep THEN branch)
4. Strip $display/TRACE/UNUSED macros
5. Resolve SV constructs (always_ff, logic, typedef, etc.)
6. Hoist generate-scoped declarations from TFR modules
7. Output Yosys-ready flat file
"""
import re, sys, os

# --- Constants ---
TCU_DIR = os.path.expanduser('~/grxgpu/hw/rtl/tcu')
TFR_DIR = os.path.join(TCU_DIR, 'tfr')
OUTPUT = '/tmp/tcu_flat_v2.sv'

# Patterns that should strip the ENTIRE ifdef block (both branches)
STRIP_PATTERNS = [
    'DBG_', 'TRACE', 'SIMULATION', 'UNUSED', 'LD_TRACE',
    'CFG_SIM', 'CFG_TRACE', 'DBG_', 'UNUSED',
]

# Patterns that should keep the THEN branch (functional code)
KEEP_THEN_PATTERNS = [
    'TCU_WGMMA', 'TCU_SPARSE', 'TCU_ENABLE', 'TCU_LOCKSTEP',
    'CFG_TCU', 'DCACHE', 'LMEM',
]

def should_strip_entirely(name):
    """Check if this ifdef block should be completely removed."""
    upper = name.upper()
    for pat in STRIP_PATTERNS:
        if pat.upper() in upper:
            return True
    return False

def should_keep_then(name):
    """Check if this ifdef block should keep the THEN branch."""
    upper = name.upper()
    for pat in KEEP_THEN_PATTERNS:
        if pat.upper() in upper:
            return True
    return False

def strip_ifdef_blocks(content):
    """Strip ifdef blocks with intelligent branch selection."""
    lines = content.split('\n')
    out = []
    stack = []  # (name, action) where action is 'strip' or 'keep_then' or 'keep_else'
    # action values: 'strip' = skip everything, 'keep_then' = keep THEN, 'keep_else' = skip THEN
    depth = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Match `ifdef / `ifndef
        m_ifdef = re.match(r'`ifn?def\s+(\w+)', stripped)
        if m_ifdef:
            name = m_ifdef.group(1)
            depth += 1
            # Check if parent is in skip mode — if so, inherit it
            parent_skip = stack and stack[-1][1] in ('strip', 'skip_rest')
            if parent_skip:
                stack.append((name, stack[-1][1]))
                continue
            if should_strip_entirely(name):
                stack.append((name, 'strip'))
                continue
            stack.append((name, 'keep_then'))
            out.append(line)
            continue
        
        if stripped == '`else':
            if stack:
                name, action = stack[-1]
                if action == 'strip':
                    continue
                elif action == 'keep_then':
                    stack[-1] = (name, 'skip_rest')
                    continue
                elif action == 'skip_rest':
                    stack[-1] = (name, 'keep_then')  # resume keeping
                    continue
            out.append(line)
            continue
        
        m_elsif = re.match(r'`elsif\s+(\w+)', stripped)
        if m_elsif:
            if stack:
                name, action = stack[-1]
                if action == 'strip':
                    continue
                elif action == 'keep_then':
                    stack[-1] = (name, 'skip_rest')
                    continue
                elif action == 'skip_rest':
                    # Check if we should keep this branch
                    ename = m_elsif.group(1)
                    if should_strip_entirely(ename):
                        stack[-1] = (name, 'strip')
                    else:
                        stack[-1] = (name, 'keep_then')
                    continue
            out.append(line)
            continue
        
        if stripped.startswith('`endif'):
            if stack:
                name, action = stack.pop()
                depth = max(0, depth - 1)
                if action == 'strip':
                    continue
                elif action == 'skip_rest':
                    continue
            out.append(line)
            continue
        
        # Check if we're inside a stripped block
        if stack:
            _, action = stack[-1]
            if action == 'strip' or action == 'skip_rest':
                continue
        
        out.append(line)
    
    return '\n'.join(out)

def phase_a_transform(content):
    """Apply Phase A Yosys compatibility transforms."""
    
    # Strip includes
    content = re.sub(r'`include\s+"[^"]*"', '', content)
    
    # Strip import statements
    content = re.sub(r'import\s+VX_gpu_pkg::\*\s*,\s*VX_tcu_pkg::\*\s*;', '', content)
    content = re.sub(r'import\s+VX_tcu_pkg::\*\s*;', '', content)
    content = re.sub(r'import\s+VX_gpu_pkg::\*\s*;', '', content)
    
    # Strip STATIC_ASSERT (multi-line)
    content = re.sub(r'`STATIC_ASSERT\s*\([^)]*(\([^)]*\))*[^)]*\)\s*;?', '', content, flags=re.DOTALL)
    
    # Strip UNUSED_* macros (strip entire line to avoid orphaned tokens)
    lines = content.split('\n')
    content = '\n'.join(l for l in lines if '`UNUSED_' not in l)
    
    # Strip RUNTIME_ASSERT macro (multi-line)
    content = re.sub(r'`RUNTIME_ASSERT\s*\([^)]*(\([^)]*\))*[^)]*\)\s*;?', '', content, flags=re.DOTALL)
    
    # Strip remaining backtick macros that are used inline (catch-all)
    # SFORMATF, MAP_AOS_SOA, ASSIGN_VX_MEM_BUS_IF, SCOPE_IO_BIND, SCOPE_IO_SWITCH
    for macro in ['SFORMATF', 'MAP_AOS_SOA', 'ASSIGN_VX_MEM_BUS_IF', 'SCOPE_IO_BIND', 'SCOPE_IO_SWITCH']:
        # Replace the macro and any surrounding parens: (`MACRO(...)) -> ("")
        content = re.sub(r'\(\s*`' + macro + r'\s*(?:\([^)]*(?:\([^)]*\))*[^)]*\))\s*\)', '(""', content)
        # Also replace standalone macro calls without outer parens
        content = re.sub(r'`' + macro + r'\s*(?:\([^)]*(?:\([^)]*\))*[^)]*\))', '""', content)
    
    # Strip string parameters
    content = re.sub(r'parameter\s+`STRING\s+\w+\s*=\s*"[^"]*"\s*,?\s*', '', content)
    content = re.sub(r'parameter\s+`STRING\s+\w+\s*=\s*"[^"]*"\s*\)', ')', content)
    
    # Strip interface port declarations (VX_*.slave/master NAME [SIZE],)
    content = re.sub(r'\s*VX_\w+\.\w+\s+\w+(?:\s*\[[^\]]+\])?\s*,?\s*\n', '\n', content)
    content = re.sub(r'\s*VX_\w+\.\w+\s+\w+(?:\s*\[[^\]]+\])?\s*\n', '\n', content)
    
    # Replace struct types with wire [31:0]
    struct_types = ['tcu_execute_t', 'fedp_class_t', 'fedp_excep_t', 'tcu_set_excep_t', 'tcu_result_t', 'tcu_tbuf_req_t', 'tcu_header_t', 'tcu_perf_t', 'data_t', 'execute_t', 'ibuffer_t', 'lsu_req_data_t', 'mem_bus_attr_t']
    for st in struct_types:
        content = re.sub(r'\b' + st + r'\b', 'wire [31:0]', content)
    
    # Flatten trailing unpacked array dimensions from port/wire declarations
    # e.g. 'input wire [31:0] data [BLOCK_SIZE]' -> 'input wire [31*BLOCK_SIZE-1:0] data'
    # Remove the original packed range and replace with a combined packed range
    content = re.sub(r'((?:input|output|inout)\s+(?:wire|reg)?\s*)(?:\s*\[[^\]]+\])?\s+(\w+)\s*\[([A-Z_][A-Z_0-9]*)\]', r'\1 [31*\3-1:0] \2', content)
    # Handle wire declarations with trailing unpacked array
    content = re.sub(r'(wire\s+)(?:\[[^\]]+\]\s*)?(\w+)\s*\[([A-Z_][A-Z_0-9]*)\]', r'\1[31*\3-1:0] \2', content)
    
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
        'VX_CFG_ISSUE_WIDTH': '1', 'VX_CFG_LMEM_LOG_SIZE': '14',
        'VX_CFG_NUM_THREADS': '4', 'VX_CFG_NUM_WARPS': '4',
        'VX_MEM_LMEM_BASE_ADDR': '0',
    }
    for const, val in gpu_consts.items():
        content = content.replace('VX_gpu_pkg::' + const, val)
    
    # Resolve VX_tcu_pkg:: function calls
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
    
    # Replace macros
    content = re.sub(r'`UP\(([^)]+)\)', r'((\1) > 0 ? (\1) : 1)', content)
    content = re.sub(r'`LOG2UP\(([^)]+)\)', r'$clog2(\1)', content)
    content = re.sub(r'`FORCE_BUILTIN_ADDER\s*\([^)]*\)', '(1)', content)
    
    # Replace $bits() with 32 (match anything inside parens)
    content = re.sub(r'\$bits\([^)]+\)', '32', content)
    
    # Convert always_ff -> always
    content = content.replace('always_ff', 'always')
    content = content.replace('always_comb', 'always @*')
    content = content.replace('always_latch', 'always @*')
    
    # Replace logic type
    content = re.sub(r'\blogic\b', 'wire', content)
    
    # Convert typedef enum to localparams + wire
    def convert_enum(m):
        enum_body = m.group(1)
        type_name = m.group(2)
        pairs = re.findall(r'(\w+)\s*=\s*([^,}]+)', enum_body)
        localparams = []
        for vname, vval in pairs:
            localparams.append('localparam %s = %s;' % (vname, vval.strip()))
        return '\n'.join(localparams) + '\n    wire [0:0] %s;' % type_name
    content = re.sub(r'typedef\s+enum\s+(?:wire(?:\s*\[[^\]]+\])?|logic\s*(?:\[[^\]]+\])?)\s*\{([^}]+)\}\s*(\w+)\s*;', convert_enum, content)
    
    # Convert type_name var_name; to wire for enum types
    enum_types = re.findall(r'localparam \w+ = [^;]+;.*?wire \[0:0\] (\w+);', content, re.DOTALL)
    for tn in enum_types:
        content = re.sub(r'\b' + tn + r'\s+(\w+)\s*;', r'wire [0:0] \1;', content)
    
    # Convert automatic int/reg/wire
    content = re.sub(r'\bautomatic\s+int\b', 'wire [31:0]', content)
    content = re.sub(r'\bautomatic\s+reg\b', 'reg', content)
    content = re.sub(r'\bautomatic\s+wire\b', 'wire', content)
    
    # Strip unsigned/signed qualifiers from wire declarations
    content = re.sub(r'(wire\s+(?:\[[^\]]+\])?)\s+unsigned\s+', r'\1 ', content)
    content = re.sub(r'(wire\s+(?:\[[^\]]+\])?)\s+signed\s+', r'\1 ', content)
    
    # Convert int'(x) casts
    content = re.sub(r"int'\(([^)]+)\)", r'(\1)', content)
    
    # Convert TYPE'(x) casts to plain expressions (handles both normal types and macro types)
    content = re.sub(r"(?:`?\w+'\()([^)]+)\)", r'(\1)', content)
    
    # Strip `TRACE macros (single-line)
    content = re.sub(r'^\s*`TRACE\([^)]*\)\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*`TRACE_ARRAY\w*\([^)]*\)\s*$', '', content, flags=re.MULTILINE)
    
    # Strip $display and $write calls (multi-line aware)
    lines = content.split('\n')
    cleaned = []
    in_display = False
    for line in lines:
        s = line.strip()
        if in_display:
            if ');' in s or s.endswith(';'):
                in_display = False
            continue
        if '$display' in s or '$write' in s:
            if not (s.endswith(';') or ');' in s):
                in_display = True
            continue
        cleaned.append(line)
    content = '\n'.join(cleaned)
    
    # Clean up empty if blocks
    content = re.sub(r'if\s*\([^)]*\)\s*\n\s*end\n', '', content)
    content = re.sub(r'if\s*\([^)]*\)\s*begin\s*\n\s*end\s*\n', '', content)
    
    # Remove lines that are just backtick tokens
    content = re.sub(r'^\s*`\w+\s*$', '', content, flags=re.MULTILINE)
    
    # Remove orphaned closing brackets/parens from stripped macros
    content = re.sub(r'^\s*[\]\)]+\s*$', '', content, flags=re.MULTILINE)
    # Remove orphaned empty string statements (""; or ";")
    content = re.sub(r'^\s*"\s*"?\s*;\s*$', '', content, flags=re.MULTILINE)
    
    # Remove duplicate `);` lines (two in a row = one is orphaned)
    content = re.sub(r'(\);\s*\n)\s*\);\s*\n', r'\1', content)
    
    # Strip remaining interface instances: VX_* #(...) NAME[SIZE]();
    content = re.sub(r'\s*VX_\w+\s*#\([^)]*\)\s*\w+(?:\s*\[[^\]]+\])?\s*\(\s*\)\s*;?', '', content)
    # Strip remaining interface instances without params: VX_* NAME();
    content = re.sub(r'\s*VX_\w+\s+\w+(?:\s*\[[^\]]+\])?\s*\(\s*\)\s*;?', '', content)
    
    return content

def collect_genvar_decls(body, genvar_name):
    """Collect wire/localparam declarations inside a genvar block."""
    decls = []
    seen = set()
    
    # Wire declarations (with optional signed)
    for m in re.finditer(r'^\s*(?:wire\s+(?:signed\s+)?)?(\[[^\]]+(?:\]\[[^\]]+)*\])\s+([^=\n;]+);', body, re.MULTILINE):
        width = m.group(1)
        names_str = m.group(2)
        for name in re.findall(r'\b(\w+)\b', names_str):
            if name not in seen and name != genvar_name:
                seen.add(name)
                decls.append({'type': 'wire', 'name': name, 'width': width})
    
    # Wire with assignment
    for m in re.finditer(r'^\s*wire\s+(?:signed\s+)?(\[[^\]]+\])\s+(\w+)\s*=\s*([^;]+);', body, re.MULTILINE):
        width = m.group(1)
        name = m.group(2)
        expr = m.group(3)
        if name not in seen and genvar_name not in expr:
            seen.add(name)
            decls.append({'type': 'wire', 'name': name, 'width': width, 'expr': expr})
    
    # Localparams (only constant ones, no genvar reference)
    for m in re.finditer(r'^\s*localparam\s+(?:\[\w[^\]]*\]\s+)?(\w+)\s*=\s*([^;]+);', body, re.MULTILINE):
        lp_name = m.group(1)
        lp_expr = m.group(2)
        if lp_name not in seen and genvar_name not in lp_expr:
            seen.add(lp_name)
            decls.append({'type': 'localparam', 'name': lp_name, 'expr': lp_expr})
    
    return decls

def hoist_genvar_blocks(content):
    """Hoist generate-scoped declarations to module scope for all modules."""
    # Find module boundaries
    modules = list(re.finditer(r'^module\s+(\w+)', content, re.MULTILINE))
    
    for mod_idx, mod_match in enumerate(modules):
        mod_name = mod_match.group(1)
        mod_start = mod_match.start()
        
        # Find endmodule
        endmod = re.search(r'^endmodule', content[mod_start:], re.MULTILINE)
        if not endmod:
            continue
        mod_end = mod_start + endmod.start()
        mod_body = content[mod_start:mod_end]
        
        # Find genvar blocks
        blocks = list(re.finditer(
            r'for\s*\(\s*genvar\s+(\w+)\s*=\s*(\d+)\s*;\s*\w+\s*<\s*(\w+)\s*;\s*\+\+\w+\)\s*begin\s*:\s*(\w+)',
            mod_body, re.MULTILINE
        ))
        
        if not blocks:
            continue
        
        all_hoisted = []
        localparams = []
        
        for block in blocks:
            var = block.group(1)
            bound = block.group(3)
            label = block.group(4)
            
            # Find the block body (matching end)
            block_start = block.start()
            begin_pos = mod_body.find('begin', block_start)
            depth = 1
            pos = begin_pos + 5
            while depth > 0 and pos < len(mod_body):
                if mod_body[pos:pos+5] == 'begin':
                    depth += 1
                    pos += 5
                elif mod_body[pos:pos+3] == 'end':
                    depth -= 1
                    pos += 3
                else:
                    pos += 1
            block_body = mod_body[begin_pos:pos]
            
            decls = collect_genvar_decls(block_body, var)
            
            for d in decls:
                if d['type'] == 'localparam':
                    localparams.append('    localparam %s = %s;' % (d['name'], d['expr']))
                elif 'expr' in d:
                    all_hoisted.append('    wire %s %s_%s = %s;' % (d['width'], label, d['name'], d['expr']))
                else:
                    all_hoisted.append('    wire %s %s_%s [0:%s-1];' % (d['width'], label, d['name'], bound))
        
        if all_hoisted or localparams:
            # Find module header end
            header_end = re.search(r'\);\s*\n', mod_body)
            if header_end:
                insert_pos = mod_start + header_end.end()
                # Insert localparams first, then wires
                hoist_text = '\n'.join(localparams + all_hoisted) + '\n'
                content = content[:insert_pos] + hoist_text + content[insert_pos:]
    
    return content

def main():
    print("=== TCU Synthesis Pipeline ===")
    
    # Step 1: Read all files
    tcu_files = sorted([f for f in os.listdir(TCU_DIR) if f.endswith('.sv') and f != 'VX_tcu_pkg.sv'])
    tfr_files = sorted([f for f in os.listdir(TFR_DIR) if f.endswith('.sv')])
    
    print("TCU files: %d" % len(tcu_files))
    print("TFR files: %d" % len(tfr_files))
    
    combined = []
    for f in tcu_files:
        with open(os.path.join(TCU_DIR, f)) as fh:
            content = fh.read()
            combined.append("// === %s ===\n%s" % (f, content))
    for f in tfr_files:
        with open(os.path.join(TFR_DIR, f)) as fh:
            content = fh.read()
            combined.append("// === %s ===\n%s" % (f, content))
    
    all_content = '\n'.join(combined)
    print("Combined: %d bytes" % len(all_content))
    
    # Step 2: Strip ifdef blocks (debug/trace -> remove entirely)
    all_content = strip_ifdef_blocks(all_content)
    print("After ifdef strip: %d bytes" % len(all_content))
    
    # Step 3: Phase A transforms
    all_content = phase_a_transform(all_content)
    print("After Phase A: %d bytes" % len(all_content))
    
    # Step 4: Hoist generate-scoped declarations
    all_content = hoist_genvar_blocks(all_content)
    print("After hoisting: %d bytes" % len(all_content))
    
    # Step 5: Prepend macro definitions for Yosys
    macro_defs = """// Macro definitions for Yosys synthesis
`define VX_CFG_XLEN 32
`define VX_CFG_NUM_THREADS 4
`define VX_CFG_NUM_WARPS 4
`define VX_CFG_ISSUE_WIDTH 1
`define VX_CFG_NUM_TCU_LANES 4
`define VX_CFG_NUM_TCU_BLOCKS 1
`define VX_CFG_LMEM_LOG_SIZE 14
`define VX_CFG_LMEM_NUM_BANKS 4
`define VX_MEM_LMEM_BASE_ADDR 0
`define CLOG2(x) $clog2(x)
`define MAX(a,b) ((a) > (b) ? (a) : (b))
"""
    all_content = macro_defs + all_content
    
    # Step 6: Write output
    with open(OUTPUT, 'w') as f:
        f.write(all_content)
    
    modules = re.findall(r'^module\s+(\w+)', all_content, re.MULTILINE)
    print("Output: %s (%d modules)" % (OUTPUT, len(modules)))
    
    return OUTPUT

if __name__ == '__main__':
    main()
