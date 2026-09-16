#!/usr/bin/env python3
"""Fix all remaining issues in tcu_final.v for Yosys synthesis."""
import re, sys

def process(path):
    with open(path) as f:
        text = f.read()
    
    # 1. Remove import VX_tcu_pkg::* from module declarations
    text = re.sub(r'\s*import\s+VX_tcu_pkg::\*;', '', text)
    
    # 2. Remove all function definitions
    text = re.sub(r'function\s+automatic\s+\[[^\]]*\]\s+\w+\s*\([^)]*\)[^;]*;.*?endfunction', '', text, flags=re.DOTALL)
    text = re.sub(r'function\s+automatic\s+\w+\s+\w+\s*\([^)]*\)[^;]*;.*?endfunction', '', text, flags=re.DOTALL)
    text = re.sub(r'function\s+automatic\s+\w+\s*\([^)]*\)[^;]*;.*?endfunction', '', text, flags=re.DOTALL)
    
    # 3. Remove orphaned ternary fragments from ifdef stripping
    text = re.sub(r'\n\s*is_wgmma \? \(rs2_data\[\(b_off_wg\) \+ WG_B_IDX\]\) :\n', '\n', text)
    
    # 4. Remove orphaned .sf_a/.sf_b port connections
    text = re.sub(r'\n\s*\.sf_[ab]\s+\([^)]*\),?\n', '\n', text)
    
    # 5. Remove duplicate fedp instance (second VX_tcu_fedp_dsp after line 3000)
    # Find the second VX_tcu_fedp_dsp instance
    fedp_positions = [m.start() for m in re.finditer(r'VX_tcu_fedp_dsp\s+#', text)]
    if len(fedp_positions) > 1:
        # Remove from second instance to its matching );
        start = fedp_positions[1]
        depth = 0
        i = start
        while i < len(text):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth <= 0:
                    end = text.find(';', i) + 1
                    text = text[:start] + text[end:]
                    break
            i += 1
    
    # 6. Replace EW with literal 16
    text = re.sub(r'localparam\s+EW\s*=\s*\d+\s*;', '', text)
    text = re.sub(r'\bEW-1\b', '15', text)
    text = re.sub(r'\bEW\b', '16', text)
    
    # 7. Inline remaining function calls
    text = re.sub(r'mx_scale_at\([^)]*\)', "8'd0", text)
    text = re.sub(r'tcu_fmt_is_signed_int\(\w+\)', 'fmt_s[3]', text)
    text = re.sub(r'mx_scale_blocks_k_words\([^)]*\)', '1', text)
    
    # 8. Remove duplicate consecutive endmodule
    text = re.sub(r'(endmodule)\s*\n\s*(endmodule)', r'\1', text)
    
    # 9. Clean up empty lines (3+ consecutive → 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    with open(path, 'w') as f:
        f.write(text)
    
    # Verify
    issues = []
    if re.search(r'function\s+automatic', text):
        issues.append('function definitions remain')
    if 'import VX_tcu_pkg' in text:
        issues.append('VX_tcu_pkg import remains')
    if re.search(r'execute_if\.data\.', text):
        issues.append('execute_if.data refs remain')
    if re.search(r'result_if\.data\.', text):
        issues.append('result_if.data refs remain')
    
    if issues:
        print(f'Issues: {issues}')
    else:
        print('All clean')
    print(f'Lines: {text.count(chr(10))+1}')

if __name__ == "__main__":
    process(sys.argv[1])
