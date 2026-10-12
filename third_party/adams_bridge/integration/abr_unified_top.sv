// SPDX-License-Identifier: Apache-2.0
// Local integration wrapper, added 2026-10-12.
// The pinned upstream RTL is unchanged. This wrapper includes all external SRAMs.
// Area scope is the unified ML-KEM-1024 / ML-DSA-87 accelerator, not ML-KEM alone.
module abr_unified_top (
    input  logic        clk,
    input  logic        rst_b,
    input  logic [31:0] haddr_i,
    input  logic [63:0] hwdata_i,
    input  logic        hsel_i,
    input  logic        hwrite_i,
    input  logic        hready_i,
    input  logic [1:0]  htrans_i,
    input  logic [2:0]  hsize_i,
    output logic        hresp_o,
    output logic        hreadyout_o,
    output logic [63:0] hrdata_o,
    input  logic        debugUnlock_or_scan_mode_switch,
    output logic        busy_o,
    output logic        error_intr,
    output logic        notif_intr
);
    abr_mem_if memory_bus();

    abr_top #(
        .AHB_ADDR_WIDTH(32),
        .AHB_DATA_WIDTH(64),
        .CLIENT_DATA_WIDTH(32)
    ) core (
        .clk(clk),
        .rst_b(rst_b),
        .haddr_i(haddr_i),
        .hwdata_i(hwdata_i),
        .hsel_i(hsel_i),
        .hwrite_i(hwrite_i),
        .hready_i(hready_i),
        .htrans_i(htrans_i),
        .hsize_i(hsize_i),
        .hresp_o(hresp_o),
        .hreadyout_o(hreadyout_o),
        .hrdata_o(hrdata_o),
        .abr_memory_export(memory_bus),
        .debugUnlock_or_scan_mode_switch(debugUnlock_or_scan_mode_switch),
        .busy_o(busy_o),
        .error_intr(error_intr),
        .notif_intr(notif_intr)
    );

    abr_mem_top memories (
        .clk_i(clk),
        .abr_memory_export(memory_bus)
    );
endmodule
