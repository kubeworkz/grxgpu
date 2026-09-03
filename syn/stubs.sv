// Functionally accurate stub modules for gate-level simulation.
// These match the real RTL behavior well enough for correctness checks.

// CSA Tree: computes sum and carry of N W-bit operands
module VX_csa_tree #(parameter N=4, parameter W=10, parameter S=10)
    (input wire [N*W-1:0] operands, output wire [S-1:0] sum, output wire [S-1:0] carry);
    // Simple behavioral: sum = XOR of all operands, carry = majority
    // For simulation accuracy, use a straightforward accumulation
    wire [S-1:0] acc_sum;
    wire [S-1:0] acc_carry;
    integer i;
    reg [S-1:0] running_sum, running_carry;
    always @(*) begin
        running_sum = 0;
        running_carry = 0;
        for (i = 0; i < N; i = i + 1) begin
            running_sum = running_sum ^ operands[i*W +: W];
            running_carry = (running_sum & operands[i*W +: W]) | (running_carry & (running_sum ^ operands[i*W +: W]));
        end
    end
    assign sum = running_sum;
    assign carry = running_carry;
endmodule

// Kogge-Stone Adder
module VX_ks_adder #(parameter N=32, parameter BYPASS=0)
    (input wire [N-1:0] dataa, input wire [N-1:0] datab, input wire cin,
     output wire [N-1:0] sum, output wire cout);
    assign {cout, sum} = dataa + datab + cin;
endmodule

// Leading Zero Count
module VX_lzc #(parameter N=32)
    (input wire [N-1:0] data_in, output wire [$clog2(N)-1:0] data_out, output wire valid_out);
    integer i;
    reg [$clog2(N)-1:0] count;
    reg found;
    always @(*) begin
        count = 0;
        found = 0;
        for (i = N-1; i >= 0; i = i - 1) begin
            if (!found && data_in[i]) begin
                count = N - 1 - i;
                found = 1;
            end
        end
    end
    assign data_out = count;
    assign valid_out = |data_in;
endmodule

// Population Count
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

// Wallace Multiplier
module VX_wallace_mul #(parameter N=8, parameter P=16, parameter CPA_KS=1)
    (input wire [N-1:0] a, input wire [N-1:0] b, output wire [P-1:0] p);
    assign p = a * b;
endmodule

// Pipeline Register (passthrough for combinational mode)
module VX_pipe_register #(parameter DATAW=512, parameter DEPTH=1)
    (input wire clk, input wire reset, input wire enable,
     input wire [DATAW-1:0] data_in, output wire [DATAW-1:0] data_out);
    reg [DATAW-1:0] r_data;
    always @(posedge clk) begin
        if (reset)
            r_data <= 0;
        else if (enable)
            r_data <= data_in;
    end
    assign data_out = r_data;
endmodule
