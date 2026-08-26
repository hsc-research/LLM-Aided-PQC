module FSM
#(
parameter IO_WIDTH = 64,
parameter parameter_set = "128s",
parameter IN_T_L_WIDTH =    
                        (parameter_set == "128s") ? 608*8:
                        (parameter_set == "128f") ? 608*8:
                        (parameter_set == "192s") ? 1280*8:
                        (parameter_set == "192f") ? 1280*8:
                        (parameter_set == "256s") ? 2208*8:
                        (parameter_set == "256f") ? 2208*8: 2208*8,
parameter L_param = //chain length        
                        (parameter_set == "128s") ? 35: 
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
parameter SEED_num = 
                        (parameter_set == "128s") ? 128:
                        (parameter_set == "128f") ? 128:
                        (parameter_set == "192s") ? 192:
                        (parameter_set == "192f") ? 192:
                        (parameter_set == "256s") ? 256:
                        (parameter_set == "256f") ? 256: 128,
parameter XMSS_Node_num = 
                        (parameter_set == "128s") ? 13:
                        (parameter_set == "128f") ? 7:
                        (parameter_set == "192s") ? 15:
                        (parameter_set == "192f") ? 9:
                        (parameter_set == "256s") ? 15:
                        (parameter_set == "256f") ? 10: 15,
parameter INDICE_WD = 
                        (parameter_set == "128s") ? 16:
                        (parameter_set == "128f") ? 12:
                        (parameter_set == "192s") ? 19:
                        (parameter_set == "192f") ? 14:
                        (parameter_set == "256s") ? 19:
                        (parameter_set == "256f") ? 15: 15,
parameter LEAF_WD = 
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
parameter XMSS_WD = 
                        (parameter_set == "128s") ? 6:
                        (parameter_set == "128f") ? 5:
                        (parameter_set == "192s") ? 7:
                        (parameter_set == "192f") ? 6:
                        (parameter_set == "256s") ? 7:
                        (parameter_set == "256f") ? 6: 6                        
)
(
input  wire                     clk,
input  wire                     rstn,
input  wire                     WOTS_start,
input  wire                     XMSS_start,
input  wire                     HT_start,
input  wire [SEED_num     -1:0] SK_seed,
input  wire [SEED_num     -1:0] PK_seed,
input  wire [64           -1:0] tree_addr,
input  wire [INDICE_WD    -1:0] leaf_node_num_WOTS,
input  wire [XMSS_H_param -1:0] XMSS_tree_height,
output wire                     o_WOTS_done,
output wire                     o_XMSS_done,
output wire [IO_WIDTH     -1:0] o_s_data_in,
output wire                     o_s_wr_en,
output wire [WD           -1:0] o_s_addr,
output wire [IO_WIDTH     -1:0] o_b_data_in,
output wire                     o_b_wr_en,
output wire [WD           -1:0] o_b_addr,
output wire [3-1:0]             o_opcode,
output wire                     o_hash_start,
input  wire                     i_hash_done,
input  wire [IO_WIDTH     -1:0] i_b_hash_data_out,         
input  wire                     i_b_hash_out_valid,   
input  wire [IO_WIDTH     -1:0] i_s_hash_data_out,         
input  wire                     i_s_hash_out_valid,
input  wire [IO_WIDTH     -1:0] s_out_0,
input  wire [IO_WIDTH     -1:0] s_out_2,
output wire [IO_WIDTH     -1:0] s_in_0,
output wire [IO_WIDTH     -1:0] s_in_1,
output wire [XMSS_WD      -1:0] s_in_0_addr,
output wire [XMSS_WD      -1:0] s_in_1_addr,
output wire                     s_in_0_wr_en,
output wire                     s_in_1_wr_en,
output wire                     s_in_2_wr_en,
output wire                     s_in_3_wr_en,
output wire [WD           -1:0] wots_o_tmp_in_0_addr,
output wire [WD           -1:0] wots_o_tmp_in_1_addr,
output wire                     wots_o_tmp_in_0_wr_en,
output wire                     wots_o_tmp_in_1_wr_en,
input  wire [IO_WIDTH     -1:0] wots_o_tmp_out_0,
input  wire [IO_WIDTH     -1:0] wots_o_tmp_out_1,
output reg  [WD      -1:0]      o_XMSS_s_in_0_addr,
output reg                      o_XMSS_s_in_0_wr_en,
output wire                     WOTS_s_in_0_wr_en,
output wire                     WOTS_FSM_start,
input  wire [INDICE_WD    -1:0] W_param,
input  wire                     i_sig_mode,
input  wire [2-1:0]             mode,
`ifdef SHA2
`ifdef PARAM_128
input  wire                     i_mode_flag,
`else
input  wire                     i_mode_flag1,
input  wire                     i_mode_flag2,
`endif
`endif
input  wire [INDICE_WD    -1:0] leaf_idx,
input  wire [32-1:0]            ap_leaf_idx,
output wire                     o_auth_path_flag,
output wire                     Left_flag,
output wire                     o_FORS_tree_one_done,
output wire                     root_flag,
output wire                     FORS_prf_flag,
output wire                     o_chain_cnt_up,
output wire                     o_wots_chain_flag1,
output wire                     o_wots_chain_flag2,
output wire [4-1:0]             o_wots_w_iter,
input  wire [4-1:0]             in_w_cnt1,
input  wire [4-1:0]             in_w_cnt2,
output wire                     o_sig_mem_flag0,
input  wire [64-1:0]            i_sig_mem_out0,
output reg  [64-1:0]            tmp_reg0_1,
output reg  [64-1:0]            tmp_reg0_2,
output reg  [64-1:0]            tmp_reg1_1,
output reg  [64-1:0]            tmp_reg1_2,
output reg  [64-1:0]            tmp_reg2_1,
output reg  [64-1:0]            tmp_reg2_2,
output reg                      tmp_flag0,
`ifdef PARAM_128           
output reg                      tmp_flag1,
output reg                      tmp_flag2,
`endif           
`ifdef PARAM_192           
output reg  [64-1:0]            tmp_reg0_3,
output reg  [64-1:0]            tmp_reg1_3,
output reg  [64-1:0]            tmp_reg2_3,
output reg  [ 2-1:0]            tmp_flag1,
output reg  [ 2-1:0]            tmp_flag2,
`endif           
`ifdef PARAM_256           
output reg  [64-1:0]            tmp_reg0_3,
output reg  [64-1:0]            tmp_reg0_4,
output reg  [64-1:0]            tmp_reg1_3,
output reg  [64-1:0]            tmp_reg1_4,
output reg  [64-1:0]            tmp_reg2_3,
output reg  [64-1:0]            tmp_reg2_4,
output reg  [ 2-1:0]            tmp_flag1,
output reg  [ 2-1:0]            tmp_flag2,
`endif           
`ifdef PARAM_128           
output reg  [6-1:0]             w_mem_addr0,
output reg  [6-1:0]             w_mem_addr1
`endif           
`ifdef PARAM_192           
output reg  [6-1:0]             w_mem_addr0,
output reg  [6-1:0]             w_mem_addr1
`endif           
`ifdef PARAM_256           
output reg  [7-1:0]             w_mem_addr0,
output reg  [7-1:0]             w_mem_addr1
`endif
);

wire                     WOTS_FSM_start;
wire                     XMSS_FSM_start;
wire [IO_WIDTH-1:0]      WOTS_hash_data_out1 ;        
wire                     WOTS_hash_out_valid1;   
wire [IO_WIDTH-1:0]      WOTS_hash_data_out2 ;        
wire                     WOTS_hash_out_valid2;
wire [IO_WIDTH-1:0]      XMSS_hash_data_out1 ;        
wire                     XMSS_hash_out_valid1;   
wire [IO_WIDTH-1:0]      XMSS_hash_data_out2 ;        
wire                     XMSS_hash_out_valid2;
wire [IO_WIDTH-1:0]      XMSS_s_out_0;
wire [IO_WIDTH-1:0]      XMSS_s_out_2;
wire                     WOTS_s_in_0_wr_en;
wire                     WOTS_s_in_1_wr_en;
wire [XMSS_WD -1:0]      XMSS_s_in_0_addr;
wire [XMSS_WD -1:0]      XMSS_s_in_1_addr;
wire [IO_WIDTH-1:0]      WOTS_hash_data_in1;
wire                     WOTS_hash_data_valid1;
wire [WD-1:0]            WOTS_hash_data_address1;
wire [IO_WIDTH-1:0]      WOTS_hash_data_in2;
wire                     WOTS_hash_data_valid2;
wire [WD-1:0]            WOTS_hash_data_address2;
wire [3-1:0]             WOTS_opcode;
wire                     WOTS_hash_start;
wire                     WOTS_o_hash_done;
wire [IO_WIDTH-1:0]      XMSS_hash_data_in1;
wire                     XMSS_hash_data_valid1;
wire [WD-1:0]            XMSS_hash_data_address1;
wire [IO_WIDTH-1:0]      XMSS_hash_data_in2;
wire                     XMSS_hash_data_valid2;
wire [WD-1:0]            XMSS_hash_data_address2;
wire [3-1:0]             XMSS_opcode;
wire                     XMSS_hash_start;
wire                     XMSS_o_hash_done;
wire                     WOTS_FSM_done;
wire                     XMSS_FSM_done;
`ifdef PARAM_128
reg  [3-1:0]             cnt_mem_addr;
`endif
`ifdef PARAM_192
reg  [4-1:0]             cnt_mem_addr;
`endif
`ifdef PARAM_256
reg  [4-1:0]             cnt_mem_addr;
`endif
reg  [8-1:0]             cnt_mem_addr2;
reg  [IO_WIDTH-1:0]      o_WOTS_s_in_0;
reg  [IO_WIDTH-1:0]      o_WOTS_s_in_1;
reg  [XMSS_WD -1:0]      o_WOTS_s_in_0_addr;
wire [XMSS_WD -1:0]      o_WOTS_s_in_1_addr;
reg                      o_WOTS_s_in_0_wr_en;
reg                      o_WOTS_s_in_1_wr_en;
reg                      o_WOTS_s_in_2_wr_en;
reg                      o_WOTS_s_in_3_wr_en;
wire                     XMSS_root_flag;
wire                     auth_path_flag;
wire                     leaf_node_gen_start;
reg                      XMSS_start_d;
reg                      XMSS_tree_done_d;
wire                     FORS_prf_in;
wire                     wots_chain_flag;
reg                      leaf_gen_flag;
wire                     XMSS_tree_done;
wire [INDICE_WD-1:0]     XMSS_leaf_idx;
reg  [32-1:0]            layer_addr_reg;
reg  [64-1:0]            tree_addr_reg;
reg  [LEAF_WD-1:0]       leaf_idx_reg;
wire [LEAF_WD-1:0]       leaf_idx_reg_w;
wire                     wots_chain_flag_w;
reg                      wots_chain_flag_d;
reg                      wots_chain_done;
reg                      tmp_flag0_2;
reg                      tmp_flag0_3;
wire                     wots_data_in_flag0;
wire                     wots_data_in_flag1;
wire                     wots_data_in_flag2;
wire                     wots_o_sig_read_mem;
wire                     xmss_o_sig_read_mem;
wire                     xmss_data_in_flag0;


assign o_FORS_tree_one_done = (XMSS_tree_done && XMSS_tree_done_d);
assign root_flag            = XMSS_root_flag;
assign FORS_prf_in          = mode == 2'd1 ? (XMSS_start_d || XMSS_tree_done_d) : 0;
assign XMSS_leaf_idx        = mode==2'd0 ? leaf_idx_reg[LEAF_WD-1:0] : leaf_idx;
assign leaf_idx_reg_w       = leaf_idx_reg;
assign wots_chain_flag_w    = wots_chain_flag && WOTS_FSM_start;
assign o_auth_path_flag     = mode==2'd0 ? (auth_path_flag && XMSS_FSM_start) : auth_path_flag;
assign o_sig_mem_flag0      = ((wots_o_sig_read_mem || xmss_o_sig_read_mem) || o_FORS_tree_one_done || XMSS_FSM_done);


`ifdef PARAM_128
assign o_WOTS_s_in_1_addr = o_WOTS_s_in_0_addr + 2'd2;
`endif
`ifdef PARAM_192
assign o_WOTS_s_in_1_addr = o_WOTS_s_in_0_addr + 3'd3;
`endif
`ifdef PARAM_256
assign o_WOTS_s_in_1_addr = o_WOTS_s_in_0_addr + 3'd4;
`endif

assign WOTS_hash_data_out1  = i_b_hash_data_out;
assign WOTS_hash_data_out2  = i_s_hash_data_out;
assign WOTS_hash_out_valid1 = WOTS_FSM_start ? i_b_hash_out_valid : 0;
assign WOTS_hash_out_valid2 = WOTS_FSM_start ? i_s_hash_out_valid : 0;

assign XMSS_hash_data_out1  = i_b_hash_data_out;
assign XMSS_hash_data_out2  = i_s_hash_data_out;
assign XMSS_hash_out_valid1 = XMSS_FSM_start ? i_b_hash_out_valid : 0;
assign XMSS_hash_out_valid2 = XMSS_FSM_start ? i_s_hash_out_valid : 0;

assign XMSS_s_out_0 = s_out_0;
assign XMSS_s_out_2 = s_out_2;

assign s_in_0       = o_WOTS_s_in_0; 
assign s_in_1       = o_WOTS_s_in_1; 

assign s_in_0_addr  = WOTS_FSM_start ? o_WOTS_s_in_0_addr  : XMSS_s_in_0_addr;
assign s_in_1_addr  = WOTS_FSM_start ? o_WOTS_s_in_1_addr  : XMSS_s_in_1_addr;

assign s_in_0_wr_en = o_WOTS_s_in_0_wr_en; 
assign s_in_1_wr_en = o_WOTS_s_in_1_wr_en; 
assign s_in_2_wr_en = o_WOTS_s_in_2_wr_en; 
assign s_in_3_wr_en = o_WOTS_s_in_3_wr_en; 

assign o_s_data_in  = WOTS_FSM_start ? WOTS_hash_data_in1      : XMSS_hash_data_in1     ;
assign o_s_wr_en    = WOTS_FSM_start ? WOTS_hash_data_valid1   : XMSS_hash_data_valid1  ;
assign o_s_addr     = WOTS_FSM_start ? WOTS_hash_data_address1 : XMSS_hash_data_address1;
assign o_b_data_in  = WOTS_FSM_start ? WOTS_hash_data_in2      : XMSS_hash_data_in2     ;
assign o_b_wr_en    = WOTS_FSM_start ? WOTS_hash_data_valid2   : XMSS_hash_data_valid2  ;
assign o_b_addr     = WOTS_FSM_start ? WOTS_hash_data_address2 : XMSS_hash_data_address2;
assign o_opcode     = WOTS_FSM_start ? WOTS_opcode             : XMSS_opcode            ;
assign o_hash_start = WOTS_FSM_start ? WOTS_hash_start         : XMSS_hash_start        ;

assign WOTS_o_hash_done = WOTS_FSM_start ? i_hash_done : 0;
assign XMSS_o_hash_done = XMSS_FSM_start ? i_hash_done : 0;

assign o_WOTS_done = WOTS_FSM_done;
assign o_XMSS_done = XMSS_FSM_done;

WOTS_FSM
#(
.parameter_set(parameter_set)
) 
md1 (
.clk             (clk           ),
.rstn            (rstn          ),

//--control signal for WOTS--//
.i_sig_mode      (i_sig_mode    ),
.mode            (mode          ),
`ifdef SHA2
`ifdef PARAM_128
.i_mode_flag1    (i_mode_flag   ),
`else
.i_mode_flag1    (i_mode_flag1  ),
.i_mode_flag2    (i_mode_flag2  ),
`endif
`endif
.FSM_start_in    (WOTS_start    || leaf_node_gen_start), //WOTS+XMSS in HT
.FSM_start_out   (WOTS_FSM_start),

//--fixed input data--//
.SK_seed         (SK_seed ), //SK.seed
.PK_seed         (PK_seed ), //PK.seed
.W_param         (W_param     ),
//--variable input data--//
.layer_addr      (layer_addr_reg       ),
.tree_addr       (tree_addr_reg        ),//64bit
.o_WOTS_done     (WOTS_FSM_done        ),
.leaf_node_num   (leaf_node_num_WOTS),

//--flags for output--//
.XMSS_root_flag    (XMSS_root_flag     ),
.XMSS_addr         (o_XMSS_s_in_0_addr ),
.w_addr2           (          leaf_idx ),//WOTS keypair address
.ap_leaf_idx       (leaf_idx_reg_w     ),
.o_w_iter          (o_wots_w_iter      ),
.in_w_cnt1         (in_w_cnt1          ),
.in_w_cnt2         (in_w_cnt2          ),
.FORS_prf_in       (FORS_prf_in        ),
.FORS_prf_flag     (FORS_prf_flag      ),
.i_wots_chain_flag (  wots_chain_flag  ),
.o_wots_chain_flag1(o_wots_chain_flag1 ),
.o_wots_chain_flag2(o_wots_chain_flag2 ),
.o_chain_cnt_up    (o_chain_cnt_up     ),
.o_sig_read_mem    (wots_o_sig_read_mem),
.i_sig_mem_out     (i_sig_mem_out0     ),

//--control signal for the hash_tile--//
.o_hash_start    (WOTS_hash_start),
.i_hash_done     (WOTS_o_hash_done),
.o_opcode        (WOTS_opcode    ),
//--output data to the hash_tile--//
.o_s_data_in     (WOTS_hash_data_in1     ),
.o_s_wr_en       (WOTS_hash_data_valid1  ),
.o_s_addr        (WOTS_hash_data_address1),
.o_b_data_in     (WOTS_hash_data_in2     ),
.o_b_wr_en       (WOTS_hash_data_valid2  ),
.o_b_addr        (WOTS_hash_data_address2),

.fsm_data_in_flag0(data_in_flag0),
.data_in_flag0(wots_data_in_flag0),
.data_in_flag1(wots_data_in_flag1),
.data_in_flag2(wots_data_in_flag2),
//--R/W control signal for the memory--//
.s_in_0_wr_en(WOTS_s_in_0_wr_en),
.s_in_1_wr_en(WOTS_s_in_1_wr_en),

.wots_o_tmp_in_0_addr (wots_o_tmp_in_0_addr ),
.wots_o_tmp_in_1_addr (wots_o_tmp_in_1_addr ),
.wots_o_tmp_in_0_wr_en(wots_o_tmp_in_0_wr_en),
.wots_o_tmp_in_1_wr_en(wots_o_tmp_in_1_wr_en),
.wots_o_tmp_out_0     (wots_o_tmp_out_0     ),
.wots_o_tmp_out_1     (wots_o_tmp_out_1     )
);

XMSS_FSM //with FORS
#(
    //mode0: HT mode with WOTS+pk + XMSS
    //mode1: FORS mode (diff is only a leaf node type)
.parameter_set(parameter_set)
) 
md0 (
.clk             (clk           ),
.rstn            (rstn          ),

//--control signal for XMSS--//
.i_sig_mode      (i_sig_mode    ),
.HT_mode         (mode          ),
`ifdef SHA2
`ifdef PARAM_128
.i_mode_flag     (i_mode_flag   ),
`else
.i_mode_flag     (i_mode_flag2  ),
`endif
`endif
.FSM_start_in    (XMSS_start    ),
.FSM_start_out   (XMSS_FSM_start),
.o_XMSS_done     (XMSS_FSM_done ),
.tree_done       (XMSS_tree_done),
.leaf_node_gen_start(leaf_node_gen_start),
.leaf_node_gen_done(leaf_gen_flag && WOTS_FSM_done), // WOTS+XMSS in HT
//--fixed input data--//
.PK_seed         (PK_seed           ), //PK.seed
.XMSS_tree_height(XMSS_tree_height  ),
//--variable input data--//
.layer_addr      (layer_addr_reg    ),
.tree_addr       (tree_addr_reg     ),//64bit
.ap_leaf_idx     (leaf_idx_reg_w    ),
.leaf_idx        (XMSS_leaf_idx     ),
//--flags for output--//
.flag_last       (XMSS_root_flag ),
.auth_path_flag  (auth_path_flag ),
.wots_chain_flag (wots_chain_flag),
.Left_flag       (Left_flag      ),
.o_sig_read_mem  (xmss_o_sig_read_mem),
.i_sig_mem_out   (i_sig_mem_out0     ),

//--control signal for the hash_tile--//
.o_hash_start    (XMSS_hash_start ),
.i_hash_done     (XMSS_o_hash_done),
.o_opcode        (XMSS_opcode     ),
//--output data to the hash_tile--//
.o_s_data_in     (XMSS_hash_data_in1     ),
.o_s_wr_en       (XMSS_hash_data_valid1  ),
.o_s_addr        (XMSS_hash_data_address1),
.o_b_data_in     (XMSS_hash_data_in2     ),
.o_b_wr_en       (XMSS_hash_data_valid2  ),
.o_b_addr        (XMSS_hash_data_address2),   

// //--R/W control signal for the memory--//
.fsm_data_in_flag0(o_WOTS_s_in_0_wr_en || o_WOTS_s_in_2_wr_en),
.data_in_flag0(xmss_data_in_flag0),
//--target address of the memory--//
.s_in_0_addr (XMSS_s_in_0_addr ),
.s_in_1_addr (XMSS_s_in_1_addr ),
//--input data from memory--//
.s_out_0     (XMSS_s_out_0     ),
.s_out_2     (XMSS_s_out_2     )
);

//In HT mode, WOTS pk gen control from XMSS
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        leaf_gen_flag <= 1'b0;
    end
    else begin
        XMSS_start_d <= XMSS_start;
        XMSS_tree_done_d <= XMSS_tree_done;
        if(leaf_node_gen_start) begin
            leaf_gen_flag <= 1'b1;
        end
        else begin
            if(leaf_gen_flag && WOTS_FSM_done) begin
                leaf_gen_flag <= 1'b0;
            end
        end
    end
end

wire data_in_flag0;
wire data_in_flag1;
wire data_in_flag2;
assign data_in_flag0 = (i_s_hash_out_valid && i_b_hash_out_valid);
assign data_in_flag1 = (data_in_flag0 && wots_data_in_flag0);
assign data_in_flag2 = (data_in_flag0 && wots_data_in_flag1);


always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        o_WOTS_s_in_0 <= 0;
        o_WOTS_s_in_1 <= 0;
    end
    else begin
        if(data_in_flag1 && mode==2'd0 && i_sig_mode==1'b0) begin
            o_WOTS_s_in_0 <= i_s_hash_data_out;
            o_WOTS_s_in_1 <= 0;                 
        end
        else if(data_in_flag1 && (mode==2'd1 || (mode==2'd0 && i_sig_mode==1'b1))) begin
            if(mode==2'd1) begin
                o_WOTS_s_in_0 <= i_s_hash_data_out;
                o_WOTS_s_in_1 <= i_b_hash_data_out;
            end
            else begin
                o_WOTS_s_in_0 <= i_s_hash_data_out;
                o_WOTS_s_in_1 <= i_s_hash_data_out;
            end
        end
        else if(data_in_flag2) begin
            o_WOTS_s_in_0 <= i_s_hash_data_out;
            o_WOTS_s_in_1 <= i_b_hash_data_out;
        end
        else if(wots_data_in_flag2) begin
            o_WOTS_s_in_0 <= i_sig_mem_out0;
            o_WOTS_s_in_1 <= 64'd0;
        end
        else if(XMSS_FSM_start) begin
            o_WOTS_s_in_0 <= i_s_hash_data_out;
            o_WOTS_s_in_1 <= i_b_hash_data_out;
        end
        else begin
            o_WOTS_s_in_0 <= 0;
            o_WOTS_s_in_1 <= 0;
        end
    end
end

always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        cnt_mem_addr <= 4'd0;
        o_WOTS_s_in_0_addr <= 0;
        o_WOTS_s_in_0_wr_en <= 0;
        o_WOTS_s_in_1_wr_en <= 0;
        o_WOTS_s_in_2_wr_en <= 0;
        o_WOTS_s_in_3_wr_en <= 0;
    end
    else begin

        if(XMSS_start || XMSS_tree_done) begin
            cnt_mem_addr <= 3'd0;
        end
        else if(WOTS_FSM_start) begin
            if(data_in_flag1 && mode==2'd0 && i_sig_mode==1'b0) begin

            `ifdef PARAM_128 
                if(!cnt_mem_addr[2]) begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[1:0];
                    o_WOTS_s_in_0_wr_en <= 1;
                    o_WOTS_s_in_1_wr_en <= 0;
                    o_WOTS_s_in_2_wr_en <= 0;
                    o_WOTS_s_in_3_wr_en <= 0;
                    cnt_mem_addr <= cnt_mem_addr + 1;
                end
                else begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[1:0];
                    o_WOTS_s_in_0_wr_en <= 0;
                    o_WOTS_s_in_1_wr_en <= 0;
                    o_WOTS_s_in_2_wr_en <= 1;
                    o_WOTS_s_in_3_wr_en <= 0;
                    cnt_mem_addr <= cnt_mem_addr + 1;
                end
                `endif 

            `ifdef PARAM_192
                if(!cnt_mem_addr[3]) begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[2:0];
                    o_WOTS_s_in_0_wr_en <= 1;
                    o_WOTS_s_in_1_wr_en <= 0;
                    o_WOTS_s_in_2_wr_en <= 0;
                    o_WOTS_s_in_3_wr_en <= 0;

                    if(cnt_mem_addr[2:0]==3'd5) begin
                        cnt_mem_addr <= cnt_mem_addr + 3'd3;
                    end
                    else begin
                        cnt_mem_addr <= cnt_mem_addr + 1;
                    end
                end
                else begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[2:0];
                    o_WOTS_s_in_0_wr_en <= 0;
                    o_WOTS_s_in_1_wr_en <= 0;
                    o_WOTS_s_in_2_wr_en <= 1;
                    o_WOTS_s_in_3_wr_en <= 0;

                    if(cnt_mem_addr[2:0]==3'd5) begin
                        cnt_mem_addr <= cnt_mem_addr + 3'd3;
                    end
                    else begin
                        cnt_mem_addr <= cnt_mem_addr + 1;
                    end
                end
                `endif 

            `ifdef PARAM_256
                if(!cnt_mem_addr[3]) begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[2:0];
                    o_WOTS_s_in_0_wr_en <= 1;
                    o_WOTS_s_in_1_wr_en <= 0;
                    o_WOTS_s_in_2_wr_en <= 0;
                    o_WOTS_s_in_3_wr_en <= 0;
                    cnt_mem_addr <= cnt_mem_addr + 1;
                end
                else begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[2:0];
                    o_WOTS_s_in_0_wr_en <= 0;
                    o_WOTS_s_in_1_wr_en <= 0;
                    o_WOTS_s_in_2_wr_en <= 1;
                    o_WOTS_s_in_3_wr_en <= 0;
                    cnt_mem_addr <= cnt_mem_addr + 1;
                end
                `endif                         
            end
            else if(data_in_flag1 && (mode==2'd1 || (mode==2'd0 && i_sig_mode==1'b1))) begin
                
                `ifdef PARAM_128
                if(!cnt_mem_addr[1]) begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[0];
                    o_WOTS_s_in_0_wr_en <= 1;
                    o_WOTS_s_in_1_wr_en <= 1;
                    o_WOTS_s_in_2_wr_en <= 0;
                    o_WOTS_s_in_3_wr_en <= 0;
                    cnt_mem_addr <= cnt_mem_addr + 2'd1;
                end
                else begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[0];
                    o_WOTS_s_in_0_wr_en <= 0;
                    o_WOTS_s_in_1_wr_en <= 0;
                    o_WOTS_s_in_2_wr_en <= 1;
                    o_WOTS_s_in_3_wr_en <= 1;
                    cnt_mem_addr <= cnt_mem_addr + 2'd1;
                end
                `endif 

                `ifdef PARAM_192 
                if(!cnt_mem_addr[2]) begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[1:0];
                    o_WOTS_s_in_0_wr_en <= 1;
                    o_WOTS_s_in_1_wr_en <= 1;
                    o_WOTS_s_in_2_wr_en <= 0;
                    o_WOTS_s_in_3_wr_en <= 0;

                    if(cnt_mem_addr[1:0]==2'd2) begin
                        cnt_mem_addr <= cnt_mem_addr + 2'd2;
                    end
                    else begin
                        cnt_mem_addr <= cnt_mem_addr + 1;
                    end
                end
                else begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[1:0];
                    o_WOTS_s_in_0_wr_en <= 0;
                    o_WOTS_s_in_1_wr_en <= 0;
                    o_WOTS_s_in_2_wr_en <= 1;
                    o_WOTS_s_in_3_wr_en <= 1;

                    if(cnt_mem_addr[1:0]==2'd2) begin
                        cnt_mem_addr <= cnt_mem_addr + 2'd2;
                    end
                    else begin
                        cnt_mem_addr <= cnt_mem_addr + 1;
                    end
                end
                `endif  

                `ifdef PARAM_256 
                if(!cnt_mem_addr[2]) begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[1:0];
                    o_WOTS_s_in_0_wr_en <= 1;
                    o_WOTS_s_in_1_wr_en <= 1;
                    o_WOTS_s_in_2_wr_en <= 0;
                    o_WOTS_s_in_3_wr_en <= 0;
                    cnt_mem_addr <= cnt_mem_addr + 2'd1;
                end
                else begin
                    o_WOTS_s_in_0_addr <= cnt_mem_addr[1:0];
                    o_WOTS_s_in_0_wr_en <= 0;
                    o_WOTS_s_in_1_wr_en <= 0;
                    o_WOTS_s_in_2_wr_en <= 1;
                    o_WOTS_s_in_3_wr_en <= 1;
                    cnt_mem_addr <= cnt_mem_addr + 2'd1;
                end
                `endif 
            end     
            else begin
            o_WOTS_s_in_0_addr <= 0;
            o_WOTS_s_in_0_wr_en <= 0;
            o_WOTS_s_in_1_wr_en <= 0;
            o_WOTS_s_in_2_wr_en <= 0;
            o_WOTS_s_in_3_wr_en <= 0;
            cnt_mem_addr <= cnt_mem_addr;
        end  
        end
        else if(XMSS_FSM_start) begin
            if(data_in_flag0) begin
                if(xmss_data_in_flag0) begin
                    o_WOTS_s_in_0_wr_en <= 1;
                    o_WOTS_s_in_1_wr_en <= 1;
                    o_WOTS_s_in_2_wr_en <= 0;
                    o_WOTS_s_in_3_wr_en <= 0;                
                end
                else begin
                    o_WOTS_s_in_0_wr_en <= 0;
                    o_WOTS_s_in_1_wr_en <= 0;
                    o_WOTS_s_in_2_wr_en <= 1;
                    o_WOTS_s_in_3_wr_en <= 1;                    
                end
            end
            else begin
                o_WOTS_s_in_0_wr_en <= 0;
                o_WOTS_s_in_1_wr_en <= 0;
                o_WOTS_s_in_2_wr_en <= 0;
                o_WOTS_s_in_3_wr_en <= 0;
            end
        end
        else begin
            o_WOTS_s_in_0_addr <= 0;
            o_WOTS_s_in_0_wr_en <= 0;
            o_WOTS_s_in_1_wr_en <= 0;
            o_WOTS_s_in_2_wr_en <= 0;
            o_WOTS_s_in_3_wr_en <= 0;
            cnt_mem_addr <= cnt_mem_addr;
        end
    end
end

always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        cnt_mem_addr2 <= 8'd4;
        o_XMSS_s_in_0_addr <= 0;
        o_XMSS_s_in_0_wr_en <= 0;
    end
    else begin
        if(XMSS_start) begin
            `ifdef PARAM_128
            cnt_mem_addr2 <= 8'd4;
            `endif 
            `ifdef PARAM_192
            cnt_mem_addr2 <= 8'd6;
            `endif 
            `ifdef PARAM_256
            cnt_mem_addr2 <= 8'd8;
            `endif 
        end
        else if(XMSS_root_flag && data_in_flag0 && mode==2'd1) begin          
            o_XMSS_s_in_0_addr <= cnt_mem_addr2;
            o_XMSS_s_in_0_wr_en <= 1;
            cnt_mem_addr2 <= cnt_mem_addr2 + 1;
        end
        else begin
            o_XMSS_s_in_0_addr <= 0;
            o_XMSS_s_in_0_wr_en <= 0;
            cnt_mem_addr2 <= cnt_mem_addr2;
        end
    end
end

`ifdef PARAM_128
reg HT_layer_flag;
//In HT, update leaf_idx and tree
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        HT_layer_flag <= 1'b0;
        layer_addr_reg <= 32'd0;
        tree_addr_reg <= 64'd0;
        leaf_idx_reg <= 32'd0;
    end
    else begin
        if(HT_start) begin //HT start
            layer_addr_reg <= 32'd0;
            tree_addr_reg <= tree_addr;
            leaf_idx_reg <= ap_leaf_idx;
        end
        //HyperTree mode
        else if(XMSS_root_flag && data_in_flag0 && mode==2'd0) begin
            if(HT_layer_flag) begin
                layer_addr_reg <= layer_addr_reg + 1;
                `ifdef PARAM_128F
                tree_addr_reg <= tree_addr_reg[63:3];
                leaf_idx_reg <= tree_addr_reg[2:0];
                `else //PARAM_128S
                tree_addr_reg <= tree_addr_reg[63:9];
                leaf_idx_reg <= tree_addr_reg[8:0];
                `endif
                HT_layer_flag <= 1'b0;
            end
            else begin
                HT_layer_flag <= 1'b1;
            end
        end
        else begin
            layer_addr_reg <= layer_addr_reg;
            tree_addr_reg <= tree_addr_reg;
            leaf_idx_reg <= leaf_idx_reg;
            HT_layer_flag <= HT_layer_flag;
        end
    end
end
`endif

`ifdef PARAM_192
reg [2-1:0] HT_layer_flag;
//In HT, update leaf_idx and tree
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        HT_layer_flag <= 2'd0;
        layer_addr_reg <= 32'd0;
        tree_addr_reg <= 64'd0;
        leaf_idx_reg <= 32'd0;
    end
    else begin
        if(HT_start) begin //HT start
            layer_addr_reg <= 32'd0;
            tree_addr_reg <= tree_addr;
            leaf_idx_reg <= ap_leaf_idx;
        end
        //HyperTree mode
        else if(XMSS_root_flag && data_in_flag0 && mode==2'd0) begin
            if(HT_layer_flag==2'd2) begin
                layer_addr_reg <= layer_addr_reg + 1;
                `ifdef PARAM_192F
                tree_addr_reg <= tree_addr_reg[63:3];
                leaf_idx_reg <= tree_addr_reg[2:0];
                `else //PARAM_192S
                tree_addr_reg <= tree_addr_reg[63:9];
                leaf_idx_reg <= tree_addr_reg[8:0];
                `endif
                HT_layer_flag <= 2'd0;
            end
            else begin
                HT_layer_flag <= HT_layer_flag + 2'd1;
            end
        end
        else begin
            layer_addr_reg <= layer_addr_reg;
            tree_addr_reg <= tree_addr_reg;
            leaf_idx_reg <= leaf_idx_reg;
            HT_layer_flag <= HT_layer_flag;
        end
    end
end
`endif

`ifdef PARAM_256
reg [2-1:0] HT_layer_flag;
//In HT, update leaf_idx and tree
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        HT_layer_flag <= 2'd0;
        layer_addr_reg <= 32'd0;
        tree_addr_reg <= 64'd0;
        leaf_idx_reg <= 32'd0;
    end
    else begin
        if(HT_start) begin //HT start
            layer_addr_reg <= 32'd0;
            tree_addr_reg <= tree_addr;
            leaf_idx_reg <= ap_leaf_idx;
        end
        //HyperTree mode
        else if(XMSS_root_flag && data_in_flag0 && mode==2'd0) begin
            if(HT_layer_flag==2'd3) begin
                layer_addr_reg <= layer_addr_reg + 1;
                `ifdef PARAM_256F
                tree_addr_reg <= tree_addr_reg[63:4];
                leaf_idx_reg <= tree_addr_reg[3:0];
                `else //PARAM_256S
                tree_addr_reg <= tree_addr_reg[63:8];
                leaf_idx_reg <= tree_addr_reg[7:0];
                `endif
                HT_layer_flag <= 2'd0;
            end
            else begin
                HT_layer_flag <= HT_layer_flag + 2'd1;
            end
        end
        else begin
            layer_addr_reg <= layer_addr_reg;
            tree_addr_reg <= tree_addr_reg;
            leaf_idx_reg <= leaf_idx_reg;
            HT_layer_flag <= HT_layer_flag;
        end
    end
end
`endif

`ifdef PARAM_128
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        tmp_flag1 <= 1'b0;
        tmp_flag2 <= 1'b0;
    end
    else begin
        if(o_chain_cnt_up) begin
            tmp_flag1 <= 1'b0;
        end
        else if(o_wots_chain_flag1 && WOTS_hash_out_valid2 && mode==2'd0) begin
            if(tmp_flag1) begin
                tmp_flag1 <= 1'b1;
            end
            else begin
                tmp_flag1 <= 1'b1;
            end
        end
        else begin
            tmp_flag1 <= tmp_flag1;
        end

        if(o_chain_cnt_up) begin
            tmp_flag2 <= 1'b0;
        end
        else if(o_wots_chain_flag2 && WOTS_hash_out_valid1 && mode==2'd0) begin
            if(tmp_flag2) begin
                tmp_flag2 <= 1'b1;
            end
            else begin
                tmp_flag2 <= 1'b1;
            end
        end
        else begin
            tmp_flag2 <= tmp_flag2;
        end
    end
end

always@(posedge clk) begin
    if(o_wots_chain_flag1 && WOTS_hash_out_valid2 && mode==2'd0) begin
        if(tmp_flag1) begin
            tmp_reg1_2 <= WOTS_hash_data_out2;
        end
        else begin
            tmp_reg1_1 <= WOTS_hash_data_out2;
        end
    end
    else begin
        tmp_reg1_1 <= tmp_reg1_1;
        tmp_reg1_2 <= tmp_reg1_2;
    end

    if(o_wots_chain_flag2 && WOTS_hash_out_valid1 && mode==2'd0) begin
        if(tmp_flag2) begin
            tmp_reg2_2 <= WOTS_hash_data_out1;
        end
        else begin
            tmp_reg2_1 <= WOTS_hash_data_out1;
        end
    end
    else begin
        tmp_reg2_1 <= tmp_reg2_1;
        tmp_reg2_2 <= tmp_reg2_2;
    end
end
`endif

`ifdef PARAM_192
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        tmp_flag1 <= 2'd0;
        tmp_flag2 <= 2'd0;
    end
    else begin
        if(o_chain_cnt_up) begin
            tmp_flag1 <= 2'd0;
        end
        else if(o_wots_chain_flag1 && WOTS_hash_out_valid2 && mode==2'd0) begin
            if(tmp_flag1==2'd2) begin
                tmp_flag1 <= tmp_flag1;
            end
            else begin
                tmp_flag1 <= tmp_flag1 + 2'd1;
            end
        end
        else begin
            tmp_flag1 <= tmp_flag1;
        end

        if(o_chain_cnt_up) begin
            tmp_flag2 <= 2'd0;
        end
        else if(o_wots_chain_flag2 && WOTS_hash_out_valid1 && mode==2'd0) begin
            if(tmp_flag2==2'd2) begin
                tmp_flag2 <= tmp_flag2;
            end
            else begin
                tmp_flag2 <= tmp_flag2 + 2'd1;
            end
        end
        else begin
            tmp_flag2 <= tmp_flag2;
        end
    end
end

always@(posedge clk) begin
    if(o_wots_chain_flag1 && WOTS_hash_out_valid2 && mode==2'd0) begin
        if(tmp_flag1==2'd2) begin
            tmp_reg1_3 <= WOTS_hash_data_out2;
        end
        else if(tmp_flag1==2'd1) begin
            tmp_reg1_2 <= WOTS_hash_data_out2;
        end
        else begin
            tmp_reg1_1 <= WOTS_hash_data_out2;
        end
    end
    else begin
        tmp_reg1_1 <= tmp_reg1_1;
        tmp_reg1_2 <= tmp_reg1_2;
        tmp_reg1_3 <= tmp_reg1_3;
    end

    if(o_wots_chain_flag2 && WOTS_hash_out_valid1 && mode==2'd0) begin
        if(tmp_flag2==2'd2) begin
            tmp_reg2_3 <= WOTS_hash_data_out1;
        end
        else if(tmp_flag2==2'd1) begin
            tmp_reg2_2 <= WOTS_hash_data_out1;
        end
        else begin
            tmp_reg2_1 <= WOTS_hash_data_out1;
        end
    end
    else begin
        tmp_reg2_1 <= tmp_reg2_1;
        tmp_reg2_2 <= tmp_reg2_2;
        tmp_reg2_3 <= tmp_reg2_3;
    end
end
`endif

`ifdef PARAM_256
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        tmp_flag1 <= 2'd0;
        tmp_flag2 <= 2'd0;
    end
    else begin
        if(o_chain_cnt_up) begin
            tmp_flag1 <= 2'd0;
        end
        else if(o_wots_chain_flag1 && WOTS_hash_out_valid2 && mode==2'd0) begin
            if(tmp_flag1==2'd3) begin
                tmp_flag1 <= tmp_flag1;
            end
            else begin
                tmp_flag1 <= tmp_flag1 + 2'd1;
            end
        end
        else begin
            tmp_flag1 <= tmp_flag1;
        end

        if(o_chain_cnt_up) begin
            tmp_flag2 <= 2'd0;
        end
        else if(o_wots_chain_flag2 && WOTS_hash_out_valid1 && mode==2'd0) begin
            if(tmp_flag2==2'd3) begin
                tmp_flag2 <= tmp_flag2;
            end
            else begin
                tmp_flag2 <= tmp_flag2 + 2'd1;
            end
        end
        else begin
            tmp_flag2 <= tmp_flag2;
        end
    end
end
always@(posedge clk) begin
    if(o_wots_chain_flag1 && WOTS_hash_out_valid2 && mode==2'd0) begin
        if(tmp_flag1==2'd3) begin
            tmp_reg1_4 <= WOTS_hash_data_out2;
        end
        else if(tmp_flag1==2'd2) begin
            tmp_reg1_3 <= WOTS_hash_data_out2;
        end
        else if(tmp_flag1==2'd1) begin
            tmp_reg1_2 <= WOTS_hash_data_out2;
        end
        else begin
            tmp_reg1_1 <= WOTS_hash_data_out2;
        end
    end
    else begin
        tmp_reg1_1 <= tmp_reg1_1;
        tmp_reg1_2 <= tmp_reg1_2;
        tmp_reg1_3 <= tmp_reg1_3;
        tmp_reg1_4 <= tmp_reg1_4;
    end

    if(o_wots_chain_flag2 && WOTS_hash_out_valid1 && mode==2'd0) begin
        if(tmp_flag2==2'd3) begin
            tmp_reg2_4 <= WOTS_hash_data_out1;
        end
        else if(tmp_flag2==2'd2) begin
            tmp_reg2_3 <= WOTS_hash_data_out1;
        end
        else if(tmp_flag2==2'd1) begin
            tmp_reg2_2 <= WOTS_hash_data_out1;
        end
        else begin
            tmp_reg2_1 <= WOTS_hash_data_out1;
        end
    end
    else begin
        tmp_reg2_1 <= tmp_reg2_1;
        tmp_reg2_2 <= tmp_reg2_2;
        tmp_reg2_3 <= tmp_reg2_3;
        tmp_reg2_4 <= tmp_reg2_4;
    end
end
`endif

//address generation for w from chain_lengths
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        w_mem_addr0 <= 7'd0;
        w_mem_addr1 <= 7'd0;        
    end
    else begin
        if(XMSS_FSM_done) begin
            w_mem_addr0 <= 7'd0;
            w_mem_addr1 <= 7'd0;
        end
        //else if(XMSS_start && HT_start) begin
        else if(XMSS_start) begin
            w_mem_addr0 <= 7'd0;
            w_mem_addr1 <= 7'd1;
        end
        else if(o_chain_cnt_up) begin
            if(i_sig_mode==1'b1 && mode==2'd0) begin
                w_mem_addr0 <= w_mem_addr0+7'd1;
                w_mem_addr1 <= w_mem_addr1+7'd1;
            end
            else begin
                w_mem_addr0 <= w_mem_addr0+7'd2;
                w_mem_addr1 <= w_mem_addr1+7'd2;
            end
        end
    end
end

`ifdef PARAM_128
reg tmp_flag0_1;
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        wots_chain_flag_d <= 1'b0;
        wots_chain_done <= 1'b0;
        tmp_flag0_1 <= 1'b0;
        tmp_flag0_2 <= 1'b0;
        tmp_flag0_3 <= 1'b0;
        tmp_flag0 <= 1'b0;
    end
    else begin
        wots_chain_flag_d <= wots_chain_flag_w;
        wots_chain_done <= !wots_chain_flag_w && wots_chain_flag_d;

        if(tmp_flag0_3 && tmp_flag0_2) begin
            tmp_flag0_3 <= 1'b0;
        end
        else if(wots_chain_done) begin
            tmp_flag0_3 <= 1'b1;
        end
        else begin
            tmp_flag0_3 <= tmp_flag0_3;
        end

        if(tmp_flag0_3 && tmp_flag0_2) begin
            tmp_flag0_1 <= 1'b0;
            tmp_flag0_2 <= 1'b0;
            tmp_flag0 <= 1'b1;
        end
        else if(auth_path_flag && WOTS_FSM_start && mode==2'd0) begin
            if((s_in_0_wr_en==1 || s_in_2_wr_en==1)) begin
                if(tmp_flag0_1) begin
                    tmp_flag0_2 <= 1'b1;
                end
                tmp_flag0_1 <= 1'b1;
            end
            else begin
                tmp_flag0_1 <= tmp_flag0_1;
                tmp_flag0_2 <= tmp_flag0_2;
                tmp_flag0 <= tmp_flag0;
            end
        end
        else begin
            tmp_flag0_1 <= tmp_flag0_1;
            tmp_flag0_2 <= tmp_flag0_2;
            tmp_flag0 <= 1'b0;
        end
    end
end
always@(posedge clk) begin
    if(auth_path_flag && WOTS_FSM_start && mode==2'd0) begin
        if((s_in_0_wr_en==1 || s_in_2_wr_en==1) && Left_flag==1) begin
            if(tmp_flag0_1) begin
                tmp_reg0_2 <= s_in_0;
            end
            else begin
                tmp_reg0_1 <= s_in_0;
            end
        end
        else if((s_in_0_wr_en==1 || s_in_2_wr_en==1) && Left_flag==0) begin
            if(tmp_flag0_1) begin
                tmp_reg0_2 <= s_in_1;
            end
            else begin
                tmp_reg0_1 <= s_in_1;
            end
        end
    end
    else begin
        tmp_reg0_1 <= tmp_reg0_1;
        tmp_reg0_2 <= tmp_reg0_2;
    end
end
`endif

`ifdef PARAM_192
reg [2-1:0] tmp_flag0_1;
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        wots_chain_flag_d <= 1'b0;
        wots_chain_done <= 1'b0;        
        tmp_flag0_1 <= 2'd0;
        tmp_flag0_2 <= 1'b0;
        tmp_flag0_3 <= 1'b0;
        tmp_flag0 <= 1'b0;
    end
    else begin
        wots_chain_flag_d <= wots_chain_flag_w;
        wots_chain_done <= !wots_chain_flag_w && wots_chain_flag_d;

        if(tmp_flag0_3 && tmp_flag0_2) begin
            tmp_flag0_3 <= 1'b0;
        end
        else if(wots_chain_done) begin
            tmp_flag0_3 <= 1'b1;
        end
        else begin
            tmp_flag0_3 <= tmp_flag0_3;
        end

        if(tmp_flag0_3 && tmp_flag0_2) begin
            tmp_flag0_1 <= 2'd0;
            tmp_flag0_2 <= 1'b0;
            tmp_flag0 <= 1'b1;
        end
        else if(auth_path_flag && WOTS_FSM_start && mode==2'd0) begin
            if((s_in_0_wr_en==1 || s_in_2_wr_en==1)) begin
                if(tmp_flag0_1==2'd2) begin
                    tmp_flag0_1 <= tmp_flag0_1;
                    tmp_flag0_2 <= 1'b1;
                end
                else begin
                    tmp_flag0_1 <= tmp_flag0_1 + 1'b1;
                end
                
            end
            else begin
                tmp_flag0_1 <= tmp_flag0_1;
                tmp_flag0_2 <= tmp_flag0_2;
                tmp_flag0 <= tmp_flag0;
            end
        end
        else begin
            tmp_flag0_1 <= tmp_flag0_1;
            tmp_flag0_2 <= tmp_flag0_2;
            tmp_flag0 <= 1'b0;
        end
    end
end
always@(posedge clk) begin
    if(auth_path_flag && WOTS_FSM_start && mode==2'd0) begin
        if((s_in_0_wr_en==1 || s_in_2_wr_en==1) && Left_flag==1) begin
            if(tmp_flag0_1==2'd2) begin
                tmp_reg0_3 <= s_in_0;
            end
            else if(tmp_flag0_1==2'd1) begin
                tmp_reg0_2 <= s_in_0;
            end
            else begin
                tmp_reg0_1 <= s_in_0;
            end
        end
        else if((s_in_0_wr_en==1 || s_in_2_wr_en==1) && Left_flag==0) begin
            if(tmp_flag0_1==2'd2) begin
                tmp_reg0_3 <= s_in_1;
            end
            else if(tmp_flag0_1==2'd1) begin
                tmp_reg0_2 <= s_in_1;
            end
            else begin
                tmp_reg0_1 <= s_in_1;
            end
        end
        else begin
            tmp_reg0_1 <= tmp_reg0_1;
            tmp_reg0_2 <= tmp_reg0_2;
            tmp_reg0_3 <= tmp_reg0_3;
        end
    end
    else begin
        tmp_reg0_1 <= tmp_reg0_1;
        tmp_reg0_2 <= tmp_reg0_2;
        tmp_reg0_3 <= tmp_reg0_3;
    end
end
`endif

`ifdef PARAM_256
reg [2-1:0] tmp_flag0_1;
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        wots_chain_flag_d <= 1'b0;
        wots_chain_done <= 1'b0;           
        tmp_flag0_1 <= 2'd0;
        tmp_flag0_2 <= 1'b0;
        tmp_flag0_3 <= 1'b0;
        tmp_flag0 <= 1'b0;
    end
    else begin
        wots_chain_flag_d <= wots_chain_flag_w;
        wots_chain_done <= !wots_chain_flag_w && wots_chain_flag_d;

        if(tmp_flag0_3 && tmp_flag0_2) begin
            tmp_flag0_3 <= 1'b0;
        end
        else if(wots_chain_done) begin
            tmp_flag0_3 <= 1'b1;
        end
        else begin
            tmp_flag0_3 <= tmp_flag0_3;
        end

        if(tmp_flag0_3 && tmp_flag0_2) begin
            tmp_flag0_1 <= 2'd0;
            tmp_flag0_2 <= 1'b0;
            tmp_flag0 <= 1'b1;
        end
        else if(auth_path_flag && WOTS_FSM_start && mode==2'd0) begin
            if((s_in_0_wr_en==1 || s_in_2_wr_en==1)) begin
                if(tmp_flag0_1==2'd3) begin
                    tmp_flag0_1 <= tmp_flag0_1;
                    tmp_flag0_2 <= 1'b1;
                end
                else begin
                    tmp_flag0_1 <= tmp_flag0_1 + 1'b1;
                end
            end
            else begin
                tmp_flag0_1 <= tmp_flag0_1;
                tmp_flag0_2 <= tmp_flag0_2;
                tmp_flag0 <= tmp_flag0;
            end
        end
        else begin
            tmp_flag0_1 <= tmp_flag0_1;
            tmp_flag0_2 <= tmp_flag0_2;
            tmp_flag0 <= 1'b0;
        end
    end
end
always@(posedge clk) begin
    if(auth_path_flag && WOTS_FSM_start && mode==2'd0) begin
        if((s_in_0_wr_en==1 || s_in_2_wr_en==1) && Left_flag==1) begin
            if(tmp_flag0_1==2'd3) begin
                tmp_reg0_4 <= s_in_0;
            end
            else if(tmp_flag0_1==2'd2) begin
                tmp_reg0_3 <= s_in_0;
            end
            else if(tmp_flag0_1==2'd1) begin
                tmp_reg0_2 <= s_in_0;
            end
            else begin
                tmp_reg0_1 <= s_in_0;
            end
        end
        else if((s_in_0_wr_en==1 || s_in_2_wr_en==1) && Left_flag==0) begin
            if(tmp_flag0_1==2'd3) begin
                tmp_reg0_4 <= s_in_1;
            end
            else if(tmp_flag0_1==2'd2) begin
                tmp_reg0_3 <= s_in_1;
            end
            else if(tmp_flag0_1==2'd1) begin
                tmp_reg0_2 <= s_in_1;
            end
            else begin
                tmp_reg0_1 <= s_in_1;
            end
        end
        else begin
            tmp_reg0_1 <= tmp_reg0_1;
            tmp_reg0_2 <= tmp_reg0_2;
            tmp_reg0_3 <= tmp_reg0_3;
            tmp_reg0_4 <= tmp_reg0_4;
        end
    end
    else begin
        tmp_reg0_1 <= tmp_reg0_1;
        tmp_reg0_2 <= tmp_reg0_2;
        tmp_reg0_3 <= tmp_reg0_3;
        tmp_reg0_4 <= tmp_reg0_4;
    end
end
`endif

endmodule
