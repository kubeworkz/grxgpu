// Yosys-compatible VX_tcu_pkg for synthesis
// Strips $bits(), functions, and VX_gpu_pkg dependency
// Replaced with TCU_synth_pkg

`ifndef VX_TCU_PKG_VH
`define VX_TCU_PKG_VH

`include "VX_define.vh"

`IGNORE_UNUSED_BEGIN

package VX_tcu_pkg;

    import TCU_synth_pkg::*;

    // Re-export all constants from the synth package
    // (already imported via import TCU_synth_pkg::*)

    // ---- Minimal types needed by TFR ----

    typedef struct packed {
        logic [4:0] step_m;
        logic [3:0] step_n;
        logic [3:0] step_k;
        logic [1:0] cd_nregs;
        logic       a_from_smem;
        logic [4:0] fmt_s;
        logic [4:0] fmt_d;
    } tcu_args_t;

`ifdef SIMULATION
`endif

    `DECL_EXECUTE_T (tcu, `VX_CFG_NUM_TCU_LANES);

endpackage

`IGNORE_UNUSED_END

`endif // VX_TCU_PKG_VH
