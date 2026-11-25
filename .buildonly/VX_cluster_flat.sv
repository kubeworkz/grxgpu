`include "VX_define.vh"

// Flat hierarchical-block facade for VX_cluster_impl. Verilator cannot put
// interfaces or modports on a hierarchy-block boundary, so this module
// exposes the cluster interfaces as packed ports and recreates them internally.
module VX_cluster_flat import VX_gpu_pkg::*; #(
    parameter CLUSTER_ID = 0,
    parameter `STRING INSTANCE_ID = "",
    parameter MEM_BUS_DATA_WIDTH = L2_SECTOR_SIZE * 8,
    parameter MEM_BUS_ADDR_WIDTH = `VX_CFG_MEM_ADDR_WIDTH - `CLOG2(L2_SECTOR_SIZE),
    parameter MEM_BUS_ATTR_WIDTH = `UP(MEM_ATTR_WIDTH),
    parameter MEM_BUS_TAG_VALUE_WIDTH = L3_TAG_WIDTH - UUID_WIDTH
) (
    `SCOPE_IO_DECL

    input  wire                 clk,
    input  wire                 reset,

`ifdef PERF_ENABLE
    input  sysmem_perf_t        sysmem_perf,
`endif

    // DCR slave
    input  wire                 dcr_bus_req_valid,
    input  VX_gpu_pkg::dcr_req_t dcr_bus_req_data,
    output wire                 dcr_bus_rsp_valid,
    output VX_gpu_pkg::dcr_rsp_t dcr_bus_rsp_data,

    // Memory master
    output wire [L2_MEM_PORTS-1:0]                              mem_bus_req_valid,
    output wire [L2_MEM_PORTS-1:0][MEM_BUS_ADDR_WIDTH-1:0]      mem_bus_req_addr,
    output wire [L2_MEM_PORTS-1:0][MEM_BUS_DATA_WIDTH-1:0]      mem_bus_req_data,
    output wire [L2_MEM_PORTS-1:0][L2_SECTOR_SIZE-1:0]          mem_bus_req_byteen,
    output wire [L2_MEM_PORTS-1:0][MEM_BUS_ATTR_WIDTH-1:0]      mem_bus_req_attr,
    output wire [L2_MEM_PORTS-1:0]                              mem_bus_req_rw,
    output wire [L2_MEM_PORTS-1:0][UUID_WIDTH-1:0]              mem_bus_req_tag_uuid,
    output wire [L2_MEM_PORTS-1:0][MEM_BUS_TAG_VALUE_WIDTH-1:0] mem_bus_req_tag_value,
    input  wire [L2_MEM_PORTS-1:0]                              mem_bus_req_ready,
    input  wire [L2_MEM_PORTS-1:0]                              mem_bus_rsp_valid,
    input  wire [L2_MEM_PORTS-1:0][MEM_BUS_DATA_WIDTH-1:0]      mem_bus_rsp_data,
    input  wire [L2_MEM_PORTS-1:0][UUID_WIDTH-1:0]              mem_bus_rsp_tag_uuid,
    input  wire [L2_MEM_PORTS-1:0][MEM_BUS_TAG_VALUE_WIDTH-1:0] mem_bus_rsp_tag_value,
    output wire [L2_MEM_PORTS-1:0]                              mem_bus_rsp_ready,

    // KMU slave
    input  wire                 kmu_bus_valid,
    input  VX_gpu_pkg::kmu_req_t kmu_bus_data,
    output wire                 kmu_bus_ready,

    // Global barrier master
    output wire                 gbar_bus_req_valid,
    output VX_gpu_pkg::gbar_req_t gbar_bus_req_data,
    input  wire                 gbar_bus_req_ready,
    input  wire                 gbar_bus_rsp_valid,
    input  VX_gpu_pkg::gbar_rsp_t gbar_bus_rsp_data,
    output wire                 gbar_bus_rsp_ready,

`ifdef VX_CFG_EXT_RASTER_ENABLE
    // Delegated raster launch slave
    input  wire                 raster_launch_valid,
    output wire                 raster_launch_ready,
`endif

    output wire                 busy
);

VX_dcr_bus_if dcr_bus_if();
VX_mem_bus_if #(
    .DATA_SIZE (L2_SECTOR_SIZE),
    .TAG_WIDTH (L3_TAG_WIDTH)
) mem_bus_if[L2_MEM_PORTS]();
VX_kmu_bus_if kmu_bus_if[1]();
VX_gbar_bus_if gbar_bus_if();
`ifdef VX_CFG_EXT_RASTER_ENABLE
VX_raster_launch_if raster_launch_if[1]();
`endif

VX_cluster_impl #(
    .CLUSTER_ID  (CLUSTER_ID),
    .INSTANCE_ID (INSTANCE_ID)
) impl (
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

    .dcr_bus_if         (dcr_bus_if),
    .mem_bus_if         (mem_bus_if),
    .kmu_bus_if         (kmu_bus_if),
    .gbar_bus_if        (gbar_bus_if),

`ifdef VX_CFG_EXT_RASTER_ENABLE
    .raster_launch_if   (raster_launch_if),
`endif

    .busy               (busy)
);

assign dcr_bus_if.req_valid = dcr_bus_req_valid;
assign dcr_bus_if.req_data  = dcr_bus_req_data;
assign dcr_bus_rsp_valid    = dcr_bus_if.rsp_valid;
assign dcr_bus_rsp_data     = dcr_bus_if.rsp_data;

assign kmu_bus_if[0].valid = kmu_bus_valid;
assign kmu_bus_if[0].data  = kmu_bus_data;
assign kmu_bus_ready       = kmu_bus_if[0].ready;

assign gbar_bus_req_valid = gbar_bus_if.req_valid;
assign gbar_bus_req_data  = gbar_bus_if.req_data;
assign gbar_bus_if.req_ready = gbar_bus_req_ready;
assign gbar_bus_if.rsp_valid = gbar_bus_rsp_valid;
assign gbar_bus_if.rsp_data  = gbar_bus_rsp_data;
assign gbar_bus_rsp_ready = gbar_bus_if.rsp_ready;

`ifdef VX_CFG_EXT_RASTER_ENABLE
assign raster_launch_if[0].valid = raster_launch_valid;
assign raster_launch_ready       = raster_launch_if[0].ready;
`endif

for (genvar i = 0; i < L2_MEM_PORTS; ++i) begin : g_mem_bus
    assign mem_bus_req_valid[i]          = mem_bus_if[i].req_valid;
    assign mem_bus_req_addr[i]           = mem_bus_if[i].req_data.addr;
    assign mem_bus_req_data[i]           = mem_bus_if[i].req_data.data;
    assign mem_bus_req_byteen[i]         = mem_bus_if[i].req_data.byteen;
    assign mem_bus_req_attr[i]           = mem_bus_if[i].req_data.attr;
    assign mem_bus_req_rw[i]             = mem_bus_if[i].req_data.rw;
    assign mem_bus_req_tag_uuid[i]       = mem_bus_if[i].req_data.tag.uuid;
    assign mem_bus_req_tag_value[i]      = mem_bus_if[i].req_data.tag.value;

    assign mem_bus_if[i].req_ready       = mem_bus_req_ready[i];
    assign mem_bus_if[i].rsp_valid       = mem_bus_rsp_valid[i];
    assign mem_bus_if[i].rsp_data.data   = mem_bus_rsp_data[i];
    assign mem_bus_if[i].rsp_data.tag.uuid  = mem_bus_rsp_tag_uuid[i];
    assign mem_bus_if[i].rsp_data.tag.value = mem_bus_rsp_tag_value[i];

    assign mem_bus_rsp_ready[i]          = mem_bus_if[i].rsp_ready;
end

endmodule
