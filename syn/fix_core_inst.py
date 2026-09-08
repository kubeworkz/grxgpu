#!/usr/bin/env python3
"""Fix internal submodule instantiations in VX_dxa_core.sv to use flat wire connections."""
import re

DXA_DIR = '/tmp/dxa_synth'

with open(f'{DXA_DIR}/VX_dxa_core.sv') as f:
    c = f.read()

# Fix VX_dxa_desc_table instantiation
# Original: .dcr_bus_if (dcr_bus_if),
# Need: .dcr_bus_if_req_valid (dcr_bus_if_req_valid), .dcr_bus_if_req_rw (dcr_bus_if_req_rw), etc.
c = re.sub(
    r'\.dcr_bus_if\s*\(dcr_bus_if\)',
    '.dcr_bus_if_req_valid (dcr_bus_if_req_valid),\n'
    '        .dcr_bus_if_req_rw   (dcr_bus_if_req_rw),\n'
    '        .dcr_bus_if_req_addr (dcr_bus_if_req_addr),\n'
    '        .dcr_bus_if_req_data (dcr_bus_if_req_data),\n'
    '        .dcr_bus_if_rsp_data (dcr_bus_if_rsp_data)',
    c
)

# Fix VX_dxa_req_arb instantiation
# Original: .bus_in_if (req_bus_if), .bus_out_if (arb_out_bus_if)
# Need flat wire connections
c = re.sub(
    r'\.bus_in_if\s*\(req_bus_if\)',
    '.bus_in_if_req_valid (req_bus_if_req_valid),\n'
    '        .bus_in_if_req_ready (req_bus_if_req_ready),\n'
    '        .bus_in_if_req_data  (req_bus_if_req_data)',
    c
)
c = re.sub(
    r'\.bus_out_if\s*\(arb_out_bus_if\)',
    '.bus_out_if_req_valid (arb_out_bus_if_req_valid),\n'
    '        .bus_out_if_req_ready (arb_out_bus_if_req_ready),\n'
    '        .bus_out_if_req_data  (arb_out_bus_if_req_data)',
    c
)

# Fix VX_elastic_buffer instantiation
# Replace arb_out_bus_if[0].req_valid with arb_out_bus_if_req_valid[0]
c = c.replace('arb_out_bus_if[0].req_valid', 'arb_out_bus_if_req_valid[0]')
c = c.replace('arb_out_bus_if[0].req_ready', 'arb_out_bus_if_req_ready[0]')
c = c.replace('arb_out_bus_if[0].req_data', 'arb_out_bus_if_req_data[0]')
c = c.replace('queue_out_bus_if[0].req_valid', 'queue_out_bus_if_req_valid[0]')
c = c.replace('queue_out_bus_if[0].req_ready', 'queue_out_bus_if_req_ready[0]')
c = c.replace('queue_out_bus_if[0].req_data', 'queue_out_bus_if_req_data[0]')

# Fix VX_dxa_dispatch instantiation
# Original: .req_in (dispatch_in_if), .req_out (worker_req_if)
# Need flat wire connections
c = re.sub(
    r'\.req_in\s*\(dispatch_in_if\)',
    '.req_in_valid    (dispatch_in_if_valid),\n'
    '        .req_in_req_data (dispatch_in_if_req_data),\n'
    '        .req_in_desc_data(dispatch_in_if_desc_data),\n'
    '        .req_in_ready    (dispatch_in_if_ready)',
    c
)
c = re.sub(
    r'\.req_out\s*\(worker_req_if\)',
    '.req_out_valid    (worker_req_if_valid),\n'
    '        .req_out_req_data (worker_req_if_req_data),\n'
    '        .req_out_desc_data(worker_req_if_desc_data),\n'
    '        .req_out_ready    (worker_req_if_ready)',
    c
)

# Fix VX_dxa_worker instantiation (inside genvar loop)
# Original: .req_if (worker_req_if[i]), .gmem_bus_if (worker_gmem_bus_if[i]), .smem_bus_if (worker_smem_bus_if[i])
c = re.sub(
    r'\.req_if\s*\(worker_req_if\[i\]\)',
    '.req_if_valid    (worker_req_if_valid[i]),\n'
    '            .req_if_req_data (worker_req_if_req_data[i]),\n'
    '            .req_if_desc_data(worker_req_if_desc_data[i]),\n'
    '            .req_if_ready    (worker_req_if_ready[i])',
    c
)
c = re.sub(
    r'\.gmem_bus_if\s*\(worker_gmem_bus_if\[i\]\)',
    '.gmem_bus_if_req_valid   (gmem_bus_if_req_valid[i]),\n'
    '            .gmem_bus_if_req_addr    (gmem_bus_if_req_addr[i*32 +: 32]),\n'
    '            .gmem_bus_if_req_data    (gmem_bus_if_req_data[i*GMEM_BYTES*8 +: GMEM_BYTES*8]),\n'
    '            .gmem_bus_if_req_byteen  (gmem_bus_if_req_byteen[i*GMEM_BYTES +: GMEM_BYTES]),\n'
    '            .gmem_bus_if_req_attr    (gmem_bus_if_req_attr[i*MEM_ATTR_W +: MEM_ATTR_W]),\n'
    '            .gmem_bus_if_req_tag_uuid(gmem_bus_if_req_tag_uuid[i*GMEM_TAG_WIDTH +: GMEM_TAG_WIDTH]),\n'
    '            .gmem_bus_if_req_tag_value(gmem_bus_if_req_tag_value[i*GMEM_TAG_WIDTH +: GMEM_TAG_WIDTH]),\n'
    '            .gmem_bus_if_req_ready   (gmem_bus_if_req_ready[i]),\n'
    '            .gmem_bus_if_rsp_valid   (gmem_bus_if_rsp_valid[i]),\n'
    '            .gmem_bus_if_rsp_ready   (gmem_bus_if_rsp_ready[i])',
    c
)
c = re.sub(
    r'\.smem_bus_if\s*\(worker_smem_bus_if\[i\]\)',
    '.smem_bus_if_req_valid   (smem_bus_if_req_valid),\n'
    '            .smem_bus_if_req_addr    (smem_bus_if_req_addr),\n'
    '            .smem_bus_if_req_data    (smem_bus_if_req_data),\n'
    '            .smem_bus_if_req_byteen  (smem_bus_if_req_byteen),\n'
    '            .smem_bus_if_req_attr    (smem_bus_if_req_attr),\n'
    '            .smem_bus_if_req_tag_uuid(smem_bus_if_req_tag_uuid),\n'
    '            .smem_bus_if_req_tag_value(smem_bus_if_req_tag_value),\n'
    '            .smem_bus_if_req_ready   (smem_bus_if_req_ready),\n'
    '            .smem_bus_if_rsp_valid   (smem_bus_if_rsp_valid),\n'
    '            .smem_bus_if_rsp_data    (smem_bus_if_rsp_data),\n'
    '            .smem_bus_if_rsp_tag_value(smem_bus_if_rsp_tag_value),\n'
    '            .smem_bus_if_rsp_ready   (smem_bus_if_rsp_ready)',
    c
)

# Fix VX_mem_bus_arb instantiation (gmem_arb, lmem_arb)
# These use bus_in_if/bus_out_if with interface arrays
c = re.sub(
    r'\.bus_in_if\s*\(worker_gmem_bus_if\)',
    '.req_valid (gmem_bus_if_req_valid),\n'
    '        .req_addr  (gmem_bus_if_req_addr),\n'
    '        .req_data  (gmem_bus_if_req_data),\n'
    '        .req_byteen(gmem_bus_if_req_byteen),\n'
    '        .req_attr  (gmem_bus_if_req_attr),\n'
    '        .req_tag   (gmem_bus_if_req_tag_uuid),\n'
    '        .req_ready (gmem_bus_if_req_ready),\n'
    '        .rsp_valid (gmem_bus_if_rsp_valid),\n'
    '        .rsp_data  (0),\n'
    '        .rsp_tag   (0),\n'
    '        .rsp_ready (gmem_bus_if_rsp_ready)',
    c
)
c = re.sub(
    r'\.bus_out_if\s*\(gmem_bus_if\)',
    '/* gmem_bus_out connected below */',
    c
)
c = re.sub(
    r'\.bus_in_if\s*\(worker_smem_bus_if\)',
    '.req_valid (smem_bus_if_req_valid),\n'
    '        .req_addr  (smem_bus_if_req_addr),\n'
    '        .req_data  (smem_bus_if_req_data),\n'
    '        .req_byteen(smem_bus_if_req_byteen),\n'
    '        .req_attr  (smem_bus_if_req_attr),\n'
    '        .req_tag   (smem_bus_if_req_tag_uuid),\n'
    '        .req_ready (smem_bus_if_req_ready),\n'
    '        .rsp_valid (smem_bus_if_rsp_valid),\n'
    '        .rsp_data  (smem_bus_if_rsp_data),\n'
    '        .rsp_tag   (smem_bus_if_rsp_tag_value),\n'
    '        .rsp_ready (smem_bus_if_rsp_ready)',
    c
)
c = re.sub(
    r'\.bus_out_if\s*\(smem_bus_if\)',
    '/* smem_bus_out connected below */',
    c
)

# Fix VX_dxa_worker instantiation in genvar — also fix .req_if and .gmem_bus_if and .smem_bus_if
# These are inside the genvar loop and reference worker_req_if[i], worker_gmem_bus_if[i], worker_smem_bus_if[i]

# Fix req_bus_if[i].req_valid in genvar
c = re.sub(r'req_bus_if\[i\]\.req_valid', 'req_bus_if_req_valid[i]', c)

with open(f'{DXA_DIR}/VX_dxa_core.sv', 'w') as f:
    f.write(c)

# Verify
remaining = len(re.findall(r'(?<!// ).*\.(req_valid|req_ready|req_data|bus_in_if|bus_out_if|dcr_bus_if|req_if|gmem_bus_if|smem_bus_if|req_in|req_out)\b', c))
print(f'VX_dxa_core.sv: {remaining} remaining interface-style refs')
