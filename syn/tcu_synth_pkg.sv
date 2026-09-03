// TCU Synthesis Package — standalone replacement for VX_gpu_pkg + VX_tcu_pkg
// Provides all constants and types needed by TFR modules
// Generated from VX_config.vh (G100 single-core config)

`ifndef TCU_SYNTH_PKG_VH
`define TCU_SYNTH_PKG_VH

// ---- Configuration constants (from VX_config.vh) ----
`define VX_CFG_XLEN 32
`define VX_CFG_NUM_THREADS 4
`define VX_CFG_NUM_WARPS 4

// TCU feature enables (G100 config)
`define VX_CFG_TCU_WGMMA_ENABLE
`define VX_CFG_TCU_WGMMA_ENABLED 1
`define VX_CFG_TCU_SPARSE_ENABLED 0
`define VX_CFG_TCU_FP8_ENABLED 1
`define VX_CFG_TCU_FP16_ENABLED 1
`define VX_CFG_TCU_TF32_ENABLED 1
`define VX_CFG_TCU_MXFP4_ENABLED 1
`define VX_CFG_TCU_NVFP4_ENABLED 1

package TCU_synth_pkg;

    // ---- Format IDs ----
    localparam TCU_FP32_ID  = 0;
    localparam TCU_TF32_ID  = 1;
    localparam TCU_FP16_ID  = 2;
    localparam TCU_BF16_ID  = 3;
    localparam TCU_FP8_ID   = 4;
    localparam TCU_BF8_ID   = 5;
    localparam TCU_MXFP8_ID = 8;
    localparam TCU_MXBF8_ID = 9;
    localparam TCU_MXFP4_ID = 10;
    localparam TCU_NVFP4_ID = 11;
    localparam TCU_I32_ID   = 16;
    localparam TCU_I8_ID    = 17;
    localparam TCU_U8_ID    = 18;
    localparam TCU_I4_ID    = 19;
    localparam TCU_U4_ID    = 20;
    localparam TCU_FMT_WIDTH = 5;

    // ---- Tile dimensions (NT=4, NR=32, WGMMA config) ----
    localparam TCU_NT = 4;   // VX_CFG_NUM_THREADS
    localparam TCU_NR = 32;

    localparam TCU_TILE_CAP = 128;  // NT * NR
    localparam TCU_LG_TILE_CAP = 7; // clog2(128)
    localparam TCU_TILE_EN = 3;
    localparam TCU_TILE_EM = 4;

    localparam TCU_TILE_M = 16;  // 1 << 4
    localparam TCU_TILE_N = 8;   // 1 << 3
    localparam TCU_TILE_K = 8;   // 128 / 16

    localparam TCU_BLOCK_CAP = 4;  // NT
    localparam TCU_LG_BLOCK_CAP = 2;
    localparam TCU_BLOCK_EN = 1;
    localparam TCU_BLOCK_EM = 1;

    localparam TCU_TC_M = 2;  // 1 << 1
    localparam TCU_TC_N = 2;  // 1 << 1
    localparam TCU_TC_K = 2;  // 4 / 2

    localparam TCU_M_STEPS = 8;  // 16/2
    localparam TCU_N_STEPS = 4;  // 8/2
    localparam TCU_K_STEPS = 4;  // 8/2

    // WGMMA tile dimensions
    localparam TCU_WG_TILE_M = 4;   // 2 * tcM
    localparam TCU_WG_TILE_K = 4;   // 2 * tcK
    localparam TCU_WG_FEDP_K = 2;   // tcK (no FEDP2K)
    localparam TCU_WG_TILE_N = 32;  // (NR * NT) / WG_TILE_M

    localparam TCU_WG_M_STEPS = 2;  // 4/2
    localparam TCU_WG_N_STEPS = 16; // 32/2
    localparam TCU_WG_K_STEPS = 2;  // 4/2

    localparam TCU_WG_UOPS = 64;    // 2*16*2

    // Register counts
    localparam TCU_NRA = 32;  // (16*8)/4
    localparam TCU_NRB = 16;  // (8*8)/4
    localparam TCU_NRC = 32;  // (16*8)/4

    localparam TCU_NRA_WIDTH = 4;   // clog2(16) for A sub-blocks
    localparam TCU_NRB_WIDTH = 4;
    localparam TCU_NRC_WIDTH = 5;

    // Exponent bits
    localparam TCU_EXP_BITS = 10;  // TF32/FP16

    // MX scale
    localparam TCU_MX_MAX_SF = 1;

    localparam TCU_MIN_FMT_WIDTH = 4;
    localparam TCU_MAX_ELT_RATIO = 8;  // 32/4

    localparam TCU_MAX_META_ROW_WIDTH   = 64;
    localparam TCU_MAX_META_BLOCK_WIDTH = 256;

    // ---- Struct types ----

    typedef struct packed {
        logic is_zero;
        logic is_sub;
        logic is_inf;
        logic is_nan;
    } fedp_class_t;

    typedef struct packed {
        logic is_inf;
        logic is_nan;
        logic sign;
    } fedp_excep_t;

    // ---- Format utility functions ----

    function automatic int exp_bits(input int fmt);
        case (fmt)
            TCU_FP32_ID: return 8;
            TCU_FP16_ID: return 5;
            TCU_BF16_ID: return 8;
            TCU_FP8_ID:  return 4;
            TCU_BF8_ID:  return 5;
            TCU_TF32_ID: return 8;
            default:     return 0;
        endcase
    endfunction

    function automatic int sig_bits(input int fmt);
        case (fmt)
            TCU_FP32_ID: return 23;
            TCU_FP16_ID: return 10;
            TCU_BF16_ID: return 7;
            TCU_FP8_ID:  return 3;
            TCU_BF8_ID:  return 2;
            TCU_TF32_ID: return 10;
            default:     return 0;
        endcase
    endfunction

    function automatic int sign_pos(input int fmt);
        case (fmt)
            TCU_FP32_ID: return 31;
            TCU_FP16_ID: return 15;
            TCU_BF16_ID: return 15;
            TCU_FP8_ID:  return 7;
            TCU_BF8_ID:  return 7;
            TCU_TF32_ID: return 18;
            default:     return 0;
        endcase
    endfunction

    function automatic int unsigned tcu_fmt_width(input logic [TCU_FMT_WIDTH-1:0] fmt);
        case (fmt)
            TCU_FP16_ID, TCU_BF16_ID: return 16;
            TCU_MXFP4_ID, TCU_NVFP4_ID, TCU_I4_ID, TCU_U4_ID: return 4;
            TCU_FP8_ID, TCU_BF8_ID, TCU_I8_ID, TCU_U8_ID, TCU_MXFP8_ID, TCU_MXBF8_ID: return 8;
            TCU_FP32_ID, TCU_I32_ID, TCU_TF32_ID: return 32;
            default: return 0;
        endcase
    endfunction

    function automatic logic tcu_fmt_is_mx(input logic [TCU_FMT_WIDTH-1:0] fmt);
        case (fmt)
            TCU_MXFP8_ID, TCU_MXBF8_ID, TCU_MXFP4_ID, TCU_NVFP4_ID: return 1'b1;
            default: return 1'b0;
        endcase
    endfunction

endpackage

`endif // TCU_SYNTH_PKG_VH
