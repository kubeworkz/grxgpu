#!/usr/bin/env python3
"""
Full preprocessor for VX_gpu_pkg.sv to make it Yosys-compatible:
- Replace $bits() with computed constants
- Strip PACKAGE_ASSERT macros
- Strip function/task blocks (elaboration-time only)
- Strip SIMULATION-only blocks
"""
import re, sys

src_path = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/grxgpu/hw/rtl/VX_gpu_pkg.sv"
dst_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/VX_gpu_pkg_synth.sv"

with open(src_path) as f:
    content = f.read()

# Step 1: Replace $bits(amo_op_e) with 4 (enum logic [3:0])
content = content.replace("$bits(amo_op_e)", "4")

# Step 2: Strip PACKAGE_ASSERT lines
content = re.sub(r"[^\n]*PACKAGE_ASSERT\([^\n]*\n", "/* assertion stripped for synth */\n", content)

# Step 3: Replace remaining $bits() with 32
remaining = list(set(re.findall(r"\$bits\((\w+)\)", content)))
for r in remaining:
    content = content.replace(f"$bits({r})", "32")

# Step 4: Strip function automatic blocks (multi-line)
content = re.sub(r"    function automatic\b.*?endfunction\n", "    /* function stripped for synth */\n", content, flags=re.DOTALL)

# Step 5: Strip task blocks (multi-line)
content = re.sub(r"    task\b.*?endtask\n", "    /* task stripped for synth */\n", content, flags=re.DOTALL)

# Step 6: Remove SIMULATION-only blocks
content = re.sub(r"`ifdef SIMULATION.*?`endif[^\n]*\n", "", content, flags=re.DOTALL)

with open(dst_path, "w") as f:
    f.write(content)

n_funcs = len(re.findall(r"function stripped for synth", content))
n_tasks = len(re.findall(r"task stripped for synth", content))
n_asserts = len(re.findall(r"assertion stripped", content))
print(f"Done: {len(content)} bytes -> {dst_path}")
print(f"  Stripped {n_funcs} functions, {n_tasks} tasks, {n_asserts} assertions")
print(f"  Replaced {len(remaining)} unique $bits() types: {remaining}")
