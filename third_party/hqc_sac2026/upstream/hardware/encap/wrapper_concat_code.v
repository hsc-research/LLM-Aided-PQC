`timescale 1ns / 1ps

`define CLOG2(x) ( \
  (x <= 2) ? 1 : \
  (x <= 4) ? 2 : \
  (x <= 8) ? 3 : \
  (x <= 16) ? 4 : \
  (x <= 32) ? 5 : \
  (x <= 64) ? 6 : \
  (x <= 128) ? 7 : \
  (x <= 256) ? 8 : \
  (x <= 512) ? 9 : \
  (x <= 1024) ? 10 : \
  (x <= 2048) ? 11 : \
  (x <= 4096) ? 12 : \
  (x <= 8192) ? 13 : \
  (x <= 16384) ? 14 : \
  (x <= 32768) ? 15 : \
  (x <= 65536) ? 16 : \
  (x <= 131072) ? 17 : \
  (x <= 262144) ? 18 : \
  (x <= 524288) ? 19 : \
  (x <= 1048576) ? 20 : \
  (x <= 2097152) ? 21 : \
  (x <= 4194304) ? 22 : \
  (x <= 8388608) ? 23 : \
  (x <= 16777216) ? 24 : \
  (x <= 33554432) ? 25 : \
  (x <= 67108864) ? 26 : \
  (x <= 134217728) ? 27 : \
  (x <= 268435456) ? 28 : \
  (x <= 536870912) ? 29 : \
  (x <= 1073741824) ? 30 : \
  -1)

module concat_code_wrapper #(
    parameter parameter_set = "hqc192",
    parameter OUT_WIDTH_BITS = 128,

    parameter N1_BYTES = (parameter_set == "hqc128")? 46:
                         (parameter_set == "hqc192")? 56:
                         (parameter_set == "hqc256")? 90: 46,
    parameter K_BYTES = (parameter_set == "hqc128")? 16:
                        (parameter_set == "hqc192")? 24:
                        (parameter_set == "hqc256")? 32: 16,
    parameter N1 = 8 * N1_BYTES,
    parameter K  = 8 * K_BYTES,
    parameter LOG_N1_BYTES = `CLOG2(N1_BYTES),

    // --- REPETITION PARAMETER ---
    parameter REP_COUNT = (parameter_set == "hqc128")? 3 : 5,

    // Derived parameters
    localparam INNER_WORD_BITS  = 128,
    localparam INNER_WORD_BYTES = INNER_WORD_BITS / 8, // 16
    localparam OUT_BYTES        = OUT_WIDTH_BITS / 8,
    
    // Total bytes increases by REP_COUNT (used for index calculation bounds)
    localparam TOTAL_BYTES      = N1_BYTES * INNER_WORD_BYTES * REP_COUNT,
    
    localparam NUM_OUT_CHUNKS   = (TOTAL_BYTES + OUT_BYTES - 1) / OUT_BYTES,
    localparam LOG_OUT_ADDR     = `CLOG2(NUM_OUT_CHUNKS)
) (
    input  clk,
    input  rst,
    input  start,
    input  [K-1:0] msg_in,
    input  out_en,
    input  [LOG_OUT_ADDR-1:0] out_addr,
    output [OUT_WIDTH_BITS-1:0] data_out,
    output done
);

    wire [127:0] inner_cdw_out;
    wire inner_done;

    // OPTIMIZATION: Instead of storing TOTAL_BYTES (which includes repetition),
    // we only store the unique blocks. We handle repetition during the READ phase.
    // This reduces register usage by factor of REP_COUNT (3x or 5x).
    // Using 128-bit width helps synthesis tools infer Block RAM.
    reg [127:0] compressed_mem [0: N1_BYTES-1];

    reg buffering_done;
    reg out_ready;

    reg [LOG_N1_BYTES-1:0] block_idx;
    reg inner_cdw_out_en;
    reg [LOG_N1_BYTES-1:0] inner_cdw_out_addr;

    reg [OUT_WIDTH_BITS-1:0] data_out_reg;

    integer init_idx;

    concat_code #(
        .parameter_set(parameter_set)
    ) concat_code_inst (
        .clk(clk),
        .rst(rst),
        .start(start),
        .msg_in(msg_in),
        .cdw_out_en(inner_cdw_out_en),
        .cdw_out_addr(inner_cdw_out_addr),
        .cdw_out(inner_cdw_out),
        .done(inner_done)
    );

    // buffering FSM
    localparam B_IDLE = 2'd0;
    localparam B_REQ  = 2'd1;
    localparam B_WAIT = 2'd2;
    localparam B_DONE = 2'd3;

    reg [1:0] buf_state;

    always @(posedge clk) begin
        if (rst) begin
            buf_state <= B_IDLE;
            buffering_done <= 1'b0;
            out_ready <= 1'b0;
            block_idx <= {LOG_N1_BYTES{1'b0}};
            inner_cdw_out_en <= 1'b0;
            inner_cdw_out_addr <= {LOG_N1_BYTES{1'b0}};
            
            // Initialization: Clearing the smaller memory is faster
            for (init_idx = 0; init_idx < N1_BYTES; init_idx = init_idx + 1) begin
                compressed_mem[init_idx] <= 128'b0;
            end

        end else if (start) begin
            buf_state <= B_IDLE;
            buffering_done <= 1'b0;
            out_ready <= 1'b0;
            block_idx <= {LOG_N1_BYTES{1'b0}};
            inner_cdw_out_en <= 1'b0;
            inner_cdw_out_addr <= {LOG_N1_BYTES{1'b0}};
            
            for (init_idx = 0; init_idx < N1_BYTES; init_idx = init_idx + 1) begin
                compressed_mem[init_idx] <= 128'b0;
            end

        end else begin
            case (buf_state)
                B_IDLE: begin
                    if (inner_done && !buffering_done) begin
                        block_idx <= {LOG_N1_BYTES{1'b0}};
                        inner_cdw_out_addr <= {LOG_N1_BYTES{1'b0}};
                        inner_cdw_out_en <= 1'b1;
                        buf_state <= B_REQ;
                    end
                end

                B_REQ: begin
                    inner_cdw_out_en <= 1'b0;
                    buf_state <= B_WAIT;
                end

                B_WAIT: begin
                    // OPTIMIZATION: Write ONLY ONCE. 
                    // We do not loop here. We store the unique block.
                    // The repetition is virtualized in the read logic.
                    compressed_mem[block_idx] <= inner_cdw_out;

                    if (block_idx + 1 < N1_BYTES) begin
                        block_idx <= block_idx + 1;
                        inner_cdw_out_addr <= block_idx + 1;
                        inner_cdw_out_en <= 1'b1;
                        buf_state <= B_REQ;
                    end else begin
                        buffering_done <= 1'b1;
                        out_ready <= 1'b1;
                        inner_cdw_out_en <= 1'b0;
                        buf_state <= B_DONE;
                    end
                end

                B_DONE: begin
                    inner_cdw_out_en <= 1'b0;
                end

                default: buf_state <= B_IDLE;
            endcase
        end
    end

    // --- Output Logic ---
    // Update: Logic generalized to support any OUT_WIDTH_BITS (e.g. 256).
    // It reconstructs the output byte-by-byte from the compressed memory.
    
    integer out_b;
    
    always @(posedge clk) begin
        if (rst || start) begin
            data_out_reg <= {OUT_WIDTH_BITS{1'b0}};
        end else if (out_en && out_ready) begin
            // We iterate through every byte of the requested output.
            // For each byte, we calculate exactly where it lives in the compressed memory.
            for (out_b = 0; out_b < OUT_BYTES; out_b = out_b + 1) begin
                if ((out_addr * OUT_BYTES + out_b) < TOTAL_BYTES) begin
                    // Index Calculation Breakdown:
                    // 1. (out_addr * OUT_BYTES + out_b) -> The absolute byte index in the virtual uncompressed stream.
                    // 2. / 16 -> Maps to the "Virtual Block Index" (since blocks are 16 bytes).
                    // 3. / REP_COUNT -> Maps Virtual Block to the unique "Physical Block Index".
                    // 4. % 16 -> Finds the byte offset within that Physical Block.
                    data_out_reg[out_b*8 +: 8] <= compressed_mem[ ((out_addr * OUT_BYTES + out_b) / 16) / REP_COUNT ][ ((out_addr * OUT_BYTES + out_b) % 16)*8 +: 8 ];
                end else begin
                    data_out_reg[out_b*8 +: 8] <= 8'b0;
                end
            end
        end
    end

    assign data_out = data_out_reg;
    assign done = buffering_done && out_ready;

endmodule
