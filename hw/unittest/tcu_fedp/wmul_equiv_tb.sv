module wmul_matrix_case #(
    parameter N = 2,
    parameter M = 2,
    parameter LANES = 1,
    parameter SHARED_B = 0,
    parameter P = N + M,
    parameter USE_DSP = 0
) (
    output reg done
);
    localparam A_COUNT = 1 << N;
    localparam B_COUNT = 1 << M;
    localparam A_MASK = A_COUNT - 1;
    localparam B_MASK = B_COUNT - 1;

    reg [LANES-1:0][N-1:0] a;
    reg [LANES-1:0][M-1:0] b;
    wire [LANES-1:0][P-1:0] product;
    reg [P-1:0] expected;
    integer i;
    integer j;
    integer lane;

    VX_tcu_tfr_wmul #(
        .N(N),
        .M(M),
        .LANES(LANES),
        .SHARED_B(SHARED_B),
        .P(P),
        .USE_DSP(USE_DSP)
    ) dut (
        .a(a),
        .b(b),
        .p(product)
    );

    initial begin
        done = 0;
        for (i = 0; i < A_COUNT; i = i + 1) begin
            for (j = 0; j < B_COUNT; j = j + 1) begin
                for (lane = 0; lane < LANES; lane = lane + 1) begin
                    a[lane] = N'((i + lane * 17) & A_MASK);
                    b[lane] = M'((j + lane * 29) & B_MASK);
                end
                #1;
                for (lane = 0; lane < LANES; lane = lane + 1) begin
                    expected = P'(a[lane]) * P'(SHARED_B ? b[0] : b[lane]);
                    if (product[lane] !== expected) begin
                        $fatal(1, "mismatch N=%0d M=%0d LANES=%0d SHARED_B=%0d USE_DSP=%0d lane=%0d a=%0d b=%0d product=%0d expected=%0d",
                               N, M, LANES, SHARED_B, USE_DSP, lane, a[lane],
                               SHARED_B ? b[0] : b[lane], product[lane], expected);
                    end
                end
            end
        end
        $display("PASS N=%0d M=%0d LANES=%0d SHARED_B=%0d P=%0d USE_DSP=%0d: %0d operand pairs per lane",
                 N, M, LANES, SHARED_B, P, USE_DSP, A_COUNT * B_COUNT);
        done = 1;
    end
endmodule

module wmul_equiv_tb;
    wire [10:0] done;

    wmul_matrix_case #(.N(11), .M(11), .LANES(1), .USE_DSP(0)) fp16_mantissa_lut(done[0]);
    wmul_matrix_case #(.N(11), .M(11), .LANES(1), .USE_DSP(1)) fp16_mantissa_dsp(done[1]);
    wmul_matrix_case #(.N(4), .M(4), .LANES(2), .USE_DSP(0)) fp8_pair_lut(done[2]);
    wmul_matrix_case #(.N(4), .M(4), .LANES(2), .USE_DSP(1)) fp8_pair_dsp(done[3]);
    wmul_matrix_case #(.N(2), .M(2), .LANES(2), .USE_DSP(0)) mx_nv_fp4_pair_lut(done[4]);
    wmul_matrix_case #(.N(2), .M(2), .LANES(2), .USE_DSP(1)) mx_nv_fp4_pair_dsp(done[5]);
    wmul_matrix_case #(.N(4), .M(4), .LANES(1), .USE_DSP(0)) nvfp4_scale_lut(done[6]);
    wmul_matrix_case #(.N(4), .M(4), .LANES(1), .USE_DSP(1)) nvfp4_scale_dsp(done[7]);
    wmul_matrix_case #(.N(4), .M(8), .LANES(2), .SHARED_B(1), .USE_DSP(0)) nvfp4_shared_scale_lut(done[8]);
    wmul_matrix_case #(.N(4), .M(8), .LANES(2), .SHARED_B(1), .USE_DSP(1)) nvfp4_shared_scale_dsp(done[9]);
    wmul_matrix_case #(.N(4), .M(4), .LANES(2), .USE_DSP(1)) int4_magnitude_dsp(done[10]);

    initial begin
        wait (&done);
        $display("PASS: complete TCU TFR multiplier parameter matrix (LUT and DSP paths)");
        $finish;
    end
endmodule
