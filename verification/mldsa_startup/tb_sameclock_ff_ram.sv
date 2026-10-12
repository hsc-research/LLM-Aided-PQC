`timescale 1ns/1ps
module tb_sameclock_ff_ram;
    reg clk=0;
    always #5 clk=~clk;
    reg hold_core=1, scrub_enable=0;
    reg [11:0] scrub_address=0;
    reg ena=0,enb=0,wea=0,web=0;
    reg [11:0] addra=0,addrb=0;
    reg [95:0] dia=0,dib=0;
    wire [95:0] a4096,b4096,a1024,b1024,r4096a,r4096b,r1024a,r1024b;
    reg [31:0] rng=32'h134fecd7;
    integer n,checks=0;
    mldsa_sameclock_ff_ram #(.LENGTH(4096)) big(clk,hold_core,scrub_enable,scrub_address,ena,enb,wea,web,addra,addrb,dia,dib,a4096,b4096);
    mldsa_sameclock_ff_ram #(.LENGTH(1024)) smallram(clk,hold_core,scrub_enable,scrub_address,ena,enb,wea,web,addra[9:0],addrb[9:0],dia,dib,a1024,b1024);
    dual_port_ram #(.WIDTH(96),.LENGTH(4096)) refbig(clk,clk,ena&&!hold_core,enb&&!hold_core,wea,web,addra,addrb,dia,dib,r4096a,r4096b);
    dual_port_ram #(.WIDTH(96),.LENGTH(1024)) refsmall(clk,clk,ena&&!hold_core,enb&&!hold_core,wea,web,addra[9:0],addrb[9:0],dia,dib,r1024a,r1024b);
    task step;
        begin
            @(posedge clk); #1;
            if (!hold_core) begin
                if ({a4096,b4096,a1024,b1024} !== {r4096a,r4096b,r1024a,r1024b})
                    $fatal(1,"read/hold/read-before-write mismatch at check %0d",checks);
                checks=checks+1;
            end
            @(negedge clk);
        end
    endtask
    task scrub;
        begin
            hold_core=1;
            // Core requests must never write while held, including reset cycles.
            ena=1;enb=1;wea=1;web=1;dia='1;dib='1;addra=0;addrb=1;
            scrub_enable=0;step();step();
            scrub_enable=1;
            for(n=0;n<4096;n=n+1)begin scrub_address=n;step();end
            scrub_enable=0;ena=0;enb=0;wea=0;web=0;
            for(n=0;n<4096;n=n+1)
                if(big.ram[n]!==96'b0)$fatal(1,"big scrub missed %0d",n);
            for(n=0;n<1024;n=n+1)
                if(smallram.ram[n]!==96'b0)$fatal(1,"smallram scrub missed %0d",n);
            hold_core=0;
        end
    endtask
    initial begin
        @(negedge clk);
        if (big.ram[0]!==96'bx || big.ram[4095]!==96'bx || smallram.ram[1023]!==96'bx)
            $fatal(1,"RAM unexpectedly has power-up initialized data");
        scrub();
        if ({a4096,b4096,a1024,b1024}!==384'bx)$fatal(1,"scrub changed held outputs");
        ena=1;enb=1;
        for(n=0;n<4096;n=n+1)begin addra=n;addrb=4095-n;step();end
        for(n=0;n<6000;n=n+1)begin
            rng=rng ^ (rng<<13);rng=rng ^ (rng>>17);rng=rng ^ (rng<<5);
            ena=rng[0];enb=rng[1];wea=rng[2];web=rng[3];
            addra=rng[15:4];addrb=rng[27:16];
            if(n%7==0)addrb=addra;
            if(ena&&enb&&wea&&web&&(addra[9:0]==addrb[9:0]))web=0;
            dia={rng,~rng,rng^32'ha542198f};dib={~rng,rng,rng^32'h45ade347};
            step();
        end
        // Explicit second boot is destructive; the old ordinary reset had no
        // storage port. A boot-only controller, not operation rst, requests this.
        scrub();
        $display("ASIC_RAM_PASS checked_cycles=%0d depths=4096,1024 width=96 boot_count=2",checks);
        $finish;
    end
endmodule
