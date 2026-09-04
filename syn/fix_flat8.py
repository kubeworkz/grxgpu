#!/usr/bin/env python3
"""Replace always_ff, strip verilator attrs and DBG_TRACE"""
import re

with open("/tmp/tfr_flat.sv") as f:
    content = f.read()

# Replace always_ff with always @(posedge clk)
content = re.sub(r"always_ff @\(posedge (\w+)\)", r"always @(\1)", content)
content = re.sub(r"always_ff @\(([^)]+)\)", r"always @(\1)", content)

# Remove verilator attributes
content = re.sub(r"/\*\s*verilator[^*]*\*/", "", content)

# Remove DBG_TRACE blocks (simulation only)
content = re.sub(r"`ifdef DBG_TRACE_TCU.*?`endif", "", content, flags=re.DOTALL)

# Remove any remaining $display/$write/$time calls
content = re.sub(r"\$display\([^)]*\)", "/* display stripped */", content)
content = re.sub(r"\$write\([^)]*\)", "/* write stripped */", content)

# Remove INSTANCE_ID references (parameter was stripped)
content = re.sub(r"\bINSTANCE_ID\b", '""', content)

with open("/tmp/tfr_flat.sv", "w") as f:
    f.write(content)
print(f"Updated: {len(content)} bytes")
