`timescale 1ns/1ps
module tb_mldsa_rom;
    reg clk=0, en=0;
    always #5 clk=~clk;
    reg [7:0] a=0,b=0;
    wire [23:0] qa,qb,ra,rb;
    dual_port_rom #(.WIDTH(24), .LENGTH(256), .INIT_FILE("zetas.txt")) dut(clk,en,a,b,qa,qb);
    reference_dual_port_rom #(.WIDTH(24), .LENGTH(256), .INIT_FILE("zetas.txt")) ref_rom(clk,en,a,b,ra,rb);
    reg [2:0] za=0,zb=0;
    wire [8:0] zqa,zqb,zra,zrb;
    dual_port_rom #(.WIDTH(9), .LENGTH(5)) zero_dut(clk,en,za,zb,zqa,zqb);
    reference_dual_port_rom #(.WIDTH(9), .LENGTH(5)) zero_ref(clk,en,za,zb,zra,zrb);
    reg [23:0] held_a,held_b;
    integer i;
    initial begin
        #1;
        if (qa !== 24'hxxxxxx || qb !== 24'hxxxxxx) $fatal(1,"output must not be initialized");
        for(i=0;i<768;i=i+1) begin
            @(negedge clk);
            held_a=qa; held_b=qb;
            a=i%256; b=(255-i)%256; za=i%8; zb=(i+3)%8;
            en=(i<256 || i%3!=0);
            #1;
            if(qa !== held_a || qb !== held_b) $fatal(1,"ROM changed before clock");
            @(posedge clk); #1;
            if(qa !== ra || qb !== rb || zqa !== zra || zqb !== zrb)
                $fatal(1,"ROM mismatch cycle %0d",i);
            if(!en && (qa !== held_a || qb !== held_b)) $fatal(1,"disabled read did not hold");
        end
        @(negedge clk); en=1; a=8'hxx; b=8'hxx;
        @(posedge clk); #1;
        if(qa !== ra || qb !== rb) $fatal(1,"unknown-address semantics mismatch");
        $display("PASS ROM: 256 constants, paired ports, 768 cycles, enable/hold, zero ROM, out-of-range and X addresses");
        $finish;
    end
endmodule
