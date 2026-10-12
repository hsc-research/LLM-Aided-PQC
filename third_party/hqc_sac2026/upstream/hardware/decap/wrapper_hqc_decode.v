module hqc_decod_wrapper #(
    parameter PARAM_SECURITY = 128,
    parameter MULTIPLICITY   = (PARAM_SECURITY == 128)? 3 : 5,
    parameter IN_AW          = (PARAM_SECURITY == 128)? 8 :
                               (PARAM_SECURITY == 192)? 9 :
                               (PARAM_SECURITY == 256)? 9 : 8,
    parameter PARAM_K        = (PARAM_SECURITY == 128)? 16:
                               (PARAM_SECURITY == 192)? 24:
                               (PARAM_SECURITY == 256)? 32 : 31,
    parameter WRAPPER_DIN_W  = 128,
    parameter CORE_DIN_W     = 128,
    parameter DOUT_W         = 8*PARAM_K,
    
    // FIX 1: Calculate External Address Width needed
    parameter EXT_AW         = (WRAPPER_DIN_W < CORE_DIN_W) ? 
                               (IN_AW + $clog2(CORE_DIN_W/WRAPPER_DIN_W)) : 
                               IN_AW
)(
    input                        clk_i,
    input                        rst_ni,
    input                        start_i,
    output                       busy_o,
    input  [WRAPPER_DIN_W-1:0]   ram_din_i,
    output                       ram_din_rd_o,
    output [EXT_AW-1:0]          ram_din_addr_o, // FIX 1: Updated Width
    output [DOUT_W-1:0]          dout_o,
    output                       dout_valid_o
);

    // Calculate Ratios
    localparam RATIO = (WRAPPER_DIN_W >= CORE_DIN_W) ?
                       (WRAPPER_DIN_W / CORE_DIN_W) :
                       (CORE_DIN_W / WRAPPER_DIN_W);

    localparam WIDER_INPUT  = (WRAPPER_DIN_W > CORE_DIN_W);
    localparam NARROW_INPUT = (WRAPPER_DIN_W < CORE_DIN_W);
    localparam SAME_WIDTH   = (WRAPPER_DIN_W == CORE_DIN_W);
    
    localparam CNT_W = (RATIO > 1) ? $clog2(RATIO) : 1;

    // Signals connecting to the Core
    wire [CORE_DIN_W-1:0]   core_ram_din;
    wire                    core_ram_din_rd;
    wire [IN_AW-1:0]        core_ram_din_addr;
    wire                    core_start;          
    wire                    core_busy;
    wire                    wrapper_busy;

    // Output assignment
    assign busy_o = core_busy || wrapper_busy;

    generate
        // =================================================================
        // CASE 1: SAME WIDTH
        // =================================================================
        if (SAME_WIDTH) begin : gen_passthrough
            assign core_ram_din      = ram_din_i;
            assign ram_din_rd_o      = core_ram_din_rd;
            // Pad address for correctness
            assign ram_din_addr_o    = {{(EXT_AW-IN_AW){1'b0}}, core_ram_din_addr};
            
            assign core_start        = start_i; 
            assign wrapper_busy      = 0;
        end 

        // =================================================================
        // CASE 2: WIDER INPUT
        // =================================================================
        else if (WIDER_INPUT) begin : gen_wide_input
            wire [CNT_W-1:0] slice_sel;
            assign slice_sel = core_ram_din_addr[CNT_W-1:0];
            assign ram_din_addr_o = core_ram_din_addr >> CNT_W;
            assign core_ram_din = ram_din_i[slice_sel * CORE_DIN_W +: CORE_DIN_W];
            
            // Passthrough read signal (stateless)
            assign ram_din_rd_o = core_ram_din_rd;

            assign core_start   = start_i;
            assign wrapper_busy = 0;
        end 

        // =================================================================
        // CASE 3: NARROW INPUT (The Critical Part)
        // =================================================================
        else if (NARROW_INPUT) begin : gen_narrow_input
            
            reg [CORE_DIN_W-1:0] cache [0:255]; 
            
            reg [IN_AW-1:0]      assembled_addr; // core words (0..255)
            reg [EXT_AW-1:0]     fetch_addr;     // FIX 1: External chunks (0..1023)
            reg [CNT_W-1:0]      chunk_cnt;      
            reg                  prefetching;
            reg                  buffer_full;    // FIX 2: Store-and-Forward flag
            reg                  start_pending;  
            reg                  core_start_reg; 
            reg                  first_fetch_cyc;
            
            // FIX 4: Busy Glitch Prevention (Added core_start_reg)
            assign wrapper_busy = start_pending || prefetching || core_start_reg;
            assign core_start   = core_start_reg;

            always @(posedge clk_i or negedge rst_ni) begin
                if (!rst_ni) begin
                    assembled_addr  <= 0;
                    fetch_addr      <= 0;
                    chunk_cnt       <= 0;
                    prefetching     <= 0;
                    buffer_full     <= 0;
                    start_pending   <= 0;
                    core_start_reg  <= 0;
                    first_fetch_cyc <= 0;
                end else begin
                    // FIX 3: Reset state on new Start (Critical for restarts)
                    if (start_i) begin
                        start_pending   <= 1;
                        buffer_full     <= 0; 
                        assembled_addr  <= 0;
                        prefetching     <= 0;
                        first_fetch_cyc <= 0;
                        chunk_cnt       <= 0;
                    end

                    // Kick off prefetch
                    if (start_pending && !prefetching && !buffer_full && assembled_addr == 0) begin
                        prefetching     <= 1;
                        fetch_addr      <= 0; 
                        chunk_cnt       <= 0;
                        first_fetch_cyc <= 1; 
                    end

                    // Fetch Data State Machine
                    if (prefetching) begin
                        if (first_fetch_cyc) begin
                            first_fetch_cyc <= 0;
                        end else begin
                            cache[assembled_addr][chunk_cnt * WRAPPER_DIN_W +: WRAPPER_DIN_W] <= ram_din_i;

                            if (chunk_cnt == RATIO - 1) begin
                                chunk_cnt <= 0;
                                if (assembled_addr == 255) begin
                                    prefetching <= 0; 
                                    buffer_full <= 1; // Done!
                                end else begin
                                    assembled_addr <= assembled_addr + 1;
                                end
                            end else begin
                                chunk_cnt <= chunk_cnt + 1;
                            end
                            
                            if (!(assembled_addr == 255 && chunk_cnt == RATIO - 1)) begin
                                fetch_addr <= fetch_addr + 1;
                            end
                        end
                    end

                    // FIX 2: Only start when Buffer is FULL
                    if (start_pending && buffer_full) begin
                        core_start_reg <= 1;    
                        start_pending  <= 0;    
                    end else begin
                        core_start_reg <= 0;
                    end
                end
            end

            assign ram_din_rd_o   = prefetching;
            assign ram_din_addr_o = fetch_addr;
            assign core_ram_din   = cache[core_ram_din_addr];

        end
    endgenerate

    hqc_decod_top #(
        .PARAM_SECURITY (PARAM_SECURITY),
        .MULTIPLICITY   (MULTIPLICITY),
        .IN_AW          (IN_AW),
        .PARAM_K        (PARAM_K),
        .DIN_W          (CORE_DIN_W),
        .DOUT_W         (DOUT_W)
    ) hqc_decod_core (
        .clk_i          (clk_i),
        .rst_ni         (rst_ni),
        .start_i        (core_start),
        .busy_o         (core_busy),
        .ram_din_i      (core_ram_din),
        .ram_din_rd_o   (core_ram_din_rd),
        .ram_din_addr_o (core_ram_din_addr),
        .dout_o         (dout_o),
        .dout_valid_o   (dout_valid_o)
    );

endmodule
