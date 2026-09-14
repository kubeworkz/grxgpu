import re
with open('/tmp/tfr_ecp5/tfr_from_tcu.sv') as f:
    content = f.read()

# Inline tcu_fmt_is_int(fmt) -> fmt[4]
content = re.sub(r'tcu_fmt_is_int\((\w+)\)', r'\1[4]', content)

# Inline tcu_fmt_is_signed_int(int_fmt) -> int_fmt[0]
content = re.sub(r'tcu_fmt_is_signed_int\((\w+)\)', r'\1[0]', content)

# Inline tcu_fmt_is_bfloat(float_fmt) -> float_fmt[0]
content = re.sub(r'tcu_fmt_is_bfloat\((\w+)\)', r'\1[0]', content)

# Inline tcu_fmt_width(fmt) -> use a case-based replacement
# Actually tcu_fmt_width returns different values for different formats
# For simplicity, keep it as a localparam or inline the common case
# Let me check usage
# tcu_fmt_width is used in: localparam WORD_SIZE_LOG2 = $clog2(tcu_fmt_width(fmt_s) / 8);
# This is too complex to inline. Let me define it as a function in the file.
# Actually, Yosys supports function definitions. Let me add the function.

with open('/tmp/tfr_ecp5/tfr_from_tcu.sv', 'w') as f:
    f.write(content)

# Check for remaining function calls
remaining = set(re.findall(r'\b([a-z_]+)\s*\([^)]*\)', content))
func_names = {m for m in remaining if not m.startswith(('wire', 'reg', 'input', 'output', 'assign', 'localparam', 'parameter', 'module', 'always', 'case', 'endcase', 'for', 'begin', 'end', 'if', 'else', 'generate', 'genvar', 'endgenerate', 'integer', 'real'))}
print(f'Function calls remaining: {func_names}')
