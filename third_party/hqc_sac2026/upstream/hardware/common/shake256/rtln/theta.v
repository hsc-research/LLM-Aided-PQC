module theta(a00, a01, a02, a03, a04, a10, a11, a12, a13, a14, a20, a21, a22, a23, a24, a30, a31, a32, a33, a34, a40, a41, a42, a43, a44, b00, b01, b02, b03, b04, b10, b11, b12, b13, b14, b20, b21, b22, b23, b24, b30, b31, b32, b33, b34, b40, b41, b42, b43, b44);   
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
wire [63:0] C [4:0];
wire [63:0] D [4:0];
wire [63:0] E [4:0];

assign C[0] = a00^a01^a02^a03^a04;
assign C[1] = a10^a11^a12^a13^a14;
assign C[2] = a20^a21^a22^a23^a24;
assign C[3] = a30^a31^a32^a33^a34;
assign C[4] = a40^a41^a42^a43^a44;

ROL A1 (1, C[0], E[0]);
ROL A2 (1, C[1], E[1]);
ROL A3 (1, C[2], E[2]);
ROL A4 (1, C[3], E[3]);
ROL A5 (1, C[4], E[4]);
  
assign D[0] = C[4]^E[1];
assign D[1] = C[0]^E[2];
assign D[2] = C[1]^E[3];
assign D[3] = C[2]^E[4];
assign D[4] = C[3]^E[0];

assign b00 = a00^D[0], b01 = a01^D[0], b02 = a02^D[0], b03 = a03^D[0], b04 = a04^D[0];
assign b10 = a10^D[1], b11 = a11^D[1], b12 = a12^D[1], b13 = a13^D[1], b14 = a14^D[1];
assign b20 = a20^D[2], b21 = a21^D[2], b22 = a22^D[2], b23 = a23^D[2], b24 = a24^D[2];
assign b30 = a30^D[3], b31 = a31^D[3], b32 = a32^D[3], b33 = a33^D[3], b34 = a34^D[3];
assign b40 = a40^D[4], b41 = a41^D[4], b42 = a42^D[4], b43 = a43^D[4], b44 = a44^D[4];

endmodule
