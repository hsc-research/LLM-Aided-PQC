module ROL(offset, a, b);
input [6:0] offset;
input [63:0] a;
output [63:0] b;
wire [6:0] offset1;

assign offset1=7'd64-offset[6:0];

    assign b = (a << offset[6:0]) ^ (a >> (offset1)); 
//assign b=(a>>63)+(a<<1);
//out=(c>>63)+(c<<1);

endmodule
