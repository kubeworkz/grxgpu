// Gate-level testbench for the Yosys-synthesized VX_tcu_fedp_tfr
// Uses Verilog-2005 compatible constructs for Icarus Verilog.

`timescale 1ns/1ps

module tb_tfr_gatesim;

    reg         clk;
    reg         reset;
    reg         enable;
    reg  [15:0] vld_mask;
    reg  [4:0]  fmt_s;
    reg  [4:0]  fmt_d;
    reg  [63:0] a_row;
    reg  [63:0] b_col;
    reg  [31:0] c_val;
    wire [31:0] d_val;

    VX_tcu_fedp_tfr u_tfr (
        .clk      (clk),
        .reset    (reset),
        .enable   (enable),
        .vld_mask (vld_mask),
        .fmt_s    (fmt_s),
        .fmt_d    (fmt_d),
        .a_row    (a_row),
        .b_col    (b_col),
        .c_val    (c_val),
        .d_val    (d_val)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    integer pass_count;
    integer fail_count;
    integer test_num;

    task check_result(
        input [31:0] actual,
        input [31:0] expected,
        input [255:0] test_name
    );
        begin
            if (actual === expected) begin
                $display("  PASS: %0s  got=%h  exp=%h", test_name, actual, expected);
                pass_count = pass_count + 1;
            end else begin
                $display("  FAIL: %0s  got=%h  exp=%h", test_name, actual, expected);
                fail_count = fail_count + 1;
            end
        end
    endtask

    task wait_cycles(input integer n);
        integer i;
        begin
            for (i = 0; i < n; i = i + 1)
                @(posedge clk);
            #1;
        end
    endtask

    // Sample d_val on every clock edge for debugging
    reg [31:0] d_val_prev;
    always @(posedge clk) begin
        if (!reset && d_val !== d_val_prev) begin
            $display("  [%0t] d_val changed: %h -> %h", $time, d_val_prev, d_val);
        end
        d_val_prev <= d_val;
    end

    initial begin
        pass_count = 0;
        fail_count = 0;
        test_num = 0;
        reset = 1;
        enable = 0;
        vld_mask = 0;
        fmt_s = 5'd0;
        fmt_d = 5'd0;
        a_row = 0;
        b_col = 0;
        c_val = 0;
        d_val_prev = 0;

        // Reset
        repeat (5) @(posedge clk);
        reset = 0;
        enable = 1;
        repeat (2) @(posedge clk);

        // Test 1: FP32 MAC  2.0*4.0 + 3.0*5.0 = 23.0
        test_num = test_num + 1;
        $display("Test %0d: FP32 MAC  2.0*4.0 + 3.0*5.0 + 0.0 = 23.0", test_num);
        vld_mask = 16'h000F;
        a_row    = {32'h40400000, 32'h40000000};  // {3.0, 2.0}
        b_col    = {32'h40A00000, 32'h40800000};  // {5.0, 4.0}
        c_val    = 32'h0000_0000;
        wait_cycles(20);
        check_result(d_val, 32'h41B80000, "2.0*4.0 + 3.0*5.0 + 0.0 = 23.0");

        // Test 2: FP32 MAC  1.0*2.0 + 1.0*3.0 + 10.0 = 15.0
        test_num = test_num + 1;
        $display("Test %0d: FP32 MAC  1.0*2.0 + 1.0*3.0 + 10.0 = 15.0", test_num);
        vld_mask = 16'h000F;
        a_row    = {32'h3F800000, 32'h3F800000};
        b_col    = {32'h40400000, 32'h40000000};
        c_val    = 32'h41200000;
        wait_cycles(20);
        check_result(d_val, 32'h41700000, "1.0*2.0 + 1.0*3.0 + 10.0 = 15.0");

        // Test 3: FP32 MAC  -2.0*4.0 + 3.0*(-5.0) + 1.0 = -22.0
        test_num = test_num + 1;
        $display("Test %0d: FP32 MAC  -2.0*4.0 + 3.0*(-5.0) + 1.0 = -22.0", test_num);
        vld_mask = 16'h000F;
        a_row    = {32'h40400000, 32'hC0000000};
        b_col    = {32'hC0A00000, 32'h40800000};
        c_val    = 32'h3F800000;
        wait_cycles(20);
        check_result(d_val, 32'hC1B00000, "-2.0*4.0 + 3.0*(-5.0) + 1.0 = -22.0");

        // Test 4: Partial valid: 6.0*7.0 = 42.0
        test_num = test_num + 1;
        $display("Test %0d: FP32 MAC (partial valid) 6.0*7.0 = 42.0", test_num);
        vld_mask = 16'h0003;
        a_row    = {32'h00000000, 32'h40C00000};
        b_col    = {32'h00000000, 32'h40E00000};
        c_val    = 32'h0000_0000;
        wait_cycles(20);
        check_result(d_val, 32'h42280000, "6.0*7.0 = 42.0");

        // Test 5: Zero
        test_num = test_num + 1;
        $display("Test %0d: FP32 MAC  0.0 = 0.0", test_num);
        vld_mask = 16'h000F;
        a_row    = 64'h0;
        b_col    = 64'h0;
        c_val    = 32'h0;
        wait_cycles(20);
        check_result(d_val, 32'h0000_0000, "0.0 = 0.0");

        $display("");
        $display("=== Gate-level simulation results ===");
        $display("  Passed: %0d / %0d", pass_count, test_num);
        if (fail_count == 0)
            $display("  ALL TESTS PASSED");
        else
            $display("  %0d TESTS FAILED", fail_count);
        $display("=====================================");

        $finish;
    end

    initial begin
        #50000;
        $display("TIMEOUT");
        $finish;
    end

    initial begin
        $dumpfile("tfr_gatesim.vcd");
        $dumpvars(0, tb_tfr_gatesim);
    end

endmodule
