#!/usr/bin/env python3
"""
Flatten interface arrays in VX_dxa_core.sv for single-core synthesis.
VX_CFG_NUM_DXA_CORES=1, so all [NUM_DXA_CORES] arrays become single instances.
"""
import re

with open('/tmp/dxa_synth/VX_dxa_core.sv') as f:
    text = f.read()

orig = text

# 1. Flatten worker_req_if array declaration
text = text.replace(
    'VX_dxa_req_bus_if worker_req_if[`VX_CFG_NUM_DXA_CORES]();',
    'VX_dxa_req_bus_if worker_req_if();'
)

# 2. Flatten worker_gmem_bus_if array declaration
text = text.replace(
    'VX_mem_bus_if #(\n        .DATA_SIZE (`VX_CFG_L1_LINE_SIZE),\n        .TAG_WIDTH (WORKER_GMEM_TAG_WIDTH)\n    ) worker_gmem_bus_if[`VX_CFG_NUM_DXA_CORES]();',
    'VX_mem_bus_if #(\n        .DATA_SIZE (`VX_CFG_L1_LINE_SIZE),\n        .TAG_WIDTH (WORKER_GMEM_TAG_WIDTH)\n    ) worker_gmem_bus_if();'
)

# 3. Flatten worker_smem_bus_if array declaration
text = text.replace(
    'VX_mem_bus_if #(\n        .DATA_SIZE   (DXA_LMEM_WORD_SIZE),\n        .TAG_WIDTH   (DXA_LMEM_TAG_W),\n        .ATTR_WIDTH  (DXA_LMEM_ATTR_W),\n        .ADDR_WIDTH  (DXA_LMEM_ADDR_W)\n    ) worker_smem_bus_if[`VX_CFG_NUM_DXA_CORES]();',
    'VX_mem_bus_if #(\n        .DATA_SIZE   (DXA_LMEM_WORD_SIZE),\n        .TAG_WIDTH   (DXA_LMEM_TAG_W),\n        .ATTR_WIDTH  (DXA_LMEM_ATTR_W),\n        .ADDR_WIDTH  (DXA_LMEM_ADDR_W)\n    ) worker_smem_bus_if();'
)

# 4. Flatten PERF_ENABLE perf array
text = text.replace(
    'dxa_perf_t worker_dxa_perf [`VX_CFG_NUM_DXA_CORES];',
    'dxa_perf_t worker_dxa_perf;'
)

# 5. Replace [i] references with flat names in the genvar loop
text = text.replace('worker_req_if[i]', 'worker_req_if')
text = text.replace('worker_gmem_bus_if[i]', 'worker_gmem_bus_if')
text = text.replace('worker_smem_bus_if[i]', 'worker_smem_bus_if')
text = text.replace('worker_dxa_perf[i]', 'worker_dxa_perf')

# 6. Replace [w] references with flat names in perf section
# (worker_req_if[w] in the busy/perf logic)
text = text.replace('worker_req_if[w]', 'worker_req_if')

# 7. Replace the generate loop's for-genvar with a single instantiation
# The g_workers loop body should be extracted and used directly
old_loop = re.search(
    r'for\s*\(genvar\s+i\s*=\s*0;\s*i\s*<\s*`VX_CFG_NUM_DXA_CORES;\s*\+\+i\)\s*begin\s*:\s*g_workers\n(.*?)\n    end',
    text, re.DOTALL
)
if old_loop:
    loop_body = old_loop.group(1)
    # Remove the genvar indentation (4 spaces -> 4 spaces, keep as-is)
    text = text[:old_loop.start()] + loop_body + text[old_loop.end():]

# 8. Replace the gmem_arb bus_in_if connection
# worker_gmem_bus_if is now a single interface, but gmem_arb expects [NUM_INPUTS]
# Since NUM_INPUTS=1, pass directly
text = text.replace(
    '        .bus_in_if  (worker_gmem_bus_if),\n        .bus_out_if (gmem_bus_if)\n    );\n\n    VX_mem_bus_arb #(\n        .NUM_INPUTS  (`VX_CFG_NUM_DXA_CORES),\n        .NUM_OUTPUTS (1),',
    '        .bus_in_if  (worker_gmem_bus_if),\n        .bus_out_if (gmem_bus_if)\n    );\n\n    VX_mem_bus_arb #(\n        .NUM_INPUTS  (1),\n        .NUM_OUTPUTS (1),'
)

# 9. Fix gmem_arb NUM_INPUTS  
text = text.replace(
    '    VX_mem_bus_arb #(\n        .NUM_INPUTS  (`VX_CFG_NUM_DXA_CORES),\n        .NUM_OUTPUTS (GMEM_OUT_PORTS),',
    '    VX_mem_bus_arb #(\n        .NUM_INPUTS  (1),\n        .NUM_OUTPUTS (GMEM_OUT_PORTS),'
)

# 10. Fix lmem_arb NUM_INPUTS
text = text.replace(
    '    VX_mem_bus_arb #(\n        .NUM_INPUTS  (`VX_CFG_NUM_DXA_CORES),\n        .NUM_OUTPUTS (1),\n        .DATA_SIZE   (DXA_LMEM_WORD_SIZE),',
    '    VX_mem_bus_arb #(\n        .NUM_INPUTS  (1),\n        .NUM_OUTPUTS (1),\n        .DATA_SIZE   (DXA_LMEM_WORD_SIZE),'
)

# 11. Fix dispatch NUM_OUTPUTS
text = text.replace(
    '        .NUM_OUTPUTS (`VX_CFG_NUM_DXA_CORES)',
    '        .NUM_OUTPUTS (1)'
)

# 12. Fix perf aggregation loop
old_perf_loop = re.search(
    r'for\s*\(genvar\s+i\s*=\s*0;\s*i\s*<\s*`VX_CFG_NUM_DXA_CORES;\s*\+\+i\)\s*begin\s*:\s*g_dxa_perf\n(.*?)\n    end',
    text, re.DOTALL
)
if old_perf_loop:
    perf_body = old_perf_loop.group(1)
    text = text[:old_perf_loop.start()] + perf_body + text[old_perf_loop.end():]

# 13. Fix busy/idle aggregation loops
for pattern in [
    (r'for\s*\(genvar\s+i\s*=\s*0;\s*i\s*<\s*`VX_CFG_NUM_DXA_CORES;\s*\+\+i\)\s*begin\s*:\s*g_worker_idle\n(.*?)\n    end', None),
    (r'for\s*\(genvar\s+i\s*=\s*0;\s*i\s*<\s*`VX_CFG_NUM_DXA_CORES;\s*\+\+i\)\s*begin\s*:\s*g_req_valid\n(.*?)\n    end', None),
]:
    m = re.search(pattern[0], text, re.DOTALL)
    if m:
        body = m.group(1)
        text = text[:m.start()] + body + text[m.end():]

with open('/tmp/dxa_synth/VX_dxa_core.sv', 'w') as f:
    f.write(text)

changes = sum(1 for a, b in zip(orig.split('\n'), text.split('\n')) if a != b)
print(f'Flattened interface arrays: {changes} lines changed')
