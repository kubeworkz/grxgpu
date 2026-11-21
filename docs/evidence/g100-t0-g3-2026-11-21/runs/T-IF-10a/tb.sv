`timescale 1ns/1ps

// T-IF-10a — CP ring encoder/decoder round-trip (L0).
//
// Drives the real VX_cp_unpack with a 64-byte line encoded by this testbench.
// All 11 mandatory opcodes (0x00..0x0A) are exercised in their profiled and
// unprofiled forms, except the unprofiled NOP: opcode 0 with flags 0 is the
// protocol's zero-header padding sentinel, so NOP is tested with F_PROFILE.
// A five-command line is also walked end to end.

module tb;
  import VX_cp_pkg::*;

  localparam int OFF_W = $clog2(CL_BYTES + 1);
  localparam logic [7:0] F_PROFILE = 8'h01;

  logic [CL_BITS-1:0] cl_data;
  logic [OFF_W-1:0]   offset;
  wire                has_cmd;
  cmd_t               cmd;
  wire [OFF_W-1:0]    cmd_size;

  VX_cp_unpack dut (
      .cl_data  (cl_data),
      .offset   (offset),
      .has_cmd  (has_cmd),
      .cmd      (cmd),
      .cmd_size (cmd_size)
  );

  int checks = 0;

  task automatic set_byte(input int idx, input logic [7:0] value);
    cl_data[idx*8 +: 8] = value;
  endtask

  task automatic get_byte(input int idx, output logic [7:0] value);
    value = cl_data[idx*8 +: 8];
  endtask

  task automatic fill_line(input logic [7:0] value);
    for (int i = 0; i < CL_BYTES; ++i) set_byte(i, value);
  endtask

  function automatic int unsigned size_of(input logic [7:0] op,
                                          input logic profiled);
    return cmd_size_bytes(cp_opcode_e'(op), profiled);
  endfunction

  // Independent copy of the wire-size table, so a bad package function cannot
  // round-trip consistently with itself.
  function automatic int unsigned expected_size(input logic [7:0] op,
                                                input logic profiled);
    int unsigned base;
    case (op)
      8'h00: base = 4;
      8'h01, 8'h02, 8'h03: base = 28;
      8'h04, 8'h05, 8'h08: base = 20;
      8'h06, 8'h0a: base = 12;
      8'h07: base = 8;
      8'h09: base = 28;
      default: base = 0;
    endcase
    return base + (profiled ? 8 : 0);
  endfunction

  task automatic emit(input int off,
                      input logic [7:0] op, flags,
                      input logic [63:0] a0, a1, a2,
                      input logic [63:0] profile_slot,
                      output int next_off);
    int unsigned sz;
    int payload;
    logic profiled;
    logic [63:0] value;

    profiled = flags[0];
    sz = size_of(op, profiled);
    if (off + int'(sz) > CL_BYTES)
      $fatal(1, "encode: command at %0d size %0d crosses the line", off, sz);

    for (int i = 0; i < int'(sz); ++i) set_byte(off + i, 8'h00);
    set_byte(off + 0, op);
    set_byte(off + 1, flags);
    set_byte(off + 2, 8'h00);
    set_byte(off + 3, 8'h00);

    payload = int'(sz) - 4 - (profiled ? 8 : 0);
    for (int i = 0; i < payload; ++i) begin
      case (i / 8)
        0: value = a0;
        1: value = a1;
        default: value = a2;
      endcase
      set_byte(off + 4 + i, value[8*(i%8) +: 8]);
    end

    if (profiled) begin
      for (int i = 0; i < 8; ++i)
        set_byte(off + int'(sz) - 8 + i, profile_slot[8*i +: 8]);
    end

    next_off = off + int'(sz);
  endtask

  task automatic check_command(input int off,
                               input logic [7:0] op, flags,
                               input logic [63:0] a0, a1, a2,
                               input logic [63:0] profile_slot,
                               input int unsigned sz);
    int payload;
    logic profiled;

    profiled = flags[0];
    if (!has_cmd)
      $fatal(1, "decode: no command at offset %0d (op 0x%02x)", off, op);
    if (cmd_size != sz)
      $fatal(1, "decode: op 0x%02x size %0d, expected %0d", op, cmd_size, sz);
    if (cmd.hdr.opcode != op)
      $fatal(1, "decode: opcode 0x%02x, expected 0x%02x", cmd.hdr.opcode, op);
    if (cmd.hdr.flags != flags)
      $fatal(1, "decode: flags 0x%02x, expected 0x%02x", cmd.hdr.flags, flags);
    if (cmd.hdr.reserved != 16'h0000)
      $fatal(1, "decode: reserved 0x%04x, expected 0", cmd.hdr.reserved);

    // Only the bytes the opcode declares are carried. FENCE carries just four
    // bytes of arg0; NOP carries none. The decoder's unused field bits read
    // neighboring bytes and are don't-care, so compare only the carried bytes.
    payload = int'(sz) - 4 - (profiled ? 8 : 0);
    if (payload == 4 && cmd.arg0[31:0] !== a0[31:0])
      $fatal(1, "decode: op 0x%02x arg0[31:0] 0x%08x, expected 0x%08x",
             op, cmd.arg0[31:0], a0[31:0]);
    if (payload >= 8 && cmd.arg0 !== a0)
      $fatal(1, "decode: op 0x%02x arg0 0x%016x, expected 0x%016x", op, cmd.arg0, a0);
    if (payload >= 16 && cmd.arg1 !== a1)
      $fatal(1, "decode: op 0x%02x arg1 0x%016x, expected 0x%016x", op, cmd.arg1, a1);
    if (payload >= 24 && cmd.arg2 !== a2)
      $fatal(1, "decode: op 0x%02x arg2 0x%016x, expected 0x%016x", op, cmd.arg2, a2);
    if (cmd.profile_slot !== (profiled ? profile_slot : 64'd0))
      $fatal(1, "decode: op 0x%02x profile 0x%016x, expected 0x%016x",
             op, cmd.profile_slot, profiled ? profile_slot : 64'd0);
    ++checks;
  endtask

  task automatic run_case(input logic [7:0] op, input logic profiled);
    logic [63:0] a0, a1, a2, profile_slot;
    logic [7:0] flags;
    int next_off;
    int unsigned sz;

    flags = profiled ? F_PROFILE : 8'h00;
    a0 = 64'h1122334455667788 ^ {56'd0, op};
    a1 = 64'h8877665544332211 ^ {56'd0, op};
    a2 = 64'h0123456789abcdef ^ {56'd0, op};
    profile_slot = 64'hfedcba9876543210;

    fill_line(8'hAA);
    emit(0, op, flags, a0, a1, a2, profile_slot, next_off);
    sz = size_of(op, profiled);
    if (sz != expected_size(op, profiled))
      $fatal(1, "encode: op 0x%02x size %0d, expected %0d",
             op, sz, expected_size(op, profiled));
    if (next_off != int'(sz))
      $fatal(1, "encode: op 0x%02x next offset %0d, expected %0d", op, next_off, sz);

    offset = 7'd0;
    #1;
    check_command(0, op, flags, a0, a1, a2, profile_slot, sz);

    // Encoding must not touch bytes beyond this single command.
    for (int i = int'(sz); i < CL_BYTES; ++i) begin
      logic [7:0] value;
      get_byte(i, value);
      if (value !== 8'hAA)
        $fatal(1, "encode: op 0x%02x wrote byte %0d beyond size %0d", op, i, sz);
    end

    $display("PASS op 0x%02x %s: size %0d, %0d argument byte(s)",
             op, profiled ? "profiled" : "unprofiled", sz,
             int'(sz) - 4 - (profiled ? 8 : 0));
  endtask

  task automatic test_zero_header_sentinel;
    int next_off;
    fill_line(8'h00);
    emit(0, 8'h00, 8'h00, 64'd0, 64'd0, 64'd0, 64'd0, next_off);
    offset = 7'd0;
    #1;
    if (has_cmd)
      $fatal(1, "zero-header NOP must decode as the padding sentinel");
    $display("PASS zero-header NOP is the padding sentinel");
  endtask

  task automatic test_five_command_line;
    int off;
    int next_off;
    logic [63:0] slot;
    logic [7:0] value;

    if (size_of(8'h00, 1'b1) != 12 || expected_size(8'h00, 1'b1) != 12)
      $fatal(1, "five-command line: profiled NOP size is not 12");

    fill_line(8'hAA);
    off = 0;
    for (int i = 0; i < 5; ++i) begin
      slot = 64'hA000000000000000 + i;
      emit(off, 8'h00, F_PROFILE, 64'd0, 64'd0, 64'd0, slot, next_off);
      off = next_off;
    end
    if (off != 60)
      $fatal(1, "five-command line ended at %0d, expected 60", off);
    for (int i = 60; i < CL_BYTES; ++i) begin
      get_byte(i, value);
      if (value !== 8'hAA)
        $fatal(1, "five-command line wrote padding byte %0d", i);
    end

    offset = 7'd0;
    #1;
    for (int i = 0; i < 5; ++i) begin
      slot = 64'hA000000000000000 + i;
      check_command(int'(offset), 8'h00, F_PROFILE,
                    64'd0, 64'd0, 64'd0, slot, 12);
      offset = offset + cmd_size;
      #1;
    end
    if (offset != 60)
      $fatal(1, "five-command walk ended at %0d, expected 60", offset);
    $display("PASS five-command line: 5 x profiled NOP, 60 B, 4 B untouched pad");
  endtask

  initial begin
    cl_data = '0;
    offset = '0;

    // NOP's unprofiled form is the zero-header sentinel; every other opcode
    // is tested unprofiled, and all 11 are tested profiled.
    for (int op = 0; op < 11; ++op) begin
      if (op != 0) run_case(op[7:0], 1'b0);
      run_case(op[7:0], 1'b1);
    end

    test_zero_header_sentinel();
    test_five_command_line();

    if (checks != 26)
      $fatal(1, "expected 26 round-trip checks, got %0d", checks);
    $display("PASS T-IF-10a: 11 opcodes, %0d round-trip checks (21 opcode + 5 line), 5-command line", checks);
    $finish;
  end
endmodule
