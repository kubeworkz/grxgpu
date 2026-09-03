// TCU Synthesis Defines — Yosys-compatible replacement for VX_gpu_pkg + VX_tcu_pkg
// Converts all package constants to `define macros that Yosys can parse

`ifndef TCU_SYNTH_DEFS_VH
`define TCU_SYNTH_DEFS_VH

// ---- Configuration constants ----
`ifndef VX_CFG_XLEN
`define VX_CFG_XLEN 32
`endif

`ifndef VX_CFG_NUM_THREADS
`define VX_CFG_NUM_THREADS 4
`endif

`ifndef VX_CFG_NUM_WARPS
`define VX_CFG_NUM_WARPS 4
`endif

// ---- TCU Feature Enables (G100 config) ----
`define VX_CFG_TCU_WGMMA_ENABLED 1
`define VX_CFG_TCU_SPARSE_ENABLED 0
`define VX_CFG_TCU_FP8_ENABLED 1
`define VX_CFG_TCU_FP16_ENABLED 1
`define VX_CFG_TCU_TF32_ENABLED 1
`define VX_CFG_TCU_MXFP4_ENABLED 1
`define VX_CFG_TCU_NVFP4_ENABLED 1

// ---- Format IDs ----
`define TCU_FP32_ID  0
`define TCU_TF32_ID  1
`define TCU_FP16_ID  2
`define TCU_BF16_ID  3
`define TCU_FP8_ID   4
`define TCU_BF8_ID   5
`define TCU_MXFP8_ID 8
`define TCU_MXBF8_ID 9
`define TCU_MXFP4_ID 10
`define TCU_NVFP4_ID 11
`define TCU_I32_ID   16
`define TCU_I8_ID    17
`define TCU_U8_ID    18
`define TCU_I4_ID    19
`define TCU_U4_ID    20
`define TCU_FMT_WIDTH 5

// ---- Tile dimensions ----
`define TCU_NT 4
`define TCU_NR 32
`define TCU_NRA 4

`define TCU_TILE_CAP 128
`define TCU_LG_TILE_CAP 7
`define TCU_TILE_EN 3
`define TCU_TILE_EM 4
`define TCU_TILE_M 16
`define TCU_TILE_N 8
`define TCU_TILE_K 8

`define TCU_BLOCK_CAP 4
`define TCU_LG_BLOCK_CAP 2
`define TCU_BLOCK_EN 1
`define TCU_BLOCK_EM 1

`define TCU_TC_M 2
`define TCU_TC_N 2
`define TCU_TC_K 2

`define TCU_M_STEPS 8
`define TCU_N_STEPS 4
`define TCU_K_STEPS 4

// WGMMA dimensions
`define TCU_WG_TILE_M 4
`define TCU_WG_TILE_K 4
`define TCU_WG_FEDP_K 2
`define TCU_WG_TILE_N 32
`define TCU_WG_M_STEPS 2
`define TCU_WG_N_STEPS 16
`define TCU_WG_K_STEPS 2
`define TCU_WG_UOPS 64

// Register counts
`define TCU_NRA_W 32
`define TCU_NRB 16
`define TCU_NRC 32

// Exponent bits (TF32/FP16 are widest)
`define TCU_EXP_BITS 10

// MX scale
`define TCU_MX_MAX_SF 1

// ---- Struct types (as plain wire declarations) ----
// fedp_class_t: 4 bits (is_zero, is_sub, is_inf, is_nan)
// fedp_excep_t: 3 bits (is_inf, is_nan, sign)

`endif // TCU_SYNTH_DEFS_VH
