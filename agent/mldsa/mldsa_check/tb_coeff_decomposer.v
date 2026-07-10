`timescale 1ns/1ps
`ifndef TB_SEC_LVL
 `define TB_SEC_LVL 3
`endif
module tb_coeff_decomposer;
    localparam integer MAXV = 4096;
    localparam [2:0] SEC_LVL = `TB_SEC_LVL;
    reg clk = 0, rst = 0, valid_i = 0, ready_o = 1;
    reg  [23:0] di = 0;
    wire [23:0] doa, dob;
    wire        valid_o, ready_i;
    coeff_decomposer DUT(
        .rst(rst), .clk(clk), .valid_i(valid_i), .ready_i(ready_i),
        .sec_lvl(SEC_LVL), .di(di), .doa(doa), .dob(dob),
        .valid_o(valid_o), .ready_o(ready_o)
    );
    always #5 clk = ~clk;
    reg [23:0] in_di  [0:MAXV-1];
    reg [23:0] exp_a1 [0:MAXV-1];
    reg [23:0] exp_a0 [0:MAXV-1];
    integer nvec, i, recv, errors, nfd, rr;
    initial begin
        nfd = $fopen("nvec.txt","r"); rr = $fscanf(nfd,"%d",nvec); $fclose(nfd);
        $readmemh("di.hex", in_di);
        $readmemh("a1.hex", exp_a1);
        $readmemh("a0.hex", exp_a0);
        $display("loaded %0d vectors (sec=%0d)", nvec, SEC_LVL);
    end
    initial begin
        errors = 0; recv = 0;
        rst = 1; valid_i = 0; @(posedge clk); @(posedge clk);
        rst = 0; @(posedge clk);
        for (i = 0; i < nvec; i = i + 1) begin
            di <= in_di[i]; valid_i <= 1; @(posedge clk);
        end
        valid_i <= 0; di <= 0;
        repeat (12) @(posedge clk);
        $display("==== checked %0d outputs, %0d errors ====", recv, errors);
        if (errors == 0 && recv == nvec)
            $display("BLOCK-KAT RESULT: PASS  (%0d/%0d)", recv, nvec);
        else
            $display("BLOCK-KAT RESULT: FAIL  (%0d errors, %0d/%0d checked)", errors, recv, nvec);
        $finish;
    end
    always @(posedge clk) begin
        if (valid_o && !rst) begin
            if (recv < nvec) begin
                if (doa !== exp_a0[recv] || dob !== exp_a1[recv]) begin
                    if (errors < 15)
                      $display("MISMATCH #%0d di=%h: doa=%h exp=%h | dob=%h exp=%h",
                               recv, in_di[recv], doa, exp_a0[recv], dob, exp_a1[recv]);
                    errors = errors + 1;
                end
                recv = recv + 1;
            end
        end
    end
    initial begin #4000000; $display("TIMEOUT recv=%0d", recv); $finish; end
endmodule
