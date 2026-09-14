import re, sys

with open(sys.argv[1]) as f:
    content = f.read()

# Replace inline backtick macros with literal values
content = re.sub(r'!`FORCE_BUILTIN_ADDER\([^)]*\)', '0', content)
content = re.sub(r'`FORCE_BUILTIN_ADDER\([^)]*\)', '0', content)
content = re.sub(r'`STATIC_ASSERT\([^)]*\)', '', content)
content = re.sub(r'`UNUSED_VAR\(([^)]*)\)', r'\1', content)
content = re.sub(r'`UNUSED_PARAM\(([^)]*)\)', r'\1', content)
content = re.sub(r'`UNUSED_PIN\(([^)]*)\)', r'\1', content)
content = re.sub(r'`UNUSED_SPARAM\(([^)]*)\)', r'\1', content)
content = re.sub(r'`MAP_AOS_SOA\([^)]*\)', '', content)
content = re.sub(r'`STRING\([^)]*\)', '0', content)
content = re.sub(r'`CLOG2\(', '$clog2(', content)

with open(sys.argv[1], 'w') as f:
    f.write(content)

remaining = set(re.findall(r'`([A-Z_][A-Z0-9_]+)', content))
print(f'Remaining backtick tokens: {remaining}')
