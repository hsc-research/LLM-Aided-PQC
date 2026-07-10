// Lockstep equivalence TB: pristine rejection_a (REF) vs candidate (DUT).
// Same stimulus to both; compare ready_i, valid_o, samples (when valid_o) every cycle.
`timescale 1ns / 1ps
module tb_rejection_a_equiv;
    reg clk=0, rst=1, valid_i=0, ready_o=0;
    reg [63:0] rdi=0;
    wire ready_i_ref, valid_o_ref, ready_i_dut, valid_o_dut;
    wire [91:0] samples_ref, samples_dut;

    rejection_a_ref REF (rst, clk, valid_i, ready_i_ref, rdi, samples_ref, valid_o_ref, ready_o);
    rejection_a     DUT (rst, clk, valid_i, ready_i_dut, rdi, samples_dut, valid_o_dut, ready_o);

    always #5 clk = ~clk;
    integer n, errors=0, checked=0, seed=32'hC0FFEE;

    task check;
    begin
        checked = checked + 1;
        if (ready_i_ref !== ready_i_dut) begin
            errors = errors + 1;
            $display("MISMATCH cycle %0d: ready_i ref=%b dut=%b", checked, ready_i_ref, ready_i_dut);
        end
        if (valid_o_ref !== valid_o_dut) begin
            errors = errors + 1;
            $display("MISMATCH cycle %0d: valid_o ref=%b dut=%b", checked, valid_o_ref, valid_o_dut);
        end
        if (valid_o_ref && valid_o_dut && (samples_ref !== samples_dut)) begin
            errors = errors + 1;
            $display("MISMATCH cycle %0d: samples ref=%h dut=%h", checked, samples_ref, samples_dut);
        end
    end
    endtask

    initial begin
        rst = 1; valid_i = 0; ready_o = 0; rdi = 0;
        repeat (4) @(posedge clk);
        rst = 0;
        @(posedge clk);
        // 20000 cycles of randomized stimulus incl. sparse valid/ready and
        // biased rdi (some words with >=Q lanes to exercise rejection).
        for (n = 0; n < 20000; n = n + 1) begin
            valid_i <= $random(seed);
            ready_o <= $random(seed);
            rdi     <= {$random(seed), $random(seed)};
            // every 7th word: force lanes near/above Q to hit rejection paths
            if (n % 7 == 0)
                rdi <= {8'hFF, 24'hFFFFFF, 8'h7F, 24'h7FE001};
            @(negedge clk);
            check;
            @(posedge clk);
        end
        // burst phases: all-valid streaming, then stalled ready_o
        ready_o <= 1;
        for (n = 0; n < 5000; n = n + 1) begin
            valid_i <= 1;
            rdi     <= {$random(seed), $random(seed)};
            @(negedge clk); check; @(posedge clk);
        end
        ready_o <= 0;
        for (n = 0; n < 2000; n = n + 1) begin
            valid_i <= $random(seed);
            rdi     <= {$random(seed), $random(seed)};
            @(negedge clk); check; @(posedge clk);
        end
        if (errors == 0)
            $display("EQUIV RESULT: PASS checked %0d outputs 0 errors", checked);
        else
            $display("EQUIV RESULT: FAIL checked %0d outputs %0d errors", checked, errors);
        $finish;
    end
endmodule
