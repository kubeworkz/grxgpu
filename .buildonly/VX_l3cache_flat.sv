`include "VX_define.vh"
`include "VX_cache_define.vh"

// Flat hierarchical-block facade for the top-level L3 cache wrapper. Verilator
// cannot put interfaces or modports on a hierarchy-block boundary, so the L3
// buses are exposed as packed ports and recreated internally.
module VX_l3cache_flat import VX_gpu_pkg::*; #(
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

    // Core-side bus
    input  wire [NUM_REQS-1:0]                                  core_req_valid,
    input  wire [NUM_REQS-1:0][L2_SECTOR_SIZE*8-1:0]            core_req_data,
    input  wire [NUM_REQS-1:0][`VX_CFG_MEM_ADDR_WIDTH-`CLOG2(L2_SECTOR_SIZE)-1:0] core_req_addr,
    input  wire [NUM_REQS-1:0][L2_SECTOR_SIZE-1:0]              core_req_byteen,
    input  wire [NUM_REQS-1:0][`UP(MEM_ATTR_WIDTH)-1:0]         core_req_attr,
    input  wire [NUM_REQS-1:0]                                  core_req_rw,
    input  wire [NUM_REQS-1:0][UUID_WIDTH-1:0]                  core_req_tag_uuid,
    input  wire [NUM_REQS-1:0][TAG_WIDTH-UUID_WIDTH-1:0]        core_req_tag_value,
    output wire [NUM_REQS-1:0]                                  core_req_ready,
    output wire [NUM_REQS-1:0]                                  core_rsp_valid,
    output wire [NUM_REQS-1:0][L2_SECTOR_SIZE*8-1:0]            core_rsp_data,
    output wire [NUM_REQS-1:0][UUID_WIDTH-1:0]                  core_rsp_tag_uuid,
    output wire [NUM_REQS-1:0][TAG_WIDTH-UUID_WIDTH-1:0]        core_rsp_tag_value,
    input  wire [NUM_REQS-1:0]                                  core_rsp_ready,

    // Memory-side bus
    output wire [MEM_PORTS-1:0]                                 mem_req_valid,
    output wire [MEM_PORTS-1:0][L3_SECTOR_SIZE*8-1:0]           mem_req_data,
    output wire [MEM_PORTS-1:0][`VX_CFG_MEM_ADDR_WIDTH-`CLOG2(L3_SECTOR_SIZE)-1:0] mem_req_addr,
    output wire [MEM_PORTS-1:0][L3_SECTOR_SIZE-1:0]             mem_req_byteen,
    output wire [MEM_PORTS-1:0][`UP(MEM_ATTR_WIDTH)-1:0]        mem_req_attr,
    output wire [MEM_PORTS-1:0]                                 mem_req_rw,
    output wire [MEM_PORTS-1:0][UUID_WIDTH-1:0]                 mem_req_tag_uuid,
    output wire [MEM_PORTS-1:0][L3_MEM_TAG_WIDTH-UUID_WIDTH-1:0] mem_req_tag_value,
    input  wire [MEM_PORTS-1:0]                                 mem_req_ready,
    input  wire [MEM_PORTS-1:0]                                 mem_rsp_valid,
    input  wire [MEM_PORTS-1:0][L3_SECTOR_SIZE*8-1:0]           mem_rsp_data,
    input  wire [MEM_PORTS-1:0][UUID_WIDTH-1:0]                 mem_rsp_tag_uuid,
    input  wire [MEM_PORTS-1:0][L3_MEM_TAG_WIDTH-UUID_WIDTH-1:0] mem_rsp_tag_value,
    output wire [MEM_PORTS-1:0]                                 mem_rsp_ready
);

VX_mem_bus_if #(
    .DATA_SIZE (L2_SECTOR_SIZE),
    .TAG_WIDTH (L3_TAG_WIDTH)
) core_bus_if[NUM_REQS]();

VX_mem_bus_if #(
    .DATA_SIZE (L3_SECTOR_SIZE),
    .TAG_WIDTH (L3_MEM_TAG_WIDTH)
) mem_bus_if[MEM_PORTS]();

VX_cache_wrap #(
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
) impl (
    .clk            (clk),
    .reset          (reset),

`ifdef PERF_ENABLE
    .cache_perf     (cache_perf),
`endif

    .core_bus_if    (core_bus_if),
    .mem_bus_if     (mem_bus_if)
);

for (genvar i = 0; i < NUM_REQS; ++i) begin : g_core_bus
    assign core_bus_if[i].req_valid         = core_req_valid[i];
    assign core_bus_if[i].req_data.addr     = core_req_addr[i];
    assign core_bus_if[i].req_data.data     = core_req_data[i];
    assign core_bus_if[i].req_data.byteen   = core_req_byteen[i];
    assign core_bus_if[i].req_data.attr     = core_req_attr[i];
    assign core_bus_if[i].req_data.rw       = core_req_rw[i];
    assign core_bus_if[i].req_data.tag.uuid = core_req_tag_uuid[i];
    assign core_bus_if[i].req_data.tag.value = core_req_tag_value[i];

    assign core_req_ready[i]                = core_bus_if[i].req_ready;
    assign core_rsp_valid[i]                = core_bus_if[i].rsp_valid;
    assign core_rsp_data[i]                 = core_bus_if[i].rsp_data.data;
    assign core_rsp_tag_uuid[i]             = core_bus_if[i].rsp_data.tag.uuid;
    assign core_rsp_tag_value[i]            = core_bus_if[i].rsp_data.tag.value;

    assign core_bus_if[i].rsp_ready         = core_rsp_ready[i];
end

for (genvar i = 0; i < MEM_PORTS; ++i) begin : g_mem_bus
    assign mem_req_valid[i]          = mem_bus_if[i].req_valid;
    assign mem_req_addr[i]           = mem_bus_if[i].req_data.addr;
    assign mem_req_data[i]           = mem_bus_if[i].req_data.data;
    assign mem_req_byteen[i]         = mem_bus_if[i].req_data.byteen;
    assign mem_req_attr[i]           = mem_bus_if[i].req_data.attr;
    assign mem_req_rw[i]             = mem_bus_if[i].req_data.rw;
    assign mem_req_tag_uuid[i]       = mem_bus_if[i].req_data.tag.uuid;
    assign mem_req_tag_value[i]      = mem_bus_if[i].req_data.tag.value;

    assign mem_bus_if[i].req_ready       = mem_req_ready[i];
    assign mem_bus_if[i].rsp_valid       = mem_rsp_valid[i];
    assign mem_bus_if[i].rsp_data.data   = mem_rsp_data[i];
    assign mem_bus_if[i].rsp_data.tag.uuid  = mem_rsp_tag_uuid[i];
    assign mem_bus_if[i].rsp_data.tag.value = mem_rsp_tag_value[i];

    assign mem_rsp_ready[i]          = mem_bus_if[i].rsp_ready;
end

endmodule
