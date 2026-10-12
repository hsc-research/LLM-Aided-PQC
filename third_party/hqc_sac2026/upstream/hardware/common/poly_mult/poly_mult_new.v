`timescale 1ns / 1ps
/*

 * 
 *
 * Copyright (C) 2025
 * Author: Sanjay Deshpande <sanjay.deshpande1@northwestern.edu>
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
//`include "clog2.v"


`define CLOG2(x) ( \
  (x <= 2) ? 1 : \
  (x <= 4) ? 2 : \
  (x <= 8) ? 3 : \
  (x <= 16) ? 4 : \
  (x <= 32) ? 5 : \
  (x <= 64) ? 6 : \
  (x <= 128) ? 7 : \
  (x <= 256) ? 8 : \
  (x <= 512) ? 9 : \
  (x <= 1024) ? 10 : \
  (x <= 2048) ? 11 : \
  (x <= 4096) ? 12 : \
  (x <= 8192) ? 13 : \
  (x <= 16384) ? 14 : \
  (x <= 32768) ? 15 : \
  (x <= 65536) ? 16 : \
  (x <= 131072) ? 17 : \
  (x <= 262144) ? 18 : \
  (x <= 524288) ? 19 : \
  (x <= 1048576) ? 20 : \
  (x <= 2097152) ? 21 : \
  (x <= 4194304) ? 22 : \
  (x <= 8388608) ? 23 : \
  (x <= 16777216) ? 24 : \
  (x <= 33554432) ? 25 : \
  (x <= 67108864) ? 26 : \
  (x <= 134217728) ? 27 : \
  (x <= 268435456) ? 28 : \
  (x <= 536870912) ? 29 : \
  (x <= 1073741824) ? 30 : \
  -1)

`define DIVCLOG2(x) ( \
  (x <= 1) ? 0 : \
  (x <= 2) ? 1 : \
  (x <= 4) ? 2 : \
  (x <= 8) ? 3 : \
  (x <= 16) ? 4 : \
  (x <= 32) ? 5 : \
  (x <= 64) ? 6 : \
  (x <= 128) ? 7 : \
  (x <= 256) ? 8 : \
  (x <= 512) ? 9 : \
  (x <= 1024) ? 10 : \
  (x <= 2048) ? 11 : \
  (x <= 4096) ? 12 : \
  (x <= 8192) ? 13 : \
  (x <= 16384) ? 14 : \
  (x <= 32768) ? 15 : \
  (x <= 65536) ? 16 : \
  (x <= 131072) ? 17 : \
  (x <= 262144) ? 18 : \
  (x <= 524288) ? 19 : \
  (x <= 1048576) ? 20 : \
  (x <= 2097152) ? 21 : \
  (x <= 4194304) ? 22 : \
  (x <= 8388608) ? 23 : \
  (x <= 16777216) ? 24 : \
  (x <= 33554432) ? 25 : \
  (x <= 67108864) ? 26 : \
  (x <= 134217728) ? 27 : \
  (x <= 268435456) ? 28 : \
  (x <= 536870912) ? 29 : \
  (x <= 1073741824) ? 30 : \
  -1)




module mem_dual_2r1w
#(
  parameter WIDTH = 512,
  parameter DEPTH = 70,
  parameter FILE  = "",
 parameter INIT  = 0
)
(
  input  wire                         clock,


  input  wire [WIDTH-1:0]             wdata,
  input  wire [`CLOG2(DEPTH)-1:0]     waddr,
  input  wire                         wren,       


  input  wire [`CLOG2(DEPTH)-1:0]     address_0,
  input  wire [`CLOG2(DEPTH)-1:0]     address_1,
  output reg  [WIDTH-1:0]             q_0,
  output reg  [WIDTH-1:0]             q_1
);

  (* ram_style = "distributed" *) reg [WIDTH-1:0] mem [0:DEPTH-1];
  integer i;
  initial begin
    if (FILE != "")
      $readmemb(FILE, mem);
    else if (INIT)
      for (i = 0; i < DEPTH; i = i + 1)
        mem[i] = {WIDTH{1'b0}};
  end


  always @(posedge clock) begin
    if (wren) begin
      mem[waddr] <= wdata;
   end

  
    if (wren && (waddr == address_0))
      q_0 <= wdata;
    else
      q_0 <= mem[address_0];


    if (wren && (waddr == address_1))
      q_1 <= wdata;
    else
      q_1 <= mem[address_1];
  end

endmodule



module poly_mult_new
#( 

    parameter parameter_set = "hqc128",
    
    parameter MAX_WEIGHT = (parameter_set == "hqc128")? 75: 
                           (parameter_set == "hqc192")? 114:
			               (parameter_set == "hqc256")? 149:
			               (parameter_set == "bike")? 71:
                                                        4,
                                                        
    parameter WEIGHT = (parameter_set == "hqc128")? 66: 
                       (parameter_set == "hqc192")? 100:
			           (parameter_set == "hqc256")? 131:
			           (parameter_set == "bike")? 71:
                                                    4,
    
    parameter N = (parameter_set == "hqc128")? 17_669:
				  (parameter_set == "hqc192")? 35_851:
			      (parameter_set == "hqc256")? 57_637: 
			      (parameter_set == "bike")?  12_323: 
                                               31,
    
    parameter M = (parameter_set == "hqc128")? 15:
				  (parameter_set == "hqc192")? 16:
			      (parameter_set == "hqc256")? 16: 
			      (parameter_set == "bike")?   14: 
                                               4, 
                                               
                                               
                                               
    parameter RAMWIDTH = 128, // Width of each chunk W needs to be divided in to. Best to choose a 2 power
    parameter TWO_N = 2*N,
    parameter W_RAMWIDTH = TWO_N + (RAMWIDTH-TWO_N%RAMWIDTH)%RAMWIDTH, 
//    parameter W_RAMWIDTH = N + (RAMWIDTH-N%RAMWIDTH)%RAMWIDTH, 
    parameter W = W_RAMWIDTH + RAMWIDTH*((W_RAMWIDTH/RAMWIDTH)%2),
    parameter X = W/RAMWIDTH,
    
    parameter LOGX = `CLOG2(X), 
    parameter LOG_RAMWIDTH = `CLOG2(RAMWIDTH),
    parameter Y = X/2,
	parameter LOGW = `CLOG2(W),
	parameter W_BY_X = W/X, 
	parameter W_BY_Y = W/Y, // This number needs to be a power of 2 for optimized synthesis
	parameter RAMSIZE = X,
	parameter ADDR_WIDTH = `CLOG2(RAMSIZE),
    parameter LOG_MAX_WEIGHT = `CLOG2(MAX_WEIGHT)
)
(
    input clk,
    input rst,
    input start,
    
	
	// Shift value (location of 1 fro  FixedWeight vector) loading
	input [M-1:0] loc_in,
    input [LOG_MAX_WEIGHT:0] weight,
	output reg [LOGW-1:0] loc_addr,
	
	// Random Bit Vector loading 
	input [W_BY_X-1:0]mux_word_0,
	input [W_BY_X-1:0]mux_word_1,
	output  [ADDR_WIDTH-1:0]addr_0,
	output  [ADDR_WIDTH-1:0]addr_1,
	
    // Mul result
	output reg valid,
	input rd_dout,
    input [`CLOG2(RAMSIZE/2)-1:0]addr_result,
	output [W_BY_X-1:0]dout,
	
	//adder ports
	input add_wr_en,
	input [`CLOG2(RAMSIZE/2)-1:0] add_addr,
	input [RAMWIDTH-1:0] add_in
    
    );

//wire [W_BY_X-1:0]dshift;

wire [W_BY_Y-1:0]mux_word;
//wire [W_BY_X-1:0]mux_word_0;
//wire [W_BY_X-1:0]mux_word_1;

reg wren_0 = 0;
reg wren_1 = 0;

wire [ADDR_WIDTH-1:0] RAMSIZE_minus_shift;

reg [ADDR_WIDTH-1:0]addr_0_reg = 0;
reg [ADDR_WIDTH-1:0]addr_1_reg = 0;

wire [LOGW-1:0]shift_int;
wire [W_BY_Y-1:0]outa;

wire [LOGW-1:0]shift_mul_chunks;
wire [LOGW-1:0]shift_mul_chunks_plus_1;
wire [`CLOG2(W_BY_X):0]shift_int_mask;

reg [ADDR_WIDTH:0] count_chunks=0;
wire [ADDR_WIDTH:0] count_chunks_reg;

reg [ADDR_WIDTH+1:0] count_chunks_inter_mem=0;

wire [W_BY_X-1:0] mask;

wire [LOGW-1:0]shift;

reg [M-1:0] loc_in_reg;

assign addr_0 = addr_0_reg;
assign addr_1 = addr_1_reg;

always@(posedge clk)
begin
    loc_in_reg <= loc_in;
end
  
assign shift = loc_in_reg;
//assign shift = loc_in;
assign mux_word = {mux_word_0,mux_word_1};



assign shift_int = shift % (W_BY_X);  /////

parameter LOG_W_BY_X = `CLOG2(W_BY_X);






localparam LOG_WIDTH = `CLOG2(W_BY_X);      // e.g., 7 for 128-bit
localparam HALF_LOG  = LOG_WIDTH / 2;       // e.g., 3
localparam TOP_BITS  = LOG_WIDTH - HALF_LOG;// e.g., 4


wire [HALF_LOG-1:0] fine_amount   = shift_int[HALF_LOG-1:0];
wire [TOP_BITS-1:0] coarse_amount = shift_int[LOG_WIDTH-1:HALF_LOG];


reg [W_BY_Y-1:0] stage_1_data; 
reg [HALF_LOG-1:0] saved_fine_amount;

reg [W_BY_X-1:0] dshift;

always @ (posedge clk) begin


    stage_1_data <= mux_word << {coarse_amount, {HALF_LOG{1'b0}}};
    saved_fine_amount <= fine_amount;
    dshift <= (stage_1_data << saved_fine_amount) >> (W_BY_X); // Adjust slice as needed

end



reg [2:0] inter_mem_wr_delay = 0;

reg [W_BY_X-1:0] din_0_intermediate; 
wire [ADDR_WIDTH-1:0] addr_0_intermediate_mux;
wire [ADDR_WIDTH-1:0] addr_1_intermediate_mux;
reg wren_0_intermediate;
reg wren_0_intermediate_reg;

wire [W_BY_X-1:0] q_0_intermediate;
wire [W_BY_X-1:0] q_1_intermediate;



// interleaved reduction logic


wire [W_BY_X-1:0] din_0;
reg [W_BY_X-1:0] qout_1_reg;
wire [W_BY_X-1:0] din_1;
wire [W_BY_X-1:0] qout_0;




wire [W_BY_X-1:0] qout_1;
reg [W_BY_X-1:0] dshift_reg;

wire [W_BY_X-1:0] adjusted_msb;
wire [W_BY_X-1:0] adjusted_last_msb;
wire [W_BY_X-1:0] last_lsb;
wire [W_BY_X-1:0] adjusted_lsb;
wire [W_BY_X-1:0] lsb_xor_msb_high;

wire [W_BY_X-1:0] xor_in_0;
wire [W_BY_X-1:0] xor_in_1;

parameter DIFF_BITS = (W_BY_X - (N)%W_BY_X)%W_BY_X;
reg [ADDR_WIDTH-1:0] addr_0_intermediate_reg;

always@(posedge clk) 
begin
    dshift_reg <= dshift;
    qout_1_reg <= qout_1;
    addr_0_intermediate_reg <= addr_0_intermediate;
end



assign adjusted_msb = (addr_0_intermediate == RAMSIZE/2 - 1)?{{(DIFF_BITS){1'b0}},dshift[(RAMWIDTH-DIFF_BITS)-1:0]} : 
                                                                 {dshift[RAMWIDTH-DIFF_BITS-1: 0], dshift_reg[RAMWIDTH-1:RAMWIDTH-DIFF_BITS]};

assign adjusted_lsb = qout_1_reg;



assign xor_in_0 = (addr_0_intermediate < RAMSIZE/2 - 1)? dshift : adjusted_lsb;
assign xor_in_1 = (addr_0_intermediate < RAMSIZE/2 - 1)? qout_1_reg : adjusted_msb;


assign din_0 = (state == S_CLEAR_INTER_MEM)? 0: xor_in_0 ^ xor_in_1;
            
 
 
reg [ADDR_WIDTH-1:0] addr_0_int_red_mem;
reg [ADDR_WIDTH-1:0] addr_1_int_red_mem;


assign dout = qout_0;
               


mem_dual_2r1w #(.WIDTH(W_BY_X), .DEPTH(RAMSIZE/2)) INTERLEAVED_RED_MEM (
  .clock(clk),
  .waddr(add_wr_en? add_addr: (rd_dout? addr_result :addr_0_int_red_mem)),     //address_0 for writes
  .wdata(add_wr_en? add_in :din_0),        //data_0 as wdata
  .wren(add_wr_en? add_wr_en: wren_0_intermediate),
  .address_0(rd_dout? addr_result :addr_0_int_red_mem),       // single write enable
  .address_1(add_wr_en? add_addr:addr_1_int_red_mem),
  .q_0(qout_0),
  .q_1(qout_1)
);



reg [ADDR_WIDTH-1:0] addr_0_intermediate;

assign RAMSIZE_minus_shift = (RAMSIZE - shift[LOGW-1:LOGW-ADDR_WIDTH]);

reg [3:0] state = 0;
parameter S_WAIT_START_L            =   0;
parameter S_CLEAR_INTER_MEM         =   1;
parameter S_LOAD_DONE_L	         =   2;
parameter S_ADDR_SETTING            =   3;
parameter S_SHIFT_L                 =   4;
parameter S_MUL_DONE                =   5;
parameter S_REDUCTION_START         =   6;
parameter S_WAIT_REDUCTION          =   7;
parameter S_REDUCTION_DONE          =   8;

parameter S_STALL          =   9;



reg [3:0] mux_delay;

assign count_chunks_reg = addr_0_intermediate + 1;

always@(posedge clk)
begin
    if (rst) begin

        state <= S_WAIT_START_L;
        	dshift <= 0;
        	mux_delay <= 1;
        	stage_1_data <= 0;
        	saved_fine_amount <= 0;
		addr_0_reg <=  0;
		addr_1_reg <=  0;
		count_chunks <= 0;
		loc_addr <= 0;
		valid <= 1'b0;
		
		//intermediate mem
		din_0_intermediate <= 0; 
        addr_0_intermediate <= 0;
        wren_0_intermediate <= 0;
        count_chunks_inter_mem <= 0;
        
        addr_0_int_red_mem <= 0;
        addr_1_int_red_mem <= 0;
    end
    else if (rd_dout == 0) begin
		
        if (state == S_WAIT_START_L) begin
			count_chunks <=0;
			valid <= 1'b0;
			
			//intermediate mem
            din_0_intermediate <= 0; 
            addr_0_intermediate <= 0;
            wren_0_intermediate <= 0;
            count_chunks_inter_mem <= 0;
            inter_mem_wr_delay <= 0;
            
            addr_0_int_red_mem <= 0;
            addr_1_int_red_mem <= 0;
			
			if (start) begin

			    state <= S_CLEAR_INTER_MEM; 
				
				if (shift[LOGW-1:LOGW-ADDR_WIDTH] == 0) begin
				    addr_0_reg <=0;
				end
				else begin
				    if (RAMSIZE_minus_shift > Y - 1) begin
                        addr_0_reg <= 0;
                    end
                    else begin
                        addr_0_reg <=RAMSIZE_minus_shift;
                    end
				end
				
				if (shift[LOGW-1:LOGW-ADDR_WIDTH] == RAMSIZE-1) begin
				    addr_1_reg <=0;
				end
				else begin
				    if (RAMSIZE_minus_shift > Y - 1) begin
                        addr_1_reg <= RAMSIZE-1;
                     end
                     else begin
                        addr_1_reg <=(RAMSIZE_minus_shift - 1);
                     end
				end
				
				loc_addr <= 0;	
				din_0_intermediate <= 0; 
				addr_0_intermediate <= 0;
				wren_0_intermediate <= 1;
			end
        end 
        
        
        else if (state == S_CLEAR_INTER_MEM) begin

			if (count_chunks_inter_mem == RAMSIZE/2) begin
			    state <= S_ADDR_SETTING;
				count_chunks_inter_mem <= 0;
                addr_0_intermediate <= 0;
				wren_0_intermediate <= 0;
			end
			else begin
				//clear the intermediate mem
                din_0_intermediate <= 0; 
                wren_0_intermediate <= 1;
                count_chunks_inter_mem <= count_chunks_inter_mem +1;
                
                if (addr_0_intermediate + 1 == RAMSIZE/2) begin
                    addr_0_intermediate <=0;
                    addr_0_int_red_mem <=0;
                end
                else begin
                   addr_0_intermediate <= (addr_0_intermediate + 1);
                   addr_0_int_red_mem <=  (addr_0_int_red_mem + 1);
                end
                

                
			end	
		end
        
        
        else if (state == S_ADDR_SETTING) begin

            if (shift[LOGW-1:LOGW-ADDR_WIDTH] == 0) begin
                addr_0_reg <=0;
            end
            else begin
                    if (RAMSIZE_minus_shift > Y - 1) begin
                        addr_0_reg <= 0;
                    end
                    else begin
                        addr_0_reg <=RAMSIZE_minus_shift;
                    end
            end
            
            if (shift[LOGW-1:LOGW-ADDR_WIDTH] == RAMSIZE-1) begin
                addr_1_reg <=0;
            end
            else begin
                if (RAMSIZE_minus_shift > Y - 1) begin
                    addr_1_reg <= RAMSIZE-1;
                 end
                 else begin
                    addr_1_reg <=(RAMSIZE_minus_shift - 1);
                 end
            end
            
            
		    state <= S_SHIFT_L;

            inter_mem_wr_delay <= 4;
            wren_0_intermediate <= 0;
            addr_0_intermediate <= ((loc_in/RAMWIDTH) - 1);
            
            addr_0_int_red_mem <= ((loc_in/RAMWIDTH) - 1);
            addr_1_int_red_mem <= ((loc_in/RAMWIDTH));
        end
		
	else if (state == S_STALL) begin
		   state <= S_SHIFT_L;
	end
		
	else if (state == S_SHIFT_L) begin
            // read the intermediate value and xor with the shifted values
            if (inter_mem_wr_delay == 0) begin
                wren_0_intermediate <= 0;
                addr_0_intermediate <= (addr_0_intermediate + 1);
                inter_mem_wr_delay <= 1;
                
                if (addr_0_int_red_mem == RAMSIZE/2 - 1) begin
                    addr_0_int_red_mem <= 0;
                end
                else begin
                    addr_0_int_red_mem <= (addr_0_int_red_mem + 1);
                end
                if (addr_1_int_red_mem == RAMSIZE/2 - 1) begin
                    addr_1_int_red_mem <= 0;
                end
                else begin
                    addr_1_int_red_mem <= (addr_1_int_red_mem + 1);
                end
                

            end else if (inter_mem_wr_delay == 4) begin 
            
            	inter_mem_wr_delay <= 0;
            	
           
            
     
                
            end else if (inter_mem_wr_delay == 1) begin
                wren_0_intermediate <= 1;
                inter_mem_wr_delay <= 2;
                
                if (addr_1_int_red_mem == RAMSIZE/2 - 1) begin
                    addr_1_int_red_mem <= 0;
                end
                else begin
                    addr_1_int_red_mem <= (addr_1_int_red_mem + 1);
                end
                
            end else if (inter_mem_wr_delay == 2) begin
            wren_0_intermediate <= 1;

                
                addr_0_intermediate <= (addr_0_intermediate + 1);
                
                if (addr_0_int_red_mem == RAMSIZE/2 - 1) begin
                    addr_0_int_red_mem <= 0;
                end
                else begin
                    addr_0_int_red_mem <= (addr_0_int_red_mem + 1);
                end
                if (addr_1_int_red_mem == RAMSIZE/2 - 1) begin
                    addr_1_int_red_mem <= 0;
                end
                else begin
                    addr_1_int_red_mem <= (addr_1_int_red_mem + 1);
                end
 
            end

	if (count_chunks == RAMSIZE/2 + 1) begin
	//$display("haha");
				mux_delay <= 2;
			    state <= S_LOAD_DONE_L;
			    loc_addr <= loc_addr + 1;
				
                if (shift[LOGW-1:LOGW-ADDR_WIDTH] == 0) begin
                    addr_0_reg <=0;
                end
                else begin
                     addr_0_reg <=RAMSIZE_minus_shift;
                end
                
                if (shift[LOGW-1:LOGW-ADDR_WIDTH] == RAMSIZE-1) begin
                    addr_1_reg <=0;
                end
                else begin
                      addr_1_reg <=(RAMSIZE_minus_shift - 1);
                end
				
				count_chunks <= 0;
			end
			else begin
				
				if (addr_0_reg + 1 == RAMSIZE) begin
                    addr_0_reg <=0;
                end
                else begin
                   addr_0_reg <= (addr_0_reg + 1);
                end
                
                if (addr_1_reg + 1 == RAMSIZE) begin
                    addr_1_reg <=0;
                end
                else begin
                    addr_1_reg <= (addr_1_reg + 1);
                end
									   	       	        
				count_chunks <= count_chunks +1;
			
			end	
		end
        
        
		else if (state == S_LOAD_DONE_L) begin
		    addr_0_intermediate <= (addr_0_intermediate + 1);
            
            if (addr_0_int_red_mem == RAMSIZE/2 - 1) begin
                    addr_0_int_red_mem <= 0;
            end
            else begin
                addr_0_int_red_mem <= (addr_0_int_red_mem + 1);
            end
            if (addr_1_int_red_mem == RAMSIZE/2 - 1) begin
                addr_1_int_red_mem <= 0;
            end
            else begin
                addr_1_int_red_mem <= (addr_1_int_red_mem + 1);
            end
			
			if (loc_addr < weight) begin
                state <= S_ADDR_SETTING;
            end
            else begin
                state <= S_MUL_DONE;
            end
		end
		
		
		else if (state == S_MUL_DONE) begin
            wren_0_intermediate <= 0;
            valid <= 1'b1;
            state <= S_WAIT_START_L;
		end

    end 
end 


endmodule
