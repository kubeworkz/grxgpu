module VX_wallace_mul #(
    parameter N = 8,
    parameter P = 2 * N,
    parameter CPA_KS = 1
) (
    input wire [N-1:0] a,
    input wire [N-1:0] b,
    output wire [P-1:0] p
);
    assign p = a * b;
endmodule

module wmul_equiv_tb;
    localparam N = 8;
    localparam P = 2 * N;

    reg [N-1:0] a;
    reg [N-1:0] b;
    wire [P-1:0] product;
    integer i;
    integer j;

    VX_tcu_tfr_wmul #(
        .N(N),
        .M(N),
        .P(P)
    ) dut (
        .a(a),
        .b(b),
        .p(product)
    );

    initial begin
        for (i = 0; i < (1 << N); i = i + 1) begin
            for (j = 0; j < (1 << N); j = j + 1) begin
                a = N'(i);
                b = N'(j);
                #1;
                if (product !== (P'(i) * P'(j))) begin
                    $fatal(1, "mismatch: a=%0d b=%0d product=%0d",
                           a, b, product);
                end
            end
        end
        $display("PASS: all %0d x %0d N=8 VX_tcu_tfr_wmul products match", 1 << N, 1 << N);
        $finish;
    end
endmodule
