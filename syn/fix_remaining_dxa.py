#!/usr/bin/env python3
"""Fix remaining interface refs in DXA modules after flatten_all_dxa.py."""
import re

DXA_DIR = '/tmp/dxa_synth'

def read(fname):
    with open(f'{DXA_DIR}/{fname}') as f:
        return f.read()

def write(fname, content):
    with open(f'{DXA_DIR}/{fname}', 'w') as f:
        f.write(content)

# ── VX_dxa_core.sv ──
c = read('VX_dxa_core.sv')

# Replace array port: VX_mem_bus_if.master gmem_bus_if[GMEM_OUT_PORTS],
c = re.sub(
    r'(\s*)VX_mem_bus_if\.master\s+gmem_bus_if\[GMEM_OUT_PORTS\],',
    r'\1output wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_req_valid,\n'
    r'\1output wire [GMEM_OUT_PORTS*32-1:0]           gmem_bus_if_req_addr,\n'
    r'\1output wire [GMEM_OUT_PORTS*GMEM_BYTES*8-1:0] gmem_bus_if_req_data,\n'
    r'\1output wire [GMEM_OUT_PORTS*GMEM_BYTES-1:0]   gmem_bus_if_req_byteen,\n'
    r'\1output wire [GMEM_OUT_PORTS*MEM_ATTR_W-1:0]   gmem_bus_if_req_attr,\n'
    r'\1output wire [GMEM_OUT_PORTS*GMEM_TAG_WIDTH-1:0] gmem_bus_if_req_tag_uuid,\n'
    r'\1output wire [GMEM_OUT_PORTS*GMEM_TAG_WIDTH-1:0] gmem_bus_if_req_tag_value,\n'
    r'\1input  wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_req_ready,\n'
    r'\1input  wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_rsp_valid,\n'
    r'\1output wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_rsp_ready,',
    c
)

# Replace array port: VX_mem_bus_if.master smem_bus_if[1],
c = re.sub(
    r'(\s*)VX_mem_bus_if\.master\s+smem_bus_if\[1\],',
    r'\1output wire                          smem_bus_if_req_valid,\n'
    r'\1output wire [31:0]                   smem_bus_if_req_addr,\n'
    r'\1output wire [DATAW-1:0]              smem_bus_if_req_data,\n'
    r'\1output wire [DATAW/8-1:0]            smem_bus_if_req_byteen,\n'
    r'\1output wire [MEM_ATTR_W-1:0]         smem_bus_if_req_attr,\n'
    r'\1output wire [UUID_WIDTH-1:0]         smem_bus_if_req_tag_uuid,\n'
    r'\1output wire [MEM_TAG_WIDTH-1:0]      smem_bus_if_req_tag_value,\n'
    r'\1input  wire                          smem_bus_if_req_ready,\n'
    r'\1input  wire                          smem_bus_if_rsp_valid,\n'
    r'\1input  wire [DATAW-1:0]              smem_bus_if_rsp_data,\n'
    r'\1input  wire [MEM_TAG_WIDTH-1:0]      smem_bus_if_rsp_tag_value,\n'
    r'\1output wire                          smem_bus_if_rsp_ready,',
    c
)

# Remove multi-line VX_mem_bus_if instances (any format)
lines = c.split('\n')
new_lines = []
skip_until_semi = False
for line in lines:
    if skip_until_semi:
        if ';' in line:
            skip_until_semi = False
        continue
    if 'VX_mem_bus_if' in line and '//' not in line.split('VX_mem_bus_if')[0] and 'output' not in line and 'input' not in line:
        skip_until_semi = True
        new_lines.append('    // [FLAT] VX_mem_bus_if instance removed')
        continue
    if re.match(r'\s*VX_dxa_worker_req_if\s+\w+', line) and 'input' not in line and 'output' not in line and '//' not in line.split('VX_dxa_worker_req_if')[0]:
        new_lines.append('    // [FLAT] VX_dxa_worker_req_if instance removed')
        continue
    new_lines.append(line)
c = '\n'.join(new_lines)

# Replace remaining hierarchical refs for gmem/smem arrays
for i_name in ['gmem_bus_if', 'smem_bus_if']:
    for field, flat in [
        ('req_data.tag.uuid', 'req_tag_uuid'), ('req_data.tag.value', 'req_tag_value'),
        ('req_data.addr', 'req_addr'), ('req_data.data', 'req_data'),
        ('req_data.byteen', 'req_byteen'), ('req_data.attr', 'req_attr'),
        ('req_data.rw', 'req_data_rw'), ('req_ready', 'req_ready'),
        ('rsp_valid', 'rsp_valid'), ('rsp_data.data', 'rsp_data'),
        ('rsp_data.tag.uuid', 'rsp_tag_uuid'), ('rsp_data.tag.value', 'rsp_tag_value'),
        ('rsp_ready', 'rsp_ready'),
    ]:
        c = re.sub(rf'{i_name}\[(\w+)\]\.{re.escape(field)}', rf'{i_name}_{flat}[\1]', c)

# Replace dispatch_in_if/worker_req_if hierarchical refs
for iface in ['dispatch_in_if', 'worker_req_if']:
    for field, flat in [('req_data', 'req_data'), ('desc_data', 'desc_data'), ('valid', 'valid'), ('ready', 'ready')]:
        c = re.sub(rf'{iface}\[(\w+)\]\.{re.escape(field)}', rf'{iface}_{flat}[\1]', c)

# Replace req_bus_if hierarchical refs
for field, flat in [('req_valid', 'req_valid'), ('req_ready', 'req_ready'), ('req_data', 'req_data')]:
    c = re.sub(rf'req_bus_if\[(\w+)\]\.{re.escape(field)}', rf'req_bus_if_{flat}[\1]', c)

write('VX_dxa_core.sv', c)
remaining = len(re.findall(r'(?<!// ).*(?:VX_mem_bus_if|VX_dcr_bus_if|VX_txbar_bus_if|VX_execute_if|VX_result_if|VX_dxa_worker_req_if|VX_dxa_req_bus_if)\b', c))
print(f'VX_dxa_core.sv: {remaining} remaining')

# ── VX_dxa_dispatch.sv ──
c = read('VX_dxa_dispatch.sv')

c = re.sub(
    r'(\s*)VX_dxa_worker_req_if\.slave\s+req_in\s+\[NUM_INPUTS\],',
    r'\1input  wire        req_in_valid [NUM_INPUTS],\n'
    r'\1input  wire [255:0] req_in_req_data [NUM_INPUTS],\n'
    r'\1input  wire [575:0] req_in_desc_data [NUM_INPUTS],\n'
    r'\1output wire        req_in_ready [NUM_INPUTS],',
    c
)
c = re.sub(
    r'(\s*)VX_dxa_worker_req_if\.master\s+req_out\s+\[NUM_OUTPUTS\]\s*\)',
    r'\1output wire        req_out_valid [NUM_OUTPUTS],\n'
    r'\1output wire [255:0] req_out_req_data [NUM_OUTPUTS],\n'
    r'\1output wire [575:0] req_out_desc_data [NUM_OUTPUTS],\n'
    r'\1input  wire        req_out_ready [NUM_OUTPUTS]',
    c
)

for i_name in ['req_in', 'req_out']:
    for field, flat in [('valid', 'valid'), ('req_data', 'req_data'), ('desc_data', 'desc_data'), ('ready', 'ready')]:
        c = re.sub(rf'{i_name}\[(\w+)\]\.{re.escape(field)}', rf'{i_name}_{flat}[\1]', c)

write('VX_dxa_dispatch.sv', c)
remaining = len(re.findall(r'(?<!// ).*(?:VX_dxa_worker_req_if)\b', c))
print(f'VX_dxa_dispatch.sv: {remaining} remaining')

# ── VX_dxa_gmem_req.sv: multi-line VX_mem_bus_if instance ──
c = read('VX_dxa_gmem_req.sv')

# Remove multi-line VX_mem_bus_if instance
lines = c.split('\n')
new_lines = []
skip = False
for line in lines:
    if skip:
        if 'mem_bus_w' in line and '()' in line:
            skip = False
        continue
    if 'VX_mem_bus_if' in line and 'mem_bus_w' not in line and '//' not in line.split('VX_mem_bus_if')[0]:
        skip = True
        new_lines.append('    // [FLAT] VX_mem_bus_if instance removed')
        continue
    new_lines.append(line)

c = '\n'.join(new_lines)

# Fix STATIC_ASSERT
c = c.replace('/* STATIC_ASSERT removed */)', '/* STATIC_ASSERT removed */')

# Fix assign /* rw */ 1'b0 = 1'b0
c = re.sub(r"assign /\* rw \*/ 1'b0 = 1'b0;", '// rw not used in flat mode', c)

# Replace mem_bus_w hierarchical refs
for field, flat in [
    ('req_data.tag.uuid', 'req_tag_uuid'), ('req_data.tag.value', 'req_tag_value'),
    ('req_data.addr', 'req_addr'), ('req_data.data', 'req_data'),
    ('req_data.byteen', 'req_byteen'), ('req_data.attr', 'req_attr'),
    ('req_data.rw', 'req_data_rw'), ('req_ready', 'req_ready'),
    ('rsp_valid', 'rsp_valid'), ('rsp_data.data', 'rsp_data'),
    ('rsp_data.tag.value', 'rsp_tag_value'), ('rsp_ready', 'rsp_ready'),
]:
    c = c.replace(f'mem_bus_w.{field}', f'gmem_bus_if_{flat}')

# Fix the .bus_in_if connection
c = c.replace('.bus_in_if  (mem_bus_w)', '.bus_in_if  (/* flat */)')

# Fix UNUSED_VAR macro for flattened signals
c = re.sub(r"`UNUSED_VAR\s*\(\s*gmem_bus_if_rsp_tag_value\[GMEM_TAG_VALUEW-1:TAG_W\]\s*\)", '// upper tag bits unused', c)

write('VX_dxa_gmem_req.sv', c)
remaining = len(re.findall(r'(?<!// ).*(?:VX_mem_bus_if|mem_bus_w\.)\b', c))
print(f'VX_dxa_gmem_req.sv: {remaining} remaining')

# ── VX_dxa_worker.sv: last port without comma ──
c = read('VX_dxa_worker.sv')

c = re.sub(
    r'(\s*)VX_mem_bus_if\.master\s+smem_bus_if\s*\)',
    r'\1output wire                          smem_bus_if_req_valid,\n'
    r'\1output wire [31:0]                   smem_bus_if_req_addr,\n'
    r'\1output wire [DATAW-1:0]              smem_bus_if_req_data,\n'
    r'\1output wire [DATAW/8-1:0]            smem_bus_if_req_byteen,\n'
    r'\1output wire [MEM_ATTR_W-1:0]         smem_bus_if_req_attr,\n'
    r'\1output wire [UUID_WIDTH-1:0]         smem_bus_if_req_tag_uuid,\n'
    r'\1output wire [MEM_TAG_WIDTH-1:0]      smem_bus_if_req_tag_value,\n'
    r'\1input  wire                          smem_bus_if_req_ready,\n'
    r'\1input  wire                          smem_bus_if_rsp_valid,\n'
    r'\1input  wire [DATAW-1:0]              smem_bus_if_rsp_data,\n'
    r'\1input  wire [MEM_TAG_WIDTH-1:0]      smem_bus_if_rsp_tag_value,\n'
    r'\1output wire                          smem_bus_if_rsp_ready\n'
    r'\1)',
    c
)

write('VX_dxa_worker.sv', c)
remaining = len(re.findall(r'(?<!// ).*(?:VX_mem_bus_if|VX_dxa_worker_req_if)\b', c))
print(f'VX_dxa_worker.sv: {remaining} remaining')
