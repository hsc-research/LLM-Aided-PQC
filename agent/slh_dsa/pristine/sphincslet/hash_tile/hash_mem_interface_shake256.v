`timescale 1ns / 1ps
//`include "clog2.v"

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

module hash_mem_interface_shake256
#(
    parameter IO_WIDTH = 64,
    parameter MAX_RAM_DEPTH = 16,
    parameter MAX_MSG_SIZE = 32_768 //in bits, e.g., 1 MB= 8388608 bits
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
                //ports for FIFO connected to SHAKE256
                input    wire                                                i_fifo_o_empty,

                output    wire [IO_WIDTH-1:0]                                o_data_out,
                output    reg                                                o_data_out_valid,
                input     wire                                               o_data_out_ready,

                input     wire  [16-1:0]                               i_input_length, // in bits
                input     wire  [10-1:0]                               i_output_length, // in bits

                
                input     wire                                               i_start,
                output    wire                                               o_done
                  
    );    
    

 parameter STREAMING = 1;

 reg [16-1:0] input_length;
 reg [16-1:0] input_length_reg;
 reg [1:0] sel_din;

 assign o_addr = h_addr[`CLOG2(MAX_RAM_DEPTH)-1:0];

// new shake signals
 wire [63:0] shake_din_64;
 reg shake_din_valid_64;
 reg [1:0] count_shake_din;
 reg start_shake256;
 reg last_shake_din_64;
 wire [3:0] last_shake_din_byte;
 reg shake_dout_ready_64;
 wire shake_din_ready_64;
 wire [63:0] shake_dout_64;
 wire shake_dout_valid_64;

assign last_shake_din_byte = i_mode==1 ? (i_input_length[5:3]==3'd0 ? 8 : i_input_length[5:3]) : 8;

wire [10-1:0] i_input_length_adjust;
assign i_input_length_adjust = ((i_input_length - 1)>>6);
 
 reg [5:0] test_count_64;
 always@(posedge clk)
 begin
    if (rst) begin
        test_count_64 <= 0;
    end
    else if (shake_din_valid_64) begin
        test_count_64 <= test_count_64 + 1;
    end
 end


assign shake_din_64 = i_data_in;

shake256_top shake256 (
  .clk_i             (clk          ),//system clock
  .rst_ni            (~rst         ),//system reset, active low
  .start_i           (start_shake256        ),//start of SHAKE process, 1 clock pulse, assert before putting input data
  .din_i             (shake_din_64          ),//data input
  .din_valid_i       (shake_din_valid_64    ),//data input valid signal, transaction happens when both din_valid_i and din_ready_o HIGH
  .last_din_i        (last_shake_din_64     ),//last data input, also used as first data output squeeze
  .last_din_byte_i   (last_shake_din_byte   ),//byte length of last data input, 0 to 8 for DW=64
  .dout_ready_i      (shake_dout_ready_64   ),//signal to request output data, transaction happens when both dout_ready_i and dout_valid_o HIGH
  .din_ready_o       (shake_din_ready_64   ),//signal showing shake module ready to receive input data, transaction happens when both din_valid_i and din_ready_o HIGH
  .dout_o            (o_data_out         ),//data output
  .dout_valid_o      (shake_dout_valid_64  ) //data output valid signal, transaction happens when both dout_ready_i and dout_valid_o HIGH
);

 reg [2:0] h_state              =   0;
 parameter h_wait_start         =   0;
 parameter h_check_shake_ready  =   1;
 parameter h_load_shake         =   2;
 parameter h_load_second_block  =   3;
 parameter h_wait_for_output  =   4;
 parameter h_load_second_block_out  =   5;

reg [`CLOG2(MAX_RAM_DEPTH)-1:0] count_hash_input;
reg done_hash_load;
reg [`CLOG2(MAX_MSG_SIZE)-1:0] h_addr;
reg [10-1:0] output_length_reg;

reg shake_din_ready_64_d;

always@(posedge clk) begin
    if(rst) begin
        shake_din_ready_64_d <= 1'b0;
    end
    else begin
        shake_din_ready_64_d <= shake_din_ready_64;
    end
end

always@(posedge clk)
begin
    if (rst) begin
        h_state <= h_wait_start;
        done_hash_load <= 1'b0;
        h_addr <= 0;
        count_hash_input <= 0;
    end
    else begin
        if (h_state == h_wait_start) begin
            done_hash_load <= 1'b0;
            if (i_start) begin
				h_state <= h_check_shake_ready;
                input_length_reg <= i_input_length;  
                input_length <= i_input_length;  
                output_length_reg <= i_output_length[9:0];
			end
            else begin
                h_addr <= 0;
            end
        end
        
        else if (h_state == h_check_shake_ready) begin
            if (shake_din_ready_64) begin
                if (i_mode == STREAMING) begin
                    if (~i_fifo_o_empty) begin
                        h_state <= h_load_shake;
                    end  
                end
                else begin
                    h_state <= h_load_shake;
                    h_addr <= h_addr + 1;
                    input_length_reg <= input_length_reg - 64;
                    count_hash_input <= count_hash_input + 1;
                end
            end
        end
		
		else if (h_state == h_load_shake) begin
            if (i_mode == STREAMING) begin
                if (~i_fifo_o_empty) begin
                    if (((h_addr == i_input_length_adjust))) begin
                        h_addr <= 0;
                        count_hash_input <= 0;
                        h_state <= h_wait_for_output;
                        done_hash_load <= 1'b1;
                    end
                    else begin
                        done_hash_load <= 1'b0;
                        if (shake_din_ready_64) begin
                            h_state <= h_load_shake;
                            count_hash_input <= count_hash_input + 1;
                            h_addr <= h_addr+1;
                        end
                    end
                end
            end
            else begin           
                if (input_length_reg < 64) begin
                    h_addr <= 0;
                    count_hash_input <= 0;
                    h_state <= h_wait_for_output;
                    done_hash_load <= 1'b1;
                end
                else begin
                    done_hash_load <= 1'b0;
                    if (!shake_din_ready_64 && shake_din_ready_64_d) begin
                        h_state <= h_load_shake;
                        h_addr <= h_addr-1;
                        count_hash_input <= count_hash_input - 1; 
                        input_length_reg <= input_length_reg + 64;
                    end
                    else if (shake_din_ready_64) begin
                        h_state <= h_load_shake;
                        h_addr <= h_addr+1;
                        count_hash_input <= count_hash_input + 1; 
                        if (count_shake_din == 2) begin
                            count_shake_din <= 1;
                        end
                        else begin
                            count_shake_din <= 1;
                        end
                        input_length_reg <= input_length_reg - 64;
                    end
                
                end

                
            end
	    end


        else if (h_state == h_wait_for_output) begin
            if (output_length_reg-64 <= 0) begin
                if (i_start) begin
                    h_state <= h_check_shake_ready;
                    input_length_reg <= i_input_length;  
                    input_length <= i_input_length;  
                    output_length_reg <= i_output_length[9:0];
                end
                else begin
                    h_state <= h_wait_start;
                end
                h_addr <= 0;
                done_hash_load <= 1'b0;
                count_hash_input <= 0;
            end
            else if (shake_dout_valid_64 && o_data_out_ready) begin

                output_length_reg <= output_length_reg - 64;
            end
           

                
        end
			
    end 
end


always@(h_state, i_start, shake_din_ready_64, shake_dout_valid_64, input_length_reg, count_hash_input, i_mode, i_fifo_o_empty, h_addr, input_length) 
begin
    case (h_state)
     h_wait_start: 
     begin
        shake_din_valid_64 <= 0;
        last_shake_din_64 <= 0;
        o_data_out_valid <= 0;
        shake_dout_ready_64 <= 0;
        if (i_start) begin
            sel_din <= 1; 
            o_rd_en <= 0;
            start_shake256 <= 1;
        end
        else begin
            sel_din <= 0;
            o_rd_en <= 0;
            start_shake256 <= 0;
        end
     end
     
      h_check_shake_ready:
      begin
         start_shake256 <= 0;
         last_shake_din_64 <= 0;
         o_data_out_valid <= 0;
         if (i_mode == STREAMING) begin
                 o_rd_en <= 0;
         end
         else begin
             o_rd_en <= 1;  
         end
      end


     
     h_load_shake:
     begin
        sel_din <= 0;
        start_shake256 <= 0;
        o_data_out_valid <= 0;
        if (i_mode) begin
            if (~i_fifo_o_empty) begin
                if (shake_din_ready_64) begin
                    if (((h_addr == i_input_length_adjust))) begin
                        last_shake_din_64 <= 1;
                    end
                    else begin
                        last_shake_din_64 <= 0;
                    end
                    shake_din_valid_64 <= 1'b1;
                end
                else begin
                    shake_din_valid_64 <= 1'b0;
                    last_shake_din_64 <= 0;
                end
            end
            else begin
                shake_din_valid_64 <= 1'b0;
                last_shake_din_64 <= 0;
            end 
        end
        else begin
            if (shake_din_ready_64 && shake_din_ready_64_d) begin
                shake_din_valid_64 <= 1;
                if (input_length_reg < 64) begin
                    last_shake_din_64 <= 1;
                end
                else begin
                    last_shake_din_64 <= 0;
                end
            end
            else begin
                shake_din_valid_64 <= 0;
            end

        end

        if (i_mode == STREAMING) begin
            if (shake_din_ready_64) begin
                if (~i_fifo_o_empty) begin
                    if ((count_hash_input == input_length[16-1:`CLOG2(IO_WIDTH)] - 1) && (input_length <= 1088)) begin                        
                        o_rd_en <= 1;
                    end
                    else if (((count_hash_input == input_length[16-1:`CLOG2(IO_WIDTH)] + 1) && (input_length > 1088))) begin
                        o_rd_en <= 0;
                    end
                    else if (count_hash_input == 1088/IO_WIDTH) begin
                        if (shake_din_ready_64) begin
                            o_rd_en <= 1;
                        end
                    end
                    else begin
                        if (shake_din_ready_64) begin
                            o_rd_en <= 1; 
                        end
                    end
                end
                else begin
                    o_rd_en <= 0;
                end
            end
            else begin    
                o_rd_en <= 0;
            end
            end
        else begin 
            o_rd_en <= 1;
        end        
     end

     h_wait_for_output: begin
        shake_din_valid_64 <= 0;
        last_shake_din_64 <= 0;
        if (shake_dout_valid_64 && o_data_out_ready) begin
            shake_dout_ready_64 <= 1;
        end
        else begin
            shake_dout_ready_64 <= 0;
        end 
        o_data_out_valid <= shake_dout_valid_64;

        if (i_start) begin
            sel_din <= 1; 
            o_rd_en <= 0;
            start_shake256 <= 1;
        end
        else begin
            sel_din <= 0;
            o_rd_en <= 0;
            start_shake256 <= 0;
        end
     end

    
        
	  default: 
	  begin
        sel_din <= 0;
        o_rd_en <= 0;
        start_shake256 <= 0;
        shake_din_valid_64 <= 0;
        last_shake_din_64 <= 0;
        o_data_out_valid <= 0;
        shake_dout_ready_64 <= 0;
        
	  end         
      
    endcase

end 
 
    
    
endmodule
