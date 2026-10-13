module corrected(input [2:0] sec_lvl, input [511:0] C_SIPO,
        output reg [10:0] W1_LEN, output reg [9:0] C_SIPO_START,
        output reg [7:0] TAU, output reg [31:0] ctilde_out_len,
        output reg [63:0] ch);
    always @(*) begin
        
        
        case(sec_lvl)
        2: begin
             W1_LEN = 4*192/8;
             TAU = 39;
             ctilde_out_len = 32*8;
             ch = C_SIPO[256 - 1 -: 64];
             C_SIPO_START = 256;
        end
        3: begin
            W1_LEN = 6*256/8/2; 
            TAU = 49;
            ctilde_out_len = 48*8;
            ch = C_SIPO[384 - 1 -: 64];
            C_SIPO_START = 384;
        end
        5: begin
             W1_LEN = 8*256/8/2; 
             TAU = 60;
             ctilde_out_len = 64*8;
             ch = C_SIPO[512 - 1 -: 64];
             C_SIPO_START = 512;
        end
        default: begin
            W1_LEN = 0;
            TAU    = 0;
            ctilde_out_len = 0;
            C_SIPO_START = 0;
            ch = 0;
        end
        endcase
    end
    
endmodule
