/*
 * Dual-ported memory module. Public domain, derived from SPHINCSLET.
 * ASIC derivative: explicit boot scrub replaces FPGA power-up initialization.
 */
module mem_dual #(
  parameter WIDTH = 128,
  parameter DEPTH = 128,
  parameter FILE = "",
  parameter INIT = 1
)(
  input wire clock,
  input wire i_boot_reset,
  output wire o_boot_ready,
  input wire [WIDTH-1:0] data_0, data_1,
  input wire [`CLOG2(DEPTH)-1:0] address_0, address_1,
  input wire wren_0, wren_1,
  output reg [WIDTH-1:0] q_0, q_1
);
  // Preserve the vendor's inclusive upper bound, including its extra word.
  reg [WIDTH-1:0] mem [0:DEPTH];
  wire boot_scrub;
  wire [`CLOG2(DEPTH+1)-1:0] boot_address;
  generate
    if (FILE != "") begin: unsupported_file
      SLH_ASIC_RUNTIME_FILE_LOADING_IS_NOT_SUPPORTED invalid_configuration();
    end
    if (INIT) begin: initialized_memory
      reg [`CLOG2(DEPTH+1)-1:0] address;
      reg done;
      assign boot_address = address;
      assign boot_scrub = !i_boot_reset && !done;
      assign o_boot_ready = !i_boot_reset && done;
      always @(posedge clock) begin
        if (i_boot_reset) begin
          address <= 0;
          done <= 1'b0;
        end else if (!done) begin
          if (address == DEPTH) done <= 1'b1;
          else address <= address + 1'b1;
        end
      end
    end else begin: uninitialized_memory
      assign boot_address = 0;
      assign boot_scrub = 1'b0;
      assign o_boot_ready = !i_boot_reset;
    end
  endgenerate

  // Full address-space view; invalid addresses remain explicit don't-cares.
  // Padding is wiring/constants only, never additional storage.
  wire [WIDTH-1:0] read_view [0:(1 << `CLOG2(DEPTH))-1];
  genvar read_word;
  generate for (read_word=0;read_word<(1 << `CLOG2(DEPTH));read_word=read_word+1) begin: read_decoder
    if (read_word <= DEPTH) assign read_view[read_word] = mem[read_word];
    else assign read_view[read_word] = {WIDTH{1'bx}};
  end endgenerate

  // Boot owns port 0. Output registers are invalid until normal reads start.
  // After boot these are exactly the original independent clocked processes:
  // local write-first, opposite-port read-old, no dual-write priority promise.
  always @(posedge clock) begin
    if (boot_scrub) mem[boot_address] <= {WIDTH{1'b0}};
    else if (o_boot_ready) begin
      if (wren_0) begin
        mem[address_0] <= data_0;
        q_0 <= data_0;
      end else q_0 <= read_view[address_0];
    end
  end
  always @(posedge clock) begin
    if (o_boot_ready) begin
      if (wren_1) begin
        mem[address_1] <= data_1;
        q_1 <= data_1;
      end else q_1 <= read_view[address_1];
    end
  end
endmodule
