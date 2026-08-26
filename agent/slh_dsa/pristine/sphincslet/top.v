`timescale 1ns/1ps

`include "setting.v"

module top
#(
parameter IO_WIDTH = 64,
parameter parameter_set = `PARAM_SET,
parameter L_param = 
                    (parameter_set == "128s") ? 35: //chain length
                    (parameter_set == "128f") ? 35:
                    (parameter_set == "192s") ? 51:
                    (parameter_set == "192f") ? 51:
                    (parameter_set == "256s") ? 67:
                    (parameter_set == "256f") ? 67: 67,
parameter Chain_count_num = 
                    (parameter_set == "128s") ? 6:
                    (parameter_set == "128f") ? 6:
                    (parameter_set == "192s") ? 6:
                    (parameter_set == "192f") ? 6:
                    (parameter_set == "256s") ? 7:
                    (parameter_set == "256f") ? 7: 7,    
parameter XMSS_H_param = 
                    (parameter_set == "128s") ? 4:
                    (parameter_set == "128f") ? 3:
                    (parameter_set == "192s") ? 4:
                    (parameter_set == "192f") ? 4:
                    (parameter_set == "256s") ? 4:
                    (parameter_set == "256f") ? 4: 4,
parameter XMSS_Node_num = 
                    (parameter_set == "128s") ? 13:
                    (parameter_set == "128f") ? 7:
                    (parameter_set == "192s") ? 15:
                    (parameter_set == "192f") ? 9:
                    (parameter_set == "256s") ? 15:
                    (parameter_set == "256f") ? 10: 15,
parameter SEED_num = 
                    (parameter_set == "128s") ? 128:
                    (parameter_set == "128f") ? 128:
                    (parameter_set == "192s") ? 192:
                    (parameter_set == "192f") ? 192:
                    (parameter_set == "256s") ? 256:
                    (parameter_set == "256f") ? 256:
                                                128,
parameter Height_XMSS = 
                    (parameter_set == "128s") ? 9:
                    (parameter_set == "128f") ? 3:
                    (parameter_set == "192s") ? 9:
                    (parameter_set == "192f") ? 3:
                    (parameter_set == "256s") ? 8:
                    (parameter_set == "256f") ? 4: 9,
parameter Height_FORS = 
                    (parameter_set == "128s") ? 12:
                    (parameter_set == "128f") ? 6:
                    (parameter_set == "192s") ? 14:
                    (parameter_set == "192f") ? 8:
                    (parameter_set == "256s") ? 14:
                    (parameter_set == "256f") ? 9: 12,
parameter Leaf_Node_Num_WOTS = 
                    (parameter_set == "128s") ? 512:
                    (parameter_set == "128f") ? 8:
                    (parameter_set == "192s") ? 512:
                    (parameter_set == "192f") ? 8:
                    (parameter_set == "256s") ? 256:
                    (parameter_set == "256f") ? 16: 512,
parameter Leaf_Node_Num_XMSS = 
                    (parameter_set == "128s") ? 128:
                    (parameter_set == "128f") ? 8:
                    (parameter_set == "192s") ? 128:
                    (parameter_set == "192f") ? 2:
                    (parameter_set == "256s") ? 64:
                    (parameter_set == "256f") ? 4: 128,
parameter Leaf_Node_Num_FORS = 
                    (parameter_set == "128s") ? 4096:
                    (parameter_set == "128f") ? 64:
                    (parameter_set == "192s") ? 16384:
                    (parameter_set == "192f") ? 256:
                    (parameter_set == "256s") ? 16384:
                    (parameter_set == "256f") ? 512: 64, 
`ifdef SHAKE
    //Input Widths in SHAKE
    parameter IN_T_L_WOTS_WIDTH = 
                        (parameter_set == "128s") ? 608*8:
                        (parameter_set == "128f") ? 608*8:
                        (parameter_set == "192s") ? 1280*8:
                        (parameter_set == "192f") ? 1280*8:
                        (parameter_set == "256s") ? 2208*8:
                        (parameter_set == "256f") ? 2208*8: 2208*8,
    //Input Widths in SHAKE
    parameter IN_T_L_FORS_WIDTH = 
                        (parameter_set == "128s") ? 272*8:
                        (parameter_set == "128f") ? 576*8:
                        (parameter_set == "192s") ? 464*8:
                        (parameter_set == "192f") ? 848*8:
                        (parameter_set == "256s") ? 768*8:
                        (parameter_set == "256f") ? 1184*8: 1184*8,
`else
    `ifdef PARAM_128
    //Input Widths in SHA2
    parameter IN_T_L_WOTS_WIDTH = 
                        (parameter_set == "128s") ? 646*8:
                        (parameter_set == "128f") ? 646*8:
                        (parameter_set == "192s") ? 1310*8:
                        (parameter_set == "192f") ? 1310*8:
                        (parameter_set == "256s") ? 2230*8:
                        (parameter_set == "256f") ? 2230*8: 2230*8,
    //Input Widths in SHA2
    parameter IN_T_L_FORS_WIDTH = 
                        (parameter_set == "128s") ? 310*8:
                        (parameter_set == "128f") ? 614*8:
                        (parameter_set == "192s") ? 494*8:
                        (parameter_set == "192f") ? 878*8:
                        (parameter_set == "256s") ? 790*8:
                        (parameter_set == "256f") ? 1206*8: 1206*8,    
    `else
    //Input Widths in SHA2
    parameter IN_T_L_WOTS_WIDTH = 
                        (parameter_set == "128s") ? 710*8:
                        (parameter_set == "128f") ? 710*8:
                        (parameter_set == "192s") ? 1374*8:
                        (parameter_set == "192f") ? 1374*8:
                        (parameter_set == "256s") ? 2294*8:
                        (parameter_set == "256f") ? 2294*8: 2294*8,
    //Input Widths in SHA2
    parameter IN_T_L_FORS_WIDTH = 
                        (parameter_set == "128s") ? 374*8:
                        (parameter_set == "128f") ? 678*8:
                        (parameter_set == "192s") ? 558*8:
                        (parameter_set == "192f") ? 942*8:
                        (parameter_set == "256s") ? 854*8:
                        (parameter_set == "256f") ? 1270*8: 1270*8,    
    `endif
`endif                              
parameter INDICE_WD = 
                    (parameter_set == "128s") ? 16:
                    (parameter_set == "128f") ? 12:
                    (parameter_set == "192s") ? 19:
                    (parameter_set == "192f") ? 14:
                    (parameter_set == "256s") ? 19:
                    (parameter_set == "256f") ? 15: 15,
parameter LEAF_IDX_WD = 
                    (parameter_set == "128s") ? 9:
                    (parameter_set == "128f") ? 3:
                    (parameter_set == "192s") ? 9:
                    (parameter_set == "192f") ? 3:
                    (parameter_set == "256s") ? 8:
                    (parameter_set == "256f") ? 4: 4,                    
parameter WD = //address bit for max data length
                    (parameter_set == "128s") ? 7:
                    (parameter_set == "128f") ? 7:
                    (parameter_set == "192s") ? 8:
                    (parameter_set == "192f") ? 8:
                    (parameter_set == "256s") ? 9:
                    (parameter_set == "256f") ? 9: 9,
parameter N = 
                    (parameter_set == "128s") ? 16:
                    (parameter_set == "128f") ? 16:
                    (parameter_set == "192s") ? 24:
                    (parameter_set == "192f") ? 24:
                    (parameter_set == "256s") ? 32:
                    (parameter_set == "256f") ? 32: 16,
parameter H = 
                    (parameter_set == "128s") ? 63:
                    (parameter_set == "128f") ? 66:
                    (parameter_set == "192s") ? 63:
                    (parameter_set == "192f") ? 66:
                    (parameter_set == "256s") ? 64:
                    (parameter_set == "256f") ? 68: 63,
parameter D = 
                    (parameter_set == "128s") ? 7:
                    (parameter_set == "128f") ? 22:
                    (parameter_set == "192s") ? 7:
                    (parameter_set == "192f") ? 22:
                    (parameter_set == "256s") ? 8:
                    (parameter_set == "256f") ? 17: 7,
parameter LOG_T = 
                    (parameter_set == "128s") ? 12:
                    (parameter_set == "128f") ? 6:
                    (parameter_set == "192s") ? 14:
                    (parameter_set == "192f") ? 8:
                    (parameter_set == "256s") ? 14:
                    (parameter_set == "256f") ? 9: 12,
parameter K = 
                    (parameter_set == "128s") ? 14:
                    (parameter_set == "128f") ? 33:
                    (parameter_set == "192s") ? 17:
                    (parameter_set == "192f") ? 33:
                    (parameter_set == "256s") ? 22:
                    (parameter_set == "256f") ? 35: 14,
parameter XMSS_WD = 
                    (parameter_set == "128s") ? 6:
                    (parameter_set == "128f") ? 5:
                    (parameter_set == "192s") ? 7:
                    (parameter_set == "192f") ? 6:
                    (parameter_set == "256s") ? 7:
                    (parameter_set == "256f") ? 6: 6,                    
`ifdef SHAKE
    //Input Widths //SHAKE
    parameter IN_PRF_WIDTH              = (N + 32 + N)*8, //For SLH-DSA TEST
    parameter IN_H_XMSS_WIDTH           = (N + 32 + N + N )*8,
    parameter IN_F_WOTS_PLUS_WIDTH      = (N + 32 + N)*8,
    parameter IN_H_MSG_PARTIAL_WIDTH    = (N + N + N)*8,
    parameter IN_PRF_MSG_PARTIAL_WIDTH  = (N + 32)*8,
`else
    //Input Widths //SHA
    parameter IN_PRF_WIDTH              = (64 + 22 + N)*8, //For SLH-DSA TEST

    `ifdef PARAM_128
    parameter IN_H_XMSS_WIDTH           = (64 + 22 + N + N )*8,
    `else
    parameter IN_H_XMSS_WIDTH           = (128 + 22 + N + N )*8,
    `endif

    parameter IN_F_WOTS_PLUS_WIDTH      = (64 + 22 + N)*8,
    parameter IN_H_MSG_PARTIAL_WIDTH    = (N + N + N)*8,
    parameter IN_PRF_MSG_PARTIAL_WIDTH  = (N + 22)*8,        
`endif

//Output Widths
parameter OUT_T_L_WIDTH         = N*8,                  
parameter OUT_PRF_WIDTH         = N*8,              
parameter OUT_H_XMSS_WIDTH      = N*8,
parameter OUT_H_MSG_WIDTH = 
                (parameter_set == "128s") ? 30*8:
                (parameter_set == "128f") ? 34*8:
                (parameter_set == "192s") ? 39*8:
                (parameter_set == "192f") ? 42*8:
                (parameter_set == "256s") ? 48*8:
                (parameter_set == "256f") ? 49*8: 49*8,   
parameter OUT_F_WOTS_PLUS_WIDTH = N*8,
parameter OUT_PRF_MSG_WIDTH     = N*8
)
(
input  wire                     clk,
input  wire                     rstn,
input  wire [12-1:0]            i_msg_in_size,//type the message length in Bytes
input  wire                     i_sig_mode,//0: signature generation, 1: signature verification
input  wire                     i_FSM_start,//start sign gen or verify
output wire                     o_FSM_done,//done sign gen or verify
output wire                     o_c_flag,//indicate matched or not after verification

output wire [64-1:0]            o_sig_data,//write sig data in sign process
output wire                     o_sig_valid,//valid signal for sig data

input  wire [64-1:0]            sig_mem_out0,//read sig data in verify process
output wire [13-1:0]            sig_mem_addr0_w,//address to read sig data

input  wire [ 8-1:0]            i_SK_seed,//set SK.seed in the internal Memory
input  wire [ 8-1:0]            i_PK_seed,//set PK.seed in the internal Memory
input  wire                     seed_valid,

input  wire [64-1:0]            i_h_msg_mem_in0,//set key and msg in the internal Memory
input  wire  [9-1:0]            i_h_msg_mem_addr0,
input  wire                     i_h_msg_mem_wen0
);

wire [IO_WIDTH-1:0] s_out_0;
wire [IO_WIDTH-1:0] s_out_2;
wire [IO_WIDTH-1:0] s_in_0;
wire [IO_WIDTH-1:0] s_in_1;
wire [XMSS_WD -1:0] s_in_0_addr;
wire [XMSS_WD -1:0] s_in_1_addr;
wire                s_in_0_wr_en;
wire                s_in_1_wr_en;
wire                s_in_2_wr_en;
wire                s_in_3_wr_en;

wire [IO_WIDTH-1:0] wots_o_tmp_in_0;
wire [IO_WIDTH-1:0] wots_o_tmp_in_1;
wire [WD-1:0]       wots_o_tmp_in_0_addr;
wire [WD-1:0]       wots_o_tmp_in_1_addr;
wire                wots_o_tmp_in_0_wr_en;
wire                wots_o_tmp_in_1_wr_en;
wire [IO_WIDTH-1:0] wots_o_tmp_out_0;
wire [IO_WIDTH-1:0] wots_o_tmp_out_1;
wire                WOTS_s_in_0_wr_en;
wire                WOTS_FSM_start_out;

wire [64-1:0] tree_addr;
wire  [3-1:0] fsm_o_opcode;
wire [32-1:0] in_ap_leaf_idx;

wire          hash_o_done;
wire          hash_start;
wire [64-1:0] hash_data_in1;
wire          hash_data_valid1;
wire [WD-1:0] hash_data_address1;
wire [64-1:0] hash_data_in2;
wire          hash_data_valid2;
wire [WD-1:0] hash_data_address2;
wire [64-1:0] hash_data_out1;
wire [64-1:0] hash_data_out2;
wire          hash_out_valid1;
wire          hash_out_valid2;

wire          out_auth_path_flag;
wire          out_left_flag;
wire          o_FORS_tree_one_done;
wire          o_root_flag;
wire          o_FORS_prf_flag;
wire          o_chain_cnt_up;
wire          o_wots_chain_flag1;
wire          o_wots_chain_flag2;
wire  [4-1:0] o_wots_w_iter;

`ifdef PARAM_128
wire [64-1:0] tmp_reg0_1;
wire [64-1:0] tmp_reg0_2;
wire [64-1:0] tmp_reg1_1;
wire [64-1:0] tmp_reg1_2;
wire [64-1:0] tmp_reg2_1;
wire [64-1:0] tmp_reg2_2;
wire          tmp_flag0;
wire          tmp_flag1;
wire          tmp_flag2;
`endif

`ifdef PARAM_192
wire [64-1:0] tmp_reg0_1;
wire [64-1:0] tmp_reg0_2;
wire [64-1:0] tmp_reg0_3;
wire [64-1:0] tmp_reg1_1;
wire [64-1:0] tmp_reg1_2;
wire [64-1:0] tmp_reg1_3;
wire [64-1:0] tmp_reg2_1;
wire [64-1:0] tmp_reg2_2;
wire [64-1:0] tmp_reg2_3;
wire          tmp_flag0;
wire [2-1:0]  tmp_flag1;
wire [2-1:0]  tmp_flag2;
`endif

`ifdef PARAM_256
wire [64-1:0] tmp_reg0_1;
wire [64-1:0] tmp_reg0_2;
wire [64-1:0] tmp_reg0_3;
wire [64-1:0] tmp_reg0_4;
wire [64-1:0] tmp_reg1_1;
wire [64-1:0] tmp_reg1_2;
wire [64-1:0] tmp_reg1_3;
wire [64-1:0] tmp_reg1_4;
wire [64-1:0] tmp_reg2_1;
wire [64-1:0] tmp_reg2_2;
wire [64-1:0] tmp_reg2_3;
wire [64-1:0] tmp_reg2_4;
wire          tmp_flag0;
wire [2-1:0]  tmp_flag1;
wire [2-1:0]  tmp_flag2;
`endif

//-- root_mem ports --//
wire [64-1:0] root_mem_out0;
//-- write_to_root_mem ports --//
wire [64-1:0] rm_root_mem_in1;
wire  [6-1:0] rm_root_mem_addr1;
wire          rm_root_mem_wen1;
wire          rm_start_next;
//-- w_mem ports --//
wire [4-1:0] w_mem_in0;
wire [4-1:0] w_mem_in1;
`ifdef PARAM_128
wire [6-1:0] w_mem_addr0;
wire [6-1:0] w_mem_addr1;
`endif
`ifdef PARAM_192
wire [6-1:0] w_mem_addr0;
wire [6-1:0] w_mem_addr1;
`endif
`ifdef PARAM_256
wire [7-1:0] w_mem_addr0;
wire [7-1:0] w_mem_addr1;
`endif
wire         w_mem_wen0;
wire         w_mem_wen1;
wire [4-1:0] w_mem_out0;
wire [4-1:0] w_mem_out1;

wire [6-1:0] cl_root_mem_addr0;
`ifdef PARAM_128
wire [6-1:0] cl_w_mem_addr0;
wire [6-1:0] cl_w_mem_addr1;
`endif
`ifdef PARAM_192
wire [6-1:0] cl_w_mem_addr0;
wire [6-1:0] cl_w_mem_addr1;
`endif
`ifdef PARAM_256
wire [7-1:0] cl_w_mem_addr0;
wire [7-1:0] cl_w_mem_addr1;
`endif
wire         cl_start_next;
wire         o_cl_flag;

wire [INDICE_WD-1:0] indices_mem_in0;
wire                 indices_mem_wen0;
wire [INDICE_WD-1:0] indices_mem_out0;

wire          mti_next_start;
wire  [4-1:0] mti_msg_digest_mem_addr0;
wire  [4-1:0] mti_msg_digest_mem_addr1;
wire  [6-1:0] mti_indices_mem_addr0;

wire  [3-1:0] hm_o_opcode  ;
wire          hm_o_h_start ;
wire          hm_o_hm_done ;
wire [LEAF_IDX_WD-1:0] hm_o_leaf_idx;
wire [64-1:0] hm_i_m1_data ; 
wire [64-1:0] hm_o_m1_data ; // output memory for H_msg, opcode=3
wire  [9-1:0] hm_o_m1_addr ;
wire          hm_o_m1_valid;
wire [64-1:0] hm_i_h0_data ; //input from hash_tile
wire          hm_i_h0_valid;
wire          hm_i_h0_ready;
wire [64-1:0] hm_o_h0_data ; // output to hash_tile
wire [WD-1:0] hm_o_h0_addr ;
wire          hm_o_h0_valid;
wire          o_s_fifo_full;
wire          R_valid_flag0;
reg           msg_w_flag0;
wire          hm_o_sig_read;
wire [64-1:0] hm_i_sig_data;

wire [64-1:0] h_msg_mem_in0;
wire  [9-1:0] h_msg_mem_addr0;
wire          h_msg_mem_wen0;
wire [64-1:0] h_msg_mem_out0;

wire          sig_mem_flag0;
wire          sig_mem_flag1;
reg  [13-1:0] sig_mem_addr0;

wire  [3-1:0] w_opcode;
wire          w_hash_start;
wire [64-1:0] w_hash_data_in1;
wire [WD-1:0] w_hash_data_address1;
wire          w_hash_data_valid1;

wire [WD      -1:0] XMSS_s_in_0_addr;
wire                XMSS_s_in_0_wr_en;

wire                     PRF_msg_flag;
wire                     H_msg_flag;
reg   [5-1:0]            cnt;
reg                      msg_write_start;
reg                      root_compare_start;
reg                      FSM_done;
reg                      msg_mode;
reg   [2-1:0]            mode;
reg                      XMSS_FSM_start;
wire                     XMSS_FSM_done;
reg                      WOTS_FSM_start;
wire                     WOTS_FSM_done;
reg  [XMSS_H_param -1:0] XMSS_tree_height;
reg  [INDICE_WD    -1:0] leaf_node_num_WOTS;
reg  [INDICE_WD    -1:0] F_iter_in_WOTS;
reg  [INDICE_WD    -1:0] in_leaf_idx;
reg   [6-1:0]            indices_mem_addr0;
reg                      hm_i_hm_mode;
reg                      hm_i_hm_start;
reg                      mti_start;
reg                      mti_mode;
reg                      HT_start;
reg  [6-1:0]             tree_cnt;
`ifdef SHA2
    wire                     first_flag;
    `ifdef PARAM_128
        wire                     mode_flag;
    `else
        wire                     mode_flag1;
        wire                     mode_flag2;
    `endif
`endif

assign o_FSM_done = FSM_done;

assign sig_mem_addr0_w = sig_mem_addr0;

assign o_sig_data           = sig_data;
assign o_sig_valid          = sig_valid;

assign h_msg_mem_in0        = hm_o_m1_data;
assign h_msg_mem_addr0      = mti_mode ? mti_msg_digest_mem_addr0 + 9'd448 : hm_o_m1_addr;
assign h_msg_mem_wen0       = hm_o_m1_valid;

assign hm_i_m1_data         = h_msg_mem_out0;

assign in_ap_leaf_idx       = hm_o_leaf_idx;
assign w_opcode             = msg_mode==1'b1 ? hm_o_opcode : fsm_o_opcode;
assign w_hash_start         = msg_mode==1'b1 ? hm_o_h_start : hash_start;
assign w_hash_data_in1      = msg_mode==1'b1 ? hm_o_h0_data : hash_data_in1;
assign w_hash_data_address1 = msg_mode==1'b1 ? hm_o_h0_addr : hash_data_address1;
assign w_hash_data_valid1   = msg_mode==1'b1 ? hm_o_h0_valid : hash_data_valid1;
assign hm_i_h0_data         = hash_data_out2;
assign hm_i_h0_valid        = hash_out_valid2;
assign hm_i_h0_ready        = o_s_fifo_full;
assign hm_i_sig_data        = sig_mem_out0;
assign sig_mem_flag1        = sig_mem_flag0 || hm_o_sig_read;

reg [SEED_num-1:0] PK_seed;
reg [SEED_num-1:0] SK_seed;
always@(posedge clk) begin
    if(seed_valid) begin
        PK_seed <= {i_PK_seed,PK_seed[SEED_num-1:8]};
        SK_seed <= {i_SK_seed,SK_seed[SEED_num-1:8]};
    end
    else begin
        PK_seed <= PK_seed;
        SK_seed <= SK_seed;
    end
end

hash_message
#(
.parameter_set(parameter_set)
) 
hm_fsm_md0 (
.clk           (clk          ),
.rstn          (rstn         ),
.o_opcode      (hm_o_opcode  ),
.i_sig_mode    (i_sig_mode   ),
.i_hm_mode     (hm_i_hm_mode ),
.i_hm_start    (hm_i_hm_start),
.o_h_start     (hm_o_h_start ),
.o_hm_done     (hm_o_hm_done ),
.o_PRF_msg_flag(PRF_msg_flag ),
.o_H_msg_flag  (H_msg_flag   ),
.msg_w_start   (msg_write_start   ),
.root_c_start  (root_compare_start),
.i_rt_data     (rm_root_mem_in1   ),
.i_rt_valid    (rm_root_mem_wen1  ),
.o_c_flag      (o_c_flag     ),
`ifdef SHA2
.o_first_flag  (first_flag   ),
`endif
.i_mlen        (i_msg_in_size),
.i_m1_data     (hm_i_m1_data ), 
.o_m1_data     (hm_o_m1_data ), // output memory for H_msg, opcode=3
.o_m1_addr     (hm_o_m1_addr ),
.o_m1_valid    (hm_o_m1_valid),
.o_sig_read    (hm_o_sig_read),
.i_sig_data    (hm_i_sig_data),
.o_tree        (tree_addr    ),
.o_leaf_idx    (hm_o_leaf_idx),
.i_h0_data     (hm_i_h0_data ), // input from hash_tile
.i_h0_valid    (hm_i_h0_valid),
.i_h0_ready    (hm_i_h0_ready),
.o_h0_data     (hm_o_h0_data ), // output to hash_tile
.o_h0_addr     (hm_o_h0_addr ),
.o_h0_valid    (hm_o_h0_valid)
);


FSM 
#(
.parameter_set(parameter_set)
) 
wots_xmss_fsm_md0 (
.clk                 (clk                 ),
.rstn                (rstn                ),
.WOTS_start          (WOTS_FSM_start      ),
.XMSS_start          (XMSS_FSM_start      ),
.HT_start            (HT_start            ),
.o_opcode            (fsm_o_opcode        ),
.o_hash_start        (hash_start          ),
.i_hash_done         (hash_o_done         ),
.SK_seed             (SK_seed             ),
.PK_seed             (PK_seed             ),
.tree_addr           (tree_addr           ),
.leaf_node_num_WOTS  (leaf_node_num_WOTS  ),
.XMSS_tree_height    (XMSS_tree_height    ),
.o_WOTS_done         (WOTS_FSM_done       ),
.o_XMSS_done         (XMSS_FSM_done       ),
.o_s_data_in         (hash_data_in1       ),
.o_s_wr_en           (hash_data_valid1    ),
.o_s_addr            (hash_data_address1  ),
.o_b_data_in         (hash_data_in2       ),
.o_b_wr_en           (hash_data_valid2    ),
.o_b_addr            (hash_data_address2  ),
.i_b_hash_data_out   (hash_data_out1      ),         
.i_b_hash_out_valid  (hash_out_valid1     ),   
.i_s_hash_data_out   (hash_data_out2      ),         
.i_s_hash_out_valid  (hash_out_valid2     ),    
.s_out_0             (s_out_0             ),
.s_out_2             (s_out_2             ),
.s_in_0              (s_in_0              ),
.s_in_1              (s_in_1              ),
.s_in_0_addr         (s_in_0_addr         ),
.s_in_1_addr         (s_in_1_addr         ),
.s_in_0_wr_en        (s_in_0_wr_en        ),
.s_in_1_wr_en        (s_in_1_wr_en        ),
.s_in_2_wr_en        (s_in_2_wr_en        ),
.s_in_3_wr_en        (s_in_3_wr_en        ),
.wots_o_tmp_in_0_addr (wots_o_tmp_in_0_addr ),
.wots_o_tmp_in_1_addr (wots_o_tmp_in_1_addr ),
.wots_o_tmp_in_0_wr_en(wots_o_tmp_in_0_wr_en),
.wots_o_tmp_in_1_wr_en(wots_o_tmp_in_1_wr_en),
.wots_o_tmp_out_0     (wots_o_tmp_out_0     ),
.wots_o_tmp_out_1     (wots_o_tmp_out_1     ),
.WOTS_s_in_0_wr_en    (WOTS_s_in_0_wr_en    ),
.o_XMSS_s_in_0_addr   (XMSS_s_in_0_addr     ),
.o_XMSS_s_in_0_wr_en  (XMSS_s_in_0_wr_en    ),
.WOTS_FSM_start       (WOTS_FSM_start_out   ),
.W_param             (F_iter_in_WOTS      ),
.i_sig_mode          (i_sig_mode          ),
.mode                (mode                ),
`ifdef SHA2
`ifdef PARAM_128
.i_mode_flag         (mode_flag           ),
`else
.i_mode_flag1        (mode_flag1          ),
.i_mode_flag2        (mode_flag2          ),
`endif
`endif
.leaf_idx            (in_leaf_idx         ),
.ap_leaf_idx         (in_ap_leaf_idx      ),
.o_auth_path_flag    (out_auth_path_flag  ),
.Left_flag           (out_left_flag       ),
.o_FORS_tree_one_done(o_FORS_tree_one_done),
.root_flag           (o_root_flag         ),
.FORS_prf_flag       (o_FORS_prf_flag     ),
.o_chain_cnt_up      (o_chain_cnt_up      ),
.o_wots_chain_flag1  (o_wots_chain_flag1  ),
.o_wots_chain_flag2  (o_wots_chain_flag2  ),
.o_wots_w_iter       (o_wots_w_iter       ),
.in_w_cnt1           (w_mem_out0          ),
.in_w_cnt2           (w_mem_out1          ),
.o_sig_mem_flag0     (sig_mem_flag0       ),
.i_sig_mem_out0      (sig_mem_out0        ),
.tmp_reg0_1          (tmp_reg0_1          ),
.tmp_reg0_2          (tmp_reg0_2          ),
.tmp_reg1_1          (tmp_reg1_1          ),
.tmp_reg1_2          (tmp_reg1_2          ),
.tmp_reg2_1          (tmp_reg2_1          ),
.tmp_reg2_2          (tmp_reg2_2          ),
.tmp_flag0           (tmp_flag0           ), 
.tmp_flag1           (tmp_flag1           ),
.tmp_flag2           (tmp_flag2           ),
`ifdef PARAM_192
.tmp_reg0_3          (tmp_reg0_3          ),
.tmp_reg1_3          (tmp_reg1_3          ),
.tmp_reg2_3          (tmp_reg2_3          ),
`endif
`ifdef PARAM_256
.tmp_reg0_3          (tmp_reg0_3          ),
.tmp_reg0_4          (tmp_reg0_4          ),
.tmp_reg1_3          (tmp_reg1_3          ),
.tmp_reg1_4          (tmp_reg1_4          ),
.tmp_reg2_3          (tmp_reg2_3          ),
.tmp_reg2_4          (tmp_reg2_4          ),
`endif
.w_mem_addr0         (w_mem_addr0         ),
.w_mem_addr1         (w_mem_addr1         )
);

message_to_indices
mti_md0
(
.clk           (clk                     ),
.rstn          (rstn                    ),
.mti_start     (mti_start               ),
.mti_next_start(mti_next_start          ),
.i_data0       (h_msg_mem_out0          ),
.o_raddr0      (mti_msg_digest_mem_addr0),
.o_data0       (indices_mem_in0         ),
.o_waddr0      (mti_indices_mem_addr0   ),
.o_valid0      (indices_mem_wen0        )
);

write_to_root_mem 
root_md0
(
.clk         (clk              ),
.rstn        (rstn             ),
.mode        (mode             ),
.i_data      (hash_data_out2   ),
.i_vaild     (hash_out_valid2  ),
.o_data      (rm_root_mem_in1  ),
.o_addr      (rm_root_mem_addr1),
.o_valid     (rm_root_mem_wen1 ),
.root_flag   (o_root_flag      ),
.o_start_next(rm_start_next    )
);

chain_lengths
cl_md0 (
.clk           (clk              ),
.rstn          (rstn             ),
.cl_start      (rm_start_next    ),
.o_cl_flag     (o_cl_flag        ),
.root          (root_mem_out0    ),
.root_mem_addr0(cl_root_mem_addr0),
.w_mem_in0     (w_mem_in0        ),
.w_mem_in1     (w_mem_in1        ),
.w_mem_addr0   (cl_w_mem_addr0   ),
.w_mem_addr1   (cl_w_mem_addr1   ),
.w_mem_wen0    (w_mem_wen0       ),
.w_mem_wen1    (w_mem_wen1       ),
.o_start_next  (cl_start_next    )
);

`ifdef SHAKE
    hash_tile
    #(
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
    .HASH                 (`HASH1               )
    )
    hash_tile_md0
    (
    .clk                         (clk                 ),
    .rst                         (!rstn               ),
    .i_opcode                    (w_opcode            ),
    .i_start                     (w_hash_start        ),
    .o_done                      (hash_o_done         ),
    .i_msg_in_size               (i_msg_in_size       ), //in bytes
    .i_h_iterations              (o_wots_w_iter       ),
    .i_s_data_in                 (w_hash_data_in1     ),
    .i_s_wr_en                   (w_hash_data_valid1  ),
    .i_s_addr                    (w_hash_data_address1),
    .i_s_rd_en                   (0                   ),
    .o_s_fifo_full               (o_s_fifo_full       ),
    .i_b_data_in                 (hash_data_in2       ),
    .i_b_wr_en                   (hash_data_valid2    ),
    .i_b_addr                    (hash_data_address2  ),
    .i_b_rd_en                   (0                   ),
    .o_b_data_out_from_hash      (hash_data_out1      ),         
    .o_b_data_out_valid_from_hash(hash_out_valid1     ),   
    .o_s_data_out_from_hash      (hash_data_out2      ),         
    .o_s_data_out_valid_from_hash(hash_out_valid2     )    
    );
`else
    `ifdef PARAM_128
        hash_tile
        #(
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
        .HASH                 (`HASH1               )
        )
        hash_tile_md0
        (
        .clk                         (clk                 ),
        .rst                         (!rstn               ),
        .i_opcode                    (w_opcode            ),
        .i_start                     (w_hash_start        ),
        .o_done                      (hash_o_done         ),
        .i_first_flag                (first_flag          ),
        .o_mode_flag                 (mode_flag           ),
        .i_msg_in_size               (i_msg_in_size       ), //in bytes
        .i_h_iterations              (o_wots_w_iter       ),
        .i_s_data_in                 (w_hash_data_in1     ),
        .i_s_wr_en                   (w_hash_data_valid1  ),
        .i_s_addr                    (w_hash_data_address1),
        .i_s_rd_en                   (0                   ),
        .o_s_fifo_full               (o_s_fifo_full       ),
        .i_b_data_in                 (hash_data_in2       ),
        .i_b_wr_en                   (hash_data_valid2    ),
        .i_b_addr                    (hash_data_address2  ),
        .i_b_rd_en                   (0                   ),
        .o_b_data_out_from_hash      (hash_data_out1      ),         
        .o_b_data_out_valid_from_hash(hash_out_valid1     ),   
        .o_s_data_out_from_hash      (hash_data_out2      ),         
        .o_s_data_out_valid_from_hash(hash_out_valid2     )    
        );
    `else
        two_hash_tile 
        #(
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
        .HASH                 (`HASH1               )
        )
        hash_tile_md0
        (
        .clk                         (clk                 ),
        .rst                         (!rstn               ),
        .i_opcode                    (w_opcode            ),
        .i_start                     (w_hash_start        ),
        .o_done                      (hash_o_done         ),
        .i_first_flag                (first_flag          ),
        .o_mode_flag1                (mode_flag1          ),
        .o_mode_flag2                (mode_flag2          ),
        .i_msg_in_size               (i_msg_in_size       ), //in bytes
        .i_h_iterations              (o_wots_w_iter       ),
        .i_s_data_in                 (w_hash_data_in1     ),
        .i_s_wr_en                   (w_hash_data_valid1  ),
        .i_s_addr                    (w_hash_data_address1),
        .o_s_fifo_full               (o_s_fifo_full       ),
        .i_b_data_in                 (hash_data_in2       ),
        .i_b_wr_en                   (hash_data_valid2    ),
        .i_b_addr                    (hash_data_address2  ),
        .o_b_data_out_from_hash      (hash_data_out1      ),         
        .o_b_data_out_valid_from_hash(hash_out_valid1     ),   
        .o_s_data_out_from_hash      (hash_data_out2      ),         
        .o_s_data_out_valid_from_hash(hash_out_valid2     )    
        );
    `endif
`endif


mem_dual #(
.WIDTH(64), 
.DEPTH(512), 
.FILE(""),
.INIT(0)
) 
H_MSG_MEM (
.clock    (clk                                ),
.data_0   (i_h_msg_mem_in0   | h_msg_mem_in0  ),
.data_1   (64'd0                              ),
.address_0(i_h_msg_mem_addr0 | h_msg_mem_addr0),
.address_1(9'd0                               ),
.wren_0   (i_h_msg_mem_wen0  | h_msg_mem_wen0 ),
.wren_1   (1'b0                               ),
.q_0      (h_msg_mem_out0                     ),
.q_1      (                                   )
);

mem_dual #(
.WIDTH(INDICE_WD),
.DEPTH(64), 
.FILE(""),
.INIT(0)
) 
INDICES_MEM (
.clock    (clk              ),
.data_0   (indices_mem_in0  ),
.data_1   (19'd0            ),
.address_0(indices_mem_addr0 | mti_indices_mem_addr0),
.address_1(6'd0             ),
.wren_0   (indices_mem_wen0 ),
.wren_1   (1'b0             ),
.q_0      (indices_mem_out0 ),
.q_1      ( )
);

mem_dual #(
.WIDTH(4), 
.DEPTH(L_param+1), 
.FILE(""),
.INIT(0)
) 
W_MEM (
.clock    (clk        ),
.data_0   (w_mem_in0  ),
.data_1   (w_mem_in1  ),
.address_0(w_mem_addr0 | cl_w_mem_addr0),
.address_1(w_mem_addr1 | cl_w_mem_addr1),
.wren_0   (w_mem_wen0 ),
.wren_1   (w_mem_wen1 ),
.q_0      (w_mem_out0 ),
.q_1      (w_mem_out1 )
);

wire [64-1:0] m64_in0;
wire [64-1:0] m64_in1;
wire [9-1:0] m64_addr0;
wire [9-1:0] m64_addr1;
wire m64_wen0;
wire m64_wen1;
wire [64-1:0] m64_out0;
wire [64-1:0] m64_out1;

wire wots_wen0;
wire wots_wen1;

assign wots_wen0 = (WOTS_FSM_start_out && (wots_o_tmp_in_0_wr_en && !WOTS_s_in_0_wr_en)) || (!WOTS_FSM_start_out && (wots_o_tmp_in_0_wr_en && WOTS_s_in_0_wr_en));
assign wots_wen1 = (WOTS_FSM_start_out && (wots_o_tmp_in_1_wr_en && !WOTS_s_in_0_wr_en)) || (!WOTS_FSM_start_out && (wots_o_tmp_in_1_wr_en && WOTS_s_in_0_wr_en));

wire s_wen0;
wire s_wen2;
wire s_wen1;
wire s_wen3;

assign s_wen0 = s_in_0_wr_en && !XMSS_s_in_0_wr_en;
assign s_wen2 = s_in_2_wr_en && !XMSS_s_in_0_wr_en;
assign s_wen1 = s_in_1_wr_en && !XMSS_s_in_0_wr_en;
assign s_wen3 = s_in_3_wr_en && !XMSS_s_in_0_wr_en;

assign m64_in0 = s_in_0;
assign m64_in1 = rm_root_mem_wen1 ? rm_root_mem_in1 : s_in_1;                 

`ifdef PARAM_128
assign m64_addr0 = s_wen0             ? s_in_0_addr :
                   s_wen2             ? s_in_0_addr + 9'd64 : 
                   o_cl_flag          ? cl_root_mem_addr0 + 9'd448 :
                   wots_wen0          ? wots_o_tmp_in_0_addr + 9'd128 :
                   WOTS_FSM_start_out ? wots_o_tmp_in_0_addr + 9'd128 : s_in_0_addr;
assign m64_addr1 = rm_root_mem_wen1   ? rm_root_mem_addr1 + 9'd448 :
                   s_in_0_wr_en       ? s_in_1_addr :
                   s_in_2_wr_en       ? s_in_1_addr + 9'd64 : 
                   wots_wen1          ? wots_o_tmp_in_1_addr + 9'd128 : 
                   WOTS_FSM_start_out ? wots_o_tmp_in_1_addr + 9'd128 : s_in_0_addr + 9'd64;
`endif

`ifdef PARAM_192
assign m64_addr0 = s_wen0             ? s_in_0_addr :
                   s_wen2             ? s_in_0_addr + 9'd128 : 
                   o_cl_flag          ? cl_root_mem_addr0 + 9'd448 :
                   wots_wen0          ? wots_o_tmp_in_0_addr + 9'd256 :
                   WOTS_FSM_start_out ? wots_o_tmp_in_0_addr + 9'd256 : s_in_0_addr;
assign m64_addr1 = rm_root_mem_wen1   ? rm_root_mem_addr1 + 9'd448 :
                   s_in_0_wr_en       ? s_in_1_addr :
                   s_in_2_wr_en       ? s_in_1_addr + 9'd128 : 
                   wots_wen1          ? wots_o_tmp_in_1_addr + 9'd256 : 
                   WOTS_FSM_start_out ? wots_o_tmp_in_1_addr + 9'd256 : s_in_0_addr + 9'd128;
`endif

`ifdef PARAM_256
assign m64_addr0 = s_wen0             ? s_in_0_addr :
                   s_wen2             ? s_in_0_addr + 9'd112 : 
                   o_cl_flag          ? cl_root_mem_addr0 + 9'd504 :
                   wots_wen0          ? wots_o_tmp_in_0_addr + 9'd224 :
                   WOTS_FSM_start_out ? wots_o_tmp_in_0_addr + 9'd224 : s_in_0_addr;
assign m64_addr1 = rm_root_mem_wen1   ? rm_root_mem_addr1 + 9'd504 :
                   s_in_0_wr_en       ? s_in_1_addr :
                   s_in_2_wr_en       ? s_in_1_addr + 9'd112 : 
                   wots_wen1          ? wots_o_tmp_in_1_addr + 9'd224 : 
                   WOTS_FSM_start_out ? wots_o_tmp_in_1_addr + 9'd224 : s_in_0_addr + 9'd112;
`endif

assign m64_wen0 = rm_root_mem_wen1 ? 1'b0 :
                  s_in_0_wr_en     ? 1'b1 :
                  s_in_2_wr_en     ? 1'b1 : 
                  wots_wen0        ? 1'b1 : 1'b0;
assign m64_wen1 = rm_root_mem_wen1 ? 1'b1 :
                  s_wen1           ? 1'b1 :
                  s_wen3           ? 1'b1 : 
                  wots_wen1        ? 1'b1 : 1'b0;                  

assign s_out_0 = m64_out0;
assign s_out_2 = m64_out1;

assign wots_o_tmp_out_0 = m64_out0;
assign wots_o_tmp_out_1 = m64_out1;

assign root_mem_out0 = m64_out0;


mem_dual #(
.WIDTH(IO_WIDTH), 
.DEPTH(512),
.FILE(""),
.INIT(0)
) 
MEM_64BIT_1 (
.clock    (clk      ),
.data_0   (m64_in0  ),
.data_1   (m64_in1  ),
.address_0(m64_addr0),
.address_1(m64_addr1),
.wren_0   (m64_wen0 ),
.wren_1   (m64_wen1 ),
.q_0      (m64_out0 ),
.q_1      (m64_out1 )
);


always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        cnt                <= 5'd0;
        tree_cnt           <= 0;
        FSM_done           <= 1'b0;
        mode               <= 2'd0;
        msg_mode           <= 1'b0;
        hm_i_hm_mode       <= 1'b0;
        hm_i_hm_start      <= 1'b0;
        XMSS_FSM_start     <= 1'b0;
        WOTS_FSM_start     <= 1'b0;
        mti_start          <= 1'b0;
        mti_mode           <= 1'b0;
        HT_start           <= 1'b0;
        root_compare_start <= 1'b0;
        msg_write_start    <= 1'b0;
        msg_w_flag0        <= 1'b0;
        XMSS_tree_height   <= 0;
        leaf_node_num_WOTS <= 0;
        F_iter_in_WOTS     <= 0;
        in_leaf_idx        <= 0;
        indices_mem_addr0  <= 0;
    end
    else begin
        case(cnt)
        5'd0: begin
            FSM_done <= 1'b0;
            if(i_FSM_start) begin
                msg_mode      <= 1'b1;
                if(i_sig_mode==1'b1) begin
                    hm_i_hm_mode  <= 1'b1;
                end
                else begin
                    hm_i_hm_mode  <= 1'b0;
                end
                hm_i_hm_start <= 1'b1;
                cnt <= 5'd1;
            end
            else begin
                msg_mode      <= 1'b0;
                hm_i_hm_mode  <= 1'b0;
                hm_i_hm_start <= 1'b0;
            end
        end
        5'd1: begin
            FSM_done <= 1'b0;
            if(hm_o_hm_done) begin 
                msg_mode           <= 1'b0;
                mode               <= 2'd1; //FORS leaf gen + XMSS root node 
                XMSS_tree_height   <= Height_FORS;
                leaf_node_num_WOTS <= Leaf_Node_Num_FORS * K;
                F_iter_in_WOTS     <= (Leaf_Node_Num_FORS * K) - 1;
                mti_start          <= 1'b1;
                mti_mode           <= 1'b1;
                cnt <= 5'd2;
            end
            else begin
                hm_i_hm_mode  <= 1'b0;
                hm_i_hm_start <= 1'b0;
            end
        end
        5'd2: begin
            if(mti_next_start) begin
                in_leaf_idx       <= indices_mem_out0;
                indices_mem_addr0 <= indices_mem_addr0 + 1;
                XMSS_FSM_start    <= 1'b1;
                HT_start          <= 1'b1;
                mti_mode          <= 1'b0;
                cnt <= 5'd3;
            end
            else begin
                mti_start      <= 1'b0;
                XMSS_FSM_start <= 1'b0;
                HT_start       <= 1'b0;
            end
        end
        5'd3: begin
            if(o_FORS_tree_one_done) begin            
                if(tree_cnt==K-2) begin                   
                    in_leaf_idx       <= indices_mem_out0;
                    indices_mem_addr0 <= 0;
                    tree_cnt          <= 0;
                    cnt <= 5'd4;
                end
                else begin
                    in_leaf_idx       <= indices_mem_out0;
                    indices_mem_addr0 <= indices_mem_addr0 + 1;
                    tree_cnt          <= tree_cnt + 1;
                    cnt <= 5'd3;
                end
            end
            else begin
                XMSS_FSM_start <= 1'b0;
                HT_start       <= 1'b0;
            end
        end
        5'd4: begin
            if(XMSS_FSM_done) begin
                mode           <= 2'd3; //FORS roots compression 
                WOTS_FSM_start <= 1'b1;
                cnt <= 5'd5;
            end
            else begin
                WOTS_FSM_start <= 1'b0;
            end
        end       
        5'd5: begin
            if(cl_start_next) begin
                mode               <= 2'd0; //WOTS pk gen + XMSS root node 
                XMSS_tree_height   <= Height_XMSS;
                leaf_node_num_WOTS <= Leaf_Node_Num_WOTS;
                F_iter_in_WOTS     <= 19'd15; 
                XMSS_FSM_start     <= 1'b1;
                cnt <= 5'd6;
            end
            else begin
                WOTS_FSM_start <= 1'b0;
            end
        end
        5'd6: begin
            if(cl_start_next) begin
                XMSS_FSM_start <= 1'b1;
                if(tree_cnt==D-2) begin
                    tree_cnt <= 0;
                    
                    if(i_sig_mode==1'b1) begin
                        //start comparing root with PK.root
                        root_compare_start <= 1'b1;
                        cnt <= 5'd9;
                    end
                    else begin
                        cnt <= 5'd7;
                    end
                end
                else begin
                    root_compare_start <= 1'b0;
                    tree_cnt <= tree_cnt + 1;
                    cnt <= 5'd6;
                end
            end
            else begin
                root_compare_start <= 1'b0;
                XMSS_FSM_start <= 1'b0;
            end
        end
        5'd7: begin
            if(XMSS_FSM_done) begin
                //start writing msg to SIG
                msg_write_start <= 1'b1;
                msg_w_flag0 <=1'b1;
                cnt <= 5'd8;
            end
            else begin
                XMSS_FSM_start <= 1'b0;
            end
        end        
        5'd8: begin
            if(hm_o_hm_done) begin
                msg_w_flag0 <=1'b0;
                cnt <= 5'd10;
            end
            else begin
                msg_write_start <= 1'b0;
            end
        end
        5'd9: begin
            XMSS_FSM_start <= 1'b0;
            if(hm_o_hm_done) begin
                //matching pass or fail come from "hm_0_c_flag" signal
                cnt <= 5'd10;
                root_compare_start <= 1'b0;
            end
        end
        5'd10: begin
            FSM_done <= 1'b1;
            cnt <= 5'd0;
        end          
        endcase
    end
end


always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        sig_mem_addr0 <= 13'd0;
    end
    else begin
        if(i_sig_mode==1'b1) begin
            if(sig_mem_flag1) begin
                sig_mem_addr0 <= sig_mem_addr0 + 1'b1;
            end
            else begin
                sig_mem_addr0 <= sig_mem_addr0;
            end
        end
        else begin
            sig_mem_addr0 <= 12'd0;
        end
    end
end

`ifdef PARAM_128
reg [64-1:0] sig_data;
reg          sig_valid;
reg          tmp_flag0_d;
reg          tmp_flag1_d;
reg          tmp_flag2_d;
reg          tmp_flag2_d2;
always@(posedge clk) begin    
    if(PRF_msg_flag) begin
        `ifdef SHAKE
        if(hm_i_h0_valid) begin
            sig_data <= hm_i_h0_data;
        end
        `else
        if(hm_i_h0_valid && !first_flag) begin
            sig_data <= hm_i_h0_data;
        end
        `endif
        else if(msg_w_flag0 && hm_o_h0_valid) begin
            sig_data <= hm_o_h0_data;         
        end
    end
    else if(tmp_flag0) begin
        sig_data <= tmp_reg0_1;
    end
    else if(out_auth_path_flag && (s_in_0_wr_en || s_in_2_wr_en) && !o_root_flag) begin
        if(out_left_flag) begin
            sig_data <= s_in_0;
        end
        else begin
            sig_data <= s_in_1;
        end
    end
    else if(o_FORS_prf_flag && hash_out_valid2) begin
        sig_data <= hash_data_out2;
    end
    else if(o_chain_cnt_up) begin
        if(tmp_flag1) begin
            sig_data <= tmp_reg1_1;
        end
    end
    else begin
        if(tmp_flag0_d) begin
            sig_data <= tmp_reg0_2;
        end
        else if(tmp_flag1_d) begin
            sig_data <= tmp_reg1_2;
        end
        else if(tmp_flag2_d) begin
            sig_data <= tmp_reg2_1;
        end
        else if(tmp_flag2_d2) begin
            sig_data <= tmp_reg2_2;
        end
    end
end
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        sig_valid <= 1'b0;
        tmp_flag0_d <= 1'b0;
        tmp_flag1_d <= 1'b0;
        tmp_flag2_d <= 1'b0;
        tmp_flag2_d2 <= 1'b0;
    end
    else begin

        if(PRF_msg_flag) begin
            `ifdef SHAKE
            if(hm_i_h0_valid || (msg_w_flag0 && hm_o_h0_valid)) begin
                sig_valid <= 1'b1;
            end
            `else
            if((hm_i_h0_valid && !first_flag) || (msg_w_flag0 && hm_o_h0_valid)) begin
                sig_valid <= 1'b1;
            end
            `endif
            else begin
                sig_valid <= 1'b0;                  
            end
        end
        else if(tmp_flag0) begin
            sig_valid <= 1'b1;
            tmp_flag0_d <= 1'b1;
        end
        else if(out_auth_path_flag && (s_in_0_wr_en || s_in_2_wr_en) && !o_root_flag) begin
            sig_valid <= 1'b1;
        end
        else if(o_FORS_prf_flag && hash_out_valid2) begin
            sig_valid <= 1'b1;
        end
        else if(o_chain_cnt_up) begin
            if(tmp_flag1) begin
                sig_valid <= 1'b1;
                tmp_flag1_d <= 1'b1;
            end

            if(tmp_flag2) begin
                tmp_flag2_d <= 1'b1;
            end
        end
        else begin
            if(tmp_flag0_d) begin
                sig_valid <= 1'b1;
                tmp_flag0_d <= 1'b0;
            end
            else if(tmp_flag1_d) begin
                sig_valid <= 1'b1;
                tmp_flag1_d <= 1'b0;
            end
            else if(tmp_flag2_d) begin
                sig_valid <= 1'b1;
                tmp_flag2_d <= 1'b0;
                tmp_flag2_d2 <= 1'b1;
            end
            else if(tmp_flag2_d2) begin
                sig_valid <= 1'b1;
                tmp_flag2_d2 <= 1'b0;
            end
            else begin
                sig_valid <= 1'b0;
            end
        end
    end
end
`endif

`ifdef PARAM_192
reg [64-1:0] sig_data;
reg          sig_valid;
reg  [2-1:0] tmp_flag0_d;
reg  [2-1:0] tmp_flag1_d;
reg          tmp_flag2_d;
reg  [2-1:0] tmp_flag2_d2;
always@(posedge clk) begin
    if(PRF_msg_flag) begin
        `ifdef SHAKE
        if(hm_i_h0_valid) begin
            sig_data <= hm_i_h0_data;
        end
        `else
        if(hm_i_h0_valid && !first_flag) begin
            sig_data <= hm_i_h0_data;
        end
        `endif
        else if(msg_w_flag0 && hm_o_h0_valid) begin
            sig_data <= hm_o_h0_data;             
        end
    end
    else if(tmp_flag0) begin
        sig_data <= tmp_reg0_1;
    end
    else if(out_auth_path_flag && (s_in_0_wr_en || s_in_2_wr_en) && !o_root_flag) begin
        if(out_left_flag) begin
            sig_data <= s_in_0;
        end
        else begin
            sig_data <= s_in_1;
        end
    end
    else if(o_FORS_prf_flag && hash_out_valid2) begin
        sig_data <= hash_data_out2;
    end
    else if(o_chain_cnt_up) begin
        if(tmp_flag1==2'd2) begin
            sig_data <= tmp_reg1_1;
        end
    end
    else begin
        if(tmp_flag0_d!=2'd0) begin
            if(tmp_flag0_d==2'd2) begin
                sig_data <= tmp_reg0_3;
            end
            else if(tmp_flag0_d==2'd1) begin
                sig_data <= tmp_reg0_2;
            end
        end
        else if(tmp_flag1_d!=2'd0) begin
            if(tmp_flag1_d==2'd2) begin
                sig_data <= tmp_reg1_3;
            end
            else if(tmp_flag1_d==2'd1) begin
                sig_data <= tmp_reg1_2;
            end
        end
        else if(tmp_flag2_d) begin
            sig_data <= tmp_reg2_1;
        end
        else if(tmp_flag2_d2!=2'd0) begin
            if(tmp_flag2_d2==2'd2) begin
                sig_data <= tmp_reg2_3;
            end
            else if(tmp_flag2_d2==2'd1) begin
                sig_data <= tmp_reg2_2;
            end                
        end
    end
end
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        sig_valid <= 1'b0;
        tmp_flag0_d <= 2'd0;
        tmp_flag1_d <= 2'd0;
        tmp_flag2_d <= 1'b0;
        tmp_flag2_d2 <= 2'd0;
    end
    else begin

        if(PRF_msg_flag) begin
            `ifdef SHAKE
            if(hm_i_h0_valid) begin
                sig_valid <= 1'b1;
            end
            `else
            if(hm_i_h0_valid && !first_flag) begin
                sig_valid <= 1'b1;
            end
            `endif
            else if(msg_w_flag0 && hm_o_h0_valid) begin
                sig_valid <= 1'b1;                
            end
            else begin
                sig_valid <= 1'b0;                  
            end
        end
        else if(tmp_flag0) begin
            sig_valid <= 1'b1;
            tmp_flag0_d <= 2'd1;
        end
        else if(out_auth_path_flag && (s_in_0_wr_en || s_in_2_wr_en) && !o_root_flag) begin
            if(out_left_flag) begin
                sig_valid <= 1'b1;
            end
            else begin
                sig_valid <= 1'b1;
            end
        end
        else if(o_FORS_prf_flag && hash_out_valid2) begin
            sig_valid <= 1'b1;
        end
        else if(o_chain_cnt_up) begin
            if(tmp_flag1==2'd2) begin
                sig_valid <= 1'b1;
                tmp_flag1_d <= 2'd1;
            end

            if(tmp_flag2==2'd2) begin
                tmp_flag2_d <= 1'b1;
            end
        end
        else begin
            if(tmp_flag0_d!=2'd0) begin
                if(tmp_flag0_d==2'd2) begin
                    tmp_flag0_d <= 2'd0;
                end
                else if(tmp_flag0_d==2'd1) begin
                    tmp_flag0_d <= tmp_flag0_d + 1;
                end
                sig_valid <= 1'b1;
            end
            else if(tmp_flag1_d!=2'd0) begin
                if(tmp_flag1_d==2'd2) begin
                    tmp_flag1_d <= 2'd0;
                end
                else if(tmp_flag1_d==2'd1) begin
                    tmp_flag1_d <= tmp_flag1_d + 1;
                end
                sig_valid <= 1'b1;
            end
            else if(tmp_flag2_d) begin
                sig_valid <= 1'b1;
                tmp_flag2_d <= 1'b0;
                tmp_flag2_d2 <= 2'd1;
            end
            else if(tmp_flag2_d2!=2'd0) begin
                if(tmp_flag2_d2==2'd2) begin
                    tmp_flag2_d2 <= 2'd0;
                end
                else if(tmp_flag2_d2==2'd1) begin
                    tmp_flag2_d2 <= tmp_flag2_d2 + 1;
                end                
                sig_valid <= 1'b1;
            end
            else begin
                sig_valid <= 1'b0;
            end
        end
    end
end
`endif

`ifdef PARAM_256
reg [64-1:0] sig_data;
reg          sig_valid;
reg  [2-1:0] tmp_flag0_d;
reg  [2-1:0] tmp_flag1_d;
reg          tmp_flag2_d;
reg  [2-1:0] tmp_flag2_d2;
always@(posedge clk) begin
    if(PRF_msg_flag) begin
        `ifdef SHAKE
        if(hm_i_h0_valid) begin
            sig_data <= hm_i_h0_data;
        end
        `else
        if(hm_i_h0_valid && !first_flag) begin
            sig_data <= hm_i_h0_data;
        end
        `endif
        else if(msg_w_flag0 && hm_o_h0_valid) begin
            sig_data <= hm_o_h0_data;
        end
    end
    else if(tmp_flag0) begin
        sig_data <= tmp_reg0_1;
    end
    else if(out_auth_path_flag && (s_in_0_wr_en || s_in_2_wr_en) && !o_root_flag) begin
        if(out_left_flag) begin
            sig_data <= s_in_0;
        end
        else begin
            sig_data <= s_in_1;
        end
    end
    else if(o_FORS_prf_flag && hash_out_valid2) begin
        sig_data <= hash_data_out2;
    end
    else if(o_chain_cnt_up) begin
        if(tmp_flag1==2'd3) begin
            sig_data <= tmp_reg1_1;
        end
    end
    else begin
        if(tmp_flag0_d!=2'd0) begin
            if(tmp_flag0_d==2'd3) begin
                sig_data <= tmp_reg0_4;
            end
            else if(tmp_flag0_d==2'd2) begin
                sig_data <= tmp_reg0_3;
            end
            else if(tmp_flag0_d==2'd1) begin
                sig_data <= tmp_reg0_2;
            end
        end
        else if(tmp_flag1_d!=2'd0) begin
            if(tmp_flag1_d==2'd3) begin
                sig_data <= tmp_reg1_4;
            end
            else if(tmp_flag1_d==2'd2) begin
                sig_data <= tmp_reg1_3;
            end
            else if(tmp_flag1_d==2'd1) begin
                sig_data <= tmp_reg1_2;
            end
        end
        else if(tmp_flag2_d) begin
            sig_data <= tmp_reg2_1;
        end
        else if(tmp_flag2_d2!=2'd0) begin
            if(tmp_flag2_d2==2'd3) begin
                sig_data <= tmp_reg2_4;
            end
            else if(tmp_flag2_d2==2'd2) begin
                sig_data <= tmp_reg2_3;
            end
            else if(tmp_flag2_d2==2'd1) begin
                sig_data <= tmp_reg2_2;
            end                
        end
    end
end
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        sig_valid <= 1'b0;
        tmp_flag0_d <= 2'd0;
        tmp_flag1_d <= 2'd0;
        tmp_flag2_d <= 1'b0;
        tmp_flag2_d2 <= 2'd0;
    end
    else begin

        if(PRF_msg_flag) begin
            `ifdef SHAKE
            if(hm_i_h0_valid) begin
                sig_valid <= 1'b1;
            end
            `else
            if(hm_i_h0_valid && !first_flag) begin
                sig_valid <= 1'b1;
            end
            `endif
            else if(msg_w_flag0 && hm_o_h0_valid) begin
                sig_valid <= 1'b1;                
            end
            else begin
                sig_valid <= 1'b0;                  
            end
        end
        else if(tmp_flag0) begin
            sig_valid <= 1'b1;
            tmp_flag0_d <= 2'd1;
        end
        else if(out_auth_path_flag && (s_in_0_wr_en || s_in_2_wr_en) && !o_root_flag) begin
            if(out_left_flag) begin
                sig_valid <= 1'b1;
            end
            else begin
                sig_valid <= 1'b1;
            end
        end
        else if(o_FORS_prf_flag && hash_out_valid2) begin
            sig_valid <= 1'b1;
        end
        else if(o_chain_cnt_up) begin
            if(tmp_flag1==2'd3) begin
                sig_valid <= 1'b1;
                tmp_flag1_d <= 2'd1;
            end

            if(tmp_flag2==2'd3) begin
                tmp_flag2_d <= 1'b1;
            end
        end
        else begin
            if(tmp_flag0_d!=2'd0) begin
                sig_valid <= 1'b1;
                tmp_flag0_d <= tmp_flag0_d + 1;
            end
            else if(tmp_flag1_d!=2'd0) begin
                sig_valid <= 1'b1;
                tmp_flag1_d <= tmp_flag1_d + 1;
            end
            else if(tmp_flag2_d) begin
                sig_valid <= 1'b1;
                tmp_flag2_d <= 1'b0;
                tmp_flag2_d2 <= 2'd1;
            end
            else if(tmp_flag2_d2!=2'd0) begin
                sig_valid <= 1'b1;
                tmp_flag2_d2 <= tmp_flag2_d2 + 1;
            end
            else begin
                sig_valid <= 1'b0;
            end
        end
    end
end
`endif

endmodule