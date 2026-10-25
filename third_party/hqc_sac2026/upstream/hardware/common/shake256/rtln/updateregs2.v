`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 05/06/2025 07:08:40 PM
// Design Name: 
// Module Name: updateregs2
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


module updateregs2(regs,message,regs1);
input [1599:0] regs;
input [527:0] message;
output [1599:0] regs1;

//genvar i;
//generate
//for (i=0;i<32;i=i+1) begin
    //xor_block XOR(regs[((i<<3)+7):(i<<3)], message[((i<<3)+7):(i<<3)], regs1[((i<<3)+7):(i<<3)]);
assign regs1=regs^{1072'd0,message};
endmodule
