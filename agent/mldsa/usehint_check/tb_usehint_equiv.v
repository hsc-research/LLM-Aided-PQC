`timescale 1ns/1ps
// Lockstep equivalence TB for usehint: pristine REF vs DUT.
// Epochs: sec_lvl {2,3,5}, reset between. Boundary injection on poly0
// (GAMMA2 constants 261888/95232, zero) and poly1 (wrap values 15/43/0).
// Coverage guard: every epoch must produce poly output beats (reach
// APPLY_HINT) or FAIL.
module tb_usehint_equiv;
    reg clk = 0, rst = 1, start = 0, valid_i = 0, poly_valid_i = 0, poly_ready_o = 0;
    reg [2:0] sec_lvl = 3'd2;
    reg [63:0] di = 0;
    reg [95:0] poly0_i = 0, poly1_i = 0;

    wire r_ready_i, r_poly_ready_i, r_poly_valid_o;  wire [95:0] r_poly_o;
    wire d_ready_i, d_poly_ready_i, d_poly_valid_o;  wire [95:0] d_poly_o;

    usehint_ref REF (.rst(rst), .clk(clk), .start(start), .sec_lvl(sec_lvl),
        .di(di), .valid_i(valid_i), .ready_i(r_ready_i),
        .poly0_i(poly0_i), .poly1_i(poly1_i), .poly_valid_i(poly_valid_i),
        .poly_ready_i(r_poly_ready_i), .poly_o(r_poly_o),
        .poly_valid_o(r_poly_valid_o), .poly_ready_o(poly_ready_o));
    usehint DUT (.rst(rst), .clk(clk), .start(start), .sec_lvl(sec_lvl),
        .di(di), .valid_i(valid_i), .ready_i(d_ready_i),
        .poly0_i(poly0_i), .poly1_i(poly1_i), .poly_valid_i(poly_valid_i),
        .poly_ready_i(d_poly_ready_i), .poly_o(d_poly_o),
        .poly_valid_o(d_poly_valid_o), .poly_ready_o(poly_ready_o));

    always #5 clk = ~clk;

    integer errors = 0, checked = 0, beats = 0, epoch_ok = 0;
    integer seed = 32'h05EE0517;

    task check; begin
        if ({r_ready_i, r_poly_ready_i, r_poly_valid_o, r_poly_o}
        !== {d_ready_i, d_poly_ready_i, d_poly_valid_o, d_poly_o}) begin
            errors = errors + 1;
            $display("MISMATCH t=%0t sec_lvl=%0d", $time, sec_lvl);
            if (errors > 5) begin $display("EQUIV RESULT: FAIL"); $finish; end
        end
        checked = checked + 1;
        if (r_poly_valid_o && poly_ready_o) beats = beats + 1;
    end endtask

    reg [23:0] b0, b1;
    integer lane;
    task drive; begin
        di = {$random(seed), $random(seed)};
        poly0_i = {$random(seed), $random(seed), $random(seed)};
        poly1_i = {$random(seed), $random(seed), $random(seed)};
        // 50% of cycles: one lane gets exact boundary values
        if ((($random(seed)) & 1) == 0) begin
            lane = ($random(seed)) & 3;
            case (($random(seed)) & 3)
            0: b0 = (sec_lvl == 2) ? 24'd95232 : 24'd261888;       // == GAMMA2
            1: b0 = ((sec_lvl == 2) ? 24'd95232 : 24'd261888) + 1; // just above
            2: b0 = 24'd0;                                          // zero case
            default: b0 = {$random(seed)} & 24'hFFFFFF;
            endcase
            case (($random(seed)) & 3)
            0: b1 = (sec_lvl == 2) ? 24'd43 : 24'd15;               // wrap top
            1: b1 = 24'd0;                                          // wrap bottom
            default: b1 = {$random(seed)} & 24'hFFFFFF;
            endcase
            poly0_i[lane*24+:24] = b0;
            poly1_i[lane*24+:24] = b1;
        end
        valid_i      = (($random(seed)) & 3) != 0;
        poly_valid_i = (($random(seed)) & 3) != 0;
        poly_ready_o = (($random(seed)) & 3) != 0;
    end endtask

    integer lvl_i, cyc;
    reg [2:0] levels [0:2];
    initial begin
        levels[0] = 3'd2; levels[1] = 3'd3; levels[2] = 3'd5;
        for (lvl_i = 0; lvl_i < 3; lvl_i = lvl_i + 1) begin
            rst = 1; start = 0; valid_i = 0; poly_valid_i = 0; poly_ready_o = 0;
            sec_lvl = levels[lvl_i];
            beats = 0;
            repeat (4) @(negedge clk);
            rst = 0;
            @(negedge clk);
            start = 1;
            @(negedge clk);
            start = 0;
            for (cyc = 0; cyc < 8000; cyc = cyc + 1) begin
                @(negedge clk);
                check;
                drive;
            end
            if (beats > 20) epoch_ok = epoch_ok + 1;
            else $display("COVERAGE WARN: sec_lvl=%0d only %0d beats", levels[lvl_i], beats);
        end
        if (epoch_ok < 3) begin
            $display("COVERAGE FAIL: only %0d/3 epochs produced output", epoch_ok);
            $display("EQUIV RESULT: FAIL");
        end else if (errors == 0)
            $display("EQUIV RESULT: PASS checked %0d", checked);
        else
            $display("EQUIV RESULT: FAIL");
        $finish;
    end
endmodule
