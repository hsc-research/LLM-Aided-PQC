`timescale 1ns/1ps
module tb_abr_memories;
    reg clk=0;
    always #5 clk=~clk;
    reg we=0,re=0;
    reg [2:0] wa=0,ra=0;
    reg [15:0] wd=0;
    reg [1:0] strobe=0;
    wire [15:0] q,beq;
    abr_1r1w_ram #(.DEPTH(8),.DATA_WIDTH(16)) word_ram(clk,we,wa,wd,re,ra,q);
    abr_1r1w_be_ram #(.DEPTH(8),.DATA_WIDTH(16),.STROBE_WIDTH(8)) byte_ram(clk,we,strobe,wa,wd,re,ra,beq);
    reg [8:0] nwa=0,nra=0;
    wire [3:0] nq;
    abr_1r1w_512x4_ram nibble_ram(clk,we,nwa,wd[3:0],re,nra,nq);
    reg zeroize=0;
    reg [1:0] wes=0,res=0;
    reg [1:0][2:0] was=0,ras=0;
    reg [1:0][15:0] wds=0;
    wire [1:0][15:0] rqs;
    wire [7:0][15:0] allq;
    abr_ram_regout #(.DEPTH(8),.DATA_WIDTH(16),.NUM_RD_PORTS(2),.NUM_WR_PORTS(2)) regout(clk,zeroize,wes,was,wds,res,ras,rqs,allq);
    reg [15:0] mem[0:7],bemem[0:7],rmem[0:7];
    reg [3:0] nmem[0:511];
    reg [15:0] expq,expbe,expr0,expr1;
    reg [3:0] expn;
    integer i,j;
    integer seed=32'h47ac1234;
    initial begin
        // Testbench-only reference arrays intentionally begin unknown.
        for(i=0;i<8;i=i+1) begin mem[i]='x; bemem[i]='x; rmem[i]='x; end
        for(i=0;i<512;i=i+1) nmem[i]='x;
        expq='x; expbe='x; expn='x; expr0='x; expr1='x;
        for(i=0;i<1200;i=i+1) begin
            @(negedge clk);
            we=$random(seed); re=$random(seed); wa=$random(seed); ra=$random(seed);
            wd=$random(seed); strobe=$random(seed); nwa=$random(seed); nra=$random(seed);
            zeroize=(i%101==0); wes=$random(seed); res=$random(seed);
            was=$random(seed); ras=$random(seed); wds={$random(seed)};
            if(i<512) begin we=1; re=1; nwa=i; nra=i; end
            if(i<8) begin wa=i; ra=i; strobe=3; end
            if(i%4==0) begin re=1; we=1; ra=wa; nra=nwa; end
            if(i%5==0) begin wes=3; was[1]=was[0]; ras[0]=was[0]; res=3; end
            if(re) begin expq=mem[ra]; expbe=bemem[ra]; expn=nmem[nra]; end
            if(res[0]) expr0=rmem[ras[0]];
            if(res[1]) expr1=rmem[ras[1]];
            if(we) begin
                mem[wa]=wd; nmem[nwa]=wd[3:0];
                if(strobe[0]) bemem[wa][7:0]=wd[7:0];
                if(strobe[1]) bemem[wa][15:8]=wd[15:8];
            end
            if(zeroize) begin for(j=0;j<8;j=j+1) rmem[j]=0; end
            else begin
                if(wes[0]) rmem[was[0]]=wds[0];
                if(wes[1]) rmem[was[1]]=wds[1];
            end
            @(posedge clk); #1;
            if(q !== expq || beq !== expbe || nq !== expn || rqs[0] !== expr0 || rqs[1] !== expr1)
                $fatal(1,"RAM cycle %0d mismatch",i);
            for(j=0;j<8;j=j+1) if(allq[j] !== rmem[j]) $fatal(1,"regout array mismatch");
        end
        $display("PASS ABR: 1200 cycles; old-data collisions, read hold, byte mask, 512x4 boundaries, zeroize and highest-port write priority");
        $finish;
    end
endmodule
