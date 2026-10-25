// ML-DSA guarded-baseline/corrected-candidate ASIC startup shell.
// Assert boot_rst for at least one rising clock edge before using this core.
// Deassert boot_rst, wait for boot_ready, then use the original rst/start protocol.
// Ordinary rst never clears boot_ready or storage. Reasserting boot_rst is an
// explicit destructive cold restart. No clock gating or power-up values are used.
module combined_top_asic #(
    parameter BUS_W=4, SAMPLE_W=23, W=64
) (
    input clk, rst, start,
    input [1:0] mode,
    input [2:0] sec_lvl,
    input valid_i,
    output ready_i,
    input [W-1:0] data_i,
    output valid_o,
    input ready_o,
    output [W-1:0] data_o,
    input boot_rst,
    output reg boot_ready
);
    reg [11:0] boot_address;
    wire hold_core = boot_rst | ~boot_ready;
    wire scrub_enable = ~boot_rst & ~boot_ready;
    wire core_ready_i, core_valid_o;
    wire [W-1:0] core_data_o;
    always @(posedge clk) begin
        if (boot_rst) begin
            boot_address <= 0;
            boot_ready <= 0;
        end else if (!boot_ready) begin
            if (boot_address == 12'd4095)
                boot_ready <= 1;
            else
                boot_address <= boot_address + 1'b1;
        end
    end
    assign ready_i = !hold_core && core_ready_i;
    assign valid_o = !hold_core && core_valid_o;
    assign data_o = hold_core ? {W{1'b0}} : core_data_o;
    mldsa_asic_core #(.BUS_W(BUS_W), .SAMPLE_W(SAMPLE_W), .W(W)) CORE (
        .clk(clk), .rst(rst | hold_core), .start(start & ~hold_core),
        .mode(mode), .sec_lvl(sec_lvl), .valid_i(valid_i & ~hold_core),
        .ready_i(core_ready_i), .data_i(data_i), .valid_o(core_valid_o),
        .ready_o(ready_o & ~hold_core), .data_o(core_data_o),
        .asic_boot_reset(hold_core), .asic_scrub_enable(scrub_enable),
        .asic_scrub_address(boot_address)
    );
endmodule
