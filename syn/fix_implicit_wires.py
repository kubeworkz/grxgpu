#!/usr/bin/env python3
"""
Fix implicit gen-scoped wires in the flattened TFR file.

Yosys can't handle undeclared variables inside generate blocks that cross
the always/assign boundary. This script adds explicit module-scope wire
declarations for these variables and replaces bare references with 
genvar-indexed versions.
"""
import re
import sys

def fix_module_implicit_wires(content):
    """
    For each module with gen blocks, find undeclared variables that are 
    assigned inside always blocks inside gen blocks but referenced by
    module instantiation ports and assigns in the same gen block.
    
    The fix: add module-scope wire declarations and replace bare name
    references with genvar-indexed versions.
    """
    lines = content.split('\n')
    
    # Find all module boundaries  
    modules = []
    i = 0
    while i < len(lines):
        m = re.match(r'\s*module\s+(\w+)', lines[i])
        if m:
            mod_start = i
            mod_name = m.group(1)
            # Find endmodule
            for j in range(i+1, len(lines)):
                if re.match(r'\s*endmodule', lines[j]):
                    modules.append((mod_name, mod_start, j))
                    i = j + 1
                    break
            else:
                i += 1
        else:
            i += 1
    
    for mod_name, mod_start, mod_end in modules:
        # Find genvar for-loops
        genvar_names = {}
        for i in range(mod_start, mod_end):
            gm = re.match(r'\s*for\s*\(\s*genvar\s+(\w+)\s*=', lines[i])
            if gm:
                genvar_names[i] = gm.group(1)
        
        if not genvar_names:
            continue
        
        # For each genvar, find the begin/end block
        for gv_line, gv_var in genvar_names.items():
            # Find the begin block
            begin_line = None
            for i in range(gv_line, min(gv_line + 5, mod_end)):
                if 'begin' in lines[i]:
                    begin_line = i
                    break
            
            if begin_line is None:
                continue
            
            # Track begin/end nesting to find the gen block end
            depth = 0
            gen_end = None
            for i in range(begin_line, mod_end):
                # Count begin/end keywords
                depth += len(re.findall(r'\bbegin\b', lines[i]))
                depth -= len(re.findall(r'\bend\b(?!\w)', lines[i]))
                if depth == 0 and i > begin_line:
                    gen_end = i
                    break
            
            if gen_end is None:
                continue
            
            # Find implicit wires: variables assigned in always blocks
            # inside the gen block but used outside always blocks in the same gen block
            implicit = {}
            in_always = False
            always_depth = 0
            
            for i in range(begin_line + 1, gen_end):
                line = lines[i].strip()
                
                # Track always blocks
                if 'always' in line:
                    in_always = True
                    always_depth = 0
                
                if in_always:
                    always_depth += len(re.findall(r'\bbegin\b', line))
                    always_depth -= len(re.findall(r'\bend\b(?!\w)', line))
                    if always_depth <= 0:
                        in_always = False
                    continue
                
                # Look for variable assignments: varname = expr or .port(varname)
                # Module instantiation port connections
                for pm in re.finditer(r'\.(\w+)\s*\(\s*(\w+)\s*\)', line):
                    port, var = pm.groups()
                    if var == gv_var or var in ('1', '0', '1\'b0', '1\'b1'):
                        continue
                    if not re.match(r'^[A-Z_]', var) and not var.startswith('g_'):
                        implicit[var] = True
                
                # Direct assign statements
                for am in re.finditer(r'\b(\w+)\s*(?:<=|==)', line):
                    var = am.group(1)
                    if var == gv_var or var.startswith('g_') or var.startswith('VX_'):
                        continue
                    if not re.match(r'^[A-Z]', var):
                        implicit[var] = True
            
            if not implicit:
                continue
            
            # Check which of these variables DON'T have explicit wire declarations
            # in the hoisted section
            hoisted = set()
            for i in range(mod_start, min(mod_start + 100, mod_end)):
                for wm in re.finditer(r'wire\s+\[.*?\]\s+(\w+)', lines[i]):
                    hoisted.add(wm.group(1))
            
            # Find the Phase B hoisted wire section
            phase_b_line = None
            for i in range(mod_start, mod_end):
                if '// Phase B: Hoisted generate-scoped wires' in lines[i]:
                    phase_b_line = i
                    break
            
            missing = [v for v in implicit if v not in hoisted]
            
            if missing and phase_b_line is not None:
                # Determine widths for each missing variable
                widths = {}
                for var in missing:
                    if 'sb' in var or 'sa' in var:
                        widths[var] = 1
                    elif 'eb' in var or 'ea' in var:
                        widths[var] = 5 if 'f8' in mod_name.lower() else 8
                    elif 'mb' in var or 'ma' in var:
                        widths[var] = 3 if 'f8' in mod_name.lower() else 10
                    else:
                        widths[var] = 8  # default
                
                # Find where to insert (after the last hoisted wire in Phase B section)
                insert_after = phase_b_line
                for i in range(phase_b_line + 1, mod_end):
                    if lines[i].strip().startswith('wire ') or lines[i].strip() == '':
                        insert_after = i
                    else:
                        break
                
                # Insert declarations
                new_lines = []
                for var in sorted(missing):
                    w = widths[var]
                    # These are used per-lane [0:15] since g_lane iterates i
                    new_lines.append(f'    wire [{w-1}:0] {var}_gen [0:15];')
                
                lines[insert_after + 1:insert_after + 1] = new_lines
                
                # Now replace bare references in the gen block with indexed versions
                # This is tricky because the genvar varies - we need to index with the right genvar
                # For now, just replace module-scope references
                
    return '\n'.join(lines)


def simple_fix(content):
    """
    Simpler approach: just add the known missing wire declarations for
    the specific variables that cause errors.
    """
    # These are the known problematic implicit wires
    # They need per-lane array declarations since they're in g_lane[i] gen blocks
    
    fixes = {
        # Module VX_tcu_tfr_mul_f8: raw_sb, raw_eb, raw_mb used in g_extract[j]
        'VX_tcu_tfr_mul_f8': {
            'raw_sb': 1,
            'raw_eb': 5,
            'raw_mb': 3,
        },
        # Module VX_tcu_tfr_mul_f4: same pattern
        'VX_tcu_tfr_mul_f4': {
            'raw_sb': 1,
            'raw_eb': 4,
            'raw_mb': 2,
        },
    }
    
    lines = content.split('\n')
    
    for mod_name, wire_info in fixes.items():
        # Find the module
        mod_start = None
        phase_b_line = None
        for i, line in enumerate(lines):
            if re.match(rf'\s*module\s+{re.escape(mod_name)}\b', line):
                mod_start = i
            if mod_start is not None and '// Phase B: Hoisted' in line:
                phase_b_line = i
                break
            if mod_start is not None and re.match(r'\s*endmodule', line):
                break
        
        if phase_b_line is None:
            continue
        
        # Find end of hoisted section
        insert_after = phase_b_line
        for i in range(phase_b_line + 1, len(lines)):
            stripped = lines[i].strip()
            if stripped.startswith('wire ') or stripped.startswith('//') or stripped == '':
                insert_after = i
            else:
                break
        
        # Check which wires already exist
        existing = set()
        for i in range(mod_start or 0, insert_after + 1):
            for wm in re.finditer(r'wire\s+\[.*?\]\s+(\w+)', lines[i]):
                existing.add(wm.group(1))
        
        # Add missing wires
        new_lines = []
        for var, width in sorted(wire_info.items()):
            if var not in existing:
                new_lines.append(f'    wire [{width-1}:0] {var} [0:15];')
        
        if new_lines:
            for j, nl in enumerate(new_lines):
                lines.insert(insert_after + 1 + j, nl)
    
    return '\n'.join(lines)


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else '/tmp/tfr_flat_v2.sv'
    dst = sys.argv[2] if len(sys.argv) > 2 else src
    
    with open(src) as f:
        content = f.read()
    
    result = simple_fix(content)
    
    with open(dst, 'w') as f:
        f.write(result)
    
    # Count lines added
    orig_lines = content.count('\n')
    new_lines = result.count('\n')
    print(f"Added {new_lines - orig_lines} lines for implicit wire declarations")
