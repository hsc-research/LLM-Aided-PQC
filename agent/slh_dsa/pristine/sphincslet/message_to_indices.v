//param addr indices total
//       bit   bit     bit
//128s     4    12      16
//128f     6     6      12
//192s     5    14      19
//192f     6     8      14
//256s     5    14      19
//256f     6     9      15
`ifdef PARAM_128F
module message_to_indices
(
input  wire          clk,
input  wire          rstn,
input  wire          mti_start,
output wire          mti_next_start,
input  wire [64-1:0] i_data0,
output wire [ 4-1:0] o_raddr0,
output wire [15-1:0] o_data0,
output wire [ 6-1:0] o_waddr0,
output wire          o_valid0
);

reg   [4-1:0] mem_addr0;
wire [64-1:0] mem_out0;
reg  [48-1:0] tmp_reg0;
reg   [6-1:0] indices_in0;
reg   [6-1:0] indices_addr0;
reg           indices_wen0;
reg   [4-1:0] cnt;
reg   [4-1:0] next_cnt;
reg   [3-1:0] loop_cnt;
reg           mti_done;
reg   [4-1:0] mti_done_d;

assign mem_out0 = i_data0;
assign o_raddr0 = mem_addr0;
assign o_data0  = {indices_addr0,indices_in0};
assign o_waddr0 = indices_addr0;
assign o_valid0 = indices_wen0;
assign mti_next_start = mti_done_d[0];

//message_to_indices( )
//128f parameter
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        mem_addr0     <= 4'd0; 
        tmp_reg0      <= 48'd0;
        indices_in0   <= 6'd0;
        indices_addr0 <= 6'd0;
        indices_wen0  <= 1'b0;
        cnt           <= 4'd0;
        loop_cnt      <= 3'd0;
        next_cnt      <= 4'd0;
        mti_done      <= 1'b0;
        mti_done_d    <= 4'd0;
    end
    else begin
        mti_done_d <= {mti_done,mti_done_d[3:1]};
        case(cnt)
            4'd0: begin
                mem_addr0     <= 4'd0; 
                tmp_reg0      <= 48'd0;
                indices_in0   <= 6'd0;
                indices_addr0 <= 6'd0;
                indices_wen0  <= 1'b0;
                mti_done      <= 1'b0;
                if(mti_start) begin
                    cnt <= 4'd1;
                end
            end
            4'd1: begin
                mem_addr0 <= 4'd0; 
                indices_addr0 <= 6'd0-6'd1;
                cnt       <= 4'd2;
            end
            4'd2: begin
                mem_addr0 <= mem_addr0;
                cnt       <= 4'd3;
            end
            4'd3: begin
                mem_addr0 <= 4'd0; 
                //Read addr 0
                tmp_reg0 <= {mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                             mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd4;
            end
            4'd15: begin
                mem_addr0 <= mem_addr0;
                cnt       <= next_cnt;
            end            
            4'd4: begin
                mem_addr0 <= 4'd1; 
                //Read addr 0
                tmp_reg0[2*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd9;
            end
            4'd9: begin
                mem_addr0 <= 4'd1; 
                //Read addr 1
                tmp_reg0[6*8-1:2*8] <= {mem_out0[5*8-1:4*8],mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],
                                                                                mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd5;
            end            
            4'd5: begin
                mem_addr0 <= 4'd2; 
                //Read addr 1
                tmp_reg0[4*8-1:0] <= {mem_out0[1*8-1:0*8],
                                      mem_out0[2*8-1:1*8],mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd10;
            end
            4'd10: begin
                mem_addr0 <= 4'd2; 
                //Read addr 2
                tmp_reg0[6*8-1:4*8] <= {mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd6;
            end
            4'd6: begin
                mem_addr0 <= 4'd3; 
                //Read addr 2
                tmp_reg0 <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],mem_out0[3*8-1:2*8],
                             mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],mem_out0[6*8-1:5*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd7;
            end            
            4'd7: begin
                mem_addr0 <= 4'd0; 
                //Read addr 3
                tmp_reg0 <= {42'd0,mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd0;
            end
            4'd8: begin
                tmp_reg0      <= {6'd0,tmp_reg0[8*6-1:1*6]};
                indices_in0   <= tmp_reg0[1*6-1:0*6];
                indices_addr0 <= indices_addr0 + 6'd1;
                indices_wen0  <= 1'b1;

                if(loop_cnt==3'd7) begin
                    loop_cnt <= 3'd0;
                    cnt      <= next_cnt;
                    if(next_cnt==3'd0) begin
                        mti_done <= 1'b1;
                    end
                end
                else begin
                    loop_cnt <= loop_cnt + 3'd1;
                    cnt      <= cnt;
                end
            end
        endcase
    end 
end
endmodule
`endif

`ifdef PARAM_128S
module message_to_indices
(
input  wire          clk,
input  wire          rstn,
input  wire          mti_start,
output wire          mti_next_start,
input  wire [64-1:0] i_data0,
output wire [ 4-1:0] o_raddr0,
output wire [16-1:0] o_data0,
output wire [ 6-1:0] o_waddr0,
output wire          o_valid0
);

reg   [4-1:0] mem_addr0;
wire [64-1:0] mem_out0;
reg  [48-1:0] tmp_reg0;
reg  [12-1:0] indices_in0;
reg   [4-1:0] indices_addr0;
reg           indices_wen0;
reg   [4-1:0] cnt;
reg   [4-1:0] next_cnt;
reg   [3-1:0] loop_cnt;
reg           mti_done;
reg   [4-1:0] mti_done_d;

assign mem_out0 = i_data0;
assign o_raddr0 = mem_addr0;
assign o_data0  = {indices_addr0,indices_in0};
assign o_waddr0 = indices_addr0;
assign o_valid0 = indices_wen0;
assign mti_next_start = mti_done_d[0];

//message_to_indices( )
//128s parameter
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        mem_addr0     <= 4'd0;
        tmp_reg0      <= 48'd0;
        indices_in0   <= 12'd0;
        indices_addr0 <= 4'd0;
        indices_wen0  <= 1'b0;
        cnt           <= 4'd0;
        loop_cnt      <= 3'd0;
        next_cnt      <= 4'd0;
        mti_done      <= 1'b0;
        mti_done_d    <= 4'd0;
    end
    else begin
        mti_done_d <= {mti_done,mti_done_d[3:1]};
        case(cnt)
            4'd0: begin
                mem_addr0     <= 4'd0;
                tmp_reg0      <= 48'd0;
                indices_in0   <= 12'd0;
                indices_addr0 <= 4'd0;
                indices_wen0  <= 1'b0;
                mti_done      <= 1'b0;
                if(mti_start) begin
                    cnt <= 4'd1;
                end
            end
            4'd1: begin
                mem_addr0 <= 4'd0; 
                indices_addr0 <= 4'd0-4'd1;
                cnt       <= 4'd2;
            end
            4'd2: begin
                mem_addr0 <= mem_addr0;
                cnt       <= 4'd3;
            end
            4'd3: begin
                mem_addr0 <= 4'd0; 
                //Read addr 0
                tmp_reg0 <= {mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                             mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                cnt      <= 4'd7;
                next_cnt <= 4'd4;
            end
            4'd15: begin
                mem_addr0 <= mem_addr0;
                cnt       <= next_cnt;
            end              
            4'd4: begin
                mem_addr0 <= 4'd1; 
                //Read addr 0
                tmp_reg0[2*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd8;
            end
            4'd8: begin
                mem_addr0 <= 4'd1; 
                //Read addr 1
                tmp_reg0[6*8-1:2*8] <= {mem_out0[5*8-1:4*8],mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],
                                        mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd7;
                next_cnt <= 4'd5;
            end
            4'd5: begin
                mem_addr0 <= 4'd2; 
                //Read addr 1
                tmp_reg0[4*8-1:0] <= {mem_out0[1*8-1:0*8],
                                      mem_out0[2*8-1:1*8],mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd9;
            end            
            4'd9: begin
                mem_addr0 <= 4'd2;
                //Read addr 2
                tmp_reg0[6*8-1:4*8] <= {mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd7;
                next_cnt <= 4'd6;
            end            
            4'd6: begin
                mem_addr0 <= 4'd0;
                //Read addr 2
                tmp_reg0 <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],mem_out0[3*8-1:2*8],
                             mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],mem_out0[6*8-1:5*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd7;
                next_cnt <= 4'd0;
            end
            4'd7: begin
                tmp_reg0      <= {12'd0,tmp_reg0[4*12-1:1*12]};
                indices_in0   <= tmp_reg0[1*12-1:0*12];
                indices_addr0 <= indices_addr0 + 6'd1;
                indices_wen0  <= 1'b1;

                if(loop_cnt==3'd3) begin
                    loop_cnt <= 3'd0;
                    cnt      <= next_cnt;
                    if(next_cnt==3'd0) begin
                        mti_done <= 1'b1;
                    end
                end
                else begin
                    loop_cnt <= loop_cnt + 3'd1;
                    cnt      <= cnt;
                end
            end
        endcase
    end 
end
endmodule
`endif

`ifdef PARAM_192F
module message_to_indices
(
input  wire          clk,
input  wire          rstn,
input  wire          mti_start,
output wire          mti_next_start,
input  wire [64-1:0] i_data0,
output wire [ 4-1:0] o_raddr0,
output wire [14-1:0] o_data0,
output wire [ 6-1:0] o_waddr0,
output wire          o_valid0
);

reg   [4-1:0] mem_addr0;
wire [64-1:0] mem_out0;
reg  [64-1:0] tmp_reg0;
reg   [8-1:0] indices_in0;
reg   [6-1:0] indices_addr0;
reg           indices_wen0;
reg   [4-1:0] cnt;
reg   [4-1:0] next_cnt;
reg   [3-1:0] loop_cnt;
reg           mti_done;
reg   [4-1:0] mti_done_d;

assign mem_out0 = i_data0;
assign o_raddr0 = mem_addr0;
assign o_data0  = {indices_addr0,indices_in0};
assign o_waddr0 = indices_addr0;
assign o_valid0 = indices_wen0;
assign mti_next_start = mti_done_d[0];

//message_to_indices( )
//192f parameter
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        mem_addr0     <= 4'd0;
        tmp_reg0      <= 64'd0;
        indices_in0   <= 9'd0;
        indices_addr0 <= 6'd0;
        indices_wen0  <= 1'b0;
        cnt           <= 4'd0;
        loop_cnt      <= 3'd0;
        next_cnt      <= 4'd0;
        mti_done      <= 1'b0;
        mti_done_d    <= 4'd0;
    end
    else begin
        mti_done_d <= {mti_done,mti_done_d[3:1]};
        case(cnt)
            4'd0: begin
                mem_addr0     <= 4'd0;
                tmp_reg0      <= 64'd0;
                indices_in0   <= 9'd0;
                indices_addr0 <= 6'd0;
                indices_wen0  <= 1'b0;
                mti_done      <= 1'b0;
                if(mti_start) begin
                    cnt <= 4'd1;
                end
            end
            4'd1: begin
                mem_addr0 <= 4'd0; 
                indices_addr0 <= 6'd0-6'd1;
                cnt       <= 4'd2;
            end
            4'd2: begin
                cnt       <= 4'd3;
            end
            4'd3: begin
                mem_addr0 <= 4'd1;
                //Read addr 0
                tmp_reg0 <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                             mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                             mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                cnt      <= 4'd8;
                next_cnt <= 4'd4;
            end
            4'd4: begin
                mem_addr0 <= 4'd2;
                //Read addr 1
                tmp_reg0 <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                             mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                             mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd5;
            end
            4'd5: begin
                mem_addr0 <= 4'd3;
                //Read addr 2
                tmp_reg0 <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                             mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                             mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd6;
            end
            4'd6: begin
                mem_addr0 <= 4'd4;
                //Read addr 3
                tmp_reg0 <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                             mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                             mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd7;
            end
            4'd7: begin
                mem_addr0 <= 4'd0;
                //Read addr 4
                tmp_reg0 <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                             mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                             mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd0;
            end            
            4'd8: begin
                tmp_reg0      <= {8'd0,tmp_reg0[8*8-1:1*8]};
                indices_in0   <= tmp_reg0[1*8-1:0*8];
                indices_addr0 <= indices_addr0 + 6'd1;
                indices_wen0  <= 1'b1;

                if(loop_cnt==3'd7) begin
                    loop_cnt <= 3'd0;
                    cnt      <= next_cnt;
                    if(next_cnt==4'd0) begin
                        mti_done <= 1'b1;
                    end
                end
                else begin
                    loop_cnt <= loop_cnt + 3'd1;
                    cnt      <= cnt;
                end
            end
        endcase
    end 
end
endmodule
`endif 

`ifdef PARAM_192S
module message_to_indices
(
input  wire          clk,
input  wire          rstn,
input  wire          mti_start,
output wire          mti_next_start,
input  wire [64-1:0] i_data0,
output wire [ 4-1:0] o_raddr0,
output wire [19-1:0] o_data0,
output wire [ 6-1:0] o_waddr0,
output wire          o_valid0
);

reg   [4-1:0] mem_addr0;
wire [64-1:0] mem_out0;
reg  [56-1:0] tmp_reg0;
reg  [14-1:0] indices_in0;
reg   [5-1:0] indices_addr0;
reg           indices_wen0;
reg   [4-1:0] cnt;
reg   [4-1:0] next_cnt;
reg   [3-1:0] loop_cnt;
reg           mti_done;
reg   [4-1:0] mti_done_d;

assign mem_out0 = i_data0;
assign o_raddr0 = mem_addr0;
assign o_data0  = {indices_addr0,indices_in0};
assign o_waddr0 = indices_addr0;
assign o_valid0 = indices_wen0;
assign mti_next_start = mti_done_d[0];

//message_to_indices( )
//192s parameter
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        mem_addr0     <= 4'd0;
        tmp_reg0      <= 56'd0;
        indices_in0   <= 14'd0;
        indices_addr0 <= 5'd0;
        indices_wen0  <= 1'b0;
        cnt           <= 4'd0;
        loop_cnt      <= 3'd0;
        next_cnt      <= 4'd0;
        mti_done      <= 1'b0;
        mti_done_d    <= 4'd0;
    end
    else begin
        mti_done_d <= {mti_done,mti_done_d[3:1]};
        case(cnt)
            4'd0: begin
                mem_addr0     <= 4'd0;
                tmp_reg0      <= 56'd0;
                indices_in0   <= 14'd0;
                indices_addr0 <= 5'd0;
                indices_wen0  <= 1'b0;
                mti_done      <= 1'b0;
                if(mti_start) begin
                    cnt <= 4'd1;
                end
            end
            4'd1: begin
                mem_addr0 <= 4'd0; 
                indices_addr0 <= 5'd0-5'd1;
                cnt       <= 4'd2;
            end
            4'd2: begin
                cnt       <= 4'd3;
            end
            4'd3: begin
                mem_addr0 <= 4'd0;
                //Read addr 0
                tmp_reg0 <= {mem_out0[2*8-1:1*8],
                             mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                             mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                cnt      <= 4'd8;
                next_cnt <= 4'd4;
            end
            4'd15: begin
                mem_addr0 <= mem_addr0;
                cnt       <= next_cnt;
            end  
            4'd4: begin
                mem_addr0 <= 4'd1;
                //Read addr 0
                tmp_reg0[1*8-1:0] <= {mem_out0[1*8-1:0*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd9;
            end
            4'd9: begin
                mem_addr0 <= 4'd1;
                //Read addr 1
                tmp_reg0[7*8-1:1*8] <= {mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                                        mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd5;
            end
            4'd5: begin
                mem_addr0 <= 4'd2;
                //Read addr 1
                tmp_reg0[2*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd10;
            end
            4'd10: begin
                mem_addr0 <= 4'd2;
                //Read addr 2
                tmp_reg0[7*8-1:2*8] <= {                    mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                                        mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd6;
            end
            4'd6: begin
                mem_addr0 <= 4'd3;
                //Read addr 2
                tmp_reg0[3*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                                      mem_out0[3*8-1:2*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd11;
            end       
            4'd11: begin
                mem_addr0 <= 4'd3;
                //Read addr 3
                tmp_reg0[7*8-1:3*8] <= {                                        mem_out0[5*8-1:4*8],
                                        mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd7;
            end       
            4'd7: begin
                mem_addr0 <= 4'd4;
                //Read addr 3
                tmp_reg0[4*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                                      mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd12;
            end            
            4'd12: begin
                mem_addr0 <= 4'd0;
                //Read addr 4
                tmp_reg0[7*8-1:4*8] <= {mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd0;
            end            
            4'd8: begin
                tmp_reg0      <= {14'd0,tmp_reg0[4*14-1:1*14]};
                indices_in0   <= tmp_reg0[1*14-1:0*14];
                indices_addr0 <= indices_addr0 + 5'd1;
                indices_wen0  <= 1'b1;

                if(loop_cnt==3'd3) begin
                    loop_cnt <= 3'd0;
                    cnt      <= next_cnt;
                    if(next_cnt==4'd0) begin
                        mti_done <= 1'b1;
                    end
                end
                else begin
                    loop_cnt <= loop_cnt + 3'd1;
                    cnt      <= cnt;
                end
            end
        endcase
    end 
end
endmodule
`endif

`ifdef PARAM_256F
module message_to_indices
(
input  wire          clk,
input  wire          rstn,
input  wire          mti_start,
output wire          mti_next_start,
input  wire [64-1:0] i_data0,
output wire [ 4-1:0] o_raddr0,
output wire [15-1:0] o_data0,
output wire [ 6-1:0] o_waddr0,
output wire          o_valid0
);

reg   [4-1:0] mem_addr0;
wire [64-1:0] mem_out0;
reg  [72-1:0] tmp_reg0;
reg   [9-1:0] indices_in0;
reg   [6-1:0] indices_addr0;
reg           indices_wen0;
reg   [4-1:0] cnt;
reg   [4-1:0] next_cnt;
reg   [3-1:0] loop_cnt;
reg           mti_done;
reg   [4-1:0] mti_done_d;

assign mem_out0 = i_data0;
assign o_raddr0 = mem_addr0;
assign o_data0  = {indices_addr0,indices_in0};
assign o_waddr0 = indices_addr0;
assign o_valid0 = indices_wen0;
assign mti_next_start = mti_done_d[0];

//message_to_indices( )
//256f parameter
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        mem_addr0     <= 4'd0;
        tmp_reg0      <= 72'd0;
        indices_in0   <= 9'd0;
        indices_addr0 <= 6'd0;
        indices_wen0  <= 1'b0;
        cnt           <= 4'd0;
        loop_cnt      <= 3'd0;
        next_cnt      <= 4'd0;
        mti_done      <= 1'b0;
        mti_done_d    <= 4'd0;
    end
    else begin
        mti_done_d <= {mti_done,mti_done_d[3:1]};
        case(cnt)
            4'd0: begin
                mem_addr0     <= 4'd0;
                tmp_reg0      <= 72'd0;
                indices_in0   <= 9'd0;
                indices_addr0 <= 6'd0;
                indices_wen0  <= 1'b0;
                mti_done      <= 1'b0;
                if(mti_start) begin
                    cnt <= 4'd1;
                end
            end
            4'd1: begin
                mem_addr0 <= 4'd0;
                indices_addr0 <= 6'd0-6'd1;
                cnt       <= 4'd2;
            end
            4'd2: begin
                mem_addr0 <= mem_addr0;
                cnt       <= 4'd3;
            end
            4'd3: begin
                mem_addr0 <= 4'd1;
                //Read addr 0
                tmp_reg0[8*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                                      mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                                      mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                cnt      <= 4'd15;
                next_cnt <= 4'd9;
            end
            4'd15: begin
                mem_addr0 <= mem_addr0;
                cnt       <= next_cnt;
            end
            4'd9: begin
                mem_addr0 <= 4'd1;
                //Read addr 1
                tmp_reg0[9*8-1:8*8] <= {mem_out0[8*8-1:7*8]};
                cnt      <= 4'd8;
                next_cnt <= 4'd4;
            end
            4'd4: begin
                mem_addr0 <= 4'd2;
                //Read addr 1
                tmp_reg0[7*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                                      mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                                      mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8]};                
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd10;
            end
            4'd10: begin
                mem_addr0 <= 4'd2;
                //Read addr 2
                tmp_reg0[9*8-1:7*8] <= {mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};                
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd5;
            end
            4'd5: begin
                mem_addr0 <= 4'd3;
                //Read addr 2
                tmp_reg0[6*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                                      mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                                      mem_out0[6*8-1:5*8]};                 
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd11;
            end
            4'd11: begin
                mem_addr0 <= 4'd3;
                //Read addr 3
                tmp_reg0[9*8-1:6*8] <= {mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};                 
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd6;
            end
            4'd6: begin
                mem_addr0 <= 4'd4;
                //Read addr 3
                tmp_reg0[5*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                                      mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8]};                 
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd12;
            end
            4'd12: begin
                mem_addr0 <= 4'd4;
                //Read addr 4
                tmp_reg0[9*8-1:5*8] <= {mem_out0[5*8-1:4*8],mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],
                                        mem_out0[8*8-1:7*8]};                 
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd7;
            end
            4'd7: begin
                mem_addr0 <= 4'd5;
                //Read addr 4
                tmp_reg0[4*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                                      mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8]};                 
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd13;
            end            
            4'd13: begin
                mem_addr0 <= 4'd0;
                //Read addr 5
                tmp_reg0[9*8-1:4*8] <= {mem_out0[4*8-1:3*8],
                                        mem_out0[5*8-1:4*8],mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],
                                        mem_out0[8*8-1:7*8]};                 
                indices_wen0 <= 1'b0;
                cnt      <= 4'd8;
                next_cnt <= 4'd0;
            end    
            4'd8: begin
                tmp_reg0      <= {9'd0,tmp_reg0[8*9-1:1*9]};
                indices_in0   <= tmp_reg0[1*9-1:0*9];
                indices_addr0 <= indices_addr0 + 6'd1;
                indices_wen0  <= 1'b1;

                if(loop_cnt==3'd7) begin
                    loop_cnt <= 3'd0;
                    cnt      <= next_cnt;
                    if(next_cnt==4'd0) begin
                        mti_done <= 1'b1;
                    end
                    else begin
                        mti_done <= 1'b0;
                    end
                end
                else begin
                    loop_cnt <= loop_cnt + 3'd1;
                    cnt      <= cnt;
                end
            end
        endcase
    end 
end
endmodule
`endif

`ifdef PARAM_256S
module message_to_indices
(
input  wire          clk,
input  wire          rstn,
input  wire          mti_start,
output wire          mti_next_start,
input  wire [64-1:0] i_data0,
output wire [ 4-1:0] o_raddr0,
output wire [19-1:0] o_data0,
output wire [ 6-1:0] o_waddr0,
output wire          o_valid0
);

reg   [4-1:0] mem_addr0;
wire [64-1:0] mem_out0;
reg  [56-1:0] tmp_reg0;
reg  [14-1:0] indices_in0;
reg   [5-1:0] indices_addr0;
reg           indices_wen0;
reg   [4-1:0] cnt;
reg   [4-1:0] next_cnt;
reg   [3-1:0] loop_cnt;
reg           mti_done;
reg   [4-1:0] mti_done_d;

assign mem_out0 = i_data0;
assign o_raddr0 = mem_addr0;
assign o_data0  = {indices_addr0,indices_in0};
assign o_waddr0 = indices_addr0;
assign o_valid0 = indices_wen0;
assign mti_next_start = mti_done_d[0];

//message_to_indices( )
//256s parameter
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        mem_addr0     <= 4'd0;
        tmp_reg0      <= 56'd0;
        indices_in0   <= 14'd0;
        indices_addr0 <= 5'd0;
        indices_wen0  <= 1'b0;
        cnt           <= 4'd0;
        loop_cnt      <= 3'd0;
        next_cnt      <= 4'd0;
        mti_done      <= 1'b0;
        mti_done_d    <= 4'd0;
    end
    else begin
        mti_done_d <= {mti_done,mti_done_d[3:1]};
        case(cnt)
            4'd0: begin
                mem_addr0     <= 4'd0;
                tmp_reg0      <= 56'd0;
                indices_in0   <= 14'd0;
                indices_addr0 <= 5'd0;
                indices_wen0  <= 1'b0;
                mti_done      <= 1'b0;
                if(mti_start) begin
                    cnt <= 4'd1;
                end
            end
            4'd1: begin
                mem_addr0 <= 4'd0;
                indices_addr0 <= 5'd0-5'd1;
                cnt       <= 4'd2;
            end
            4'd2: begin
                cnt       <= 4'd3;
            end
            4'd3: begin
                mem_addr0 <= 4'd0;
                //Read addr 0
                tmp_reg0 <= {mem_out0[2*8-1:1*8],
                             mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                             mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                cnt      <= 4'd9;
                next_cnt <= 4'd4;
            end
            4'd15: begin
                mem_addr0 <= mem_addr0;
                cnt       <= next_cnt;
            end
            4'd4: begin
                mem_addr0 <= 4'd1;
                //Read addr 0
                tmp_reg0[1*8-1:0] <= {mem_out0[1*8-1:0*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd10;
            end
            4'd10: begin
                mem_addr0 <= 4'd1;
                //Read addr 1
                tmp_reg0[7*8-1:1*8] <= {mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                                        mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd9;
                next_cnt <= 4'd5;
            end
            4'd5: begin
                mem_addr0 <= 4'd2;
                //Read addr 1
                tmp_reg0[2*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd11;
            end
            4'd11: begin
                mem_addr0 <= 4'd2;
                //Read addr 2
                tmp_reg0[7*8-1:2*8] <= {                    mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8],
                                        mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd9;
                next_cnt <= 4'd6;
            end
            4'd6: begin
                mem_addr0 <= 4'd3;
                //Read addr 2
                tmp_reg0[3*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                                      mem_out0[3*8-1:2*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd12;
            end
            4'd12: begin
                mem_addr0 <= 4'd3;
                //Read addr 3
                tmp_reg0[7*8-1:3*8] <= {                                        mem_out0[5*8-1:4*8],
                                        mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd9;
                next_cnt <= 4'd7;
            end
            4'd7: begin
                mem_addr0 <= 4'd4;
                //Read addr 3
                tmp_reg0[4*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                                      mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd13;
            end
            4'd13: begin
                mem_addr0 <= 4'd4;
                //Read addr 4
                tmp_reg0[7*8-1:4*8] <= {mem_out0[6*8-1:5*8],mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd9;
                next_cnt <= 4'd8;
            end
            4'd8: begin
                mem_addr0 <= 4'd5;
                //Read addr 4
                tmp_reg0[5*8-1:0] <= {mem_out0[1*8-1:0*8],mem_out0[2*8-1:1*8],
                                      mem_out0[3*8-1:2*8],mem_out0[4*8-1:3*8],mem_out0[5*8-1:4*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd15;
                next_cnt <= 4'd14;
            end           
            4'd14: begin
                mem_addr0 <= 4'd0;
                //Read addr 5
                tmp_reg0[7*8-1:5*8] <= {mem_out0[7*8-1:6*8],mem_out0[8*8-1:7*8]};
                indices_wen0 <= 1'b0;
                cnt      <= 4'd9;
                next_cnt <= 4'd0;
            end              
            4'd9: begin
                tmp_reg0      <= {14'd0,tmp_reg0[4*14-1:1*14]};
                indices_in0   <= tmp_reg0[1*14-1:0*14];
                indices_addr0 <= indices_addr0 + 5'd1;
                indices_wen0  <= 1'b1;

                if(loop_cnt==3'd3) begin
                    loop_cnt <= 3'd0;
                    cnt      <= next_cnt;
                    if(next_cnt==4'd0) begin
                        mti_done <= 1'b1;
                    end
                end
                else begin
                    loop_cnt <= loop_cnt + 3'd1;
                    cnt      <= cnt;
                end
            end
        endcase
    end 
end
endmodule
`endif