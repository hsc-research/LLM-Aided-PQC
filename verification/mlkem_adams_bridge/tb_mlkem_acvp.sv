// SPDX-License-Identifier: Apache-2.0
// Independent, public-interface-only ACVP harness. No hierarchical backdoors.
`timescale 1ns/1ps
module tb_mlkem_acvp;
  reg clk = 0;
  always #5 clk = ~clk;
  reg rst_b = 0;
  reg [31:0] haddr = 0;
  reg [63:0] hwdata = 0;
  reg hsel = 0, hwrite = 0;
  reg [1:0] htrans = 0;
  wire hready, hresp;
  wire [63:0] hrdata;
  wire busy, error_intr, notif_intr;
  abr_unified_top dut (
    .clk(clk), .rst_b(rst_b), .haddr_i(haddr), .hwdata_i(hwdata),
    .hsel_i(hsel), .hwrite_i(hwrite), .hready_i(hready),
    .htrans_i(htrans), .hsize_i(3'b010), .hresp_o(hresp),
    .hreadyout_o(hready), .hrdata_o(hrdata),
    .debugUnlock_or_scan_mode_switch(1'b0),
    .busy_o(busy), .error_intr(error_intr), .notif_intr(notif_intr)
  );

  integer fd, parsed, case_id = 0, cases = 0, checks = 0;
  integer total_checks = 0, commands = 0, case_cycles = 0;
  integer limit_cycles = 200000, active = 0, operation_started = 0;
  integer finished = 0;
  reg [31:0] opcode, address, value, actual;
  string command_file;

  // Independent timeout also catches an AHB wait that never terminates.
  always @(posedge clk) begin
    if (active != 0) begin
      case_cycles <= case_cycles + 1;
      if (case_cycles >= limit_cycles)
        $fatal(1, "MLKEM_FAIL case=%0d reason=cycle_timeout", case_id);
    end
  end

  task automatic transfer(input reg wr, input reg [31:0] addr,
                          input reg [31:0] data, output reg [31:0] result);
    integer waits;
    begin
      // Single-slave AHB-Lite, non-pipelined 32-bit transfers on AHB64.
      // Master changes address/control on falling edges, samples on rising.
      @(negedge clk);
      haddr = addr;
      hwdata = addr[2] ? {data, 32'b0} : {32'b0, data};
      hsel = 1;
      hwrite = wr;
      htrans = 2'b10;
      waits = 0;
      @(posedge clk);
      while (hready !== 1'b1) begin
        if ($isunknown(hready) || waits >= 1000)
          $fatal(1, "MLKEM_FAIL case=%0d reason=address_wait", case_id);
        waits = waits + 1;
        @(posedge clk);
      end
      @(negedge clk);
      hsel = 0;
      htrans = 0;
      // Keep write data and address stable throughout the data phase.
      waits = 0;
      @(posedge clk);
      while (hready !== 1'b1) begin
        if ($isunknown(hready) || waits >= 1000)
          $fatal(1, "MLKEM_FAIL case=%0d reason=data_wait", case_id);
        waits = waits + 1;
        @(posedge clk);
      end
      if (hresp !== 1'b0)
        $fatal(1, "MLKEM_FAIL case=%0d reason=AHB_response addr=%08h", case_id, addr);
      result = addr[2] ? hrdata[63:32] : hrdata[31:0];
      if (!wr && $isunknown(result))
        $fatal(1, "MLKEM_FAIL case=%0d reason=unknown_read addr=%08h", case_id, addr);
    end
  endtask

  task automatic reset_case(input integer ident);
    begin
      if (active != 0) $fatal(1, "MLKEM_FAIL reason=unfinished_case");
      @(negedge clk);
      rst_b = 0;
      hsel = 0;
      htrans = 0;
      hwrite = 0;
      haddr = 0;
      hwdata = 0;
      repeat (10) @(negedge clk);
      rst_b = 1;
      case_id = ident;
      case_cycles = 0;
      checks = 0;
      operation_started = 0;
      active = 1;
    end
  endtask

  task automatic wait_status(input reg completion, input reg [31:0] expected);
    reg [31:0] state;
    reg done;
    begin
      done = 0;
      while (!done) begin
        transfer(0, 32'h9014, 0, state);
        if (!completion) begin
          if (state[2:1] !== 2'b00)
            $fatal(1, "MLKEM_FAIL case=%0d reason=dirty_reset_status status=%08h", case_id, state);
          done = state[0];
        end else if (expected == 4) begin
          if (state[1] !== 0)
            $fatal(1, "MLKEM_FAIL case=%0d reason=invalid_key_accepted status=%08h", case_id, state);
          done = state[2];
        end else begin
          if (state[2] !== 0)
            $fatal(1, "MLKEM_FAIL case=%0d reason=unexpected_key_error status=%08h", case_id, state);
          // READY permits new input writes only in ABR_RESET.
          // A completed operation stays VALID with READY=0 until reset/zeroize
          // (pinned abr_ctrl.sv:679); outputs are available when VALID=1.
          done = state[1];
        end
      end
      if (completion) checks = checks + 1;
    end
  endtask

  initial begin
    if (!$value$plusargs("COMMANDS=%s", command_file))
      $fatal(1, "MLKEM_FAIL reason=missing_command_file");
    if ($value$plusargs("MAX_CYCLES=%d", limit_cycles)) begin
      if (limit_cycles < 1) $fatal(1, "MLKEM_FAIL reason=bad_cycle_limit");
    end
    fd = $fopen(command_file, "r");
    if (fd == 0) $fatal(1, "MLKEM_FAIL reason=unreadable_command_file");
    while (!finished) begin
      parsed = $fscanf(fd, "%h %h %h\n", opcode, address, value);
      if (parsed != 3) begin
        if ($feof(fd)) $fatal(1, "MLKEM_FAIL reason=missing_terminator");
        else $fatal(1, "MLKEM_FAIL reason=malformed_command");
      end
      commands = commands + 1;
      if (opcode != 5 && opcode != 7 && active == 0)
        $fatal(1, "MLKEM_FAIL reason=command_outside_case");
      case (opcode)
        1: begin
          transfer(1, address, value, actual);
          if (address == 'h9010) begin
            if (operation_started != 0) $fatal(1, "MLKEM_FAIL reason=duplicate_start");
            operation_started = 1;
          end
        end
        2: begin
          transfer(0, address, 0, actual);
          if (actual !== value)
            $fatal(1, "MLKEM_FAIL case=%0d reason=word_mismatch addr=%08h expected=%08h actual=%08h", case_id, address, value, actual);
          checks = checks + 1;
        end
        3: wait_status(0, 0);
        4: begin
          if (operation_started != 1) $fatal(1, "MLKEM_FAIL reason=missing_start");
          wait_status(1, value);
        end
        5: reset_case(value);
        6: begin
          if (operation_started != 1 || checks != value || checks < 1 || case_id != address)
            $fatal(1, "MLKEM_FAIL reason=case_accounting");
          active = 0;
          cases = cases + 1;
          total_checks = total_checks + checks;
          $display("MLKEM_CASE_PASS id=%0d checks=%0d cycles=%0d", case_id, checks, case_cycles);
          $fflush();
        end
        7: begin
          if (active != 0 || cases != address || total_checks != value || cases < 1)
            $fatal(1, "MLKEM_FAIL reason=final_accounting");
          // The explicit terminator must be the last line, never early success.
          parsed = $fscanf(fd, "%h %h %h\n", opcode, address, value);
          if (parsed > 0 || !$feof(fd))
            $fatal(1, "MLKEM_FAIL reason=data_after_terminator");
          finished = 1;
        end
        default: $fatal(1, "MLKEM_FAIL reason=unknown_opcode");
      endcase
    end
    // Keep $finish last: Verilator can complete the current procedural block
    // after setting gotFinish(). Never call $feof on an already closed handle.
    $fclose(fd);
    $display("MLKEM_ACVP_PASS cases=%0d checks=%0d", cases, total_checks);
    $fflush();
    $finish;
  end
endmodule
