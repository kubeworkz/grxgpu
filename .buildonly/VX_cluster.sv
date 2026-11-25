`include "VX_define.vh"

// Interface-preserving facade. The actual cluster is compiled as the flat
// hierarchical block VX_cluster_flat; this module keeps Vortex.sv unchanged.
module VX_cluster import VX_gpu_pkg::*; #(
    parameter CLUSTER_ID = 0,
    parameter `STRING INSTANCE_ID = ""
) (
    `SCOPE_IO_DECL

    input  wire                 clk,
    input  wire                 reset,

`ifdef PERF_ENABLE
    input  sysmem_perf_t        sysmem_perf,
`endif

    VX_dcr_bus_if.slave         dcr_bus_if,
    VX_mem_bus_if               mem_bus_if [L2_MEM_PORTS],
    VX_kmu_bus_if.slave         kmu_bus_if[1],
    VX_gbar_bus_if.master       gbar_bus_if,

`ifdef VX_CFG_EXT_RASTER_ENABLE
    VX_raster_launch_if.slave   raster_launch_if[1],
`endif

    output wire                 busy
);

localparam MEM_BUS_DATA_WIDTH      = L2_SECTOR_SIZE * 8;
localparam MEM_BUS_ADDR_WIDTH      = `VX_CFG_MEM_ADDR_WIDTH - `CLOG2(L2_SECTOR_SIZE);
localparam MEM_BUS_ATTR_WIDTH      = `UP(MEM_ATTR_WIDTH);
localparam MEM_BUS_TAG_VALUE_WIDTH = L3_TAG_WIDTH - UUID_WIDTH;

wire [L2_MEM_PORTS-1:0]                              mem_bus_req_valid;
wire [L2_MEM_PORTS-1:0][MEM_BUS_ADDR_WIDTH-1:0]      mem_bus_req_addr;
wire [L2_MEM_PORTS-1:0][MEM_BUS_DATA_WIDTH-1:0]      mem_bus_req_data;
wire [L2_MEM_PORTS-1:0][L2_SECTOR_SIZE-1:0]          mem_bus_req_byteen;
wire [L2_MEM_PORTS-1:0][MEM_BUS_ATTR_WIDTH-1:0]      mem_bus_req_attr;
wire [L2_MEM_PORTS-1:0]                              mem_bus_req_rw;
wire [L2_MEM_PORTS-1:0][UUID_WIDTH-1:0]              mem_bus_req_tag_uuid;
wire [L2_MEM_PORTS-1:0][MEM_BUS_TAG_VALUE_WIDTH-1:0] mem_bus_req_tag_value;
wire [L2_MEM_PORTS-1:0]                              mem_bus_req_ready;
wire [L2_MEM_PORTS-1:0]                              mem_bus_rsp_valid;
wire [L2_MEM_PORTS-1:0][MEM_BUS_DATA_WIDTH-1:0]      mem_bus_rsp_data;
wire [L2_MEM_PORTS-1:0][UUID_WIDTH-1:0]              mem_bus_rsp_tag_uuid;
wire [L2_MEM_PORTS-1:0][MEM_BUS_TAG_VALUE_WIDTH-1:0] mem_bus_rsp_tag_value;
wire [L2_MEM_PORTS-1:0]                              mem_bus_rsp_ready;

// The flat block exposes the cluster's memory-master port, so this side drives
// requests out and takes responses in - the reverse of the mirror block inside
// VX_cluster_flat, which reads its own local interface.
for (genvar i = 0; i < L2_MEM_PORTS; ++i) begin : g_mem_bus
    assign mem_bus_if[i].req_valid          = mem_bus_req_valid[i];
    assign mem_bus_if[i].req_data.addr      = mem_bus_req_addr[i];
    assign mem_bus_if[i].req_data.data      = mem_bus_req_data[i];
    assign mem_bus_if[i].req_data.byteen    = mem_bus_req_byteen[i];
    assign mem_bus_if[i].req_data.attr      = mem_bus_req_attr[i];
    assign mem_bus_if[i].req_data.rw        = mem_bus_req_rw[i];
    assign mem_bus_if[i].req_data.tag.uuid  = mem_bus_req_tag_uuid[i];
    assign mem_bus_if[i].req_data.tag.value = mem_bus_req_tag_value[i];

    assign mem_bus_req_ready[i]     = mem_bus_if[i].req_ready;
    assign mem_bus_rsp_valid[i]     = mem_bus_if[i].rsp_valid;
    assign mem_bus_rsp_data[i]      = mem_bus_if[i].rsp_data.data;
    assign mem_bus_rsp_tag_uuid[i]  = mem_bus_if[i].rsp_data.tag.uuid;
    assign mem_bus_rsp_tag_value[i] = mem_bus_if[i].rsp_data.tag.value;

    assign mem_bus_if[i].rsp_ready = mem_bus_rsp_ready[i];
end

VX_cluster_flat #(
    .CLUSTER_ID  (CLUSTER_ID),
    .INSTANCE_ID (INSTANCE_ID)
) flat (
`ifdef SCOPE
    .scope_reset        (scope_reset),
    .scope_bus_in       (scope_bus_in),
    .scope_bus_out      (scope_bus_out),
`endif

    .clk                (clk),
    .reset              (reset),

`ifdef PERF_ENABLE
    .sysmem_perf        (sysmem_perf),
`endif

    .dcr_bus_req_valid  (dcr_bus_if.req_valid),
    .dcr_bus_req_data   (dcr_bus_if.req_data),
    .dcr_bus_rsp_valid  (dcr_bus_if.rsp_valid),
    .dcr_bus_rsp_data   (dcr_bus_if.rsp_data),

    .mem_bus_req_valid          (mem_bus_req_valid),
    .mem_bus_req_addr           (mem_bus_req_addr),
    .mem_bus_req_data           (mem_bus_req_data),
    .mem_bus_req_byteen         (mem_bus_req_byteen),
    .mem_bus_req_attr           (mem_bus_req_attr),
    .mem_bus_req_rw             (mem_bus_req_rw),
    .mem_bus_req_tag_uuid       (mem_bus_req_tag_uuid),
    .mem_bus_req_tag_value      (mem_bus_req_tag_value),
    .mem_bus_req_ready          (mem_bus_req_ready),
    .mem_bus_rsp_valid          (mem_bus_rsp_valid),
    .mem_bus_rsp_data           (mem_bus_rsp_data),
    .mem_bus_rsp_tag_uuid       (mem_bus_rsp_tag_uuid),
    .mem_bus_rsp_tag_value      (mem_bus_rsp_tag_value),
    .mem_bus_rsp_ready          (mem_bus_rsp_ready),

    .kmu_bus_valid      (kmu_bus_if[0].valid),
    .kmu_bus_data       (kmu_bus_if[0].data),
    .kmu_bus_ready      (kmu_bus_if[0].ready),

    .gbar_bus_req_valid (gbar_bus_if.req_valid),
    .gbar_bus_req_data  (gbar_bus_if.req_data),
    .gbar_bus_req_ready (gbar_bus_if.req_ready),
    .gbar_bus_rsp_valid (gbar_bus_if.rsp_valid),
    .gbar_bus_rsp_data  (gbar_bus_if.rsp_data),
    .gbar_bus_rsp_ready (gbar_bus_if.rsp_ready),

`ifdef VX_CFG_EXT_RASTER_ENABLE
    .raster_launch_valid (raster_launch_if[0].valid),
    .raster_launch_ready (raster_launch_if[0].ready),
`endif

    .busy               (busy)
);

endmodule
