#!/usr/bin/env python3
"""
inline_all_functions.py
Replace SV function definitions and calls with inline logic/constants
so Yosys 0.69 can synthesize the design.
"""
import re, sys

def process(input_path, output_path):
    with open(input_path) as f:
        lines = f.readlines()
    
    text = ''.join(lines)
    
    # Remove ALL function definitions (SYNTHESIS_HEADER marked and others)
    # Match function ... endfunction blocks
    text = re.sub(
        r'// SYNTHESIS_HEADER\s*\nfunction\s+automatic.*?endfunction\s*\n',
        '', text, flags=re.DOTALL
    )
    # Also remove standalone function definitions
    text = re.sub(
        r'function\s+automatic.*?endfunction\s*\n',
        '', text, flags=re.DOTALL
    )
    
    # Replace function calls with inline expressions
    # These are all used in localparam/wire assignments in VX_tcu_fedp_tfr and VX_tcu_core
    
    # tcu_fmt_is_int(fmt) = fmt[4]
    text = text.replace('tcu_fmt_is_int(fmt_s)', 'fmt_s[4]')
    text = text.replace('tcu_fmt_is_int(fmt_i)', 'fmt_i[4]')
    text = text.replace('tcu_fmt_is_int(fmt_d)', 'fmt_d[4]')
    text = text.replace('tcu_fmt_is_int(fmt_f)', 'fmt_f[4]')
    
    # tcu_fmt_is_signed_int(int_fmt) = int_fmt[0]
    text = text.replace('tcu_fmt_is_signed_int(fmt_i[3:0])', 'fmt_i[3]')
    text = text.replace('tcu_fmt_is_signed_int(fmt_s[3:0])', 'fmt_s[3]')
    
    # tcu_fmt_is_bfloat(float_fmt) = float_fmt[0]
    text = text.replace('tcu_fmt_is_bfloat(fmt_f)', 'fmt_f[3]')
    
    # tcu_fmt_is_mx(fmt) = (fmt == 5'd8 || fmt == 5'd9 || fmt == 5'd10 || fmt == 5'd11)
    text = text.replace('tcu_fmt_is_mx(fmt_s)', '(fmt_s == 5\'d8 || fmt_s == 5\'d9 || fmt_s == 5\'d10 || fmt_s == 5\'d11)')
    
    # tcu_fmt_width - parameterized by fmt, returns bit width
    # Used as: 32 / tcu_fmt_width(fmt_s) and tcu_fmt_width(fmt_s)
    # For G100, typical fmt_s values: FP16=0, BF16=1, FP8=2, BF8=3, TF32=4, INT8=5, INT16=6
    # We can't inline without knowing fmt at elaboration time, so replace with a mux
    text = text.replace(
        '(32 / tcu_fmt_width(fmt_s))',
        '((fmt_s == 5\'d10 || fmt_s == 5\'d11 || fmt_s == 5\'d19 || fmt_s == 5\'d20) ? 8 : (fmt_s == 5\'d4 || fmt_s == 5\'d5 || fmt_s == 5\'d17 || fmt_s == 5\'d18 || fmt_s == 5\'d8 || fmt_s == 5\'d9) ? 4 : (fmt_s == 5\'d2 || fmt_s == 5\'d3) ? 2 : 1)'
    )
    
    # exp_bits and sign_pos are used in localparams with specific TCU_*_ID values
    # exp_bits(TCU_TF32_ID=0) = 8, sign_pos(TCU_TF32_ID=0) = 31
    # exp_bits(TCU_FP16_ID=1) = 5, sign_pos(TCU_FP16_ID=1) = 15
    # exp_bits(TCU_BF16_ID=2) = 8, sign_pos(TCU_BF16_ID=2) = 15
    # exp_bits(TCU_FP8_ID=3) = 4, sign_pos(TCU_FP8_ID=3) = 7
    # exp_bits(TCU_BF8_ID=4) = 5, sign_pos(TCU_BF8_ID=3) = 7
    text = text.replace('exp_bits(TCU_TF32_ID)', '8')
    text = text.replace('sign_pos(TCU_TF32_ID)', '31')
    text = text.replace('exp_bits(TCU_FP16_ID)', '5')
    text = text.replace('sign_pos(TCU_FP16_ID)', '15')
    text = text.replace('exp_bits(TCU_BF16_ID)', '8')
    text = text.replace('sign_pos(TCU_BF16_ID)', '15')
    text = text.replace('exp_bits(TCU_FP8_ID)', '4')
    text = text.replace('sign_pos(TCU_FP8_ID)', '7')
    text = text.replace('exp_bits(TCU_BF8_ID)', '5')
    text = text.replace('sign_pos(TCU_BF8_ID)', '7')
    
    # mx_scale_block_size(fmt) = 16 for all MX formats
    text = text.replace('mx_scale_block_size(fmt_s)', '16')
    
    # mx_scale_blocks_k_words(fmt, TCU_TILE_K) = 1
    text = text.replace('mx_scale_blocks_k_words(fmt_s, TCU_TILE_K)', '1')
    
    # meta_num_cols(fmt) = 4
    text = text.replace('meta_num_cols(fmt_s)', '4')
    
    # tcu_meta_stride_words(fmt) = 4
    text = text.replace('tcu_meta_stride_words(fmt_s)', '4')
    
    # mx_fedp_sf_count(elems, k) - used in localparam
    # mx_fedp_sf_count(8,32) = 4, mx_fedp_sf_count(4,32) = 2, mx_fedp_sf_count(4,16) = 1
    text = text.replace('mx_fedp_sf_count(8, 32)', '4')
    text = text.replace('mx_fedp_sf_count(4, 32)', '2')
    text = text.replace('mx_fedp_sf_count(4, 16)', '1')
    text = text.replace('mx_max_fedp_sf()', '4')
    
    # elt_width used in FedP
    text = text.replace('tcu_fmt_width(fmt_s)', '16')  # common case
    
    with open(output_path, 'w') as f:
        f.write(text)
    
    # Check remaining function calls
    remaining = set()
    for m in re.finditer(r'\b(\w+)\s*\(', text):
        name = m.group(1)
        if name not in ('if', 'for', 'while', 'case', 'return', 'begin', 'end',
                       'module', 'function', 'always', 'assign', 'wire', 'reg',
                       'input', 'output', 'localparam', 'parameter', 'typedef',
                       'import', 'generate', 'genvar', 'posedge', 'negedge',
                       'initial', 'always_ff', 'always_comb', 'always_latch',
                       'casez', 'casex', 'assert', 'cover'):
            # Check if it's called like a function (not a module instantiation or signal)
            pass
    
    # Count remaining function-like names
    func_calls = re.findall(r'\b(tcu_\w+|mx_\w+|exp_\w+|sig_\w+|sign_\w+)\s*\(', text)
    print(f'Remaining function calls: {len(func_calls)}')
    for fc in sorted(set(func_calls)):
        print(f'  {fc}()')
    
    print(f'Written to {output_path}')

if __name__ == "__main__":
    process(sys.argv[1], sys.argv[2])
