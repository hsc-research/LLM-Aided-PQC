module Keccak_F1600(string1, string2, finish, count, clk, rst);
input clk, rst;
input [7:0] count;
input [1599:0] string1;
output [1599:0] string2;
output reg finish;

wire [63:0] a00, a01, a02, a03, a04;
wire [63:0] a10, a11, a12, a13, a14;
wire [63:0] a20, a21, a22, a23, a24;
wire [63:0] a30, a31, a32, a33, a34;
wire [63:0] a40, a41, a42, a43, a44;

wire [63:0] d00, d01, d02, d03, d04;
wire [63:0] d10, d11, d12, d13, d14;
wire [63:0] d20, d21, d22, d23, d24;
wire [63:0] d30, d31, d32, d33, d34;
wire [63:0] d40, d41, d42, d43, d44;

reg [63:0] e00, e01, e02, e03, e04;
reg [63:0] e10, e11, e12, e13, e14;
reg [63:0] e20, e21, e22, e23, e24;
reg [63:0] e30, e31, e32, e33, e34;
reg [63:0] e40, e41, e42, e43, e44;

wire [63:0] c00, c01, c02, c03, c04;
wire [63:0] c10, c11, c12, c13, c14;
wire [63:0] c20, c21, c22, c23, c24;
wire [63:0] c30, c31, c32, c33, c34;
wire [63:0] c40, c41, c42, c43, c44;

assign d00 = e00, d01 = e01, d02 = e02, d03 = e03, d04 = e04;
assign d10 = e10, d11 = e11, d12 = e12, d13 = e13, d14 = e14;
assign d20 = e20, d21 = e21, d22 = e22, d23 = e23, d24 = e24;
assign d30 = e30, d31 = e31, d32 = e32, d33 = e33, d34 = e34;
assign d40 = e40, d41 = e41, d42 = e42, d43 = e43, d44 = e44;

stringtostate String2State(string1, a00, a01, a02, a03, a04, a10, a11, a12, a13, a14, a20, a21, a22, a23, a24, a30, 
a31, a32, a33, a34, a40, a41, a42, a43, a44);

round ROUND(d00, d01, d02, d03, d04, d10, d11, d12, d13, d14, d20, d21, d22, d23, d24, d30, d31, d32, d33, d34, d40, d41, 
d42, d43, d44, c00, c01, c02, c03, c04, c10, c11, c12, c13, c14, c20, c21, c22, c23, c24, c30, c31, c32, c33, c34, c40, 
c41, c42, c43, c44, count);

always @(posedge clk) begin

    if (rst) begin
        e00 <= a00; e01 <= a01; e02 <= a02; e03 <= a03; e04 <= a04;
        e10 <= a10; e11 <= a11; e12 <= a12; e13 <= a13; e14 <= a14;
        e20 <= a20; e21 <= a21; e22 <= a22; e23 <= a23; e24 <= a24;
        e30 <= a30; e31 <= a31; e32 <= a32; e33 <= a33; e34 <= a34;
        e40 <= a40; e41 <= a41; e42 <= a42; e43 <= a43; e44 <= a44;
        finish <= 0;
    end
    
    else if (count < 8'd24) begin
        e00 <= c00; e01 <= c01; e02 <= c02; e03 <= c03; e04 <= c04;
        e10 <= c10; e11 <= c11; e12 <= c12; e13 <= c13; e14 <= c14;
        e20 <= c20; e21 <= c21; e22 <= c22; e23 <= c23; e24 <= c24;
        e30 <= c30; e31 <= c31; e32 <= c32; e33 <= c33; e34 <= c34;
        e40 <= c40; e41 <= c41; e42 <= c42; e43 <= c43; e44 <= c44;
        finish <= 0;
    end
    
    else begin
        finish <= 1;
    end
end

statetostring State2String(d00, d01, d02, d03, d04, d10, d11, d12, d13, d14, d20, d21, d22, d23, d24, d30, d31, d32, d33, d34, d40, d41, d42, d43, d44, string2);

endmodule
