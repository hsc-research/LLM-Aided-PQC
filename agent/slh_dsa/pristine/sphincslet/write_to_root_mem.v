module write_to_root_mem
(
input  wire          clk,
input  wire          rstn,
input  wire [ 2-1:0] mode,
input  wire [64-1:0] i_data,
input  wire          i_vaild,
output wire [64-1:0] o_data,
output wire [ 6-1:0] o_addr,
output wire          o_valid,
input  wire          root_flag,
output wire          o_start_next
);

reg [64-1:0] out_data;
reg [6-1:0]  out_addr;
reg          out_valid;
reg          start_next;
reg          start_next_d;


assign o_data = out_data;
assign o_addr = out_addr;
assign o_valid = out_valid;
assign o_start_next = start_next_d;

`ifdef PARAM_128
reg flag;
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        out_data <= 64'd0;
        out_addr <= 6'd0;      
        out_valid <= 1'b0;
        start_next <= 1'b0;
        start_next_d <= 1'b0;
        flag <= 1'b0;
    end
    else begin
        start_next_d <= start_next;
        if(i_vaild && mode==2'd3) begin
            out_data <= i_data;
            out_valid <= 1'b1;
            if(flag) begin
                out_addr <= out_addr + 1;
                start_next <= 1'b1;
                flag <= 1'b0;
            end
            else begin
                out_addr <= out_addr;
                start_next <= 1'b0;
                flag <= 1'b1;
            end
        end
        else if(root_flag && i_vaild && mode==2'd0) begin
            out_data <= i_data;
            out_valid <= 1'b1;
            if(flag) begin
                out_addr <= out_addr + 1;
                start_next <= 1'b1;
                flag <= 1'b0;
            end
            else begin
                out_addr <= out_addr;
                start_next <= 1'b0;
                flag <= 1'b1;
            end
        end
        else begin
            out_data <= 64'd0;
            out_addr <= 6'd0;
            out_valid <= 1'b0;
            start_next <= 1'b0;
            flag <= 1'b0;
        end
    end
end
`endif

`ifdef PARAM_192
reg [2-1:0] flag;
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        out_data <= 64'd0;
        out_addr <= 6'd0;      
        out_valid <= 1'b0;
        start_next <= 1'b0;
        start_next_d <= 1'b0;
        flag <= 2'd0;
    end
    else begin
        start_next_d <= start_next;
        if(i_vaild && mode==2'd3) begin
            out_data <= i_data;
            out_valid <= 1'b1;
            if(flag==2'd2) begin
                out_addr <= out_addr + 1;
                start_next <= 1'b1;
                flag <= 2'd0;
            end
            else if(flag==2'd1) begin
                out_addr <= out_addr + 1;
                start_next <= 1'b0;
                flag <= flag + 2'd1;
            end
            else begin
                out_addr <= out_addr;
                start_next <= 1'b0;
                flag <= flag + 2'd1;
            end
        end
        else if(root_flag && i_vaild && mode==2'd0) begin
            out_data <= i_data;
            out_valid <= 1'b1;
            if(flag==2'd2) begin
                out_addr <= out_addr + 1;
                start_next <= 1'b1;
                flag <= 2'd0;
            end
            else if(flag==2'd1) begin
                out_addr <= out_addr + 1;
                start_next <= 1'b0;
                flag <= flag + 2'd1;
            end
            else begin
                out_addr <= out_addr;
                start_next <= 1'b0;
                flag <= flag + 2'd1;
            end
        end
        else begin
            out_data <= 64'd0;
            out_addr <= 6'd0;
            out_valid <= 1'b0;
            start_next <= 1'b0;
            flag <= 2'd0;
        end
    end
end
`endif

`ifdef PARAM_256
reg [2-1:0] flag;
always@(posedge clk, negedge rstn) begin
    if(!rstn) begin
        out_data <= 64'd0;
        out_addr <= 6'd0;      
        out_valid <= 1'b0;
        start_next <= 1'b0;
        start_next_d <= 1'b0;
        flag <= 2'd0;
    end
    else begin
        start_next_d <= start_next;
        if(i_vaild && mode==2'd3) begin
            out_data <= i_data;
            out_valid <= 1'b1;
            if(flag==2'd3) begin
                out_addr <= out_addr + 1;
                start_next <= 1'b1;
                flag <= 2'd0;
            end
            else if(flag==2'd1 || flag==2'd2) begin
                out_addr <= out_addr + 1;
                start_next <= 1'b0;
                flag <= flag + 2'd1;
            end
            else begin
                out_addr <= out_addr;
                start_next <= 1'b0;
                flag <= flag + 2'd1;
            end
        end
        else if(root_flag && i_vaild && mode==2'd0) begin
            out_data <= i_data;
            out_valid <= 1'b1;
            if(flag==2'd3) begin
                out_addr <= out_addr + 1;
                start_next <= 1'b1;
                flag <= 2'd0;
            end
            else if(flag==2'd1 || flag==2'd2) begin
                out_addr <= out_addr + 1;
                start_next <= 1'b0;
                flag <= flag + 2'd1;
            end
            else begin
                out_addr <= out_addr;
                start_next <= 1'b0;
                flag <= flag + 2'd1;
            end
        end
        else begin
            out_data <= 64'd0;
            out_addr <= 6'd0;
            out_valid <= 1'b0;
            start_next <= 1'b0;
            flag <= 2'd0;
        end
    end
end
`endif
endmodule