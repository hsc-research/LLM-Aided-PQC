
module WOTS_FSM
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
parameter L_param = //chain length
                    (parameter_set == "128s") ? 35: 
                    (parameter_set == "128f") ? 35:
                    (parameter_set == "192s") ? 51:
                    (parameter_set == "192f") ? 51:
                    (parameter_set == "256s") ? 67:
                    (parameter_set == "256f") ? 67: 67,
parameter TL_len = //lenght of T_L child data
                    (parameter_set == "128s") ? 70:
                    (parameter_set == "128f") ? 70:
                    (parameter_set == "192s") ? 153:
                    (parameter_set == "192f") ? 153:
                    (parameter_set == "256s") ? 268:
                    (parameter_set == "256f") ? 268: 268,
parameter TL_k = 
                    (parameter_set == "128s") ? 28:
                    (parameter_set == "128f") ? 66:
                    (parameter_set == "192s") ? 51:
                    (parameter_set == "192f") ? 99:
                    (parameter_set == "256s") ? 88:
                    (parameter_set == "256f") ? 140: 140,                         
parameter Node_count_num = 
                    (parameter_set == "128s") ? 13:
                    (parameter_set == "128f") ? 7:
                    (parameter_set == "192s") ? 15:
                    (parameter_set == "192f") ? 9:
                    (parameter_set == "256s") ? 15:
                    (parameter_set == "256f") ? 10: 15,
parameter Chain_count_num = 
                    (parameter_set == "128s") ? 6:
                    (parameter_set == "128f") ? 6:
                    (parameter_set == "192s") ? 6:
                    (parameter_set == "192f") ? 6:
                    (parameter_set == "256s") ? 7:
                    (parameter_set == "256f") ? 7: 7,
parameter TL_count_num = 
                    (parameter_set == "128s") ? 8:
                    (parameter_set == "128f") ? 8:
                    (parameter_set == "192s") ? 9:
                    (parameter_set == "192f") ? 9:
                    (parameter_set == "256s") ? 10:
                    (parameter_set == "256f") ? 10: 10,
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
input  wire                clk,
input  wire                rstn,
input  wire                FSM_start_in,
output wire                FSM_start_out,
input  wire [SEED_num-1:0] SK_seed,
input  wire [SEED_num-1:0] PK_seed,
input  wire [32  -1:0]     layer_addr,
input  wire [32*2-1:0]     tree_addr,
output wire                o_WOTS_done,
output wire [IO_WIDTH-1:0] o_s_data_in,
output wire                o_s_wr_en,
output wire [WD-1:0]       o_s_addr,
output wire [IO_WIDTH-1:0] o_b_data_in,
output wire                o_b_wr_en,
output wire [WD-1:0]       o_b_addr,
// o_opcode = 0 => T_L_WOTS
// o_opcode = 1 => PRF
// o_opcode = 4 => F_WOTS+
// o_opcode = 6 => F_WOTS+ iterated for h_iterations
// o_opcode = 7 => T_L_FORS
output wire [3-1:0]        o_opcode,
output wire                o_hash_start,
input  wire                i_hash_done,
input wire                 fsm_data_in_flag0,
output wire                data_in_flag0,
output wire                data_in_flag1,
output wire                data_in_flag2,
output reg                 s_in_0_wr_en,
output reg                 s_in_1_wr_en,
input [INDICE_WD-1:0]      W_param,
input [INDICE_WD-1:0]      leaf_node_num, //# of leaf node
output wire                o_sig_read_mem,
input  wire [64-1:0]       i_sig_mem_out,
input wire                 i_sig_mode, //0:sig generation, 1:sig verification
input [2-1:0]              mode, 
//mode0: WOTS pk gen
//mode1: FORS leaf gen
//mode3: FORS T_L
`ifdef SHA2
`ifdef PARAM_128
input wire i_mode_flag1,
`else
input wire i_mode_flag1,
input wire i_mode_flag2,
`endif
`endif
input wire                 XMSS_root_flag,
input wire [WD       -1:0] XMSS_addr,
input wire [INDICE_WD-1:0] w_addr2,
input wire [LEAF_WD-1:0]   ap_leaf_idx,
input wire                 FORS_prf_in,
output reg                 FORS_prf_flag,
input  wire                i_wots_chain_flag,
output  reg                o_wots_chain_flag1,
output  reg                o_wots_chain_flag2,
output  reg                o_chain_cnt_up,
output wire [4-1:0]        o_w_iter,
input  wire [4-1:0]        in_w_cnt1,
input  wire [4-1:0]        in_w_cnt2,
output wire [WD-1:0]       wots_o_tmp_in_0_addr,
output wire [WD-1:0]       wots_o_tmp_in_1_addr,
output wire                wots_o_tmp_in_0_wr_en,
output wire                wots_o_tmp_in_1_wr_en,
input  wire [IO_WIDTH-1:0] wots_o_tmp_out_0,
input  wire [IO_WIDTH-1:0] wots_o_tmp_out_1
); 

reg  [IO_WIDTH-1:0]        out_data1;
reg  [IO_WIDTH-1:0]        out_data2;
reg  [WD-1:0]              out_addr;
wire [8-1:0]               type;
wire [8-1:0]               type_T_L;
wire [32-1:0]              node_addr_w;//leaf node
wire [ 7-1:0]              chain_addr;//chain in one node
reg  [INDICE_WD-1:0]       w_addr;//w iter in one chain
reg  [ 3-1:0]              opcode;
reg  [ 5-1:0]              cnt;
reg  [Node_count_num-1:0]  node_cnt;
reg  [Chain_count_num-1:0] chain_cnt;
reg  [INDICE_WD-1:0]       w_cnt;
reg  [TL_count_num-1:0]    tl_cnt;
wire [Node_count_num-1:0]  NC;//node count
wire [Chain_count_num-1:0] CC;//chain count
reg  [INDICE_WD-1:0]       WC;//w count
reg                        out_valid;
reg                        hash_start;
reg                        hash_start_1d;
reg                        hash_start_2d;
reg                        WOTS_start;
reg                        WOTS_done;
wire                       hash_done_1d;
reg                        PRF_flag;
reg                        flag1;
reg  [4-1:0]               ch_cnt;
wire [IO_WIDTH-1:0]        tmp_out_0;
wire [IO_WIDTH-1:0]        tmp_out_1;
`ifdef SHA2
reg  [IO_WIDTH-1:0]        tmp_reg_0;
reg  [IO_WIDTH-1:0]        tmp_reg_1;
`endif
reg  [WD-1:0]              tmp_in_0_addr;
wire [WD-1:0]              tmp_in_1_addr;
reg                        tmp_in_0_wr_en;
reg                        tmp_in_1_wr_en;
reg                        write_tmp_valid;
wire [32-1:0]              w_addr2_32_w;
wire [32-1:0]              w_addr_32_w;
wire [32-1:0]              w_addr_32_w_1;
wire [5-1:0]               w_iter_5;
wire                       skip_flag;
wire [4-1:0]               w_iter_tmp;
reg                        o_sig_read_mem_r;
wire [WD-1:0]              i_tmp_in_0_addr;
wire                       i_tmp_in_1_wr_en;

assign NC                    = leaf_node_num;
assign CC                    = L_param;
assign o_sig_read_mem        = o_sig_read_mem_r;
assign data_in_flag2         = write_tmp_valid;
assign wots_o_tmp_in_0_addr  = i_tmp_in_0_addr;
assign wots_o_tmp_in_1_addr  = tmp_in_1_addr;
assign wots_o_tmp_in_0_wr_en = tmp_in_0_wr_en;
assign wots_o_tmp_in_1_wr_en = i_tmp_in_1_wr_en;
assign tmp_out_0             = wots_o_tmp_out_0;
assign tmp_out_1             = wots_o_tmp_out_1;

assign i_tmp_in_0_addr  = XMSS_root_flag ? XMSS_addr : tmp_in_0_addr;
assign i_tmp_in_1_wr_en = XMSS_root_flag ? 0 : ((i_sig_mode==1'b1 && mode==2'd0) ? 0 : tmp_in_1_wr_en);

assign chain_addr = chain_cnt-1;
assign w_addr2_32_w  = w_addr2;
assign w_addr_32_w   = w_cnt-1;
assign w_addr_32_w_1 = w_cnt;
assign w_iter_5      = (in_w_cnt1==4'b1111) ? 5'd15 : (in_w_cnt1 + 1);
assign skip_flag     = (i_sig_mode==1'b1 && mode==2'd0) ? ((in_w_cnt1==4'b1111) ? 1 : 0) : 0;

assign type         = mode==2'd0 ? (PRF_flag ? 8'd5 : 8'd0) : (PRF_flag ? 8'd6 : 8'd3); 
assign type_T_L     = mode==2'd0 ? 8'd1 : 8'd4;     
//when mode0: PRF=5, F=0, T_L=1 (WOTS pk gen & Comp)
//when mode1: PRF=6, F=3, T_L=4 (FORS leaf gen & Comp)

assign hash_done_1d  = i_hash_done;
assign FSM_start_out = WOTS_start;

`ifdef PARAM_128
assign tmp_in_1_addr = tmp_in_0_addr + 10'd2;
`endif

`ifdef PARAM_192
assign tmp_in_1_addr = tmp_in_0_addr + 10'd3;
`endif

`ifdef PARAM_256
assign tmp_in_1_addr = tmp_in_0_addr + 10'd4;
`endif

assign o_s_data_in  = out_data1;
assign o_s_wr_en    = out_valid;
assign o_s_addr     = out_addr;
assign o_b_data_in  = out_data2;
assign o_b_wr_en    = out_valid;
assign o_b_addr     = out_addr;

assign o_hash_start = flag1 ? hash_start_2d : hash_start;
assign o_opcode     = opcode;
assign o_WOTS_done  = WOTS_done;

assign node_addr_w = mode==2'd0 ? (i_sig_mode==1'b1 ? ap_leaf_idx : (node_cnt - 1)) : ap_leaf_idx;
assign w_iter_tmp  = (i_sig_mode==1'b1 && mode==2'd0) ? 4'b1111 ^ in_w_cnt1 : 4'b1111;
assign o_w_iter    = (w_iter_tmp==4'd0) ? 4'd1 : w_iter_tmp;

always@(i_wots_chain_flag, w_cnt, WC, cnt, hash_done_1d) begin   
    o_chain_cnt_up <= 1'b0; 
    if(i_wots_chain_flag) begin
        if(w_cnt==WC && cnt == 5'd16 && hash_done_1d) begin
            o_chain_cnt_up <= 1'b1;
        end
        else begin
            o_chain_cnt_up <= 1'b0;
        end
    end
    else begin
        o_chain_cnt_up <= 1'b0;
    end    
end

always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        o_wots_chain_flag1 <= 1'b0;
        o_wots_chain_flag2 <= 1'b0;
    end
    else begin
        if(i_wots_chain_flag) begin

            if(((4'd0 == in_w_cnt1) && opcode==3'd1) || ((w_cnt == in_w_cnt1) && (opcode==3'd4 || opcode==3'd6))) begin
                o_wots_chain_flag1 <= 1'b1;
            end
            else begin
                o_wots_chain_flag1 <= 1'b0;
            end

            if(((4'd0 == in_w_cnt2) && opcode==3'd1 && chain_cnt!=CC) || ((w_cnt == in_w_cnt2) && (opcode==3'd4 || opcode==3'd6))) begin
                o_wots_chain_flag2 <= 1'b1;
            end
            else begin
                o_wots_chain_flag2 <= 1'b0;
            end    
        end
        else begin
            o_wots_chain_flag1 <= 1'b0;
            o_wots_chain_flag2 <= 1'b0;
        end    
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

always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
	 	flag1         <= 1'b0;
    end
    else begin
        if(FSM_start_in) begin
			flag1      <= 1'b1;
        end
        else begin
			if(hash_start_2d) begin
				flag1 <= 1'b0;
			end
            else if((hash_done_1d && PRF_flag)||(w_cnt==19'd15 && hash_done_1d)) begin
                flag1 <= 1'b1;
            end
			else begin
				flag1 <= flag1;
			end
        end
    end
end


reg [3-1:0] state;
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        state <= 3'd0;
        WOTS_start    <= 1'b0;
        WOTS_done     <= 1'b0;
        node_cnt      <= 12'd1;
        chain_cnt     <= 12'd0;  
        w_cnt         <= 19'd1;
        hash_start    <= 1'b0;
        WC            <= 19'd0;
        opcode        <= 3'd0;
        PRF_flag      <= 1'b0;
        FORS_prf_flag <= 1'b0;        
    end
    else begin
        case(state)
        3'd0: begin
            if(FSM_start_in) begin
                WOTS_start <= 1'b1;
                node_cnt   <= node_cnt;
                chain_cnt  <= 12'd1;
                hash_start <= 1'b1;
                WC         <= W_param;

                if(mode==2'd3) begin//T_L_FORS
                    state <= 3'd3;
                    opcode <= 3'd7;
                    PRF_flag <= 1'b0;
                end
                else if(mode==2'd1 && i_sig_mode==1'b1) begin//F1
                    state <= 3'd2;
                    opcode <= 3'd4;
                    PRF_flag <= 1'b0;
                    FORS_prf_flag <= 1'b0;
                end            
                else if(mode==2'd0 && i_sig_mode==1'b1) begin//F_iter
                    state <= 3'd2;
                    opcode <= 3'd6;
                    PRF_flag <= 1'b0;
                    FORS_prf_flag <= 1'b0;
                end            
                else if(FORS_prf_in) begin//PRF
                    state <= 3'd1;
                    opcode <= 3'd1;
                    PRF_flag <= 1'b1;
                    FORS_prf_flag <= 1'b1;
                end
                else begin//PRF
                    state <= 3'd1;
                    opcode <= 3'd1;
                    PRF_flag <= 1'b1;
                end                
            end
        end
        3'd1: begin//cnt==16, after PRF
            if(hash_done_1d) begin
                if(FORS_prf_flag) begin//PRF->PRF
                    state <= state;
                    hash_start <= 1'b1;
                    PRF_flag   <= 1'b1;
                    opcode     <= 3'd1; 
                    FORS_prf_flag <= 1'b0;
                end
                else begin//PRF->F
                    state <= 3'd2;
                    hash_start <= 1'b1;
                    PRF_flag   <= 1'b0;
                    if(mode==2'd0) begin
                        opcode <= 3'd6;//F_iter
                    end
                    else begin
                        opcode <= 3'd4;//F1
                    end  
                end
            end        
            else begin
                state <= state;
                node_cnt   <= node_cnt;
                chain_cnt  <= chain_cnt;
                PRF_flag   <= PRF_flag;
                hash_start <= 1'b0;
                WOTS_done  <= 1'b0;
                w_cnt <= w_cnt;
            end            
        end
        3'd2: begin//cnt==16, after F    
            if(hash_done_1d) begin//F->F
                if(w_cnt == WC && mode==2'd0) begin//mode 0
                    w_cnt  <= 19'd1;

                    if(i_sig_mode==1'b0) begin
                        chain_cnt <= chain_cnt + 2;
                    end
                    else begin
                        chain_cnt <= chain_cnt + 1;
                    end   

                    if(chain_cnt == CC) begin                        
                        state <= 3'd3;
                        WOTS_done  <= 1'b0;
                        hash_start <= 1'b1;
                        PRF_flag   <= 1'b0;
                        opcode     <= 3'd0;//T_L_WOTS
                    end
                    else begin
                        if(i_sig_mode==1'b0) begin
                            state <= 3'd1;
                            WOTS_done  <= 1'b0;
                            hash_start <= 1'b1;
                            PRF_flag   <= 1'b1;
                            opcode     <= 3'd1;//PRF
                            node_cnt   <= node_cnt;
                        end
                        else begin
                            state <= state;
                            WOTS_done  <= 1'b0;
                            hash_start <= 1'b1;
                            PRF_flag   <= 1'b0;
                            opcode     <= 3'd6;//F_iter
                            node_cnt   <= node_cnt;
                        end
                    end
                end
                else begin
                    chain_cnt  <= chain_cnt;
                    if(mode == 2'd1) begin
                        state <= 3'd4;
                        WOTS_done  <= 1'b1;
                        hash_start <= 1'b0;
                        w_cnt      <= w_cnt + 2;
                    end
                    else begin
                        state <= state;
                        WOTS_done  <= 1'b0;
                        hash_start <= 1'b1;
                        w_cnt      <= w_cnt + 1;
                    end
                end
            end        
            else begin
                state <= state;
                node_cnt   <= node_cnt;
                chain_cnt  <= chain_cnt;
                PRF_flag   <= PRF_flag;
                hash_start <= 1'b0;
                WOTS_done  <= 1'b0;

                if(cnt == 5'd15 && i_sig_mode==1'b1 && mode==2'd0) begin
                    w_cnt <= {14'd0,w_iter_5};
                end
                else begin
                    w_cnt <= w_cnt;
                end                    
            end            
        end
        3'd3: begin//cnt==22, after T_L
            if(hash_done_1d) begin//T_L
                state <= 3'd4;
                chain_cnt  <= 1;
                WOTS_done  <= 1'b1;
                hash_start <= 1'b0;
                PRF_flag   <= 1'b0;
                opcode     <= 3'd0;
                WC         <= W_param;

                if(mode==2'd3 || node_cnt == NC) begin
                    node_cnt <= 12'd1;
                end
                else begin
                    node_cnt <= node_cnt + 1'b1;
                end
                if(mode==2'd3) begin
                    w_cnt     <= 19'd1;//reset before starting the HT
                end
            end
            else begin
                state <= state;
                node_cnt   <= node_cnt;
                PRF_flag   <= PRF_flag;
                hash_start <= 1'b0;
                WOTS_done  <= 1'b0;
                w_cnt <= w_cnt;               
            end              
        end
        3'd4: begin//done
            state <= 3'd0;
            WOTS_start <= 1'b0;
            hash_start <= 1'b0;
            WOTS_done <= 1'b0;
        end
        endcase
    end
end


`ifdef SHAKE
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        out_data1     <= 32'd0;
        out_data2     <= 32'd0;
        cnt           <= 5'd0;
        out_valid     <= 1'b0;
        out_addr      <= 8'd0-1;
        tmp_in_0_addr <= 10'd0;
        //w_addr        <= 19'd0;
        tl_cnt        <= 8'd0;
        ch_cnt        <= 8'd0;
        write_tmp_valid <= 1'b0;
    end
    else begin
        case(cnt)
        5'd0: begin
            if(FSM_start_in) begin
                cnt <= 5'd2;//start from PK.seed
            end
        end
        5'd6: begin// push SK_seed N-Bytes to hash_tile
            tl_cnt    <= 8'd1;
            out_data1 <= SK_seed[64*(SD_len+0)-1:64*(SD_len-1)];
            out_data2 <= SK_seed[64*(SD_len+0)-1:64*(SD_len-1)];
            
            cnt <= 5'd1;
            ch_cnt <= 8'd1;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
            tmp_in_0_addr <= tmp_in_0_addr;
        end
        `ifdef PARAM_128
        5'd1: begin
            out_data1 <= SK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            out_data2 <= SK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            
            cnt <= 5'd16;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        `endif            
        `ifdef PARAM_192
        5'd1: begin
            out_data1 <= SK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            out_data2 <= SK_seed[64*(SD_len-1)-1:64*(SD_len-2)];

            cnt <= 5'd23;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd23: begin
            out_data1 <= SK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            out_data2 <= SK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            
            cnt <= 5'd16;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        `endif            
        `ifdef PARAM_256
        5'd1: begin
            out_data1 <= SK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            out_data2 <= SK_seed[64*(SD_len-1)-1:64*(SD_len-2)];

            cnt <= 5'd23;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd23: begin
            out_data1 <= SK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            out_data2 <= SK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            
            cnt <= 5'd24;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd24: begin
            out_data1 <= SK_seed[64*(SD_len-3)-1:64*(SD_len-4)];
            out_data2 <= SK_seed[64*(SD_len-3)-1:64*(SD_len-4)];
            
            cnt <= 5'd16;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        `endif
        5'd2: begin// push PK_seed N-Bytes to hash_tile
            tl_cnt    <= 8'd1;
            out_data1 <= PK_seed[64*(SD_len+0)-1:64*(SD_len-1)];
            out_data2 <= PK_seed[64*(SD_len+0)-1:64*(SD_len-1)];
            
            cnt <= 5'd3;
            ch_cnt <= 8'd1;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        `ifdef PARAM_128
        5'd3: begin
            out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            
            cnt <= 5'd4;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end      
        `endif
        `ifdef PARAM_192
        5'd3: begin
            out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            
            cnt <= 5'd25;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd25: begin
            out_data1 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            out_data2 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            
            cnt <= 5'd4;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        `endif
        `ifdef PARAM_256
        5'd3: begin
            out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            
            cnt <= 5'd25;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd25: begin
            out_data1 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            out_data2 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            
            cnt <= 5'd26;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd26: begin
            out_data1 <= PK_seed[64*(SD_len-3)-1:64*(SD_len-4)];
            out_data2 <= PK_seed[64*(SD_len-3)-1:64*(SD_len-4)];
            
            cnt <= 5'd4;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        `endif
        5'd4: begin//ADRS start
            out_data1 <= {24'd0,layer_addr[8-1:0],32'd0};
            out_data2 <= {24'd0,layer_addr[8-1:0],32'd0};
            out_valid <= 1'b1;
            cnt <= 5'd5;
            out_addr <= out_addr + 1'b1;
        end
        5'd5: begin//
            out_data1 <= tree_addr;
            out_data2 <= tree_addr;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;

            //select type(cnt: 8) or type_T_L(cnt: 17)
            if(mode==2'd3) begin
                cnt <= 5'd17; // T_L only
                `ifdef PARAM_128
                tmp_in_0_addr <= 12'd4;
                `endif
                `ifdef PARAM_192
                tmp_in_0_addr <= 12'd6;
                `endif
                `ifdef PARAM_256
                tmp_in_0_addr <= 12'd8;
                `endif
            end
            else begin
                cnt <= 5'd8; //mode 0,1
            end
        end
        5'd8: begin//8
            out_data1 <= {24'd0,type[8-1:0],node_addr_w};
            out_data2 <= {24'd0,type[8-1:0],node_addr_w};
            out_valid <= 1'b1;
            cnt <= 5'd10;
            out_addr <= out_addr + 1'b1;
        end
        5'd10: begin//10 
            if(mode==2'd0) begin
                if(i_sig_mode==1'b1) begin
                    out_data1 <= {25'd0,chain_addr,28'd0,in_w_cnt1};
                    out_data2 <= {25'd0,chain_addr,28'd0,in_w_cnt1};
                end
                else begin
                    out_data1 <= {25'd0,chain_addr,w_addr_32_w};
                    out_data2 <= {25'd0,(chain_addr + 1'b1),w_addr_32_w};//next chain
                end
            end
            else if(FORS_prf_flag || i_sig_mode)begin //mode==1
                out_data1 <= {25'd0,chain_addr,w_addr2_32_w};
                out_data2 <= {25'd0,chain_addr,w_addr2_32_w};//next chain
            end
            else begin //mode==1
                out_data1 <= {25'd0,chain_addr,w_addr_32_w};
                out_data2 <= {25'd0,chain_addr,w_addr_32_w_1};//next chain
            end
            out_valid <= 1'b1;    
            out_addr <= out_addr + 1'b1;

            if(FORS_prf_flag) begin
                cnt <= 5'd6;
            end
            else if(PRF_flag) begin
                cnt <= 5'd6;
            end
            else begin
                cnt <= 5'd12; //jump to cnt 12
            end
            
            if(PRF_flag || FORS_prf_flag) begin
                tmp_in_0_addr <= tmp_in_0_addr;
            end
            else begin
                if(i_sig_mode==1'b1 && mode==2'd0) begin
                    write_tmp_valid <= 1'b1;
                    `ifdef PARAM_128
                    tmp_in_0_addr <= (chain_cnt - 1) << 1;
                    `endif
                    `ifdef PARAM_192
                    tmp_in_0_addr <= ((chain_cnt - 1) << 1) + (chain_cnt - 1);
                    `endif
                    `ifdef PARAM_256
                    tmp_in_0_addr <= (chain_cnt - 1) << 2;
                    `endif
                end
                else begin
                    tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
                end
            end
        end            
        5'd12: begin
            if(i_sig_mode==1'b0) begin
                out_data1 <= tmp_out_0;//previous_node_data
                out_data2 <= tmp_out_1;//previous_node_data
            end
            else begin
                out_data1 <= i_sig_mem_out;//previous_node_data
                out_data2 <= i_sig_mem_out;//previous_node_data
            end

            out_valid <= 1'b1;
            out_addr  <= out_addr + 1'b1;

            if(ch_cnt == (CH_len >> 1)) begin
                cnt         <= 5'd15; //jump to cnt 15
                ch_cnt      <= 8'd1;

                if(i_sig_mode==1'b1 && mode==2'd0 && tmp_in_0_wr_en==1'b1) begin
                    tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
                end
                else begin
                    tmp_in_0_addr <= tmp_in_0_addr;
                end
            end
            else begin
                cnt    <= cnt;
                ch_cnt <= ch_cnt + 1'b1;

                if(i_sig_mode==1'b1 && mode==2'd0) begin
                    if(tmp_in_0_wr_en==1'b1) begin
                        tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
                    end
                    else begin
                        tmp_in_0_addr <= tmp_in_0_addr;
                    end
                end
                else begin
                    tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
                end
            end
        end
        5'd15: begin//
            if(i_sig_mode==1'b0) begin
                out_data1 <= tmp_out_0;//previous_node_data
                out_data2 <= tmp_out_1;//previous_node_data
            end
            else begin
                out_data1 <= i_sig_mem_out;//previous_node_data
                out_data2 <= i_sig_mem_out;//previous_node_data
            end

            out_valid <= 1'b1;
            cnt       <= 5'd16;
            out_addr  <= out_addr + 1'b1;

            if(i_sig_mode==1'b1 && mode==2'd0) begin
                write_tmp_valid <= 1'b0;
                tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
            end         
        end
        5'd17: begin//17
            out_data1 <= {24'd0,type_T_L[8-1:0],node_addr_w};//type;
            out_data2 <= {24'd0,type_T_L[8-1:0],node_addr_w};//type;
            out_valid <= 1'b1;
            cnt <= 5'd19; //jump to cnt 19
            out_addr <= out_addr + 1'b1;
        end
        5'd19: begin//19
            out_data1 <= 64'd0;//padding
            out_data2 <= 64'd0;//padding
            out_valid <= 1'b1;
            cnt <= 5'd21; //jump to cnt 21
            out_addr <= out_addr + 1'b1;
            tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
        end
        5'd21: begin//
            out_data1 <= tmp_out_0;//previous_node_data1
            out_data2 <= tmp_out_1;//previous_node_data1
            out_valid <= 1'b1;

            if((tl_cnt == (TL_k)) && mode==2'd3) begin
                cnt    <= 5'd22;
                tl_cnt <= 8'd1;
            end
            else if(tl_cnt == (TL_len)) begin
                cnt    <= 5'd22;
                tl_cnt <= 8'd1;
            end
            else begin
                cnt    <= cnt;
                tl_cnt <= tl_cnt + 1'b1;
            end
            out_addr      <= out_addr + 1'b1;
            tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
        end
        5'd16: begin
            out_data1 <= 32'd0;
            out_data2 <= 32'd0;
            out_valid <= 1'b0;

            if(w_cnt != 12'd0 && w_cnt <= WC) begin
                if(hash_done_1d && chain_cnt == CC && w_cnt == 4'd15) begin
                    tmp_in_0_addr <= 10'd0;
                end
                else if(!hash_done_1d && tmp_in_0_wr_en) begin
                    tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
                end
                `ifdef PARAM_128
                else begin
                    if(i_sig_mode==1'b1 && mode==2'd0) begin
                        tmp_in_0_addr <= (chain_cnt - 1) << 1;
                    end
                    else begin
                        tmp_in_0_addr <= (chain_cnt >> 1) << 2;
                    end
                end
                `endif
                `ifdef PARAM_192
                else begin
                    if(i_sig_mode==1'b1 && mode==2'd0) begin
                        tmp_in_0_addr <= ((chain_cnt - 1) << 1) + (chain_cnt - 1);
                    end
                    else begin
                        tmp_in_0_addr <= ((chain_cnt >> 1) << 2) + ((chain_cnt >> 1) << 1);
                    end
                end
                `endif
                `ifdef PARAM_256
                else begin
                    if(i_sig_mode==1'b1 && mode==2'd0) begin
                        tmp_in_0_addr <= (chain_cnt - 1) << 2;
                    end
                    else begin
                        tmp_in_0_addr <= (chain_cnt >> 1) << 3;
                    end
                end
                `endif
            end
            else begin
                tmp_in_0_addr <= tmp_in_0_addr;
            end               

            if(hash_done_1d) begin
                if(w_cnt == WC && mode==2'd0) begin 
                    if(chain_cnt == CC) begin //T_L start
                        cnt      <= 5'd17;
                        `ifdef PARAM_128
                        out_addr <= 8'd3;
                        `endif
                        `ifdef PARAM_192
                        out_addr <= 8'd4;
                        `endif
                        `ifdef PARAM_256
                        out_addr <= 8'd5;
                        `endif
                    end
                    else begin //PRF 
                        cnt      <= 5'd8; //when it use same frontend
                        `ifdef PARAM_128
                        out_addr <= 8'd3;
                        `endif
                        `ifdef PARAM_192
                        out_addr <= 8'd4;
                        `endif
                        `ifdef PARAM_256
                        out_addr <= 8'd5;
                        `endif                           
                    end
                end                    
                else if(PRF_flag) begin //PRF->F
                    if(FORS_prf_flag) begin
                        cnt      <= 5'd2;
                        out_addr <= 8'd0 - 1;
                    end
                    else begin
                        cnt <= 5'd4;
                        `ifdef PARAM_128
                        out_addr <= 8'd1;
                        `endif
                        `ifdef PARAM_192
                        out_addr <= 8'd2;
                        `endif
                        `ifdef PARAM_256
                        out_addr <= 8'd3;
                        `endif
                    end
                end
                else begin //F->F
                    if(mode == 2'd1) begin
                        //FORS leaf node gen
                        cnt      <= 5'd0;
                        out_addr <= 8'd0-1;                         
                    end
                    else begin
                        //WOTS pk gen
                        cnt <= 5'd16;//F_iter

                        `ifdef PARAM_128
                        out_addr <= 8'd4;
                        `endif
                        `ifdef PARAM_192
                        out_addr <= 8'd5;
                        `endif
                        `ifdef PARAM_256
                        out_addr <= 8'd6;
                        `endif
                    end
                end
            end
            else begin
                cnt <= cnt;
                out_addr <= out_addr;
            end
        end     
        5'd22: begin
            out_data1 <= 64'd0;
            out_data2 <= 64'd0;
            out_valid <= 1'b0;
            tmp_in_0_addr <= tmp_in_0_addr;              

            if(hash_done_1d) begin //T_L end
                cnt       <= 5'd0;
                out_addr  <= 8'd0-1;
            end
            else begin
                cnt       <= cnt;
                out_addr  <= out_addr;
            end
        end                   
        default: begin
            out_data1     <= 64'd0;
            out_data2     <= 64'd0;
            out_valid     <= 1'b0;
            tmp_in_0_addr <= tmp_in_0_addr;             
            cnt           <= cnt;
            out_addr      <= out_addr;
            tl_cnt        <= tl_cnt;
            ch_cnt        <= ch_cnt;    
        end
        endcase
    end
end
`endif 

`ifdef SHA2
`ifdef PARAM_128
reg [3-1:0] zp_cnt;//zero padding count
`else
reg [4-1:0] zp_cnt;//zero padding count
`endif

always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        out_data1     <= 32'd0;
        out_data2     <= 32'd0;
        cnt           <= 5'd0;
        out_valid     <= 1'b0;
        out_addr      <= 8'd0-1;
        tmp_in_0_addr <= 10'd0;
        tl_cnt        <= 8'd0;
        ch_cnt        <= 8'd0;
        zp_cnt        <= 0;
        write_tmp_valid <= 1'b0;
    end
    else begin
        case(cnt)
        5'd0: begin
            if(FSM_start_in) begin
                if(i_mode_flag1) begin
                    cnt <= 5'd4;//start from ADRS
                end
                else begin
                    cnt <= 5'd2;//start from PK.seed
                end
            end
        end
        5'd6: begin// push SK_seed N-Bytes to hash_tile
            tl_cnt    <= 8'd1;
            if(mode==2'd0) begin
                if(i_sig_mode==1'b1) begin
                    out_data1 <= {9'd0,chain_addr,28'd0,in_w_cnt1,SK_seed[64*(SD_len+0)-1:64*(SD_len-1)+48]};//16(9+7)+32(28+4)+16
                    out_data2 <= {9'd0,chain_addr,28'd0,in_w_cnt1,SK_seed[64*(SD_len+0)-1:64*(SD_len-1)+48]};//16(9+7)+32(28+4)+16
                end
                else begin
                    out_data1 <= {9'd0,chain_addr,w_addr_32_w,SK_seed[64*(SD_len+0)-1:64*(SD_len-1)+48]};//16(9+7)+32+16
                    out_data2 <= {9'd0,(chain_addr + 1'b1),w_addr_32_w,SK_seed[64*(SD_len+0)-1:64*(SD_len-1)+48]};//16(9+7)+32+16
                end
            end
            else if(FORS_prf_flag || i_sig_mode)begin //mode==1
                out_data1 <= {9'd0,chain_addr,w_addr2_32_w,SK_seed[64*(SD_len+0)-1:64*(SD_len-1)+48]};//16(9+7)+32+16
                out_data2 <= {9'd0,chain_addr,w_addr2_32_w,SK_seed[64*(SD_len+0)-1:64*(SD_len-1)+48]};//16(9+7)+32+16
            end
            else begin //mode==1
                out_data1 <= {9'd0,chain_addr,w_addr_32_w,SK_seed[64*(SD_len+0)-1:64*(SD_len-1)+48]};//16(9+7)+32+16
                out_data2 <= {9'd0,chain_addr,w_addr_32_w_1,SK_seed[64*(SD_len+0)-1:64*(SD_len-1)+48]};//16(9+7)+32+16                
            end                
            
            cnt <= 5'd1;
            ch_cnt <= 8'd1;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
            tmp_in_0_addr <= tmp_in_0_addr;
        end
        `ifdef PARAM_128
        5'd1: begin
            out_data1 <= SK_seed[64*(SD_len-1)+48-1:64*(SD_len-2)+48];
            out_data2 <= SK_seed[64*(SD_len-1)+48-1:64*(SD_len-2)+48];

            cnt <= 5'd27;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd27: begin
            out_data1 <= {SK_seed[64*(SD_len-2)+48-1:64*(SD_len-2)],16'h0000};//48+16
            out_data2 <= {SK_seed[64*(SD_len-2)+48-1:64*(SD_len-2)],16'h0000};//48+16
            
            cnt <= 5'd16;//wait state for hash done
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        `endif            
        `ifdef PARAM_192
        5'd1: begin
            out_data1 <= SK_seed[64*(SD_len-1)+48-1:64*(SD_len-2)+48];
            out_data2 <= SK_seed[64*(SD_len-1)+48-1:64*(SD_len-2)+48];

            cnt <= 5'd23;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd23: begin
            out_data1 <= SK_seed[64*(SD_len-2)+48-1:64*(SD_len-3)+48];
            out_data2 <= SK_seed[64*(SD_len-2)+48-1:64*(SD_len-3)+48];                
            
            cnt <= 5'd27;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd27: begin
            out_data1 <= {SK_seed[64*(SD_len-3)+48-1:64*(SD_len-3)],16'h0000};//48+16
            out_data2 <= {SK_seed[64*(SD_len-3)+48-1:64*(SD_len-3)],16'h0000};//48+16
            
            cnt <= 5'd16;//wait state for hash done
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end            
        `endif            
        `ifdef PARAM_256
        5'd1: begin
            out_data1 <= SK_seed[64*(SD_len-1)+48-1:64*(SD_len-2)+48];
            out_data2 <= SK_seed[64*(SD_len-1)+48-1:64*(SD_len-2)+48];

            cnt <= 5'd23;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd23: begin
            out_data1 <= SK_seed[64*(SD_len-2)+48-1:64*(SD_len-3)+48];
            out_data2 <= SK_seed[64*(SD_len-2)+48-1:64*(SD_len-3)+48]; 
            
            cnt <= 5'd24;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd24: begin
            out_data1 <= SK_seed[64*(SD_len-3)+48-1:64*(SD_len-4)+48];
            out_data2 <= SK_seed[64*(SD_len-3)+48-1:64*(SD_len-4)+48]; 
            
            cnt <= 5'd27;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd27: begin
            out_data1 <= {SK_seed[64*(SD_len-4)+48-1:64*(SD_len-4)],16'h0000};//48+16
            out_data2 <= {SK_seed[64*(SD_len-4)+48-1:64*(SD_len-4)],16'h0000};//48+16
            
            cnt <= 5'd16;//wait state for hash done
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end 
        `endif

        5'd2: begin// push PK_seed N-Bytes to hash_tile
            tl_cnt    <= 8'd1;
            out_data1 <= PK_seed[64*(SD_len+0)-1:64*(SD_len-1)];
            out_data2 <= PK_seed[64*(SD_len+0)-1:64*(SD_len-1)];
            
            cnt <= 5'd3;
            ch_cnt <= 8'd1;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        `ifdef PARAM_128
        5'd3: begin
            out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            
            if(FORS_prf_flag || PRF_flag) begin
                cnt <= 5'd28;//PRF
            end
            else begin
                cnt <= 5'd28;//F or T_L
            end
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end   
        `endif            
        `ifdef PARAM_192
        5'd3: begin
            out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            
            cnt <= 5'd25;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd25: begin
            out_data1 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            out_data2 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            
            if(FORS_prf_flag || PRF_flag) begin
                cnt <= 5'd28;//PRF
            end
            else begin
                cnt <= 5'd28;//F or T_L
            end
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        `endif
        `ifdef PARAM_256
        5'd3: begin
            out_data1 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            out_data2 <= PK_seed[64*(SD_len-1)-1:64*(SD_len-2)];
            
            cnt <= 5'd25;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd25: begin
            out_data1 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            out_data2 <= PK_seed[64*(SD_len-2)-1:64*(SD_len-3)];
            
            cnt <= 5'd26;
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        5'd26: begin
            out_data1 <= PK_seed[64*(SD_len-3)-1:64*(SD_len-4)];
            out_data2 <= PK_seed[64*(SD_len-3)-1:64*(SD_len-4)];
            
            if(FORS_prf_flag || PRF_flag) begin
                cnt <= 5'd28;//PRF
            end
            else begin
                cnt <= 5'd28;//F or T_L
            end
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;
        end
        `endif
        5'd28: begin//zero padding
            out_data1 <= 64'd0;
            out_data2 <= 64'd0;

            `ifdef PARAM_128
            if(zp_cnt==(3'd7-SD_len)) begin
                cnt <= 5'd4;
                zp_cnt <= 0;
            end
            else begin
                cnt <= cnt;
                zp_cnt <= zp_cnt + 1;
            end
            `else
            if(zp_cnt==(3'd7-SD_len) && (opcode!=3'd0 && opcode!=3'd7)) begin    
                cnt <= 5'd4;
                zp_cnt <= 0;
            end
            else if(zp_cnt==(4'd15-SD_len)) begin
                cnt <= 5'd4;
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
        5'd4: begin//ADRS start
            out_data1 <= {layer_addr[8-1:0],tree_addr[64-1:8]};//8+56
            out_data2 <= {layer_addr[8-1:0],tree_addr[64-1:8]};
            out_valid <= 1'b1;

            `ifdef PARAM_128
            if(i_mode_flag1) begin
                tl_cnt    <= 8'd1;
                ch_cnt <= 8'd1;
                out_addr <= 8'd8;
            end
            else begin
                out_addr <= out_addr + 1'b1;
            end  
            `else
            if(i_mode_flag2 && (mode==2'd3 || opcode==3'd0)) begin
                tl_cnt    <= 8'd1;
                ch_cnt <= 8'd1;
                out_addr <= 8'd16;
            end
            else if(i_mode_flag1 && (mode!=2'd3 && opcode!=3'd0)) begin
                tl_cnt    <= 8'd1;
                ch_cnt <= 8'd1;
                out_addr <= 8'd8;
            end
            else begin
                out_addr <= out_addr + 1'b1;
            end                  
            `endif              

            //select type(cnt: 8) or type_T_L(cnt: 17)
            if(mode==2'd3) begin
                cnt <= 5'd17; // T_L only
                `ifdef PARAM_128
                tmp_in_0_addr <= 12'd4;
                `endif
                `ifdef PARAM_192
                tmp_in_0_addr <= 12'd6;
                `endif
                `ifdef PARAM_256
                tmp_in_0_addr <= 12'd8;
                `endif
            end
            else if(opcode==3'd0) begin
                cnt <= 5'd17; // T_L only
                tmp_in_0_addr <= tmp_in_0_addr;
            end
            else begin
                cnt <= 5'd5; //mode 0,1
            end                
        end
        5'd5: begin//
            out_data1 <= {tree_addr[8-1:0],type[8-1:0],node_addr_w,16'd0};//8+8+32+16
            out_data2 <= {tree_addr[8-1:0],type[8-1:0],node_addr_w,16'd0};
            out_valid <= 1'b1;
            out_addr <= out_addr + 1'b1;

            if(FORS_prf_flag) begin
                cnt <= 5'd6;
            end
            else if(PRF_flag) begin
                cnt <= 5'd6;
            end
            else begin
                cnt <= 5'd12; //jump to cnt 12
            end
            
            if(PRF_flag || FORS_prf_flag) begin
                tmp_in_0_addr <= tmp_in_0_addr;
            end
            else begin
                if(i_sig_mode==1'b1 && mode==2'd0) begin
                    write_tmp_valid <= 1'b1;
                    `ifdef PARAM_128
                    tmp_in_0_addr <= (chain_cnt - 1) << 1;
                    `endif
                    `ifdef PARAM_192
                    tmp_in_0_addr <= ((chain_cnt - 1) << 1) + (chain_cnt - 1);
                    `endif
                    `ifdef PARAM_256
                    tmp_in_0_addr <= (chain_cnt - 1) << 2;
                    `endif
                end
                else begin
                    tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
                end
            end
        end 
        5'd12: begin
            if(mode==2'd0) begin
                if(i_sig_mode==1'b1) begin
                    out_data1 <= {9'd0,chain_addr,28'd0,in_w_cnt1,i_sig_mem_out[64-1:48]};//16(9+7)+32(28+4)+16
                    out_data2 <= {9'd0,chain_addr,28'd0,in_w_cnt1,i_sig_mem_out[64-1:48]};//16(9+7)+32(28+4)+16
                    tmp_reg_0 <= i_sig_mem_out[48-1:0];
                    tmp_reg_1 <= i_sig_mem_out[48-1:0];
                end
                else begin
                    out_data1 <= {9'd0,chain_addr,w_addr_32_w,tmp_out_0[64-1:48]};//16(9+7)+32+16
                    out_data2 <= {9'd0,(chain_addr + 1'b1),w_addr_32_w,tmp_out_1[64-1:48]};//16(9+7)+32+16
                    tmp_reg_0 <= tmp_out_0[48-1:0];
                    tmp_reg_1 <= tmp_out_1[48-1:0];
                end
            end
            else if(FORS_prf_flag || i_sig_mode)begin //mode==1
                out_data1 <= {9'd0,chain_addr,w_addr2_32_w,i_sig_mem_out[64-1:48]};//16(9+7)+32+16
                out_data2 <= {9'd0,chain_addr,w_addr2_32_w,i_sig_mem_out[64-1:48]};//16(9+7)+32+16
                tmp_reg_0 <= i_sig_mem_out[48-1:0];
                tmp_reg_1 <= i_sig_mem_out[48-1:0];
            end
            else begin //mode==1
                out_data1 <= {9'd0,chain_addr,w_addr_32_w,tmp_out_0[64-1:48]};//16(9+7)+32+16
                out_data2 <= {9'd0,chain_addr,w_addr_32_w_1,tmp_out_1[64-1:48]};//16(9+7)+32+16      
                tmp_reg_0 <= tmp_out_0[48-1:0];          
                tmp_reg_1 <= tmp_out_1[48-1:0];          
            end                 

            out_valid <= 1'b1;
            out_addr  <= out_addr + 1'b1;
            cnt    <= 5'd13;

            if(i_sig_mode==1'b1 && mode==2'd0) begin
                if(tmp_in_0_wr_en==1'b1) begin
                    tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
                end
                else begin
                    tmp_in_0_addr <= tmp_in_0_addr;
                end
            end
            else begin
                tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
            end
        end
        5'd13: begin//
            if(i_sig_mode==1'b0) begin
                out_data1 <= {tmp_reg_0,tmp_out_0[64-1:48]};//48+16
                out_data2 <= {tmp_reg_1,tmp_out_1[64-1:48]};//48+16    
                tmp_reg_0 <= tmp_out_0[48-1:0];
                tmp_reg_1 <= tmp_out_1[48-1:0];
            end
            else begin
                out_data1 <= {tmp_reg_0,i_sig_mem_out[64-1:48]};//48+16
                out_data2 <= {tmp_reg_1,i_sig_mem_out[64-1:48]};//48+16    
                tmp_reg_0 <= i_sig_mem_out[48-1:0];
                tmp_reg_1 <= i_sig_mem_out[48-1:0];                       
            end            

            out_valid <= 1'b1;
            out_addr  <= out_addr + 1'b1;

            if(ch_cnt == (CH_len >> 1)) begin
                cnt         <= 5'd15; //jump to cnt 15
                ch_cnt      <= 8'd1;

                if(i_sig_mode==1'b1 && mode==2'd0 && tmp_in_0_wr_en==1'b1) begin
                    tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
                end
                else begin
                    tmp_in_0_addr <= tmp_in_0_addr;
                end
            end
            else begin
                cnt    <= cnt;
                ch_cnt <= ch_cnt + 1'b1;

                if(i_sig_mode==1'b1 && mode==2'd0) begin
                    if(tmp_in_0_wr_en==1'b1) begin
                        tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
                    end
                    else begin
                        tmp_in_0_addr <= tmp_in_0_addr;
                    end
                end
                else begin
                    tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
                end
            end                       
        end          
        5'd15: begin//
            out_data1 <= {tmp_reg_0,16'd0};//48+16
            out_data2 <= {tmp_reg_1,16'd0};//48+16

            out_valid <= 1'b1;
            cnt       <= 5'd16;
            out_addr  <= out_addr + 1'b1;

            if(i_sig_mode==1'b1 && mode==2'd0) begin
                write_tmp_valid <= 1'b0;
                tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
            end         
        end
        5'd17: begin//17
            out_data1 <= {tree_addr[8-1:0],type_T_L[8-1:0],node_addr_w,16'd0};//8+8+32+16
            out_data2 <= {tree_addr[8-1:0],type_T_L[8-1:0],node_addr_w,16'd0};//8+8+32+16
            out_valid <= 1'b1;
            cnt <= 5'd19; //jump to cnt 19
            out_addr <= out_addr + 1'b1;

            tmp_in_0_addr <= tmp_in_0_addr + 1'b1;//
        end
        5'd19: begin//19
            out_data1 <= {48'd0,tmp_out_0[64-1:48]};//48+16
            out_data2 <= {48'd0,tmp_out_1[64-1:48]};//48+16    
            tmp_reg_0 <= tmp_out_0[48-1:0];
            tmp_reg_1 <= tmp_out_1[48-1:0]; 
            out_valid <= 1'b1;
            cnt <= 5'd20;
            out_addr <= out_addr + 1'b1;
            tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
        end
        5'd20: begin//
            out_data1 <= {tmp_reg_0,tmp_out_0[64-1:48]};//48+16
            out_data2 <= {tmp_reg_1,tmp_out_1[64-1:48]};//48+16    
            tmp_reg_0 <= tmp_out_0[48-1:0];
            tmp_reg_1 <= tmp_out_1[48-1:0]; 
            out_valid <= 1'b1;

            if((tl_cnt == (TL_k-1)) && mode==2'd3) begin
                cnt    <= 5'd21;
                tl_cnt <= 8'd1;
            end
            else if(tl_cnt == (TL_len-1)) begin
                cnt    <= 5'd21;
                tl_cnt <= 8'd1;
            end
            else begin
                cnt    <= cnt;
                tl_cnt <= tl_cnt + 1'b1;
            end
            out_addr      <= out_addr + 1'b1;
            tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
        end            
        5'd21: begin//
            out_data1 <= {tmp_reg_0,16'd0};//48+16
            out_data2 <= {tmp_reg_1,16'd0};//48+16    
            out_valid <= 1'b1;
            cnt <= 5'd22;
            out_addr      <= out_addr + 1'b1;
        end
        5'd16: begin
            out_data1 <= 32'd0;
            out_data2 <= 32'd0;
            out_valid <= 1'b0;

            if(w_cnt != 12'd0 && w_cnt <= WC) begin
                if(hash_done_1d && chain_cnt == CC && w_cnt == 4'd15) begin
                    tmp_in_0_addr <= 10'd0;
                end
                else if(!hash_done_1d && tmp_in_0_wr_en) begin
                    tmp_in_0_addr <= tmp_in_0_addr + 1'b1;
                end
                `ifdef PARAM_128
                else begin
                    if(i_sig_mode==1'b1 && mode==2'd0) begin
                        tmp_in_0_addr <= (chain_cnt - 1) << 1;
                    end
                    else begin
                        tmp_in_0_addr <= (chain_cnt >> 1) << 2;
                    end
                end
                `endif
                `ifdef PARAM_192
                else begin
                    if(i_sig_mode==1'b1 && mode==2'd0) begin
                        tmp_in_0_addr <= ((chain_cnt - 1) << 1) + (chain_cnt - 1);
                    end
                    else begin
                        tmp_in_0_addr <= ((chain_cnt >> 1) << 2) + ((chain_cnt >> 1) << 1);
                    end
                    
                end
                `endif
                `ifdef PARAM_256
                else begin
                    if(i_sig_mode==1'b1 && mode==2'd0) begin
                        tmp_in_0_addr <= (chain_cnt - 1) << 2;
                    end
                    else begin
                        tmp_in_0_addr <= (chain_cnt >> 1) << 3;
                    end
                end
                `endif
            end
            else begin
                tmp_in_0_addr <= tmp_in_0_addr;
            end               

            if(hash_done_1d) begin
                if(w_cnt == WC && mode==2'd0) begin //mode 0
                    if(chain_cnt == CC) begin //T_L start
                        out_addr <= 8'd0 - 1;

                        `ifdef PARAM_128
                        if(i_mode_flag1) begin
                            cnt <= 5'd4;//start from ADRS
                        end
                        else begin
                            cnt <= 5'd2;//start from PK.seed
                        end
                        `else
                        if(i_mode_flag2) begin
                            cnt <= 5'd4;//start from ADRS
                        end
                        else begin
                            cnt <= 5'd2;//start from PK.seed
                        end
                        `endif                            
                    end
                    else begin //PRF 
                        out_addr <= 8'd0 - 1;

                        if(i_mode_flag1) begin
                            cnt <= 5'd4;//start from ADRS
                        end
                        else begin
                            cnt <= 5'd2;//start from PK.seed
                        end                          
                    end
                end                    
                else if(PRF_flag) begin //PRF->F
                    if(FORS_prf_flag) begin
                        out_addr <= 8'd0 - 1;

                        if(i_mode_flag1) begin
                            cnt <= 5'd4;//start from ADRS
                        end
                        else begin
                            cnt <= 5'd2;//start from PK.seed
                        end                            
                    end
                    else begin
                        if(i_mode_flag1) begin
                            cnt <= 5'd4;//start from ADRS
                        end
                        else begin
                            cnt <= 5'd28;//SHA2 zero padding state
                        end                              
                        `ifdef PARAM_128
                        out_addr <= 8'd1;
                        `endif
                        `ifdef PARAM_192
                        out_addr <= 8'd2;
                        `endif
                        `ifdef PARAM_256
                        out_addr <= 8'd3;
                        `endif
                    end
                end
                else begin //F->F
                    if(mode == 2'd1) begin
                        //FORS leaf node gen
                        cnt      <= 5'd0;
                        out_addr <= 8'd0-1;                           
                    end
                    else begin
                        //WOTS pk gen
                        cnt <= 5'd16;//F_iter

                        `ifdef PARAM_128
                        out_addr <= 8'd4;
                        `endif
                        `ifdef PARAM_192
                        out_addr <= 8'd5;
                        `endif
                        `ifdef PARAM_256
                        out_addr <= 8'd6;
                        `endif
                    end
                end
            end
            else begin
                cnt <= cnt;
                out_addr <= out_addr;
            end
        end     
        5'd22: begin
            out_data1 <= 64'd0;
            out_data2 <= 64'd0;
            out_valid <= 1'b0;
            tmp_in_0_addr <= tmp_in_0_addr;              

            if(hash_done_1d) begin //T_L end
                cnt       <= 5'd0;
                out_addr  <= 8'd0-1;
            end
            else begin
                cnt       <= cnt;
                out_addr  <= out_addr;
            end
        end                   
        default: begin
            out_data1     <= 64'd0;
            out_data2     <= 64'd0;
            out_valid     <= 1'b0;
            tmp_in_0_addr <= tmp_in_0_addr;             
            cnt           <= cnt;
            out_addr      <= out_addr;
            tl_cnt        <= tl_cnt;
            ch_cnt        <= ch_cnt;    
        end
        endcase
    end
end
`endif

always@(cnt, PRF_flag, ch_cnt, hash_done_1d, w_cnt, WC, chain_cnt, CC) begin
    case(cnt)
    `ifdef SHAKE
    5'd10: begin
        if(PRF_flag) begin
            o_sig_read_mem_r <= 1'b0;            
        end
        else begin
            o_sig_read_mem_r <= 1'b1;
        end
    end    
    `else
    5'd5: begin
        if(PRF_flag) begin
            o_sig_read_mem_r <= 1'b0;            
        end
        else begin
            o_sig_read_mem_r <= 1'b1;
        end
    end
    `endif
    5'd12: begin
        if(ch_cnt == (CH_len >> 1)) begin
            o_sig_read_mem_r <= 1'b0;
        end
        else begin
            o_sig_read_mem_r <= 1'b1;
        end
    end
    `ifdef SHA2
    5'd13: begin
        if(ch_cnt >= (CH_len >> 1)-1) begin
            o_sig_read_mem_r <= 1'b0;
        end
        else begin
            o_sig_read_mem_r <= 1'b1;
        end
    end
    `endif
    5'd16: begin
        if(hash_done_1d && w_cnt == WC && chain_cnt!=CC) begin
            o_sig_read_mem_r <= 1'b1;
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


assign data_in_flag0 = ((mode==2'd0 && chain_cnt==(CC+2)) || (i_sig_mode==1'b1 && mode==2'd0 && chain_cnt==(CC+1)) || (mode==2'd1 && opcode==3'd4)) ? 1'b1 : 1'b0;

always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        s_in_0_wr_en <= 1'b0;
        s_in_1_wr_en <= 1'b0;
    end
    else begin
        if(fsm_data_in_flag0 && data_in_flag0) begin
            s_in_0_wr_en <= 1'b1;
            s_in_1_wr_en <= 1'b1;
        end
        else begin
            s_in_0_wr_en <= 1'b0;
            s_in_1_wr_en <= 1'b0;
        end
    end
end


assign data_in_flag1 = (!(skip_flag==1'b1 && i_sig_mode==1'b1 && mode==2'd0)) ? 1'b1 : 1'b0;

//W&R data to/from mem for PRF and F in WOTS
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        tmp_in_0_wr_en <= 1'b0;
        tmp_in_1_wr_en <= 1'b0;
    end
    else begin
        if(fsm_data_in_flag0 && data_in_flag1) begin
            tmp_in_0_wr_en <= 1'b1;
            tmp_in_1_wr_en <= 1'b1;
        end
        else if(write_tmp_valid) begin
            tmp_in_0_wr_en <= 1'b1;
            tmp_in_1_wr_en <= 1'b0;
        end
        else begin
            tmp_in_0_wr_en <= 1'b0;
            tmp_in_1_wr_en <= 1'b0;
        end
    end
end


endmodule
