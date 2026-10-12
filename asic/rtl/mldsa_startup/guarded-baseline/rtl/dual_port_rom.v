/*
 * From our research paper "High-Performance Hardware Implementation of CRYSTALS-Dilithium"
 * by Luke Beckwith, Duc Tri Nguyen, Kris Gaj
 * at George Mason University, USA
 * https://eprint.iacr.org/2021/1451.pdf
 * =============================================================================
 * Copyright (c) 2021 by Cryptographic Engineering Research Group (CERG)
 * ECE Department, George Mason University
 * Fairfax, VA, U.S.A.
 * Author: Luke Beckwith
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *     http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * =============================================================================
 * @author   Luke Beckwith <lbeckwit@gmu.edu>
 */


// ASIC constant-ROM derivative. Original FPGA source is preserved unchanged.
// The qualified design uses WIDTH=24, LENGTH=256, INIT_FILE="zetas.txt".
// No power-up register initialization or runtime file access is required.
// This component is separately tested; full-core target requalification is pending.
// zetas.txt SHA256: 07d0eabbd7a102982b11d39b748758d34baf309aa71cf3d1bac518b9dded0241
`timescale 1ns / 1ps
module dual_port_rom #(parameter WIDTH=96, LENGTH=1024, INIT_FILE="")
    (input clk, en,
     input [$clog2(LENGTH)-1:0] addra, addrb,
     output reg [WIDTH-1:0] doa, dob);
    generate
        if (WIDTH == 24 && LENGTH == 256 && INIT_FILE == "zetas.txt") begin: zetas
            function [23:0] lookup;
                input [7:0] address;
                begin
                    case (address)
                        8'd0: lookup = 24'h000000;
                        8'd1: lookup = 24'h495E02;
                        8'd2: lookup = 24'h397567;
                        8'd3: lookup = 24'h396569;
                        8'd4: lookup = 24'h4F062B;
                        8'd5: lookup = 24'h53DF73;
                        8'd6: lookup = 24'h4FE033;
                        8'd7: lookup = 24'h4F066B;
                        8'd8: lookup = 24'h76B1AE;
                        8'd9: lookup = 24'h360DD5;
                        8'd10: lookup = 24'h28EDB0;
                        8'd11: lookup = 24'h207FE4;
                        8'd12: lookup = 24'h397283;
                        8'd13: lookup = 24'h70894A;
                        8'd14: lookup = 24'h088192;
                        8'd15: lookup = 24'h6D3DC8;
                        8'd16: lookup = 24'h4C7294;
                        8'd17: lookup = 24'h41E0B4;
                        8'd18: lookup = 24'h28A3D2;
                        8'd19: lookup = 24'h66528A;
                        8'd20: lookup = 24'h4A18A7;
                        8'd21: lookup = 24'h794034;
                        8'd22: lookup = 24'h0A52EE;
                        8'd23: lookup = 24'h6B7D81;
                        8'd24: lookup = 24'h4E9F1D;
                        8'd25: lookup = 24'h1A2877;
                        8'd26: lookup = 24'h2571DF;
                        8'd27: lookup = 24'h1649EE;
                        8'd28: lookup = 24'h7611BD;
                        8'd29: lookup = 24'h492BB7;
                        8'd30: lookup = 24'h2AF697;
                        8'd31: lookup = 24'h22D8D5;
                        8'd32: lookup = 24'h36F72A;
                        8'd33: lookup = 24'h30911E;
                        8'd34: lookup = 24'h29D13F;
                        8'd35: lookup = 24'h492673;
                        8'd36: lookup = 24'h50685F;
                        8'd37: lookup = 24'h2010A2;
                        8'd38: lookup = 24'h3887F7;
                        8'd39: lookup = 24'h11B2C3;
                        8'd40: lookup = 24'h0603A4;
                        8'd41: lookup = 24'h0E2BED;
                        8'd42: lookup = 24'h10B72C;
                        8'd43: lookup = 24'h4A5F35;
                        8'd44: lookup = 24'h1F9D15;
                        8'd45: lookup = 24'h428CD4;
                        8'd46: lookup = 24'h3177F4;
                        8'd47: lookup = 24'h20E612;
                        8'd48: lookup = 24'h341C1D;
                        8'd49: lookup = 24'h1AD873;
                        8'd50: lookup = 24'h736681;
                        8'd51: lookup = 24'h49553F;
                        8'd52: lookup = 24'h3952F6;
                        8'd53: lookup = 24'h62564A;
                        8'd54: lookup = 24'h65AD05;
                        8'd55: lookup = 24'h439A1C;
                        8'd56: lookup = 24'h53AA5F;
                        8'd57: lookup = 24'h30B622;
                        8'd58: lookup = 24'h087F38;
                        8'd59: lookup = 24'h3B0E6D;
                        8'd60: lookup = 24'h2C83DA;
                        8'd61: lookup = 24'h1C496E;
                        8'd62: lookup = 24'h330E2B;
                        8'd63: lookup = 24'h1C5B70;
                        8'd64: lookup = 24'h2EE3F1;
                        8'd65: lookup = 24'h137EB9;
                        8'd66: lookup = 24'h57A930;
                        8'd67: lookup = 24'h3AC6EF;
                        8'd68: lookup = 24'h3FD54C;
                        8'd69: lookup = 24'h4EB2EA;
                        8'd70: lookup = 24'h503EE1;
                        8'd71: lookup = 24'h7BB175;
                        8'd72: lookup = 24'h2648B4;
                        8'd73: lookup = 24'h1EF256;
                        8'd74: lookup = 24'h1D90A2;
                        8'd75: lookup = 24'h45A6D4;
                        8'd76: lookup = 24'h2AE59B;
                        8'd77: lookup = 24'h52589C;
                        8'd78: lookup = 24'h6EF1F5;
                        8'd79: lookup = 24'h3F7288;
                        8'd80: lookup = 24'h175102;
                        8'd81: lookup = 24'h075D59;
                        8'd82: lookup = 24'h1187BA;
                        8'd83: lookup = 24'h52ACA9;
                        8'd84: lookup = 24'h773E9E;
                        8'd85: lookup = 24'h0296D8;
                        8'd86: lookup = 24'h2592EC;
                        8'd87: lookup = 24'h4CFF12;
                        8'd88: lookup = 24'h404CE8;
                        8'd89: lookup = 24'h4AA582;
                        8'd90: lookup = 24'h1E54E6;
                        8'd91: lookup = 24'h4F16C1;
                        8'd92: lookup = 24'h1A7E79;
                        8'd93: lookup = 24'h03978F;
                        8'd94: lookup = 24'h4E4817;
                        8'd95: lookup = 24'h31B859;
                        8'd96: lookup = 24'h5884CC;
                        8'd97: lookup = 24'h1B4827;
                        8'd98: lookup = 24'h5B63D0;
                        8'd99: lookup = 24'h5D787A;
                        8'd100: lookup = 24'h35225E;
                        8'd101: lookup = 24'h400C7E;
                        8'd102: lookup = 24'h6C09D1;
                        8'd103: lookup = 24'h5BD532;
                        8'd104: lookup = 24'h6BC4D3;
                        8'd105: lookup = 24'h258ECB;
                        8'd106: lookup = 24'h2E534C;
                        8'd107: lookup = 24'h097A6C;
                        8'd108: lookup = 24'h3B8820;
                        8'd109: lookup = 24'h6D285C;
                        8'd110: lookup = 24'h2CA4F8;
                        8'd111: lookup = 24'h337CAA;
                        8'd112: lookup = 24'h14B2A0;
                        8'd113: lookup = 24'h558536;
                        8'd114: lookup = 24'h28F186;
                        8'd115: lookup = 24'h55795D;
                        8'd116: lookup = 24'h4AF670;
                        8'd117: lookup = 24'h234A86;
                        8'd118: lookup = 24'h75E826;
                        8'd119: lookup = 24'h78DE66;
                        8'd120: lookup = 24'h05528C;
                        8'd121: lookup = 24'h7ADF59;
                        8'd122: lookup = 24'h0F6E17;
                        8'd123: lookup = 24'h5BF3DA;
                        8'd124: lookup = 24'h459B7E;
                        8'd125: lookup = 24'h628B34;
                        8'd126: lookup = 24'h5DBECB;
                        8'd127: lookup = 24'h1A9E7B;
                        8'd128: lookup = 24'h0006D9;
                        8'd129: lookup = 24'h6257C5;
                        8'd130: lookup = 24'h574B3C;
                        8'd131: lookup = 24'h69A8EF;
                        8'd132: lookup = 24'h289838;
                        8'd133: lookup = 24'h64B5FE;
                        8'd134: lookup = 24'h7EF8F5;
                        8'd135: lookup = 24'h2A4E78;
                        8'd136: lookup = 24'h120A23;
                        8'd137: lookup = 24'h0154A8;
                        8'd138: lookup = 24'h09B7FF;
                        8'd139: lookup = 24'h435E87;
                        8'd140: lookup = 24'h437FF8;
                        8'd141: lookup = 24'h5CD5B4;
                        8'd142: lookup = 24'h4DC04E;
                        8'd143: lookup = 24'h4728AF;
                        8'd144: lookup = 24'h7F735D;
                        8'd145: lookup = 24'h0C8D0D;
                        8'd146: lookup = 24'h0F66D5;
                        8'd147: lookup = 24'h5A6D80;
                        8'd148: lookup = 24'h61AB98;
                        8'd149: lookup = 24'h185D96;
                        8'd150: lookup = 24'h437F31;
                        8'd151: lookup = 24'h468298;
                        8'd152: lookup = 24'h662960;
                        8'd153: lookup = 24'h4BD579;
                        8'd154: lookup = 24'h28DE06;
                        8'd155: lookup = 24'h465D8D;
                        8'd156: lookup = 24'h49B0E3;
                        8'd157: lookup = 24'h09B434;
                        8'd158: lookup = 24'h7C0DB3;
                        8'd159: lookup = 24'h5A68B0;
                        8'd160: lookup = 24'h409BA9;
                        8'd161: lookup = 24'h64D3D5;
                        8'd162: lookup = 24'h21762A;
                        8'd163: lookup = 24'h658591;
                        8'd164: lookup = 24'h246E39;
                        8'd165: lookup = 24'h48C39B;
                        8'd166: lookup = 24'h7BC759;
                        8'd167: lookup = 24'h4F5859;
                        8'd168: lookup = 24'h392DB2;
                        8'd169: lookup = 24'h230923;
                        8'd170: lookup = 24'h12EB67;
                        8'd171: lookup = 24'h454DF2;
                        8'd172: lookup = 24'h30C31C;
                        8'd173: lookup = 24'h285424;
                        8'd174: lookup = 24'h13232E;
                        8'd175: lookup = 24'h7FAF80;
                        8'd176: lookup = 24'h2DBFCB;
                        8'd177: lookup = 24'h022A0B;
                        8'd178: lookup = 24'h7E832C;
                        8'd179: lookup = 24'h26587A;
                        8'd180: lookup = 24'h6B3375;
                        8'd181: lookup = 24'h095B76;
                        8'd182: lookup = 24'h6BE1CC;
                        8'd183: lookup = 24'h5E061E;
                        8'd184: lookup = 24'h78E00D;
                        8'd185: lookup = 24'h628C37;
                        8'd186: lookup = 24'h3DA604;
                        8'd187: lookup = 24'h4AE53C;
                        8'd188: lookup = 24'h1F1D68;
                        8'd189: lookup = 24'h6330BB;
                        8'd190: lookup = 24'h7361B8;
                        8'd191: lookup = 24'h5EA06C;
                        8'd192: lookup = 24'h671AC7;
                        8'd193: lookup = 24'h201FC6;
                        8'd194: lookup = 24'h5BA4FF;
                        8'd195: lookup = 24'h60D772;
                        8'd196: lookup = 24'h08F201;
                        8'd197: lookup = 24'h6DE024;
                        8'd198: lookup = 24'h080E6D;
                        8'd199: lookup = 24'h56038E;
                        8'd200: lookup = 24'h695688;
                        8'd201: lookup = 24'h1E6D3E;
                        8'd202: lookup = 24'h2603BD;
                        8'd203: lookup = 24'h6A9DFA;
                        8'd204: lookup = 24'h07C017;
                        8'd205: lookup = 24'h6DBFD4;
                        8'd206: lookup = 24'h74D0BD;
                        8'd207: lookup = 24'h63E1E3;
                        8'd208: lookup = 24'h519573;
                        8'd209: lookup = 24'h7AB60D;
                        8'd210: lookup = 24'h2867BA;
                        8'd211: lookup = 24'h2DECD4;
                        8'd212: lookup = 24'h58018C;
                        8'd213: lookup = 24'h3F4CF5;
                        8'd214: lookup = 24'h0B7009;
                        8'd215: lookup = 24'h427E23;
                        8'd216: lookup = 24'h3CBD37;
                        8'd217: lookup = 24'h273333;
                        8'd218: lookup = 24'h673957;
                        8'd219: lookup = 24'h1A4B5D;
                        8'd220: lookup = 24'h196926;
                        8'd221: lookup = 24'h1EF206;
                        8'd222: lookup = 24'h11C14E;
                        8'd223: lookup = 24'h4C76C8;
                        8'd224: lookup = 24'h3CF42F;
                        8'd225: lookup = 24'h7FB19A;
                        8'd226: lookup = 24'h6AF66C;
                        8'd227: lookup = 24'h2E1669;
                        8'd228: lookup = 24'h3352D6;
                        8'd229: lookup = 24'h034760;
                        8'd230: lookup = 24'h085260;
                        8'd231: lookup = 24'h741E78;
                        8'd232: lookup = 24'h2F6316;
                        8'd233: lookup = 24'h6F0A11;
                        8'd234: lookup = 24'h07C0F1;
                        8'd235: lookup = 24'h776D0B;
                        8'd236: lookup = 24'h0D1FF0;
                        8'd237: lookup = 24'h345824;
                        8'd238: lookup = 24'h0223D4;
                        8'd239: lookup = 24'h68C559;
                        8'd240: lookup = 24'h5E8885;
                        8'd241: lookup = 24'h2FAA32;
                        8'd242: lookup = 24'h23FC65;
                        8'd243: lookup = 24'h5E6942;
                        8'd244: lookup = 24'h51E0ED;
                        8'd245: lookup = 24'h65ADB3;
                        8'd246: lookup = 24'h2CA5E6;
                        8'd247: lookup = 24'h79E1FE;
                        8'd248: lookup = 24'h7B4064;
                        8'd249: lookup = 24'h35E1DD;
                        8'd250: lookup = 24'h433AAC;
                        8'd251: lookup = 24'h464ADE;
                        8'd252: lookup = 24'h1CFE14;
                        8'd253: lookup = 24'h73F1CE;
                        8'd254: lookup = 24'h10170E;
                        8'd255: lookup = 24'h74B6D7;
                        default: lookup = 24'hxxxxxx;
                    endcase
                end
            endfunction
            always @(posedge clk) begin
                if (en) begin
                    doa <= lookup(addra);
                    dob <= lookup(addrb);
                end
            end
        end else if (INIT_FILE == "") begin: all_zero
            // Match the original empty-file ROM, including out-of-range reads.
            always @(posedge clk) begin
                if (en) begin
                    doa <= (addra < LENGTH) ? {WIDTH{1'b0}} : {WIDTH{1'bx}};
                    dob <= (addrb < LENGTH) ? {WIDTH{1'b0}} : {WIDTH{1'bx}};
                end
            end
        end else begin: unsupported
            // Fail elaboration instead of silently using the wrong constants.
            PQC_ASIC_ROM_REQUIRES_24X256_ZETAS_OR_EMPTY_FILE reject_configuration();
        end
    endgenerate
endmodule
