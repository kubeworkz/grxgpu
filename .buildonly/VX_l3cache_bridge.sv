`include "VX_define.vh"
`include "VX_cache_define.vh"

// Interface-preserving bridge for the top-level L3 cache. The cache itself is
// compiled as VX_l3cache_flat, keeping Vortex.sv's interface connection shape.
module VX_l3cache_bridge import VX_gpu_pkg::*; #(
    parameter `STRING INSTANCE_ID    = "",

    parameter TAG_SEL_IDX           = 0,

    parameter NUM_REQS              = 4,
    parameter MEM_PORTS             = 1,

    parameter CACHE_SIZE            = 4096,
    parameter LINE_SIZE             = 64,
    parameter NUM_BANKS             = 4,
    parameter NUM_WAYS              = 4,
    parameter WORD_SIZE             = 16,
    parameter SECTOR_SIZE           = LINE_SIZE,

    parameter CRSQ_SIZE             = 0,
    parameter MSHR_SIZE             = 16,
    parameter MRSQ_SIZE             = 4,
    parameter MREQ_SIZE             = 0,

    parameter LATENCY               = 2,

    parameter WRITE_ENABLE          = 1,
    parameter WRITEBACK             = 0,
    parameter DIRTY_BYTES           = 0,
    parameter REPL_POLICY           = `CS_REPL_FIFO,

    parameter TAG_WIDTH             = UUID_WIDTH + 1,

    parameter NC_ENABLE             = 0,
    parameter PASSTHRU              = 0,

    parameter CORE_OUT_BUF          = 3,
    parameter MEM_OUT_BUF           = 3,

    parameter IS_LLC                = 0,
    parameter AMO_ENABLE            = 0
) (
    input  wire clk,
    input  wire reset,

`ifdef PERF_ENABLE
    output cache_perf_t cache_perf,
`endif

    VX_mem_bus_if.slave core_bus_if[NUM_REQS],
    VX_mem_bus_if.master mem_bus_if[MEM_PORTS]
);

wire [NUM_REQS-1:0]                                  core_req_valid;
wire [NUM_REQS-1:0][L2_SECTOR_SIZE*8-1:0]            core_req_data;
wire [NUM_REQS-1:0][`VX_CFG_MEM_ADDR_WIDTH-`CLOG2(L2_SECTOR_SIZE)-1:0] core_req_addr;
wire [NUM_REQS-1:0][L2_SECTOR_SIZE-1:0]              core_req_byteen;
wire [NUM_REQS-1:0][`UP(MEM_ATTR_WIDTH)-1:0]         core_req_attr;
wire [NUM_REQS-1:0]                                  core_req_rw;
wire [NUM_REQS-1:0][UUID_WIDTH-1:0]                  core_req_tag_uuid;
wire [NUM_REQS-1:0][TAG_WIDTH-UUID_WIDTH-1:0]        core_req_tag_value;
wire [NUM_REQS-1:0]                                  core_req_ready;
wire [NUM_REQS-1:0]                                  core_rsp_valid;
wire [NUM_REQS-1:0][L2_SECTOR_SIZE*8-1:0]            core_rsp_data;
wire [NUM_REQS-1:0][UUID_WIDTH-1:0]                  core_rsp_tag_uuid;
wire [NUM_REQS-1:0][TAG_WIDTH-UUID_WIDTH-1:0]        core_rsp_tag_value;
wire [NUM_REQS-1:0]                                  core_rsp_ready;

wire [MEM_PORTS-1:0]                                 mem_req_valid;
wire [MEM_PORTS-1:0][L3_SECTOR_SIZE*8-1:0]           mem_req_data;
wire [MEM_PORTS-1:0][`VX_CFG_MEM_ADDR_WIDTH-`CLOG2(L3_SECTOR_SIZE)-1:0] mem_req_addr;
wire [MEM_PORTS-1:0][L3_SECTOR_SIZE-1:0]             mem_req_byteen;
wire [MEM_PORTS-1:0][`UP(MEM_ATTR_WIDTH)-1:0]        mem_req_attr;
wire [MEM_PORTS-1:0]                                 mem_req_rw;
wire [MEM_PORTS-1:0][UUID_WIDTH-1:0]                 mem_req_tag_uuid;
wire [MEM_PORTS-1:0][L3_MEM_TAG_WIDTH-UUID_WIDTH-1:0] mem_req_tag_value;
wire [MEM_PORTS-1:0]                                 mem_req_ready;
wire [MEM_PORTS-1:0]                                 mem_rsp_valid;
wire [MEM_PORTS-1:0][L3_SECTOR_SIZE*8-1:0]           mem_rsp_data;
wire [MEM_PORTS-1:0][UUID_WIDTH-1:0]                 mem_rsp_tag_uuid;
wire [MEM_PORTS-1:0][L3_MEM_TAG_WIDTH-UUID_WIDTH-1:0] mem_rsp_tag_value;
wire [MEM_PORTS-1:0]                                 mem_rsp_ready;

for (genvar i = 0; i < NUM_REQS; ++i) begin : g_core_bus
    assign core_req_valid[i]          = core_bus_if[i].req_valid;
    assign core_req_addr[i]           = core_bus_if[i].req_data.addr;
    assign core_req_data[i]           = core_bus_if[i].req_data.data;
    assign core_req_byteen[i]         = core_bus_if[i].req_data.byteen;
    assign core_req_attr[i]           = core_bus_if[i].req_data.attr;
    assign core_req_rw[i]             = core_bus_if[i].req_data.rw;
    assign core_req_tag_uuid[i]       = core_bus_if[i].req_data.tag.uuid;
    assign core_req_tag_value[i]      = core_bus_if[i].req_data.tag.value;

    assign core_bus_if[i].req_ready       = core_req_ready[i];
    assign core_bus_if[i].rsp_valid       = core_rsp_valid[i];
    assign core_bus_if[i].rsp_data.data   = core_rsp_data[i];
    assign core_bus_if[i].rsp_data.tag.uuid  = core_rsp_tag_uuid[i];
    assign core_bus_if[i].rsp_data.tag.value = core_rsp_tag_value[i];

    assign core_rsp_ready[i]          = core_bus_if[i].rsp_ready;
end

for (genvar i = 0; i < MEM_PORTS; ++i) begin : g_mem_bus
    assign mem_bus_if[i].req_valid        = mem_req_valid[i];
    assign mem_bus_if[i].req_data.addr    = mem_req_addr[i];
    assign mem_bus_if[i].req_data.data    = mem_req_data[i];
    assign mem_bus_if[i].req_data.byteen  = mem_req_byteen[i];
    assign mem_bus_if[i].req_data.attr    = mem_req_attr[i];
    assign mem_bus_if[i].req_data.rw      = mem_req_rw[i];
    assign mem_bus_if[i].req_data.tag.uuid  = mem_req_tag_uuid[i];
    assign mem_bus_if[i].req_data.tag.value = mem_req_tag_value[i];

    assign mem_req_ready[i]               = mem_bus_if[i].req_ready;
    assign mem_rsp_valid[i]               = mem_bus_if[i].rsp_valid;
    assign mem_rsp_data[i]                = mem_bus_if[i].rsp_data.data;
    assign mem_rsp_tag_uuid[i]            = mem_bus_if[i].rsp_data.tag.uuid;
    assign mem_rsp_tag_value[i]           = mem_bus_if[i].rsp_data.tag.value;

    assign mem_bus_if[i].rsp_ready        = mem_rsp_ready[i];
end

VX_l3cache_flat #(
    .INSTANCE_ID    (INSTANCE_ID),
    .TAG_SEL_IDX    (TAG_SEL_IDX),
    .NUM_REQS       (NUM_REQS),
    .MEM_PORTS      (MEM_PORTS),
    .CACHE_SIZE     (CACHE_SIZE),
    .LINE_SIZE      (LINE_SIZE),
    .SECTOR_SIZE    (SECTOR_SIZE),
    .NUM_BANKS      (NUM_BANKS),
    .NUM_WAYS       (NUM_WAYS),
    .WORD_SIZE      (WORD_SIZE),
    .CRSQ_SIZE      (CRSQ_SIZE),
    .MSHR_SIZE      (MSHR_SIZE),
    .MRSQ_SIZE      (MRSQ_SIZE),
    .MREQ_SIZE      (MREQ_SIZE),
    .LATENCY        (LATENCY),
    .WRITE_ENABLE   (WRITE_ENABLE),
    .WRITEBACK      (WRITEBACK),
    .DIRTY_BYTES    (DIRTY_BYTES),
    .REPL_POLICY    (REPL_POLICY),
    .TAG_WIDTH      (TAG_WIDTH),
    .NC_ENABLE      (NC_ENABLE),
    .PASSTHRU       (PASSTHRU),
    .CORE_OUT_BUF   (CORE_OUT_BUF),
    .MEM_OUT_BUF    (MEM_OUT_BUF),
    .IS_LLC         (IS_LLC),
    .AMO_ENABLE     (AMO_ENABLE)
) flat (
    .clk                 (clk),
    .reset               (reset),

`ifdef PERF_ENABLE
    .cache_perf          (cache_perf),
`endif

    .core_req_valid      (core_req_valid),
    .core_req_addr       (core_req_addr),
    .core_req_data       (core_req_data),
    .core_req_byteen     (core_req_byteen),
    .core_req_attr       (core_req_attr),
    .core_req_rw         (core_req_rw),
    .core_req_tag_uuid   (core_req_tag_uuid),
    .core_req_tag_value  (core_req_tag_value),
    .core_req_ready      (core_req_ready),
    .core_rsp_valid      (core_rsp_valid),
    .core_rsp_data       (core_rsp_data),
    .core_rsp_tag_uuid   (core_rsp_tag_uuid),
    .core_rsp_tag_value  (core_rsp_tag_value),
    .core_rsp_ready      (core_rsp_ready),

    .mem_req_valid       (mem_req_valid),
    .mem_req_addr        (mem_req_addr),
    .mem_req_data        (mem_req_data),
    .mem_req_byteen      (mem_req_byteen),
    .mem_req_attr        (mem_req_attr),
    .mem_req_rw          (mem_req_rw),
    .mem_req_tag_uuid    (mem_req_tag_uuid),
    .mem_req_tag_value   (mem_req_tag_value),
    .mem_req_ready       (mem_req_ready),
    .mem_rsp_valid       (mem_rsp_valid),
    .mem_rsp_data        (mem_rsp_data),
    .mem_rsp_tag_uuid    (mem_rsp_tag_uuid),
    .mem_rsp_tag_value   (mem_rsp_tag_value),
    .mem_rsp_ready       (mem_rsp_ready)
);

endmodule
