// Lockstep equivalence TB: pristine rejection_s (REF) vs candidate (DUT).
`timescale 1ns / 1ps
module tb_rejection_s_equiv;
    reg clk=0, rst=1, valid_i=0, ready_o=0;
    reg [2:0] sec_lvl = 2;
    reg [63:0] rdi=0;
    wire ri_ref, vo_ref, ri_dut, vo_dut;
    wire [91:0] s_ref, s_dut;

    rejection_s_ref REF (rst, clk, sec_lvl, valid_i, ri_ref, rdi, s_ref, vo_ref, ready_o);
    rejection_s     DUT (rst, clk, sec_lvl, valid_i, ri_dut, rdi, s_dut, vo_dut, ready_o);

    always #5 clk = ~clk;
    integer n, errors=0, checked=0, seed=32'hFACE02;

    task check;
    begin
        checked = checked + 1;
        if (ri_ref !== ri_dut) begin errors=errors+1; $display("MISMATCH cyc %0d: ready_i %b/%b",checked,ri_ref,ri_dut); end
        if (vo_ref !== vo_dut) begin errors=errors+1; $display("MISMATCH cyc %0d: valid_o %b/%b",checked,vo_ref,vo_dut); end
        if (vo_ref && vo_dut && (s_ref !== s_dut)) begin errors=errors+1; $display("MISMATCH cyc %0d: samples %h/%h",checked,s_ref,s_dut); end
    end
    endtask

    task run_epoch(input [2:0] lvl, input integer cycles);
    begin
        sec_lvl = lvl;
        rst = 1; valid_i=0; ready_o=0; rdi=0;
        repeat (4) @(posedge clk);
        rst = 0; @(posedge clk);
        for (n = 0; n < cycles; n = n + 1) begin
            valid_i <= $random(seed);
            ready_o <= $random(seed);
            rdi     <= {$random(seed), $random(seed)};
            if (n % 5 == 0) rdi <= 64'hFFFF_FFFF_FFFF_FFFF;  // all-reject lanes
            if (n % 11 == 0) rdi <= 64'h0123_4567_89AB_CDEF; // mixed
            @(negedge clk); check; @(posedge clk);
        end
        // streaming burst
        ready_o <= 1;
        for (n = 0; n < 3000; n = n + 1) begin
            valid_i <= 1;
            rdi     <= {$random(seed), $random(seed)};
            @(negedge clk); check; @(posedge clk);
        end
        // stall
        ready_o <= 0;
        for (n = 0; n < 1500; n = n + 1) begin
            valid_i <= $random(seed);
            rdi     <= {$random(seed), $random(seed)};
            @(negedge clk); check; @(posedge clk);
        end
    end
    endtask

    initial begin
        run_epoch(2, 10000);
        run_epoch(3, 10000);
        run_epoch(5, 10000);
        if (errors == 0) $display("EQUIV RESULT: PASS checked %0d outputs 0 errors", checked);
        else             $display("EQUIV RESULT: FAIL checked %0d outputs %0d errors", checked, errors);
        $finish;
    end
endmodule
