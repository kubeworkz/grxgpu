// Wrapper to synthesize VX_stream_arb standalone at a given config.
// Parameters are set per-run via a generated instantiation (see synth script).
module arb_sweep_top #(
    parameter NI = 16,
    parameter NO = 1,
    parameter DW = 64,
    parameter `STRING ARB = "R",
    parameter STK = 0,
    parameter OB = 0
) (
    input  wire clk,
    input  wire reset,
    input  wire [NI-1:0]              valid_in,
    input  wire [NI-1:0][DW-1:0]      data_in,
    output wire [NI-1:0]              ready_in,
    output wire [NO-1:0]              valid_out,
    output wire [NO-1:0][DW-1:0]      data_out,
    input  wire [NO-1:0]              ready_out,
    output wire [`UP(`CLOG2(NI > NO ? ((NI + NO - 1) / NO) : ((NO + NI - 1) / NI)))-1:0] sel_out
);
    VX_stream_arb #(
        .NUM_INPUTS  (NI),
        .NUM_OUTPUTS (NO),
        .DATAW       (DW),
        .ARBITER     (ARB),
        .STICKY      (STK),
        .OUT_BUF     (OB)
    ) u_arb (
        .clk        (clk),
        .reset      (reset),
        .valid_in   (valid_in),
        .data_in    (data_in),
        .ready_in   (ready_in),
        .valid_out  (valid_out),
        .data_out   (data_out),
        .ready_out  (ready_out),
        .sel_out    (sel_out)
    );
endmodule