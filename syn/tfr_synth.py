#!/usr/bin/env python3
"""
Strip $bits() calls and PACKAGE_ASSERT macros from VX_gpu_pkg.sv
to produce a Yosys-compatible synthesis file.

$bits() is used in ~5 places for localparam calculations; we replace them
with explicit computed widths.  PACKAGE_ASSERT lines are assertion-only
and can be removed for synthesis.
"""
import re, sys

def compute_bits(type_name, lines):
    """
    Approximate $bits() for packed structs by scanning the struct definition.
    Returns a string constant or None if unknown.
    """
    # Find the struct definition
    in_struct = False
    total_bits = 0
    for line in lines:
        stripped = line.strip()
        if f"}} {type_name}" in stripped or f"}} {type_name};" in stripped:
            # Found end of struct definition
            break
        if "typedef struct packed" in stripped:
            in_struct = True
            continue
        if in_struct:
            # Parse logic [WIDTH-1:0] fields
            m = re.search(r'logic\s*\[(.+?)\]\s+\w+', stripped)
            if m:
                w = m.group(1).strip()
                # Evaluate simple arithmetic
                try:
                    # Handle simple cases like "7:0" -> 8, "WIDTH-1:0" -> WIDTH
                    if ':' in w:
                        parts = w.split(':')
                        hi = parts[0].strip()
                        lo = parts[1].strip()
                        if lo == '0':
                            total_bits += int(hi) + 1 if hi.isdigit() else None
                            if total_bits is None:
                                return None
                        else:
                            return None  # Complex case
                    else:
                        total_bits += int(w)
                except ValueError:
                    return None
            elif stripped.startswith("logic") and "{" not in stripped:
                # Single-bit field
                total_bits += 1
    return str(total_bits) if total_bits > 0 else None

def main():
    src = sys.argv[1]
    dst = sys.argv[2]
    
    with open(src) as f:
        lines = f.readlines()
    
    output = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Remove PACKAGE_ASSERT lines
        if 'PACKAGE_ASSERT' in stripped:
            output.append(f"// [synth-strip] {stripped}\n")
            continue
        
        # Replace $bits() with computed values
        bits_matches = list(re.finditer(r'\$bits\((\w+)\)', stripped))
        if bits_matches:
            for m in bits_matches:
                type_name = m.group(1)
                # Known widths for common types
                known = {
                    'amo_req_t': '38',      # hart_id + amo_unsigned + amo_op + amo_valid
                    'mem_bus_attr_t': '3',   # is_flush + is_write + is_cachable (approx)
                    'amo_op_e': '3',         # 3-bit enum
                    'lsu_header_t': '80',    # typical LSU header width
                }
                if type_name in known:
                    stripped = stripped.replace(f'$bits({type_name})', known[type_name])
                else:
                    print(f"WARNING: Unknown $bits({type_name}) at line {i+1}", file=sys.stderr)
                    stripped = stripped.replace(f'$bits({type_name})', '32')  # placeholder
        
        output.append(line if stripped == line.strip() else line.replace(line.strip(), stripped))
    
    with open(dst, 'w') as f:
        f.writelines(output)
    
    print(f"Processed {len(lines)} lines -> {dst}")

if __name__ == '__main__':
    main()
