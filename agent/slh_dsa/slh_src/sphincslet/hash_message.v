module hash_message
#(
parameter parameter_set = "128s",
parameter WD = //address bit for max data length
    (parameter_set == "128s") ? 7:
    (parameter_set == "128f") ? 7:
    (parameter_set == "192s") ? 8:
    (parameter_set == "192f") ? 8:
    (parameter_set == "256s") ? 9:
    (parameter_set == "256f") ? 9: 9,
parameter LEAF_IDX_WD = 
    (parameter_set == "128s") ? 9:
    (parameter_set == "128f") ? 3:
    (parameter_set == "192s") ? 9:
    (parameter_set == "192f") ? 3:
    (parameter_set == "256s") ? 8:
    (parameter_set == "256f") ? 4: 4,
parameter DIGEST_LEN = 
    (parameter_set == "128s") ? 3:
    (parameter_set == "128f") ? 4:
    (parameter_set == "192s") ? 4:
    (parameter_set == "192f") ? 5:
    (parameter_set == "256s") ? 5:
    (parameter_set == "256f") ? 5: 5,
parameter SD_len = 
    (parameter_set == "128s") ? 2:
    (parameter_set == "128f") ? 2:
    (parameter_set == "192s") ? 3:
    (parameter_set == "192f") ? 3:
    (parameter_set == "256s") ? 4:
    (parameter_set == "256f") ? 4: 2    
)
(
input wire clk,
input wire rstn,

output wire  [3-1:0] o_opcode,
input  wire          i_sig_mode,
input  wire          i_hm_mode,
input  wire          i_hm_start,
output wire          o_h_start,
output wire          o_hm_done,
output wire          o_PRF_msg_flag,
output wire          o_H_msg_flag,
input  wire          msg_w_start,
input  wire          root_c_start,
input  wire [64-1:0] i_rt_data,
input  wire          i_rt_valid,
output wire          o_c_flag,
`ifdef SHA2
output wire          o_first_flag,
`endif

input wire  [12-1:0] i_mlen,

input  wire [64-1:0] i_m1_data, 
output wire [64-1:0] o_m1_data, // output memory for H_msg, opcode=3
output wire  [9-1:0] o_m1_addr,
output wire          o_m1_valid,

output wire          o_sig_read,
input  wire [64-1:0] i_sig_data,

output wire [64-1:0]          o_tree,
output wire [LEAF_IDX_WD-1:0] o_leaf_idx,

input  wire [64-1:0] i_h0_data, //input from hash_tile
input  wire          i_h0_valid,

input  wire          i_h0_ready,
output wire [64-1:0] o_h0_data, // output to hash_tile
output wire [WD-1:0] o_h0_addr,
output wire          o_h0_valid
);

wire [12-1:0] mlen_adjust;
wire [9-1:0] mlen;
assign mlen_adjust = i_mlen + 3'd7;
assign mlen = mlen_adjust[12-1:3];// INT((i_mlen+7)/8)

wire [3-1:0] dlen;
assign dlen = DIGEST_LEN;

reg [5-1:0] cnt;

`ifdef SHAKE
    `ifdef PARAM_128
    reg         cnt2;
    `endif
    `ifdef PARAM_192
    reg [2-1:0] cnt2;
    `endif
    `ifdef PARAM_256
    reg [2-1:0] cnt2;
    `endif
`else
    `ifdef PARAM_128
    reg [2-1:0] cnt2;
    `endif
    `ifdef PARAM_192
    reg [3-1:0] cnt2;
    `endif
    `ifdef PARAM_256
    reg [3-1:0] cnt2;
    `endif
`endif
reg [9-1:0] cntm;

reg [3-1:0] opcode;
reg         h_start;

reg [64-1:0] m1_data;
reg  [9-1:0] m1_addr;
reg          m1_valid;

reg [64-1:0] tree;
reg [LEAF_IDX_WD-1:0] leaf_idx;

reg [64-1:0] h0_data;
reg [WD-1:0] h0_addr;
reg          h0_valid;

reg hm_start_d;
reg hm_mode_d;

reg bw_flag;
reg hm_done;

reg PRF_msg_flag;
reg H_msg_flag;
reg sig_read;
reg c_flag;
`ifdef SHA2
reg first_flag;
reg H_iter;
`endif

assign o_opcode       = opcode;
assign o_h_start      = h_start;
assign o_hm_done      = hm_done;
assign o_PRF_msg_flag = PRF_msg_flag;
assign o_H_msg_flag   = H_msg_flag;
assign o_sig_read     = sig_read;
assign o_c_flag       = c_flag;
`ifdef SHA2
assign o_first_flag   = first_flag;
`endif

assign o_m1_data  = m1_data;
assign o_m1_addr  = m1_addr;
assign o_m1_valid = m1_valid;

assign o_tree     = tree;
assign o_leaf_idx = leaf_idx;

assign o_h0_data  = h0_data;
assign o_h0_addr  = h0_addr;
assign o_h0_valid = h0_valid;

`ifdef SHAKE
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        cnt <= 5'd0;
        `ifdef PARAM_128
        cnt2 <= 1'b0;
        `endif
        `ifdef PARAM_192
        cnt2 <= 2'd0;
        `endif
        `ifdef PARAM_256
        cnt2 <= 2'd0;
        `endif
        cntm <= 9'd0;

        opcode <= 3'd0;
        h_start <= 1'b0;
        hm_done <= 1'b0;

        m1_data <= 64'd0;
        m1_addr <= 9'd0;
        m1_valid <= 1'b0;

        tree <= 64'd0;
        leaf_idx <= {{1'b0}*LEAF_IDX_WD};

        h0_data <= 64'd0;
        h0_addr <= {{1'b0}*WD};
        h0_valid <= 1'b0;

        hm_start_d <= 1'b0;
        bw_flag <= 1'b0;

        PRF_msg_flag <= 1'b0;
        H_msg_flag <= 1'b0;
        sig_read <= 1'b0;
        c_flag <= 1'b0;
    end
    else begin
        hm_start_d <= i_hm_start;
        hm_mode_d  <= i_hm_mode;

        case(cnt)
        5'd0: begin
            hm_done <= 1'b0;      

            h0_data <= 64'd0;
            h0_addr <= 9'd0;
            h0_valid <= 1'b0;

            if(hm_start_d && !hm_mode_d) begin
                cnt <= 5'd31;
                opcode <= 3'd5;//PRF_msg
                m1_addr <= 9'd0;
                h_start <= 1'b1;
                PRF_msg_flag <= 1'b1;
            end
            else if(hm_start_d && hm_mode_d) begin
                cnt <= 5'd30;
                opcode <= 3'd3;//H_msg
                `ifdef PARAM_128
                m1_addr <= 9'd4;
                `endif
                `ifdef PARAM_192
                m1_addr <= 9'd6;
                `endif
                `ifdef PARAM_256
                m1_addr <= 9'd8;
                `endif
                sig_read <= 1'b1;
                h_start <= 1'b1;
                H_msg_flag <= 1'b1;    
            end
            else if(msg_w_start) begin
                cnt <= 5'd13;
                `ifdef PARAM_128
                m1_addr <= 9'd10;//10=N*5=2*5
                `endif
                `ifdef PARAM_192
                m1_addr <= 9'd15;//15=N*5=3*5
                `endif
                `ifdef PARAM_256
                m1_addr <= 9'd20;//20=N*5=4*5
                `endif
                PRF_msg_flag <= 1'b1;
            end
            else if(root_c_start) begin
                cnt <= 5'd15;
                `ifdef PARAM_128
                m1_addr <= 9'd8;//8=N*4=2*4
                `endif
                `ifdef PARAM_192
                m1_addr <= 9'd12;//12=N*4=3*4
                `endif
                `ifdef PARAM_256
                m1_addr <= 9'd16;//16=N*4=4*4
                `endif
            end
            else begin
                m1_addr <= 9'd0;
                PRF_msg_flag <= 1'b0;
                H_msg_flag <= 1'b0;
            end
        end
        5'd31: begin
            m1_addr <= m1_addr + 1;
            h0_data <= i_m1_data;
            h_start <= 1'b0;
            cnt <= 5'd1;
        end
        5'd1: begin //push sk_prf 16 Bytes
            m1_addr <= m1_addr + 1;
            h0_data <= i_m1_data;
            h0_valid <= 1'b1;

            h_start <= 1'b0;

            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd2;
                h0_addr <= h0_addr + 1;
            end
            else begin
                cnt2 <= 1'b1;
                h0_addr <= h0_addr;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd2;
                h0_addr <= h0_addr + 1;
            end
            else if(cnt2==2'd1) begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr + 1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd2;
                h0_addr <= h0_addr + 1;
            end
            else if(cnt2==2'd1 || cnt2==2'd2) begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr + 1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr;
            end
            `endif
        end
        5'd2: begin //push optrand 16 Bytes
            h0_data <= i_m1_data;
            h0_addr <= h0_addr + 1;
            h0_valid <= 1'b1;

            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd3;
                m1_addr <= m1_addr + 1;
            end
            else begin
                cnt2 <= 1'b1;
                m1_addr <= m1_addr + 7;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd3;
                m1_addr <= m1_addr + 1;
            end
            else if(cnt2==2'd1) begin
                cnt2 <= cnt2 + 2'd1;
                m1_addr <= m1_addr + 10;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
                m1_addr <= m1_addr + 1;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd3;
                m1_addr <= m1_addr + 1;
            end
            else if(cnt2==2'd2) begin
                cnt2 <= cnt2 + 2'd1;
                m1_addr <= m1_addr + 13;
            end
            else if(cnt2==2'd1) begin
                cnt2 <= cnt2 + 2'd1;
                m1_addr <= m1_addr + 1;
            end            
            else begin
                cnt2 <= cnt2 + 2'd1;
                m1_addr <= m1_addr + 1;
            end
            `endif
        end
        5'd3: begin //push msg 33 Bytes //variable length
            if(bw_flag) begin
                `ifdef PARAM_128
                if(cnt2 && !i_h0_ready) begin
                    m1_addr <= m1_addr + 1;
                    bw_flag <= 1'b0;
                    cnt2 <= 1'b0;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2 <= 1'b1;
                end
                `else
                if(cnt2[0] && !i_h0_ready) begin
                    m1_addr <= m1_addr + 1;
                    bw_flag <= 1'b0;
                    cnt2[0] <= 1'b0;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2[0] <= 1'b1;
                end                
                `endif

                h0_data <= i_m1_data;
                h0_addr <= h0_addr;
                h0_valid <= 1'b0;
            end        
            else if(i_h0_ready) begin
                cnt <= 5'd29;
                h0_valid <= 1'b0;
            end
            else begin
                m1_addr <= m1_addr + 1;
                h0_data <= i_m1_data;
                h0_addr <= h0_addr + 1;
                h0_valid <= 1'b1;
                if(cntm==mlen-1) begin
                    cnt <= 5'd29;
                end
                else begin
                    cntm <= cntm + 9'd1;
                end
            end
        end
        5'd29: begin
            h0_valid <= 1'b0;
            if(i_h0_ready) begin
                bw_flag <= 1'b1;
                m1_addr <= m1_addr - 2'd2;
                h0_addr <= h0_addr - 1;
                cntm <= cntm - 9'd1;
                cnt <= 5'd3;
            end
            else begin
                cntm <= 9'd0;
                cnt <= 5'd4;
                `ifdef PARAM_128
                m1_addr <= 9'd4;
                `endif
                `ifdef PARAM_192
                m1_addr <= 9'd6;
                `endif
                `ifdef PARAM_256
                m1_addr <= 9'd8;
                `endif                
            end
        end
        5'd4: begin //if hash is done, pull R 16 Bytes
            h0_data <= 64'd0;
            h0_addr <= 6'd0;
            h0_valid <= 1'b0;
            //write to m1
            if(i_h0_valid) begin
                m1_data <= i_h0_data;
                m1_valid <= 1'b1;

                `ifdef PARAM_128
                if(cnt2) begin
                    m1_addr <= m1_addr + 1; 
                    cnt2 <= 1'b0;
                    cnt <= 5'd5;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2 <= 1'b1;
                end
                `endif

                `ifdef PARAM_192
                if(cnt2==2'd2) begin
                    m1_addr <= m1_addr + 1; 
                    cnt2 <= 2'd0;
                    cnt <= 5'd5;
                end
                else if(cnt2==2'd1) begin
                    m1_addr <= m1_addr + 1; 
                    cnt2 <= cnt2 + 2'd1;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2 <= cnt2 + 2'd1;
                end
                `endif

                `ifdef PARAM_256
                if(cnt2==2'd3) begin
                    m1_addr <= m1_addr + 1; 
                    cnt2 <= 2'd0;
                    cnt <= 5'd5;
                end
                else if(cnt2==2'd1 || cnt2==2'd2) begin
                    m1_addr <= m1_addr + 1; 
                    cnt2 <= cnt2 + 2'd1;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2 <= cnt2 + 2'd1;
                end
                `endif
            end
            else begin
                m1_data <= 64'd0;
                m1_addr <= m1_addr;
                m1_valid <= 1'b0;
            end
        end
        5'd5: begin //start H_msg
            `ifdef PARAM_128
            m1_addr <= 9'd4;
            `endif
            `ifdef PARAM_192
            m1_addr <= 9'd6;
            `endif
            `ifdef PARAM_256
            m1_addr <= 9'd8;
            `endif                
            h0_data <= 64'd0;
            h0_addr <= 9'd0;
            h0_valid <= 1'b0;
            m1_valid <= 1'b0;

            cnt <= 5'd30;
            opcode <= 3'd3;//H_msg
            h_start <= 1'b1;
            PRF_msg_flag <= 1'b0;
            H_msg_flag <= 1'b1;
        end      
        5'd30: begin
            m1_addr <= m1_addr + 1;
            h_start <= 1'b0;
            cnt <= 5'd6;
        end          
        5'd6: begin //push R 16 Bytes
            m1_addr <= m1_addr + 1;
            if(i_sig_mode==1'b1) begin
                h0_data <= i_sig_data;
            end
            else begin
                h0_data <= i_m1_data;
            end
            h0_valid <= 1'b1;
            h_start <= 1'b0;

            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd7;
                h0_addr <= h0_addr + 1;
            end
            else begin
                sig_read <= 1'b0;
                cnt2 <= 1'b1;
                h0_addr <= h0_addr;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd7;
                h0_addr <= h0_addr + 1;
            end
            else if(cnt2==2'd1) begin
                sig_read <= 1'b0;
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr + 1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd7;
                h0_addr <= h0_addr + 1;
            end
            else if(cnt2==2'd2) begin
                sig_read <= 1'b0;
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr + 1;
            end
            else if(cnt2==2'd1) begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr + 1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr;
            end
            `endif            
        end
        5'd7: begin //push PK_seed 16 Bytes
            m1_addr <= m1_addr + 1;
            h0_data <= i_m1_data;
            h0_addr <= h0_addr + 1;
            h0_valid <= 1'b1;

            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd8;
            end
            else begin
                cnt2 <= 1'b1;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd8;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd8;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif             
        end
        5'd8: begin //push PK_root 16 Bytes
            m1_addr <= m1_addr + 1;
            h0_data <= i_m1_data;
            h0_addr <= h0_addr + 1;
            h0_valid <= 1'b1;     

            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd9;
            end
            else begin
                cnt2 <= 1'b1;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd9;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd9;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif               
        end
        5'd9: begin //push msg 33 Bytes //variable length     
            if(bw_flag) begin
                `ifdef PARAM_128
                if(cnt2 && !i_h0_ready) begin
                    m1_addr <= m1_addr + 1;
                    bw_flag <= 1'b0;
                    cnt2 <= 1'b0;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2 <= 1'b1;
                end
                `else
                if(cnt2[0] && !i_h0_ready) begin
                    m1_addr <= m1_addr + 1;
                    bw_flag <= 1'b0;
                    cnt2[0] <= 1'b0;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2[0] <= 1'b1;
                end
                `endif
                h0_data <= i_m1_data;
                h0_addr <= h0_addr;
                h0_valid <= 1'b0;
            end        
            else if(i_h0_ready) begin
                cnt <= 5'd28;
                h0_valid <= 1'b0;
            end
            else begin
                m1_addr <= m1_addr + 1;
                h0_data <= i_m1_data;
                h0_addr <= h0_addr + 1;
                h0_valid <= 1'b1;
                if(cntm==mlen-1) begin
                    cnt <= 5'd28;
                end
                else begin
                    cntm <= cntm + 9'd1;
                end
            end            
        end
        5'd28: begin
            h0_valid <= 1'b0;
            if(i_h0_ready) begin
                bw_flag <= 1'b1;
                m1_addr <= m1_addr - 2'd2;
                h0_addr <= h0_addr - 1;
                cntm <= cntm - 9'd1;
                cnt <= 5'd9;
            end
            else begin
                m1_addr <= 9'd448-1;
                cntm <= 9'd0;
                cnt <= 5'd10;
            end
        end        
        5'd10: begin //if hash is done, pull digest 25 Bytes
            //write to DIGEST_MEM
            h0_data <= 64'd0;
            h0_addr <= 6'd0;
            h0_valid <= 1'b0;
            //write to m2
            if(i_h0_valid) begin
                if(cntm==dlen-1) begin

                    `ifdef PARAM_128S
                    tree[8*8-1:4*8] <= {10'd0,i_h0_data[3*8-1-2:0*8]};//128s: 54bit/7Byte
                    `endif 
                    `ifdef PARAM_128F
                    tree[8*8-1:1*8] <= {1'b0,i_h0_data[7*8-1-1:0*8]};//128f: 63bit/8Byte
                    `endif
                    `ifdef PARAM_192S
                    tree[8*8-1:5*8] <= {10'd0,i_h0_data[2*8-1-2:0*8]};//192s: 54bit/7Byte
                    `endif 
                    `ifdef PARAM_192F
                    tree[8*8-1:1*8] <= {1'b0,i_h0_data[7*8-1-1:0*8]};//192f: 63bit/8Byte
                    `endif
                    `ifdef PARAM_256S
                    tree[8*8-1:6*8] <= {8'd0,i_h0_data[1*8-1:0*8]};//256s: 56bit/7Byte
                    `endif 

                    m1_data <= i_h0_data;
                    m1_addr <= m1_addr + 1;
                    m1_valid <= 1'b1;                 
                    cntm <= 9'd0;
                    cnt <= 5'd11;
                end
                else begin
                    m1_data <= i_h0_data;
                    m1_addr <= m1_addr + 1;
                    m1_valid <= 1'b1;                         
                    cntm <= cntm + 9'd1;
                end                  
            end
            else begin
                m1_data <= 64'd0;
                m1_addr <= m1_addr;
                m1_valid <= 1'b0;
            end        
        end
        5'd11: begin //pull tree 8 Bytes & leaf_idx 1 Byte
            m1_addr <= 6'd0;
            m1_valid <= 1'b0; 
            if(i_h0_valid) begin
                
                `ifdef PARAM_128S
                tree[4*8-1:0*8] <= i_h0_data[8*8-1:4*8];//128s: 54bit/7Byte
                leaf_idx        <= i_h0_data[4*8-1-7:2*8];//128s: 9bit/2Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
                `endif
                `ifdef PARAM_128F
                tree[1*8-1:0*8] <= i_h0_data[8*8-1:7*8];//128f: 63bit/8Byte
                leaf_idx        <= i_h0_data[7*8-1-5:6*8];//128f: 3bit/1Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
                `endif
                `ifdef PARAM_192S
                tree[5*8-1:0*8] <= i_h0_data[8*8-1:3*8];//192s: 54bit/7Byte
                leaf_idx        <= i_h0_data[3*8-1-7:1*8];//192s: 9bit/2Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
                `endif
                `ifdef PARAM_192F
                tree[1*8-1:0*8] <= i_h0_data[8*8-1:7*8];//192f: 63bit/8Byte
                leaf_idx        <= i_h0_data[7*8-1-5:6*8];//192f: 3bit/1Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
                `endif        
                `ifdef PARAM_256S
                tree[6*8-1:0*8] <= i_h0_data[8*8-1:2*8];//256s: 56bit/7Byte
                leaf_idx        <= i_h0_data[2*8-1:1*8];//256s: 8bit/2Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
                `endif
                `ifdef PARAM_256F
                tree[8*8-1:0*8] <= i_h0_data[8*8-1:0*8];//256f: 64bit/8Byte
                cnt <= 5'd12;
                `endif                          

            end          
        end
        `ifdef PARAM_256F
        5'd12: begin //pull leaf_idx 1 Byte
            if(i_h0_valid) begin
                leaf_idx <= i_h0_data[8*8-1-4:7*8];//256f: 4bit/1Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
            end
        end
        `endif
        5'd13: begin
            m1_addr <= m1_addr + 1;
            cnt <= 5'd14;
        end        
        5'd14: begin
            m1_addr <= m1_addr + 1;
            h0_data <= i_m1_data;
            h0_valid <= 1'b1;
            if(cntm==mlen-1) begin
                cntm <= 9'd0;
                cnt <= 5'd0;
                hm_done <= 1'b1;
            end
            else begin
                cntm <= cntm + 9'd1;
            end
        end
        5'd15: begin
            if(i_rt_valid) begin
                m1_addr <= m1_addr + 1;
                m1_data <= i_rt_data;
                cnt <= 5'd16;
            end
        end        
        5'd16: begin
            m1_addr <= m1_addr + 1;
            m1_data <= i_rt_data;
            if(i_m1_data == m1_data) begin
                c_flag <= 1'b0;
            end
            else begin
                c_flag <= 1'b1;
            end
        
            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd0;
                hm_done <= 1'b1;
            end
            else begin
                cnt2 <= 1'b1;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd0;
                hm_done <= 1'b1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd0;
                hm_done <= 1'b1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif   
        end
        endcase
    end
end
`endif


`ifdef SHA2
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        cnt <= 5'd0;
        `ifdef PARAM_128
            cnt2 <= 2'd0;
        `endif
        `ifdef PARAM_192
            cnt2 <= 3'd0;
        `endif
        `ifdef PARAM_256
            cnt2 <= 3'd0;
        `endif
        cntm <= 9'd0;

        opcode <= 3'd0;
        h_start <= 1'b0;
        hm_done <= 1'b0;

        m1_data <= 64'd0;
        m1_addr <= 9'd0;
        m1_valid <= 1'b0;

        tree <= 64'd0;
        leaf_idx <= {{1'b0}*LEAF_IDX_WD};

        h0_data <= 64'd0;
        h0_addr <= {{1'b0}*WD};
        h0_valid <= 1'b0;

        hm_start_d <= 1'b0;
        bw_flag <= 1'b0;

        PRF_msg_flag <= 1'b0;
        H_msg_flag <= 1'b0;
        sig_read <= 1'b0;
        c_flag <= 1'b0;
        first_flag <= 1'b0;
        H_iter <= 1'b0;
    end
    else begin
        hm_start_d <= i_hm_start;
        hm_mode_d  <= i_hm_mode;

        case(cnt)
        5'd0: begin
            hm_done <= 1'b0;
            H_iter <= 1'b0;        

            h0_data <= 64'd0;
            h0_addr <= 9'd0;
            h0_valid <= 1'b0;

            if(hm_start_d && !hm_mode_d) begin
                cnt <= 5'd20;
                opcode <= 3'd5;//PRF_msg
                m1_addr <= 9'd0;
                h_start <= 1'b1;
                PRF_msg_flag <= 1'b1;
                first_flag <= 1'b1;
            end
            else if(hm_start_d && hm_mode_d) begin
                cnt <= 5'd23;
                opcode <= 3'd3;//H_msg
                `ifdef PARAM_128
                m1_addr <= 9'd4+4;
                `endif
                `ifdef PARAM_192
                m1_addr <= 9'd6+8;
                `endif
                `ifdef PARAM_256
                m1_addr <= 9'd8+8;
                `endif
                sig_read <= 1'b1;
                h_start <= 1'b1;
                H_msg_flag <= 1'b1;
                first_flag <= 1'b1;    
            end
            else if(msg_w_start) begin
                cnt <= 5'd13;
                `ifdef PARAM_128
                m1_addr <= 9'd10+4;//10=N*5=2*5
                `endif
                `ifdef PARAM_192
                m1_addr <= 9'd15+8;//15=N*5=3*5
                `endif
                `ifdef PARAM_256
                m1_addr <= 9'd20+8;//20=N*5=4*5
                `endif
                PRF_msg_flag <= 1'b1;
            end
            else if(root_c_start) begin
                cnt <= 5'd15;
                `ifdef PARAM_128
                m1_addr <= 9'd8+4;//8=N*4=2*4
                `endif
                `ifdef PARAM_192
                m1_addr <= 9'd12+8;//12=N*4=3*4
                `endif
                `ifdef PARAM_256
                m1_addr <= 9'd16+8;//16=N*4=4*4
                `endif
            end
            else begin
                m1_addr <= 9'd0;
                PRF_msg_flag <= 1'b0;
                H_msg_flag <= 1'b0;
            end
        end
        5'd20: begin           
            m1_addr <= m1_addr + 1;
            m1_valid <= 1'b0;
            h0_data <= i_m1_data;
            h_start <= 1'b0;
            cnt <= 5'd1;
        end
        5'd1: begin //push sk_prf 16 Bytes
            h0_valid <= 1'b1;
            h_start <= 1'b0;

            if(first_flag) begin
                h0_data <= i_m1_data ^ 64'h3636363636363636;
            end
            else begin
                h0_data <= i_m1_data ^ 64'h5C5C5C5C5C5C5C5C;
            end            

            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd21;
                h0_addr <= h0_addr + 1;
                if(first_flag) begin
                    m1_addr <= m1_addr;
                end
                else begin
                    m1_addr <= 9'd4;                 
                end
            end
            else begin
                cnt2 <= 1'b1;
                h0_addr <= h0_addr;
                m1_addr <= m1_addr + 1;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd21;
                h0_addr <= h0_addr + 1;

                if(first_flag) begin
                    m1_addr <= m1_addr;
                end
                else begin
                    m1_addr <= 9'd6;                  
                end                
            end
            else if(cnt2==2'd1) begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr + 1;
                m1_addr <= m1_addr + 1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr;
                m1_addr <= m1_addr + 1;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd21;
                h0_addr <= h0_addr + 1;

                if(first_flag) begin
                    m1_addr <= m1_addr;
                end
                else begin
                    m1_addr <= 9'd8;                  
                end  
            end
            else if(cnt2==2'd1 || cnt2==2'd2) begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr + 1;
                m1_addr <= m1_addr + 1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr;
                m1_addr <= m1_addr + 1;
            end
            `endif
        end
        5'd21: begin//zero padding
            h0_addr <= h0_addr + 1;
            h0_valid <= 1'b1;

            if(first_flag) begin
                h0_data <= 64'h3636363636363636;
            end
            else begin
                h0_data <= 64'h5C5C5C5C5C5C5C5C;
            end              

            `ifdef PARAM_128
            if(cntm==(9'd7-SD_len)) begin
                if(first_flag==1'b1) begin
                    cnt <= 5'd2;//push optrand
                end
                else begin
                    cnt <= 5'd18;//push tmp
                end
                cntm <= 0;
                m1_addr <= m1_addr + 1;
            end           
            else begin
                cnt <= cnt;
                cntm <= cntm + 1;
                m1_addr <= m1_addr;
            end
            `else
            if(cntm==(9'd15-SD_len)) begin
                if(first_flag==1'b1) begin
                    cnt <= 5'd2;//push optrand
                end
                else begin
                    cnt <= 5'd18;//push tmp
                end                
                cntm <= 0;
                m1_addr <= m1_addr + 1;
            end
            else begin
                cnt <= cnt;
                cntm <= cntm + 1;
                m1_addr <= m1_addr;
            end                
            `endif                
        end         
        5'd2: begin //push optrand 16 Bytes
            h0_data <= i_m1_data;
            h0_addr <= h0_addr + 1;
            h0_valid <= 1'b1;

            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd3;
                m1_addr <= m1_addr + 1;
            end
            else begin
                cnt2 <= 1'b1;
                m1_addr <= m1_addr + 7 + 4;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd3;
                m1_addr <= m1_addr + 1;
            end
            else if(cnt2==2'd1) begin
                cnt2 <= cnt2 + 2'd1;
                m1_addr <= m1_addr + 10 + 8;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
                m1_addr <= m1_addr + 1;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd3;
                m1_addr <= m1_addr + 1;
            end
            else if(cnt2==2'd2) begin
                cnt2 <= cnt2 + 2'd1;
                m1_addr <= m1_addr + 13 + 8;
            end
            else if(cnt2==2'd1) begin
                cnt2 <= cnt2 + 2'd1;
                m1_addr <= m1_addr + 1;
            end            
            else begin
                cnt2 <= cnt2 + 2'd1;
                m1_addr <= m1_addr + 1;
            end
            `endif
        end
        5'd3: begin //push msg 33 Bytes //variable length
            if(bw_flag) begin
                `ifdef PARAM_128
                if(cnt2[0] && !i_h0_ready) begin                    
                    m1_addr <= m1_addr + 1;
                    bw_flag <= 1'b0;
                    cnt2 <= 1'b0;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2 <= 1'b1;
                end
                `else
                if(cnt2[0] && !i_h0_ready) begin
                    m1_addr <= m1_addr + 1;
                    bw_flag <= 1'b0;
                    cnt2[0] <= 1'b0;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2[0] <= 1'b1;
                end                
                `endif
                h0_data <= i_m1_data;
                h0_addr <= h0_addr;
                h0_valid <= 1'b0;
            end        
            else if(i_h0_ready) begin
                cnt <= 5'd22;
                h0_valid <= 1'b0;
            end
            else begin
                m1_addr <= m1_addr + 1;
                h0_data <= i_m1_data;
                h0_addr <= h0_addr + 1;
                h0_valid <= 1'b1;
                if(cntm==mlen-1) begin
                    cnt <= 5'd22;
                end
                else begin
                    cntm <= cntm + 9'd1;
                end
            end
        end
        5'd18: begin //push tmp 32 Bytes
            h0_data <= i_m1_data;
            h0_addr <= h0_addr + 1;
            h0_valid <= 1'b1;

            `ifdef PARAM_128 // 32Byte output
                if(cnt2==2'd3) begin
                    cnt2 <= 2'd0;
                    cnt <= 5'd22;
                    m1_addr <= m1_addr + 1;
                end
                else if(cnt2==2'd2) begin
                    cnt2 <= cnt2 + 1;
                    m1_addr <= m1_addr + 13;
                end        
                else begin
                    cnt2 <= cnt2 + 1;
                    m1_addr <= m1_addr + 1;
                end
            `else // 64Byte output
                if(cnt2==3'd7) begin
                    cnt2 <= 3'd0;
                    cnt <= 5'd22;
                    m1_addr <= m1_addr + 1;
                end
                else if(cnt2==3'd6) begin
                    cnt2 <= cnt2 + 1;
                    m1_addr <= m1_addr + 13;
                end           
                else begin
                    cnt2 <= cnt2 + 1;
                    m1_addr <= m1_addr + 1;
                end
            `endif
        end        
        5'd22: begin
            h0_valid <= 1'b0;
            if(i_h0_ready) begin
                bw_flag <= 1'b1;
                m1_addr <= m1_addr - 2'd2;
                h0_addr <= h0_addr - 1;
                cntm <= cntm - 9'd1;
                cnt <= 5'd3;
            end
            else begin
                cntm <= 9'd0;
                if(first_flag) begin
                    cnt <= 5'd17;

                    `ifdef PARAM_128
                    m1_addr <= 9'd4;
                    `endif
                    `ifdef PARAM_192
                    m1_addr <= 9'd6;
                    `endif
                    `ifdef PARAM_256
                    m1_addr <= 9'd8;
                    `endif       
                end
                else begin
                    cnt <= 5'd4;

                    `ifdef PARAM_128
                    m1_addr <= 9'd4+4;
                    `endif
                    `ifdef PARAM_192
                    m1_addr <= 9'd6+8;
                    `endif
                    `ifdef PARAM_256
                    m1_addr <= 9'd8+8;
                    `endif                      
                end
            end
        end
        5'd17: begin//if hash is done, pull intermediate value N Bytes
            h0_data <= 64'd0;
            h0_addr <= 6'd0;
            h0_valid <= 1'b0;
            //write to m1
            if(i_h0_valid) begin
                m1_data <= i_h0_data;
                m1_valid <= 1'b1;

                `ifdef PARAM_128 // 32Byte tmp
                    if(cnt2==2'd3) begin
                        m1_addr <= m1_addr + 1; 
                        cnt2 <= 2'd0;
                        cnt <= 5'd19;
                    end
                    else if(cnt2==2'd1 || cnt2==2'd2) begin
                        m1_addr <= m1_addr + 1; 
                        cnt2 <= cnt2 + 2'd1;
                    end
                    else begin
                        m1_addr <= m1_addr;
                        cnt2 <= cnt2 + 2'd1;
                    end
                `else // 64Byte tmp
                    if(cnt2==3'd7) begin
                        m1_addr <= m1_addr + 1; 
                        cnt2 <= 3'd0;
                        cnt <= 5'd19;
                    end
                    else if(cnt2!=3'd0) begin
                        m1_addr <= m1_addr + 1; 
                        cnt2 <= cnt2 + 1;
                    end
                    else begin
                        m1_addr <= m1_addr;
                        cnt2 <= cnt2 + 1;
                    end                
                `endif
            end
            else begin
                m1_data <= 64'd0;
                m1_addr <= m1_addr;
                m1_valid <= 1'b0;
            end
        end               
        5'd19: begin//start second PRF_msg
            h0_data <= 64'd0;
            h0_addr <= 9'd0;
            h0_valid <= 1'b0;
            m1_valid <= 1'b0;

            if(first_flag==1'b1) begin
                cnt <= 5'd20;
                opcode <= 3'd5;//PRF_msg
                m1_addr <= 9'd0;
                h_start <= 1'b1;
                PRF_msg_flag <= 1'b1;
                first_flag <= 1'b0;
            end
            else begin
                cnt <= 5'd4;
            end
        end        
        5'd4: begin //if hash is done, pull R 16 Bytes
            h0_data <= 64'd0;
            h0_addr <= 6'd0;
            h0_valid <= 1'b0;
            //write to m1
            if(i_h0_valid) begin
                m1_data <= i_h0_data;
                m1_valid <= 1'b1;

                `ifdef PARAM_128
                if(cnt2[0]) begin                    
                    m1_addr <= m1_addr + 1; 
                    cnt2 <= 1'b0;
                    cnt <= 5'd5;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2 <= 1'b1;
                end
                `endif

                `ifdef PARAM_192
                if(cnt2==2'd2) begin
                    m1_addr <= m1_addr + 1; 
                    cnt2 <= 2'd0;
                    cnt <= 5'd5;
                end
                else if(cnt2==2'd1) begin
                    m1_addr <= m1_addr + 1; 
                    cnt2 <= cnt2 + 2'd1;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2 <= cnt2 + 2'd1;
                end
                `endif

                `ifdef PARAM_256
                if(cnt2==2'd3) begin
                    m1_addr <= m1_addr + 1; 
                    cnt2 <= 2'd0;
                    cnt <= 5'd5;
                end
                else if(cnt2==2'd1 || cnt2==2'd2) begin
                    m1_addr <= m1_addr + 1; 
                    cnt2 <= cnt2 + 2'd1;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2 <= cnt2 + 2'd1;
                end
                `endif
            end
            else begin
                m1_data <= 64'd0;
                m1_addr <= m1_addr;
                m1_valid <= 1'b0;
            end
        end
        5'd5: begin //start H_msg
            `ifdef PARAM_128
            m1_addr <= 9'd4+4;
            `endif
            `ifdef PARAM_192
            m1_addr <= 9'd6+8;
            `endif
            `ifdef PARAM_256
            m1_addr <= 9'd8+8;
            `endif                
            h0_data <= 64'd0;
            h0_addr <= 9'd0;
            h0_valid <= 1'b0;
            m1_valid <= 1'b0;

            cnt <= 5'd23;
            opcode <= 3'd3;//H_msg
            h_start <= 1'b1;
            PRF_msg_flag <= 1'b0;
            H_msg_flag <= 1'b1;
            first_flag <= 1'b1;
        end      
        5'd23: begin //buffer
            m1_addr <= m1_addr + 1;
            h_start <= 1'b0;
            cnt <= 5'd6;
        end          
        5'd6: begin //push R 16 Bytes
            m1_addr <= m1_addr + 1;
            if(i_sig_mode==1'b1) begin
                h0_data <= i_sig_data;
            end
            else begin
                h0_data <= i_m1_data;
            end
            h0_valid <= 1'b1;
            h_start <= 1'b0;

            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd7;
                h0_addr <= h0_addr + 1;
            end
            else begin
                sig_read <= 1'b0;
                cnt2 <= 1'b1;
                h0_addr <= h0_addr;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd7;
                h0_addr <= h0_addr + 1;
            end
            else if(cnt2==2'd1) begin
                sig_read <= 1'b0;
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr + 1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd7;
                h0_addr <= h0_addr + 1;
            end
            else if(cnt2==2'd2) begin
                sig_read <= 1'b0;
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr + 1;
            end
            else if(cnt2==2'd1) begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr + 1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
                h0_addr <= h0_addr;
            end
            `endif            
        end
        5'd7: begin //push PK_seed 16 Bytes
            m1_addr <= m1_addr + 1;
            h0_data <= i_m1_data;
            h0_addr <= h0_addr + 1;
            h0_valid <= 1'b1;

            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd8;
            end
            else begin
                cnt2 <= 1'b1;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd8;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd8;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif             
        end
        5'd8: begin //push PK_root 16 Bytes
            m1_addr <= m1_addr + 1;
            h0_data <= i_m1_data;
            h0_addr <= h0_addr + 1;
            h0_valid <= 1'b1;     

            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd9;
            end
            else begin
                cnt2 <= 1'b1;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd9;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd9;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif               
        end
        5'd9: begin //push msg 33 Bytes //variable length      

            if(bw_flag) begin
                `ifdef PARAM_128
                if(cnt2[0] && !i_h0_ready) begin
                    m1_addr <= m1_addr + 1;
                    bw_flag <= 1'b0;
                    cnt2 <= 1'b0;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2 <= 1'b1;
                end
                `else
                if(cnt2[0] && !i_h0_ready) begin
                    m1_addr <= m1_addr + 1;
                    bw_flag <= 1'b0;
                    cnt2[0] <= 1'b0;
                end
                else begin
                    m1_addr <= m1_addr;
                    cnt2[0] <= 1'b1;
                end
                `endif
                h0_data <= i_m1_data;
                h0_addr <= h0_addr;
                h0_valid <= 1'b0;
            end        
            else if(i_h0_ready) begin
                cnt <= 5'd24;
                h0_valid <= 1'b0;
            end
            else begin
                m1_addr <= m1_addr + 1;
                h0_data <= i_m1_data;
                h0_addr <= h0_addr + 1;
                h0_valid <= 1'b1;
                if(cntm==mlen-1) begin
                    cnt <= 5'd24;
                end
                else begin
                    cntm <= cntm + 9'd1;
                end
            end            
        end
        5'd24: begin
            h0_valid <= 1'b0;
            if(i_h0_ready) begin
                bw_flag <= 1'b1;
                m1_addr <= m1_addr - 2'd2;
                h0_addr <= h0_addr - 1;
                cntm <= cntm - 9'd1;
                cnt <= 5'd9;
            end
            else begin
                m1_addr <= 9'd4;
                cntm <= 9'd0;
                cnt <= 5'd25;//write tmp
            end
        end 
        5'd25: begin//if hash is done, pull intermediate value N Bytes
            h0_data <= 64'd0;
            h0_addr <= 6'd0;
            h0_valid <= 1'b0;
            //write to m1
            if(i_h0_valid) begin
                m1_data <= i_h0_data;
                m1_valid <= 1'b1;

                `ifdef PARAM_128 // 32Byte tmp
                    if(cnt2==2'd3) begin
                        m1_addr <= m1_addr + 1; 
                        cnt2 <= 2'd0;
                        cnt <= 5'd26;
                    end
                    else if(cnt2==2'd1 || cnt2==2'd2) begin
                        m1_addr <= m1_addr + 1; 
                        cnt2 <= cnt2 + 2'd1;
                    end
                    else begin
                        m1_addr <= m1_addr;
                        cnt2 <= cnt2 + 2'd1;
                    end
                `else // 64Byte tmp
                    if(cnt2==3'd7) begin
                        m1_addr <= m1_addr + 1; 
                        cnt2 <= 3'd0;
                        cnt <= 5'd26;
                    end
                    else if(cnt2!=3'd0) begin
                        m1_addr <= m1_addr + 1; 
                        cnt2 <= cnt2 + 1;
                    end
                    else begin
                        m1_addr <= m1_addr;
                        cnt2 <= cnt2 + 1;
                    end                
                `endif
            end
            else begin
                m1_data <= 64'd0;
                m1_addr <= m1_addr;
                m1_valid <= 1'b0;
            end
        end   
        5'd26: begin//start second H_msg
            h0_data <= 64'd0;
            h0_addr <= 9'd0;
            h0_valid <= 1'b0;
            m1_valid <= 1'b0;

            cnt <= 5'd27;
            opcode <= 3'd3;//H_msg
            m1_addr <= 9'd4;
            h_start <= 1'b1;
            first_flag <= 1'b0;
        end
        5'd27: begin           
            m1_addr <= m1_addr + 1;
            m1_valid <= 1'b0;
            h0_data <= i_m1_data;
            h_start <= 1'b0;
            cnt <= 5'd28;
        end        
        5'd28: begin //push tmp 32 Bytes
            h0_data <= i_m1_data;
            h0_addr <= h0_addr + 1;
            h0_valid <= 1'b1;

            `ifdef PARAM_128 // 32Byte output
                if(cnt2==2'd3) begin
                    cnt2 <= 2'd0;
                    cnt <= 5'd29;
                    m1_addr <= m1_addr + 1;
                end
                else if(cnt2==2'd2) begin
                    cnt2 <= cnt2 + 2'd1;
                    m1_addr <= m1_addr + 13;
                end
                else if(cnt2==2'd1) begin
                    cnt2 <= cnt2 + 2'd1;
                    m1_addr <= m1_addr + 1;
                end            
                else begin
                    cnt2 <= cnt2 + 2'd1;
                    m1_addr <= m1_addr + 1;
                end
            `else // 64Byte output
                if(cnt2==3'd7) begin
                    cnt2 <= 3'd0;
                    cnt <= 5'd29;
                    m1_addr <= m1_addr + 1;
                end
                else if(cnt2==3'd6) begin
                    cnt2 <= cnt2 + 1;
                    m1_addr <= m1_addr + 13;
                end           
                else begin
                    cnt2 <= cnt2 + 1;
                    m1_addr <= m1_addr + 1;
                end
            `endif
        end  
        5'd29: begin //push count 4 or 8 Bytes
            h0_addr <= h0_addr + 1;
            h0_valid <= 1'b1;
            m1_addr <= 9'd448-1;

            `ifdef PARAM_128 // 32Byte output
                if(H_iter==2'd1) begin
                    h0_data <= 64'h0000000100000000;
                    cnt2 <= 2'd0;
                    cnt <= 5'd11;
                end
                else begin
                    h0_data <= 64'h0000000000000000;
                    cnt2 <= 2'd0;
                    cnt <= 5'd10;
                end
            `else // 64Byte output
                    if(H_iter==1'b1) begin
                        h0_data <= 64'h0000000000000001;
                        cnt2 <= 2'd0;
                        cnt <= 5'd11;//
                    end
                    else begin
                        h0_data <= 64'h0000000000000000;
                        cnt2 <= 2'd0;
                        cnt <= 5'd10;
                    end
            `endif
        end                          
        5'd10: begin //if hash is done, pull digest 25 Bytes
            //write to DIGEST_MEM
            h0_data <= 64'd0;
            h0_addr <= 6'd0;
            h0_valid <= 1'b0;
            H_iter <= 1'b1;

            //write to m2
            if(i_h0_valid) begin
                if(cntm==dlen-1) begin

                    `ifdef PARAM_128S
                    tree[8*8-1:4*8] <= {10'd0,i_h0_data[3*8-1-2:0*8]};//128s: 54bit/7Byte
                    `endif 
                    `ifdef PARAM_128F
                    tree[8*8-1:1*8] <= {1'b0,i_h0_data[7*8-1-1:0*8]};//128f: 63bit/8Byte
                    `endif
                    `ifdef PARAM_192S
                    tree[8*8-1:5*8] <= {10'd0,i_h0_data[2*8-1-2:0*8]};//192s: 54bit/7Byte
                    `endif 
                    `ifdef PARAM_192F
                    tree[8*8-1:1*8] <= {1'b0,i_h0_data[7*8-1-1:0*8]};//192f: 63bit/8Byte
                    `endif
                    `ifdef PARAM_256S
                    tree[8*8-1:6*8] <= {8'd0,i_h0_data[1*8-1:0*8]};//256s: 56bit/7Byte
                    `endif 

                    m1_data <= i_h0_data;
                    m1_addr <= m1_addr + 1;
                    m1_valid <= 1'b1;                 
                    cntm <= 9'd0;
                    `ifdef PARAM_128F
                        cnt <= 5'd26; 
                    `else
                        cnt <= 5'd11; 
                    `endif
                    
                end               
                else begin
                    m1_data <= i_h0_data;
                    m1_addr <= m1_addr + 1;
                    m1_valid <= 1'b1;                         
                    cntm <= cntm + 9'd1;
                end                  
            end
            else begin
                m1_data <= 64'd0;
                m1_addr <= m1_addr;
                m1_valid <= 1'b0;
            end        
        end
        5'd11: begin //pull tree 8 Bytes & leaf_idx 1 Byte
            h0_data <= 64'd0;
            h0_addr <= 6'd0;
            h0_valid <= 1'b0;        
            m1_addr <= 6'd0;
            m1_valid <= 1'b0; 
            if(i_h0_valid) begin
                
                `ifdef PARAM_128S
                tree[4*8-1:0*8] <= i_h0_data[8*8-1:4*8];//128s: 54bit/7Byte
                leaf_idx        <= i_h0_data[4*8-1-7:2*8];//128s: 9bit/2Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
                `endif
                `ifdef PARAM_128F
                tree[1*8-1:0*8] <= i_h0_data[8*8-1:7*8];//128f: 63bit/8Byte
                leaf_idx        <= i_h0_data[7*8-1-5:6*8];//128f: 3bit/1Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
                `endif
                `ifdef PARAM_192S
                tree[5*8-1:0*8] <= i_h0_data[8*8-1:3*8];//192s: 54bit/7Byte
                leaf_idx        <= i_h0_data[3*8-1-7:1*8];//192s: 9bit/2Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
                `endif
                `ifdef PARAM_192F
                tree[1*8-1:0*8] <= i_h0_data[8*8-1:7*8];//192f: 63bit/8Byte
                leaf_idx        <= i_h0_data[7*8-1-5:6*8];//192f: 3bit/1Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
                `endif        
                `ifdef PARAM_256S
                tree[6*8-1:0*8] <= i_h0_data[8*8-1:2*8];//256s: 56bit/7Byte
                leaf_idx        <= i_h0_data[2*8-1:1*8];//256s: 8bit/2Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
                `endif
                `ifdef PARAM_256F
                tree[8*8-1:0*8] <= i_h0_data[8*8-1:0*8];//256f: 64bit/8Byte
                cnt <= 5'd12;
                `endif                          

            end          
        end
        `ifdef PARAM_256F
        5'd12: begin //pull leaf_idx 1 Byte
            if(i_h0_valid) begin
                leaf_idx <= i_h0_data[8*8-1-4:7*8];//256f: 4bit/1Byte
                cnt <= 5'd0;
                hm_done <= 1'b1;
            end
        end
        `endif
        5'd13: begin
            m1_addr <= m1_addr + 1;
            cnt <= 5'd14;
        end        
        5'd14: begin
            m1_addr <= m1_addr + 1;
            h0_data <= i_m1_data;
            h0_valid <= 1'b1;
            if(cntm==mlen-1) begin
                cntm <= 9'd0;
                cnt <= 5'd0;
                hm_done <= 1'b1;
            end
            else begin
                cntm <= cntm + 9'd1;
            end
        end
        5'd15: begin
            if(i_rt_valid) begin
                m1_addr <= m1_addr + 1;
                m1_data <= i_rt_data;
                cnt <= 5'd16;
            end
        end        
        5'd16: begin
            m1_addr <= m1_addr + 1;
            m1_data <= i_rt_data;
            if(i_m1_data == m1_data) begin
                c_flag <= 1'b0;
            end
            else begin
                c_flag <= 1'b1;
            end
        
            `ifdef PARAM_128
            if(cnt2) begin
                cnt2 <= 1'b0;
                cnt <= 5'd0;
                hm_done <= 1'b1;
            end
            else begin
                cnt2 <= 1'b1;
            end
            `endif

            `ifdef PARAM_192
            if(cnt2==2'd2) begin
                cnt2 <= 2'd0;
                cnt <= 5'd0;
                hm_done <= 1'b1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif

            `ifdef PARAM_256
            if(cnt2==2'd3) begin
                cnt2 <= 2'd0;
                cnt <= 5'd0;
                hm_done <= 1'b1;
            end
            else begin
                cnt2 <= cnt2 + 2'd1;
            end
            `endif   
        end
        endcase
    end
end
`endif 

endmodule