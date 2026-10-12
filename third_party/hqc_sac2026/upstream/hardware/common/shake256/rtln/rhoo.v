module rhoo(a00, a01, a02, a03, a04, a10, a11, a12, a13, a14, a20, a21, a22, a23, a24, a30, a31, a32, a33, a34, a40, a41, a42, a43, a44, b00, b01, b02, b03, b04, b10, b11, b12, b13, b14, b20, b21, b22, b23, b24, b30, b31, b32, b33, b34, b40, b41, b42, b43, b44);
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

ROL A1 (0,a00,b00);
ROL A2 (1,a10,b10);
ROL A3 (3,a02,b02);
ROL A4 (6,a21,b21);
ROL A5 (10,a12,b12);  
ROL A6 (15,a23,b23);
ROL A7 (21,a33,b33);
ROL A8 (28,a30,b30);
ROL A9 (36,a01,b01);
ROL A10(45,a13,b13);
ROL A11 (55,a31,b31);
ROL A12 (2,a14,b14);
ROL A13 (14,a44,b44);
ROL A14 (27,a40,b40);
ROL A15 (41,a03,b03);    
ROL A16 (56,a34,b34);
ROL A17 (8,a43,b43);
ROL A18 (25,a32,b32);
ROL A19 (43,a22,b22);
ROL A20 (62,a20,b20);    
ROL A21 (18,a04,b04);
ROL A22 (39,a42,b42);
ROL A23 (61,a24,b24);
ROL A24 (20,a41,b41);
ROL A25 (44,a11,b11);
   
endmodule
