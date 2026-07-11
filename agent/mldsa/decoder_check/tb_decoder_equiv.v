`timescale 1ns/1ps
// Lockstep equivalence TB for decoder: pristine REF vs DUT.
// Epochs: sec_lvl {2,3,5} x encode_mode {T0,T1,S1,S2,W1,Z}, reset between.
// Boundary injection: mode-appropriate compare constants (4096, ETA,
// GAMMA1_2, GAMMA1_35) written into di at random bit offsets, so the
// rare equality cases (up to ~2^-18 under uniform data) are exercised.
// Coverage guard: every epoch must produce output beats.
module tb_decoder_equiv;
    reg clk = 0, rst = 1, valid_i = 0, ready_o = 0;
    reg [2:0] sec_lvl = 3'd2, encode_modei = 3'd0;
    reg [63:0] di = 0;

    wire r_ready_i, r_valid_o;  wire [91:0] r_samples;
    wire d_ready_i, d_valid_o;  wire [91:0] d_samples;

    decoder_ref REF (.rst(rst), .clk(clk), .sec_lvl(sec_lvl), .encode_modei(encode_modei),
        .valid_i(valid_i), .ready_i(r_ready_i), .di(di),
        .samples(r_samples), .valid_o(r_valid_o), .ready_o(ready_o));
    decoder DUT (.rst(rst), .clk(clk), .sec_lvl(sec_lvl), .encode_modei(encode_modei),
        .valid_i(valid_i), .ready_i(d_ready_i), .di(di),
        .samples(d_samples), .valid_o(d_valid_o), .ready_o(ready_o));

    always #5 clk = ~clk;

    integer errors = 0, checked = 0, beats = 0, epoch_ok = 0;
    integer seed = 32'hD ^ 32'hEC0DE;

    task check; begin
        if ({r_ready_i, r_valid_o, r_samples} !== {d_ready_i, d_valid_o, d_samples}) begin
            errors = errors + 1;
            $display("MISMATCH t=%0t sec_lvl=%0d mode=%0d", $time, sec_lvl, encode_modei);
            if (errors > 5) begin $display("EQUIV RESULT: FAIL"); $finish; end
        end
        checked = checked + 1;
        if (r_valid_o && ready_o) beats = beats + 1;
    end endtask

    reg [22:0] bconst;
    reg [5:0]  boff;
    task drive; begin
        di      = {$random(seed), $random(seed)};
        // 25% boundary injection at random alignment
        if ((($random(seed)) & 3) == 0) begin
            case (encode_modei)
            3'd0: bconst = 23'd4096;                                  // T0
            3'd2, 3'd3: bconst = (sec_lvl == 3) ? 23'd4 : 23'd2;      // S1/S2 ETA
            3'd5: bconst = (sec_lvl == 2) ? 23'd131072 : 23'd524288;  // Z GAMMA1
            default: bconst = {$random(seed)} & 23'h7FFFFF;
            endcase
            boff = ($random(seed)) & 6'd43;
            di = di & ~(64'hFFFFF << boff);
            di = di | ({41'd0, bconst} << boff);
        end
        valid_i = (($random(seed)) & 3) != 0;
        ready_o = (($random(seed)) & 3) != 0;
    end endtask

    integer lvl_i, md, cyc;
    reg [2:0] levels [0:2];
    initial begin
        levels[0] = 3'd2; levels[1] = 3'd3; levels[2] = 3'd5;
        for (lvl_i = 0; lvl_i < 3; lvl_i = lvl_i + 1) begin
            for (md = 0; md < 6; md = md + 1) begin
                rst = 1; valid_i = 0; ready_o = 0;
                sec_lvl = levels[lvl_i];
                encode_modei = md[2:0];
                beats = 0;
                repeat (4) @(negedge clk);
                rst = 0;
                for (cyc = 0; cyc < 2500; cyc = cyc + 1) begin
                    @(negedge clk);
                    check;
                    drive;
                end
                if (beats > 10) epoch_ok = epoch_ok + 1;
                else $display("COVERAGE WARN: sec_lvl=%0d mode=%0d only %0d beats",
                              levels[lvl_i], md, beats);
            end
        end
        if (epoch_ok < 18) begin
            $display("COVERAGE FAIL: only %0d/18 epochs produced output", epoch_ok);
            $display("EQUIV RESULT: FAIL");
        end else if (errors == 0)
            $display("EQUIV RESULT: PASS checked %0d", checked);
        else
            $display("EQUIV RESULT: FAIL");
        $finish;
    end
endmodule
