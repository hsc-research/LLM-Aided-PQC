module counter(clk, rst, count);
    input clk, rst;
    output reg [7:0] count;

    always @(posedge clk) begin
        if (rst) begin
            count <= 8'd0;      // Start at Round 0 immediately
        end
        else if (count < 8'd24) begin
            count <= count + 1; // Count up to 23
        end
        else begin
            count <= count;     // Hold at 24 when done
        end
    end
endmodule
