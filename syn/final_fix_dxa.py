#!/usr/bin/env python3
"""Final fix for remaining DXA synthesis issues."""
import re

DXA_DIR = '/tmp/dxa_synth'

def read(fname):
    with open(f'{DXA_DIR}/{fname}') as f:
        return f.read()

def write(fname, content):
    with open(f'{DXA_DIR}/{fname}', 'w') as f:
        f.write(content)

# Fix VX_dxa_gmem_req.sv: remove multi-line VX_mem_bus_if instance
c = read('VX_dxa_gmem_req.sv')
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

# Fix STATIC_ASSERT
c = c.replace('/* STATIC_ASSERT removed */)', '/* STATIC_ASSERT removed */')
# Fix assign /* rw */ 1'b0 = 1'b0
c = re.sub(r"assign /\* rw \*/ 1'b0 = 1'b0;", '// rw not used in flat mode', c)
# Fix .bus_in_if connection
c = c.replace('.bus_in_if  (mem_bus_w)', '.bus_in_if  (/* flat */)')
# Fix UNUSED_VAR
c = re.sub(r"`UNUSED_VAR\s*\(\s*gmem_bus_if_rsp_tag_value\[GMEM_TAG_VALUEW-1:TAG_W\]\s*\)", '// upper tag bits unused', c)

# Replace MEM_ATTR_W with 8 and GMEM_TAG_WIDTH with 33
c = re.sub(r'\bMEM_ATTR_W\b', '8', c)
c = re.sub(r'\bGMEM_TAG_WIDTH\b', '33', c)

write('VX_dxa_gmem_req.sv', c)
print(f'gmem_req: {c.count("MEM_ATTR_W")} MEM_ATTR_W remaining')

# Fix VX_dxa_worker.sv: replace .gmem_bus_if and .smem_bus_if with flat connections
c = read('VX_dxa_worker.sv')
c = c.replace(
    '.gmem_bus_if        (gmem_bus_if),',
    '.gmem_bus_if_req_valid   (gmem_bus_if_req_valid),\n'
    '        .gmem_bus_if_req_addr    (gmem_bus_if_req_addr),\n'
    '        .gmem_bus_if_req_data    (gmem_bus_if_req_data),\n'
    '        .gmem_bus_if_req_byteen  (gmem_bus_if_req_byteen),\n'
    '        .gmem_bus_if_req_attr    (gmem_bus_if_req_attr),\n'
    '        .gmem_bus_if_req_tag_uuid(gmem_bus_if_req_tag_uuid),\n'
    '        .gmem_bus_if_req_tag_value(gmem_bus_if_req_tag_value),\n'
    '        .gmem_bus_if_req_ready   (gmem_bus_if_req_ready),\n'
    '        .gmem_bus_if_rsp_valid   (gmem_bus_if_rsp_valid),\n'
    '        .gmem_bus_if_rsp_data    (gmem_bus_if_rsp_data),\n'
    '        .gmem_bus_if_rsp_tag_uuid(gmem_bus_if_rsp_tag_uuid),\n'
    '        .gmem_bus_if_rsp_tag_value(gmem_bus_if_rsp_tag_value),\n'
    '        .gmem_bus_if_rsp_ready   (gmem_bus_if_rsp_ready),'
)
c = c.replace(
    '.smem_bus_if           (smem_bus_if),',
    '.smem_bus_if_req_valid   (smem_bus_if_req_valid),\n'
    '        .smem_bus_if_req_addr    (smem_bus_if_req_addr),\n'
    '        .smem_bus_if_req_data    (smem_bus_if_req_data),\n'
    '        .smem_bus_if_req_byteen  (smem_bus_if_req_byteen),\n'
    '        .smem_bus_if_req_attr    (smem_bus_if_req_attr),\n'
    '        .smem_bus_if_req_tag_uuid(smem_bus_if_req_tag_uuid),\n'
    '        .smem_bus_if_req_tag_value(smem_bus_if_req_tag_value),\n'
    '        .smem_bus_if_req_ready   (smem_bus_if_req_ready),\n'
    '        .smem_bus_if_rsp_valid   (smem_bus_if_rsp_valid),\n'
    '        .smem_bus_if_rsp_data    (smem_bus_if_rsp_data),\n'
    '        .smem_bus_if_rsp_tag_uuid(smem_bus_if_rsp_tag_uuid),\n'
    '        .smem_bus_if_rsp_tag_value(smem_bus_if_rsp_tag_value),\n'
    '        .smem_bus_if_rsp_ready   (smem_bus_if_rsp_ready),'
)
c = re.sub(r'\bMEM_ATTR_W\b', '8', c)
c = re.sub(r'\bGMEM_TAG_WIDTH\b', '33', c)
write('VX_dxa_worker.sv', c)
print(f'worker: {c.count("gmem_bus_if")} gmem refs remaining')

# Fix VX_dxa_core.sv: fix port list, VX_mem_bus_if instances, and hierarchical refs
c = read('VX_dxa_core.sv')

# Replace VX_mem_bus_if array ports
c = re.sub(
    r'(\s*)VX_mem_bus_if\.master\s+gmem_bus_if\[GMEM_OUT_PORTS\],',
    r'\1output wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_req_valid,\n'
    r'\1output wire [GMEM_OUT_PORTS*32-1:0]           gmem_bus_if_req_addr,\n'
    r'\1output wire [GMEM_OUT_PORTS*64*8-1:0]         gmem_bus_if_req_data,\n'
    r'\1output wire [GMEM_OUT_PORTS*64-1:0]           gmem_bus_if_req_byteen,\n'
    r'\1output wire [GMEM_OUT_PORTS*8-1:0]            gmem_bus_if_req_attr,\n'
    r'\1output wire [GMEM_OUT_PORTS*33-1:0]           gmem_bus_if_req_tag_uuid,\n'
    r'\1output wire [GMEM_OUT_PORTS*33-1:0]           gmem_bus_if_req_tag_value,\n'
    r'\1input  wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_req_ready,\n'
    r'\1input  wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_rsp_valid,\n'
    r'\1output wire [GMEM_OUT_PORTS-1:0]              gmem_bus_if_rsp_ready,',
    c
)
c = re.sub(
    r'(\s*)VX_mem_bus_if\.master\s+smem_bus_if\[1\],',
    r'\1output wire                          smem_bus_if_req_valid,\n'
    r'\1output wire [31:0]                   smem_bus_if_req_addr,\n'
    r'\1output wire [DATAW-1:0]              smem_bus_if_req_data,\n'
    r'\1output wire [DATAW/8-1:0]            smem_bus_if_req_byteen,\n'
    r'\1output wire [8-1:0]                  smem_bus_if_req_attr,\n'
    r'\1output wire [UUID_WIDTH-1:0]         smem_bus_if_req_tag_uuid,\n'
    r'\1output wire [33-1:0]                 smem_bus_if_req_tag_value,\n'
    r'\1input  wire                          smem_bus_if_req_ready,\n'
    r'\1input  wire                          smem_bus_if_rsp_valid,\n'
    r'\1input  wire [DATAW-1:0]              smem_bus_if_rsp_data,\n'
    r'\1input  wire [33-1:0]                 smem_bus_if_rsp_tag_value,\n'
    r'\1output wire                          smem_bus_if_rsp_ready,',
    c
)

# Remove multi-line VX_mem_bus_if instances
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

# Replace VX_dxa_req_bus_if port
c = re.sub(
    r'(\s*)VX_dxa_req_bus_if\.slave\s+req_bus_if\[NUM_REQS\],',
    r'\1input  wire [NUM_REQS-1:0]     req_bus_if_req_valid,\n'
    r'\1output wire [NUM_REQS-1:0]     req_bus_if_req_ready,\n'
    r'\1input  wire [NUM_REQS*128-1:0] req_bus_if_req_data,',
    c
)

# Fix all hierarchical refs
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

for iface in ['dispatch_in_if', 'worker_req_if']:
    for field, flat in [('req_data', 'req_data'), ('desc_data', 'desc_data'), ('valid', 'valid'), ('ready', 'ready')]:
        c = re.sub(rf'{iface}\[(\w+)\]\.{re.escape(field)}', rf'{iface}_{flat}[\1]', c)

for field, flat in [('req_valid', 'req_valid'), ('req_ready', 'req_ready'), ('req_data', 'req_data')]:
    c = re.sub(rf'req_bus_if\[(\w+)\]\.{re.escape(field)}', rf'req_bus_if_{flat}[\1]', c)

# Fix desc_read_addr struct access
c = re.sub(
    r"assign desc_read_addr = DXA_DESC_SLOT_W'\(queue_out_bus_if\[0\]\.meta\[DXA_DESC_SLOT_W-1:0\]\);",
    "assign desc_read_addr = DXA_DESC_SLOT_W'(queue_out_bus_if_req_data[0][64 +: DXA_DESC_SLOT_W]);",
    c
)

# Fix queue_out_bus_if hierarchical refs
c = c.replace('queue_out_bus_if[0].req_valid', 'queue_out_bus_if_req_valid[0]')
c = c.replace('queue_out_bus_if[0].req_ready', 'queue_out_bus_if_req_ready[0]')
c = c.replace('queue_out_bus_if[0].req_data', 'queue_out_bus_if_req_data[0]')
c = c.replace('queue_out_bus_if[0].req_data', 'queue_out_bus_if_req_data[0]')

# Replace MEM_ATTR_W and GMEM_TAG_WIDTH
c = re.sub(r'\bMEM_ATTR_W\b', '8', c)
c = re.sub(r'\bGMEM_TAG_WIDTH\b', '33', c)

write('VX_dxa_core.sv', c)
print(f'core: done')

# Fix VX_dxa_smem_wr.sv: replace MEM_ATTR_W and GMEM_TAG_WIDTH
c = read('VX_dxa_smem_wr.sv')
c = re.sub(r'\bMEM_ATTR_W\b', '8', c)
c = re.sub(r'\bGMEM_TAG_WIDTH\b', '33', c)
write('VX_dxa_smem_wr.sv', c)
print(f'smem_wr: done')
