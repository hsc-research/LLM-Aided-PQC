
module mem_dual_2r1w
#(
  parameter WIDTH = 512,
  parameter DEPTH = 70,
  parameter FILE  = "",
  parameter INIT  = 0
)
(
  input  wire                         clock,


  input  wire [WIDTH-1:0]             wdata,
  input  wire [`CLOG2(DEPTH)-1:0]     waddr,
  input  wire                         wren,       


  input  wire [`CLOG2(DEPTH)-1:0]     address_0,
  input  wire [`CLOG2(DEPTH)-1:0]     address_1,
  output reg  [WIDTH-1:0]             q_0,
  output reg  [WIDTH-1:0]             q_1
);

  (* ram_style = "distributed" *) reg [WIDTH-1:0] mem [0:DEPTH-1];
  integer i;
  initial begin
    if (FILE != "")
      $readmemb(FILE, mem);
    else if (INIT)
      for (i = 0; i < DEPTH; i = i + 1)
        mem[i] = {WIDTH{1'b0}};
  end


  always @(posedge clock) begin
    if (wren) begin
      mem[waddr] <= wdata;
    end

  
    if (wren)
      q_0 <= wdata;
    else
      q_0 <= mem[address_0];


    if (wren && (waddr == address_1))
      q_1 <= wdata;
    else
      q_1 <= mem[address_1];
  end

endmodule
