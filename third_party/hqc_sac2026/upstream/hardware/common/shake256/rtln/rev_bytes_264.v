`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/25/2024 11:40:06 PM
// Design Name: 
// Module Name: rev_bytes_264
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


module rev_bytes_264(message,message1);
input [271:0] message1;
output [271:0] message;

assign message[3:0]= message1[7:4];
assign message[7:4]= message1[3:0];
assign message[11:8]= message1[15:12];
assign message[15:12]= message1[11:8];
assign message[19:16]= message1[23:20];
assign message[23:20]= message1[19:16];
assign message[27:24]= message1[31:28];
assign message[31:28]= message1[27:24];
assign message[35:32]= message1[39:36];
assign message[39:36]= message1[35:32];
assign message[43:40]= message1[47:44];
assign message[47:44]= message1[43:40];
assign message[51:48]= message1[55:52];
assign message[55:52]= message1[51:48];
assign message[59:56]= message1[63:60];
assign message[63:60]= message1[59:56];
assign message[67:64]= message1[71:68];
assign message[71:68]= message1[67:64];
assign message[75:72]= message1[79:76];
assign message[79:76]= message1[75:72];
assign message[83:80]= message1[87:84];
assign message[87:84]= message1[83:80];
assign message[91:88]= message1[95:92];
assign message[95:92]= message1[91:88];
assign message[99:96]= message1[103:100];
assign message[103:100]= message1[99:96];
assign message[107:104]= message1[111:108];
assign message[111:108]= message1[107:104];
assign message[115:112]= message1[119:116];
assign message[119:116]= message1[115:112];
assign message[123:120]= message1[127:124];
assign message[127:124]= message1[123:120];
assign message[131:128]= message1[135:132];
assign message[135:132]= message1[131:128];
assign message[139:136]= message1[143:140];
assign message[143:140]= message1[139:136];
assign message[147:144]= message1[151:148];
assign message[151:148]= message1[147:144];
assign message[155:152]= message1[159:156];
assign message[159:156]= message1[155:152];
assign message[163:160]= message1[167:164];
assign message[167:164]= message1[163:160];
assign message[171:168]= message1[175:172];
assign message[175:172]= message1[171:168];
assign message[179:176]= message1[183:180];
assign message[183:180]= message1[179:176];
assign message[187:184]= message1[191:188];
assign message[191:188]= message1[187:184];
assign message[195:192]= message1[199:196];
assign message[199:196]= message1[195:192];
assign message[203:200]= message1[207:204];
assign message[207:204]= message1[203:200];
assign message[211:208]= message1[215:212];
assign message[215:212]= message1[211:208];
assign message[219:216]= message1[223:220];
assign message[223:220]= message1[219:216];
assign message[227:224]= message1[231:228];
assign message[231:228]= message1[227:224];
assign message[235:232]= message1[239:236];
assign message[239:236]= message1[235:232];
assign message[243:240]= message1[247:244];
assign message[247:244]= message1[243:240];
assign message[251:248]= message1[255:252];
assign message[255:252]= message1[251:248];
//assign message[259:256]= message1[263:260];
//assign message[263:260]= message1[259:256];
//assign message[267:264]= message1[271:268];
//assign message[271:268]= message1[267:264];
assign message[271:256]=message1[271:256];
endmodule
