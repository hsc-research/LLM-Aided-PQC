// MIT License

// Copyright (c) 2025 KU Leuven - COSIC

// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

/*
 * From our research paper "High-Performance Hardware Implementation of CRYSTALS-Dilithium"
 * by Luke Beckwith, Duc Tri Nguyen, Kris Gaj
 * at George Mason University, USA
 * https://eprint.iacr.org/2021/1451.pdf
 * =============================================================================
 * Copyright (c) 2021 by Cryptographic Engineering Research Group (CERG)
 * ECE Department, George Mason University
 * Fairfax, VA, U.S.A.
 * Author: Luke Beckwith
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *     http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * =============================================================================
 * @author   Luke Beckwith <lbeckwit@gmu.edu>
 */


`timescale 1ns / 1ps


module encoder #(
    parameter OUTPUT_W    = 4,
    parameter COEFF_W     = 23,
    parameter MAX_LVL     = 20,
    parameter W           = 64
    ) (
    input rst,
    input clk,
    input [2:0] sec_lvl,
    input [2:0] encode_mode,
    input  valid_i,
    output reg ready_i,
    input [OUTPUT_W*COEFF_W-1:0] di,
    output reg [W-1:0] dout,
    output reg valid_o,
    input  ready_o
    );
    
    reg [4:0] ENCODE_LVL;
    reg [2:0] mode;
    
    localparam
        DILITHIUM_Q = 23'd8380417,
        ENCODE_T0   = 3'd0,
        ENCODE_T1   = 3'd1,
        ENCODE_S1   = 3'd2,
        ENCODE_S2   = 3'd3,
        ENCODE_W1   = 3'd4,
        ENCODE_Z    = 3'd5;
    
    localparam
        NONE   = 3'd0,
        ETA    = 3'd1,
        T0     = 3'd2,
        T1     = 3'd3,
        GAMMA1 = 3'd4;
    
    wire [OUTPUT_W*COEFF_W-1:0] di_uncentered;
    reg  [OUTPUT_W*COEFF_W-1:0] di_uncentered_buffer;
    wire [MAX_LVL*OUTPUT_W-1:0]  stripped;
    
    reg [OUTPUT_W*COEFF_W-1:0] di_buffer;

    reg [1:0] valid_buffer;

    genvar i;
    generate
        for (i = 0; i < OUTPUT_W; i = i + 1) begin
            uncenter_coeff UNCENTER (sec_lvl, mode, di_buffer[23*i+:23], di_uncentered[23*i+:23]);
        end
    endgenerate

    zero_strip Z_STRIP(ENCODE_LVL, di_uncentered_buffer, stripped);
    
    // BANKED PISO: 144b accumulator (6-bit shift) + 4x64 word FIFO (no shift)
    reg [255:0] ACC;
    reg [7:0]   acc_len;
    reg [63:0]  fifo [3:0];
    reg [1:0]   fifo_head, fifo_tail;
    reg [2:0]   fifo_count;
    reg [9:0] buffer_len [1:0];
    wire fifo_full  = (fifo_count == 3'd4);
    wire fifo_empty = (fifo_count == 3'd0);
    wire do_pop  = (acc_len >= 8'd64) && !fifo_full;
    wire do_out;
    reg  [255:0] acc_after_pop;
    reg  [7:0]   len_after_pop;
    initial begin
        ACC = 0; acc_len = 0;
        fifo_head = 0; fifo_tail = 0; fifo_count = 0;
    end
    
    always @(*) begin
       /* ----- decoder lane connection ----- */
        ENCODE_LVL = 0;
        mode = NONE;
        
        casex({sec_lvl, encode_mode})
        {3'dX, ENCODE_T0}: begin
            ENCODE_LVL = 13;
            mode = T0;
        end
        {3'dX, ENCODE_T1}: begin
            ENCODE_LVL = 10;
            mode = T1;
        end
        {3'd2, ENCODE_S2},
        {3'd5, ENCODE_S2},
        {3'd2, ENCODE_S1},
        {3'd5, ENCODE_S1}: begin
            ENCODE_LVL = 3;
            mode = ETA;
        end
        {3'd3, ENCODE_S2},
        {3'd3, ENCODE_S1}: begin
            ENCODE_LVL = 4;
            mode = ETA;
        end   
        {3'd3, ENCODE_W1},
        {3'd5, ENCODE_W1}: begin
            ENCODE_LVL = 4;
        end
        {3'd2, ENCODE_W1}: begin
            ENCODE_LVL = 6;
        end
        {3'd2, ENCODE_Z}: begin
            ENCODE_LVL = 18;
            mode = GAMMA1;
        end
        {3'd3, ENCODE_Z},
        {3'd5, ENCODE_Z}: begin
            ENCODE_LVL = 20;
            mode = GAMMA1;
        end
        endcase
    
        
        valid_o = !fifo_empty;
        ready_i = 1;
        dout = fifo[fifo_head];
        acc_after_pop = do_pop ? (ACC >> 64) : ACC;
        len_after_pop = do_pop ? (acc_len - 8'd64) : acc_len;
    end
    assign do_out = valid_o && ready_o;
    
    always @(posedge clk) begin
        
        di_uncentered_buffer <= di_uncentered;

        valid_buffer[0] <= ready_i && valid_i;
        valid_buffer[1] <= valid_buffer[0];

        buffer_len[0] <= (ready_i && valid_i) ? 4*ENCODE_LVL : 0;
        buffer_len[1] <= buffer_len[0];
        di_buffer <= di;
        if (rst) begin
            ACC <= 0; acc_len <= 0;
            fifo_head <= 0; fifo_tail <= 0; fifo_count <= 0;
        end else begin
            // pop ACC word -> FIFO, then insert stripped at post-pop length
            if (valid_buffer[1])
                ACC <= acc_after_pop | ({176'd0, stripped} << len_after_pop);
            else
                ACC <= acc_after_pop;
            acc_len <= len_after_pop + (valid_buffer[1] ? buffer_len[1][7:0] : 8'd0);
            if (do_pop) begin
                fifo[fifo_tail] <= ACC[63:0];
                fifo_tail <= fifo_tail + 2'd1;
            end
            if (do_pop)
                $display("BANKPOP t=%0t word=%h acclen=%0d vb=%b", $time, ACC[63:0], acc_len, valid_buffer[1]);
            if (do_out)
                fifo_head <= fifo_head + 2'd1;
            fifo_count <= fifo_count + (do_pop ? 3'd1 : 3'd0) - (do_out ? 3'd1 : 3'd0);
        end
    end
    
endmodule
