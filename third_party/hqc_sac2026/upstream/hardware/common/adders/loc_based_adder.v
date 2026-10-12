`timescale 1ns / 1ps

module loc_based_adder
    #(
    parameter parameter_set = "hqc128",
    parameter N = (parameter_set == "hqc128")? 17_669:
                  (parameter_set == "hqc192")? 35_851:
                  (parameter_set == "hqc256")? 57_637: 17_669,
    
    parameter M = (parameter_set == "hqc128")? 15:
                  (parameter_set == "hqc192")? 16:
                  (parameter_set == "hqc256")? 16: 15, 

    parameter WEIGHT = (parameter_set == "hqc128")? 66:
                       (parameter_set == "hqc192")? 100:
                       (parameter_set == "hqc256")? 131: 66,
    
    parameter WIDTH = 32,
    parameter N_MEM = N + (WIDTH - N%WIDTH)%WIDTH, 
    parameter DEPTH = N_MEM/WIDTH,
    parameter LOG_DEPTH = `CLOG2(DEPTH),    
    parameter LOG_WEIGHT   = `CLOG2(WEIGHT)
    )
    (
    input clk,
    input rst,
    
    input [(M-1):0] location,
    output reg [LOG_WEIGHT-1:0] loc_rd_addr,
    output reg loc_rd_en,
    
    input [(WIDTH-1):0] pm_in,
    output  [LOG_DEPTH-1:0] pm_rd_addr,
    output reg pm_rd_en,
  
    input start,
    
    output wire [(WIDTH-1):0] add_out,
    output wire [LOG_DEPTH-1:0] add_out_addr,
    output wire add_out_valid,
    
    output wire done
    );

reg [(M-1):0] location_reg;
wire [WIDTH-1:0] gen_one;

// Pipeline Registers for Data Path
reg  [WIDTH-1:0] gen_one_reg;
wire [LOG_DEPTH -1:0] decode_addr;

// Original Control Registers
reg add_out_valid_reg;
reg [LOG_DEPTH-1:0] add_out_addr_reg;
reg done_reg;

// -------------------------------------------------------------------------
// PIPELINE ALIGNMENT (1 Cycle Delay)
// -------------------------------------------------------------------------
// The new data path has 1 cycle extra latency compared to original.
// Original: Valid @ T2.
// New:      Valid @ T3.
// Fix:      Delay control signals by 1 cycle.
reg add_out_valid_pipe;
reg done_pipe;

// Below are states
parameter s_wait_start             =   0;
parameter s_load_loc               =   1;
parameter s_stall                  =   2;
parameter s_stall_1                =   3;

reg [3:0] state     = 0;
genvar i;

  generate
    for (i = 0; i < WIDTH; i=i+1) begin:vector_gen
        // Logic now depends on the registered location (Cycle 1)
        assign gen_one[i] = (i == location_reg[`CLOG2(WIDTH-1)-1:0]) ? 1'b1 : 1'b0; 
    end
  endgenerate
  
  // STEP 1: Break Input Timing Path
  // Latches data at Cycle 1.
  always@(posedge clk) begin
    location_reg <= location;
  end 

  // STEP 2: Register Mask for XOR
  // Latches mask at Cycle 2. (Used for XOR in Cycle 3).
  always@(posedge clk) begin
    gen_one_reg <= gen_one;
  end 
  
  // STEP 3: Control Signal Pipeline
  // Delays valid and done by 1 cycle to match Data at Cycle 3.
  always @(posedge clk) begin
      add_out_valid_pipe <= add_out_valid_reg;
      done_pipe          <= done_reg;
  end

  // Output Assignments
  assign add_out = gen_one_reg ^ pm_in; // XOR happens at Cycle 3
  assign add_out_valid = add_out_valid_pipe; // Valid at Cycle 3
  assign done = done_pipe;                   // Done delayed to allow pipeline flush
  assign add_out_addr = add_out_addr_reg;    // Address logic handles its own timing below

  // Address Decoding
  // Using location_reg (Cycle 1) breaks the critical path to memory
  assign decode_addr = location_reg[M-1:`CLOG2(WIDTH)]; 
  assign pm_rd_addr = decode_addr;

  // Address Registration
  // Captures decode_addr (Cycle 2 availability) -> available at Cycle 3.
  // This naturally aligns with the 1-cycle control delay, so no extra pipe needed here.
  always@(posedge clk)
  begin
    if (pm_rd_en == 1'b1) begin
        add_out_addr_reg <= decode_addr;
    end
  end  
    
  always@(posedge clk)
  begin
    if (rst) begin
        state <= s_wait_start;
        loc_rd_addr <= 0;
        add_out_valid_reg <= 0;
        done_reg<= 0;
    end
    else begin
         if (state == s_wait_start) begin
            add_out_valid_reg <= 0;
            loc_rd_addr <= 0;
            done_reg<= 0;
            if (start) begin 
                state <=  s_load_loc;
            end
         end
         
         else if (state == s_stall_1) begin
            state <=  s_load_loc;
            add_out_valid_reg <= 0;
            done_reg<= 0; 
         end
         
         else if (state == s_load_loc) begin
            done_reg<= 0;
            if (loc_rd_addr == WEIGHT-1) begin
                state <= s_stall;
                add_out_valid_reg <= 1;
            end
            else begin
                loc_rd_addr <= loc_rd_addr + 1;
                add_out_valid_reg <= 1;
                state <= s_stall_1;
            end  
         end
         
         else if (state == s_stall) begin
            state <=  s_wait_start;
            add_out_valid_reg <= 0;
            done_reg <= 1;
         end
    end
    // Note: done_reg_reg was removed as we are now using explicit pipeline `done_pipe`
  end 

always@(state or start)
begin
    case (state)
      s_wait_start: begin
                        if (start) begin
                            loc_rd_en <= 1'b1;
                            pm_rd_en <= 1'b0;
                        end
                        else begin
                            loc_rd_en <= 1'b0;
                            pm_rd_en <= 1'b0;
                        end
                    end  
      s_load_loc: begin
                    loc_rd_en <= 1'b1;
                    pm_rd_en <= 1'b1;
                  end 
      s_stall_1: begin
                    loc_rd_en <= 1'b1;
                    pm_rd_en <= 1'b1;
                  end 
       s_stall: begin
                    loc_rd_en <= 1'b0;
                    pm_rd_en <= 1'b1;
                   end
      default: begin
                loc_rd_en <= 1'b0;
                pm_rd_en <= 1'b0;
      end
    endcase
end     
endmodule
