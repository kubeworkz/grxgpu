// Stub modules for Yosys elaboration — these are instantiated by TFR
// but defined outside the TFR source tree.

module VX_csa_tree #(parameter N=4, parameter W=10, parameter S=10)
    (input wire [N*W-1:0] operands, output wire [S-1:0] sum, output wire [S-1:0] carry);
    assign sum = {S{1'b0}};
    assign carry = {S{1'b0}};
endmodule

module VX_ks_adder #(parameter N=32, parameter BYPASS=0)
    (input wire [N-1:0] dataa, input wire [N-1:0] datab, input wire cin,
     output wire [N-1:0] sum, output wire cout);
    assign {cout, sum} = dataa + datab + cin;
endmodule

module VX_lzc #(parameter N=32)
    (input wire [N-1:0] data_in, output wire [$clog2(N)-1:0] data_out, output wire valid_out);
    assign data_out = 0;
    assign valid_out = |data_in;
endmodule

module VX_popcount #(parameter N=32)
    (input wire [N-1:0] data_in, output wire [$clog2(N+1)-1:0] data_out);
    integer i;
    reg [$clog2(N+1)-1:0] sum;
    always @(*) begin
        sum = 0;
        for (i = 0; i < N; i = i + 1)
            sum = sum + data_in[i];
    end
    assign data_out = sum;
endmodule

module VX_pipe_register #(parameter DATAW=32, parameter DEPTH=1)
    (input wire clk, input wire reset, input wire enable,
     input wire [DATAW-1:0] data_in, output wire [DATAW-1:0] data_out);
    assign data_out = data_in;
endmodule

module VX_wallace_mul #(parameter N=8, parameter P=16, parameter CPA_KS=1)
    (input wire [N-1:0] a, input wire [N-1:0] b, output wire [P-1:0] p);
    assign p = a * b;
endmodule
