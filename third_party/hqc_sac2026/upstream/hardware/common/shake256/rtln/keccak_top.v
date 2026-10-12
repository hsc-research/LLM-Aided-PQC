`timescale 1ns / 1ps

module keccak_top (
    input  wire            clk,
    input  wire            rst,
    input  wire            din_valid,
    output wire            din_ready, 
    input  wire [31:0]     din,
    output reg             dout_valid,
    input  wire            dout_ready,
    output wire [31:0]     dout,
    input  wire            force_done,
    output reg             force_done_ack
);

    reg  [1599:0] state;
    wire [1599:0] perm_out_raw; 
    wire          perm_finish;
    reg           perm_rst;
    
    reg first_perm;
    
    wire [1599:0] state_rev;
    rev_bytes_1600 rev_state(state_rev, state, !first_perm, clk);
    
    reg [29:0] req_bytes;     
    reg [10:0] rate_words;    
    reg [10:0] bits_in_block; 
    reg is_last_block; 
    reg [10:0] word_count;    
    reg [10:0] words_needed;  
    reg mode_256;

    // Added S_WAIT_EXTRA (State 8) to handle the pause between squeezes
    localparam S_IDLE=0, S_LENGTH=2, S_ABSORB=3, S_PAD=4, S_PERMUTE=5, S_UPDATE=6, S_SQUEEZE=7, S_WAIT_EXTRA=8, S_PIPE = 9;
    reg [3:0] current_state;

    function [31:0] swap_nibbles;
        input [31:0] in;
        integer i;
        begin
            for (i = 0; i < 4; i = i + 1) begin
                swap_nibbles[i*8 +: 4]   = in[i*8+4 +: 4]; 
                swap_nibbles[i*8+4 +: 4] = in[i*8 +: 4];   
            end
        end
    endfunction
    
    assign dout = (current_state == S_SQUEEZE) ? swap_nibbles(state[word_count*32 +: 32]) : 32'b0;

    // Updated din_ready to be high during S_WAIT_EXTRA so we can receive the new length header
    assign din_ready = (current_state == S_IDLE || current_state == S_LENGTH || current_state == S_WAIT_EXTRA || (current_state == S_ABSORB && word_count < words_needed));
    
    Keccak_state_func core_inst (.keccakin(state_rev), .keccakout(perm_out_raw), .finish(perm_finish), .clk(clk), .rst(perm_rst));

    always @(posedge clk) begin
        if (rst || force_done) begin
            is_last_block <= 0;
            first_perm <= 1;
            current_state <= S_IDLE;
            state <= 0; dout_valid <= 0; word_count <= 0; perm_rst <= 1;
            force_done_ack <= force_done;
        end else begin
            force_done_ack <= 0;
            case (current_state)
                S_IDLE: begin
                    first_perm <= 1;
                    perm_rst <= 1; state <= 0;
                    if (din_valid && din_ready) begin
                        req_bytes <= din[29:0];
                        mode_256 <= din[30];
                        rate_words <= (din[30]) ? 34 : 42; 
                        current_state <= S_LENGTH;
                    end
                end

                S_LENGTH: begin
                    if (din_valid && din_ready) begin
                        is_last_block <= din[31];
                        bits_in_block <= din[10:0];
                        words_needed  <= (din[10:0] + 31) >> 5;
                        word_count    <= 0;
                        current_state <= S_ABSORB;
                    end
                end

                S_ABSORB: begin
                    if (word_count < words_needed) begin
                        if (din_valid && din_ready) begin
                            state[word_count*32 +: 32] <= state[word_count*32 +: 32] ^ (first_perm ? din : swap_nibbles(din));
                            word_count <= word_count + 1;
                        end
                    end else begin
                        current_state <= (is_last_block) ? S_PAD : S_PERMUTE;
                    end
                end

                S_PAD: begin
                    state[(bits_in_block/8)*8 +: 8] <= state[(bits_in_block/8)*8 +: 8] ^ (first_perm ? 8'h1F : 8'hF1);
                    state[((mode_256?1088:1344)/8 - 1)*8 +: 8] <= state[((mode_256?1088:1344)/8 - 1)*8 +: 8] ^ (first_perm ? 8'h80 : 8'h08);
                    
                    current_state <= S_PERMUTE;
                end

                S_PERMUTE: begin             
                    perm_rst <= 0;
                    if (perm_finish) begin
                        state <= perm_out_raw; 
                        perm_rst <= 1; 
                        word_count <= 0;
                        first_perm <= 0; 
                        current_state <= (is_last_block) ? S_SQUEEZE : S_LENGTH;
                    end
                end
                
                S_UPDATE: begin
                    // Placeholder state from original code
                end

                S_SQUEEZE: begin
                   if (req_bytes > 0) begin
                        dout_valid <= 1;
                        if (dout_ready && dout_valid) begin
                            if (word_count == (rate_words - 1)) begin
                                dout_valid <= 0;                                 
                                if (req_bytes >= 32) begin
                                    req_bytes <= req_bytes - 32; 
                                    current_state <= S_PERMUTE;
                                end else begin
                                    req_bytes <= 0; 
                                    current_state <= S_WAIT_EXTRA; 
                                end
                            end else begin
                                word_count <= word_count + 1;
                                if (req_bytes <= 32) begin
                                    req_bytes <= 0;
                                    dout_valid <= 0; 
 
                                    current_state <= S_WAIT_EXTRA; 
                                end else begin
                                    req_bytes <= req_bytes - 32;
                                end
                            end
                        end
                    end else begin
                        dout_valid <= 0;
                        current_state <= S_WAIT_EXTRA; 
                    end
                end

                S_WAIT_EXTRA: begin
                    dout_valid <= 0;
                    if (din_valid && din_ready) begin                      
                        req_bytes <= din[29:0];

                        current_state <= S_SQUEEZE;
                    end
                end
                
                	


            endcase
        end
    end
endmodule
