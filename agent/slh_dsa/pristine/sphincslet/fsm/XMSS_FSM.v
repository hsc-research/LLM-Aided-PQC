
module XMSS_FSM
#(
parameter IO_WIDTH = 64,
parameter parameter_set = "128s",
parameter WD = //address bit for max data length
                    (parameter_set == "128s") ? 7:
                    (parameter_set == "128f") ? 7:
                    (parameter_set == "192s") ? 8:
                    (parameter_set == "192f") ? 8:
                    (parameter_set == "256s") ? 9:
                    (parameter_set == "256f") ? 9: 9,
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
                    (parameter_set == "256f") ? 256: 128,
parameter CH_len = 
                    (parameter_set == "128s") ? 2:
                    (parameter_set == "128f") ? 2:
                    (parameter_set == "192s") ? 4:
                    (parameter_set == "192f") ? 4:
                    (parameter_set == "256s") ? 6:
                    (parameter_set == "256f") ? 6: 6,
parameter SD_len = 
                    (parameter_set == "128s") ? 2:
                    (parameter_set == "128f") ? 2:
                    (parameter_set == "192s") ? 3:
                    (parameter_set == "192f") ? 3:
                    (parameter_set == "256s") ? 4:
                    (parameter_set == "256f") ? 4: 2,
parameter T_CNT = 
                    (parameter_set == "128s") ? 14:
                    (parameter_set == "128f") ? 33:
                    (parameter_set == "192s") ? 17:
                    (parameter_set == "192f") ? 33:
                    (parameter_set == "256s") ? 22:
                    (parameter_set == "256f") ? 35: 14,
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
input  wire                     FSM_start_in,
output wire                     FSM_start_out,
input  wire [SEED_num-1:0]      PK_seed,
input  wire [ 8  -1:0]          layer_addr,
input  wire [32*2-1:0]          tree_addr,
input  wire [LEAF_WD      -1:0] ap_leaf_idx,
input  wire [INDICE_WD    -1:0] leaf_idx,
input  wire [XMSS_H_param -1:0] XMSS_tree_height,
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
input  wire [IO_WIDTH     -1:0] s_out_0,
input  wire [IO_WIDTH     -1:0] s_out_2,
output reg  [XMSS_WD      -1:0] s_in_0_addr,
output wire [XMSS_WD      -1:0] s_in_1_addr,
input wire                      fsm_data_in_flag0,
output wire                     data_in_flag0,
output reg                      leaf_node_gen_start,
input  wire                     leaf_node_gen_done,
input  wire                     i_sig_mode,
input  wire                     HT_mode,
`ifdef SHA2
input  wire                     i_mode_flag,
`endif
output wire                     o_sig_read_mem,
input  wire [64-1:0]            i_sig_mem_out,
output  reg                     flag_last,
output wire                     tree_done,
output  reg                     auth_path_flag,
output  reg                     wots_chain_flag,
output  reg                     Left_flag
); 

reg  [IO_WIDTH-1:0]      out_data1;
reg  [IO_WIDTH-1:0]      out_data2;
`ifdef SHA2
reg  [IO_WIDTH-1:0]      tmp_reg_0;
reg  [IO_WIDTH-1:0]      tmp_reg_1;
`endif
reg  [WD      -1:0]      out_addr;
reg  [ 3-1:0]            opcode;
reg  [ 4-1:0]            cnt;
wire [XMSS_H_param -1:0] HC;//height count
reg                      out_valid;
reg                      hash_start;
reg                      hash_start_1d;
reg                      hash_start_2d;
reg                      XMSS_start;
reg                      XMSS_done;
reg                      XMSS_tree_done;
wire                     hash_done_1d;
reg                      flag1;
reg  [4-1:0]             ch_cnt;
reg                      o_sig_read_mem_r;
reg  [INDICE_WD  -1:0]   LR_flag2_sr;
wire                     LR_flag2;
reg  [2-1:0]             o_sig_read_mem_r_d;
wire                     o_sig_read_mem_r2;
reg  [INDICE_WD  -1:0]   target_idx;
reg  [INDICE_WD  -1:0]   h1_target_idx;
reg                      LR_flag;
reg                      h0_LR_flag;
wire [INDICE_WD  -1:0]   target_idx_w;
wire [32-1:0]            target_idx_32_w;
reg  [15-1:0]            leaf_node_cnt;
wire [15-1:0]            pre_ncnt;
wire [14-1:0]            ncnt;
reg  [ 5-1:0]            h_cnt;
reg  [ 5-1:0]            h_cnt2;
reg  [ 6-1:0]            tree_cnt;
reg  [ 5-1:0]            state1;

`ifdef PARAM_128F
reg  [ 3-1:0]            tree_h;//6: 3bit
reg  [19-7-1:0]          tree_i;
reg  [19-7-1:0]          tree_i0;
reg  [14-8-1:0]          tree_i5;//33: 6bit
wire [32-1:0] tree_h_w;
wire [32-1:0] tree_i_w;
assign tree_h_w = tree_h;
assign tree_i_w = tree_i;
`endif
`ifdef PARAM_192F
reg  [ 4-1:0]            tree_h;//8: 4bit
reg  [19-5-1:0]          tree_i;
reg  [19-5-1:0]          tree_i0;
reg  [12-6-1:0]          tree_i7;//33: 6bit
wire [32-1:0] tree_h_w;
wire [32-1:0] tree_i_w;
assign tree_h_w = tree_h;
assign tree_i_w = tree_i;
`endif
`ifdef PARAM_256F
reg  [ 4-1:0]            tree_h;//9: 4bit
reg  [19-4-1:0]          tree_i;
reg  [19-4-1:0]          tree_i0;
reg  [11-5-1:0]          tree_i8;//35: 6bit
wire [32-1:0] tree_h_w;
wire [32-1:0] tree_i_w;
assign tree_h_w = tree_h;
assign tree_i_w = tree_i;
`endif
`ifdef PARAM_128S
reg  [ 4-1:0]            tree_h;//12: 4bit
reg  [19-3-1:0]          tree_i;
reg  [19-3-1:0]          tree_i0;
reg  [ 8-4-1:0]          tree_i11;//14: 4bit
wire [32-1:0] tree_h_w;
wire [32-1:0] tree_i_w;
assign tree_h_w = tree_h;
assign tree_i_w = tree_i;
`endif
`ifdef PARAM_192S
reg  [ 4-1:0]            tree_h;//14: 4bit
reg  [19-0-1:0]          tree_i;
reg  [19-0-1:0]          tree_i0;
reg  [ 6-1-1:0]          tree_i13;//17: 5bit
wire [32-1:0] tree_h_w;
wire [32-1:0] tree_i_w;
assign tree_h_w = tree_h;
assign tree_i_w = tree_i;
`endif
`ifdef PARAM_256S
reg  [ 4-1:0]            tree_h;//14: 4bit
reg  [19-0-1:0]          tree_i;
reg  [19-0-1:0]          tree_i0;
reg  [ 6-1-1:0]          tree_i13;//22: 5bit
wire [32-1:0] tree_h_w;
wire [32-1:0] tree_i_w;
assign tree_h_w = tree_h;
assign tree_i_w = tree_i;
`endif

wire                     h_con1;
wire                     h_con3;
wire [32-1:0]            ap_leaf_idx_w;

assign ap_leaf_idx_w     = ap_leaf_idx;
assign HC                = XMSS_tree_height;
assign o_sig_read_mem    = o_sig_read_mem_r;
assign LR_flag2          = LR_flag2_sr[0];
assign LR_flag2_pre      = LR_flag2_sr[1];
assign o_sig_read_mem_r2 = o_sig_read_mem_r_d[0];

assign target_idx_w    = LR_flag ? target_idx - 1 : target_idx + 1;
assign target_idx_32_w = target_idx;

assign hash_done_1d = i_hash_done;
assign tree_done    = XMSS_tree_done;

assign FSM_start_out = XMSS_start;

`ifdef PARAM_128
assign s_in_1_addr = s_in_0_addr + 10'd2;
`endif
`ifdef PARAM_192
assign s_in_1_addr = s_in_0_addr + 10'd3;
`endif
`ifdef PARAM_256
assign s_in_1_addr = s_in_0_addr + 10'd4;
`endif

assign o_s_data_in = out_data1;
assign o_s_wr_en   = out_valid;
assign o_s_addr    = out_addr;
assign o_b_data_in = out_data2;
assign o_b_wr_en   = out_valid;
assign o_b_addr    = out_addr;
assign o_hash_start = 1 ? hash_start_2d : hash_start;
assign o_opcode     = opcode;
assign o_XMSS_done  = XMSS_done;
assign pre_ncnt     = leaf_node_cnt + 1;
assign ncnt         = pre_ncnt[14:2];
assign h_con1       = h_cnt == h_cnt2 ? 1 : 0;
assign h_con3       = h_cnt < h_cnt2 ? 1 : 0;

always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        XMSS_start          <= 1'b0;
        XMSS_done           <= 1'b0;
        XMSS_tree_done      <= 1'b0;
        leaf_node_cnt       <= 14'd0;
        leaf_node_gen_start <= 1'b0;
        opcode              <= 3'd0;
        h_cnt2              <= 5'd0;
        state1              <= 5'd0;
        `ifdef PARAM_128F
        tree_h              <= 32'd0;
        tree_i              <= 32'd0;
        tree_i0             <= 19'd0;
        tree_i5             <= 14'd0;
        `endif
        `ifdef PARAM_192F
        tree_h              <= 32'd0;
        tree_i              <= 32'd0;
        tree_i0             <= 19'd0;
        tree_i7             <= 12'd0;
        `endif
        `ifdef PARAM_256F
        tree_h              <= 32'd0;
        tree_i              <= 32'd0;
        tree_i0             <= 19'd0;
        tree_i8             <= 11'd0;
        `endif   
        `ifdef PARAM_128S
        tree_h              <= 32'd0;
        tree_i              <= 32'd0;
        tree_i0             <= 19'd0;
        tree_i11            <= 8'd0;        
        `endif
        `ifdef PARAM_192S
        tree_h              <= 32'd0;
        tree_i              <= 32'd0;
        tree_i0             <= 19'd0;
        tree_i13            <= 6'd0;
        `endif
        `ifdef PARAM_256S
        tree_h              <= 32'd0;
        tree_i              <= 32'd0;
        tree_i0             <= 19'd0;     
        tree_i13            <= 6'd0;
        `endif

        flag_last           <= 1'b0;
        tree_cnt            <= 6'd0;
    end
    else begin
        case(state1)
        5'd0: begin //idle, start
            if(FSM_start_in || XMSS_tree_done) begin
                state1 <= 5'd1;
                XMSS_start <= 1'b0;
                XMSS_tree_done <= 1'b0;
                
                if(i_sig_mode==1'b0) begin
                    leaf_node_cnt <= 14'd0;
                    leaf_node_gen_start <= 1'b1;
                end
                else begin
                    leaf_node_cnt <= 14'd3;
                    leaf_node_gen_start <= 1'b1;
                end
                h_cnt2 <= 5'd1;
            end
        end
        5'd1: begin //generate 4 leaf nodes
            if(leaf_node_gen_done) begin
                if(leaf_node_cnt[1:0]==2'b11) begin    
                    //jump state of height 0
                    state1 <= 5'd2;
                    //stop leaf gen
                    leaf_node_cnt <= leaf_node_cnt;
                    leaf_node_gen_start <= 1'b0;
                    //start H in height 0
                    XMSS_start <= 1'b1;
                    hash_start <= 1'b1;
                    opcode <= 3'd2;
                    tree_h <= 32'd1; //start from '1'
                    tree_i <= tree_i0;
                    h_cnt2 <= 5'd1;
                end
                else begin
                    if(!HT_mode) begin
                        leaf_node_cnt <= leaf_node_cnt + 1;
                        leaf_node_gen_start <= 1'b1;
                    end
                    else begin
                        leaf_node_cnt <= leaf_node_cnt + 3;
                        leaf_node_gen_start <= 1'b1;
                    end
                end
            end
            else begin
                leaf_node_gen_start <= 1'b0;
            end
        end
        5'd2: begin //compute H
            `ifdef SHAKE
            if(cnt == 4'd10 && hash_done_1d) 
            `else
            if(cnt == 4'd9 && hash_done_1d) 
            `endif
            begin
                if((h_cnt==h_cnt2 && h_cnt!=HC-1) && i_sig_mode==1'b0) begin
                    XMSS_start <= 1'b0;
                    hash_start <= 1'b0;                    
                    state1 <= 5'd1; //gen leaf nodes   
                    tree_i0 <= tree_i0 + 14'd2;//     
                    leaf_node_cnt <= leaf_node_cnt + 1;
                    leaf_node_gen_start <= 1'b1;
                end
                else begin
                    if((h_cnt==HC-1 && h_cnt2==HC-1) || (h_cnt2==(HC-1) && i_sig_mode==1'b1)) begin
                        state1 <= 5'd3; //done
                        tree_i0 <= tree_i0 + 14'd2;//
                        flag_last <= 1'b1;
                    end
                    else begin
                        state1 <= 5'd2; //start H again
                        flag_last <= flag_last;
                    end
                    XMSS_start <= 1'b1;
                    hash_start <= 1'b1;
                    h_cnt2 <= h_cnt2 + 1;
                    tree_h <= h_cnt2 + 1;
                    case(h_cnt2)
                    `ifdef PARAM_128F
                        5'd1:  begin tree_i <= {tree_i0>>2,1'b0};  end
                        5'd2:  begin tree_i <= {tree_i0>>3,1'b0};  end
                        5'd3:  begin tree_i <= {tree_i0>>4,1'b0};  end
                        5'd4:  begin tree_i <= {tree_i0>>5,1'b0};  end
                        5'd5:  begin tree_i <= tree_i5;  tree_i5  <= tree_i5  + 14'd2; end
                    `endif
                    `ifdef PARAM_192F
                        5'd1:  begin tree_i <= {tree_i0>>2,1'b0};  end
                        5'd2:  begin tree_i <= {tree_i0>>3,1'b0};  end
                        5'd3:  begin tree_i <= {tree_i0>>4,1'b0};  end
                        5'd4:  begin tree_i <= {tree_i0>>5,1'b0};  end
                        5'd5:  begin tree_i <= {tree_i0>>6,1'b0};  end
                        5'd6:  begin tree_i <= {tree_i0>>7,1'b0};  end
                        5'd7:  begin tree_i <= tree_i7;  tree_i7  <= tree_i7  + 12'd2; end
                    `endif     
                    `ifdef PARAM_256F
                        5'd1:  begin tree_i <= {tree_i0>>2,1'b0};  end
                        5'd2:  begin tree_i <= {tree_i0>>3,1'b0};  end
                        5'd3:  begin tree_i <= {tree_i0>>4,1'b0};  end
                        5'd4:  begin tree_i <= {tree_i0>>5,1'b0};  end
                        5'd5:  begin tree_i <= {tree_i0>>6,1'b0};  end
                        5'd6:  begin tree_i <= {tree_i0>>7,1'b0};  end
                        5'd7:  begin tree_i <= {tree_i0>>8,1'b0};  end
                        5'd8:  begin tree_i <= tree_i8;  tree_i8  <= tree_i8  + 11'd2; end
                    `endif          
                    `ifdef PARAM_128S
                        5'd1:  begin tree_i <= {tree_i0>>2,1'b0};  end
                        5'd2:  begin tree_i <= {tree_i0>>3,1'b0};  end
                        5'd3:  begin tree_i <= {tree_i0>>4,1'b0};  end
                        5'd4:  begin tree_i <= {tree_i0>>5,1'b0};  end
                        5'd5:  begin tree_i <= {tree_i0>>6,1'b0};  end
                        5'd6:  begin tree_i <= {tree_i0>>7,1'b0};  end
                        5'd7:  begin tree_i <= {tree_i0>>8,1'b0};  end
                        5'd8:  begin tree_i <= {tree_i0>>9,1'b0};  end
                        5'd9:  begin tree_i <= {tree_i0>>10,1'b0};  end
                        5'd10: begin tree_i <= {tree_i0>>11,1'b0};  end
                        5'd11: begin tree_i <= tree_i11; tree_i11 <= tree_i11 +  8'd2; end
                    `endif         
                    `ifdef PARAM_192S
                        5'd1:  begin tree_i <= {tree_i0>>2,1'b0};  end
                        5'd2:  begin tree_i <= {tree_i0>>3,1'b0};  end
                        5'd3:  begin tree_i <= {tree_i0>>4,1'b0};  end
                        5'd4:  begin tree_i <= {tree_i0>>5,1'b0};  end
                        5'd5:  begin tree_i <= {tree_i0>>6,1'b0};  end
                        5'd6:  begin tree_i <= {tree_i0>>7,1'b0};  end
                        5'd7:  begin tree_i <= {tree_i0>>8,1'b0};  end
                        5'd8:  begin tree_i <= {tree_i0>>9,1'b0};  end
                        5'd9:  begin tree_i <= {tree_i0>>10,1'b0};  end
                        5'd10: begin tree_i <= {tree_i0>>11,1'b0};  end
                        5'd11: begin tree_i <= {tree_i0>>12,1'b0};  end
                        5'd12: begin tree_i <= {tree_i0>>13,1'b0};  end
                        5'd13: begin tree_i <= tree_i13; tree_i13 <= tree_i13 +  6'd2; end
                    `endif
                    `ifdef PARAM_256S
                        5'd1:  begin tree_i <= {tree_i0>>2,1'b0};  end
                        5'd2:  begin tree_i <= {tree_i0>>3,1'b0};  end
                        5'd3:  begin tree_i <= {tree_i0>>4,1'b0};  end
                        5'd4:  begin tree_i <= {tree_i0>>5,1'b0};  end
                        5'd5:  begin tree_i <= {tree_i0>>6,1'b0};  end
                        5'd6:  begin tree_i <= {tree_i0>>7,1'b0};  end
                        5'd7:  begin tree_i <= {tree_i0>>8,1'b0};  end
                        5'd8:  begin tree_i <= {tree_i0>>9,1'b0};  end
                        5'd9:  begin tree_i <= {tree_i0>>10,1'b0};  end
                        5'd10: begin tree_i <= {tree_i0>>11,1'b0};  end
                        5'd11: begin tree_i <= {tree_i0>>12,1'b0};  end
                        5'd12: begin tree_i <= {tree_i0>>13,1'b0};  end
                        5'd13: begin tree_i <= tree_i13; tree_i13 <= tree_i13 +  6'd2; end
                    `endif                                                                
                        default: begin
                        `ifdef PARAM_128F
                            tree_i   <= tree_i;
                            tree_i5  <= tree_i5;
                        `endif
                        `ifdef PARAM_192F
                            tree_i   <= tree_i;
                            tree_i7  <= tree_i7;
                        `endif
                        `ifdef PARAM_256F
                            tree_i   <= tree_i;
                            tree_i8  <= tree_i8;
                        `endif      
                        `ifdef PARAM_128S
                            tree_i   <= tree_i;
                            tree_i11 <= tree_i11;
                        `endif                 
                        `ifdef PARAM_192S
                            tree_i   <= tree_i;
                            tree_i13 <= tree_i13;
                        `endif                 
                        `ifdef PARAM_256S
                            tree_i   <= tree_i;
                            tree_i13 <= tree_i13;
                        `endif
                        end
                    endcase
                end
            end
            else begin
                XMSS_start <= XMSS_start;
                hash_start <= 1'b0;
            end
        end
        5'd3: begin //compute H
            `ifdef SHAKE
            if(cnt == 4'd10 && hash_done_1d)
            `else
            if(cnt == 4'd9 && hash_done_1d)
            `endif
            begin
                XMSS_start <= 1'b0;
                hash_start <= 1'b0;    
                flag_last <= 1'b0;                
                state1 <= 5'd31; //done
            end             
            else begin
                XMSS_start <= XMSS_start;
                hash_start <= 1'b0;
            end
        end
        5'd31: begin //done
            if(XMSS_done) begin
                state1 <= 5'd0;
                XMSS_start <= 1'b0;
                hash_start <= 1'b0;
                XMSS_done <= 1'b0;
                XMSS_tree_done <= 1'b0;
                // reset to zero
                `ifdef PARAM_128F
                tree_h <= 32'd0;
                tree_i <= 32'd0;
                tree_i0 <= 19'd0;
                tree_i5 <= 14'd0;
                `endif
                `ifdef PARAM_192F
                tree_h <= 32'd0;
                tree_i <= 32'd0;
                tree_i0 <= 19'd0;
                tree_i7 <= 12'd0;
                `endif
                `ifdef PARAM_256F
                tree_h <= 32'd0;
                tree_i <= 32'd0;
                tree_i0 <= 19'd0;
                tree_i8 <= 11'd0;
                `endif  
                `ifdef PARAM_128S
                tree_h <= 32'd0;
                tree_i <= 32'd0;
                tree_i0 <= 19'd0;
                tree_i11 <= 8'd0;
                `endif           
                `ifdef PARAM_192S
                tree_h <= 32'd0;
                tree_i <= 32'd0;
                tree_i0 <= 19'd0;
                tree_i13 <= 6'd0;
                `endif           
                `ifdef PARAM_256S
                tree_h <= 32'd0;
                tree_i <= 32'd0;
                tree_i0 <= 19'd0;
                tree_i13 <= 6'd0;
                `endif
            end
            else if(XMSS_tree_done) begin
                state1 <= 5'd0;
                XMSS_start <= 1'b0;
                hash_start <= 1'b0;
                XMSS_done <= 1'b0;
                // reset to zero
                tree_h <= 32'd0;
                tree_i <= 32'd0;
                case(HC-1)
                `ifdef PARAM_128F
                    5'd5:  begin tree_i5  <= tree_i5  - 1; end//6
                `endif
                `ifdef PARAM_192F
                    5'd7:  begin tree_i7  <= tree_i7  - 1; end//8
                `endif
                `ifdef PARAM_256F
                    5'd8:  begin tree_i8  <= tree_i8  - 1; end//9
                `endif
                `ifdef PARAM_128S
                    5'd11: begin tree_i11 <= tree_i11 - 1; end//12
                `endif
                `ifdef PARAM_192S
                    5'd13: begin tree_i13 <= tree_i13 - 1; end//14
                `endif
                `ifdef PARAM_256S
                    5'd13: begin tree_i13 <= tree_i13 - 1; end//14
                `endif
                    default: begin 
                        `ifdef PARAM_128F
                        tree_i5 <= tree_i5;
                        `endif
                        `ifdef PARAM_192F
                        tree_i7 <= tree_i7;
                        `endif
                        `ifdef PARAM_256F
                        tree_i8 <= tree_i8;
                        `endif
                        `ifdef PARAM_128S
                        tree_i11 <= tree_i11;
                        `endif
                        `ifdef PARAM_192S
                        tree_i13 <= tree_i13;
                        `endif
                        `ifdef PARAM_256S
                        tree_i13 <= tree_i13;
                        `endif
                    end
                endcase
            end
            else begin
                if((tree_cnt==(T_CNT-1) && HT_mode) || !HT_mode) begin
                    XMSS_done <= 1'b1;
                    XMSS_tree_done <= 1'b0;
                    tree_cnt <= 0;
                end
                else begin
                    XMSS_done <= 1'b0;
                    XMSS_tree_done <= 1'b1;
                    tree_cnt <= tree_cnt + 1;
                end
            end
        end
        endcase
    end
end


always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        hash_start_1d <= 1'b0;
        hash_start_2d <= 1'b0;
    end
    else begin
        hash_start_1d <= hash_start;
        hash_start_2d <= hash_start_1d;
    end
end

//Checking auth_path nodes
always@(h_cnt2) begin
    case(h_cnt2)
        5'd1: begin
            target_idx <= (leaf_idx>>1);
            LR_flag <= leaf_idx[1];
        end
        5'd2: begin
            target_idx <= (leaf_idx>>2);
            LR_flag <= leaf_idx[2];
        end
        5'd3: begin
            target_idx <= (leaf_idx>>3);
            LR_flag <= leaf_idx[3];
        end
        5'd4: begin
            target_idx <= (leaf_idx>>4);
            LR_flag <= leaf_idx[4];
        end
        5'd5: begin
            target_idx <= (leaf_idx>>5);
            LR_flag <= leaf_idx[5];
        end
        5'd6: begin
            target_idx <= (leaf_idx>>6);
            LR_flag <= leaf_idx[6];
        end     

        `ifdef PARAM_192F
        5'd7: begin
            target_idx <= (leaf_idx>>7);
            LR_flag <= leaf_idx[7];
        end
        5'd8: begin
            target_idx <= (leaf_idx>>8);
            LR_flag <= leaf_idx[8];
        end
        `endif            

        `ifdef PARAM_256F
        5'd7: begin
            target_idx <= (leaf_idx>>7);
            LR_flag <= leaf_idx[7];
        end
        5'd8: begin
            target_idx <= (leaf_idx>>8);
            LR_flag <= leaf_idx[8];
        end
        5'd9: begin
            target_idx <= (leaf_idx>>9);
            LR_flag <= leaf_idx[9];
        end
        `endif

        `ifdef PARAM_128S
        5'd7: begin
            target_idx <= (leaf_idx>>7);
            LR_flag <= leaf_idx[7];
        end
        5'd8: begin
            target_idx <= (leaf_idx>>8);
            LR_flag <= leaf_idx[8];
        end            
        5'd9: begin
            target_idx <= (leaf_idx>>9);
            LR_flag <= leaf_idx[9];
        end
        5'd10: begin
            target_idx <= (leaf_idx>>10);
            LR_flag <= leaf_idx[10];
        end
        5'd11: begin
            target_idx <= (leaf_idx>>11);
            LR_flag <= leaf_idx[11];
        end
        5'd12: begin
            target_idx <= (leaf_idx>>12);
            LR_flag <= leaf_idx[12];
        end
        `endif

        `ifdef PARAM_192S
        5'd7: begin
            target_idx <= (leaf_idx>>7);
            LR_flag <= leaf_idx[7];
        end
        5'd8: begin
            target_idx <= (leaf_idx>>8);
            LR_flag <= leaf_idx[8];
        end            
        5'd9: begin
            target_idx <= (leaf_idx>>9);
            LR_flag <= leaf_idx[9];
        end
        5'd10: begin
            target_idx <= (leaf_idx>>10);
            LR_flag <= leaf_idx[10];
        end
        5'd11: begin
            target_idx <= (leaf_idx>>11);
            LR_flag <= leaf_idx[11];
        end
        5'd12: begin
            target_idx <= (leaf_idx>>12);
            LR_flag <= leaf_idx[12];
        end
        5'd13: begin
            target_idx <= (leaf_idx>>13);
            LR_flag <= leaf_idx[13];
        end
        5'd14: begin
            target_idx <= (leaf_idx>>14);
            LR_flag <= leaf_idx[14];
        end
        `endif

        `ifdef PARAM_256S
        5'd7: begin
            target_idx <= (leaf_idx>>7);
            LR_flag <= leaf_idx[7];
        end
        5'd8: begin
            target_idx <= (leaf_idx>>8);
            LR_flag <= leaf_idx[8];
        end            
        5'd9: begin
            target_idx <= (leaf_idx>>9);
            LR_flag <= leaf_idx[9];
        end
        5'd10: begin
            target_idx <= (leaf_idx>>10);
            LR_flag <= leaf_idx[10];
        end
        5'd11: begin
            target_idx <= (leaf_idx>>11);
            LR_flag <= leaf_idx[11];
        end
        5'd12: begin
            target_idx <= (leaf_idx>>12);
            LR_flag <= leaf_idx[12];
        end
        5'd13: begin
            target_idx <= (leaf_idx>>13);
            LR_flag <= leaf_idx[13];
        end
        5'd14: begin
            target_idx <= (leaf_idx>>14);
            LR_flag <= leaf_idx[14];
        end
        `endif
        default: begin
            target_idx <= 0;
            LR_flag <= 0;
        end
    endcase
end

always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        wots_chain_flag <= 1'b0;
        auth_path_flag <= 1'b0;
        Left_flag <= 1'b0;
        h1_target_idx <= 15'd0;
        h0_LR_flag <= 1'b0;
    end
    else begin

        h1_target_idx <= (leaf_idx>>1);
        h0_LR_flag <= leaf_idx[0];

        if(FSM_start_in) begin
            auth_path_flag <= 1'b0;
            Left_flag <= 1'b0;
            wots_chain_flag <= wots_chain_flag;
        end
        else if(FSM_start_out) begin //For XMSS output checking
            if((tree_i_w[INDICE_WD-1:1]==target_idx_w[INDICE_WD-1:1])) begin            
                if(!LR_flag) begin //Right child node (s)
                    auth_path_flag <= 1'b1;
                    Left_flag <= 1'b0;
                end
                else begin //Left child node (b)
                    auth_path_flag <= 1'b1;
                    Left_flag <= 1'b1;
                end                
            end
            else begin
                auth_path_flag <= 1'b0;
                Left_flag <= 1'b0;
            end
            wots_chain_flag <= wots_chain_flag;
        end
        else begin //For child node checking

            //FORS tree mode
            if((tree_i0[INDICE_WD-1:1]==h1_target_idx[INDICE_WD-1:1]) && HT_mode==1) begin
                if((tree_i0[0]==h1_target_idx[0]) && !leaf_node_cnt[0]) begin //Left child node
                    auth_path_flag <= 1'b1;
                    Left_flag <= h0_LR_flag;
                end
                else if((tree_i0[0]!=h1_target_idx[0]) && leaf_node_cnt[0]) begin //Right child node
                    auth_path_flag <= 1'b1;
                    Left_flag <= h0_LR_flag;
                end
                else begin
                    auth_path_flag <= 1'b0;
                    Left_flag <= 1'b0;
                end
                wots_chain_flag <= wots_chain_flag;
            end
            //HyperTree mode
            else if(HT_mode==0) begin
                if((leaf_idx)==leaf_node_cnt) begin
                    wots_chain_flag <= 1'b1;
                end
                else if(i_sig_mode==1'b1) begin
                    wots_chain_flag <= 1'b1;
                end
                else begin
                    wots_chain_flag <= 1'b0;
                end

                if((leaf_idx[0]==0) && ((leaf_idx+1)==leaf_node_cnt)) begin //Left child node
                    auth_path_flag <= 1'b1;
                    Left_flag <= 1'b1;
                end
                else if((leaf_idx[0]==1) && ((leaf_idx-1)==leaf_node_cnt)) begin //Right child node
                    auth_path_flag <= 1'b1;
                    Left_flag <= 1'b1;
                end
                else begin
                    auth_path_flag <= 1'b0;
                    Left_flag <= 1'b0;
                end
            end
            else begin
                wots_chain_flag <= 1'b0;
                auth_path_flag <= 1'b0;
                Left_flag <= 1'b0;
            end
        end
    end
end


`ifdef SHAKE
////----SHAKE----////
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        out_data1    <= 64'd0;
        out_data2    <= 64'd0;
        cnt          <= 4'd0;
        ch_cnt       <= 8'd0;
        out_valid    <= 1'b0;
        out_addr     <= 8'd0-1;
        s_in_0_addr  <= 10'd0;
    end
    else begin
        if(XMSS_start) begin
            case(cnt)
            4'd0: begin//seed 64 bits
                out_data1 <= PK_seed[64*(SD_len+0)-1:64*(SD_len-1)];
                out_data2 <= PK_seed[64*(SD_len+0)-1:64*(SD_len-1)];
                cnt <= cnt + 1;
                ch_cnt <= 8'd1;
                out_valid <= 1'b1;           
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            `ifdef PARAM_128
            4'd1: begin//seed 128 bits //SD_len=2
                out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                cnt <= 4'd4;           
                ch_cnt <= ch_cnt;  
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            `endif
            `ifdef PARAM_192
            4'd1: begin//seed 192 bits //SD_len=3
                out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;    
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end            
            4'd2: begin//seed 192 bits //SD_len=3
                out_data1 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
                out_data2 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
                cnt <= 4'd4;         
                ch_cnt <= ch_cnt;      
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            `endif
            `ifdef PARAM_256
            4'd1: begin//seed 256 bits //SD_len=4
                out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;    
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end             
            4'd2: begin//seed 256 bits //SD_len=4
                out_data1 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
                out_data2 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;       
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end            
            4'd3: begin//seed 256 bits //SD_len=4
                out_data1 <= PK_seed[64*(SD_len-3)-1:64*(SD_len-4)];
                out_data2 <= PK_seed[64*(SD_len-3)-1:64*(SD_len-4)];
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;            
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            `endif
            4'd4: begin
                out_data1 <= {24'd0,layer_addr[8-1:0],32'd0};
                out_data2 <= {24'd0,layer_addr[8-1:0],32'd0};
                out_valid <= 1'b1;
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            4'd5: begin
                out_data1 <= tree_addr;
                out_data2 <= tree_addr;
                out_valid <= 1'b1;
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            4'd6: begin
                //HT_mode 0: HyperTree mode, H type=2
                //HT_mode 1: FORS Tree mode, H type=3
                if(!HT_mode) begin
                    out_data1 <= {24'd0,8'd2,32'd0};
                    out_data2 <= {24'd0,8'd2,32'd0};
                end
                else begin
                    out_data1 <= {24'd0,8'd3,ap_leaf_idx_w};
                    out_data2 <= {24'd0,8'd3,ap_leaf_idx_w};
                end
                out_valid <= 1'b1;
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            4'd7: begin
                if(i_sig_mode==1'b0) begin
                    out_data1 <= {tree_h_w,tree_i_w};
                    out_data2 <= {tree_h_w,(tree_i_w+1'b1)};
                end
                else begin
                    out_data1 <= {tree_h_w,target_idx_32_w};
                    out_data2 <= {tree_h_w,target_idx_32_w};
                end
                out_valid <= 1'b1;
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr + 1'b1;
            end
            4'd8: begin//
                if(o_sig_read_mem_r2 && i_sig_mode==1'b1) begin
                    out_data1 <= i_sig_mem_out;//child_node_data
                    out_data2 <= i_sig_mem_out;//child_node_data
                end
                else if(i_sig_mode==1'b1) begin
                    out_data1 <= s_out_0;//child_node_data
                    out_data2 <= s_out_0;//child_node_data
                end
                else begin
                    out_data1 <= s_out_0;//child_node_data
                    out_data2 <= s_out_2;//child_node_data
                end
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
				if(ch_cnt == ((CH_len)+1)) begin
                    cnt <= cnt + 1;
                    ch_cnt <= 8'd1;
                    s_in_0_addr <= s_in_0_addr;
                end
                else begin
                    cnt <= cnt;
                    ch_cnt <= ch_cnt + 1'b1;
                    s_in_0_addr <= s_in_0_addr + 1'b1;
                end
            end
            4'd9: begin//
                if(o_sig_read_mem_r2 && i_sig_mode==1'b1) begin
                    out_data1 <= i_sig_mem_out;//child_node_data
                    out_data2 <= i_sig_mem_out;//child_node_data
                end
                else if(i_sig_mode==1'b1) begin
                    out_data1 <= s_out_0;//child_node_data
                    out_data2 <= s_out_0;//child_node_data
                end
                else begin
                    out_data1 <= s_out_0;//child_node_data
                    out_data2 <= s_out_2;//child_node_data
                end
                out_valid <= 1'b1;
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr + 1'b1;
            end
            4'd10: begin//cnt 10: wait state
                out_data1 <= 32'd0;
                out_data2 <= 32'd0;
                out_valid <= 1'b0;
                ch_cnt <= ch_cnt;

                if(hash_done_1d) begin
                    `ifdef PARAM_128
                    s_in_0_addr <= s_in_0_addr - 10'd1;
                    out_addr <= 8'd4;
                    `endif
                    `ifdef PARAM_192
                    s_in_0_addr <= s_in_0_addr - 10'd2;
                    out_addr <= 8'd5;
                    `endif
                    `ifdef PARAM_256
                    s_in_0_addr <= s_in_0_addr - 10'd3;
                    out_addr <= 8'd6;
                    `endif 
                    cnt <= 4'd7;
                end
                else if(fsm_data_in_flag0) begin 
                    s_in_0_addr <= s_in_0_addr + 1'b1;
                end
                else begin
                    s_in_0_addr <= s_in_0_addr;
                    out_addr <= out_addr;
                    cnt <= cnt;
                end
            end            
            default: begin
                out_data1 <= 64'd0;
                out_data2 <= 64'd0;
                out_valid <= 1'b0;
                s_in_0_addr <= s_in_0_addr;
                out_addr <= out_addr;
                cnt <= cnt;
                ch_cnt <= ch_cnt;
            end
            endcase
        end
        else begin
            out_data1 <= 64'd0;
            out_data2 <= 64'd0;
            out_valid <= 1'b0;
            cnt <= 4'd0;
            ch_cnt <= 8'd0;
            out_addr <= 8'd0-1;
            s_in_0_addr <= 10'd0;
        end
    end
end
`else
////----SHA2----////
`ifdef PARAM_128
reg [3-1:0] zp_cnt;//zero padding count
`else
reg [4-1:0] zp_cnt;//zero padding count
`endif

always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        out_data1    <= 64'd0;
        out_data2    <= 64'd0;
        cnt          <= 4'd0;
        ch_cnt       <= 8'd0;
        zp_cnt       <= 0;
        out_valid    <= 1'b0;
        out_addr     <= 8'd0-1;
        s_in_0_addr  <= 10'd0;
    end
    else begin
        if(XMSS_start) begin
            case(cnt)
            4'd0: begin//seed 64 bits
                out_data1 <= PK_seed[64*(SD_len+0)-1:64*(SD_len-1)];
                out_data2 <= PK_seed[64*(SD_len+0)-1:64*(SD_len-1)];
                cnt <= cnt + 1;
                ch_cnt <= 8'd1;
                out_valid <= 1'b1;           
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            `ifdef PARAM_128
            4'd1: begin//seed 128 bits //SD_len=2
                out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                cnt <= 4'd10;           
                ch_cnt <= ch_cnt;  
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            `endif
            `ifdef PARAM_192
            4'd1: begin//seed 192 bits //SD_len=3
                out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                cnt <= cnt + 1;       
                ch_cnt <= ch_cnt;    
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end            
            4'd2: begin//seed 192 bits //SD_len=3
                out_data1 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
                out_data2 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
                cnt <= 4'd10;   
                ch_cnt <= ch_cnt;      
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            `endif
            `ifdef PARAM_256            
            4'd1: begin//seed 256 bits //SD_len=4
                out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
                cnt <= cnt + 1;   
                ch_cnt <= ch_cnt;    
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end             
            4'd2: begin//seed 256 bits //SD_len=4
                out_data1 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
                out_data2 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;       
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end            
            4'd3: begin//seed 256 bits //SD_len=4
                out_data1 <= PK_seed[64*(SD_len-3)-1:64*(SD_len-4)];
                out_data2 <= PK_seed[64*(SD_len-3)-1:64*(SD_len-4)];
                cnt <= 4'd10;
                ch_cnt <= ch_cnt;            
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            `endif
            4'd10: begin
                out_data1 <= 64'd0;
                out_data2 <= 64'd0;

				`ifdef PARAM_128
                if(zp_cnt==(3'd7-SD_len)) begin
                    cnt <= 4'd4;
                    zp_cnt <= 0;
                end
                else begin
                    cnt <= cnt;
                    zp_cnt <= zp_cnt + 1;
                end
                `else
                if(zp_cnt==(4'd15-SD_len)) begin
                    cnt <= 4'd4;
                    zp_cnt <= 0;
                end
                else begin
                    cnt <= cnt;
                    zp_cnt <= zp_cnt + 1;
                end                
                `endif

                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
            end              
            4'd4: begin//4
                out_data1 <= {layer_addr[8-1:0],tree_addr[64-1:8]};
                out_data2 <= {layer_addr[8-1:0],tree_addr[64-1:8]};
                out_valid <= 1'b1;
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;
                if(i_mode_flag) begin
                    `ifdef PARAM_128
                    out_addr <= 8;
                    `else
                    out_addr <= 16;
                    `endif
                end
                else begin
                    out_addr <= out_addr + 1'b1;
                end                 
                s_in_0_addr <= s_in_0_addr;
            end
            4'd5: begin
                //HT_mode 0: HyperTree mode, H type=2
                //HT_mode 1: FORS Tree mode, H type=3                
                if(!HT_mode) begin
                    out_data1 <= {tree_addr[8-1:0],8'd2,32'd0,tree_h_w[32-1:16]};
                    out_data2 <= {tree_addr[8-1:0],8'd2,32'd0,tree_h_w[32-1:16]};
                end
                else begin
                    out_data1 <= {tree_addr[8-1:0],8'd3,ap_leaf_idx_w,tree_h_w[32-1:16]};
                    out_data2 <= {tree_addr[8-1:0],8'd3,ap_leaf_idx_w,tree_h_w[32-1:16]};
                end            
                out_valid <= 1'b1;
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr + 1'b1;
            end
            4'd6: begin//
                if(o_sig_read_mem_r2 && i_sig_mode==1'b1) begin
                    out_data1 <= {tree_h_w[16-1:0],target_idx_32_w,i_sig_mem_out[64-1:48]};
                    out_data2 <= {tree_h_w[16-1:0],target_idx_32_w,i_sig_mem_out[64-1:48]};
                    tmp_reg_0 <= i_sig_mem_out[48-1:0];
                    tmp_reg_1 <= i_sig_mem_out[48-1:0];                    
                end
                else if(i_sig_mode==1'b1) begin
                    out_data1 <= {tree_h_w[16-1:0],target_idx_32_w,s_out_0[64-1:48]};
                    out_data2 <= {tree_h_w[16-1:0],target_idx_32_w,s_out_0[64-1:48]};
                    tmp_reg_0 <= s_out_0[48-1:0];
                    tmp_reg_1 <= s_out_0[48-1:0];
                end
                else begin
                    out_data1 <= {tree_h_w[16-1:0],tree_i_w,s_out_0[64-1:48]};
                    out_data2 <= {tree_h_w[16-1:0],(tree_i_w+1'b1),s_out_2[64-1:48]};
                    tmp_reg_0 <= s_out_0[48-1:0];
                    tmp_reg_1 <= s_out_2[48-1:0];
                end
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
                cnt <= cnt + 1;
                s_in_0_addr <= s_in_0_addr + 1'b1;
            end
            4'd7: begin//
                if(o_sig_read_mem_r2 && i_sig_mode==1'b1) begin
                    out_data1 <= {tmp_reg_0,i_sig_mem_out[64-1:48]};
                    out_data2 <= {tmp_reg_1,i_sig_mem_out[64-1:48]};
                    tmp_reg_0 <= i_sig_mem_out[48-1:0];
                    tmp_reg_1 <= i_sig_mem_out[48-1:0];                    
                end
                else if(i_sig_mode==1'b1) begin
                    out_data1 <= {tmp_reg_0,s_out_0[64-1:48]};
                    out_data2 <= {tmp_reg_1,s_out_0[64-1:48]};
                    tmp_reg_0 <= s_out_0[48-1:0];
                    tmp_reg_1 <= s_out_0[48-1:0];
                end
                else begin
                    out_data1 <= {tmp_reg_0,s_out_0[64-1:48]};
                    out_data2 <= {tmp_reg_1,s_out_2[64-1:48]};
                    tmp_reg_0 <= s_out_0[48-1:0];
                    tmp_reg_1 <= s_out_2[48-1:0];
                end
                out_valid <= 1'b1;
                out_addr <= out_addr + 1'b1;
				if(ch_cnt == ((CH_len)+1)) begin
                    cnt <= cnt + 1;
                    ch_cnt <= 8'd1;
                    s_in_0_addr <= s_in_0_addr;
                end
                else begin
                    cnt <= cnt;
                    ch_cnt <= ch_cnt + 1'b1;
                    s_in_0_addr <= s_in_0_addr + 1'b1;
                end
            end            
            4'd8: begin//
                out_data1 <= {tmp_reg_0,16'd0};
                out_data2 <= {tmp_reg_1,16'd0};
                out_valid <= 1'b1;
                cnt <= cnt + 1;
                ch_cnt <= ch_cnt;
                out_addr <= out_addr + 1'b1;
                s_in_0_addr <= s_in_0_addr;
            end
            4'd9: begin//cnt 9: wait state
                out_data1 <= 32'd0;
                out_data2 <= 32'd0;
                out_valid <= 1'b0;
                ch_cnt <= ch_cnt;

                if(hash_done_1d) begin
                    `ifdef PARAM_128
                    s_in_0_addr <= s_in_0_addr - 10'd1;
                    `endif
                    `ifdef PARAM_192
                    s_in_0_addr <= s_in_0_addr - 10'd2;
                    `endif
                    `ifdef PARAM_256
                    s_in_0_addr <= s_in_0_addr - 10'd3;
                    `endif 
                    out_addr <= 8'd0-1;
                    if(i_mode_flag) begin
                        cnt <= 4'd4;
                    end
                    else begin
                        cnt <= 4'd0;
                    end                    
                end
                else if(fsm_data_in_flag0) begin 
                    s_in_0_addr <= s_in_0_addr + 1'b1;
                end
                else begin
                    s_in_0_addr <= s_in_0_addr;
                    out_addr <= out_addr;
                    cnt <= cnt;
                end
            end            
            default: begin
                out_data1 <= 32'd0;
                out_data2 <= 32'd0;
                out_valid <= 1'b0;
                s_in_0_addr <= s_in_0_addr;
                out_addr <= out_addr;
                cnt <= cnt;
                ch_cnt <= ch_cnt;
            end
            endcase
        end
        else begin
            out_data1 <= 32'd0;
            out_data2 <= 32'd0;
            out_valid <= 1'b0;
            if(i_mode_flag) begin
                cnt <= 4'd4;
            end
            else begin
                cnt <= 4'd0;
            end
            ch_cnt <= 8'd1;
            out_addr <= 8'd0-1;
            s_in_0_addr <= 10'd0;
        end
    end
end
`endif

`ifdef SHAKE
always@(cnt, ch_cnt, LR_flag, LR_flag2, hash_done_1d, flag_last, XMSS_start) begin
    case(cnt)
    4'd6: begin
        if(LR_flag2) begin
            o_sig_read_mem_r <= 1'b1;
        end
        else begin
            o_sig_read_mem_r <= 1'b0;
        end
    end    
    4'd7: begin
        if(XMSS_start) begin
            if(LR_flag2) begin
                o_sig_read_mem_r <= 1'b1;
            end
            else begin
                o_sig_read_mem_r <= 1'b0;
            end
        end
    end
    4'd8: begin
        if(ch_cnt <= (CH_len>>1)-1) begin
            if(LR_flag2) begin
                o_sig_read_mem_r <= 1'b1;
            end
            else begin
                o_sig_read_mem_r <= 1'b0;
            end            
        end        
        else if(ch_cnt <= (CH_len)) begin
            if(LR_flag2) begin
                o_sig_read_mem_r <= 1'b0;
            end
            else begin
                o_sig_read_mem_r <= 1'b1;
            end            
        end
        else begin
            o_sig_read_mem_r <= 1'b0;
        end
    end
    4'd10: begin
        if(hash_done_1d && !flag_last) begin
            if(LR_flag2_pre) begin
                o_sig_read_mem_r <= 1'b1;
            end
            else begin
                o_sig_read_mem_r <= 1'b0;
            end
        end
    end
    default: begin
        o_sig_read_mem_r <= 1'b0;
    end
    endcase
end
`else
always@(cnt, ch_cnt, LR_flag, LR_flag2, hash_done_1d, flag_last, XMSS_start) begin
    case(cnt)
    4'd4: begin
        if(XMSS_start) begin
            if(LR_flag2) begin
                o_sig_read_mem_r <= 1'b1;
            end
            else begin
                o_sig_read_mem_r <= 1'b0;
            end
        end
    end    
    4'd5: begin
        if(XMSS_start) begin
            if(LR_flag2) begin
                o_sig_read_mem_r <= 1'b1;
            end
            else begin
                o_sig_read_mem_r <= 1'b0;
            end
        end
    end
    4'd6: begin
        if(ch_cnt <= (CH_len>>1)-1) begin
            if(LR_flag2) begin
                o_sig_read_mem_r <= 1'b1;
            end
            else begin
                o_sig_read_mem_r <= 1'b0;
            end            
        end        
        else if(ch_cnt <= (CH_len)-1) begin
            if(LR_flag2) begin
                o_sig_read_mem_r <= 1'b0;
            end
            else begin
                o_sig_read_mem_r <= 1'b1;
            end            
        end
        else begin
            o_sig_read_mem_r <= 1'b0;
        end
    end
    4'd7: begin
        if(ch_cnt <= (((CH_len>>1)-1)>>1)) begin
            if(LR_flag2) begin
                o_sig_read_mem_r <= 1'b1;
            end
            else begin
                o_sig_read_mem_r <= 1'b0;
            end            
        end        
        else if(ch_cnt <= (CH_len)-1) begin
            if(LR_flag2) begin
                o_sig_read_mem_r <= 1'b0;
            end
            else begin
                o_sig_read_mem_r <= 1'b1;
            end            
        end
        else begin
            o_sig_read_mem_r <= 1'b0;
        end
    end
    default: begin
        o_sig_read_mem_r <= 1'b0;
    end
    endcase
end
`endif

always@(posedge clk) begin
    if(i_sig_mode==1'b1) begin
        if(FSM_start_in || leaf_node_gen_done==1'b1) begin
            LR_flag2_sr <= leaf_idx;
        end
        else if(hash_done_1d) begin
            LR_flag2_sr <= {1'b0,LR_flag2_sr[INDICE_WD-1:1]};
        end
        else begin
            LR_flag2_sr <= LR_flag2_sr;
        end
    end
    else begin
        LR_flag2_sr <= 0;
    end
end

always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        o_sig_read_mem_r_d <= 2'd0;
    end
    else begin
        o_sig_read_mem_r_d <= {o_sig_read_mem_r,o_sig_read_mem_r_d[2-1]};
    end
end

assign data_in_flag0 = (h_con1 || h_con3);

//Calculate h_cnt: H hash count
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        h_cnt <= 5'd0;
    end
    else begin
        `ifdef PARAM_128F
        if(ncnt[0]) begin //1
            h_cnt <= 5'd1;
        end
        else if(ncnt[1]) begin //10
            h_cnt <= 5'd2;
        end
        else if(ncnt[2]) begin //100
            h_cnt <= 5'd3;
        end
        else if(ncnt[3]) begin //1000
            h_cnt <= 5'd4;
        end
        else if(ncnt[4]) begin //1_0000
            h_cnt <= 5'd5;
        end
        else begin
            h_cnt <= 5'd1;
        end
        `endif
        `ifdef PARAM_128S
        if(ncnt[0]) begin //1
            h_cnt <= 5'd1;
        end
        else if(ncnt[1]) begin //10
            h_cnt <= 5'd2;
        end
        else if(ncnt[2]) begin //100
            h_cnt <= 5'd3;
        end
        else if(ncnt[3]) begin //1000
            h_cnt <= 5'd4;
        end
        else if(ncnt[4]) begin //1_0000
            h_cnt <= 5'd5;
        end        
        else if(ncnt[5]) begin //10_0000
            h_cnt <= 5'd6;
        end
        else if(ncnt[6]) begin //100_0000
            h_cnt <= 5'd7;
        end
        else if(ncnt[7]) begin //1000_0000
            h_cnt <= 5'd8;
        end
        else if(ncnt[8]) begin //1_0000_0000
            h_cnt <= 5'd9;
        end
        else if(ncnt[9]) begin //10_0000_0000
            h_cnt <= 5'd10;
        end
        else if(ncnt[10]) begin //100_0000_0000
            h_cnt <= 5'd11;
        end
        else begin
            h_cnt <= 5'd1;
        end
        `endif
        `ifdef PARAM_192F
        if(ncnt[0]) begin //1
            h_cnt <= 5'd1;
        end
        else if(ncnt[1]) begin //10
            h_cnt <= 5'd2;
        end
        else if(ncnt[2]) begin //100
            h_cnt <= 5'd3;
        end
        else if(ncnt[3]) begin //1000
            h_cnt <= 5'd4;
        end
        else if(ncnt[4]) begin //1_0000
            h_cnt <= 5'd5;
        end        
        else if(ncnt[5]) begin //10_0000
            h_cnt <= 5'd6;
        end
        else if(ncnt[6]) begin //100_0000
            h_cnt <= 5'd7;
        end
        else begin
            h_cnt <= 5'd1;
        end         
        `endif
        `ifdef PARAM_192S
        if(ncnt[0]) begin //1
            h_cnt <= 5'd1;
        end
        else if(ncnt[1]) begin //10
            h_cnt <= 5'd2;
        end
        else if(ncnt[2]) begin //100
            h_cnt <= 5'd3;
        end
        else if(ncnt[3]) begin //1000
            h_cnt <= 5'd4;
        end
        else if(ncnt[4]) begin //1_0000
            h_cnt <= 5'd5;
        end        
        else if(ncnt[5]) begin //10_0000
            h_cnt <= 5'd6;
        end
        else if(ncnt[6]) begin //100_0000
            h_cnt <= 5'd7;
        end
        else if(ncnt[7]) begin //1000_0000
            h_cnt <= 5'd8;
        end
        else if(ncnt[8]) begin //1_0000_0000
            h_cnt <= 5'd9;
        end
        else if(ncnt[9]) begin //10_0000_0000
            h_cnt <= 5'd10;
        end
        else if(ncnt[10]) begin //100_0000_0000
            h_cnt <= 5'd11;
        end
        else if(ncnt[11]) begin //1000_0000_0000
            h_cnt <= 5'd12;
        end
        else if(ncnt[12]) begin //1_0000_0000_0000
            h_cnt <= 5'd13;
        end
        else begin
            h_cnt <= 5'd1;
        end           
        `endif
        `ifdef PARAM_256F
        if(ncnt[0]) begin //1
            h_cnt <= 5'd1;
        end
        else if(ncnt[1]) begin //10
            h_cnt <= 5'd2;
        end
        else if(ncnt[2]) begin //100
            h_cnt <= 5'd3;
        end
        else if(ncnt[3]) begin //1000
            h_cnt <= 5'd4;
        end
        else if(ncnt[4]) begin //1_0000
            h_cnt <= 5'd5;
        end        
        else if(ncnt[5]) begin //10_0000
            h_cnt <= 5'd6;
        end
        else if(ncnt[6]) begin //100_0000
            h_cnt <= 5'd7;
        end
        else if(ncnt[7]) begin //1000_0000
            h_cnt <= 5'd8;
        end
        else begin
            h_cnt <= 5'd1;
        end          
        `endif
        `ifdef PARAM_256S
        if(ncnt[0]) begin //1
            h_cnt <= 5'd1;
        end
        else if(ncnt[1]) begin //10
            h_cnt <= 5'd2;
        end
        else if(ncnt[2]) begin //100
            h_cnt <= 5'd3;
        end
        else if(ncnt[3]) begin //1000
            h_cnt <= 5'd4;
        end
        else if(ncnt[4]) begin //1_0000
            h_cnt <= 5'd5;
        end        
        else if(ncnt[5]) begin //10_0000
            h_cnt <= 5'd6;
        end
        else if(ncnt[6]) begin //100_0000
            h_cnt <= 5'd7;
        end
        else if(ncnt[7]) begin //1000_0000
            h_cnt <= 5'd8;
        end
        else if(ncnt[8]) begin //1_0000_0000
            h_cnt <= 5'd9;
        end
        else if(ncnt[9]) begin //10_0000_0000
            h_cnt <= 5'd10;
        end
        else if(ncnt[10]) begin //100_0000_0000
            h_cnt <= 5'd11;
        end
        else if(ncnt[11]) begin //1000_0000_0000
            h_cnt <= 5'd12;
        end
        else if(ncnt[12]) begin //1_0000_0000_0000
            h_cnt <= 5'd13;
        end
        else begin
            h_cnt <= 5'd1;
        end           
        `endif
    end
end

endmodule