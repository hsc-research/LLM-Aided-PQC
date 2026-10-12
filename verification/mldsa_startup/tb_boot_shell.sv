`timescale 1ns/1ps
// Tests the real startup shell against an interface-observation stub.
// This is a shell/control check, not a cryptographic core simulation.
module mldsa_asic_core #(parameter BUS_W=4,SAMPLE_W=23,W=64)(
 input clk,rst,start,input [1:0] mode,input [2:0] sec_lvl,input valid_i,
 output ready_i,input [W-1:0] data_i,output valid_o,input ready_o,
 output [W-1:0] data_o,input asic_boot_reset,asic_scrub_enable,input [11:0] asic_scrub_address);
 assign ready_i=1'b1;assign valid_o=1'b1;assign data_o=data_i;
endmodule
module tb_boot_shell;
 reg clk=0;always #5 clk=~clk;
 reg boot_rst=0,rst=0,start=1,valid_i=1,ready_o=1;
 wire ready_i,valid_o,boot_ready;wire [63:0] data_o;
 integer n,boots=0;
 combined_top_asic dut(clk,rst,start,2'd0,3'd2,valid_i,ready_i,64'h1234567abcde,valid_o,ready_o,data_o,boot_rst,boot_ready);
 task tick;begin @(posedge clk);#1;@(negedge clk);end endtask
 task reset_boot;
  begin
   boot_rst=1;#1;
   if({ready_i,valid_o,data_o}!==66'b0)$fatal(1,"boot reset must mask outputs immediately");
   tick();
   if(boot_ready!==0 || dut.boot_address!==0)$fatal(1,"boot reset did not initialize controller");
   boot_rst=0;#1;
  end
 endtask
 task finish_boot;
  begin
   for(n=0;n<4096;n=n+1)begin
    if(boot_ready!==0 || dut.boot_address!==n || dut.scrub_enable!==1)$fatal(1,"scrub progress/early-ready");
    if(dut.CORE.rst!==1 || dut.CORE.start!==0 || dut.CORE.valid_i!==0 || dut.CORE.ready_o!==0 || dut.CORE.asic_boot_reset!==1)$fatal(1,"core not held inactive");
    if({ready_i,valid_o,data_o}!==66'b0)$fatal(1,"boot output leaked");
    // Normal operation reset must neither restart nor pause the scrub.
    rst=n[2];tick();
   end
   rst=0;
   if(boot_ready!==1 || dut.scrub_enable!==0 || dut.hold_core!==0)$fatal(1,"boot not released after 4096 writes");
   if(ready_i!==1 || valid_o!==1 || data_o!==64'h1234567abcde)$fatal(1,"postboot interface mismatch");
   boots=boots+1;
  end
 endtask
 initial begin
  @(negedge clk);reset_boot();finish_boot();
  repeat(12)begin
   rst=1;tick();
   if(boot_ready!==1 || dut.scrub_enable!==0 || dut.CORE.asic_boot_reset!==0)$fatal(1,"ordinary reset caused reinitialization");
  end
  rst=0;
  // A new explicit boot aborts active traffic.
  reset_boot();
  repeat(31)tick();
  // A boot interrupted during its own scrub restarts at word zero.
  reset_boot();finish_boot();
  repeat(20)tick();reset_boot();finish_boot();
  $display("ASIC_BOOT_SHELL_PASS complete_boots=%0d interrupted_scrub=1 ordinary_reset_cycles=12",boots);
  $finish;
 end
endmodule
