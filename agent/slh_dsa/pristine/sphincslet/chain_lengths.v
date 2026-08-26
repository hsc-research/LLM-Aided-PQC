module chain_lengths
(
input wire           clk,
input wire           rstn,
input  wire          cl_start,
output wire          o_start_next,
output reg           o_cl_flag,
input  wire [64-1:0] root,
output reg   [6-1:0] root_mem_addr0,
output reg   [4-1:0] w_mem_in0,
output reg   [4-1:0] w_mem_in1,
`ifdef PARAM_128
output reg   [6-1:0] w_mem_addr0,
output reg   [6-1:0] w_mem_addr1,
`endif
`ifdef PARAM_192
output reg   [6-1:0] w_mem_addr0,
output reg   [6-1:0] w_mem_addr1,
`endif
`ifdef PARAM_256
output reg   [7-1:0] w_mem_addr0,
output reg   [7-1:0] w_mem_addr1,
`endif
output reg           w_mem_wen0,
output reg           w_mem_wen1
);

reg [64-1:0] root_reg;
`ifdef PARAM_128
reg  [9-1:0] csum;
reg  [9-1:0] csum_sub0;
reg  [9-1:0] csum_sub1;
`endif
`ifdef PARAM_192
reg [10-1:0] csum;
reg [10-1:0] csum_sub0;
reg [10-1:0] csum_sub1;
`endif
`ifdef PARAM_256
reg [10-1:0] csum;
reg [10-1:0] csum_sub0;
reg [10-1:0] csum_sub1;
`endif
reg  [3-1:0] cnt;
reg          start_next;
reg          start_next_d;

assign o_start_next = start_next_d;

always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        root_reg <= 64'd0;
        root_mem_addr0 <= 6'd0;
        csum      <= 10'd0;
        csum_sub0 <= 10'd0;
        csum_sub1 <= 10'd0;
        w_mem_in0 <= 4'd0;
        w_mem_in1 <= 4'd0;
        w_mem_addr0 <= 7'd0;
        w_mem_addr1 <= 7'd0;
        w_mem_wen0 <= 1'b0;
        w_mem_wen1 <= 1'b0;
        cnt <= 3'd0;
        start_next <= 1'b0;
        start_next_d <= 1'b0;
        o_cl_flag <= 1'b0;
    end
    else begin
        start_next_d <= start_next;
        case(cnt)
            3'd0: begin
                root_mem_addr0 <= 6'd0;
                w_mem_in0   <= 4'd0;
                w_mem_in1   <= 4'd0;
                w_mem_addr0 <= 7'd0;
                w_mem_addr1 <= 7'd0;
                w_mem_wen0  <= 1'b0;
                w_mem_wen1  <= 1'b0;
                csum        <= 10'd0;
                csum_sub0   <= 10'd0;
                csum_sub1   <= 10'd0;
                start_next  <= 1'b0;
                if(cl_start) begin
                    cnt <= 3'd1;
                    o_cl_flag <= 1'b1;
                end
            end
            3'd1: begin
                w_mem_addr0 <= 7'd0 - 6'd2;
                w_mem_addr1 <= 7'd1 - 6'd2;                
                cnt <= 3'd2;
            end
            3'd2: begin
                root_reg <= root;
                root_mem_addr0 <= root_mem_addr0 + 6'd1;
                w_mem_wen0 <= 1'b0;
                w_mem_wen1 <= 1'b0;                
                cnt <= 3'd3;
            end            
            3'd3: begin
                root_reg <= {root_reg[14*4-1:0*4],8'd0};

                w_mem_in0 <= root_reg[16*4-1:15*4];
                w_mem_in1 <= root_reg[15*4-1:14*4];
                w_mem_addr0 <= w_mem_addr0 + 7'd2;
                w_mem_addr1 <= w_mem_addr1 + 7'd2;
                w_mem_wen0 <= 1'b1;
                w_mem_wen1 <= 1'b1;
                csum_sub0 <= csum_sub0 + root_reg[16*4-1:15*4];
                csum_sub1 <= csum_sub1 + root_reg[15*4-1:14*4];

                `ifdef PARAM_128
                if(w_mem_addr0==6'd12) begin
                    cnt <= 3'd2;
                end
                else if(w_mem_addr0==6'd28) begin
                    root_mem_addr0 <= 6'd0;
                    cnt <= 3'd4;
                end
                else begin
                    cnt <= cnt;
                end
                `endif

                `ifdef PARAM_192
                if(w_mem_addr0==6'd12 || w_mem_addr0==6'd28) begin
                    cnt <= 3'd2;
                end
                else if(w_mem_addr0==6'd44) begin
                    root_mem_addr0 <= 6'd0;
                    cnt <= 3'd4;
                end
                else begin
                    cnt <= cnt;
                end                
                `endif                

                `ifdef PARAM_256
                if(w_mem_addr0==6'd12 || w_mem_addr0==6'd28 || w_mem_addr0==6'd44) begin
                    cnt <= 3'd2;
                end
                else if(w_mem_addr0==6'd60) begin
                    root_mem_addr0 <= 6'd0;
                    cnt <= 3'd4;
                end
                else begin
                    cnt <= cnt;
                end                
                `endif
            end
            3'd4: begin
                csum <= csum_sub0 + csum_sub1;
                w_mem_wen0 <= 1'b0;
                w_mem_wen1 <= 1'b0;                    
                cnt <= 3'd5;
            end
            3'd5: begin
                `ifdef PARAM_128
                csum <= 9'd480 - csum;
                `endif

                `ifdef PARAM_192 
                csum <= 10'd720 - csum;
                `endif

                `ifdef PARAM_256
                csum <= 10'd960 - csum;
                `endif
                cnt <= 3'd6;
            end
            3'd6: begin

                `ifdef PARAM_128
                w_mem_in0 <= {3'd0,csum[8]};
                w_mem_in1 <= csum[7:4];
                w_mem_addr0 <= 6'd32;
                w_mem_addr1 <= 6'd33;
                `endif 

                `ifdef PARAM_192 
                w_mem_in0 <= {2'd0,csum[9:8]};
                w_mem_in1 <= csum[7:4];
                w_mem_addr0 <= 6'd48;
                w_mem_addr1 <= 6'd49;
                `endif 

                `ifdef PARAM_256 
                w_mem_in0 <= {2'd0,csum[9:8]};
                w_mem_in1 <= csum[7:4];
                w_mem_addr0 <= 7'd64;
                w_mem_addr1 <= 7'd65;
                `endif 

                w_mem_wen0 <= 1'b1;
                w_mem_wen1 <= 1'b1;
                cnt <= 3'd7;
            end
            3'd7: begin
                w_mem_in0 <= csum[3:0];
                w_mem_in1 <= 4'd0;

                `ifdef PARAM_128
                w_mem_addr0 <= 6'd34;
                w_mem_addr1 <= 6'd35;
                `endif

                `ifdef PARAM_192
                w_mem_addr0 <= 6'd50;
                w_mem_addr1 <= 6'd51;
                `endif

                `ifdef PARAM_256
                w_mem_addr0 <= 7'd66;
                w_mem_addr1 <= 7'd67;
                `endif

                w_mem_wen0 <= 1'b1;
                w_mem_wen1 <= 1'b1;
                start_next <= 1'b1;
                o_cl_flag <= 1'b0;
                cnt <= 3'd0;
            end
        endcase
    end
end
endmodule