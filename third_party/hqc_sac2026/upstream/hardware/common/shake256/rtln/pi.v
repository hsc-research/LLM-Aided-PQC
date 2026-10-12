module pi(a00, a01, a02, a03, a04, a10, a11, a12, a13, a14, a20, a21, a22, a23, a24, a30, a31, a32, a33, a34, a40, a41, a42, a43, a44, b00, b01, b02, b03, b04, b10, b11, b12, b13, b14, b20, b21, b22, b23, b24, b30, b31, b32, b33, b34, b40, b41, b42, b43, b44);   
input [63:0] a00, a01, a02, a03, a04;
input [63:0] a10, a11, a12, a13, a14;
input [63:0] a20, a21, a22, a23, a24;
input [63:0] a30, a31, a32, a33, a34;
input [63:0] a40, a41, a42, a43, a44;    
output [63:0] b00, b01, b02, b03, b04;
output [63:0] b10, b11, b12, b13, b14;
output [63:0] b20, b21, b22, b23, b24;
output [63:0] b30, b31, b32, b33, b34;
output [63:0] b40, b41, b42, b43, b44;

assign b00 = a00, b01 = a30, b02 = a10, b03 = a40, b04 = a20;
assign b10 = a11, b11 = a41, b12 = a21, b13 = a01, b14 = a31;
assign b20 = a22, b21 = a02, b22 = a32, b23 = a12, b24 = a42;
assign b30 = a33, b31 = a13, b32 = a43, b33 = a23, b34 = a03;
assign b40 = a44, b41 = a24, b42 = a04, b43 = a34, b44 = a14;

endmodule
