module Keccak_state_func(keccakin, keccakout, finish, clk, rst);
input clk, rst;
input [1599:0] keccakin;
output [1599:0] keccakout;
output finish;
wire [7:0] count;

counter COUNTER(clk, rst, count);

Keccak_F1600 KECCAK(keccakin, keccakout, finish, count, clk, rst);

endmodule

