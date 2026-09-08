// Minimal VX_gpu_pkg stub for DXA synthesis
package VX_gpu_pkg;

  // Width constants matching G100 config
  localparam UUID_WIDTH = 32;
  localparam NW_WIDTH = 4;
  localparam NCTA_WIDTH = 8;
  localparam PC_BITS = 16;
  localparam NUM_XREGS = 32;
  localparam NUM_REGS_BITS = 5;
  localparam BYTESEL_BITS = 2;
  localparam INST_OP_BITS = 4;

  // Execute header type used by DXA
  typedef struct packed {
    logic [UUID_WIDTH-1:0]  uuid;
    logic [NW_WIDTH-1:0]    wid;
    logic [NCTA_WIDTH-1:0]  cta_id;
    logic [3:0]             tmask;
    logic [1:0]             pid;
    logic                   sop;
    logic                   eop;
    logic [PC_BITS-1:0]     PC;
    logic                   wb;
    logic [NUM_XREGS-1:0]   wr_xregs;
    logic [NUM_REGS_BITS-1:0] rd;
    logic [BYTESEL_BITS-1:0] bytesel;
  } sfu_header_t;

  // op_args union (simplified for synthesis)
  typedef struct packed {
    logic [31:0] a;
    logic [31:0] b;
    logic [31:0] c;
  } op_args_t;

  // Execute type
  typedef struct packed {
    sfu_header_t           header;
    logic [INST_OP_BITS-1:0] op_type;
    op_args_t              op_args;
    logic [3:0][31:0]      rs1_data;
    logic [3:0][31:0]      rs2_data;
    logic [3:0][31:0]      rs3_data;
  } sfu_execute_t;

  // Result type
  typedef struct packed {
    sfu_header_t           header;
    logic [3:0][31:0]      data;
  } sfu_result_t;

endpackage
