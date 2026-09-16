#!/usr/bin/env python3
"""Fix port name mismatches in VX_dxa_core.sv submodule instantiations."""
import re, os

os.chdir("/tmp/dxa_synth")

fname = "VX_dxa_core.sv"
if os.path.exists(fname):
    with open(fname) as f:
        c = f.read()
    
    # Fix desc_table instantiation: restore dcr_bus_if_ prefix
    c = c.replace('.req_valid(dcr_bus_if_req_valid)', '.dcr_bus_if_req_valid(dcr_bus_if_req_valid)')
    c = c.replace('.req_rw(dcr_bus_if_req_rw)', '.dcr_bus_if_req_rw(dcr_bus_if_req_rw)')
    c = c.replace('.req_addr(dcr_bus_if_req_addr)', '.dcr_bus_if_req_addr(dcr_bus_if_req_addr)')
    c = c.replace('.req_data(dcr_bus_if_req_data)', '.dcr_bus_if_req_data(dcr_bus_if_req_data)')
    c = c.replace('.rsp_data(dcr_bus_if_rsp_data)', '.dcr_bus_if_rsp_data(dcr_bus_if_rsp_data)')
    
    # Fix req_arb instantiation: restore bus_in_if_ and bus_out_if_ prefixes
    c = c.replace('.bus_in_req_valid(req_bus_if_req_valid)', '.bus_in_if_req_valid(req_bus_if_req_valid)')
    c = c.replace('.bus_in_req_addr(req_bus_if_req_addr)', '.bus_in_if_req_addr(req_bus_if_req_addr)')
    c = c.replace('.bus_in_req_data(req_bus_if_req_data)', '.bus_in_if_req_data(req_bus_if_req_data)')
    c = c.replace('.bus_in_req_byteen(req_bus_if_req_byteen)', '.bus_in_if_req_byteen(req_bus_if_req_byteen)')
    c = c.replace('.bus_in_req_attr(req_bus_if_req_attr)', '.bus_in_if_req_attr(req_bus_if_req_attr)')
    c = c.replace('.bus_in_req_tag(req_bus_if_req_tag_uuid)', '.bus_in_if_req_tag(req_bus_if_req_tag_uuid)')
    c = c.replace('.bus_in_req_ready(req_bus_if_req_ready)', '.bus_in_if_req_ready(req_bus_if_req_ready)')
    c = c.replace('.bus_in_rsp_valid(req_bus_if_rsp_valid)', '.bus_in_if_rsp_valid(req_bus_if_rsp_valid)')
    c = c.replace('.bus_in_rsp_data(req_bus_if_rsp_data)', '.bus_in_if_rsp_data(req_bus_if_rsp_data)')
    c = c.replace('.bus_in_rsp_tag(req_bus_if_rsp_tag_uuid)', '.bus_in_if_rsp_tag(req_bus_if_rsp_tag_uuid)')
    c = c.replace('.bus_in_rsp_ready(req_bus_if_rsp_ready)', '.bus_in_if_rsp_ready(req_bus_if_rsp_ready)')
    
    c = c.replace('.bus_out_req_valid(arb_out_bus_if_req_valid)', '.bus_out_if_req_valid(arb_out_bus_if_req_valid)')
    c = c.replace('.bus_out_req_addr(arb_out_bus_if_req_addr)', '.bus_out_if_req_addr(arb_out_bus_if_req_addr)')
    c = c.replace('.bus_out_req_data(arb_out_bus_if_req_data)', '.bus_out_if_req_data(arb_out_bus_if_req_data)')
    c = c.replace('.bus_out_req_byteen(arb_out_bus_if_req_byteen)', '.bus_out_if_req_byteen(arb_out_bus_if_req_byteen)')
    c = c.replace('.bus_out_req_attr(arb_out_bus_if_req_attr)', '.bus_out_if_req_attr(arb_out_bus_if_req_attr)')
    c = c.replace('.bus_out_req_tag(arb_out_bus_if_req_tag_uuid)', '.bus_out_if_req_tag(arb_out_bus_if_req_tag_uuid)')
    c = c.replace('.bus_out_req_ready(arb_out_bus_if_req_ready)', '.bus_out_if_req_ready(arb_out_bus_if_req_ready)')
    c = c.replace('.bus_out_rsp_valid(arb_out_bus_if_rsp_valid)', '.bus_out_if_rsp_valid(arb_out_bus_if_rsp_valid)')
    c = c.replace('.bus_out_rsp_data(arb_out_bus_if_rsp_data)', '.bus_out_if_rsp_data(arb_out_bus_if_rsp_data)')
    c = c.replace('.bus_out_rsp_tag(arb_out_bus_if_rsp_tag_uuid)', '.bus_out_if_rsp_tag(arb_out_bus_if_rsp_tag_uuid)')
    c = c.replace('.bus_out_rsp_ready(arb_out_bus_if_rsp_ready)', '.bus_out_if_rsp_ready(arb_out_bus_if_rsp_ready)')
    
    with open(fname, 'w') as f:
        f.write(c)
    print(f"  Fixed {fname}")
