#!/usr/bin/env python3
"""
expand_struct_refs.py
---------------------
Replace struct member accesses on execute_if__data / result_if__data with
explicit bit selections so Surelog can resolve them without SV interface
elaboration.
"""
import re, sys

# ── Parameter values (G100 defaults) ─────────────────────────────────────
XLEN          = 32
TCU_LANES     = 4
UUID_WIDTH    = 44
NW_WIDTH      = 2
NCTA_WIDTH    = 1
INST_OP_BITS  = 4
NUM_XREGS     = 2
BYTESEL_BITS  = 2
INST_ARGS_BITS = 27
HEADER_RD_BITS = 6

header_fields = [
    ("uuid", UUID_WIDTH), ("wid", NW_WIDTH), ("cta_id", NCTA_WIDTH),
    ("tmask", TCU_LANES), ("pid", 2), ("sop", 1), ("eop", 1),
    ("PC", XLEN), ("wb", 1), ("wr_xregs", NUM_XREGS),
    ("rd", HEADER_RD_BITS), ("bytesel", BYTESEL_BITS),
]
HEADER_BITS = sum(w for _, w in header_fields)

data_fields = [("op_type", INST_OP_BITS), ("op_args", INST_ARGS_BITS)]
DATA_XLEN_FIELDS = [
    ("rs1_data", TCU_LANES * XLEN),
    ("rs2_data", TCU_LANES * XLEN),
    ("rs3_data", TCU_LANES * XLEN),
]
EXEC_TOTAL = HEADER_BITS + sum(w for _, w in data_fields) + sum(w for _, w in DATA_XLEN_FIELDS)
RESULT_DATA_BITS = TCU_LANES * XLEN

def build_field_map(fields):
    m, pos = {}, 0
    for name, width in fields:
        m[name] = (pos + width - 1, pos)
        pos += width
    return m

header_map = build_field_map(header_fields)

exec_map = {}
offset = 0
for name, width in header_fields:
    exec_map[f"header.{name}"] = (offset + width - 1, offset)
    offset += width
for name, width in data_fields:
    exec_map[name] = (offset + width - 1, offset)
    offset += width
for name, width in DATA_XLEN_FIELDS:
    exec_map[name] = (offset + width - 1, offset)
    offset += width

result_map = {}
offset = 0
for name, width in header_fields:
    result_map[f"header.{name}"] = (offset + width - 1, offset)
    offset += width
result_map["header"] = (offset - 1, 0)
result_map["data"] = (offset + RESULT_DATA_BITS - 1, offset)

tcu_args_map = {
    "is_last_uop": (26, 26), "is_first_uop": (25, 25), "a_from_smem": (24, 24),
    "cd_nregs": (23, 22), "fmt_d": (21, 17), "fmt_s": (16, 12),
    "step_k": (11, 8), "step_n": (7, 4), "step_m": (3, 0),
}

def expand_execute_ref(m):
    prefix = m.group(1)  # execute_if__data
    field_path = m.group(3).lstrip(".")
    suffix = m.group(4) or ""  # optional [idx] after field
    parts = field_path.split(".")

    # header.field
    if parts[0] == "header" and len(parts) == 2:
        hfield = parts[1]
        if hfield in header_map:
            hi, lo = header_map[hfield]
            return f"{prefix}[{hi}:{lo}]" if hi != lo else f"{prefix}[{hi}]" + suffix
        return m.group(0)

    # op_args.tcu.field
    if parts[0] == "op_args" and len(parts) >= 3 and parts[1] == "tcu":
        tcu_field = parts[2]
        if tcu_field in tcu_args_map:
            op_lo = exec_map["op_args"][1]
            tcu_hi, tcu_lo = tcu_args_map[tcu_field]
            abs_hi, abs_lo = op_lo + tcu_hi, op_lo + tcu_lo
            return f"{prefix}[{abs_hi}:{abs_lo}]" if abs_hi != abs_lo else f"{prefix}[{abs_hi}]"
        return m.group(0)

    # field[idx] — array element access (suffix was captured separately)
    if parts[0] in exec_map:
        field = parts[0]
        hi, lo = exec_map[field]
        if suffix.startswith("["):
            idx_expr = suffix[1:-1]  # strip [ and ]
            if field in ["rs1_data", "rs2_data", "rs3_data", "data"]:
                return f"{prefix}[({idx_expr}) * {XLEN} + {lo} +: {XLEN}]"
        if hi != lo:
            return f"{prefix}[{hi}:{lo}]" + suffix
        return f"{prefix}[{hi}]" + suffix

    return m.group(0)


def expand_result_ref(m):
    prefix = m.group(1)  # result_if__data
    field_path = m.group(3).lstrip(".")
    suffix = m.group(4) or ""
    parts = field_path.split(".")

    if parts[0] == "header" and len(parts) == 1:
        hi, lo = result_map["header"]
        return f"{prefix}[{hi}:{lo}]" + suffix

    if parts[0] == "header" and len(parts) == 2:
        hfield = parts[1]
        if hfield in header_map:
            hi, lo = header_map[hfield]
            return f"{prefix}[{hi}:{lo}]" if hi != lo else f"{prefix}[{hi}]" + suffix
        return m.group(0)

    if parts[0] == "data" and suffix.startswith("["):
        idx_expr = suffix[1:-1]
        lo = result_map["data"][1]
        return f"{prefix}[({idx_expr}) * {XLEN} + {lo} +: {XLEN}]"

    if parts[0] == "data":
        hi, lo = result_map["data"]
        return f"{prefix}[{hi}:{lo}]" + suffix

    return m.group(0)


def process(input_path, output_path):
    with open(input_path) as f:
        content = f.read()

    # Match execute_if__data.field [optional_array_index]
    exe_pat = re.compile(r'(execute_if__data)(\.([\w.]+))(\[[^\]]*\])?')
    res_pat = re.compile(r'(result_if__data)(\.([\w.]+))(\[[^\]]*\])?')

    content = exe_pat.sub(expand_execute_ref, content)
    content = res_pat.sub(expand_result_ref, content)

    with open(output_path, 'w') as f:
        f.write(content)

    print(f"Expanded struct references: {input_path} -> {output_path}")
    print(f"  execute_t total width: {EXEC_TOTAL} bits")
    print(f"  result_t data width: {RESULT_DATA_BITS} bits")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: expand_struct_refs.py <input.sv> <output.sv>")
        sys.exit(1)
    process(sys.argv[1], sys.argv[2])
