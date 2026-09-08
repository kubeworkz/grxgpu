#!/usr/bin/env python3
"""Fix VX_dp_ram stub and add LMEM_DMA_ADDR_WIDTH to gpu_pkg_stub."""
import os
os.chdir("/tmp/dxa_synth")

# Fix VX_dp_ram stub
with open("vortex_stubs.sv") as f:
    content = f.read()

start = content.find("module VX_dp_ram")
end = content.find("endmodule", start) + len("endmodule")

new_dpram = """module VX_dp_ram #(
    parameter DATAW       = 1,
    parameter SIZE        = 1,
    parameter WRENW       = 1,
    parameter OUT_REG     = 0,
    parameter LUTRAM      = 0,
    parameter RDW_MODE    = "W",
    parameter RADDR_REG   = 0,
    parameter RADDR_RESET = 0,
    parameter RDW_ASSERT  = 0,
    parameter RESET_RAM   = 0,
    parameter INIT_ENABLE = 0,
    parameter INIT_FILE   = "",
    parameter INIT_VALUE  = 0,
    parameter ADDRW       = (SIZE > 1) ? $clog2(SIZE) : 1
) (
    input  wire             clk,
    input  wire             reset,
    input  wire             read,
    input  wire             write,
    input  wire [WRENW-1:0] wren,
    input  wire [ADDRW-1:0] waddr,
    input  wire [DATAW-1:0] wdata,
    input  wire [ADDRW-1:0] raddr,
    output wire [DATAW-1:0] rdata
);
    reg [DATAW-1:0] ram [0:SIZE-1];
    always @(posedge clk) begin
        if (write) ram[waddr] <= wdata;
    end
    assign rdata = ram[raddr];
endmodule"""

content = content[:start] + new_dpram + content[end:]
with open("vortex_stubs.sv", "w") as f:
    f.write(content)
print("VX_dp_ram stub fixed")

# Fix gpu_pkg_stub to add LMEM_DMA_ADDR_WIDTH
with open("vx_gpu_pkg_stub.sv") as f:
    content = f.read()

# Add LMEM_DMA_ADDR_WIDTH before endpackage
new_param = """
    // DXA address width: derived from LMEM config
    localparam LMEM_DMA_ADDR_WIDTH = 12;
"""
content = content.replace("endpackage", new_param + "\nendpackage")
with open("vx_gpu_pkg_stub.sv", "w") as f:
    f.write(content)
print("vx_gpu_pkg_stub.sv updated with LMEM_DMA_ADDR_WIDTH")
