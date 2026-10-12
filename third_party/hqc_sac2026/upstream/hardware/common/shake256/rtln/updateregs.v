`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 07.06.2024 13:04:41
// Design Name: 
// Module Name: updateregs
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

module updateregs(regs,message,regs1);
input [1599:0] regs;
input [271:0] message;
output [1599:0] regs1;

//genvar i;
//generate
//for (i=0;i<32;i=i+1) begin
    //xor_block XOR(regs[((i<<3)+7):(i<<3)], message[((i<<3)+7):(i<<3)], regs1[((i<<3)+7):(i<<3)]);
assign regs1=regs^{1328'd0,message};
//end
//endgenerate

//assign regs1[1599:256]=0;

endmodule
