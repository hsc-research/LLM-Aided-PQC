`timescale 1ns/1ps
`include "setting.v"
module tb_startup;
  reg clk = 0;
  always #5 clk = !clk;
  reg boot_reset = 1, rstn = 1, start = 1;
  wire ready, sig_valid, done;
  top dut(.clk(clk), .rstn(rstn), .i_boot_reset(boot_reset), .o_boot_ready(ready),
    .i_msg_in_size(12'd33), .i_sig_mode(1'b0), .i_FSM_start(start),
    .o_FSM_done(done), .o_c_flag(), .o_sig_data(), .o_sig_valid(sig_valid),
    .sig_mem_out0(64'd0), .sig_mem_addr0_w(), .i_SK_seed(8'h5a), .i_PK_seed(8'ha5),
    .seed_valid(1'b1), .i_h_msg_mem_in0(64'hBAD), .i_h_msg_mem_addr0(9'd0), .i_h_msg_mem_wen0(1'b1));
`ifdef PARAM_128
  localparam LAST = 80;
  `define TILE0 dut.hash_tile_md0
`else
  localparam LAST = 171;
  `define TILE0 dut.hash_tile_md0.DUT_SHA256
  `define TILE1 dut.hash_tile_md0.DUT_SHA512
`endif
  integer i;
  task tick;
    begin @(posedge clk); #1; end
  endtask
  task check_blocked;
    begin
      if (ready !== 0 || sig_valid !== 0 || done !== 0)
        $fatal(1,"boot did not suppress ready/signature/completion");
      if (dut.PK_seed !== 1 || dut.SK_seed !== 2)
        $fatal(1,"seed writes were accepted before boot-ready");
      if (dut.H_MSG_MEM.mem[0] !== 64'hDEADBEEF)
        $fatal(1,"INIT=0 storage changed during boot");
    end
  endtask
  initial begin
    #1;
    dut.PK_seed = 1; dut.SK_seed = 2;
    dut.H_MSG_MEM.mem[0] = 64'hDEADBEEF;
    dut.INDICES_MEM.mem[0] = 7;
    dut.W_MEM.mem[0] = 4'ha;
    dut.MEM_64BIT_1.mem[0] = 64'hABCDEF;
    for(i=0;i<=LAST;i=i+1) begin
      `TILE0.SMALL_MEM.mem[i] = -1;
      `TILE0.BIG_MEM.mem[i] = -1;
`ifndef PARAM_128
      `TILE1.SMALL_MEM.mem[i] = -1;
      `TILE1.BIG_MEM.mem[i] = -1;
`endif
    end
    repeat(3) begin tick; check_blocked; end
    @(negedge clk); boot_reset = 0;
    repeat(7) begin tick; check_blocked; end
    // Explicit boot reset restarts scrubbing; ordinary rstn does not.
    @(negedge clk); boot_reset = 1;
    tick; check_blocked;
    @(negedge clk); boot_reset = 0; start = 0;
    for (i=0;i<LAST;i=i+1) begin
      tick; check_blocked;
      @(negedge clk);
      rstn = (i != 4 && i != 5);
    end
    tick;
    if (ready !== 1) $fatal(1,"ready did not assert at DEPTH+1 scrub cycles");
    for(i=0;i<=LAST;i=i+1) begin
      if (`TILE0.SMALL_MEM.mem[i] !== 0 || `TILE0.BIG_MEM.mem[i] !== 0)
        $fatal(1,"tile0 word did not clear, including inclusive final word");
`ifndef PARAM_128
      if (`TILE1.SMALL_MEM.mem[i] !== 0 || `TILE1.BIG_MEM.mem[i] !== 0)
        $fatal(1,"tile1 word did not clear");
`endif
    end
    if (`TILE0.S_FIFO_INSTANCE.wr_addr !== 0 || `TILE0.S_FIFO_INSTANCE.rd_addr !== 0 ||
        `TILE0.B_FIFO_INSTANCE.wr_addr !== 0 || `TILE0.B_FIFO_INSTANCE.rd_addr !== 0)
      $fatal(1,"FIFO pointers were not boot reset");
    if (dut.INDICES_MEM.mem[0] !== 7 || dut.W_MEM.mem[0] !== 4'ha || dut.MEM_64BIT_1.mem[0] !== 64'hABCDEF)
      $fatal(1,"INIT=0 bank was accidentally scrubbed");
    @(negedge clk); rstn = 0;
    `TILE0.SMALL_MEM.mem[LAST] = 64'h123456;
    `TILE0.S_FIFO_INSTANCE.wr_addr = 3;
    `TILE0.S_FIFO_INSTANCE.rd_addr = 1;
    repeat(4) tick;
    if (ready !== 1 || `TILE0.SMALL_MEM.mem[LAST] !== 64'h123456 ||
        `TILE0.S_FIFO_INSTANCE.wr_addr !== 3 || `TILE0.S_FIFO_INSTANCE.rd_addr !== 1)
      $fatal(1,"ordinary operation reset cleared boot state or storage");
    // Reboot must suppress seed loads even after a successful previous boot.
    @(negedge clk); boot_reset = 1; dut.PK_seed = 1; dut.SK_seed = 2;
    repeat(3) begin
      tick;
      if (dut.PK_seed !== 1 || dut.SK_seed !== 2 || ready !== 0)
        $fatal(1,"reboot accepted seed writes");
    end
    @(negedge clk); boot_reset = 0;
    repeat(LAST+1) begin
      tick;
      if (dut.PK_seed !== 1 || dut.SK_seed !== 2)
        $fatal(1,"reboot scrub accepted seed writes");
    end
    if (ready !== 1) $fatal(1,"reboot did not complete");
    $display("SLH_ASIC_STARTUP_PASS depth=%0d",LAST);
    $finish;
  end
  initial begin #100000; $fatal(1,"startup watchdog"); end
endmodule
