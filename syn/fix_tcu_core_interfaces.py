#!/usr/bin/env python3
"""
fix_tcu_core_interfaces.py
Replace VX_execute_if / VX_result_if interface references in tcu_final.sv
with flat wire declarations and bit-level selections.
"""
import re, sys

XLEN = 32
TCU_LANES = 4
UUID_WIDTH = 44
NW_WIDTH = 2
NCTA_WIDTH = 1
INST_OP_BITS = 4
NUM_XREGS = 2
BYTESEL_BITS = 2
HEADER_RD_BITS = 6
INST_ARGS_BITS = 27

header_fields = [
    ("uuid", UUID_WIDTH), ("wid", NW_WIDTH), ("cta_id", NCTA_WIDTH),
    ("tmask", TCU_LANES), ("pid", 2), ("sop", 1), ("eop", 1),
    ("PC", XLEN), ("wb", 1), ("wr_xregs", NUM_XREGS),
    ("rd", HEADER_RD_BITS), ("bytesel", BYTESEL_BITS),
]

def build_map(fields):
    m, pos = {}, 0
    for name, w in fields:
        m[name] = (pos + w - 1, pos, w)
        pos += w
    return m, pos

header_map, HEADER_BITS = build_map(header_fields)

exec_map = {}
offset = 0
for name, w in header_fields:
    exec_map[f"header.{name}"] = (offset + w - 1, offset, w)
    offset += w
exec_map["header"] = (offset - 1, 0, offset)
for name, w in [("op_type", INST_OP_BITS), ("op_args", INST_ARGS_BITS)]:
    exec_map[name] = (offset + w - 1, offset, w)
    offset += w
for name, w in [("rs1_data", TCU_LANES * XLEN), ("rs2_data", TCU_LANES * XLEN), ("rs3_data", TCU_LANES * XLEN)]:
    exec_map[name] = (offset + w - 1, offset, w)
    offset += w

tcu_args_map = {
    "is_last_uop": (26, 26), "is_first_uop": (25, 25), "a_from_smem": (24, 24),
    "cd_nregs": (23, 22), "fmt_d": (21, 17), "fmt_s": (16, 12),
    "step_k": (11, 8), "step_n": (7, 4), "step_m": (3, 0),
}

result_map = {}
offset = 0
for name, w in header_fields:
    result_map[f"header.{name}"] = (offset + w - 1, offset, w)
    offset += w
result_map["header"] = (offset - 1, 0, offset)
RESULT_DATA_LO = offset
RESULT_DATA_HI = RESULT_DATA_LO + TCU_LANES * XLEN - 1
result_map["data"] = (RESULT_DATA_HI, RESULT_DATA_LO, TCU_LANES * XLEN)

def expand_exe_ref(m):
    """Expand execute_if.data.X to execute_if_data[hi:lo]"""
    full_match = m.group(0)
    parts = full_match.split(".")
    # execute_if.data.X.Y
    if len(parts) < 3 or parts[0] != "execute_if" or parts[1] != "data":
        return full_match
    
    field_path = ".".join(parts[2:])
    
    # header.X
    if field_path.startswith("header."):
        hfield = field_path.split(".")[1]
        if hfield in header_map:
            hi, lo, w = header_map[hfield]
            return f"execute_if_data[{hi}:{lo}]" if hi != lo else f"execute_if_data[{hi}]"
    
    # header (whole)
    if field_path == "header":
        hi, lo, w = exec_map["header"]
        return f"execute_if_data[{hi}:{lo}]"
    
    # op_args.tcu.X
    if field_path.startswith("op_args.tcu."):
        tcu_field = field_path.split(".")[-1]
        if tcu_field in tcu_args_map:
            op_lo = exec_map["op_args"][1]
            tcu_hi, tcu_lo = tcu_args_map[tcu_field]
            abs_hi, abs_lo = op_lo + tcu_hi, op_lo + tcu_lo
            return f"execute_if_data[{abs_hi}:{abs_lo}]" if abs_hi != abs_lo else f"execute_if_data[{abs_hi}]"
    
    # op_type
    if field_path == "op_type":
        hi, lo, w = exec_map["op_type"]
        return f"execute_if_data[{hi}:{lo}]" if hi != lo else f"execute_if_data[{hi}]"
    
    # rs1_data[expr] or rs2_data[expr]
    for arr in ["rs1_data", "rs2_data", "rs3_data"]:
        if field_path.startswith(arr + "["):
            idx = field_path[len(arr):]  # [expr]
            lo = exec_map[arr][1]
            return f"execute_if_data[({idx.lstrip('[').rstrip(']')}) * {XLEN} + {lo} +: {XLEN}]"
    
    # rs1_data (whole)
    for arr in ["rs1_data", "rs2_data", "rs3_data"]:
        if field_path == arr:
            hi, lo, w = exec_map[arr]
            return f"execute_if_data[{hi}:{lo}]"
    
    return full_match

def expand_res_ref(m):
    """Expand result_if.data.X to result_if_data[hi:lo]"""
    full_match = m.group(0)
    parts = full_match.split(".")
    if len(parts) < 3 or parts[0] != "result_if" or parts[1] != "data":
        return full_match
    
    field_path = ".".join(parts[2:])
    
    # header.X
    if field_path.startswith("header."):
        hfield = field_path.split(".")[1]
        if hfield in header_map:
            hi, lo, w = header_map[hfield]
            return f"result_if_data[{hi}:{lo}]" if hi != lo else f"result_if_data[{hi}]"
    
    # header (whole)
    if field_path == "header":
        hi, lo, w = result_map["header"]
        return f"result_if_data[{hi}:{lo}]"
    
    # data[expr]
    if field_path.startswith("data["):
        idx = field_path[5:-1]
        return f"result_if_data[({idx}) * {XLEN} + {RESULT_DATA_LO} +: {XLEN}]"
    
    # data (whole)
    if field_path == "data":
        hi, lo, w = result_map["data"]
        return f"result_if_data[{hi}:{lo}]"
    
    return full_match

def process(input_path, output_path):
    with open(input_path) as f:
        text = f.read()
    
    # Replace interface port declarations
    text = text.replace(
        '    VX_execute_if.slave execute_if,',
        '    input  wire        execute_if_valid,\n'
        '    output wire        execute_if_ready,\n'
        '    input  wire [511:0] execute_if_data,'
    )
    text = text.replace(
        '    VX_result_if.master result_if',
        '    output wire         result_if_valid,\n'
        '    input  wire         result_if_ready,\n'
        '    output wire [511:0] result_if_data'
    )
    
    # Replace .valid / .ready
    text = text.replace('execute_if.valid', 'execute_if_valid')
    text = text.replace('execute_if.ready', 'execute_if_ready')
    text = text.replace('result_if.valid', 'result_if_valid')
    text = text.replace('result_if.ready', 'result_if_ready')
    
    # Replace execute_if.data.X.Y.Z references
    text = re.sub(r'execute_if\.data\.[\w.]+(?:\[[^\]]*\])?', expand_exe_ref, text)
    
    # Replace result_if.data.X.Y references
    text = re.sub(r'result_if\.data\.[\w.]+(?:\[[^\]]*\])?', expand_res_ref, text)
    
    with open(output_path, 'w') as f:
        f.write(text)
    
    # Verify
    remaining_exe = len(re.findall(r'execute_if\.data\.', text))
    remaining_res = len(re.findall(r'result_if\.data\.', text))
    remaining_if = len(re.findall(r'VX_\w+_if\.', text))
    print(f"Remaining execute_if.data refs: {remaining_exe}")
    print(f"Remaining result_if.data refs: {remaining_res}")
    print(f"Remaining interface refs: {remaining_if}")
    print(f"Written to {output_path}")

if __name__ == "__main__":
    process(sys.argv[1], sys.argv[2])
