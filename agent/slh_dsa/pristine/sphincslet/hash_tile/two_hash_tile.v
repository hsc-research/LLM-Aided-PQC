`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 02/14/2024 05:35:33 PM
// Design Name: 
// Module Name: two_hash_tile
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////
//`include "clog2.v"

module two_hash_tile
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
    parameter parameter_set = "256s", 

    parameter N     = (parameter_set == "128s") ? 16:
                      (parameter_set == "128f") ? 16:
                      (parameter_set == "192s") ? 24:
                      (parameter_set == "192f") ? 24:
                      (parameter_set == "256s") ? 32:
                      (parameter_set == "256f") ? 32: 16,
    parameter SD     = (parameter_set == "128s") ? 8:
                      (parameter_set == "128f") ? 8:
                      (parameter_set == "192s") ? 16:
                      (parameter_set == "192f") ? 16:
                      (parameter_set == "256s") ? 16:
                      (parameter_set == "256f") ? 16: 16,

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
    parameter WD = //address bit for max data length
                    (parameter_set == "128s") ? 7:
                    (parameter_set == "128f") ? 7:
                    (parameter_set == "192s") ? 8:
                    (parameter_set == "192f") ? 8:
                    (parameter_set == "256s") ? 9:
                    (parameter_set == "256f") ? 9: 9,                      

    //Input Widths
    parameter IN_T_L_WOTS_WIDTH = 608*8, //need to update this
    parameter IN_T_L_FORS_WIDTH = 576*8, //need to update this
    parameter IN_PRF_WIDTH = (N+32)*8,
    parameter IN_H_XMSS_WIDTH = (N + 32 + N + N )*8,
    parameter IN_H_MSG_PARTIAL_WIDTH = (N + N + N)*8,
    parameter IN_F_WOTS_PLUS_WIDTH = (N + 32 + N)*8,
    parameter IN_PRF_MSG_PARTIAL_WIDTH = (N + N)*8,
    

    //Output Widths
    parameter OUT_T_L_WIDTH = N*8,                  
    parameter OUT_PRF_WIDTH = N*8,              
    parameter OUT_H_XMSS_WIDTH = N*8,
    parameter OUT_H_MSG_WIDTH = 
                    (parameter_set == "128s") ? 30*8:
                    (parameter_set == "128f") ? 34*8:
                    (parameter_set == "192s") ? 39*8:
                    (parameter_set == "192f") ? 42*8:
                    (parameter_set == "256s") ? 48*8:
                    (parameter_set == "256f") ? 49*8: 49*8,    
    parameter OUT_F_WOTS_PLUS_WIDTH = N*8,
    parameter OUT_PRF_MSG_WIDTH = N*8,

    parameter HASH = "SHA256", //  possible options are SHAKE256, SHA256, SHA512
    parameter S_FILE = "",
    parameter B_FILE = ""
)
(
input     wire                                               clk,
input     wire                                               rst,
input     wire [IO_WIDTH-1:0]                                i_s_data_in,
input     wire                                               i_s_wr_en,
input     wire [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0]     i_s_addr,
output    wire                                               o_s_fifo_full,
input     wire [IO_WIDTH-1:0]                                i_b_data_in,
input     wire                                               i_b_wr_en,
input     wire [`CLOG2(IN_T_L_WOTS_WIDTH/IO_WIDTH) -1:0]     i_b_addr,
input     wire [12-1:0]                                      i_msg_in_size, 
input     wire [4-1:0]                                       i_h_iterations,
input     wire [2:0]                                         i_opcode,
input     wire                                               i_start,
output    wire                                               o_done,
input     wire                                               i_first_flag,
output    wire                                               o_mode_flag1,
output    wire                                               o_mode_flag2,
output    wire [IO_WIDTH-1:0]                                o_b_data_out_from_hash,         //  b data output directly from the hash module
output    wire                                               o_b_data_out_valid_from_hash,   //  b data valid directly from the hash module
output    wire [IO_WIDTH-1:0]                                o_s_data_out_from_hash,         //  s data output directly from the hash module
output    wire                                               o_s_data_out_valid_from_hash    //  s data valid directly from the hash module             
);
    
    
wire [64-1:0] hash_data_in1_SHA256;
wire          hash_data_valid1_SHA256;
wire [WD-1:0] hash_data_address1_SHA256;
wire          o_s_fifo_full_SHA256;
wire [64-1:0] hash_data_in2_SHA256;
wire          hash_data_valid2_SHA256;
wire [WD-1:0] hash_data_address2_SHA256;
wire [ 3-1:0] opcode_SHA256;
wire          hash_start_SHA256;

wire [64-1:0] hash_data_out1_SHA256;
wire [64-1:0] hash_data_out2_SHA256;
wire          hash_out_valid1_SHA256;
wire          hash_out_valid2_SHA256;
wire          done_SHA256;

wire [64-1:0] hash_data_in1_SHA512;
wire          hash_data_valid1_SHA512;
wire [WD-1:0] hash_data_address1_SHA512;
wire          o_s_fifo_full_SHA512;
wire [64-1:0] hash_data_in2_SHA512;
wire          hash_data_valid2_SHA512;
wire [WD-1:0] hash_data_address2_SHA512;
wire [ 3-1:0] opcode_SHA512;
wire          hash_start_SHA512;

wire [64-1:0] hash_data_out1_SHA512;
wire [64-1:0] hash_data_out2_SHA512;
wire          hash_out_valid1_SHA512;
wire          hash_out_valid2_SHA512;
wire          done_SHA512;

reg hash_sel;//0:SHA256, 1:SHA512 

always@(i_opcode) begin   
    if(i_opcode==3'd1 || i_opcode==3'd4 || i_opcode==3'd6) begin
        hash_sel <= 1'b0;
    end
    else begin
        hash_sel <= 1'b1;
    end    
end

assign hash_data_in1_SHA256         = i_s_data_in;
assign hash_data_valid1_SHA256      = hash_sel ? 1'b0 : i_s_wr_en;
assign hash_data_address1_SHA256    = hash_sel ? 7'd0 : i_s_addr;
assign hash_data_in2_SHA256         = i_b_data_in;
assign hash_data_valid2_SHA256      = hash_sel ? 1'b0 : i_b_wr_en;
assign hash_data_address2_SHA256    = hash_sel ? 7'd0 : i_b_addr;
assign opcode_SHA256                = i_opcode;
assign hash_start_SHA256            = hash_sel ? 1'b0 : i_start;

assign hash_data_in1_SHA512         = i_s_data_in;
assign hash_data_valid1_SHA512      = !hash_sel ? 1'b0 : i_s_wr_en;
assign hash_data_address1_SHA512    = !hash_sel ? 7'd0 : i_s_addr;
assign hash_data_in2_SHA512         = i_b_data_in;
assign hash_data_valid2_SHA512      = !hash_sel ? 1'b0 : i_b_wr_en;
assign hash_data_address2_SHA512    = !hash_sel ? 7'd0 : i_b_addr;
assign opcode_SHA512                = i_opcode;
assign hash_start_SHA512            = !hash_sel ? 1'b0 : i_start;


assign o_b_data_out_from_hash = !hash_sel ? hash_data_out1_SHA256 : hash_data_out1_SHA512;
assign o_s_data_out_from_hash = !hash_sel ? hash_data_out2_SHA256 : hash_data_out2_SHA512;
assign o_b_data_out_valid_from_hash = !hash_sel ? hash_out_valid1_SHA256 : hash_out_valid1_SHA512;
assign o_s_data_out_valid_from_hash = !hash_sel ? hash_out_valid2_SHA256 : hash_out_valid2_SHA512;
assign o_done = !hash_sel ? done_SHA256 : done_SHA512;
assign o_s_fifo_full = !hash_sel ? o_s_fifo_full_SHA256 : o_s_fifo_full_SHA512;

hash_tile #(
.IO_WIDTH             (IO_WIDTH             ),
.parameter_set        (parameter_set        ),
.IN_T_L_WOTS_WIDTH    (IN_T_L_WOTS_WIDTH    ),
.IN_T_L_FORS_WIDTH    (IN_T_L_FORS_WIDTH    ),
.IN_PRF_WIDTH         (IN_PRF_WIDTH         ),
.IN_H_XMSS_WIDTH      (IN_H_XMSS_WIDTH      ),
.IN_F_WOTS_PLUS_WIDTH (IN_F_WOTS_PLUS_WIDTH ),
.OUT_PRF_WIDTH        (OUT_PRF_WIDTH        ),
.OUT_H_XMSS_WIDTH     (OUT_H_XMSS_WIDTH     ),
.OUT_F_WOTS_PLUS_WIDTH(OUT_F_WOTS_PLUS_WIDTH),
.HASH                 ("SHA256"             )
)
DUT_SHA256
(
.clk(clk),
.rst(rst),
    
.i_s_data_in(hash_data_in1_SHA256     ),
.i_s_wr_en  (hash_data_valid1_SHA256  ),
.i_s_addr   (hash_data_address1_SHA256),
.i_s_rd_en                   (0                   ),
.o_s_fifo_full               (o_s_fifo_full_SHA256),

.i_b_data_in(hash_data_in2_SHA256     ),
.i_b_wr_en  (hash_data_valid2_SHA256  ),
.i_b_addr   (hash_data_address2_SHA256),
.i_b_rd_en                   (0                   ),

.i_msg_in_size  (i_msg_in_size), //in bytes
.i_h_iterations (i_h_iterations),

.i_opcode   (opcode_SHA256),
.i_start    (hash_start_SHA256),
.o_done     (done_SHA256),
.i_first_flag(i_first_flag),
.o_mode_flag(o_mode_flag1),

.o_b_data_out_from_hash      (hash_data_out1_SHA256 ),         
.o_b_data_out_valid_from_hash(hash_out_valid1_SHA256),   
.o_s_data_out_from_hash      (hash_data_out2_SHA256 ),         
.o_s_data_out_valid_from_hash(hash_out_valid2_SHA256)    
);

hash_tile #(
.IO_WIDTH             (IO_WIDTH             ),
.parameter_set        (parameter_set        ),
.IN_T_L_WOTS_WIDTH    (IN_T_L_WOTS_WIDTH    ),
.IN_T_L_FORS_WIDTH    (IN_T_L_FORS_WIDTH    ),
.IN_PRF_WIDTH         (IN_PRF_WIDTH         ),
.IN_H_XMSS_WIDTH      (IN_H_XMSS_WIDTH      ),
.IN_F_WOTS_PLUS_WIDTH (IN_F_WOTS_PLUS_WIDTH ),
.OUT_PRF_WIDTH        (OUT_PRF_WIDTH        ),
.OUT_H_XMSS_WIDTH     (OUT_H_XMSS_WIDTH     ),
.OUT_F_WOTS_PLUS_WIDTH(OUT_F_WOTS_PLUS_WIDTH),
.HASH                 ("SHA512"             )
)
DUT_SHA512
(
.clk(clk),
.rst(rst),
    
.i_s_data_in(hash_data_in1_SHA512     ),
.i_s_wr_en  (hash_data_valid1_SHA512  ),
.i_s_addr   (hash_data_address1_SHA512),
.i_s_rd_en                   (0                   ),
.o_s_fifo_full               (o_s_fifo_full_SHA512),

.i_b_data_in(hash_data_in2_SHA512     ),
.i_b_wr_en  (hash_data_valid2_SHA512  ),
.i_b_addr   (hash_data_address2_SHA512),
.i_b_rd_en                   (0                   ),

.i_msg_in_size  (i_msg_in_size), //in bytes
.i_h_iterations (i_h_iterations),

.i_opcode   (opcode_SHA512),
.i_start    (hash_start_SHA512),
.o_done     (done_SHA512),
.i_first_flag(i_first_flag),
.o_mode_flag(o_mode_flag2),

.o_b_data_out_from_hash      (hash_data_out1_SHA512 ),         
.o_b_data_out_valid_from_hash(hash_out_valid1_SHA512),   
.o_s_data_out_from_hash      (hash_data_out2_SHA512 ),         
.o_s_data_out_valid_from_hash(hash_out_valid2_SHA512)    
);
        
endmodule
