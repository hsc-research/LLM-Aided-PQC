module probe #(parameter DEPTH = 64)
(
  input wire clk,
  input wire [`CLOG2(DEPTH)-1:0] addr,
  output reg q
);
  always @(posedge clk) q <= ^addr;
endmodule
