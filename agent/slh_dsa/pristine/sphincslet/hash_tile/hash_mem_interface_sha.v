`timescale 1ns / 1ps

/*
 * 
 * Copyright (C): 2023
 * Author:        Sanjay Deshpande
 * Updated:       
 *          
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
 *
*/

module hash_mem_interface_sha
#(
    parameter IO_WIDTH = 64,
    parameter MAX_RAM_DEPTH = 16,

    parameter SHA_TYPE = "SHA256", //SHA256, SHA512
    parameter BLOCK_SIZE = (SHA_TYPE == "SHA512") ? 1024: 512,
    parameter LOG_BS = `CLOG2(BLOCK_SIZE),
    parameter SHA_DIGEST_SIZE = (SHA_TYPE == "SHA512") ? 512: 256

)
(
                input     wire                                                clk,
                input     wire                                                rst,
                  
                //ports for RAM connected to SHAKE256
                input     wire [IO_WIDTH-1:0]                                 i_data_in,
                output    wire [`CLOG2(MAX_RAM_DEPTH) -1:0]                   o_addr,

                output    reg                                                 o_rd_en,

                //mode = 0 data loading from BRAM, mode = 1 data loading from FIFO
                input    wire                                                i_mode,
                input    wire                                                i_mode_flag,
                //ports for FIFO connected to SHAKE256
                input    wire                                                i_fifo_o_empty,

                output    wire [IO_WIDTH-1:0]                                o_data_out,
                output    reg                                                o_data_out_valid,
                input     wire                                               o_data_out_ready,

                input     wire  [16-1:0]                                     i_input_length, // in bits
                input     wire  [10-1:0]                                     i_output_length, // in bits

                
                input     wire                                               i_start,
                output    reg                                                o_done
                  
    );    
    
localparam OFFSET = (SHA_TYPE == "SHA512") ? 128 : 64;

reg [BLOCK_SIZE-1:0] sha_input;
wire [BLOCK_SIZE-1:0] sha_input_shifted;
wire [BLOCK_SIZE-1:0] sha_input_shifted_with_in_length;
wire [BLOCK_SIZE-1:0] sha_in_block;
reg shifter_init;
reg shifter_next;

wire [IO_WIDTH-1:0] data_in_shift_reg;
wire append_mask;
wire append_mask_partial;

wire [IO_WIDTH-1:0] input_length2;
reg mode_flag;
always@(posedge clk) begin
    if(i_mode_flag) begin
        if(sha_next) begin
            mode_flag <= 1;
        end
        else begin
            mode_flag <= mode_flag;
        end
    end
    else begin
        mode_flag <= 0;
    end
end
 
assign input_length2 = mode_flag ? input_length + BLOCK_SIZE : input_length;

assign append_mask_partial = ((h_state == h_load_data || h_state == h_load_first_data) && count_hash_input == input_length_by_32 && (input_length[`CLOG2(IO_WIDTH)-1:0] != 0));
assign append_mask         = (h_state == h_sha_blocks_dom_sep && count_hash_input == input_length_by_32 && (input_length[`CLOG2(IO_WIDTH)-1:0] == 0));

assign data_in_shift_reg =  
                            (append_mask_partial == 1)? i_data_in | mask_32: 
                            (append_mask == 1)?         mask_32: 
                            (append_zeros == 1)?        {(IO_WIDTH){1'b0}}: 
                                                        i_data_in;                           

always@(posedge clk)
begin
    if (shifter_init) begin
        sha_input <= {{{(BLOCK_SIZE-IO_WIDTH)}{1'b0}},data_in_shift_reg};
    end
    else if (shifter_next) begin
        sha_input <= {sha_input[BLOCK_SIZE-IO_WIDTH-1:0],data_in_shift_reg};
    end
end

//BARREL SHIFTER
reg [LOG_BS:0] shift;
reg [LOG_BS:0] shift_minus_one;
reg [`CLOG2(IO_WIDTH):0] shift_minus_one_32;
wire [BLOCK_SIZE-1:0] mask;
wire [IO_WIDTH-1:0] mask_32;

genvar k;

always@(posedge clk)
begin
        shift_minus_one_32 <= IO_WIDTH-1-input_length[`CLOG2(IO_WIDTH)-1:0];
end


genvar j;
generate
    for (j=0;j<IO_WIDTH;j=j+1) begin
        assign mask_32[j] = (j == shift_minus_one_32) ?  1'b1 : 1'b0;
    end
endgenerate

assign sha_input_shifted = sha_input;

wire [IO_WIDTH-1:0] sel_in_length;

assign sel_in_length = last_block_448? sha_input_shifted[63:0] :input_length2;

assign sha_input_shifted_with_in_length = {sha_input_shifted[BLOCK_SIZE-1:IO_WIDTH],sel_in_length};

assign sha_in_block =   (sel_last_block)?                                               {!sel_last_block_488,{{(BLOCK_SIZE-IO_WIDTH-1)}{1'b0}},input_length2}:
                        (count_hash_input == input_length_by_32 && !full_last_block)?    sha_input_shifted_with_in_length:
                                                                                         sha_input;

 parameter STREAMING = 1;

reg sha_init;
reg sha_next;
wire sha_ready;
wire [SHA_DIGEST_SIZE-1:0] sha_digest;
wire sha_digest_valid;

generate
    if (SHA_TYPE == "SHA512") begin
      sha512_core SHA512(
               .clk(clk),
               .reset_n(!rst),

               .init(sha_init),
               .next(sha_next),
               .mode(!mode_flag),
               .mode_flag(mode_flag),

               .work_factor(0),
               .work_factor_num(0),

               .block(sha_in_block),

               .ready(sha_ready),

               .digest(sha_digest),
               .digest_valid(sha_digest_valid)
             );

    end
    else begin
        sha256_core 
            SHA256(
                .clk(clk),
                .reset_n(!rst),

                .init(sha_init),
                .next(sha_next),
                .mode(!mode_flag),
                .mode_flag(mode_flag),

                .block(sha_in_block),

                .ready(sha_ready),

                .digest(sha_digest),
                .digest_valid(sha_digest_valid)
            );
    end
endgenerate


reg [SHA_DIGEST_SIZE-1:0] sha_output;
reg capture_sha_valid;
reg [`CLOG2(MAX_RAM_DEPTH):0] count_hash_output;
always@(posedge clk)
begin
    if (capture_sha_valid && !full_last_block) begin
        sha_output <= sha_digest;
        count_hash_output <= 0;
    end
    else if ((count_hash_input_reg == input_length_by_32) && (o_data_out_ready) && (count_hash_output <= output_length_by_32)) begin
        sha_output <= {sha_output[SHA_DIGEST_SIZE-IO_WIDTH-1:0],{(IO_WIDTH){1'b0}}};
        count_hash_output <= count_hash_output + 1;
    end

    if (i_start) begin
        o_data_out_valid <= 0;
    end
    if (capture_sha_valid && !full_last_block) begin
        o_data_out_valid <= 1;
    end
    else if ((count_hash_input_reg == input_length_by_32) && (o_data_out_ready) && (count_hash_output < output_length_by_32-1)) begin
        o_data_out_valid <= 1;
    end
    else if (count_hash_output >= output_length_by_32-1) begin
        o_data_out_valid <= 0;
    end
end


assign o_data_out = sha_output[SHA_DIGEST_SIZE-1:SHA_DIGEST_SIZE-IO_WIDTH];

 reg [3:0] h_state                  =   0;
 parameter h_wait_start             =   0;
 parameter h_stall                  =   1;
 parameter h_load_first_data        =   2;
 parameter h_load_data              =   3;
 parameter h_sha_blocks_dom_sep     =   4;
 parameter h_sha_blocks_incomplete  =   5;
 parameter h_start_sha              =   6;
 parameter h_done_sha               =   7;
 parameter h_full_block             =   8;
 parameter h_done                   =   9;

reg [`CLOG2(MAX_RAM_DEPTH)-1:0] count_hash_input_reg;
reg [`CLOG2(MAX_RAM_DEPTH)-1:0] count_hash_input;
reg [`CLOG2(MAX_RAM_DEPTH)-1:0] addr;
reg [`CLOG2(MAX_RAM_DEPTH)-1:0] count_sha_blocks;
reg done_hash_load;
reg [16-1:0]           input_length_red;
reg [16-1:0]           input_length;
reg [16-6-1:0]         input_length_by_32; // in 32 bit blocks
reg [9-1:0]            input_length_mod_512; // in 32 bit blocks
reg [10-6-1:0]         output_length_by_32; // in 32 bit blocks
reg first_block;
reg en_sha_out;
assign o_addr = addr;
reg full_last_block;
reg sel_last_block;
reg sel_last_block_488;
reg last_block_448;
reg append_zeros;

always@(posedge clk)
begin
    if (rst) begin
       h_state <= h_wait_start;
       o_done <= 1'b0;
       count_sha_blocks <= 0;
       count_hash_input <= 0;
       addr <= 0;
       en_sha_out <= 0;
       full_last_block <= 0;
       sel_last_block <= 0;
       last_block_448 <= 0;
       sel_last_block_488 <= 0;
       input_length_red <= 0;
       count_hash_input_reg <= 0;
    end
    else begin
        if (h_state == h_wait_start) begin
            o_done <= 1'b0;
            first_block <= 1;
            count_sha_blocks <= 0;     
            input_length <= i_input_length;
            input_length_red <= i_input_length;
            sel_last_block <= 0;
            last_block_448 <= 0;
            sel_last_block_488 <= 0;
            count_hash_input <= 0;

            if(i_mode_flag) begin
                
                `ifdef PARAM_128
                addr <= 8; // 
                `else
                if((SHA_TYPE == "SHA512")) begin
                    addr <= 16; //
                end
                else begin
                    addr <= 8; //
                end                
                `endif
            end
            else begin
                addr <= 0; // 
            end             
            if (i_start) begin
                h_state <= h_stall;
                output_length_by_32 <= i_output_length[9:6]; //updated to divided by 64
                input_length_mod_512 <= i_input_length[LOG_BS-1:0];
                en_sha_out <= 1'b0;
                if (i_input_length[5:0] > 0) begin
                    input_length_by_32 <= i_input_length[15:6]; //updated to divided by 64
                end
                else begin
                    input_length_by_32 <= i_input_length[15:6]-1; //updated to divided by 64
                end
                if ( (i_input_length[LOG_BS-1:0] == 0)) begin 
                    full_last_block <= 1'b1;
                end
                else begin
                    full_last_block <= 1'b0;
                end   
            end
        end
        
        else if (h_state == h_stall) begin
            if (i_mode == STREAMING && i_fifo_o_empty) begin
                    h_state <= h_stall;
            end
            else begin
                h_state <= h_load_first_data;
                addr <= addr + 1; //                
            end
        end

        else if (h_state == h_load_first_data) begin
            if (i_mode == STREAMING && i_fifo_o_empty && count_hash_input != input_length_by_32) begin
                    h_state <= h_load_first_data;
            end
            else begin
                if (count_hash_input == input_length_by_32 && count_sha_blocks != BLOCK_SIZE/IO_WIDTH - 1) begin
                    count_sha_blocks <= count_sha_blocks + 1;
                    h_state <= h_sha_blocks_dom_sep;
                end
                else begin
                    h_state <= h_load_data;
                    count_sha_blocks <= count_sha_blocks + 1;
                    count_hash_input <= count_hash_input + 1; 
                    addr <= addr + 1;
                end
                if (input_length_red >= BLOCK_SIZE-OFFSET && input_length_red < BLOCK_SIZE ) begin//

                        last_block_448 <= 1;
                end
                else begin
                        last_block_448 <= 0;
                end
            end
        end

        else if (h_state == h_load_data) begin
            if (i_mode == STREAMING && i_fifo_o_empty && count_hash_input != input_length_by_32) begin
                h_state <= h_load_first_data;
            end
            else begin
                if (count_sha_blocks == BLOCK_SIZE/IO_WIDTH - 1) begin
                    count_sha_blocks <= 0;
                    h_state <= h_start_sha;
                    if (input_length_red[16-1:9] != 0 ) begin
                        input_length_red <= input_length_red - BLOCK_SIZE;
                    end
                end
                else if (count_hash_input == input_length_by_32 && count_sha_blocks != BLOCK_SIZE/IO_WIDTH - 1) begin
                    count_sha_blocks <= count_sha_blocks + 1;
                    h_state <= h_sha_blocks_dom_sep;
                end
                else begin
                    count_sha_blocks <= count_sha_blocks + 1;
                    count_hash_input <= count_hash_input + 1;
                    addr <= addr + 1;
                end
            end
        end

        else if (h_state == h_sha_blocks_dom_sep) begin
            if (count_sha_blocks == BLOCK_SIZE/IO_WIDTH - 1) begin
                 count_sha_blocks <= 0;
                 h_state <= h_start_sha;
            end
            else begin
                count_sha_blocks <= count_sha_blocks + 1;
                h_state <= h_sha_blocks_incomplete;
            end     
        end

        else if (h_state == h_sha_blocks_incomplete) begin
            if (count_sha_blocks == BLOCK_SIZE/IO_WIDTH - 1) begin
                 count_sha_blocks <= 0;
                 h_state <= h_start_sha;
            end
            else begin
                count_sha_blocks <= count_sha_blocks + 1;
            end     
        end

        else if (h_state == h_start_sha) begin
            if (sha_ready) begin
                h_state <= h_done_sha;
            end

        end

        else if (h_state == h_done_sha) begin
            first_block <= 0;
            if (count_hash_input == input_length_by_32  && sha_digest_valid && last_block_448) begin
                h_state <= h_start_sha;
                sel_last_block <= 1'b1;
                last_block_448 <= 0;
                sel_last_block_488 <= 1;
            end
            else if (count_hash_input == input_length_by_32 && sha_digest_valid && full_last_block) begin
                h_state <= h_start_sha;
                full_last_block <= 1'b0;
                sel_last_block <= 1'b1;
            end
            else if (count_hash_input == input_length_by_32 && sha_digest_valid) begin
                h_state <= h_done;
                en_sha_out <= 1'b1;
                count_hash_input_reg <= count_hash_input;
                count_hash_input <= 0;
                addr <= 0;
            end
            else if (count_hash_input < input_length_by_32) begin
                h_state <= h_load_first_data;
                count_hash_input <= count_hash_input + 1;
                addr <= addr + 1;
            end
        end

        else if (h_state == h_done) begin   
            o_done <= 1'b1;
            h_state <= h_wait_start;
        end

    end 
end



always@(*) 
begin
    case (h_state)
     h_wait_start: 
     begin
        sha_init <= 1'b0;
        sha_next <= 1'b0;
        shifter_next <= 1'b0;
        shifter_init <= 1'b0;
        capture_sha_valid <= 0;
        append_zeros <= 0;
        if (i_start) begin
            o_rd_en <= 1'b0;
        end
        else begin
            o_rd_en <= 1'b0;
        end       
     end

     h_stall:
     begin
        shifter_init <= 1'b0;
        sha_init <= 1'b0;
        sha_next <= 1'b0;
        shifter_next <= 1'b0;
        append_zeros <= 0;
        if (i_mode == STREAMING) begin
            o_rd_en <= 1'b0;
        end
        else begin
            o_rd_en <= 1'b1;
        end      
        capture_sha_valid <= 0;
     end
     
     h_load_first_data:
     begin
        shifter_init <= 1'b1;
        sha_init <= 1'b0;
        sha_next <= 1'b0;
        shifter_next <= 1'b0;
        append_zeros <= 0;
        if (i_mode == STREAMING) begin
            if (i_fifo_o_empty) begin
                o_rd_en <= 1'b0;
            end
            else begin
                o_rd_en <= 1'b1;
            end
        end
        else begin
            o_rd_en <= 1'b1;
        end
        capture_sha_valid <= 0;
     end

     
     h_load_data:
     begin
        shifter_init <= 1'b0;
        sha_init <= 1'b0;
        sha_next <= 1'b0;
        shifter_next <= 1'b1;
        append_zeros <= 0;
        if (i_mode == STREAMING) begin
            if (i_fifo_o_empty) begin
                o_rd_en <= 1'b0;
            end
            else begin
                o_rd_en <= 1'b1;
            end
        end
        else begin
            o_rd_en <= 1'b1;
        end
        capture_sha_valid <= 0;
     end

    h_sha_blocks_dom_sep: begin
        shifter_init <= 1'b0;
        sha_init <= 1'b0;
        sha_next <= 1'b0;
        shifter_next <= 1'b1;
        capture_sha_valid <= 0;
        o_rd_en <= 1'b0;

        if (count_sha_blocks == BLOCK_SIZE/IO_WIDTH) begin            
            append_zeros <= 0;
        end
        else begin
            append_zeros <= 1;
        end         
    end

    h_sha_blocks_incomplete: begin
        shifter_init <= 1'b0;
        sha_init <= 1'b0;
        sha_next <= 1'b0;
        shifter_next <= 1'b1;
        capture_sha_valid <= 0;
        o_rd_en <= 1'b0;
        append_zeros <= 1;
    end
     
     h_start_sha:
     begin
        if (i_mode == STREAMING) begin
            o_rd_en <= 1'b0;
        end
        else begin
            o_rd_en <= 1'b1;
        end
        capture_sha_valid <= 0;
        if (sha_ready) begin
            if (first_block) begin
                sha_init <= 1'b1;
                sha_next <= 1'b0;
            end
            else begin
                sha_next <= 1'b1;
                sha_init <= 1'b0;
            end
        end
        else begin
            sha_init <= 1'b0;
            sha_next <= 1'b0;
        end
         shifter_next <= 1'b0;
         shifter_init <= 1'b0;
         append_zeros <= 0;
     end

     h_done_sha:
     begin
        shifter_init <= 1'b0;
        sha_init <= 1'b0;
        sha_next <= 1'b0;
        shifter_next <= 1'b0;

        if (count_hash_input < input_length_by_32) begin //
            if (i_mode == STREAMING) begin
                o_rd_en <= 1'b0;
            end
            else begin
                o_rd_en <= 1'b1;
            end   
        end
        else begin
            o_rd_en <= 1'b0;
        end
        append_zeros <= 0;
        capture_sha_valid <= 0;
     end

     h_done:
     begin
        shifter_init <= 1'b0;
        sha_init <= 1'b0;
        sha_next <= 1'b0;
        shifter_next <= 1'b0;
        o_rd_en <= 1'b0;
        capture_sha_valid <= 1;
        append_zeros <= 0;
     end


     default: begin
        shifter_init <= 1'b0;
        sha_init <= 1'b0;
        sha_next <= 1'b0;
        shifter_next <= 1'b0;
        o_rd_en <= 1'b0;
        capture_sha_valid <= 0;
        append_zeros <= 0;
     end
   
    endcase
end 
    
endmodule
