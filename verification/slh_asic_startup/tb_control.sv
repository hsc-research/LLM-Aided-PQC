`timescale 1ns/1ps
module tb_control;
  parameter CH_len=2;
  reg clk=0; always #5 clk=!clk;
  reg rstn=0;
  reg [3:0] cnt=0,ch_cnt=0;
  reg start=0,lr=0;
  wire original,current;
  original_decoder #(.CH_len(CH_len)) a(clk,rstn,cnt,ch_cnt,lr,start,original);
  current_decoder #(.CH_len(CH_len)) b(clk,rstn,cnt,ch_cnt,lr,start,current);
  integer c,h,s,l,held,checks=0;
  task drive;
    input [3:0] cc,hh;
    input ss,ll;
    begin
      // Actual decoder sources update in the NBA region of posedge processes.
      @(posedge clk); cnt<=cc;ch_cnt<=hh;start<=ss;lr<=ll;
      @(negedge clk);
      if(original !== current) $fatal(1,"cycle equivalence mismatch cnt=%0d ch=%0d start=%0b lr=%0b old=%0b new=%0b",cnt,ch_cnt,start,lr,original,current);
      checks=checks+1;
    end
  endtask
  initial begin
    repeat(3) @(negedge clk);rstn=1;
    for(held=0;held<2;held=held+1)
      for(c=0;c<16;c=c+1)
        for(h=0;h<16;h=h+1)
          for(s=0;s<2;s=s+1)
            for(l=0;l<2;l=l+1) begin
              drive(6,0,1,held); // establish both possible histories
              drive(c,h,s,l);  // exhaustive binary control tuple
              drive(4,h,0,!l); // hold entry, independent data transition
              drive(5,h,0,l);  // transition between hold states
              drive(5,h,1,!l); // bypass replaces history immediately after edge
              drive(4,h,0,l);  // retain freshly bypassed value
            end
    for(held=0;held<2;held=held+1) begin
      drive(6,0,1,held);
      drive(4,0,0,!held);
      // Real producer registers also asynchronously reset to cnt=0/start=0.
      #1; rstn=0; cnt<=0;start<=0;ch_cnt<=0;lr<=0;
      #1;
      if(original !== 0 || current !== 0) $fatal(1,"asynchronous reset during hold mismatch");
      @(negedge clk);rstn=1;
      drive(4,0,0,held);
    end
    $display("SLH_ASIC_CONTROL_PASS CH_len=%0d checks=%0d",CH_len,checks);$finish;
  end
endmodule
