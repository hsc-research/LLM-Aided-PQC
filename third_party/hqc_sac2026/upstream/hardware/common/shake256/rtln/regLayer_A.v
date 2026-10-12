`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 17.11.2025 16:44:18
// Design Name: 
// Module Name: regLayer_A
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////
module regLayer_A(clk, a0,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,
out0,out1,out2,out3,out4,out5,out6,out7,out8,out9,out10,out11,out12,out13,out14,out15);
input clk;
input [22:0] a0,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15;
output reg [22:0] out0,out1,out2,out3,out4,out5,out6,out7,out8,out9,out10,out11,out12,out13,out14,out15;

reg [22:0] reg1a0,reg1a1,reg1a2,reg1a3,reg1a4,reg1a5,reg1a6,reg1a7,reg1a8,reg1a9,reg1a10,reg1a11,reg1a12,reg1a13,reg1a14,reg1a15;
reg [22:0] reg2a0,reg2a1,reg2a2,reg2a3,reg2a4,reg2a5,reg2a6,reg2a7,reg2a8,reg2a9,reg2a10,reg2a11,reg2a12,reg2a13,reg2a14,reg2a15;
reg [22:0] reg3a0,reg3a1,reg3a2,reg3a3,reg3a4,reg3a5,reg3a6,reg3a7,reg3a8,reg3a9,reg3a10,reg3a11,reg3a12,reg3a13,reg3a14,reg3a15;
reg [22:0] reg4a0,reg4a1,reg4a2,reg4a3,reg4a4,reg4a5,reg4a6,reg4a7,reg4a8,reg4a9,reg4a10,reg4a11,reg4a12,reg4a13,reg4a14,reg4a15;
reg [22:0] reg5a0,reg5a1,reg5a2,reg5a3,reg5a4,reg5a5,reg5a6,reg5a7,reg5a8,reg5a9,reg5a10,reg5a11,reg5a12,reg5a13,reg5a14,reg5a15;
reg [22:0] reg6a0,reg6a1,reg6a2,reg6a3,reg6a4,reg6a5,reg6a6,reg6a7,reg6a8,reg6a9,reg6a10,reg6a11,reg6a12,reg6a13,reg6a14,reg6a15;
reg [22:0] reg7a0,reg7a1,reg7a2,reg7a3,reg7a4,reg7a5,reg7a6,reg7a7,reg7a8,reg7a9,reg7a10,reg7a11,reg7a12,reg7a13,reg7a14,reg7a15;
reg [22:0] reg8a0,reg8a1,reg8a2,reg8a3,reg8a4,reg8a5,reg8a6,reg8a7,reg8a8,reg8a9,reg8a10,reg8a11,reg8a12,reg8a13,reg8a14,reg8a15;

always@(posedge clk) begin
    {reg1a0,reg1a1,reg1a2,reg1a3,reg1a4,reg1a5,reg1a6,reg1a7,reg1a8,reg1a9,reg1a10,
    reg1a11,reg1a12,reg1a13,reg1a14,reg1a15}<={a0,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,
    a12,a13,a14,a15};
    
    {reg2a0,reg2a1,reg2a2,reg2a3,reg2a4,reg2a5,reg2a6,reg2a7,reg2a8,reg2a9,reg2a10,
    reg2a11,reg2a12,reg2a13,reg2a14,reg2a15}<={reg1a0,reg1a1,reg1a2,reg1a3,reg1a4,reg1a5,
    reg1a6,reg1a7,reg1a8,reg1a9,reg1a10,reg1a11,reg1a12,reg1a13,reg1a14,reg1a15};
    
    {reg3a0,reg3a1,reg3a2,reg3a3,reg3a4,reg3a5,reg3a6,reg3a7,reg3a8,reg3a9,reg3a10,reg3a11,reg3a12,reg3a13,reg3a14,reg3a15}
    <={reg2a0,reg2a1,reg2a2,reg2a3,reg2a4,reg2a5,reg2a6,reg2a7,reg2a8,reg2a9,reg2a10,
    reg2a11,reg2a12,reg2a13,reg2a14,reg2a15};
    
    {reg4a0,reg4a1,reg4a2,reg4a3,reg4a4,reg4a5,reg4a6,reg4a7,reg4a8,reg4a9,reg4a10,reg4a11,reg4a12,reg4a13,reg4a14,reg4a15}
    <={reg3a0,reg3a1,reg3a2,reg3a3,reg3a4,reg3a5,reg3a6,reg3a7,reg3a8,reg3a9,reg3a10,reg3a11,reg3a12,reg3a13,reg3a14,reg3a15};
    
        {reg5a0,reg5a1,reg5a2,reg5a3,reg5a4,reg5a5,reg5a6,reg5a7,reg5a8,reg5a9,reg5a10,reg5a11,reg5a12,reg5a13,reg5a14,reg5a15}
    <={reg4a0,reg4a1,reg4a2,reg4a3,reg4a4,reg4a5,reg4a6,reg4a7,reg4a8,reg4a9,reg4a10,reg4a11,reg4a12,reg4a13,reg4a14,reg4a15};
    
    {reg6a0,reg6a1,reg6a2,reg6a3,reg6a4,reg6a5,reg6a6,reg6a7,reg6a8,reg6a9,reg6a10,reg6a11,reg6a12,reg6a13,reg6a14,reg6a15}
    <={reg5a0,reg5a1,reg5a2,reg5a3,reg5a4,reg5a5,reg5a6,reg5a7,reg5a8,reg5a9,reg5a10,reg5a11,reg5a12,reg5a13,reg5a14,reg5a15};
    
        {reg7a0,reg7a1,reg7a2,reg7a3,reg7a4,reg7a5,reg7a6,reg7a7,reg7a8,reg7a9,reg7a10,reg7a11,reg7a12,reg7a13,reg7a14,reg7a15}
    <={reg6a0,reg6a1,reg6a2,reg6a3,reg6a4,reg6a5,reg6a6,reg6a7,reg6a8,reg6a9,reg6a10,reg6a11,reg6a12,reg6a13,reg6a14,reg6a15};
    
            {reg8a0,reg8a1,reg8a2,reg8a3,reg8a4,reg8a5,reg8a6,reg8a7,reg8a8,reg8a9,reg8a10,reg8a11,reg8a12,reg8a13,reg8a14,reg8a15}
    <={reg7a0,reg7a1,reg7a2,reg7a3,reg7a4,reg7a5,reg7a6,reg7a7,reg7a8,reg7a9,reg7a10,reg7a11,reg7a12,reg7a13,reg7a14,reg7a15};
    
    {out0,out1,out2,out3,out4,out5,out6,out7,out8,out9,out10,out11,out12,out13,out14,out15}
    <={reg8a0,reg8a1,reg8a2,reg8a3,reg8a4,reg8a5,reg8a6,reg8a7,reg8a8,reg8a9,reg8a10,reg8a11,reg8a12,reg8a13,reg8a14,reg8a15};
end

endmodule
