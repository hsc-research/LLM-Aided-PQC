`timescale 1ns/1ps
module tb_memories;
  parameter DUAL_DEPTH=7;
  reg clk=0; always #5 clk=!clk;
  reg boot=1;
  wire ready, single_ready;
  reg [2:0] a=0,b=0;
  reg [7:0] da=0,db=0;
  reg wa=0,wb=0,fw=0,fr=0;
  wire [7:0] q0,q1,r0,r1,sq,sr,fd,rf;
  wire full,empty,rfull,rempty;
  wire [3:0] fill,rfill;
  mem_dual #(.WIDTH(8),.DEPTH(DUAL_DEPTH),.INIT(1)) dut(clk,boot,ready,da,db,a,b,wa,wb,q0,q1);
  reference_dual #(.WIDTH(8),.DEPTH(DUAL_DEPTH),.INIT(1)) refmem(clk,da,db,a,b,wa,wb,r0,r1);
  mem_single #(.WIDTH(8),.DEPTH(8),.INIT(1)) sm(clk,boot,single_ready,da,a,wa,sq);
  reference_single #(.WIDTH(8),.DEPTH(8),.INIT(1)) smref(clk,da,a,wa,sr);
  fifo #(.BW(8),.LGFLEN(3)) ff(clk,boot,fw,da,full,fill,fr,fd,empty);
  reference_fifo #(.BW(8),.LGFLEN(3)) fref(clk,fw,da,rfull,rfill,fr,rf,rempty);
  integer i;
  reg [31:0] rng=32'h762345ab;
  initial begin
    repeat(3) @(negedge clk);
    boot=0;
    wait(ready && single_ready);
    @(negedge clk);
    for(i=0;i<2000;i=i+1) begin
      rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
      a=rng[2:0]; b=rng[5:3]; da=rng[13:6]; db=rng[21:14];
      wa=rng[22]; wb=rng[23] && (a!=b);
      if(i%17==0) begin a=3'bxxx;b=3'bxxx;wa=0;wb=0;end
      fw=rng[24]; fr=rng[25];
      @(posedge clk); #1;
      if(q0 !== r0 || q1 !== r1 || sq !== sr)
        $fatal(1,"memory timing/collision mismatch at cycle %0d",i);
      if(full !== rfull || empty !== rempty || fill !== rfill || (!empty && fd !== rf))
        $fatal(1,"FIFO mismatch at cycle %0d",i);
      @(negedge clk);
    end
    $display("SLH_ASIC_MEMORIES_PASS cycles=2000"); $finish;
  end
endmodule
