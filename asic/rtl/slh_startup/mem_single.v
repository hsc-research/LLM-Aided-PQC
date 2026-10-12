// Derived from SPHINCSLET mem_single. No production top instance uses it.
// Explicit boot initialization retains read-first behavior and DEPTH words.
module mem_single #(
  parameter WIDTH = 8, parameter DEPTH = 64,
  parameter FILE = "", parameter INIT = 0
)(
  input wire clock,
  input wire i_boot_reset,
  output wire o_boot_ready,
  input wire [WIDTH-1:0] data,
  input wire [`CLOG2(DEPTH)-1:0] address,
  input wire wr_en,
  output reg [WIDTH-1:0] q
);
  reg [WIDTH-1:0] mem [DEPTH-1:0];
  wire boot_scrub;
  wire [`CLOG2(DEPTH)-1:0] boot_address;
  generate
    if (FILE != "") begin: unsupported_file
      SLH_ASIC_RUNTIME_FILE_LOADING_IS_NOT_SUPPORTED invalid_configuration();
    end
    if (INIT) begin: initialized_memory
      reg [`CLOG2(DEPTH)-1:0] address;
      reg done;
      assign boot_address = address;
      assign boot_scrub = !i_boot_reset && !done;
      assign o_boot_ready = !i_boot_reset && done;
      always @(posedge clock) begin
        if (i_boot_reset) begin address <= 0; done <= 1'b0; end
        else if (!done) begin
          if (address == DEPTH-1) done <= 1'b1;
          else address <= address + 1'b1;
        end
      end
    end else begin: uninitialized_memory
      assign boot_address = 0;
      assign boot_scrub = 1'b0;
      assign o_boot_ready = !i_boot_reset;
    end
  endgenerate
  always @(posedge clock) begin
    if (boot_scrub) mem[boot_address] <= {WIDTH{1'b0}};
    else if (o_boot_ready) begin
      if (wr_en) mem[address] <= data;
      q <= mem[address];
    end
  end
endmodule
