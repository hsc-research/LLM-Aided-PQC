// SPDX-License-Identifier: MIT
// Canonical HintBitUnpack validation, FIPS 204 Algorithm 21.
// Functional hardening variant; area/timing have not been qualified.
module mldsa_hint_guard (
    input wire [2:0] sec_lvl,
    input wire [671:0] hint_bytes,
    output reg invalid
);
    reg [7:0] encoded [0:83];
    integer k, omega, total, i, polynomial, index, first, last;
    always @* begin
        case (sec_lvl)
            2: begin k = 4; omega = 80; end
            3: begin k = 6; omega = 55; end
            5: begin k = 8; omega = 75; end
            default: begin k = 0; omega = 0; end
        endcase
        total = omega + k;
        invalid = (k == 0);
        for (i = 0; i < 84; i = i + 1) begin
            if (i < total)
                encoded[i] = hint_bytes[(total-1-i)*8 +: 8];
            else
                encoded[i] = 0;
        end
        first = 0;
        last = 0;
        for (polynomial = 0; polynomial < 8; polynomial = polynomial + 1) begin
            if (polynomial < k) begin
                last = encoded[omega+polynomial];
                // Cumulative counts may be equal (empty polynomials), but
                // cannot decrease or exceed the available index bytes.
                if (last < first || last > omega)
                    invalid = 1;
                for (index = 1; index < 80; index = index + 1) begin
                    if (index > first && index < last && index < omega) begin
                        if (encoded[index-1] >= encoded[index])
                            invalid = 1;
                    end
                end
                first = last;
            end
        end
        // Unused index bytes must all be zero for a unique encoding.
        for (index = 0; index < 80; index = index + 1) begin
            if (index >= first && index < omega && encoded[index] != 0)
                invalid = 1;
        end
    end
endmodule
