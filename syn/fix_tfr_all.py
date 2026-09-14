#!/usr/bin/env python3
"""
All-in-one TFR cleanup for Yosys synthesis.
Applies: macro resolution, type replacement, function inlining, 
stray string removal, preprocessor stripping.
"""
import re, sys

with open('/tmp/tfr_ecp5/tfr_raw.sv') as f:
    content = f.read()

# 1. Replace package constants with literal values (G100 config: 4 threads, 8 NR)
CONSTANTS = {
    'TCU_TC_K': '2', 'TCU_TC_M': '2', 'TCU_TC_N': '2',
    'TCU_BLOCK_CAP': '4', 'TCU_TILE_CAP': '32',
    'TCU_TILE_M': '8', 'TCU_TILE_N': '4', 'TCU_TILE_K': '4',
    'TCU_EXP_BITS': '10', 'TCU_FMT_WIDTH': '5',
    'TCU_MAX_INPUTS': '16', 'TCU_MAX_ELT_RATIO': '8', 'TCU_MIN_FMT_WIDTH': '4',
    'TCU_FP16_ID': '2', 'TCU_FP8_ID': '4', 'TCU_BF8_ID': '5',
    'TCU_BF16_ID': '3', 'TCU_TF32_ID': '1', 'TCU_FP32_ID': '0',
    'TCU_MXFP8_ID': '8', 'TCU_MXBF8_ID': '9', 'TCU_MXFP4_ID': '10',
    'TCU_NVFP4_ID': '11', 'TCU_I8_ID': '6', 'TCU_I4_ID': '7',
}
for name, value in CONSTANTS.items():
    content = re.sub(r'\b' + name + r'\b', value, content)

# 2. Fix parameter N = 2 (was TCU_TC_K)
# Already resolved above

# 3. Fix parameter name issue (parameter 16 = 16 -> parameter TCU_MAX_INPUTS = 16)
content = content.replace('parameter 16 = 16', 'parameter TCU_MAX_INPUTS = 16')

# 4. Replace custom types
content = content.replace('fedp_excep_t', 'wire [2:0]')
content = content.replace('fedp_class_t', 'wire [3:0]')

# 5. Fix doubled 'wire wire'
while 'wire wire' in content:
    content = content.replace('wire wire', 'wire')

# 6. Replace inline backtick macros
content = re.sub(r'`CLOG2\(', '$clog2(', content)
content = re.sub(r'`UNUSED_VAR\([^)]*\)', '', content)
content = re.sub(r'`UNUSED_PARAM\([^)]*\)', '', content)
content = re.sub(r'`UNUSED_PIN\([^)]*\)', '', content)
content = re.sub(r'`UNUSED_SPARAM\([^)]*\)', '', content)
content = re.sub(r'`FORCE_BUILTIN_ADDER\([^)]*\)', '0', content)
content = content.replace('!0', '1')
content = re.sub(r'`STATIC_ASSERT\([^)]*\)', '', content)
content = re.sub(r'`MAP_AOS_SOA\([^)]*\)', '', content)
content = re.sub(r'`STRING\b', '', content)

# 7. Inline package functions
# exp_bits: TF32(1)=8, FP16(2)=5, BF16(3)=8, FP8(4)=4, BF8(5)=5, FP32(0)=8
# sign_pos: TF32(1)=18, FP16(2)=15, BF16(3)=15, FP8(4)=7, BF8(5)=7, FP32(0)=31
for fmt_id, val in {0: 8, 1: 8, 2: 5, 3: 8, 4: 4, 5: 5}.items():
    content = content.replace(f'VX_tcu_pkg::exp_bits({fmt_id})', str(val))
for fmt_id, val in {0: 31, 1: 18, 2: 15, 3: 15, 4: 7, 5: 7}.items():
    content = content.replace(f'VX_tcu_pkg::sign_pos({fmt_id})', str(val))

# Inline boolean functions
content = re.sub(r'tcu_fmt_is_int\((\w+)\)', r'\1[4]', content)
content = re.sub(r'tcu_fmt_is_signed_int\((\w+)\)', r'\1[0]', content)
content = re.sub(r'tcu_fmt_is_bfloat\((\w+)\)', r'\1[0]', content)

# 8. Remove all preprocessor directive lines
content = re.sub(r'^[ \t]*`[^\n]*\n', '', content, flags=re.MULTILINE)

# 9. Remove stray empty string lines
lines = content.split('\n')
lines = [l for l in lines if l.strip() not in ('""', '"",')]
content = '\n'.join(lines)

# 10. Remove $display/$write/$fatal/$error/$warning (multi-line aware)
lines = content.split('\n')
out = []
in_syscall = False
depth = 0
for line in lines:
    s = line.strip()
    if in_syscall:
        depth += s.count('(') - s.count(')')
        if depth <= 0:
            in_syscall = False
        continue
    if re.search(r'\$display|\$write|\$fatal|\$error|\$warning', s):
        depth = s.count('(') - s.count(')')
        if depth > 0:
            in_syscall = True
        continue
    if re.match(r'^\s*\$time,', s):
        continue
    if re.match(r'^\s*\(\s*".*%0', s):
        continue
    if '/* trace */' in s:
        continue
    out.append(line)
content = '\n'.join(out)

# 11. Remove empty begin/end blocks
content = re.sub(r'begin\s*\n\s*end', '', content)

with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)

# Verify
remaining_backtick = set(re.findall(r'`([A-Z_][A-Z0-9_]+)', content))
remaining_tcu = set(re.findall(r'\b(TCU_[A-Z_]+)\b', content))
remaining_pkg = set(re.findall(r'VX_tcu_pkg::\w+', content))
print(f'Lines: {len(content.splitlines())}')
print(f'Backtick remaining: {remaining_backtick}')
print(f'TCU_ remaining: {remaining_tcu}')
print(f'VX_tcu_pkg remaining: {remaining_pkg}')
