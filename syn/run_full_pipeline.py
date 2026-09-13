#!/usr/bin/env python3
"""Run the full TCU synthesis pipeline and check results."""
import subprocess, re, sys, os

GRXGPU = os.path.expanduser("~/grxgpu")
TMP = "/tmp"
YOSYS = os.path.expanduser("~/yosys-0.69/bin/yosys")
SYNLIG = os.path.expanduser("~/tools/synlig/synlig/synlig")

def run(cmd, timeout=600):
    """Run a command and return stdout."""
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=GRXGPU)
    if r.returncode != 0 and r.stderr:
        print(f"  WARN: {r.stderr[:200]}")
    return r.stdout

# Step 1: Flatten
print("=== Step 1: Flatten TCU modules ===")
run(f"python3 syn/flatten_tcu.py . {TMP}/tcu_flat.sv")

# Step 2: Expand interfaces
print("=== Step 2: Expand SV interfaces ===")
run(f"python3 syn/expand_interfaces.py {TMP}/tcu_flat.sv {TMP}/tcu_expanded.sv")

# Step 3: Preprocess
print("=== Step 3: Preprocess for synthesis ===")
run(f"python3 syn/preprocess_for_synth.py {TMP}/tcu_expanded.sv {TMP}/tcu_final.sv")

# Step 4: Expand struct refs
print("=== Step 4: Expand struct references ===")
run(f"python3 syn/expand_struct_refs.py {TMP}/tcu_final.sv {TMP}/tcu_struct.sv")

# Step 5: Post-fix (ternaries, orphaned fragments, imports)
print("=== Step 5: Post-fix cleanup ===")
with open(f"{TMP}/tcu_struct.sv") as f:
    content = f.read()

# Collapse multi-line ternaries
content = re.sub(r'(=\s*is_wgmma)\s*\n\s+\?', r'\1 ?', content)
content = re.sub(r'(=\s*\(is_wgmma)\s*\n\s+(&&\s*!is_sparse)\s*\n\s+(\)\s*\?)', r'\1 \2 \3', content)
content = re.sub(r'(\))\s*\n\s+(:\s*\(execute_if)', r'\1 \2', content)
content = re.sub(r'(=\s*is_sparse\s*\?\s*32\'b0\s*:)\s*\n\s+', r'\1 ', content)
content = re.sub(r'(\))\s*\n\s+(:\s*\(rs2_data)', r'\1 \2', content)
content = re.sub(r'(\)\s*:)\s*\n\s+(32\'b0)', r'\1 \2', content)

# Remove orphaned .sf_a/.sf_b after );
lines = content.split('\n')
result = []
for line in lines:
    stripped = line.strip()
    if (stripped.startswith('.sf_a') or stripped.startswith('.sf_b')):
        prev = ''
        for j in range(len(result) - 1, -1, -1):
            if result[j].strip():
                prev = result[j].strip()
                break
        if prev.endswith(');'):
            continue
    result.append(line)

# Remove duplicate fedp instances
final = []
i = 0
while i < len(result):
    line = result[i]
    stripped = line.strip()
    if re.match(r'VX_tcu_fedp_\w+\s+#\(', stripped):
        found_prior = False
        for j in range(len(final) - 1, max(0, len(final) - 30), -1):
            ps = final[j].strip()
            if ps.startswith('VX_tcu_fedp_'):
                found_prior = True
                break
            if ps.startswith('module '):
                break
        if found_prior:
            depth = 0
            while i < len(result):
                for ch in result[i]:
                    if ch == '(': depth += 1
                    elif ch == ')': depth -= 1
                if depth <= 0 and ');' in result[i]:
                    i += 1
                    break
                i += 1
            continue
    final.append(line)
    i += 1

# Remove orphaned ternary fragments
final2 = []
for line in final:
    stripped = line.strip()
    if stripped.startswith('is_wgmma ?') and stripped.endswith(':'):
        prev = ''
        for j in range(len(final2) - 1, -1, -1):
            if final2[j].strip():
                prev = final2[j].strip()
                break
        if prev.endswith(';') or prev.endswith('end'):
            continue
    final2.append(line)

content2 = '\n'.join(final2)

# Fix remaining execute_if__data.header references
content2 = content2.replace('mdata_queue_in = execute_if__data.header;', 'mdata_queue_in = execute_if__data[97:0];')
content2 = content2.replace('setup_header_r <= execute_if__data.header;', 'setup_header_r <= execute_if__data[97:0];')

# Fix import VX_tcu_pkg::* in stubs
for stub in ['VX_tcu_fedp_dpi', 'VX_tcu_fedp_bhf', 'VX_tcu_fedp_fpnew', 'VX_tcu_fedp_dsp']:
    content2 = content2.replace(f'module {stub} import VX_tcu_pkg::*; #(', f'module {stub} #(')

with open(f"{TMP}/tcu_struct.sv", 'w') as f:
    f.write(content2)

# Count lines
print(f"  Final file: {content2.count(chr(10))+1} lines, {len(content2)} bytes")

# Step 6: Surelog parse check
print("=== Step 6: Surelog parse check ===")
out = run(f"{SYNLIG} -p 'read_systemverilog -top VX_tcu_core {TMP}/tcu_struct.sv'", timeout=180)
for line in out.split('\n'):
    if 'FATAL' in line or 'SYNTAX' in line or 'ERROR' in line:
        print(f"  {line.strip()}")

# Step 7: Synlig + Yosys ECP5 synthesis
print("=== Step 7: ECP5 synthesis ===")
out = run(f"{SYNLIG} -p 'read_systemverilog -top VX_tcu_core {TMP}/tcu_struct.sv; synth_ecp5 -top VX_tcu_core -abc9; stat'", timeout=600)
for line in out.split('\n'):
    if any(k in line for k in ['Number of', 'DFF', 'LUT', 'carry', 'ERROR', 'FATAL', 'SYNTAX']):
        print(f"  {line.strip()}")

# Write full output to log
with open(f"{TMP}/tcu_synthesis.log", 'w') as f:
    f.write(out)
print(f"\nFull log: {TMP}/tcu_synthesis.log")
