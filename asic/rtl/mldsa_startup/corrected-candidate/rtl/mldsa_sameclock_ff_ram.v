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


// Explicit same-clock ASIC derivative. No power-up initialization.
// Both reads retain the original one-cycle enabled, read-before-write behavior.
// Simultaneous same-address dual writes are outside the portable contract.
module mldsa_sameclock_ff_ram #(parameter WIDTH=96, LENGTH=1024) (
    input clk, input hold_core, input scrub_enable,
    input [11:0] scrub_address,
    input ena, enb, wea, web,
    input [$clog2(LENGTH)-1:0] addra, addrb,
    input [WIDTH-1:0] dia, dib,
    output reg [WIDTH-1:0] doa, dob
);
    reg [WIDTH-1:0] ram [0:LENGTH-1];
    generate
        if (LENGTH != 1024 && LENGTH != 4096) begin : unsupported_length
            MLDSA_ASIC_RAM_REQUIRES_1024_OR_4096_WORDS invalid_configuration();
        end
    endgenerate
    always @(posedge clk) begin
        if (scrub_enable && scrub_address < LENGTH)
            ram[scrub_address[$clog2(LENGTH)-1:0]] <= {WIDTH{1'b0}};
        else if (!hold_core) begin
            if (ena) begin
                doa <= ram[addra];
                if (wea) ram[addra] <= dia;
            end
            if (enb) begin
                dob <= ram[addrb];
                if (web) ram[addrb] <= dib;
            end
        end
    end
endmodule
