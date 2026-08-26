/*
 * This file is the testbench for the XOR based Adder.
 *
 * Copyright (C) 2022
 * Authors: Sanjay Deshpande <sanjay.deshpande@yale.edu>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
 *
*/

// This file can be used to test the hash_tile module for all opcodes except H_MSG and PRF_MSG operations


`timescale 1ns/1ps
`include "clog2.v"
`include "setting.v"

module tb #(
parameter parameter_set = `PARAM_SET,   
parameter XMSS_H_param = 
                    (parameter_set == "128s") ? 4:
                    (parameter_set == "128f") ? 3:
                    (parameter_set == "192s") ? 4:
                    (parameter_set == "192f") ? 4:
                    (parameter_set == "256s") ? 4:
                    (parameter_set == "256f") ? 4: 4,
parameter XMSS_Node_num = 
                    (parameter_set == "128s") ? 13:
                    (parameter_set == "128f") ? 7:
                    (parameter_set == "192s") ? 15:
                    (parameter_set == "192f") ? 9:
                    (parameter_set == "256s") ? 15:
                    (parameter_set == "256f") ? 10: 15,
parameter SEED_num = 
                    (parameter_set == "128s") ? 128:
                    (parameter_set == "128f") ? 128:
                    (parameter_set == "192s") ? 192:
                    (parameter_set == "192f") ? 192:
                    (parameter_set == "256s") ? 256:
                    (parameter_set == "256f") ? 256:
                                                128,
parameter Height_XMSS = 
                    (parameter_set == "128s") ? 9:
                    (parameter_set == "128f") ? 3:
                    (parameter_set == "192s") ? 9:
                    (parameter_set == "192f") ? 3:
                    (parameter_set == "256s") ? 8:
                    (parameter_set == "256f") ? 4: 9,
parameter Height_FORS = 
                    (parameter_set == "128s") ? 12:
                    (parameter_set == "128f") ? 6:
                    (parameter_set == "192s") ? 14:
                    (parameter_set == "192f") ? 8:
                    (parameter_set == "256s") ? 14:
                    (parameter_set == "256f") ? 9: 12,
parameter Leaf_Node_Num_WOTS = 
                    (parameter_set == "128s") ? 512:
                    (parameter_set == "128f") ? 8:
                    (parameter_set == "192s") ? 512:
                    (parameter_set == "192f") ? 8:
                    (parameter_set == "256s") ? 256:
                    (parameter_set == "256f") ? 16: 512,
parameter Leaf_Node_Num_XMSS = 
                    (parameter_set == "128s") ? 128:
                    (parameter_set == "128f") ? 8:
                    (parameter_set == "192s") ? 128:
                    (parameter_set == "192f") ? 2:
                    (parameter_set == "256s") ? 64:
                    (parameter_set == "256f") ? 4: 128,
parameter Leaf_Node_Num_FORS = 
                    (parameter_set == "128s") ? 4096:
                    (parameter_set == "128f") ? 64:
                    (parameter_set == "192s") ? 16384:
                    (parameter_set == "192f") ? 256:
                    (parameter_set == "256s") ? 16384:
                    (parameter_set == "256f") ? 512: 64,
parameter INDICE_WD = 
                    (parameter_set == "128s") ? 16:
                    (parameter_set == "128f") ? 12:
                    (parameter_set == "192s") ? 19:
                    (parameter_set == "192f") ? 14:
                    (parameter_set == "256s") ? 19:
                    (parameter_set == "256f") ? 15: 15,                   
parameter WD = //address bit for max data length
                    (parameter_set == "128s") ? 7:
                    (parameter_set == "128f") ? 7:
                    (parameter_set == "192s") ? 8:
                    (parameter_set == "192f") ? 8:
                    (parameter_set == "256s") ? 9:
                    (parameter_set == "256f") ? 9: 9,
parameter N = 
                    (parameter_set == "128s") ? 16:
                    (parameter_set == "128f") ? 16:
                    (parameter_set == "192s") ? 24:
                    (parameter_set == "192f") ? 24:
                    (parameter_set == "256s") ? 32:
                    (parameter_set == "256f") ? 32: 16,                    
parameter D = 
                    (parameter_set == "128s") ? 7:
                    (parameter_set == "128f") ? 22:
                    (parameter_set == "192s") ? 7:
                    (parameter_set == "192f") ? 22:
                    (parameter_set == "256s") ? 8:
                    (parameter_set == "256f") ? 17: 7,
parameter K = 
                    (parameter_set == "128s") ? 14:
                    (parameter_set == "128f") ? 33:
                    (parameter_set == "192s") ? 17:
                    (parameter_set == "192f") ? 33:
                    (parameter_set == "256s") ? 22:
                    (parameter_set == "256f") ? 35: 14
);
reg clk = 0;
reg rst;

always 
    #5 clk = !clk;

integer fp;
integer i;
integer start_time, end_time;
integer log;

parameter PROJECT_NAME = "TECS_v8";
`ifdef SHAKE
    parameter HASH_DATA = "data_shake";
`else
    parameter HASH_DATA = "data_sha2";
`endif
`ifdef PARAM_128
    parameter PARAM_NUM = "128";
`endif
`ifdef PARAM_192
    parameter PARAM_NUM = "192";
`endif
`ifdef PARAM_256
    parameter PARAM_NUM = "256";
`endif


parameter SIG_FILE_r   = {"../../../../",PROJECT_NAME,".srcs/sources_1/imports/",HASH_DATA,"/SIG_file0_",parameter_set,"_w.hex"};
parameter SIG_FILE_w   = {"../../../../",PROJECT_NAME,".srcs/sources_1/imports/",HASH_DATA,"/SIG_file0_",parameter_set,"_w.hex"};
parameter MSG_FILE     = {"../../../../",PROJECT_NAME,".srcs/sources_1/imports/",HASH_DATA,"/SLH_msg_33B.hex"};
parameter SK_FILE      = {"../../../../",PROJECT_NAME,".srcs/sources_1/imports/",HASH_DATA,"/SLH_",parameter_set,"_SK.hex"};
parameter PK_FILE      = {"../../../../",PROJECT_NAME,".srcs/sources_1/imports/",HASH_DATA,"/SLH_",parameter_set,"_PK.hex"};
parameter OPTRAND_FILE = {"../../../../",PROJECT_NAME,".srcs/sources_1/imports/",HASH_DATA,"/",PARAM_NUM,"_optrand.hex"};


reg                 FSM_start;
wire                FSM_done;
wire                c_flag;
reg                 i_sig_mode;
reg  [12-1:0]       i_msg_in_size;//max: 3300 Bytes
reg  [SEED_num-1:0] SK_seed;
reg  [SEED_num-1:0] PK_seed;
reg  [ 8-1:0]       i_SK_seed;
reg  [ 8-1:0]       i_PK_seed;
reg                 seed_valid;
wire [64-1:0]       o_sig_data;
wire                o_sig_valid;
reg  [64-1:0]       sig_mem_in0;
reg  [13-1:0]       sig_mem_addr0;
reg                 sig_mem_wen0;
wire [64-1:0]       sig_mem_out1;
wire [13-1:0]       sig_mem_addr0_w;
reg  [64-1:0]       i_h_msg_mem_in0;
reg  [ 9-1:0]       i_h_msg_mem_addr0;
reg                 i_h_msg_mem_wen0;

top
top_md0 (
.clk                (clk                ),
.rstn               (!rst               ),
.i_msg_in_size      (i_msg_in_size      ),//input: msg size
.i_sig_mode         (i_sig_mode         ),//input: select sign or verify mode
.i_FSM_start        (FSM_start          ),//input: start
.o_FSM_done         (FSM_done           ),//output: done
.o_c_flag           (c_flag             ),//output: check flag for signature verification

.i_SK_seed          (i_SK_seed          ),//input: write SK.seed in the internal register
.i_PK_seed          (i_PK_seed          ),//input: write PK.seed in the internal register
.seed_valid         (seed_valid         ),//input: seed valid

.i_h_msg_mem_in0    (i_h_msg_mem_in0    ),//input: setting the sk/pk/msg data in the internal memory
.i_h_msg_mem_addr0  (i_h_msg_mem_addr0  ),//input: setting data address
.i_h_msg_mem_wen0   (i_h_msg_mem_wen0   ),//input: setting data valid

//-- signals for signature generation --//
.o_sig_data         (o_sig_data         ),//output: signature data
.o_sig_valid        (o_sig_valid        ),//output: signature data valid

//-- signals for signature verification --//
.sig_mem_addr0_w    (sig_mem_addr0_w    ),//output: read address for signature data
.sig_mem_out0       (sig_mem_out1       ) //input: signature data
);


integer fp_SK;
integer fp_PK;
integer fp_OPTRAND;
integer fp_MSG;
`ifdef PARAM_128
reg  [64-1:0] rdata1;
reg  [64-1:0] rdata2;
`endif
`ifdef PARAM_192
reg  [64-1:0] rdata1;
reg  [64-1:0] rdata2;
reg  [64-1:0] rdata3;
`endif
`ifdef PARAM_256
reg  [64-1:0] rdata1;
reg  [64-1:0] rdata2;
reg  [64-1:0] rdata3;
reg  [64-1:0] rdata4;
`endif
wire [12-1:0] mlen;
assign mlen = i_msg_in_size;


initial begin
    //-- initial reset --//
    rst <= 1'b1;
    FSM_start <= 1'b0;
    #100; 
    rst <= 1'b0;
    #100

    //-- file read start --//
    fp_SK      = $fopen(SK_FILE,"r");
    fp_PK      = $fopen(PK_FILE,"r");
    fp_OPTRAND = $fopen(OPTRAND_FILE,"r");
    fp_MSG     = $fopen(MSG_FILE,"r");
    i_msg_in_size <= 12'd33; //type the message length in Bytes

    i_h_msg_mem_in0 <= 64'h0;
    i_h_msg_mem_addr0 <= 9'd0-1;
    i_h_msg_mem_wen0 <= 1'b0;  
    seed_valid <= 1'b0;

    `ifdef PARAM_128
    $fscanf(fp_SK,"%h", rdata1);
    $fscanf(fp_SK,"%h", rdata2);
    SK_seed <= {rdata1,rdata2};
    `endif 
    `ifdef PARAM_192
    $fscanf(fp_SK,"%h", rdata1);
    $fscanf(fp_SK,"%h", rdata2);
    $fscanf(fp_SK,"%h", rdata3);
    SK_seed <= {rdata1,rdata2,rdata3};
    `endif 
    `ifdef PARAM_256
    $fscanf(fp_SK,"%h", rdata1);
    $fscanf(fp_SK,"%h", rdata2);
    $fscanf(fp_SK,"%h", rdata3);
    $fscanf(fp_SK,"%h", rdata4);
    SK_seed <= {rdata1,rdata2,rdata3,rdata4};
    `endif 

    for(i=0; i<(N/8); i=i+1) begin
        #10
        $fscanf(fp_SK,"%h", rdata1);
        i_h_msg_mem_in0 <= rdata1;
        i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1;
        i_h_msg_mem_wen0 <= 1'b1;
    end

    for(i=0; i<(N/8); i=i+1) begin
        #10
        $fscanf(fp_OPTRAND,"%h", rdata1);
        i_h_msg_mem_in0 <= rdata1;
        i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1;
        i_h_msg_mem_wen0 <= 1'b1;
    end

    `ifdef PARAM_128
    #10
    $fscanf(fp_PK,"%h", rdata1);
    $fscanf(fp_PK,"%h", rdata2);
    PK_seed <= {rdata1,rdata2};
    i_h_msg_mem_in0 <= rdata1;
    `ifdef SHAKE
        i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1 + (N/8);
    `else
        i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1 + (N/8) + 4;
    `endif
    i_h_msg_mem_wen0 <= 1'b1;
    #10
    i_h_msg_mem_in0 <= rdata2;
    i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1;
    i_h_msg_mem_wen0 <= 1'b1;
    `endif
    `ifdef PARAM_192
    #10
    $fscanf(fp_PK,"%h", rdata1);
    $fscanf(fp_PK,"%h", rdata2);
    $fscanf(fp_PK,"%h", rdata3);
    PK_seed <= {rdata1,rdata2,rdata3};
    i_h_msg_mem_in0 <= rdata1;
    `ifdef SHAKE
        i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1 + (N/8);
    `else
        i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1 + (N/8) + 8;
    `endif
    i_h_msg_mem_wen0 <= 1'b1;
    #10
    i_h_msg_mem_in0 <= rdata2;
    i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1;
    i_h_msg_mem_wen0 <= 1'b1;
    #10
    i_h_msg_mem_in0 <= rdata3;
    i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1;
    i_h_msg_mem_wen0 <= 1'b1;    
    `endif
    `ifdef PARAM_256
    #10
    $fscanf(fp_PK,"%h", rdata1);
    $fscanf(fp_PK,"%h", rdata2);
    $fscanf(fp_PK,"%h", rdata3);
    $fscanf(fp_PK,"%h", rdata4);
    PK_seed <= {rdata1,rdata2,rdata3,rdata4};
    i_h_msg_mem_in0 <= rdata1;
    `ifdef SHAKE
        i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1 + (N/8);
    `else
        i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1 + (N/8) + 8;
    `endif
    i_h_msg_mem_wen0 <= 1'b1;
    #10
    i_h_msg_mem_in0 <= rdata2;
    i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1;
    i_h_msg_mem_wen0 <= 1'b1;
    #10
    i_h_msg_mem_in0 <= rdata3;
    i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1;
    i_h_msg_mem_wen0 <= 1'b1;
    #10
    i_h_msg_mem_in0 <= rdata4;
    i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1;
    i_h_msg_mem_wen0 <= 1'b1;
    `endif        

    for(i=0; i<(N/8); i=i+1) begin
        #10
        $fscanf(fp_PK,"%h", rdata1);
        i_h_msg_mem_in0 <= rdata1;
        i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1;
        i_h_msg_mem_wen0 <= 1'b1;
    end      

    for(i=0; i<(mlen>>3); i=i+1) begin
        #10
        $fscanf(fp_MSG,"%h", rdata1);
        i_h_msg_mem_in0 <= rdata1;
        i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1;
        i_h_msg_mem_wen0 <= 1'b1;
    end 

    if((mlen-((mlen>>3)<<3)) > 0) begin
        #10
        $fscanf(fp_MSG,"%h", rdata1);
        i_h_msg_mem_in0 <= rdata1 << (64 - ((mlen-((mlen>>3)<<3))<<3));
        i_h_msg_mem_addr0 <= i_h_msg_mem_addr0 + 9'd1;
        i_h_msg_mem_wen0 <= 1'b1;
    end

    #10
    i_h_msg_mem_in0 <= 64'h0;
    i_h_msg_mem_addr0 <= 9'd0;
    i_h_msg_mem_wen0 <= 1'b0; 
    
    for(i=0; i<N+1; i=i+1) begin 
        #10
        SK_seed <= {8'd0,SK_seed[SEED_num-1:8]};
        i_SK_seed <= SK_seed[8-1:0];
        PK_seed <= {8'd0,PK_seed[SEED_num-1:8]};
        i_PK_seed <= PK_seed[8-1:0];
        seed_valid <= 1'b1;
    end   
    seed_valid <= 1'b0;

    #10
    $fclose(fp_SK);
    $fclose(fp_PK);
    $fclose(fp_OPTRAND);
    $fclose(fp_MSG);
    #100
    //-- file read done --//

    //-- main FSM start --//
    //-- signature genetation --//
    fp = $fopen(SIG_FILE_w,"w");
    i_sig_mode <= 1'b0;//0: signature generation, 1: signature verification
    FSM_start <= 1'b1;
    #10
    FSM_start <= 1'b0;

    
    //-- mode 1 test -- fors_sign() --//
    @(posedge top_md0.hm_o_hm_done);
    $display("start fors_sign(), mode 1");
    @(posedge top_md0.mti_next_start);
    $display("FORS tree # ",1,"/ ",K);
    for(i=1; i<K; i=i+1) begin       
        @(posedge top_md0.o_FORS_tree_one_done);
        $display("FORS tree # ",(i+1),"/ ",K);
    end    

    
    //-- mode 3 test -- thash() in fors_sign() --//
    @(posedge top_md0.XMSS_FSM_done);
    $display("start thash(), mode 3");    

    
    //-- mode 0 test -- tree_hash() in HT--//
    //-- it includes wots_sign() in HT   --//
    @(posedge top_md0.cl_start_next);
    $display("start tree_hash(), mode 0");    
    //-- iterate other HT layers --//
    $display("HT tree # ",1,"/ ",D);
    for(i=1; i<D; i=i+1) begin      
        @(posedge top_md0.cl_start_next);
        $display("HT tree # ",(i+1),"/ ",D);
    end

    @(posedge FSM_done);
    $display("sig gen done");
    #100
    $fclose(fp);
    #200
    //-- main FSM done --//


    //-- main FSM start --//
    //-- signature verification --//
    i_sig_mode <= 1'b1;//0: signature generation, 1: signature verification
    FSM_start <= 1'b1;
    #10
    FSM_start <= 1'b0;
 

    //-- mode 1 test -- fors_pk_from_sig() --//
    @(posedge top_md0.hm_o_hm_done);
    $display("start fors_pk_from_sig(), mode 1");
    @(posedge top_md0.mti_next_start);
    $display("FORS tree # ",1,"/ ",K);
    for(i=1; i<K; i=i+1) begin
        @(posedge top_md0.o_FORS_tree_one_done);
        $display("FORS tree # ",(i+1),"/ ",K);
    end    

    
    //-- mode 3 test -- thash() in fors_pk_from_sig() --//
    @(posedge top_md0.XMSS_FSM_done);
    $display("start thash(), mode 3");    

    
    //-- mode 0 test -- compute_root() in HT --//
    //-- it includes wots_pk_from_sig() in HT--//
    @(posedge top_md0.cl_start_next);
    $display("start compute_root(), mode 0");    
    //-- iterate other HT layers --//
    $display("HT tree # ",1,"/ ",D);
    for(i=1; i<D; i=i+1) begin      
        @(posedge top_md0.cl_start_next);
        $display("HT tree # ",(i+1),"/ ",D);
    end


    @(posedge FSM_done);   
    $display("sig verification done"); 
    if(c_flag) begin
        $display("The signature is not matched!");
    end
    else begin
        $display("The signature is matched!");
    end
    #10
    //-- main FSM done --//

    $finish;    
end

mem_dual #(
.WIDTH(64), 
.DEPTH(8192),
//.FILE(SIG_FILE_r), //when run verification-only with SIG file
.FILE(""),
.INIT(0)
) 
SIG_MEM (
.clock    (clk            ),
.data_0   (sig_mem_in0    ),
.data_1   (64'd0          ),
.address_0(sig_mem_addr0  ),
.address_1(sig_mem_addr0_w),
.wren_0   (sig_mem_wen0   ),
.wren_1   (1'b0           ),
.q_0      (               ),
.q_1      (sig_mem_out1   )
);

initial begin
    sig_mem_in0   <= 64'h0;
    sig_mem_addr0 <= 6'd0-1;
    sig_mem_wen0  <= 1'b0;   
end

//write signature data to hex file
always@(posedge clk) begin
    if(i_sig_mode==1'b0) begin
        if(o_sig_valid) begin
            $fdisplay(fp,"%X",o_sig_data);
            sig_mem_in0   <= o_sig_data;
            sig_mem_addr0 <= sig_mem_addr0 + 1;
            sig_mem_wen0  <= 1'b1;
        end
        else begin
            sig_mem_in0   <= 64'h0;
            sig_mem_addr0 <= sig_mem_addr0;
            sig_mem_wen0  <= 1'b0;   
        end
    end
end

endmodule