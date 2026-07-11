`timescale 1ns/1ps
// Lockstep equivalence TB for gen_c (SampleInBall): pristine REF vs DUT.
// Scripted Keccak driver reacts to REF handshake outputs; identical inputs
// to both; ALL outputs compared every cycle. sec_lvl epochs {2,3,5} x
// modes {sign,verify}, reset between. Coverage-guarded: requires 6/6
// complete runs (done_sampler observed) or the result is FAIL.
module tb_gen_c_equiv;
    reg clk = 0, rst = 1, start = 0, mode = 0, valid_i = 0, ready_o = 0, ch_read = 0;
    reg [2:0] sec_lvl = 3'd2;
    reg [63:0] seed_i = 0, dout = 0;
    reg src_read = 0, dst_write = 0;

    wire r_ready_i, r_valid_o, r_done, r_rst_k, r_src_ready, r_dst_ready;
    wire [91:0] r_samples;  wire [63:0] r_ch, r_din;
    wire d_ready_i, d_valid_o, d_done, d_rst_k, d_src_ready, d_dst_ready;
    wire [91:0] d_samples;  wire [63:0] d_ch, d_din;

    gen_c_ref REF (.start(start), .rst(rst), .clk(clk), .sec_lvl(sec_lvl), .mode(mode),
        .valid_i(valid_i), .ready_i(r_ready_i), .seed_i(seed_i), .samples(r_samples),
        .valid_o(r_valid_o), .ready_o(ready_o), .ch_read(ch_read), .ch(r_ch),
        .done_sampler(r_done), .rst_k(r_rst_k), .din(r_din), .dout(dout),
        .src_ready(r_src_ready), .src_read(src_read), .dst_write(dst_write), .dst_ready(r_dst_ready));

    gen_c DUT (.start(start), .rst(rst), .clk(clk), .sec_lvl(sec_lvl), .mode(mode),
        .valid_i(valid_i), .ready_i(d_ready_i), .seed_i(seed_i), .samples(d_samples),
        .valid_o(d_valid_o), .ready_o(ready_o), .ch_read(ch_read), .ch(d_ch),
        .done_sampler(d_done), .rst_k(d_rst_k), .din(d_din), .dout(dout),
        .src_ready(d_src_ready), .src_read(src_read), .dst_write(dst_write), .dst_ready(d_dst_ready));

    always #5 clk = ~clk;

    integer errors = 0, checked = 0, done_count = 0;
    integer seed = 32'hC0FFEE01;

    task check; begin
        if ({r_ready_i,r_valid_o,r_done,r_rst_k,r_src_ready,r_dst_ready,r_samples,r_ch,r_din}
        !== {d_ready_i,d_valid_o,d_done,d_rst_k,d_src_ready,d_dst_ready,d_samples,d_ch,d_din}) begin
            errors = errors + 1;
            $display("MISMATCH t=%0t sec_lvl=%0d mode=%0d", $time, sec_lvl, mode);
            if (errors > 5) begin $display("EQUIV RESULT: FAIL"); $finish; end
        end
        checked = checked + 1;
    end endtask

    task drive; begin
        // Boundary injection: 25% of cycles, all dout bytes = REF's current
        // sample_no, guaranteeing sample_addr == sample_no accept events.
        // Both REF and DUT receive the identical value; whitebox stimulus only.
        if ((($random(seed)) & 3) == 0)
            dout = {8{REF.sample_no[7:0]}};
        else
            dout = {$random(seed), $random(seed)};
        seed_i    = {$random(seed), $random(seed)};
        valid_i   = (($random(seed)) & 3) != 0;                 // 75%
        ready_o   = (($random(seed)) & 3) != 0;
        ch_read   = (($random(seed)) & 15) == 0;                // occasional
        src_read  = (r_src_ready == 1'b0) && ((($random(seed)) & 3) != 0);
        dst_write = (r_dst_ready == 1'b0) && ((($random(seed)) & 3) != 0);
    end endtask

    integer lvl_i, m, cyc;
    reg [2:0] levels [0:2];
    initial begin
        levels[0] = 3'd2; levels[1] = 3'd3; levels[2] = 3'd5;
        for (lvl_i = 0; lvl_i < 3; lvl_i = lvl_i + 1) begin
            for (m = 0; m < 2; m = m + 1) begin
                rst = 1; start = 0; valid_i = 0; src_read = 0; dst_write = 0; ch_read = 0;
                sec_lvl = levels[lvl_i];
                mode = m[0];
                repeat (4) @(negedge clk);
                rst = 0;
                @(negedge clk);
                start = 1;
                @(negedge clk);
                start = 0;
                for (cyc = 0; cyc < 20000; cyc = cyc + 1) begin
                    @(negedge clk);
                    check;
                    if (r_done) begin
                        done_count = done_count + 1;
                        cyc = 20000;
                    end
                    drive;
                end
            end
        end
        if (done_count < 6) begin
            $display("COVERAGE FAIL: only %0d/6 complete runs reached done_sampler", done_count);
            $display("EQUIV RESULT: FAIL");
        end else if (errors == 0)
            $display("EQUIV RESULT: PASS checked %0d", checked);
        else
            $display("EQUIV RESULT: FAIL");
        $finish;
    end
endmodule
