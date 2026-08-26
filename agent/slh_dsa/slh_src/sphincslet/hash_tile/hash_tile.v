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

module hash_tile
#(
    parameter IO_WIDTH = 64,
    
    /*possible options for parameter sets
    "128s" = SPHINCS+-128s,
    "128f" = SPHINCS+-128f,
    "192s" = SPHINCS+-192s,
    "192f" = SPHINCS+-192f,
    "256s" = SPHINCS+-256s,
    "256f" = SPHINCS+-256f,
    */
    parameter parameter_set = "128s", 

    parameter N     = (parameter_set == "128s") ? 16:
                      (parameter_set == "128f") ? 16:
                      (parameter_set == "192s") ? 24:
                      (parameter_set == "192f") ? 24:
                      (parameter_set == "256s") ? 32:
                      (parameter_set == "256f") ? 32: 16,


    parameter H     = (parameter_set == "128s") ? 63:
                      (parameter_set == "128f") ? 66:
                      (parameter_set == "192s") ? 63:
                      (parameter_set == "192f") ? 66:
                      (parameter_set == "256s") ? 64:
                      (parameter_set == "256f") ? 68: 63,

    parameter D     = (parameter_set == "128s") ? 7:
                      (parameter_set == "128f") ? 22:
                      (parameter_set == "192s") ? 7:
                      (parameter_set == "192f") ? 22:
                      (parameter_set == "256s") ? 8:
                      (parameter_set == "256f") ? 17: 7,

    parameter LOG_T = (parameter_set == "128s") ? 12:
                      (parameter_set == "128f") ? 6:
                      (parameter_set == "192s") ? 14:
                      (parameter_set == "192f") ? 8:
                      (parameter_set == "256s") ? 14:
                      (parameter_set == "256f") ? 9: 12,

    parameter K     = (parameter_set == "128s") ? 14:
                      (parameter_set == "128f") ? 33:
                      (parameter_set == "192s") ? 17:
                      (parameter_set == "192f") ? 33:
                      (parameter_set == "256s") ? 22:
                      (parameter_set == "256f") ? 35: 14,


    //Input Widths
    parameter IN_T_L_WOTS_WIDTH    = 608*8, 
    parameter IN_T_L_FORS_WIDTH    = 576*8, 
    parameter IN_PRF_WIDTH         = (N + 32)*8,
    parameter IN_H_XMSS_WIDTH      = (N + 32 + N + N )*8,
    parameter IN_F_WOTS_PLUS_WIDTH = (N + 32 + N)*8,

    `ifdef SHAKE
        parameter IN_PRF_MSG_PARTIAL_WIDTH = (N + N)*8,
        parameter IN_H_MSG_PARTIAL_WIDTH   = (N + N + N)*8,
    `else
        `ifdef PARAM_128
            parameter IN_PRF_MSG_PARTIAL_WIDTH = (64 + N    )*8,//+M*8
            parameter IN_PRF_MSG_SECOND_WIDTH  = (64 + 32   )*8,
            parameter IN_H_MSG_PARTIAL_WIDTH   = ( N + N + N)*8,//+M*8 
            parameter IN_H_MSG_SECOND_WIDTH    = (32 + 4    )*8,    
        `endif
        `ifdef PARAM_192
            parameter IN_PRF_MSG_PARTIAL_WIDTH = (128 + N    )*8,//+M*8
            parameter IN_PRF_MSG_SECOND_WIDTH  = (128 + 64   )*8,
            parameter IN_H_MSG_PARTIAL_WIDTH   = (  N + N + N)*8,//+M*8 
            parameter IN_H_MSG_SECOND_WIDTH    = ( 64 + 8    )*8,    
        `endif
        `ifdef PARAM_256
            parameter IN_PRF_MSG_PARTIAL_WIDTH = (128 + N    )*8,//+M*8
            parameter IN_PRF_MSG_SECOND_WIDTH  = (128 + 64   )*8,
            parameter IN_H_MSG_PARTIAL_WIDTH   = (  N + N + N)*8,//+M*8 
            parameter IN_H_MSG_SECOND_WIDTH    = ( 64 + 8    )*8,    
        `endif
    `endif
    

    //Output Widths
    parameter OUT_T_L_WIDTH = N*8,                  
    parameter OUT_PRF_WIDTH = N*8,              
    parameter OUT_H_XMSS_WIDTH = N*8,
    parameter OUT_F_WOTS_PLUS_WIDTH = N*8,

    `ifdef SHAKE
        parameter OUT_PRF_MSG_WIDTH = N*8,
        parameter OUT_H_MSG_WIDTH = 
                        (parameter_set == "128s") ? 30*8:
                        (parameter_set == "128f") ? 34*8:
                        (parameter_set == "192s") ? 39*8:
                        (parameter_set == "192f") ? 42*8:
                        (parameter_set == "256s") ? 48*8:
                        (parameter_set == "256f") ? 49*8: 49*8,
    `else
        `ifdef PARAM_128   
            parameter OUT_PRF_MSG_WIDTH        = N*8,//PRF_msg2
            parameter OUT_H_MSG_WIDTH          = 32*8,//PRF_msg1 & H_msg
        `endif
        `ifdef PARAM_192  
            parameter OUT_PRF_MSG_WIDTH        = N*8,//PRF_msg2
            parameter OUT_H_MSG_WIDTH          = 64*8,//PRF_msg1 & H_msg
        `endif
        `ifdef PARAM_256  
            parameter OUT_PRF_MSG_WIDTH        = N*8,//PRF_msg2
            parameter OUT_H_MSG_WIDTH          = 64*8,//PRF_msg1 & H_msg
        `endif
    `endif    

    parameter HASH = "SHAKE256", //  possible options are SHAKE256, SHA256, SHA512
    parameter S_FILE = "",
    parameter B_FILE = ""
)
(
                  input     wire                                               clk,
                  input     wire                                               rst,
                  
                  //ports for small RAM connected to SHAKE256
                  input     wire [IO_WIDTH-1:0]                                i_s_data_in,
                  input     wire                                               i_s_wr_en,
                  input     wire [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0]     i_s_addr,
                  input     wire                                               i_s_rd_en,
                  output    wire [IO_WIDTH-1:0]                                o_s_data_out,
                  
                  output    wire                                               o_s_fifo_full,  // used only for i_opcode = 3 => H_MSG, i_opcode = 5 => PRF_MSG
                  

                  //ports for big RAM connected to SHAKE256
                  input     wire [IO_WIDTH-1:0]                                i_b_data_in,
                  input     wire                                               i_b_wr_en,
                  input     wire [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0]     i_b_addr,
                  input     wire                                               i_b_rd_en,
                  output    wire [IO_WIDTH-1:0]                                o_b_data_out,
                  output    wire                                               o_b_fifo_full, // used only for i_opcode = 3 => H_MSG, i_opcode = 5 => PRF_MSG
                  

                  //port used only in PRF_msg, H_msg (i_opcode = 5, 6)
                  input     wire [12-1:0]                                      i_msg_in_size, 

                  input     wire [4-1:0]                                       i_h_iterations, 

                  /*
                  i_opcode = 0 => T_L_WOTS (WOTS+ pk compression)
                  i_opcode = 1 => PRF
                  i_opcode = 2 => H(XMSS)
                  i_opcode = 3 => H_MSG
                  i_opcode = 4 => F_WOTS+
                  i_opcode = 5 => PRF_MSG
                  i_opcode = 6 => F_WOTS+ iterated for h_iterations
                  i_opcode = 7 => T_L_FORS (FORS roots compression)
                  */
                  input     wire [2:0]                                          i_opcode,
                  input     wire                                                i_start,
                  output    reg                                                 o_done,
                  `ifdef SHA2
                  input     wire                                                i_first_flag,
                  output    wire                                                o_mode_flag,
                  `endif

                //ports for drawing outputs directly from the hash function
                  output     wire [IO_WIDTH-1:0]                                o_b_data_out_from_hash,         //  b data output directly from the hash module
                  output     wire                                               o_b_data_out_valid_from_hash,   //  b data valid directly from the hash module
                  output     wire [IO_WIDTH-1:0]                                o_s_data_out_from_hash,         //  s data output directly from the hash module
                  output     wire                                               o_s_data_out_valid_from_hash    //  s data valid directly from the hash module
                  
    );    

 parameter T_L_WOTS                     = 0;
 parameter PRF                          = 1;
 parameter H_XMSS                       = 2;
 parameter H_MSG                        = 3;
 parameter F_WOTS_PLUS                  = 4;
 parameter PRF_MSG                      = 5;
 parameter F_WOTS_PLUS_ITERATED         = 6;
 parameter T_L_FORS                     = 7;

 parameter STREAMING                   = 1; 

 parameter OUT_T_L_WIDTH_ADJUSTED = OUT_T_L_WIDTH + (IO_WIDTH - (OUT_T_L_WIDTH % IO_WIDTH))%IO_WIDTH;
 parameter OUT_PRF_WIDTH_ADJUSTED = OUT_PRF_WIDTH + (IO_WIDTH - (OUT_PRF_WIDTH % IO_WIDTH))%IO_WIDTH;
 parameter OUT_H_XMSS_WIDTH_ADJUSTED = OUT_H_XMSS_WIDTH + (IO_WIDTH - (OUT_H_XMSS_WIDTH % IO_WIDTH))%IO_WIDTH; 
 parameter OUT_H_MSG_WIDTH_ADJUSTED = OUT_H_MSG_WIDTH + (IO_WIDTH - (OUT_H_MSG_WIDTH % IO_WIDTH))%IO_WIDTH;      
 parameter OUT_F_WOTS_PLUS_WIDTH_ADJUSTED = OUT_F_WOTS_PLUS_WIDTH + (IO_WIDTH - (OUT_F_WOTS_PLUS_WIDTH % IO_WIDTH))%IO_WIDTH;

 `ifdef SHAKE
    parameter OUT_PRF_MSG_WIDTH_ADJUSTED = OUT_PRF_MSG_WIDTH + (IO_WIDTH - (OUT_PRF_MSG_WIDTH % IO_WIDTH))%IO_WIDTH; 
 `else
    parameter OUT_PRF_MSG_WIDTH_ADJUSTED  = OUT_H_MSG_WIDTH + (IO_WIDTH - (OUT_H_MSG_WIDTH % IO_WIDTH))%IO_WIDTH; 
    parameter OUT_PRF_MSG_WIDTH_ADJUSTED2 = OUT_PRF_MSG_WIDTH + (IO_WIDTH - (OUT_PRF_MSG_WIDTH % IO_WIDTH))%IO_WIDTH; 
 `endif

 wire [IO_WIDTH-1:0] s_out_0;
 wire [IO_WIDTH-1:0] s_out_1;
 wire [IO_WIDTH-1:0] s_in_0;
 wire [IO_WIDTH-1:0] s_in_1;
 wire [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] s_in_0_addr;
 wire [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] s_in_1_addr;
 wire s_in_0_wr_en;
 wire s_in_1_wr_en;
 wire s_h_rd_en;
 wire [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] s_h_addr;
 wire [IO_WIDTH-1:0] s_h_data_out; 
 wire s_h_data_out_valid; 
 reg  s_h_data_out_ready; 
 wire s_h_done;
 reg  s_h_start;
 wire [16-1:0] s_h_input_length;
 wire [10-1:0] s_h_output_length;

 wire [IO_WIDTH-1:0] b_out;
 wire [IO_WIDTH-1:0] b_in;
 wire [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] b_in_addr;
 wire b_in_wr_en;
 wire b_h_rd_en;
 wire [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] b_h_addr;
 wire [IO_WIDTH-1:0] b_h_data_out; 
 wire b_h_data_out_valid; 
 wire b_h_data_out_ready; 
 assign b_h_data_out_ready = s_h_data_out_ready;
 wire b_h_done;
 reg  b_h_start;
 
 
 reg [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] s_cap_addr; 
 wire [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] b_cap_addr; 
 reg s_cap_wen; 
 wire b_cap_wen; 
 assign b_cap_wen = s_cap_wen;
 assign b_cap_addr = s_cap_addr;

 reg s_mem_transfer_completed;
 
 reg [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] s_cap_addr_init;
 reg [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] s_cap_addr_max;

 wire [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] wb_start_addr;

 reg output_enable;

 reg [2:0] opcode_reg;

 reg [1:0] s_h_ADDR_update;
 
 reg [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] s_ADDR_update_addr_v; 
 reg [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0] b_ADDR_update_addr_v; 
 
 reg s_ADDR_update_wen;
 reg [IO_WIDTH-1:0] ADDR_update_v; 
 reg [IO_WIDTH-1:0] b_ADDR_update_v; 

 wire mode; 

 assign mode = (i_opcode == H_MSG || i_opcode == PRF_MSG)? STREAMING : 0;

 assign o_b_data_out_from_hash = b_h_data_out;
 assign o_b_data_out_valid_from_hash = b_h_data_out_valid && output_enable;

 assign o_s_data_out_from_hash = s_h_data_out;
 assign o_s_data_out_valid_from_hash = s_h_data_out_valid && output_enable;

 assign s_in_0 = s_h_data_out;                                                                                                    

 assign s_in_0_addr = s_h_rd_en? s_h_addr :s_cap_addr;
 `ifdef SHAKE
 assign s_in_0_wr_en = s_cap_wen2;
 `else
 assign s_in_0_wr_en = 1'b0;
 `endif
 assign o_s_data_out = s_out_0;

assign s_in_1 = i_s_wr_en?  i_s_data_in:
                `ifdef SHAKE
                condition_s_wen2_d? ADDR_update_v  :
                `else
                condition_s_wen2? ADDR_update_v  :
                `endif
                b_in;

assign s_in_1_addr = (i_s_wr_en || i_s_rd_en)? i_s_addr: 
                     `ifdef SHAKE
                     condition_s_wen2_d? s_ADDR_update_addr_v  :
                     `else
                     condition_s_wen2? s_ADDR_update_addr_v  :
                     `endif
                     b_in_addr;

assign s_in_1_wr_en =   i_s_wr_en? 1'b1:
                        `ifdef SHAKE
                        (condition_s_wen2_d)? 1'b1  :
                        `else 
                        (condition_s_wen2)? 1'b1  :    
                        `endif
                        0;


reg condition_s, condition_b;

always@(posedge clk)
begin
    condition_s <= (opcode_reg == 6 && s_h_addr == ({wb_start_addr,3'b000})/IO_WIDTH - 1);
    condition_b <= (opcode_reg == 6 && b_h_addr == ({wb_start_addr,3'b000})/IO_WIDTH - 1);
end

`ifdef SHAKE
wire condition_s_wen2;
reg condition_s_wen2_d;
wire s_cap_wen2;
wire b_cap_wen2;
assign condition_s_wen2 = ((s_h_ADDR_update == 2) && opcode_reg==6);
assign s_cap_wen2 = (s_cap_wen && opcode_reg==6);
assign b_cap_wen2 = s_cap_wen2;

always@(posedge clk)
begin
    condition_s_wen2_d <= condition_s_wen2;

    if (condition_s) begin
        ADDR_update_v <= s_out_0[IO_WIDTH-1:0] + 1;
    end
end

always@(posedge clk)
begin
    if (condition_b) begin
        b_ADDR_update_v <= b_out[IO_WIDTH-1:0] + 1;
    end
end
`else
reg s_cap_wen_d;
reg s_cap_wen_d2;
reg [48:0] tmp_reg_0;
reg [48:0] tmp_reg_1;
wire condition_s_wen2;
assign condition_s_wen2 = ((s_cap_wen_d || s_cap_wen_d2) && opcode_reg==6);

always@(posedge clk)
begin
    s_cap_wen_d <= s_cap_wen;
    s_cap_wen_d2 <= s_cap_wen_d;

    if (condition_s) begin        
        ADDR_update_v <= s_out_0[IO_WIDTH-1:0] + 17'h10000;//SHA2
    end
    else if(((s_cap_wen && !s_cap_wen_d) && opcode_reg==6)) begin
        ADDR_update_v <= {ADDR_update_v[64-1:16],s_h_data_out[64-1:48]};
        tmp_reg_0 <= s_h_data_out[48-1:0];
    end
    else if(((s_cap_wen && s_cap_wen_d) && opcode_reg==6)) begin
        ADDR_update_v <= {tmp_reg_0,s_h_data_out[64-1:48]};
        tmp_reg_0 <= s_h_data_out[48-1:0];
    end
    else if(((!s_cap_wen && s_cap_wen_d) && opcode_reg==6)) begin
        ADDR_update_v <= {tmp_reg_0,16'd0};
        tmp_reg_0 <= 48'd0;
    end
    else begin
        tmp_reg_0 <= tmp_reg_0;
    end
end

always@(posedge clk)
begin
    if (condition_b) begin
        b_ADDR_update_v <= b_out[IO_WIDTH-1:0] + 17'h10000;//SHA2
    end
    else if(((s_cap_wen && !s_cap_wen_d) && opcode_reg==6)) begin
        b_ADDR_update_v <= {b_ADDR_update_v[64-1:16],b_h_data_out[64-1:48]};
        tmp_reg_1 <= b_h_data_out[48-1:0];
    end
    else if(((s_cap_wen && s_cap_wen_d) && opcode_reg==6)) begin
        b_ADDR_update_v <= {tmp_reg_1,b_h_data_out[64-1:48]};
        tmp_reg_1 <= b_h_data_out[48-1:0];
    end
    else if(((!s_cap_wen && s_cap_wen_d) && opcode_reg==6)) begin
        b_ADDR_update_v <= {tmp_reg_1,16'd0};
        tmp_reg_1 <= 48'd0;
    end
    else begin
        tmp_reg_1 <= tmp_reg_1;
    end    
end
`endif

 wire [IO_WIDTH-1:0]    s_fifo_out;
 wire                   s_fifo_o_empty;

  fifo #(.BW(IO_WIDTH), .LGFLEN(3) ) S_FIFO_INSTANCE
 (
    .i_clk(clk), 
    .i_wr(i_s_wr_en), 
    .i_data(i_s_data_in), 
    .o_full(o_s_fifo_full), 
    .o_fill(), 
    .i_rd(s_h_rd_en), 
    .o_data(s_fifo_out), 
    .o_empty(s_fifo_o_empty)
 );

   mem_dual #(.WIDTH(IO_WIDTH), .DEPTH(IN_T_L_WOTS_WIDTH/IO_WIDTH), .FILE(S_FILE)) SMALL_MEM
 (
        .clock(clk),
        .data_0(s_in_0),
        .data_1(s_in_1),
        .address_0(s_in_0_addr),
        .address_1(s_in_1_addr),
        .wren_0(s_in_0_wr_en),
        .wren_1(s_in_1_wr_en),
        .q_0(s_out_0),
        .q_1(s_out_1)
 );

`ifdef SHAKE
 assign s_h_input_length  = (i_opcode == T_L_WOTS)? IN_T_L_WOTS_WIDTH:
                            (i_opcode == PRF)? IN_PRF_WIDTH:
                            (i_opcode == H_XMSS)? IN_H_XMSS_WIDTH:
                            (i_opcode == H_MSG)? IN_H_MSG_PARTIAL_WIDTH + {i_msg_in_size,3'b000}:
                            (i_opcode == F_WOTS_PLUS)? IN_F_WOTS_PLUS_WIDTH:
                            (i_opcode == PRF_MSG)? IN_PRF_MSG_PARTIAL_WIDTH + {i_msg_in_size,3'b000} : 
                            (i_opcode == F_WOTS_PLUS_ITERATED)? IN_F_WOTS_PLUS_WIDTH :
                            (i_opcode == T_L_FORS)? IN_T_L_FORS_WIDTH :0;

 assign s_h_output_length = (i_opcode == T_L_WOTS)? OUT_T_L_WIDTH_ADJUSTED:
                            (i_opcode == PRF)? OUT_PRF_WIDTH_ADJUSTED:
                            (i_opcode == H_XMSS)? OUT_H_XMSS_WIDTH_ADJUSTED:
                            (i_opcode == H_MSG)? OUT_H_MSG_WIDTH_ADJUSTED:
                            (i_opcode == F_WOTS_PLUS)? OUT_F_WOTS_PLUS_WIDTH_ADJUSTED: 
                            (i_opcode == PRF_MSG)? OUT_PRF_MSG_WIDTH_ADJUSTED: 
                            (i_opcode == F_WOTS_PLUS_ITERATED)? OUT_F_WOTS_PLUS_WIDTH_ADJUSTED: 
                            (i_opcode == T_L_FORS)? OUT_T_L_WIDTH_ADJUSTED:0;
`else

`ifdef PARAM_128
wire [10-1:0] LEN_OFFSET;
localparam BLOCK_SIZE = 512;
assign LEN_OFFSET = mode_flag ? BLOCK_SIZE : 0;
`else
wire [11-1:0] LEN_OFFSET;
localparam BLOCK_SIZE = (HASH == "SHA512") ? 1024: 512;
assign LEN_OFFSET = mode_flag ? BLOCK_SIZE : 0;
`endif

 assign s_h_input_length  = (i_opcode == T_L_WOTS)? IN_T_L_WOTS_WIDTH - LEN_OFFSET:
                            (i_opcode == PRF)? IN_PRF_WIDTH - LEN_OFFSET:
                            (i_opcode == H_XMSS)? IN_H_XMSS_WIDTH - LEN_OFFSET:
                            (i_opcode == H_MSG && i_first_flag)? IN_H_MSG_PARTIAL_WIDTH + {i_msg_in_size,3'b000}: //
                            (i_opcode == H_MSG)? IN_H_MSG_SECOND_WIDTH : //
                            (i_opcode == F_WOTS_PLUS)? IN_F_WOTS_PLUS_WIDTH - LEN_OFFSET:
                            (i_opcode == PRF_MSG && i_first_flag)? IN_PRF_MSG_PARTIAL_WIDTH + {i_msg_in_size,3'b000} : //
                            (i_opcode == PRF_MSG)? IN_PRF_MSG_SECOND_WIDTH : //
                            (i_opcode == F_WOTS_PLUS_ITERATED)? IN_F_WOTS_PLUS_WIDTH - LEN_OFFSET :
                            (i_opcode == T_L_FORS)? IN_T_L_FORS_WIDTH - LEN_OFFSET :0;

 assign s_h_output_length = (i_opcode == T_L_WOTS)? OUT_T_L_WIDTH_ADJUSTED:
                            (i_opcode == PRF)? OUT_PRF_WIDTH_ADJUSTED:
                            (i_opcode == H_XMSS)? OUT_H_XMSS_WIDTH_ADJUSTED:
                            (i_opcode == H_MSG)? OUT_H_MSG_WIDTH_ADJUSTED:
                            (i_opcode == F_WOTS_PLUS)? OUT_F_WOTS_PLUS_WIDTH_ADJUSTED: 
                            (i_opcode == PRF_MSG && i_first_flag)? OUT_PRF_MSG_WIDTH_ADJUSTED: //
                            (i_opcode == PRF_MSG)? OUT_PRF_MSG_WIDTH_ADJUSTED2: //
                            (i_opcode == F_WOTS_PLUS_ITERATED)? OUT_F_WOTS_PLUS_WIDTH_ADJUSTED: 
                            (i_opcode == T_L_FORS)? OUT_T_L_WIDTH_ADJUSTED:0;
 `endif 
                     

`ifdef SHAKE
 assign wb_start_addr = (N+32); //SHAKE
 `else
 assign wb_start_addr = (64+24); //SHA2
 `endif

`ifdef SHA2
reg mode_flag;
assign o_mode_flag = mode_flag; 
always@(posedge clk) begin
    if (rst) begin
        mode_flag <= 0;
    end
    else begin
        if((i_opcode==H_MSG || i_opcode==PRF_MSG) && i_start) begin
            mode_flag <= 0;
        end
        else if((i_opcode!=H_MSG && i_opcode!=PRF_MSG) && i_start) begin
            mode_flag <= 1;
        end
        else begin
            mode_flag <= mode_flag;
        end  
    end
end
`endif

generate
    if (HASH == "SHA512" || HASH == "SHA256") begin
         hash_mem_interface_sha
        #(
            .IO_WIDTH(IO_WIDTH),
            .MAX_RAM_DEPTH(IN_T_L_WOTS_WIDTH/IO_WIDTH),
            .SHA_TYPE(HASH)
        )
        HASH_SM
        (
        .clk(clk),
        .rst(rst),

        .i_data_in(mode == STREAMING? s_fifo_out :s_out_0),
        .o_data_out_ready(s_h_data_out_ready),
        .i_input_length(s_h_input_length),
        .i_output_length(s_h_output_length),
        .i_start(s_h_start),

        .i_mode(mode),
        `ifdef SHA2
        .i_mode_flag(mode_flag),
        `endif
        .i_fifo_o_empty(s_fifo_o_empty),
        
        .o_rd_en(s_h_rd_en),
        .o_addr(s_h_addr),

        .o_data_out(s_h_data_out),
        .o_data_out_valid(s_h_data_out_valid),
        .o_done(s_h_done) 
        );
    end
    else begin
        hash_mem_interface_shake256
        #(
            .IO_WIDTH(IO_WIDTH),
            .MAX_RAM_DEPTH(IN_T_L_WOTS_WIDTH/IO_WIDTH)
        )
        HASH_SM
        (
        .clk(clk),
        .rst(rst),

        .i_data_in(mode == STREAMING? s_fifo_out :s_out_0),
        .o_data_out_ready(s_h_data_out_ready),
        .i_input_length(s_h_input_length),
        .i_output_length(s_h_output_length),
        .i_start(s_h_start),

        .i_mode(mode),
        .i_fifo_o_empty(s_fifo_o_empty),
        
        .o_rd_en(s_h_rd_en),
        .o_addr(s_h_addr),

        .o_data_out(s_h_data_out),
        .o_data_out_valid(s_h_data_out_valid),
        .o_done(s_h_done) 
        ); 
    end
endgenerate


 wire test_b_condition;
 assign test_b_condition = (i_b_wr_en == 1)  ? 1'b1: 1'b0;
 
 assign b_in =  b_h_data_out;                

 assign b_in_addr = b_h_rd_en? b_h_addr :b_cap_addr;
 `ifdef SHAKE
 assign b_in_wr_en = b_cap_wen2;
 `else
 assign b_in_wr_en = 1'b0;
 `endif
 assign o_b_data_out = b_out;

 

 wire [IO_WIDTH-1:0]    b_fifo_out;
 wire                   b_fifo_o_empty;

  fifo #(.BW(IO_WIDTH), .LGFLEN(3) ) B_FIFO_INSTANCE
 (
    .i_clk(clk), 
    .i_wr(i_b_wr_en), 
    .i_data(i_b_data_in), 
    .o_full(o_b_fifo_full), 
    .o_fill(), 
    .i_rd(b_h_rd_en), 
    .o_data(b_fifo_out), 
    .o_empty(b_fifo_o_empty)
 );
   
    mem_dual #(.WIDTH(IO_WIDTH), .DEPTH(IN_T_L_WOTS_WIDTH/IO_WIDTH), .FILE(B_FILE)) BIG_MEM
 (
        .clock(clk),
        .data_0(b_in),
        .data_1(i_b_wr_en? i_b_data_in: b_ADDR_update_v),
        .address_0(b_in_addr),
        .address_1(i_b_wr_en? i_b_addr: b_ADDR_update_addr_v),
        .wren_0(b_in_wr_en),
        `ifdef SHAKE
        .wren_1(i_b_wr_en? 1 : condition_s_wen2_d? 1 : 0),
        `else
        .wren_1(i_b_wr_en? 1 : condition_s_wen2? 1 : 0),
        `endif
        .q_0(b_out),
        .q_1()
 );  

generate
    if (HASH == "SHA512" || HASH == "SHA256") begin
                hash_mem_interface_sha
            #(
                .IO_WIDTH(IO_WIDTH),
                .MAX_RAM_DEPTH(IN_T_L_WOTS_WIDTH/IO_WIDTH),
                .SHA_TYPE(HASH)
            )
            HASH_BM
            (
            .clk(clk),
            .rst(rst),

            .i_data_in(mode == STREAMING? b_fifo_out :b_out),
            .o_data_out_ready(b_h_data_out_ready),
            .i_input_length(s_h_input_length),
            .i_output_length(s_h_output_length),            
            .i_start(mode == STREAMING? 0 : b_h_start),

            .i_mode(mode),
            `ifdef SHA2
            .i_mode_flag(mode_flag),
            `endif
            .i_fifo_o_empty(b_fifo_o_empty),
            
            .o_rd_en(b_h_rd_en),
            .o_addr(b_h_addr),

            .o_data_out(b_h_data_out),
            .o_data_out_valid(b_h_data_out_valid),
            .o_done(b_h_done) 
            );
    end
    else begin
        hash_mem_interface_shake256
            #(
                .IO_WIDTH(IO_WIDTH),
                .MAX_RAM_DEPTH(IN_T_L_WOTS_WIDTH/IO_WIDTH)
            )
            HASH_BM
            (
            .clk(clk),
            .rst(rst),

            .i_data_in(mode == STREAMING? b_fifo_out :b_out),
            .o_data_out_ready(b_h_data_out_ready),
            .i_input_length(s_h_input_length),
            .i_output_length(s_h_output_length),               
            .i_start(mode == STREAMING? 0 : b_h_start),

            .i_mode(mode),
            .i_fifo_o_empty(b_fifo_o_empty),
            
            .o_rd_en(b_h_rd_en),
            .o_addr(b_h_addr),

            .o_data_out(b_h_data_out),
            .o_data_out_valid(b_h_data_out_valid),
            .o_done(b_h_done) 
            );
    end
endgenerate
    
 reg [4:0] state;
 parameter s_wait_start                 = 0;
 parameter s_t_l                        = 1;
 parameter s_prf                        = 2;
 parameter s_h_xmss                     = 3;
 parameter s_h_msg                      = 4;
 parameter s_f_wots                     = 5;
 parameter s_prf_msg                    = 6;
 parameter s_f_wots_iterated            = 7;
 
reg [4-1:0] h_iterations_reg;
reg done_reg;

always@(posedge clk)
begin
    o_done <= done_reg;
    if (rst) begin  
        state <= s_wait_start;
        s_cap_addr_init <= 0;
        s_cap_addr_max  <= 0;
        h_iterations_reg <= 0;
        s_ADDR_update_addr_v <= 0;
    end
    else begin
        if (state == s_wait_start) begin
            if (i_start) begin
                opcode_reg <= i_opcode;
                if (i_opcode == T_L_WOTS || i_opcode == T_L_FORS) begin
                    state <= s_t_l;
                    s_cap_addr_init <= 0;
                    s_cap_addr_max <= (OUT_T_L_WIDTH_ADJUSTED)/IO_WIDTH - 1;   
                end
                else if (i_opcode == PRF) begin
                    state <= s_prf;
                    s_cap_addr_init <= 0;
                    s_cap_addr_max <= (OUT_PRF_WIDTH_ADJUSTED)/IO_WIDTH - 1;
                end
                else if (i_opcode == H_XMSS) begin
                    state <= s_h_xmss;
                    s_cap_addr_init <= 0;
                    s_cap_addr_max <= (OUT_H_XMSS_WIDTH_ADJUSTED)/IO_WIDTH - 1;
                end
                else if (i_opcode == H_MSG) begin
                    state <= s_h_msg;
                    s_cap_addr_init <= 0;
                    s_cap_addr_max <= (OUT_H_MSG_WIDTH_ADJUSTED)/IO_WIDTH - 1;
                end
                else if (i_opcode == F_WOTS_PLUS) begin
                    state <= s_f_wots;
                    s_cap_addr_init <= 0;
                    s_cap_addr_max <= (OUT_F_WOTS_PLUS_WIDTH_ADJUSTED)/IO_WIDTH - 1;
                end
                `ifdef SHAKE
                else if (i_opcode == PRF_MSG) begin
                    state <= s_prf_msg;
                    s_cap_addr_init <= 0;
                    s_cap_addr_max <= (OUT_PRF_MSG_WIDTH_ADJUSTED)/IO_WIDTH - 1;
                end                
                `else
                else if (i_opcode == PRF_MSG && i_first_flag) begin
                    state <= s_prf_msg;
                    s_cap_addr_init <= 0;
                    s_cap_addr_max <= (OUT_PRF_MSG_WIDTH_ADJUSTED)/IO_WIDTH - 1;                  
                end
                else if (i_opcode == PRF_MSG) begin
                    state <= s_prf_msg;
                    s_cap_addr_init <= 0;
                    s_cap_addr_max <= (OUT_PRF_MSG_WIDTH_ADJUSTED2)/IO_WIDTH - 1;
                end  
                `endif              
                else if (i_opcode == F_WOTS_PLUS_ITERATED) begin
                    state <= s_f_wots_iterated;
                    h_iterations_reg <= i_h_iterations - 1;
                    s_cap_addr_init <= {wb_start_addr, 3'b000}/IO_WIDTH;
                    s_cap_addr_max <= ({wb_start_addr, 3'b000} + OUT_F_WOTS_PLUS_WIDTH_ADJUSTED)/IO_WIDTH - 1;
                    s_ADDR_update_addr_v <= ({(wb_start_addr),3'b000})/IO_WIDTH - 1;
                    b_ADDR_update_addr_v <= ({(wb_start_addr),3'b000})/IO_WIDTH - 1;
                end
            end
        end
        else if (state == s_t_l) begin
            if (s_mem_transfer_completed) begin
                state <= s_wait_start; 
            end
        end
        else if (state == s_prf) begin
            if (s_mem_transfer_completed) begin
                state <= s_wait_start; 
            end
        end
        else if (state == s_h_xmss) begin
            if (s_mem_transfer_completed) begin
                state <= s_wait_start; 
            end
        end
        else if (state == s_h_msg) begin
            if (s_mem_transfer_completed) begin
                state <= s_wait_start; 
            end
        end
        else if (state == s_prf_msg) begin
            if (s_mem_transfer_completed) begin
                state <= s_wait_start; 
            end
        end
        else if (state == s_f_wots) begin
            if (s_mem_transfer_completed) begin
                state <= s_wait_start; 
            end
        end 
        else if (state == s_f_wots_iterated) begin
            if (h_iterations_reg == 0) begin
                if (s_mem_transfer_completed) begin
                    state <= s_wait_start; 
                end
            end
            else begin
                if (s_mem_transfer_completed) begin
                    state <= s_f_wots_iterated; 
                    h_iterations_reg <= h_iterations_reg - 1;
                end
            end 

            `ifdef SHA2
            if(condition_s_wen2) begin
                s_ADDR_update_addr_v <= s_ADDR_update_addr_v + 1;
                b_ADDR_update_addr_v <= b_ADDR_update_addr_v + 1;
            end
            else begin
                s_ADDR_update_addr_v <= ({(wb_start_addr),3'b000})/IO_WIDTH - 1;
                b_ADDR_update_addr_v <= ({(wb_start_addr),3'b000})/IO_WIDTH - 1;
            end
            `endif
        end
     
    end
end     


always@(state, i_start, i_opcode, s_h_data_out_valid, b_h_data_out_valid, s_mem_transfer_completed, h_iterations_reg)
begin
    case(state)

    s_wait_start:begin
        // start_mem_transfer <= 0;
        done_reg <= 0;
        output_enable <= 0;
        s_h_ADDR_update <= 0;
        if (i_start) begin
            s_h_start <= 1;
            b_h_start <= 1;
        end        
        else begin
            s_h_start <= 0;
            b_h_start <= 0;
        end
    end

    s_t_l:begin
        s_h_start <= 0;
        b_h_start <= 0;
        output_enable <= 1;
        s_h_ADDR_update <= 0;
        if (s_mem_transfer_completed) begin
            done_reg <= 1;
        end
        else begin
            done_reg <= 0;
        end
    end

    s_prf:begin
        s_h_start <= 0;
        b_h_start <= 0;
        output_enable <= 1;
        s_h_ADDR_update <= 0;
        if (s_mem_transfer_completed) begin
            done_reg <= 1;
        end
        else begin
            done_reg <= 0;
        end
    end

    s_h_xmss:begin
        s_h_start <= 0;
        b_h_start <= 0;
        output_enable <= 1;
        s_h_ADDR_update <= 0;
        if (s_mem_transfer_completed) begin
            done_reg <= 1;
        end
        else begin
            done_reg <= 0;
        end
    end

    s_h_msg:begin
        s_h_start <= 0;
        b_h_start <= 0;
        output_enable <= 1;
        s_h_ADDR_update <= 0;
        if (s_mem_transfer_completed) begin
            done_reg <= 1;
        end
        else begin
            done_reg <= 0;
        end
    end

    s_f_wots:begin
        s_h_start <= 0;
        b_h_start <= 0;
        output_enable <= 1;
        s_h_ADDR_update <= 0;
        if (s_mem_transfer_completed) begin
            done_reg <= 1;
        end
        else begin
            done_reg <= 0;
        end
    end

    s_prf_msg:begin
        s_h_start <= 0;
        b_h_start <= 0;
        output_enable <= 1;
        s_h_ADDR_update <= 0;
        if (s_mem_transfer_completed) begin
            done_reg <= 1;
        end
        else begin
            done_reg <= 0;
        end
    end

    s_f_wots_iterated:begin
        
        if (h_iterations_reg == 0) begin
            s_h_start <= 0;
            b_h_start <= 0;
            output_enable <= 1;
            s_h_ADDR_update <= 0;
            if (s_mem_transfer_completed) begin
                done_reg <= 1;
            end
            else begin
                done_reg <= 0;
            end
        end
        else begin
            output_enable <= 1;
            if (s_mem_transfer_completed) begin
                done_reg <= 1;
                s_h_start <= 1;
                b_h_start <= 1;
                s_h_ADDR_update <= 2; 
            end
            else begin
                s_h_start <= 0;
                b_h_start <= 0;
                done_reg <= 0;
                s_h_ADDR_update <= 0; 
            end
        end
    end

    default: begin
        s_h_start <= 0;
        b_h_start <= 0;
        done_reg <= 0;
    end
    endcase
end

reg [2:0] m_s_state = 0;
parameter m_s_wait_start = 0;
parameter m_s_capture_data = 1;

//logic for storing the data in the _MEM
always@(posedge clk)
begin
    if (rst) begin
        m_s_state <= 0;
    end
    else begin
        if (m_s_state == m_s_wait_start) begin
            s_cap_addr <= s_cap_addr_init;
            s_h_data_out_ready <= 1;
            if (s_h_data_out_valid) begin
                m_s_state <= m_s_capture_data;
                s_cap_addr <= s_cap_addr + 1;
            end
        end

        else if (m_s_state == m_s_capture_data) begin
            s_h_data_out_ready <= 1;
            if (s_cap_addr == s_cap_addr_max) begin
                m_s_state <= m_s_wait_start;
            end
            else begin
                if (s_h_data_out_valid) begin
                    s_cap_addr <= s_cap_addr + 1;
                end
            end
        end
    end
end

always@(m_s_state, s_h_data_out_valid, s_cap_addr)
begin
    case(m_s_state)
    m_s_wait_start:begin
        s_mem_transfer_completed <= 0;
        if (s_h_data_out_valid) begin
            s_cap_wen <= 1;
        end
        else begin
            s_cap_wen <= 0;
        end
    end

    m_s_capture_data:begin
        if (s_h_data_out_valid) begin
            s_cap_wen <= 1;
        end
        else begin
            s_cap_wen <= 0;
        end
        if (s_cap_addr == s_cap_addr_max) begin
            s_mem_transfer_completed <= 1;
        end
        else begin
            s_mem_transfer_completed <= 0;
        end
    end

    default: begin
        s_cap_wen <= 0;
        s_mem_transfer_completed <= 0;  
    end
    endcase
end

endmodule
