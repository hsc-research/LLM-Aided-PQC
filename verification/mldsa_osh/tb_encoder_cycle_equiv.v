`timescale 1ns / 1ps
// Cycle-exact simulation check: pristine (encoder_gold) vs candidate
// (encoder) under identical legal-envelope stimulus. Output valid and data
// must agree on every active cycle, including stalled output cycles.
// The existing per-configuration accepted-stream checks are also retained.
// Defaults only: OUTPUT_W=4, COEFF_W=23, MAX_LVL=20, W=64.
// Independent configurations reset first; switch sequences drain between modes.
// This does not test reset with pending data or prove arbitrary backpressure.
module tb_encoder;
    reg clk = 0, rst = 1;
    reg [2:0] sec_lvl, encode_mode;
    reg valid_i = 0;
    reg [91:0] di;
    reg ready_o = 0;

    wire g_ready_i, g_valid_o, c_ready_i, c_valid_o;
    wire [63:0] g_dout, c_dout;

    encoder_gold GOLD (rst, clk, sec_lvl, encode_mode, valid_i, g_ready_i,
                       di, g_dout, g_valid_o, ready_o);
    encoder      CAND (rst, clk, sec_lvl, encode_mode, valid_i, c_ready_i,
                       di, c_dout, c_valid_o, ready_o);

    always #5 clk = ~clk;

    localparam NWORDS = 200;
    localparam MAXOUT = 4096;
    reg [63:0] g_stream [0:MAXOUT-1];
    reg [63:0] c_stream [0:MAXOUT-1];
    integer g_n, c_n;

    integer cycle_checks = 0;
    integer unknown_valid_errors = 0;
    integer unknown_data_errors = 0;

    // Four-state knownness and cycle checks, then accepted-stream capture.
    always @(posedge clk) begin
        if (!rst) begin
            cycle_checks = cycle_checks + 1;
            if ((g_valid_o !== 1'b0 && g_valid_o !== 1'b1) ||
                (c_valid_o !== 1'b0 && c_valid_o !== 1'b1)) begin
                errors = errors + 1;
                unknown_valid_errors = unknown_valid_errors + 1;
                $display("UNKNOWN VALID ERROR t=%0t gv=%b cv=%b", $time, g_valid_o, c_valid_o);
            end
            if ((g_valid_o === 1'b1 && (^g_dout === 1'bx)) ||
                (c_valid_o === 1'b1 && (^c_dout === 1'bx))) begin
                errors = errors + 1;
                unknown_data_errors = unknown_data_errors + 1;
                $display("UNKNOWN DATA ERROR t=%0t gv=%b cv=%b gd=%h cd=%h", $time, g_valid_o, c_valid_o, g_dout, c_dout);
            end
            if (g_valid_o !== c_valid_o ||
                (g_valid_o && g_dout !== c_dout)) begin
                errors = errors + 1;
                $display("CYCLE MISMATCH t=%0t gv=%b cv=%b gd=%h cd=%h", $time, g_valid_o, c_valid_o, g_dout, c_dout);
            end
            if (g_valid_o && ready_o && g_n < MAXOUT) begin
                g_stream[g_n] = g_dout; g_n = g_n + 1;
            end
            if (c_valid_o && ready_o && c_n < MAXOUT) begin
                c_stream[c_n] = c_dout; c_n = c_n + 1;
            end
        end
    end

    integer errors = 0;
    integer cfg, w, k, d;
    reg [2:0] lvls [0:2];
    reg [2:0] modes [0:5];
    reg [31:0] seed;

    task run_config(input [2:0] sl, input [2:0] em);
        integer j;
        begin
            // reset both DUTs
            @(negedge clk); rst = 1; valid_i = 0; ready_o = 0;
            sec_lvl = sl; encode_mode = em;
            @(negedge clk); @(negedge clk);
            rst = 0; g_n = 0; c_n = 0;
            // feed NWORDS with random gaps and random backpressure
            j = 0;
            while (j < NWORDS) begin
                @(negedge clk);
                ready_o = ($random(seed) % 4 != 0);   // 75% ready
                // envelope gate: pristine PISO legal only if insert cannot exceed 256b.
                // In-system flow control guarantees this; TB must respect the same contract.
                if ($random(seed) % 3 != 0 && (GOLD.piso_len + GOLD.buffer_len[0] + GOLD.buffer_len[1] <= 176)) begin
                    valid_i = 1;
                    di = {$random(seed), $random(seed), $random(seed)};
                    j = j + 1;
                end else valid_i = 0;
            end
            @(negedge clk); valid_i = 0;
            // drain: full backpressure release, long enough for both
            ready_o = 1;
            for (j = 0; j < 200; j = j + 1) @(negedge clk);
            // compare
            if (g_n != c_n) begin
                errors = errors + 1;
                $display("CFG sl=%0d em=%0d COUNT MISMATCH gold=%0d cand=%0d", sl, em, g_n, c_n);
            end else begin
                for (j = 0; j < g_n; j = j + 1) begin
                    if (g_stream[j] !== c_stream[j]) begin
                        errors = errors + 1;
                        $display("CFG sl=%0d em=%0d WORD %0d MISMATCH gold=%h cand=%h", sl, em, j, g_stream[j], c_stream[j]);
                        j = g_n; // stop at first per config
                    end
                end
            end
            $display("CFG sl=%0d em=%0d done: %0d words", sl, em, g_n);
        end
    endtask

    task run_switch_seq(input [2:0] sl);
        integer j, m;
        begin
            @(negedge clk); rst = 1; valid_i = 0; ready_o = 0;
            sec_lvl = sl; encode_mode = 0;
            @(negedge clk); @(negedge clk); @(negedge clk); @(negedge clk);
            rst = 0; g_n = 0; c_n = 0;
            for (m = 0; m < 6; m = m + 1) begin
                // change mode AND offer first word in the same cycle,
                // matching combined_top FSM state-entry behavior
                @(negedge clk);
                encode_mode = m[2:0];
                ready_o = 1; valid_i = 1;
                di = {$random(seed), $random(seed), $random(seed)};
                j = 1;
                while (j < 40) begin
                    @(negedge clk);
                    ready_o = ($random(seed) % 4 != 0);
                    if ($random(seed) % 3 != 0 && (GOLD.piso_len + GOLD.buffer_len[0] + GOLD.buffer_len[1] <= 176)) begin
                        valid_i = 1;
                        di = {$random(seed), $random(seed), $random(seed)};
                        j = j + 1;
                    end else valid_i = 0;
                end
                @(negedge clk); valid_i = 0;
                ready_o = 1;
                for (j = 0; j < 100; j = j + 1) @(negedge clk);  // drain
            end
            if (g_n != c_n) begin
                errors = errors + 1;
                $display("SWITCHSEQ sl=%0d COUNT MISMATCH gold=%0d cand=%0d", sl, g_n, c_n);
            end else begin
                for (j = 0; j < g_n; j = j + 1)
                    if (g_stream[j] !== c_stream[j]) begin
                        errors = errors + 1;
                        $display("SWITCHSEQ sl=%0d WORD %0d MISMATCH gold=%h cand=%h", sl, j, g_stream[j], c_stream[j]);
                        j = g_n;
                    end
            end
            $display("SWITCHSEQ sl=%0d done: %0d words", sl, g_n);
        end
    endtask

    initial begin
        seed = 32'hC0FFEE01;
        lvls[0] = 2; lvls[1] = 3; lvls[2] = 5;
        modes[0] = 0; modes[1] = 1; modes[2] = 2;
        modes[3] = 3; modes[4] = 4; modes[5] = 5;
        for (cfg = 0; cfg < 3; cfg = cfg + 1)
            for (k = 0; k < 6; k = k + 1)
                run_config(lvls[cfg], modes[k]);
        // config 19+: mode-switch sequences (drain between modes, as
        // combined_top's FSM does). Catches mode-decode lag bugs.
        run_switch_seq(3);
        run_switch_seq(5);
        $display("CYCLE CHECK SUMMARY checked=%0d errors=%0d unknown_valid=%0d unknown_data=%0d", cycle_checks, errors, unknown_valid_errors, unknown_data_errors);
        if (errors == 0) $display("GATE RESULT: PASS");
        else             $display("GATE RESULT: FAIL (%0d errors)", errors);
        $finish;
    end
endmodule
