module stringtostate (string,a00,a01,a02,a03,a04,a10,a11,a12,a13,a14,a20,a21,a22,a23,a24,a30,a31,a32,a33,a34,a40,a41,a42,a43,a44);
input [1599:0] string;
output [63:0]a00,a01,a02,a03,a04;
output [63:0]a10,a11,a12,a13,a14;
output [63:0]a20,a21,a22,a23,a24;
output [63:0]a30,a31,a32,a33,a34;
output [63:0]a40,a41,a42,a43,a44;

assign  a00[63:0]= string[63:0];
assign  a01[63:0]= string[383:320];
assign  a02[63:0]= string[703:640];
assign  a03[63:0]= string[1023:960];
assign  a04[63:0]= string[1343:1280];

assign  a10[63:0]= string[127:64];
assign  a11[63:0]= string[447:384];
assign  a12[63:0]= string[767:704];
assign  a13[63:0]= string[1087:1024];
assign  a14[63:0]= string[1407:1344];

assign  a20[63:0]= string[191:128];
assign  a21[63:0]= string[511:448];
assign  a22[63:0]= string[831:768];
assign  a23[63:0]= string[1151:1088];
assign  a24[63:0]= string[1471:1408];

assign  a30[63:0]= string[255:192];
assign  a31[63:0]= string[575:512];
assign  a32[63:0]= string[895:832];
assign  a33[63:0]= string[1215:1152];
assign  a34[63:0]= string[1535:1472];

assign  a40[63:0]= string[319:256];
assign  a41[63:0]= string[639:576];
assign  a42[63:0]= string[959:896];
assign  a43[63:0]= string[1279:1216];
assign  a44[63:0]= string[1599:1536];

endmodule