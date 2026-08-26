//======================================================================
//
// sha512_h_constants.v
// ---------------------
// The H initial constants for the different modes in SHA-512.
//
//
// Author: Joachim Strombergson
// Copyright (c) 2014 Secworks Sweden AB
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or
// without modification, are permitted provided that the following
// conditions are met:
//
// 1. Redistributions of source code must retain the above copyright
//    notice, this list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright
//    notice, this list of conditions and the following disclaimer in
//    the documentation and/or other materials provided with the
//    distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
// FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
// COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
// INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
// BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
// CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
// STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
// ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//======================================================================

`default_nettype none

module sha512_h_constants(
                          //input wire  [1 : 0]  mode,
                          input wire mode,

                          input wire [63 : 0] H0_keep,
                          input wire [63 : 0] H1_keep,
                          input wire [63 : 0] H2_keep,
                          input wire [63 : 0] H3_keep,
                          input wire [63 : 0] H4_keep,
                          input wire [63 : 0] H5_keep,
                          input wire [63 : 0] H6_keep,
                          input wire [63 : 0] H7_keep,

                          output wire [63 : 0] H0,
                          output wire [63 : 0] H1,
                          output wire [63 : 0] H2,
                          output wire [63 : 0] H3,
                          output wire [63 : 0] H4,
                          output wire [63 : 0] H5,
                          output wire [63 : 0] H6,
                          output wire [63 : 0] H7
                         );

  //----------------------------------------------------------------
  // Wires.
  //----------------------------------------------------------------
  reg [63 : 0] tmp_H0;
  reg [63 : 0] tmp_H1;
  reg [63 : 0] tmp_H2;
  reg [63 : 0] tmp_H3;
  reg [63 : 0] tmp_H4;
  reg [63 : 0] tmp_H5;
  reg [63 : 0] tmp_H6;
  reg [63 : 0] tmp_H7;


  //----------------------------------------------------------------
  // Concurrent connectivity for ports etc.
  //----------------------------------------------------------------
  assign H0 = tmp_H0;
  assign H1 = tmp_H1;
  assign H2 = tmp_H2;
  assign H3 = tmp_H3;
  assign H4 = tmp_H4;
  assign H5 = tmp_H5;
  assign H6 = tmp_H6;
  assign H7 = tmp_H7;


  //----------------------------------------------------------------
  // mode_mux
  //
  // Based on the given mode, the correct H constants are selected.
  //----------------------------------------------------------------
  always @*
    begin : mode_mux
      case(mode)
        0:
          begin
            // SHA-512
            tmp_H0 = H0_keep;
            tmp_H1 = H1_keep;
            tmp_H2 = H2_keep;
            tmp_H3 = H3_keep;
            tmp_H4 = H4_keep;
            tmp_H5 = H5_keep;
            tmp_H6 = H6_keep;
            tmp_H7 = H7_keep;
          end      
          
        1:
          begin
            // SHA-512
            tmp_H0 = 64'h6a09e667f3bcc908;
            tmp_H1 = 64'hbb67ae8584caa73b;
            tmp_H2 = 64'h3c6ef372fe94f82b;
            tmp_H3 = 64'ha54ff53a5f1d36f1;
            tmp_H4 = 64'h510e527fade682d1;
            tmp_H5 = 64'h9b05688c2b3e6c1f;
            tmp_H6 = 64'h1f83d9abfb41bd6b;
            tmp_H7 = 64'h5be0cd19137e2179;
          end      
      endcase // case (addr)
    end // block: mode_mux
endmodule // sha512_h_constants

//======================================================================
// sha512_h_constants.v
//======================================================================
