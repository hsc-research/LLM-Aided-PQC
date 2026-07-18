#!/usr/bin/env python3
import shutil, sys, os
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/PQC/hqc/agent/mldsa/mldsa_src"
SRC = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src/encoder.v"
F = os.path.join(D, "encoder.v")
shutil.copy(SRC, F)  # start from pristine
shutil.copy(F, F + ".bak")
src = open(F).read()

old_decl = """    reg [255:0] PISO;
    reg [9:0]  piso_len, piso_len_next;
    reg [9:0] buffer_len [1:0];
    
    initial begin
        PISO = 0;
        piso_len = 0;        
    end"""
new_decl = """    // BANKED PISO: 144b accumulator (6-bit shift) + 4x64 word FIFO (no shift)
    reg [191:0] ACC;
    reg [7:0]   acc_len;
    reg [63:0]  fifo [3:0];
    reg [1:0]   fifo_head, fifo_tail;
    reg [2:0]   fifo_count;
    reg [9:0] buffer_len [1:0];
    wire fifo_full  = (fifo_count == 3'd4);
    wire fifo_empty = (fifo_count == 3'd0);
    wire do_pop  = (acc_len >= 8'd64) && !fifo_full;
    wire do_out;
    reg  [191:0] acc_after_pop;
    reg  [7:0]   len_after_pop;
    initial begin
        ACC = 0; acc_len = 0;
        fifo_head = 0; fifo_tail = 0; fifo_count = 0;
    end"""
assert src.count(old_decl) == 1, "decl anchor"
src = src.replace(old_decl, new_decl)

old_comb = """        valid_o = (piso_len >= W) ? 1 : 0; 
        piso_len_next = (valid_o && ready_o) ? piso_len - W: piso_len;   
        ready_i = 1;
        
        dout = PISO[W-1:0];
    end"""
new_comb = """        valid_o = !fifo_empty;
        ready_i = 1;
        dout = fifo[fifo_head];
        acc_after_pop = do_pop ? (ACC >> 64) : ACC;
        len_after_pop = do_pop ? (acc_len - 8'd64) : acc_len;
    end
    assign do_out = valid_o && ready_o;"""
assert src.count(old_comb) == 1, "comb anchor"
src = src.replace(old_comb, new_comb)

old_seq = """        piso_len <= piso_len_next + buffer_len[1];

        di_buffer <= di;
        if (rst) begin
            piso_len <= 0;
            PISO     <= 0;
        end else begin
            if (valid_buffer[1]) begin
                if (valid_o && ready_o) begin
                    PISO <= (PISO >> W) | ({192'd0, stripped} << piso_len_next);
                end else begin
                    PISO <= PISO | ({192'd0, stripped} << piso_len_next);    
                end
            end else if (valid_o && ready_o) begin
                PISO <= (PISO >> W);
            end
        end
    end"""
new_seq = """        di_buffer <= di;
        if (rst) begin
            ACC <= 0; acc_len <= 0;
            fifo_head <= 0; fifo_tail <= 0; fifo_count <= 0;
        end else begin
            // pop ACC word -> FIFO, then insert stripped at post-pop length
            if (valid_buffer[1])
                ACC <= acc_after_pop | ({112'd0, stripped} << len_after_pop);
            else
                ACC <= acc_after_pop;
            acc_len <= len_after_pop + (valid_buffer[1] ? buffer_len[1][7:0] : 8'd0);
            if (do_pop) begin
                fifo[fifo_tail] <= ACC[63:0];
                fifo_tail <= fifo_tail + 2'd1;
            end
            if (do_out)
                fifo_head <= fifo_head + 2'd1;
            fifo_count <= fifo_count + (do_pop ? 3'd1 : 3'd0) - (do_out ? 3'd1 : 3'd0);
        end
    end"""
assert src.count(old_seq) == 1, "seq anchor"
src = src.replace(old_seq, new_seq)
open(F, "w").write(src)
final = open(F).read()
assert "ACC" in final and "PISO" not in final.replace("BANKED PISO","")
print("BANKED PISO APPLIED")
