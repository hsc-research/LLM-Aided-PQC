`timescale 1ns/1ps
module tb_slh_memories;
    reg clk=0;
    always #5 clk=~clk;
    reg [2:0] a=0,b=0;
    reg [7:0] da=0,db=0;
    reg wa=0,wb=0;
    wire [7:0] qa,qb,sq,ziqa,ziqb;
    mem_dual #(.WIDTH(8),.DEPTH(5),.INIT(0)) d(clk,da,db,a,b,wa,wb,qa,qb);
    mem_single #(.WIDTH(8),.DEPTH(5),.INIT(0)) s(clk,da,a,wa,sq);
    mem_dual #(.WIDTH(8),.DEPTH(5),.INIT(1)) zi(clk,8'b0,8'b0,a,b,1'b0,1'b0,ziqa,ziqb);
    reg [7:0] dm[0:5],sm[0:4],expa,expb,exps;
    integer i,j,seed=32'h254733;
    initial begin
        for(j=0;j<6;j=j+1) dm[j]='x;
        for(j=0;j<5;j=j+1) sm[j]='x;
        for(i=0;i<600;i=i+1) begin
            @(negedge clk);
            a=$random(seed)%6; b=$random(seed)%6;
            // Avoid unsigned-modulus surprises from a negative $random value.
            a=a%6; b=b%6;
            da=$random(seed); db=$random(seed); wa=$random(seed); wb=$random(seed);
            if(i<6) begin a=i; b=i; wa=1; wb=0; end
            if(i%4==0) begin b=a; wa=1; wb=0; end
            // Original separate always blocks do not define dual-write priority.
            if(wa && wb && a==b) wb=0;
            expa=wa ? da : dm[a]; expb=wb ? db : dm[b];
            exps=(a<5) ? sm[a] : 8'hxx;
            if(wa) begin dm[a]=da; if(a<5) sm[a]=da; end
            if(wb) dm[b]=db;
            @(posedge clk); #1;
            if(qa !== expa || qb !== expb || sq !== exps) $fatal(1,"SLH memory mismatch cycle %0d",i);
            if(ziqa !== 0 || ziqb !== 0) $fatal(1,"SLH INIT default semantics changed");
        end
        $display("PASS SLH: 600 cycles; dual write-first, cross-port old-data, single read-first, extra DEPTH element, INIT-zero behavior; dual-write collision excluded");
        $finish;
    end
endmodule
