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


module rejection_y #(
    parameter W            = 64,
    parameter SAMPLE_W     = 23,
    parameter BUS_W        = 4
    )(
        input  rst,
        input  clk,
        input [2:0] sec_lvl,
        input  valid_i,
        output reg ready_i,
        input  [W-1:0] rdi,
        output reg [SAMPLE_W*BUS_W-1:0] samples = 0,
        output reg valid_o = 0,
        input  ready_o
    );
    
    wire [4:0] RDI_SAMPLE_W;
    assign RDI_SAMPLE_W = (sec_lvl == 2) ? 18 : 20;
    
    
    localparam
        DILITHIUM_Q = 23'd8380417,
        GAMMA2_LIMIT  = 20'd131072,
        GAMMA3_5_LIMIT   = 20'd524288;    
    
    wire [19:0] GAMMA_LIMIT;
    assign GAMMA_LIMIT = (sec_lvl == 2) ? GAMMA2_LIMIT : GAMMA3_5_LIMIT;
    
    reg [79:0]  SIPO_IN, SIPO_IN_SHIFT;
    reg [137:0] SIPO_OUT;
    reg [3*SAMPLE_W-1:0] sipo_out_in;
    
    reg [19:0] rej_lane0, rej_lane1, rej_lane2;
    
    reg [22:0] sample0, sample1, sample2;
    reg signed [22:0] sdiff0, sdiff1, sdiff2;  // GAMMA_LIMIT - lane, sign selects +Q correction
    reg rej_lane0_valid, rej_lane1_valid, rej_lane2_valid;
    reg [1:0] num_valid;
    
    reg [6:0] sipo_in_len, sipo_in_len_next;
    (* max_fanout = 16 *) reg ge1_r = 0, ge2_r = 0, ge3_r = 0;
    reg [6:0] len_nx;
    reg [7:0] sipo_out_len, sipo_out_len_next;
    
    reg [10:0] SHIFT_IN_AMT;
    
    
    function [79:0] rdi_shifted(input [10:0] amt);
    begin
        case (amt)
            11'd0:  rdi_shifted = {16'd0, rdi};
            11'd2:  rdi_shifted = {14'd0, rdi, 2'd0};
            11'd4:  rdi_shifted = {12'd0, rdi, 4'd0};
            11'd6:  rdi_shifted = {10'd0, rdi, 6'd0};
            11'd8:  rdi_shifted = {8'd0,  rdi, 8'd0};
            11'd10: rdi_shifted = {6'd0,  rdi, 10'd0};
            11'd12: rdi_shifted = {4'd0,  rdi, 12'd0};
            11'd14: rdi_shifted = {2'd0,  rdi, 14'd0};
            11'd16: rdi_shifted = {rdi, 16'd0};
            11'd18: rdi_shifted = {rdi[61:0], 18'd0};
            11'd20: rdi_shifted = {rdi[59:0], 20'd0};
            11'd22: rdi_shifted = {rdi[57:0], 22'd0};
            11'd24: rdi_shifted = {rdi[55:0], 24'd0};
            11'd26: rdi_shifted = {rdi[53:0], 26'd0};
            default: rdi_shifted = 80'd0;  // unreachable per even/<=26 invariant; gate verifies
        endcase
    end
    endfunction

    always @(*) begin
        ready_i = (sipo_in_len < 3*RDI_SAMPLE_W) ? 1 : 0;
        valid_o = (sipo_out_len >= SAMPLE_W*BUS_W) ? 1 : 0; 
    
        if (sec_lvl == 2) begin
            rej_lane0 = {2'd0, SIPO_IN[17:0]};
            rej_lane1 = {2'd0, SIPO_IN[35:18]};
            rej_lane2 = {2'd0, SIPO_IN[53:36]};
        end else begin
            rej_lane0 = {SIPO_IN[19:0]};
            rej_lane1 = {SIPO_IN[39:20]};
            rej_lane2 = {SIPO_IN[59:40]};
        end
        
        if (ge3_r) begin
            SHIFT_IN_AMT = 3*RDI_SAMPLE_W;
        end else if (ge2_r) begin
            SHIFT_IN_AMT = 2*RDI_SAMPLE_W;
        end else if (ge1_r) begin
            SHIFT_IN_AMT = RDI_SAMPLE_W;
        end else begin
            SHIFT_IN_AMT = 0;
        end
        
        
        sdiff0 = $signed({3'b0, GAMMA_LIMIT}) - $signed({3'b0, rej_lane0});
        sample0 = sdiff0[22] ? (sdiff0 + DILITHIUM_Q) : sdiff0;
        sdiff1 = $signed({3'b0, GAMMA_LIMIT}) - $signed({3'b0, rej_lane1});
        sample1 = sdiff1[22] ? (sdiff1 + DILITHIUM_Q) : sdiff1;
        sdiff2 = $signed({3'b0, GAMMA_LIMIT}) - $signed({3'b0, rej_lane2});
        sample2 = sdiff2[22] ? (sdiff2 + DILITHIUM_Q) : sdiff2;
        
        
        rej_lane0_valid = ge1_r;
        rej_lane1_valid = ge2_r;
        rej_lane2_valid = ge3_r;
        num_valid       = rej_lane0_valid + rej_lane1_valid + rej_lane2_valid;
        
        if (rej_lane0_valid == 0)
            sample0 = 0;
        if (rej_lane1_valid == 0)
            sample1 = 0;
        if (rej_lane2_valid == 0)
            sample2 = 0;
        
        sipo_in_len_next  = (ready_i && valid_i) ? sipo_in_len + W : sipo_in_len;
        sipo_out_len_next = (valid_o && ready_o) ? sipo_out_len - SAMPLE_W*BUS_W: sipo_out_len;      
        
        SIPO_IN_SHIFT = (SIPO_IN >> SHIFT_IN_AMT);

        sipo_out_in = {sample2, sample1, sample0}; 
        samples = SIPO_OUT[SAMPLE_W*BUS_W-1:0];
    end
    
    initial begin
        SIPO_IN  = 0;
        SIPO_OUT = 0;
    
        sipo_in_len  = 0;
        sipo_out_len = 0;
    end
    
    always @(posedge clk) begin
            
        sipo_in_len <= sipo_in_len_next - SHIFT_IN_AMT;
        len_nx = sipo_in_len_next - SHIFT_IN_AMT;
        ge1_r <= (len_nx >= RDI_SAMPLE_W);
        ge2_r <= (len_nx >= 2*RDI_SAMPLE_W);
        ge3_r <= (len_nx >= 3*RDI_SAMPLE_W);
        if (valid_i) begin
            SIPO_IN <= SIPO_IN_SHIFT | rdi_shifted(sipo_in_len - SHIFT_IN_AMT);
        end else begin
            SIPO_IN <= SIPO_IN_SHIFT;
        end
        
        if (num_valid == 1) begin
            sipo_out_len <= sipo_out_len_next + SAMPLE_W;
        end else if (num_valid == 2) begin
            sipo_out_len <= sipo_out_len_next + 2*SAMPLE_W;
        end else if (num_valid == 3) begin
            sipo_out_len <= sipo_out_len_next + 3*SAMPLE_W;
        end else begin
            sipo_out_len <= sipo_out_len_next;
        end
        
        if (valid_o) begin   
            if (num_valid != 0) begin
                SIPO_OUT <= (SIPO_OUT >> SAMPLE_W*BUS_W) | sipo_out_in << sipo_out_len_next;
            end else begin
                SIPO_OUT <= SIPO_OUT >> SAMPLE_W*BUS_W;
            end
        end else if (num_valid >0) begin
            SIPO_OUT <= SIPO_OUT | sipo_out_in << sipo_out_len;
        end
        
        if (rst) begin
            SIPO_IN  <= 0;
            SIPO_OUT <= 0;
        
            sipo_in_len  <= 0;
            ge1_r <= 0; ge2_r <= 0; ge3_r <= 0;
            sipo_out_len <= 0;         
        end   
    end
    
endmodule
