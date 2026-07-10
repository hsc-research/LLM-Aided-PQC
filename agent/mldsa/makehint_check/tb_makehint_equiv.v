// Lockstep equivalence TB: pristine makehint (REF) vs candidate (DUT).
`timescale 1ns / 1ps
module tb_makehint_equiv;
    reg clk=0, rst=1, poly_valid_ie=0, hint_ready_o=0;
    reg [2:0] sec_lvl = 3;
    reg [95:0] poly0_ie=0, poly1_ie=0;
    wire rej_ref, pri_ref, hv_ref, rej_dut, pri_dut, hv_dut;
    wire [63:0] ho_ref, ho_dut;

    makehint_ref REF (rst, clk, sec_lvl, rej_ref, poly0_ie, poly1_ie, poly_valid_ie, pri_ref, ho_ref, hv_ref, hint_ready_o);
    makehint     DUT (rst, clk, sec_lvl, rej_dut, poly0_ie, poly1_ie, poly_valid_ie, pri_dut, ho_dut, hv_dut, hint_ready_o);

    always #5 clk = ~clk;
    integer n, m, errors=0, checked=0, seed=32'hBEEF01;
    reg [23:0] lane;

    task check;
    begin
        checked = checked + 1;
        if (rej_ref !== rej_dut) begin errors=errors+1; $display("MISMATCH cyc %0d: reject %b/%b",checked,rej_ref,rej_dut); end
        if (pri_ref !== pri_dut) begin errors=errors+1; $display("MISMATCH cyc %0d: ready %b/%b",checked,pri_ref,pri_dut); end
        if (hv_ref  !== hv_dut ) begin errors=errors+1; $display("MISMATCH cyc %0d: hvalid %b/%b",checked,hv_ref,hv_dut); end
        if (hv_ref && hv_dut && (ho_ref !== ho_dut)) begin errors=errors+1; $display("MISMATCH cyc %0d: hint_o %h/%h",checked,ho_ref,ho_dut); end
    end
    endtask

    // one lane: mostly small (no hint), sometimes in hint band, sometimes boundary Q-GAMMA2
    task automatic randlane(output [23:0] v);
        integer r;
    begin
        r = $random(seed) % 100; if (r<0) r=-r;
        if (r < 70)       v = ($random(seed) % 24'd95232);          // below GAMMA2_2: never hint
        else if (r < 90)  v = 24'd300000 + ($random(seed) % 24'd7000000); // hint band
        else if (r < 92)  v = (sec_lvl==2) ? 24'd8285185 : 24'd8118529;   // exactly Q-GAMMA2
        else if (r < 94)  v = (sec_lvl==2) ? 24'd95232   : 24'd261888;    // exactly GAMMA2
        else if (r < 95)  v = ((sec_lvl==2) ? 24'd95232  : 24'd261888) + 1; // GAMMA2+1
        else              v = $random(seed);                          // anything
        if (v[23]) v = v & 24'h7FFFFF;
    end
    endtask

    task run_epoch(input [2:0] lvl, input integer cycles);
    begin
        sec_lvl = lvl;
        rst = 1; poly_valid_ie=0; hint_ready_o=0; poly0_ie=0; poly1_ie=0;
        repeat (4) @(posedge clk);
        rst = 0; @(posedge clk);
        for (n = 0; n < cycles; n = n + 1) begin
            poly_valid_ie <= ($random(seed) % 4) != 0;  // 75% valid: drive through full polys
            hint_ready_o  <= $random(seed);
            for (m = 0; m < 4; m = m + 1) begin
                randlane(lane); poly0_ie[m*24+:24] <= lane;
                randlane(lane); poly1_ie[m*24+:24] <= lane;
            end
            @(negedge clk); check; @(posedge clk);
        end
    end
    endtask

    initial begin
        run_epoch(2, 15000);
        run_epoch(3, 15000);
        run_epoch(5, 15000);
        if (errors == 0) $display("EQUIV RESULT: PASS checked %0d outputs 0 errors", checked);
        else             $display("EQUIV RESULT: FAIL checked %0d outputs %0d errors", checked, errors);
        $finish;
    end
endmodule
