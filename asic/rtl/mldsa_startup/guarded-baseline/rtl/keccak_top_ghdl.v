module countern_Bcountern_11_1_1
  (input  clk,
   input  rst,
   input  load,
   input  en,
   input  [10:0] \input ,
   output [10:0] \output );
  wire [10:0] temp;
  wire [10:0] value;
  wire [10:0] init_value;
  wire [10:0] n2861;
  wire [10:0] n2862;
  wire [10:0] n2863;
  wire [10:0] n2864;
  reg [10:0] n2867;
  assign \output  = temp; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:34:11 */
  assign temp = n2867; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:35:11 */
  assign value = 11'b00000000001; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:36:11 */
  assign init_value = \input ; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:64:46 */
  assign n2861 = temp + value;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:63:25 */
  assign n2862 = en ? n2861 : temp;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:61:25 */
  assign n2863 = load ? \input  : n2862;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:59:25 */
  assign n2864 = rst ? init_value : n2863;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:58:17 */
  always @(posedge clk)
    n2867 <= n2864;
endmodule

module sr_reg_Bstruct_9842926af7ca0a8cca12604f945414f07b01e13d
  (input  rst,
   input  clk,
   input  set,
   input  clr,
   output \output );
  wire output_s;
  wire n2849;
  wire n2850;
  wire n2851;
  wire n2853;
  reg n2856;
  assign \output  = output_s; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:24:16 */
  assign output_s = n2856; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:32:54 */
  assign n2849 = ~clr;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:32:63 */
  assign n2850 = n2849 & output_s;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:32:49 */
  assign n2851 = set | n2850;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:29:25 */
  assign n2853 = rst ? 1'b1 : n2851;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:28:17 */
  always @(posedge clk)
    n2856 <= n2853;
endmodule

module piso_Bbehavioral_1344_64
  (input  clk,
   input  en,
   input  sel,
   input  [1343:0] \input ,
   output [63:0] \output );
  wire [1343:0] \reg ;
  wire [1343:0] mux;
  wire [63:0] n2551;
  wire [63:0] n2552;
  wire [63:0] n2553;
  wire [63:0] n2554;
  wire [63:0] n2555;
  wire [63:0] n2556;
  wire [63:0] n2557;
  wire [63:0] n2558;
  wire [63:0] n2559;
  wire [63:0] n2560;
  wire [63:0] n2561;
  wire [63:0] n2562;
  wire [63:0] n2563;
  wire [63:0] n2564;
  wire [63:0] n2565;
  wire [63:0] n2566;
  wire [63:0] n2567;
  wire [63:0] n2568;
  wire [63:0] n2569;
  wire [63:0] n2570;
  wire [63:0] n2571;
  wire [63:0] n2572;
  wire [63:0] n2573;
  wire [63:0] n2574;
  wire [63:0] n2575;
  wire [63:0] n2576;
  wire [63:0] n2577;
  wire [63:0] n2578;
  wire [63:0] n2579;
  wire [63:0] n2580;
  wire [63:0] n2581;
  wire [63:0] n2582;
  wire [63:0] n2583;
  wire [63:0] n2584;
  wire [63:0] n2585;
  wire [63:0] n2586;
  wire [63:0] n2587;
  wire [63:0] n2588;
  wire [63:0] n2589;
  wire [63:0] n2590;
  wire [63:0] n2591;
  wire [63:0] n2592;
  wire [63:0] n2593;
  wire [63:0] n2594;
  wire [63:0] n2595;
  wire [63:0] n2596;
  wire [63:0] n2597;
  wire [63:0] n2598;
  wire [63:0] n2599;
  wire [63:0] n2600;
  wire [63:0] n2601;
  wire [63:0] n2602;
  wire [63:0] n2603;
  wire [63:0] n2604;
  wire [63:0] n2605;
  wire [63:0] n2606;
  wire [63:0] n2607;
  wire [63:0] n2608;
  wire [63:0] n2609;
  wire [63:0] n2610;
  wire [63:0] n2611;
  wire [63:0] n2614;
  wire [63:0] n2622;
  wire [63:0] n2630;
  wire [63:0] n2638;
  wire [63:0] n2646;
  wire [63:0] n2654;
  wire [63:0] n2662;
  wire [63:0] n2670;
  wire [63:0] n2678;
  wire [63:0] n2686;
  wire [63:0] n2694;
  wire [63:0] n2702;
  wire [63:0] n2710;
  wire [63:0] n2718;
  wire [63:0] n2726;
  wire [63:0] n2734;
  wire [63:0] n2742;
  wire [63:0] n2750;
  wire [63:0] n2758;
  wire [63:0] n2766;
  wire [63:0] n2774;
  wire [63:0] n2780;
  wire [1343:0] n2781;
  wire [1343:0] n2782;
  wire [63:0] n2783;
  wire [63:0] n2784;
  reg [63:0] n2785;
  wire [63:0] n2786;
  wire [63:0] n2787;
  reg [63:0] n2788;
  wire [63:0] n2789;
  wire [63:0] n2790;
  reg [63:0] n2791;
  wire [63:0] n2792;
  wire [63:0] n2793;
  reg [63:0] n2794;
  wire [63:0] n2795;
  wire [63:0] n2796;
  reg [63:0] n2797;
  wire [63:0] n2798;
  wire [63:0] n2799;
  reg [63:0] n2800;
  wire [63:0] n2801;
  wire [63:0] n2802;
  reg [63:0] n2803;
  wire [63:0] n2804;
  wire [63:0] n2805;
  reg [63:0] n2806;
  wire [63:0] n2807;
  wire [63:0] n2808;
  reg [63:0] n2809;
  wire [63:0] n2810;
  wire [63:0] n2811;
  reg [63:0] n2812;
  wire [63:0] n2813;
  wire [63:0] n2814;
  reg [63:0] n2815;
  wire [63:0] n2816;
  wire [63:0] n2817;
  reg [63:0] n2818;
  wire [63:0] n2819;
  wire [63:0] n2820;
  reg [63:0] n2821;
  wire [63:0] n2822;
  wire [63:0] n2823;
  reg [63:0] n2824;
  wire [63:0] n2825;
  wire [63:0] n2826;
  reg [63:0] n2827;
  wire [63:0] n2828;
  wire [63:0] n2829;
  reg [63:0] n2830;
  wire [63:0] n2831;
  wire [63:0] n2832;
  reg [63:0] n2833;
  wire [63:0] n2834;
  wire [63:0] n2835;
  reg [63:0] n2836;
  wire [63:0] n2837;
  wire [63:0] n2838;
  reg [63:0] n2839;
  wire [63:0] n2840;
  wire [63:0] n2841;
  reg [63:0] n2842;
  wire [63:0] n2843;
  wire [63:0] n2844;
  reg [63:0] n2845;
  assign \output  = n2780; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:31:16 */
  assign \reg  = n2781; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:31:21 */
  assign mux = n2782; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:34:34 */
  assign n2551 = \input [63:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2552 = \input [1343:1280]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2553 = sel ? n2552 : n2554;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2554 = \reg [1279:1216]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2555 = \input [1279:1216]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2556 = sel ? n2555 : n2557;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2557 = \reg [1215:1152]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2558 = \input [1215:1152]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2559 = sel ? n2558 : n2560;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2560 = \reg [1151:1088]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2561 = \input [1151:1088]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2562 = sel ? n2561 : n2563;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2563 = \reg [1087:1024]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2564 = \input [1087:1024]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2565 = sel ? n2564 : n2566;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2566 = \reg [1023:960]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2567 = \input [1023:960]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2568 = sel ? n2567 : n2569;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2569 = \reg [959:896]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2570 = \input [959:896]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2571 = sel ? n2570 : n2572;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2572 = \reg [895:832]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2573 = \input [895:832]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2574 = sel ? n2573 : n2575;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2575 = \reg [831:768]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2576 = \input [831:768]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2577 = sel ? n2576 : n2578;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2578 = \reg [767:704]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2579 = \input [767:704]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2580 = sel ? n2579 : n2581;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2581 = \reg [703:640]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2582 = \input [703:640]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2583 = sel ? n2582 : n2584;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2584 = \reg [639:576]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2585 = \input [639:576]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2586 = sel ? n2585 : n2587;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2587 = \reg [575:512]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2588 = \input [575:512]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2589 = sel ? n2588 : n2590;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2590 = \reg [511:448]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2591 = \input [511:448]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2592 = sel ? n2591 : n2593;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2593 = \reg [447:384]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2594 = \input [447:384]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2595 = sel ? n2594 : n2596;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2596 = \reg [383:320]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2597 = \input [383:320]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2598 = sel ? n2597 : n2599;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2599 = \reg [319:256]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2600 = \input [319:256]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2601 = sel ? n2600 : n2602;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2602 = \reg [255:192]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2603 = \input [255:192]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2604 = sel ? n2603 : n2605;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2605 = \reg [191:128]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2606 = \input [191:128]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2607 = sel ? n2606 : n2608;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2608 = \reg [127:64]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:32 */
  assign n2609 = \input [127:64]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:57 */
  assign n2610 = sel ? n2609 : n2611;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:36:80 */
  assign n2611 = \reg [63:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2614 = mux[1343:1280]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2622 = mux[1279:1216]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2630 = mux[1215:1152]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2638 = mux[1151:1088]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2646 = mux[1087:1024]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2654 = mux[1023:960]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2662 = mux[959:896]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2670 = mux[895:832]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2678 = mux[831:768]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2686 = mux[767:704]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2694 = mux[703:640]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2702 = mux[639:576]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2710 = mux[575:512]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2718 = mux[511:448]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2726 = mux[447:384]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2734 = mux[383:320]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2742 = mux[319:256]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2750 = mux[255:192]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2758 = mux[191:128]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2766 = mux[127:64]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:44:54 */
  assign n2774 = mux[63:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:50:22 */
  assign n2780 = \reg [1343:1280]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:31:16 */
  assign n2781 = {n2785, n2788, n2791, n2794, n2797, n2800, n2803, n2806, n2809, n2812, n2815, n2818, n2821, n2824, n2827, n2830, n2833, n2836, n2839, n2842, n2845};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:31:21 */
  assign n2782 = {n2553, n2556, n2559, n2562, n2565, n2568, n2571, n2574, n2577, n2580, n2583, n2586, n2589, n2592, n2595, n2598, n2601, n2604, n2607, n2610, n2551};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2783 = \reg [1343:1280]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2784 = en ? n2614 : n2783;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2785 <= n2784;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2786 = \reg [1279:1216]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2787 = en ? n2622 : n2786;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2788 <= n2787;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2789 = \reg [1215:1152]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2790 = en ? n2630 : n2789;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2791 <= n2790;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2792 = \reg [1151:1088]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2793 = en ? n2638 : n2792;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2794 <= n2793;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2795 = \reg [1087:1024]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2796 = en ? n2646 : n2795;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2797 <= n2796;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2798 = \reg [1023:960]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2799 = en ? n2654 : n2798;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2800 <= n2799;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2801 = \reg [959:896]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2802 = en ? n2662 : n2801;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2803 <= n2802;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2804 = \reg [895:832]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2805 = en ? n2670 : n2804;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2806 <= n2805;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2807 = \reg [831:768]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2808 = en ? n2678 : n2807;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2809 <= n2808;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2810 = \reg [767:704]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2811 = en ? n2686 : n2810;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2812 <= n2811;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2813 = \reg [703:640]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2814 = en ? n2694 : n2813;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2815 <= n2814;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2816 = \reg [639:576]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2817 = en ? n2702 : n2816;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2818 <= n2817;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2819 = \reg [575:512]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2820 = en ? n2710 : n2819;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2821 <= n2820;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2822 = \reg [511:448]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2823 = en ? n2718 : n2822;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2824 <= n2823;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2825 = \reg [447:384]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2826 = en ? n2726 : n2825;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2827 <= n2826;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2828 = \reg [383:320]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2829 = en ? n2734 : n2828;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2830 <= n2829;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2831 = \reg [319:256]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2832 = en ? n2742 : n2831;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2833 <= n2832;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2834 = \reg [255:192]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2835 = en ? n2750 : n2834;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2836 <= n2835;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2837 = \reg [191:128]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2838 = en ? n2758 : n2837;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2839 <= n2838;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2840 = \reg [127:64]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2841 = en ? n2766 : n2840;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2842 <= n2841;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2843 = \reg [63:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  assign n2844 = en ? n2774 : n2843;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/piso.vhd:42:25 */
  always @(posedge clk)
    n2845 <= n2844;
endmodule

module countern_Bcountern_5_1_1
  (input  clk,
   input  rst,
   input  load,
   input  en,
   input  [4:0] \input ,
   output [4:0] \output );
  wire [4:0] temp;
  wire [4:0] value;
  wire [4:0] init_value;
  wire [4:0] n2543;
  wire [4:0] n2544;
  wire [4:0] n2545;
  wire [4:0] n2546;
  reg [4:0] n2549;
  assign \output  = temp; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:34:11 */
  assign temp = n2549; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:35:11 */
  assign value = 5'b00001; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:36:11 */
  assign init_value = \input ; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:64:46 */
  assign n2543 = temp + value;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:63:25 */
  assign n2544 = en ? n2543 : temp;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:61:25 */
  assign n2545 = load ? \input  : n2544;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:59:25 */
  assign n2546 = rst ? init_value : n2545;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/countern.vhd:58:17 */
  always @(posedge clk)
    n2549 <= n2546;
endmodule

module keccak_round_Bmrogawski_round
  (input  [1599:0] rin,
   input  [63:0] rc,
   output [1599:0] rout);
  wire [63:0] aba;
  wire [63:0] abe;
  wire [63:0] abi;
  wire [63:0] abo;
  wire [63:0] abu;
  wire [63:0] aga;
  wire [63:0] age;
  wire [63:0] agi;
  wire [63:0] ago;
  wire [63:0] agu;
  wire [63:0] aka;
  wire [63:0] ake;
  wire [63:0] aki;
  wire [63:0] ako;
  wire [63:0] aku;
  wire [63:0] ama;
  wire [63:0] ame;
  wire [63:0] ami;
  wire [63:0] amo;
  wire [63:0] amu;
  wire [63:0] asa;
  wire [63:0] ase;
  wire [63:0] asi;
  wire [63:0] aso;
  wire [63:0] asu;
  wire [63:0] aba_wire;
  wire [63:0] abe_wire;
  wire [63:0] abi_wire;
  wire [63:0] abo_wire;
  wire [63:0] abu_wire;
  wire [63:0] aga_wire;
  wire [63:0] age_wire;
  wire [63:0] agi_wire;
  wire [63:0] ago_wire;
  wire [63:0] agu_wire;
  wire [63:0] aka_wire;
  wire [63:0] ake_wire;
  wire [63:0] aki_wire;
  wire [63:0] ako_wire;
  wire [63:0] aku_wire;
  wire [63:0] ama_wire;
  wire [63:0] ame_wire;
  wire [63:0] ami_wire;
  wire [63:0] amo_wire;
  wire [63:0] amu_wire;
  wire [63:0] asa_wire;
  wire [63:0] ase_wire;
  wire [63:0] asi_wire;
  wire [63:0] aso_wire;
  wire [63:0] asu_wire;
  wire [63:0] bba;
  wire [63:0] bbe;
  wire [63:0] bbi;
  wire [63:0] bbo;
  wire [63:0] bbu;
  wire [63:0] bga;
  wire [63:0] bge;
  wire [63:0] bgi;
  wire [63:0] bgo;
  wire [63:0] bgu;
  wire [63:0] bka;
  wire [63:0] bke;
  wire [63:0] bki;
  wire [63:0] bko;
  wire [63:0] bku;
  wire [63:0] bma;
  wire [63:0] bme;
  wire [63:0] bmi;
  wire [63:0] bmo;
  wire [63:0] bmu;
  wire [63:0] bsa;
  wire [63:0] bse;
  wire [63:0] bsi;
  wire [63:0] bso;
  wire [63:0] bsu;
  wire [63:0] ca;
  wire [63:0] ce;
  wire [63:0] ci;
  wire [63:0] co;
  wire [63:0] cu;
  wire [63:0] da;
  wire [63:0] de;
  wire [63:0] di;
  wire [63:0] \do ;
  wire [63:0] du;
  wire [63:0] eba;
  wire [63:0] ebe;
  wire [63:0] ebi;
  wire [63:0] ebo;
  wire [63:0] ebu;
  wire [63:0] eba_wire;
  wire [63:0] ega;
  wire [63:0] ege;
  wire [63:0] egi;
  wire [63:0] ego;
  wire [63:0] egu;
  wire [63:0] eka;
  wire [63:0] eke;
  wire [63:0] eki;
  wire [63:0] eko;
  wire [63:0] eku;
  wire [63:0] ema;
  wire [63:0] eme;
  wire [63:0] emi;
  wire [63:0] emo;
  wire [63:0] emu;
  wire [63:0] esa;
  wire [63:0] ese;
  wire [63:0] esi;
  wire [63:0] eso;
  wire [63:0] esu;
  wire [63:0] n2155;
  wire [63:0] n2156;
  wire [63:0] n2157;
  wire [63:0] n2158;
  wire [63:0] n2159;
  wire [63:0] n2160;
  wire [63:0] n2161;
  wire [63:0] n2162;
  wire [63:0] n2163;
  wire [63:0] n2164;
  wire [63:0] n2165;
  wire [63:0] n2166;
  wire [63:0] n2167;
  wire [63:0] n2168;
  wire [63:0] n2169;
  wire [63:0] n2170;
  wire [63:0] n2171;
  wire [63:0] n2172;
  wire [63:0] n2173;
  wire [63:0] n2174;
  wire [63:0] n2175;
  wire [63:0] n2176;
  wire [63:0] n2177;
  wire [63:0] n2178;
  wire [63:0] n2179;
  wire [63:0] n2180;
  wire [63:0] n2181;
  wire [63:0] n2182;
  wire [63:0] n2183;
  wire [63:0] n2184;
  wire [63:0] n2185;
  wire [63:0] n2186;
  wire [63:0] n2187;
  wire [63:0] n2188;
  wire [63:0] n2189;
  wire [63:0] n2190;
  wire [63:0] n2191;
  wire [63:0] n2192;
  wire [63:0] n2193;
  wire [63:0] n2194;
  wire [63:0] n2195;
  wire [63:0] n2196;
  wire [63:0] n2197;
  wire [63:0] n2198;
  wire [63:0] n2199;
  wire [62:0] n2205;
  wire n2206;
  wire [63:0] n2207;
  wire [63:0] n2208;
  wire [62:0] n2214;
  wire n2215;
  wire [63:0] n2216;
  wire [63:0] n2217;
  wire [62:0] n2223;
  wire n2224;
  wire [63:0] n2225;
  wire [63:0] n2226;
  wire [62:0] n2232;
  wire n2233;
  wire [63:0] n2234;
  wire [63:0] n2235;
  wire [62:0] n2241;
  wire n2242;
  wire [63:0] n2243;
  wire [63:0] n2244;
  wire [63:0] n2245;
  wire [63:0] n2246;
  wire [19:0] n2252;
  wire [43:0] n2253;
  wire [63:0] n2254;
  wire [63:0] n2255;
  wire [20:0] n2261;
  wire [42:0] n2262;
  wire [63:0] n2263;
  wire [63:0] n2264;
  wire [63:0] n2265;
  wire [63:0] n2266;
  wire [63:0] n2267;
  wire [63:0] n2268;
  wire [42:0] n2274;
  wire [20:0] n2275;
  wire [63:0] n2276;
  wire [63:0] n2277;
  wire [63:0] n2278;
  wire [63:0] n2279;
  wire [63:0] n2280;
  wire [49:0] n2286;
  wire [13:0] n2287;
  wire [63:0] n2288;
  wire [63:0] n2289;
  wire [63:0] n2290;
  wire [63:0] n2291;
  wire [63:0] n2292;
  wire [63:0] n2293;
  wire [63:0] n2294;
  wire [63:0] n2295;
  wire [63:0] n2296;
  wire [63:0] n2297;
  wire [63:0] n2298;
  wire [35:0] n2304;
  wire [27:0] n2305;
  wire [63:0] n2306;
  wire [63:0] n2307;
  wire [43:0] n2313;
  wire [19:0] n2314;
  wire [63:0] n2315;
  wire [63:0] n2316;
  wire [60:0] n2322;
  wire [2:0] n2323;
  wire [63:0] n2324;
  wire [63:0] n2325;
  wire [63:0] n2326;
  wire [63:0] n2327;
  wire [63:0] n2328;
  wire [18:0] n2334;
  wire [44:0] n2335;
  wire [63:0] n2336;
  wire [63:0] n2337;
  wire [63:0] n2338;
  wire [63:0] n2339;
  wire [63:0] n2340;
  wire [2:0] n2346;
  wire [60:0] n2347;
  wire [63:0] n2348;
  wire [63:0] n2349;
  wire [63:0] n2350;
  wire [63:0] n2351;
  wire [63:0] n2352;
  wire [63:0] n2353;
  wire [63:0] n2354;
  wire [63:0] n2355;
  wire [63:0] n2356;
  wire [63:0] n2357;
  wire [63:0] n2358;
  wire [62:0] n2364;
  wire n2365;
  wire [63:0] n2366;
  wire [63:0] n2367;
  wire [57:0] n2373;
  wire [5:0] n2374;
  wire [63:0] n2375;
  wire [63:0] n2376;
  wire [38:0] n2382;
  wire [24:0] n2383;
  wire [63:0] n2384;
  wire [63:0] n2385;
  wire [63:0] n2386;
  wire [63:0] n2387;
  wire [63:0] n2388;
  wire [55:0] n2394;
  wire [7:0] n2395;
  wire [63:0] n2396;
  wire [63:0] n2397;
  wire [63:0] n2398;
  wire [63:0] n2399;
  wire [63:0] n2400;
  wire [45:0] n2406;
  wire [17:0] n2407;
  wire [63:0] n2408;
  wire [63:0] n2409;
  wire [63:0] n2410;
  wire [63:0] n2411;
  wire [63:0] n2412;
  wire [63:0] n2413;
  wire [63:0] n2414;
  wire [63:0] n2415;
  wire [63:0] n2416;
  wire [63:0] n2417;
  wire [63:0] n2418;
  wire [36:0] n2424;
  wire [26:0] n2425;
  wire [63:0] n2426;
  wire [63:0] n2427;
  wire [27:0] n2433;
  wire [35:0] n2434;
  wire [63:0] n2435;
  wire [63:0] n2436;
  wire [53:0] n2442;
  wire [9:0] n2443;
  wire [63:0] n2444;
  wire [63:0] n2445;
  wire [63:0] n2446;
  wire [63:0] n2447;
  wire [63:0] n2448;
  wire [48:0] n2454;
  wire [14:0] n2455;
  wire [63:0] n2456;
  wire [63:0] n2457;
  wire [63:0] n2458;
  wire [63:0] n2459;
  wire [63:0] n2460;
  wire [7:0] n2466;
  wire [55:0] n2467;
  wire [63:0] n2468;
  wire [63:0] n2469;
  wire [63:0] n2470;
  wire [63:0] n2471;
  wire [63:0] n2472;
  wire [63:0] n2473;
  wire [63:0] n2474;
  wire [63:0] n2475;
  wire [63:0] n2476;
  wire [63:0] n2477;
  wire [63:0] n2478;
  wire [1:0] n2484;
  wire [61:0] n2485;
  wire [63:0] n2486;
  wire [63:0] n2487;
  wire [8:0] n2493;
  wire [54:0] n2494;
  wire [63:0] n2495;
  wire [63:0] n2496;
  wire [24:0] n2502;
  wire [38:0] n2503;
  wire [63:0] n2504;
  wire [63:0] n2505;
  wire [63:0] n2506;
  wire [63:0] n2507;
  wire [63:0] n2508;
  wire [22:0] n2514;
  wire [40:0] n2515;
  wire [63:0] n2516;
  wire [63:0] n2517;
  wire [63:0] n2518;
  wire [63:0] n2519;
  wire [63:0] n2520;
  wire [61:0] n2526;
  wire [1:0] n2527;
  wire [63:0] n2528;
  wire [63:0] n2529;
  wire [63:0] n2530;
  wire [63:0] n2531;
  wire [63:0] n2532;
  wire [63:0] n2533;
  wire [63:0] n2534;
  wire [63:0] n2535;
  wire [63:0] n2536;
  wire [63:0] n2537;
  wire [1599:0] n2538;
  assign rout = n2538; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:234:8 */
  assign aba = n2155; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:234:13 */
  assign abe = n2156; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:234:18 */
  assign abi = n2157; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:234:23 */
  assign abo = n2158; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:234:28 */
  assign abu = n2159; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:235:8 */
  assign aga = n2160; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:235:13 */
  assign age = n2161; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:235:18 */
  assign agi = n2162; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:235:23 */
  assign ago = n2163; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:235:28 */
  assign agu = n2164; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:236:8 */
  assign aka = n2165; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:236:13 */
  assign ake = n2166; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:236:18 */
  assign aki = n2167; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:236:23 */
  assign ako = n2168; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:236:28 */
  assign aku = n2169; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:237:8 */
  assign ama = n2170; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:237:13 */
  assign ame = n2171; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:237:18 */
  assign ami = n2172; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:237:23 */
  assign amo = n2173; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:237:28 */
  assign amu = n2174; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:238:8 */
  assign asa = n2175; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:238:13 */
  assign ase = n2176; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:238:18 */
  assign asi = n2177; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:238:23 */
  assign aso = n2178; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:238:28 */
  assign asu = n2179; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:239:8 */
  assign aba_wire = n2245; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:239:18 */
  assign abe_wire = n2358; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:239:28 */
  assign abi_wire = n2478; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:239:38 */
  assign abo_wire = n2298; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:239:48 */
  assign abu_wire = n2418; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:240:8 */
  assign aga_wire = n2427; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:240:18 */
  assign age_wire = n2246; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:240:28 */
  assign agi_wire = n2367; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:240:38 */
  assign ago_wire = n2487; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:240:48 */
  assign agu_wire = n2307; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:241:8 */
  assign aka_wire = n2316; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:241:18 */
  assign ake_wire = n2436; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:241:28 */
  assign aki_wire = n2255; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:241:38 */
  assign ako_wire = n2376; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:241:48 */
  assign aku_wire = n2496; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:242:8 */
  assign ama_wire = n2508; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:242:18 */
  assign ame_wire = n2328; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:242:28 */
  assign ami_wire = n2448; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:242:38 */
  assign amo_wire = n2268; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:242:48 */
  assign amu_wire = n2388; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:243:8 */
  assign asa_wire = n2400; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:243:18 */
  assign ase_wire = n2520; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:243:28 */
  assign asi_wire = n2340; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:243:38 */
  assign aso_wire = n2460; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:243:48 */
  assign asu_wire = n2280; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:244:8 */
  assign bba = aba_wire; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:244:13 */
  assign bbe = n2254; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:244:18 */
  assign bbi = n2263; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:244:23 */
  assign bbo = n2276; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:244:28 */
  assign bbu = n2288; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:245:8 */
  assign bga = n2306; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:245:13 */
  assign bge = n2315; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:245:18 */
  assign bgi = n2324; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:245:23 */
  assign bgo = n2336; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:245:28 */
  assign bgu = n2348; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:246:8 */
  assign bka = n2366; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:246:13 */
  assign bke = n2375; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:246:18 */
  assign bki = n2384; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:246:23 */
  assign bko = n2396; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:246:28 */
  assign bku = n2408; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:247:8 */
  assign bma = n2426; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:247:13 */
  assign bme = n2435; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:247:18 */
  assign bmi = n2444; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:247:23 */
  assign bmo = n2456; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:247:28 */
  assign bmu = n2468; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:248:8 */
  assign bsa = n2486; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:248:13 */
  assign bse = n2495; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:248:18 */
  assign bsi = n2504; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:248:23 */
  assign bso = n2516; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:248:28 */
  assign bsu = n2528; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:249:8 */
  assign ca = n2183; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:249:12 */
  assign ce = n2187; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:249:16 */
  assign ci = n2191; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:249:20 */
  assign co = n2195; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:249:24 */
  assign cu = n2199; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:250:8 */
  assign da = n2208; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:250:12 */
  assign de = n2217; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:250:16 */
  assign di = n2226; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:250:20 */
  assign \do  = n2235; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:250:24 */
  assign du = n2244; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:251:8 */
  assign eba = n2267; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:251:13 */
  assign ebe = n2279; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:251:18 */
  assign ebi = n2291; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:251:23 */
  assign ebo = n2294; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:251:28 */
  assign ebu = n2297; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:251:33 */
  assign eba_wire = n2266; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:252:8 */
  assign ega = n2327; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:252:13 */
  assign ege = n2339; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:252:18 */
  assign egi = n2351; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:252:23 */
  assign ego = n2354; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:252:28 */
  assign egu = n2357; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:253:8 */
  assign eka = n2387; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:253:13 */
  assign eke = n2399; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:253:18 */
  assign eki = n2411; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:253:23 */
  assign eko = n2414; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:253:28 */
  assign eku = n2417; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:254:8 */
  assign ema = n2447; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:254:13 */
  assign eme = n2459; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:254:18 */
  assign emi = n2471; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:254:23 */
  assign emo = n2474; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:254:28 */
  assign emu = n2477; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:255:8 */
  assign esa = n2507; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:255:13 */
  assign ese = n2519; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:255:18 */
  assign esi = n2531; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:255:23 */
  assign eso = n2534; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:255:28 */
  assign esu = n2537; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:259:23 */
  assign n2155 = rin[1599:1536]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:260:23 */
  assign n2156 = rin[1535:1472]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:261:23 */
  assign n2157 = rin[1471:1408]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:262:23 */
  assign n2158 = rin[1407:1344]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:263:23 */
  assign n2159 = rin[1343:1280]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:264:23 */
  assign n2160 = rin[1279:1216]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:265:23 */
  assign n2161 = rin[1215:1152]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:266:23 */
  assign n2162 = rin[1151:1088]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:267:23 */
  assign n2163 = rin[1087:1024]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:268:23 */
  assign n2164 = rin[1023:960]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:269:23 */
  assign n2165 = rin[959:896]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:270:23 */
  assign n2166 = rin[895:832]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:271:23 */
  assign n2167 = rin[831:768]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:272:23 */
  assign n2168 = rin[767:704]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:273:23 */
  assign n2169 = rin[703:640]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:274:23 */
  assign n2170 = rin[639:576]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:275:23 */
  assign n2171 = rin[575:512]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:276:23 */
  assign n2172 = rin[511:448]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:277:23 */
  assign n2173 = rin[447:384]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:278:23 */
  assign n2174 = rin[383:320]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:279:23 */
  assign n2175 = rin[319:256]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:280:23 */
  assign n2176 = rin[255:192]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:281:23 */
  assign n2177 = rin[191:128]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:282:23 */
  assign n2178 = rin[127:64]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:283:23 */
  assign n2179 = rin[63:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:285:19 */
  assign n2180 = aba ^ aga;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:285:27 */
  assign n2181 = n2180 ^ aka;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:285:35 */
  assign n2182 = n2181 ^ ama;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:285:43 */
  assign n2183 = n2182 ^ asa;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:286:19 */
  assign n2184 = abe ^ age;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:286:27 */
  assign n2185 = n2184 ^ ake;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:286:35 */
  assign n2186 = n2185 ^ ame;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:286:43 */
  assign n2187 = n2186 ^ ase;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:287:19 */
  assign n2188 = abi ^ agi;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:287:27 */
  assign n2189 = n2188 ^ aki;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:287:35 */
  assign n2190 = n2189 ^ ami;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:287:43 */
  assign n2191 = n2190 ^ asi;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:288:19 */
  assign n2192 = abo ^ ago;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:288:27 */
  assign n2193 = n2192 ^ ako;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:288:35 */
  assign n2194 = n2193 ^ amo;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:288:43 */
  assign n2195 = n2194 ^ aso;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:289:19 */
  assign n2196 = abu ^ agu;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:289:27 */
  assign n2197 = n2196 ^ aku;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:289:35 */
  assign n2198 = n2197 ^ amu;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:289:43 */
  assign n2199 = n2198 ^ asu;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2205 = ce[62:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2206 = ce[63]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2207 = {n2205, n2206};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:292:18 */
  assign n2208 = cu ^ n2207;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2214 = ci[62:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2215 = ci[63]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2216 = {n2214, n2215};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:293:18 */
  assign n2217 = ca ^ n2216;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2223 = co[62:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2224 = co[63]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2225 = {n2223, n2224};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:294:18 */
  assign n2226 = ce ^ n2225;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2232 = cu[62:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2233 = cu[63]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2234 = {n2232, n2233};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:295:18 */
  assign n2235 = ci ^ n2234;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2241 = ca[62:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2242 = ca[63]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2243 = {n2241, n2242};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:296:18 */
  assign n2244 = co ^ n2243;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:298:25 */
  assign n2245 = aba ^ da;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:301:25 */
  assign n2246 = age ^ de;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2252 = age_wire[19:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2253 = age_wire[63:20]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2254 = {n2252, n2253};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:303:25 */
  assign n2255 = aki ^ di;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2261 = aki_wire[20:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2262 = aki_wire[63:21]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2263 = {n2261, n2262};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:305:33 */
  assign n2264 = ~bbe;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:305:42 */
  assign n2265 = n2264 & bbi;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:305:27 */
  assign n2266 = bba ^ n2265;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:306:25 */
  assign n2267 = eba_wire ^ rc;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:307:25 */
  assign n2268 = amo ^ \do ;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2274 = amo_wire[42:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2275 = amo_wire[63:43]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2276 = {n2274, n2275};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:309:26 */
  assign n2277 = ~bbi;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:309:35 */
  assign n2278 = n2277 & bbo;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:309:20 */
  assign n2279 = bbe ^ n2278;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:310:25 */
  assign n2280 = asu ^ du;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2286 = asu_wire[49:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2287 = asu_wire[63:50]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2288 = {n2286, n2287};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:312:26 */
  assign n2289 = ~bbo;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:312:35 */
  assign n2290 = n2289 & bbu;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:312:20 */
  assign n2291 = bbi ^ n2290;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:313:26 */
  assign n2292 = ~bbu;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:313:35 */
  assign n2293 = n2292 & bba;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:313:20 */
  assign n2294 = bbo ^ n2293;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:314:26 */
  assign n2295 = ~bba;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:314:35 */
  assign n2296 = n2295 & bbe;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:314:20 */
  assign n2297 = bbu ^ n2296;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:315:25 */
  assign n2298 = abo ^ \do ;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2304 = abo_wire[35:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2305 = abo_wire[63:36]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2306 = {n2304, n2305};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:317:25 */
  assign n2307 = agu ^ du;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2313 = agu_wire[43:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2314 = agu_wire[63:44]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2315 = {n2313, n2314};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:319:25 */
  assign n2316 = aka ^ da;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2322 = aka_wire[60:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2323 = aka_wire[63:61]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2324 = {n2322, n2323};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:321:28 */
  assign n2325 = ~bge;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:321:36 */
  assign n2326 = n2325 & bgi;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:321:22 */
  assign n2327 = bga ^ n2326;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:322:25 */
  assign n2328 = ame ^ de;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2334 = ame_wire[18:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2335 = ame_wire[63:19]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2336 = {n2334, n2335};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:324:26 */
  assign n2337 = ~bgi;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:324:34 */
  assign n2338 = n2337 & bgo;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:324:20 */
  assign n2339 = bge ^ n2338;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:325:26 */
  assign n2340 = asi ^ di;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2346 = asi_wire[2:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2347 = asi_wire[63:3]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2348 = {n2346, n2347};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:327:26 */
  assign n2349 = ~bgo;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:327:34 */
  assign n2350 = n2349 & bgu;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:327:20 */
  assign n2351 = bgi ^ n2350;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:328:26 */
  assign n2352 = ~bgu;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:328:34 */
  assign n2353 = n2352 & bga;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:328:20 */
  assign n2354 = bgo ^ n2353;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:329:26 */
  assign n2355 = ~bga;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:329:34 */
  assign n2356 = n2355 & bge;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:329:20 */
  assign n2357 = bgu ^ n2356;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:330:25 */
  assign n2358 = abe ^ de;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2364 = abe_wire[62:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2365 = abe_wire[63]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2366 = {n2364, n2365};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:332:26 */
  assign n2367 = agi ^ di;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2373 = agi_wire[57:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2374 = agi_wire[63:58]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2375 = {n2373, n2374};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:334:25 */
  assign n2376 = ako ^ \do ;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2382 = ako_wire[38:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2383 = ako_wire[63:39]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2384 = {n2382, n2383};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:336:27 */
  assign n2385 = ~bke;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:336:35 */
  assign n2386 = n2385 & bki;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:336:21 */
  assign n2387 = bka ^ n2386;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:337:26 */
  assign n2388 = amu ^ du;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2394 = amu_wire[55:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2395 = amu_wire[63:56]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2396 = {n2394, n2395};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:339:26 */
  assign n2397 = ~bki;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:339:35 */
  assign n2398 = n2397 & bko;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:339:20 */
  assign n2399 = bke ^ n2398;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:340:25 */
  assign n2400 = asa ^ da;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2406 = asa_wire[45:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2407 = asa_wire[63:46]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2408 = {n2406, n2407};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:342:26 */
  assign n2409 = ~bko;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:342:34 */
  assign n2410 = n2409 & bku;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:342:20 */
  assign n2411 = bki ^ n2410;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:343:26 */
  assign n2412 = ~bku;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:343:34 */
  assign n2413 = n2412 & bka;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:343:20 */
  assign n2414 = bko ^ n2413;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:344:26 */
  assign n2415 = ~bka;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:344:34 */
  assign n2416 = n2415 & bke;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:344:20 */
  assign n2417 = bku ^ n2416;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:345:25 */
  assign n2418 = abu ^ du;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2424 = abu_wire[36:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2425 = abu_wire[63:37]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2426 = {n2424, n2425};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:347:25 */
  assign n2427 = aga ^ da;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2433 = aga_wire[27:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2434 = aga_wire[63:28]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2435 = {n2433, n2434};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:349:25 */
  assign n2436 = ake ^ de;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2442 = ake_wire[53:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2443 = ake_wire[63:54]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2444 = {n2442, n2443};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:351:27 */
  assign n2445 = ~bme;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:351:35 */
  assign n2446 = n2445 & bmi;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:351:21 */
  assign n2447 = bma ^ n2446;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:352:25 */
  assign n2448 = ami ^ di;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2454 = ami_wire[48:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2455 = ami_wire[63:49]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2456 = {n2454, n2455};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:354:27 */
  assign n2457 = ~bmi;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:354:35 */
  assign n2458 = n2457 & bmo;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:354:21 */
  assign n2459 = bme ^ n2458;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:355:26 */
  assign n2460 = aso ^ \do ;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2466 = aso_wire[7:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2467 = aso_wire[63:8]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2468 = {n2466, n2467};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:357:26 */
  assign n2469 = ~bmo;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:357:34 */
  assign n2470 = n2469 & bmu;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:357:20 */
  assign n2471 = bmi ^ n2470;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:358:26 */
  assign n2472 = ~bmu;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:358:34 */
  assign n2473 = n2472 & bma;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:358:20 */
  assign n2474 = bmo ^ n2473;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:359:26 */
  assign n2475 = ~bma;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:359:34 */
  assign n2476 = n2475 & bme;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:359:20 */
  assign n2477 = bmu ^ n2476;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:360:25 */
  assign n2478 = abi ^ di;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2484 = abi_wire[1:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2485 = abi_wire[63:2]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2486 = {n2484, n2485};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:362:25 */
  assign n2487 = ago ^ \do ;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2493 = ago_wire[8:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2494 = ago_wire[63:9]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2495 = {n2493, n2494};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:364:25 */
  assign n2496 = aku ^ du;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2502 = aku_wire[24:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2503 = aku_wire[63:25]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2504 = {n2502, n2503};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:366:26 */
  assign n2505 = ~bse;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:366:34 */
  assign n2506 = n2505 & bsi;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:366:20 */
  assign n2507 = bsa ^ n2506;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:367:25 */
  assign n2508 = ama ^ da;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2514 = ama_wire[22:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2515 = ama_wire[63:23]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2516 = {n2514, n2515};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:369:27 */
  assign n2517 = ~bsi;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:369:35 */
  assign n2518 = n2517 & bso;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:369:21 */
  assign n2519 = bse ^ n2518;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:370:25 */
  assign n2520 = ase ^ de;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:26 */
  assign n2526 = ase_wire[61:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:53 */
  assign n2527 = ase_wire[63:62]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:469:50 */
  assign n2528 = {n2526, n2527};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:372:27 */
  assign n2529 = ~bso;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:372:36 */
  assign n2530 = n2529 & bsu;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:372:21 */
  assign n2531 = bsi ^ n2530;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:373:27 */
  assign n2532 = ~bsu;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:373:35 */
  assign n2533 = n2532 & bsa;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:373:21 */
  assign n2534 = bso ^ n2533;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:374:27 */
  assign n2535 = ~bsa;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:374:35 */
  assign n2536 = n2535 & bse;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:374:21 */
  assign n2537 = bsu ^ n2536;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_round.vhd:22:5 */
  assign n2538 = {eba, ebe, ebi, ebo, ebu, ega, ege, egi, ego, egu, eka, eke, eki, eko, eku, ema, eme, emi, emo, emu, esa, ese, esi, eso, esu};
endmodule

module keccak_cons_Bkeccak_cons_1
  (input  [4:0] addr,
   output [63:0] rc);
  wire [63:0] n2153; // mem_rd
  assign rc = n2153; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_cons.vhd:38:22 */
  wire [63:0] n2151[31:0] ; // memory
    assign n2151[31] = 64'b0000000000000000000000000000000000000000000000000000000000000000;
  assign n2151[30] = 64'b0000000000000000000000000000000000000000000000000000000000000000;
  assign n2151[29] = 64'b0000000000000000000000000000000000000000000000000000000000000000;
  assign n2151[28] = 64'b0000000000000000000000000000000000000000000000000000000000000000;
  assign n2151[27] = 64'b0000000000000000000000000000000000000000000000000000000000000000;
  assign n2151[26] = 64'b0000000000000000000000000000000000000000000000000000000000000000;
  assign n2151[25] = 64'b0000000000000000000000000000000000000000000000000000000000000000;
  assign n2151[24] = 64'b0000000000000000000000000000000000000000000000000000000000000000;
  assign n2151[23] = 64'b1000000000000000000000000000000010000000000000001000000000001000;
  assign n2151[22] = 64'b0000000000000000000000000000000010000000000000000000000000000001;
  assign n2151[21] = 64'b1000000000000000000000000000000000000000000000001000000010000000;
  assign n2151[20] = 64'b1000000000000000000000000000000010000000000000001000000010000001;
  assign n2151[19] = 64'b1000000000000000000000000000000010000000000000000000000000001010;
  assign n2151[18] = 64'b0000000000000000000000000000000000000000000000001000000000001010;
  assign n2151[17] = 64'b1000000000000000000000000000000000000000000000000000000010000000;
  assign n2151[16] = 64'b1000000000000000000000000000000000000000000000001000000000000010;
  assign n2151[15] = 64'b1000000000000000000000000000000000000000000000001000000000000011;
  assign n2151[14] = 64'b1000000000000000000000000000000000000000000000001000000010001001;
  assign n2151[13] = 64'b1000000000000000000000000000000000000000000000000000000010001011;
  assign n2151[12] = 64'b0000000000000000000000000000000010000000000000001000000010001011;
  assign n2151[11] = 64'b0000000000000000000000000000000010000000000000000000000000001010;
  assign n2151[10] = 64'b0000000000000000000000000000000010000000000000001000000000001001;
  assign n2151[9] = 64'b0000000000000000000000000000000000000000000000000000000010001000;
  assign n2151[8] = 64'b0000000000000000000000000000000000000000000000000000000010001010;
  assign n2151[7] = 64'b1000000000000000000000000000000000000000000000001000000000001001;
  assign n2151[6] = 64'b1000000000000000000000000000000010000000000000001000000010000001;
  assign n2151[5] = 64'b0000000000000000000000000000000010000000000000000000000000000001;
  assign n2151[4] = 64'b0000000000000000000000000000000000000000000000001000000010001011;
  assign n2151[3] = 64'b1000000000000000000000000000000010000000000000001000000000000000;
  assign n2151[2] = 64'b1000000000000000000000000000000000000000000000001000000010001010;
  assign n2151[1] = 64'b0000000000000000000000000000000000000000000000001000000010000010;
  assign n2151[0] = 64'b0000000000000000000000000000000000000000000000000000000000000001;
  assign n2153 = n2151[addr];
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_cons.vhd:38:22 */
endmodule

module regn_Bstruct_1600_cff588bd0114761108cce8606ec6021ff729e20e
  (input  clk,
   input  rst,
   input  en,
   input  [1599:0] \input ,
   output [1599:0] \output );
  wire [1599:0] n2138;
  wire [1599:0] n2140;
  reg [1599:0] n2143;
  assign \output  = n2143; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/regn.vhd:34:25 */
  assign n2138 = en ? \input  : n2143;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/regn.vhd:32:25 */
  assign n2140 = rst ? 1600'b0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 : n2138;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/regn.vhd:31:17 */
  always @(posedge clk)
    n2143 <= n2140;
endmodule

module sipo_Bbehavioral_1344_64
  (input  clk,
   input  en,
   input  [63:0] \input ,
   output [1343:0] \output );
  wire [1343:0] \reg ;
  wire [63:0] n1882;
  wire [63:0] n1883;
  wire [63:0] n1884;
  wire [63:0] n1885;
  wire [63:0] n1886;
  wire [63:0] n1887;
  wire [63:0] n1888;
  wire [63:0] n1889;
  wire [63:0] n1890;
  wire [63:0] n1891;
  wire [63:0] n1892;
  wire [63:0] n1893;
  wire [63:0] n1894;
  wire [63:0] n1895;
  wire [63:0] n1896;
  wire [63:0] n1897;
  wire [63:0] n1898;
  wire [63:0] n1899;
  wire [63:0] n1900;
  wire [63:0] n1901;
  wire [63:0] n1902;
  wire [63:0] n1905;
  wire [63:0] n1913;
  wire [63:0] n1921;
  wire [63:0] n1929;
  wire [63:0] n1937;
  wire [63:0] n1945;
  wire [63:0] n1953;
  wire [63:0] n1961;
  wire [63:0] n1969;
  wire [63:0] n1977;
  wire [63:0] n1985;
  wire [63:0] n1993;
  wire [63:0] n2001;
  wire [63:0] n2009;
  wire [63:0] n2017;
  wire [63:0] n2025;
  wire [63:0] n2033;
  wire [63:0] n2041;
  wire [63:0] n2049;
  wire [63:0] n2057;
  wire [1343:0] n2070;
  wire [1343:0] n2071;
  wire [63:0] n2072;
  wire [63:0] n2073;
  reg [63:0] n2074;
  wire [63:0] n2075;
  wire [63:0] n2076;
  reg [63:0] n2077;
  wire [63:0] n2078;
  wire [63:0] n2079;
  reg [63:0] n2080;
  wire [63:0] n2081;
  wire [63:0] n2082;
  reg [63:0] n2083;
  wire [63:0] n2084;
  wire [63:0] n2085;
  reg [63:0] n2086;
  wire [63:0] n2087;
  wire [63:0] n2088;
  reg [63:0] n2089;
  wire [63:0] n2090;
  wire [63:0] n2091;
  reg [63:0] n2092;
  wire [63:0] n2093;
  wire [63:0] n2094;
  reg [63:0] n2095;
  wire [63:0] n2096;
  wire [63:0] n2097;
  reg [63:0] n2098;
  wire [63:0] n2099;
  wire [63:0] n2100;
  reg [63:0] n2101;
  wire [63:0] n2102;
  wire [63:0] n2103;
  reg [63:0] n2104;
  wire [63:0] n2105;
  wire [63:0] n2106;
  reg [63:0] n2107;
  wire [63:0] n2108;
  wire [63:0] n2109;
  reg [63:0] n2110;
  wire [63:0] n2111;
  wire [63:0] n2112;
  reg [63:0] n2113;
  wire [63:0] n2114;
  wire [63:0] n2115;
  reg [63:0] n2116;
  wire [63:0] n2117;
  wire [63:0] n2118;
  reg [63:0] n2119;
  wire [63:0] n2120;
  wire [63:0] n2121;
  reg [63:0] n2122;
  wire [63:0] n2123;
  wire [63:0] n2124;
  reg [63:0] n2125;
  wire [63:0] n2126;
  wire [63:0] n2127;
  reg [63:0] n2128;
  wire [63:0] n2129;
  wire [63:0] n2130;
  reg [63:0] n2131;
  wire [63:0] n2132;
  wire [63:0] n2133;
  reg [63:0] n2134;
  assign \output  = n2071; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:30:16 */
  assign \reg  = n2070; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1882 = \reg [1343:1280]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1883 = \reg [1279:1216]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1884 = \reg [1215:1152]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1885 = \reg [1151:1088]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1886 = \reg [1087:1024]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1887 = \reg [1023:960]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1888 = \reg [959:896]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1889 = \reg [895:832]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1890 = \reg [831:768]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1891 = \reg [767:704]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1892 = \reg [703:640]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1893 = \reg [639:576]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1894 = \reg [575:512]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1895 = \reg [511:448]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1896 = \reg [447:384]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1897 = \reg [383:320]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1898 = \reg [319:256]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1899 = \reg [255:192]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1900 = \reg [191:128]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1901 = \reg [127:64]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:33:57 */
  assign n1902 = \reg [63:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1905 = \reg [63:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1913 = \reg [127:64]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1921 = \reg [191:128]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1929 = \reg [255:192]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1937 = \reg [319:256]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1945 = \reg [383:320]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1953 = \reg [447:384]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1961 = \reg [511:448]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1969 = \reg [575:512]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1977 = \reg [639:576]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1985 = \reg [703:640]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n1993 = \reg [767:704]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n2001 = \reg [831:768]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n2009 = \reg [895:832]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n2017 = \reg [959:896]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n2025 = \reg [1023:960]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n2033 = \reg [1087:1024]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n2041 = \reg [1151:1088]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n2049 = \reg [1215:1152]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:41:54 */
  assign n2057 = \reg [1279:1216]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:30:16 */
  assign n2070 = {n2074, n2077, n2080, n2083, n2086, n2089, n2092, n2095, n2098, n2101, n2104, n2107, n2110, n2113, n2116, n2119, n2122, n2125, n2128, n2131, n2134};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:23:17 */
  assign n2071 = {n1882, n1883, n1884, n1885, n1886, n1887, n1888, n1889, n1890, n1891, n1892, n1893, n1894, n1895, n1896, n1897, n1898, n1899, n1900, n1901, n1902};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2072 = \reg [1343:1280]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2073 = en ? n2057 : n2072;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2074 <= n2073;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2075 = \reg [1279:1216]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2076 = en ? n2049 : n2075;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2077 <= n2076;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2078 = \reg [1215:1152]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2079 = en ? n2041 : n2078;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2080 <= n2079;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2081 = \reg [1151:1088]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2082 = en ? n2033 : n2081;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2083 <= n2082;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2084 = \reg [1087:1024]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2085 = en ? n2025 : n2084;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2086 <= n2085;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2087 = \reg [1023:960]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2088 = en ? n2017 : n2087;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2089 <= n2088;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2090 = \reg [959:896]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2091 = en ? n2009 : n2090;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2092 <= n2091;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2093 = \reg [895:832]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2094 = en ? n2001 : n2093;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2095 <= n2094;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2096 = \reg [831:768]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2097 = en ? n1993 : n2096;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2098 <= n2097;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2099 = \reg [767:704]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2100 = en ? n1985 : n2099;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2101 <= n2100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2102 = \reg [703:640]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2103 = en ? n1977 : n2102;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2104 <= n2103;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2105 = \reg [639:576]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2106 = en ? n1969 : n2105;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2107 <= n2106;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2108 = \reg [575:512]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2109 = en ? n1961 : n2108;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2110 <= n2109;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2111 = \reg [511:448]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2112 = en ? n1953 : n2111;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2113 <= n2112;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2114 = \reg [447:384]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2115 = en ? n1945 : n2114;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2116 <= n2115;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2117 = \reg [383:320]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2118 = en ? n1937 : n2117;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2119 <= n2118;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2120 = \reg [319:256]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2121 = en ? n1929 : n2120;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2122 <= n2121;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2123 = \reg [255:192]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2124 = en ? n1921 : n2123;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2125 <= n2124;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2126 = \reg [191:128]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2127 = en ? n1913 : n2126;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2128 <= n2127;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2129 = \reg [127:64]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  assign n2130 = en ? n1905 : n2129;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:39:25 */
  always @(posedge clk)
    n2131 <= n2130;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:49:17 */
  assign n2132 = \reg [63:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:49:17 */
  assign n2133 = en ? \input  : n2132;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sipo.vhd:49:17 */
  always @(posedge clk)
    n2134 <= n2133;
endmodule

module keccak_bytepad_Bstruct_64
  (input  [63:0] din_input,
   output [63:0] din_output,
   input  [7:0] sel_pad_location,
   input  [7:0] sel_din,
   input  last_word,
   input  [1:0] mode,
   input  [63:0] dout_input,
   output [63:0] dout_output,
   input  [7:0] sel_dout,
   input  last_out_word);
  wire [63:0] byte_pad_wire;
  wire [1:0] sel_last_mux;
  wire [7:0] first_byte;
  wire [7:0] first_last_byte;
  wire [63:0] dout_output_padded;
  wire n1764;
  wire [7:0] n1765;
  wire [7:0] n1767;
  wire n1768;
  wire [7:0] n1769;
  wire [7:0] n1770;
  wire n1771;
  wire [7:0] n1772;
  wire [7:0] n1774;
  wire n1775;
  wire [7:0] n1776;
  wire [7:0] n1777;
  wire n1778;
  wire [7:0] n1779;
  wire [7:0] n1781;
  wire n1782;
  wire [7:0] n1783;
  wire [7:0] n1784;
  wire n1785;
  wire [7:0] n1786;
  wire [7:0] n1788;
  wire n1789;
  wire [7:0] n1790;
  wire [7:0] n1791;
  wire n1792;
  wire [7:0] n1793;
  wire [7:0] n1795;
  wire n1796;
  wire [7:0] n1797;
  wire [7:0] n1798;
  wire n1799;
  wire [7:0] n1800;
  wire [7:0] n1802;
  wire n1803;
  wire [7:0] n1804;
  wire [7:0] n1805;
  wire n1806;
  wire [7:0] n1807;
  wire [7:0] n1809;
  wire n1810;
  wire [7:0] n1811;
  wire [7:0] n1812;
  wire n1813;
  wire [1:0] n1814;
  wire n1817;
  wire n1819;
  wire n1820;
  wire [7:0] n1821;
  wire n1825;
  wire n1827;
  wire n1828;
  wire [7:0] n1829;
  wire n1833;
  wire n1835;
  wire n1838;
  wire [2:0] n1839;
  reg [7:0] n1840;
  wire [7:0] n1841;
  wire n1842;
  wire [7:0] n1843;
  wire [7:0] n1844;
  wire [7:0] n1845;
  wire n1846;
  wire [7:0] n1847;
  wire [7:0] n1849;
  wire n1850;
  wire [7:0] n1851;
  wire [7:0] n1853;
  wire n1854;
  wire [7:0] n1855;
  wire [7:0] n1857;
  wire n1858;
  wire [7:0] n1859;
  wire [7:0] n1861;
  wire n1862;
  wire [7:0] n1863;
  wire [7:0] n1865;
  wire n1866;
  wire [7:0] n1867;
  wire [7:0] n1869;
  wire n1870;
  wire [7:0] n1871;
  wire [7:0] n1873;
  wire n1874;
  wire [7:0] n1875;
  wire [63:0] n1877;
  wire [63:0] n1878;
  wire [63:0] n1879;
  wire [63:0] n1880;
  assign din_output = n1880; //(module output)
  assign dout_output = n1877; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:30:16 */
  assign byte_pad_wire = n1878; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:31:16 */
  assign sel_last_mux = n1814; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:32:12 */
  assign first_byte = n1821; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:32:24 */
  assign first_last_byte = n1829; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:33:12 */
  assign dout_output_padded = n1879; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:60 */
  assign n1764 = sel_pad_location[7]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:39 */
  assign n1765 = n1764 ? first_byte : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:62 */
  assign n1767 = din_input[63:56]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:20 */
  assign n1768 = sel_din[7]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:85 */
  assign n1769 = n1768 ? n1767 : n1770;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:48 */
  assign n1770 = byte_pad_wire[63:56]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:60 */
  assign n1771 = sel_pad_location[6]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:39 */
  assign n1772 = n1771 ? first_byte : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:62 */
  assign n1774 = din_input[55:48]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:20 */
  assign n1775 = sel_din[6]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:85 */
  assign n1776 = n1775 ? n1774 : n1777;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:48 */
  assign n1777 = byte_pad_wire[55:48]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:60 */
  assign n1778 = sel_pad_location[5]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:39 */
  assign n1779 = n1778 ? first_byte : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:62 */
  assign n1781 = din_input[47:40]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:20 */
  assign n1782 = sel_din[5]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:85 */
  assign n1783 = n1782 ? n1781 : n1784;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:48 */
  assign n1784 = byte_pad_wire[47:40]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:60 */
  assign n1785 = sel_pad_location[4]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:39 */
  assign n1786 = n1785 ? first_byte : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:62 */
  assign n1788 = din_input[39:32]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:20 */
  assign n1789 = sel_din[4]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:85 */
  assign n1790 = n1789 ? n1788 : n1791;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:48 */
  assign n1791 = byte_pad_wire[39:32]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:60 */
  assign n1792 = sel_pad_location[3]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:39 */
  assign n1793 = n1792 ? first_byte : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:62 */
  assign n1795 = din_input[31:24]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:20 */
  assign n1796 = sel_din[3]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:85 */
  assign n1797 = n1796 ? n1795 : n1798;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:48 */
  assign n1798 = byte_pad_wire[31:24]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:60 */
  assign n1799 = sel_pad_location[2]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:39 */
  assign n1800 = n1799 ? first_byte : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:62 */
  assign n1802 = din_input[23:16]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:20 */
  assign n1803 = sel_din[2]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:85 */
  assign n1804 = n1803 ? n1802 : n1805;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:48 */
  assign n1805 = byte_pad_wire[23:16]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:60 */
  assign n1806 = sel_pad_location[1]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:37:39 */
  assign n1807 = n1806 ? first_byte : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:62 */
  assign n1809 = din_input[15:8]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:20 */
  assign n1810 = sel_din[1]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:38:85 */
  assign n1811 = n1810 ? n1809 : n1812;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:39:48 */
  assign n1812 = byte_pad_wire[15:8]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:42:57 */
  assign n1813 = sel_pad_location[0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:42:39 */
  assign n1814 = {last_word, n1813};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:43:41 */
  assign n1817 = mode == 2'b11;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:43:54 */
  assign n1819 = mode == 2'b10;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:43:47 */
  assign n1820 = n1817 | n1819;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:43:30 */
  assign n1821 = n1820 ? 8'b00011111 : 8'b00000110;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:44:41 */
  assign n1825 = mode == 2'b11;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:44:54 */
  assign n1827 = mode == 2'b10;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:44:47 */
  assign n1828 = n1825 | n1827;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:44:30 */
  assign n1829 = n1828 ? 8'b10011111 : 8'b10000110;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:46:46 */
  assign n1833 = sel_last_mux == 2'b00;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:47:66 */
  assign n1835 = sel_last_mux == 2'b01;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:48:66 */
  assign n1838 = sel_last_mux == 2'b10;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:45:9 */
  assign n1839 = {n1838, n1835, n1833};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:45:9 */
  always @*
    case (n1839)
      3'b100: n1840 = 8'b10000000;
      3'b010: n1840 = first_byte;
      3'b001: n1840 = 8'b00000000;
      default: n1840 = first_last_byte;
    endcase
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:50:42 */
  assign n1841 = din_input[7:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:50:67 */
  assign n1842 = sel_din[0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:50:55 */
  assign n1843 = n1842 ? n1841 : n1844;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:50:93 */
  assign n1844 = byte_pad_wire[7:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:23 */
  assign n1845 = dout_input[63:56]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:59 */
  assign n1846 = sel_dout[7]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:46 */
  assign n1847 = n1846 ? n1845 : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:23 */
  assign n1849 = dout_input[55:48]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:59 */
  assign n1850 = sel_dout[6]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:46 */
  assign n1851 = n1850 ? n1849 : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:23 */
  assign n1853 = dout_input[47:40]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:59 */
  assign n1854 = sel_dout[5]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:46 */
  assign n1855 = n1854 ? n1853 : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:23 */
  assign n1857 = dout_input[39:32]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:59 */
  assign n1858 = sel_dout[4]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:46 */
  assign n1859 = n1858 ? n1857 : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:23 */
  assign n1861 = dout_input[31:24]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:59 */
  assign n1862 = sel_dout[3]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:46 */
  assign n1863 = n1862 ? n1861 : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:23 */
  assign n1865 = dout_input[23:16]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:59 */
  assign n1866 = sel_dout[2]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:46 */
  assign n1867 = n1866 ? n1865 : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:23 */
  assign n1869 = dout_input[15:8]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:59 */
  assign n1870 = sel_dout[1]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:46 */
  assign n1871 = n1870 ? n1869 : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:23 */
  assign n1873 = dout_input[7:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:59 */
  assign n1874 = sel_dout[0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:55:46 */
  assign n1875 = n1874 ? n1873 : 8'b00000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:57:39 */
  assign n1877 = last_out_word ? dout_output_padded : dout_input;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:30:16 */
  assign n1878 = {n1765, n1772, n1779, n1786, n1793, n1800, n1807, n1840};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:33:12 */
  assign n1879 = {n1847, n1851, n1855, n1859, n1863, n1867, n1871, n1875};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_bytepad.vhd:16:12 */
  assign n1880 = {n1769, n1776, n1783, n1790, n1797, n1804, n1811, n1843};
endmodule

module sr_reg_Bstruct_c4ea21bb365bbeeaf5f2c654883e56d11e43c44e
  (input  rst,
   input  clk,
   input  set,
   input  clr,
   output \output );
  wire output_s;
  wire n1754;
  wire n1755;
  wire n1756;
  wire n1758;
  reg n1761;
  assign \output  = output_s; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:24:16 */
  assign output_s = n1761; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:32:54 */
  assign n1754 = ~clr;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:32:63 */
  assign n1755 = n1754 & output_s;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:32:49 */
  assign n1756 = set | n1755;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:29:25 */
  assign n1758 = rst ? 1'b0 : n1756;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sr_reg.vhd:28:17 */
  always @(posedge clk)
    n1761 <= n1758;
endmodule

module sha3_fsm3_Bbeh_64
  (input  clk,
   input  rst,
   output eo,
   input  output_write,
   output output_write_clr,
   output output_busy_clr,
   input  dst_ready,
   output dst_write,
   input  [10:0] output_size,
   output last_out_word);
  wire [10:0] hseg;
  wire [31:0] outsize_div_w;
  wire ek;
  wire lk;
  wire zkfin;
  wire [10:0] kc;
  wire cstate_fsm3;
  wire nstate;
  wire [30:0] n1643;
  wire [31:0] n1648;
  wire [5:0] n1649;
  wire [31:0] n1650;
  wire n1652;
  wire [31:0] n1653;
  wire [31:0] n1655;
  wire [31:0] n1657;
  wire [30:0] n1658;
  wire [31:0] n1659;
  wire [31:0] n1661;
  wire [30:0] n1662;
  wire [30:0] n1663;
  wire [31:0] n1664;
  wire [10:0] n1665;
  localparam n1666 = 1'b0;
  localparam [10:0] n1667 = 11'b00000000000;
  wire [10:0] kcount_gen_n1668;
  wire [10:0] n1673;
  wire n1674;
  wire n1675;
  wire n1680;
  wire n1686;
  wire n1688;
  wire n1689;
  wire n1690;
  wire n1693;
  wire n1695;
  wire [1:0] n1696;
  reg n1698;
  wire n1702;
  wire n1703;
  wire n1704;
  wire n1705;
  wire n1709;
  wire n1710;
  wire n1711;
  wire n1715;
  wire n1716;
  wire n1717;
  wire n1718;
  wire n1719;
  wire n1723;
  wire n1724;
  wire n1725;
  wire n1726;
  wire n1727;
  wire n1728;
  wire n1732;
  wire n1733;
  wire n1734;
  wire n1735;
  wire n1737;
  wire n1738;
  wire n1739;
  wire n1740;
  wire n1744;
  wire n1745;
  wire n1746;
  wire n1747;
  reg n1750;
  wire [10:0] n2882;
  assign eo = n1747; //(module output)
  assign output_write_clr = n1711; //(module output)
  assign output_busy_clr = n1719; //(module output)
  assign dst_write = n1705; //(module output)
  assign last_out_word = zkfin; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:42:12 */
  assign hseg = n1665; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:43:12 */
  assign outsize_div_w = n1664; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:50:16 */
  assign ek = n1728; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:50:20 */
  assign lk = n1740; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:50:24 */
  assign zkfin = n1675; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:53:12 */
  assign kc = kcount_gen_n1668; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:57:16 */
  assign cstate_fsm3 = n1750; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:57:29 */
  assign nstate = n1698; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:60:30 */
  assign n1643 = {20'b0, output_size};  // uext
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:73:14 */
  assign n1648 = {1'b0, n1643};  // uext
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:73:14 */
  assign n1649 = n1648[5:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:73:14 */
  assign n1650 = {26'b0, n1649};  // uext
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:73:21 */
  assign n1652 = $signed(n1650) > $signed(32'b00000000000000000000000000000000);
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:74:23 */
  assign n1653 = {1'b0, n1643};  // uext
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:74:23 */
  assign n1655 = $signed(n1653) / $signed(32'b00000000000000000000000001000000); // sdiv
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:74:28 */
  assign n1657 = n1655 + 32'b00000000000000000000000000000001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:74:13 */
  assign n1658 = n1657[30:0];  // trunc
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:76:23 */
  assign n1659 = {1'b0, n1643};  // uext
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:76:23 */
  assign n1661 = $signed(n1659) / $signed(32'b00000000000000000000000001000000); // sdiv
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:76:13 */
  assign n1662 = n1661[30:0];  // trunc
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_pkg.vhd:73:9 */
  assign n1663 = n1652 ? n1658 : n1662;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:60:22 */
  assign n1664 = {1'b0, n1663};  // uext
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:64:13 */
  assign n1665 = outsize_div_w[10:0];  // trunc
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:66:146 */
  assign kcount_gen_n1668 = n2882; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:66:9 */
  countern_Bcountern_11_1_1 kcount_gen (
    .clk(clk),
    .rst(1'b0),
    .load(lk),
    .en(ek),
    .\input (11'b00000000000),
    .\output (n2882));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:68:32 */
  assign n1673 = hseg - 11'b00000000001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:68:26 */
  assign n1674 = kc == n1673;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:68:18 */
  assign n1675 = n1674 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:74:25 */
  assign n1680 = rst ? 1'b0 : nstate;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:86:33 */
  assign n1686 = output_write ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:85:25 */
  assign n1688 = cstate_fsm3 == 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:92:48 */
  assign n1689 = ~dst_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:92:54 */
  assign n1690 = zkfin & n1689;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:92:33 */
  assign n1693 = n1690 ? 1'b0 : 1'b1;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:91:25 */
  assign n1695 = cstate_fsm3 == 1'b1;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:84:17 */
  assign n1696 = {n1695, n1688};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:84:17 */
  always @*
    case (n1696)
      2'b10: n1698 = n1693;
      2'b01: n1698 = n1686;
      default: n1698 = 1'bX;
    endcase
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:100:44 */
  assign n1702 = cstate_fsm3 == 1'b1;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:100:71 */
  assign n1703 = ~dst_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:100:57 */
  assign n1704 = n1703 & n1702;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:100:26 */
  assign n1705 = n1704 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:101:51 */
  assign n1709 = cstate_fsm3 == 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:101:58 */
  assign n1710 = output_write & n1709;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:101:33 */
  assign n1711 = n1710 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:102:51 */
  assign n1715 = cstate_fsm3 == 1'b1;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:102:78 */
  assign n1716 = ~dst_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:102:64 */
  assign n1717 = n1716 & n1715;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:102:84 */
  assign n1718 = zkfin & n1717;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:102:33 */
  assign n1719 = n1718 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:103:37 */
  assign n1723 = cstate_fsm3 == 1'b1;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:103:64 */
  assign n1724 = ~dst_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:103:50 */
  assign n1725 = n1724 & n1723;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:103:80 */
  assign n1726 = ~zkfin;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:103:70 */
  assign n1727 = n1726 & n1725;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:103:19 */
  assign n1728 = n1727 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:104:38 */
  assign n1732 = cstate_fsm3 == 1'b1;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:104:65 */
  assign n1733 = ~dst_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:104:51 */
  assign n1734 = n1733 & n1732;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:104:71 */
  assign n1735 = zkfin & n1734;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:104:105 */
  assign n1737 = cstate_fsm3 == 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:104:112 */
  assign n1738 = output_write & n1737;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:104:89 */
  assign n1739 = n1735 | n1738;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:104:19 */
  assign n1740 = n1739 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:105:37 */
  assign n1744 = cstate_fsm3 == 1'b1;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:105:64 */
  assign n1745 = ~dst_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:105:50 */
  assign n1746 = n1745 & n1744;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:105:19 */
  assign n1747 = n1746 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_fsm3.vhd:73:17 */
  always @(posedge clk)
    n1750 <= n1680;
endmodule

module keccak_fsm2_Bbeh
  (input  clk,
   input  rst,
   output wr_state,
   output sel_xor,
   output sel_final,
   output ld_rdctr,
   output en_rdctr,
   output block_ready_clr,
   output msg_end_clr,
   input  block_ready,
   input  msg_end,
   output lo,
   output output_write_set,
   output output_busy_set,
   input  output_busy,
   input  [31:0] d,
   output [10:0] output_size,
   input  [1:0] mode,
   output [1:0] mode_ctrl);
  wire [3:0] cstate;
  wire [3:0] nstate;
  wire [4:0] pc;
  wire ziroundnr;
  wire li;
  wire ei;
  wire output_data_s;
  wire sel_xor_set;
  wire sel_xor_clr;
  wire sel_xor_wire;
  wire [31:0] cnt_output_size_next;
  wire [31:0] cnt_output_size_r;
  wire [10:0] output_size_next;
  wire [10:0] output_size_r;
  wire [31:0] b;
  wire hashing_started_r;
  wire hashing_started_next;
  wire [1:0] mode_r;
  wire [1:0] mode_next;
  wire n1167;
  wire [31:0] n1168;
  localparam [4:0] n1170 = 5'b00000;
  wire [4:0] proc_counter_gen_n1171;
  wire n1176;
  wire n1177;
  wire [3:0] n1182;
  wire [31:0] n1184;
  wire [10:0] n1186;
  wire n1188;
  wire [1:0] n1190;
  wire n1199;
  wire n1200;
  wire n1201;
  wire n1202;
  wire [31:0] n1203;
  wire n1205;
  wire [1:0] n1206;
  wire n1207;
  wire n1208;
  wire [31:0] n1209;
  wire n1211;
  wire [1:0] n1212;
  wire [3:0] n1215;
  wire n1216;
  wire n1217;
  wire n1218;
  wire [3:0] n1220;
  wire [31:0] n1221;
  wire n1222;
  wire [1:0] n1223;
  wire n1225;
  wire n1226;
  wire n1227;
  wire n1228;
  wire n1229;
  wire n1230;
  wire n1231;
  wire [3:0] n1234;
  wire [3:0] n1236;
  wire n1238;
  wire n1239;
  wire n1241;
  wire n1243;
  wire n1244;
  wire [3:0] n1247;
  wire [3:0] n1249;
  wire [3:0] n1251;
  wire n1253;
  wire n1255;
  wire n1257;
  wire [10:0] n1259;
  wire [10:0] n1261;
  wire n1262;
  wire [3:0] n1265;
  wire [31:0] n1266;
  wire n1268;
  wire [1:0] n1269;
  wire [3:0] n1271;
  wire [31:0] n1272;
  wire n1273;
  wire [1:0] n1274;
  wire [3:0] n1276;
  wire [31:0] n1277;
  wire n1279;
  wire [1:0] n1280;
  wire n1282;
  wire n1283;
  wire [3:0] n1286;
  wire [31:0] n1287;
  wire n1289;
  wire [1:0] n1290;
  wire [3:0] n1292;
  wire [31:0] n1293;
  wire n1295;
  wire [1:0] n1296;
  wire [3:0] n1298;
  wire [31:0] n1299;
  wire n1300;
  wire [1:0] n1301;
  wire n1303;
  wire n1304;
  wire [10:0] n1305;
  wire [10:0] n1306;
  wire n1307;
  wire [3:0] n1310;
  wire [31:0] n1311;
  wire n1313;
  wire [1:0] n1314;
  wire [3:0] n1316;
  wire [31:0] n1317;
  wire n1318;
  wire [1:0] n1319;
  wire [3:0] n1321;
  wire [31:0] n1322;
  wire n1324;
  wire [1:0] n1325;
  wire [3:0] n1327;
  wire [31:0] n1328;
  wire [10:0] n1329;
  wire n1330;
  wire [1:0] n1331;
  wire n1333;
  wire n1334;
  wire [3:0] n1337;
  wire [31:0] n1338;
  wire n1340;
  wire [1:0] n1341;
  wire [3:0] n1343;
  wire [31:0] n1344;
  wire n1346;
  wire [1:0] n1347;
  wire [3:0] n1349;
  wire [31:0] n1350;
  wire n1351;
  wire [1:0] n1352;
  wire n1354;
  wire n1355;
  wire [31:0] n1356;
  wire [3:0] n1359;
  wire [31:0] n1360;
  wire [3:0] n1362;
  wire [31:0] n1363;
  wire [3:0] n1365;
  wire [31:0] n1366;
  wire n1368;
  wire n1369;
  wire [31:0] n1370;
  wire [3:0] n1372;
  wire [31:0] n1373;
  wire n1375;
  wire [9:0] n1376;
  reg [3:0] n1379;
  reg [31:0] n1381;
  reg [10:0] n1383;
  reg n1385;
  reg [1:0] n1387;
  wire n1391;
  wire n1393;
  wire n1394;
  wire n1395;
  wire n1396;
  wire n1398;
  wire n1400;
  wire n1401;
  wire n1402;
  wire n1403;
  wire n1404;
  wire n1405;
  wire n1409;
  wire n1411;
  wire n1412;
  wire n1414;
  wire n1415;
  wire n1416;
  wire n1420;
  wire n1422;
  wire n1423;
  wire n1425;
  wire n1426;
  wire n1427;
  wire n1431;
  wire n1433;
  wire n1434;
  wire n1435;
  wire n1436;
  wire sf_gen_n1438;
  wire n1443;
  wire n1445;
  wire n1446;
  wire n1447;
  wire n1449;
  wire n1450;
  wire n1451;
  wire n1452;
  wire n1456;
  wire n1457;
  wire n1459;
  wire n1461;
  wire n1462;
  wire n1463;
  wire n1464;
  wire n1465;
  wire n1466;
  wire n1468;
  wire n1470;
  wire n1471;
  wire n1472;
  wire n1473;
  wire n1474;
  wire n1475;
  wire n1476;
  wire n1477;
  wire n1481;
  wire n1482;
  wire n1484;
  wire n1485;
  wire n1486;
  wire n1488;
  wire n1489;
  wire n1490;
  wire n1491;
  wire n1492;
  wire n1493;
  wire n1494;
  wire n1496;
  wire n1497;
  wire n1498;
  wire n1499;
  wire n1500;
  wire n1502;
  wire n1504;
  wire n1505;
  wire n1506;
  wire n1507;
  wire n1508;
  wire n1509;
  wire n1510;
  wire n1514;
  wire n1515;
  wire n1517;
  wire n1518;
  wire n1519;
  wire n1520;
  wire n1522;
  wire n1523;
  wire n1524;
  wire n1526;
  wire n1527;
  wire n1528;
  wire n1529;
  wire n1533;
  wire n1535;
  wire n1536;
  wire n1538;
  wire n1539;
  wire n1540;
  wire n1541;
  wire n1542;
  wire n1546;
  wire n1547;
  wire n1549;
  wire n1550;
  wire n1551;
  wire n1552;
  wire n1554;
  wire n1555;
  wire n1556;
  wire n1557;
  wire n1558;
  wire n1559;
  wire n1560;
  wire n1562;
  wire n1563;
  wire n1565;
  wire n1566;
  wire n1567;
  wire n1568;
  wire n1569;
  wire n1570;
  wire n1571;
  wire n1573;
  wire n1574;
  wire n1575;
  wire n1576;
  wire n1577;
  wire n1579;
  wire n1581;
  wire n1582;
  wire n1583;
  wire n1584;
  wire n1585;
  wire n1586;
  wire n1588;
  wire n1589;
  wire n1590;
  wire n1594;
  wire n1595;
  wire n1596;
  wire n1598;
  wire n1599;
  wire n1600;
  wire n1601;
  wire n1602;
  wire n1604;
  wire n1605;
  wire n1606;
  wire n1607;
  wire n1608;
  wire n1609;
  wire n1611;
  wire n1612;
  wire n1613;
  wire n1614;
  wire n1615;
  wire n1616;
  wire n1617;
  wire n1618;
  wire n1620;
  wire n1622;
  wire n1623;
  wire n1624;
  wire n1625;
  wire n1626;
  wire n1627;
  wire n1628;
  wire n1629;
  reg [3:0] n1631;
  reg [31:0] n1632;
  reg [10:0] n1633;
  reg n1634;
  reg [1:0] n1635;
  wire [4:0] n2880;
  wire n2881;
  assign wr_state = n1590; //(module output)
  assign sel_xor = sel_xor_wire; //(module output)
  assign sel_final = n1510; //(module output)
  assign ld_rdctr = n1529; //(module output)
  assign en_rdctr = n1542; //(module output)
  assign block_ready_clr = n1416; //(module output)
  assign msg_end_clr = n1629; //(module output)
  assign lo = output_data_s; //(module output)
  assign output_write_set = output_data_s; //(module output)
  assign output_busy_set = output_data_s; //(module output)
  assign output_size = output_size_r; //(module output)
  assign mode_ctrl = mode_r; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:53:16 */
  assign cstate = n1631; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:53:24 */
  assign nstate = n1379; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:55:16 */
  assign pc = proc_counter_gen_n1171; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:56:16 */
  assign ziroundnr = n1177; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:56:27 */
  assign li = n1436; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:56:31 */
  assign ei = n1427; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:57:16 */
  assign output_data_s = n1405; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:58:16 */
  assign sel_xor_set = n1452; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:58:29 */
  assign sel_xor_clr = n1477; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:58:42 */
  assign sel_xor_wire = sf_gen_n1438; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:60:12 */
  assign cnt_output_size_next = n1381; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:60:34 */
  assign cnt_output_size_r = n1632; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:61:12 */
  assign output_size_next = n1383; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:61:30 */
  assign output_size_r = n1633; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:63:12 */
  assign b = n1168; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:64:12 */
  assign hashing_started_r = n1634; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:64:31 */
  assign hashing_started_next = n1385; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:65:12 */
  assign mode_r = n1635; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:65:20 */
  assign mode_next = n1387; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:67:40 */
  assign n1167 = mode_r == 2'b11;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:67:28 */
  assign n1168 = n1167 ? 32'b00000000000000000000010001000000 : 32'b00000000000000000000010101000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:76:19 */
  assign proc_counter_gen_n1171 = n2880; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:69:9 */
  countern_Bcountern_5_1_1 proc_counter_gen (
    .clk(clk),
    .rst(rst),
    .load(li),
    .en(ei),
    .\input (5'b00000),
    .\output (n2880));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:78:34 */
  assign n1176 = pc == 5'b10111;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:78:26 */
  assign n1177 = n1176 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:84:25 */
  assign n1182 = rst ? 4'b0000 : nstate;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:84:25 */
  assign n1184 = rst ? 32'b00000000000000000000000000000000 : cnt_output_size_next;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:84:25 */
  assign n1186 = rst ? 11'b00000000000 : output_size_next;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:84:25 */
  assign n1188 = rst ? 1'b0 : hashing_started_next;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:84:25 */
  assign n1190 = rst ? 2'b00 : mode_next;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:110:25 */
  assign n1199 = cstate == 4'b0000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:113:68 */
  assign n1200 = ~msg_end;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:113:56 */
  assign n1201 = n1200 & block_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:115:43 */
  assign n1202 = ~hashing_started_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:115:21 */
  assign n1203 = n1202 ? d : cnt_output_size_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:115:21 */
  assign n1205 = n1202 ? 1'b1 : hashing_started_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:115:21 */
  assign n1206 = n1202 ? mode : mode_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:120:58 */
  assign n1207 = msg_end & block_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:122:43 */
  assign n1208 = ~hashing_started_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:120:33 */
  assign n1209 = n1216 ? d : cnt_output_size_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:120:33 */
  assign n1211 = n1217 ? 1'b1 : hashing_started_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:120:33 */
  assign n1212 = n1218 ? mode : mode_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:120:33 */
  assign n1215 = n1207 ? 4'b0011 : 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:120:33 */
  assign n1216 = n1208 & n1207;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:120:33 */
  assign n1217 = n1208 & n1207;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:120:33 */
  assign n1218 = n1208 & n1207;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:113:33 */
  assign n1220 = n1201 ? 4'b0010 : n1215;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:113:33 */
  assign n1221 = n1201 ? n1203 : n1209;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:113:33 */
  assign n1222 = n1201 ? n1205 : n1211;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:113:33 */
  assign n1223 = n1201 ? n1206 : n1212;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:112:25 */
  assign n1225 = cstate == 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:132:48 */
  assign n1226 = ~ziroundnr;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:132:88 */
  assign n1227 = ~msg_end;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:132:76 */
  assign n1228 = n1227 & ziroundnr;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:132:94 */
  assign n1229 = block_ready & n1228;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:132:56 */
  assign n1230 = n1226 | n1229;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:135:56 */
  assign n1231 = msg_end & ziroundnr;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:135:33 */
  assign n1234 = n1231 ? 4'b0011 : 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:132:33 */
  assign n1236 = n1230 ? 4'b0010 : n1234;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:131:25 */
  assign n1238 = cstate == 4'b0010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:142:48 */
  assign n1239 = ~ziroundnr;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:145:33 */
  assign n1241 = mode_r == 2'b00;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:145:50 */
  assign n1243 = mode_r == 2'b01;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:145:40 */
  assign n1244 = n1241 | n1243;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:145:21 */
  assign n1247 = n1244 ? 4'b0101 : 4'b0100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:144:33 */
  assign n1249 = ziroundnr ? n1247 : 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:142:33 */
  assign n1251 = n1239 ? 4'b0011 : n1249;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:141:25 */
  assign n1253 = cstate == 4'b0011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:155:28 */
  assign n1255 = mode_r == 2'b00;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:158:31 */
  assign n1257 = mode_r == 2'b01;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:158:17 */
  assign n1259 = n1257 ? 11'b01000000000 : output_size_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:155:17 */
  assign n1261 = n1255 ? 11'b00100000000 : n1259;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:166:42 */
  assign n1262 = msg_end & block_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:170:17 */
  assign n1265 = block_ready ? 4'b0010 : 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:170:17 */
  assign n1266 = block_ready ? d : cnt_output_size_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:170:17 */
  assign n1268 = block_ready ? hashing_started_r : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:170:17 */
  assign n1269 = block_ready ? mode : mode_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:166:17 */
  assign n1271 = n1262 ? 4'b0011 : n1265;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:166:17 */
  assign n1272 = n1262 ? d : n1266;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:166:17 */
  assign n1273 = n1262 ? hashing_started_r : n1268;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:166:17 */
  assign n1274 = n1262 ? mode : n1269;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:163:17 */
  assign n1276 = output_busy ? 4'b0111 : n1271;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:163:17 */
  assign n1277 = output_busy ? cnt_output_size_r : n1272;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:163:17 */
  assign n1279 = output_busy ? 1'b0 : n1273;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:163:17 */
  assign n1280 = output_busy ? mode_r : n1274;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:154:13 */
  assign n1282 = cstate == 4'b0101;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:182:58 */
  assign n1283 = msg_end & block_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:187:33 */
  assign n1286 = block_ready ? 4'b0010 : 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:187:33 */
  assign n1287 = block_ready ? d : cnt_output_size_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:187:33 */
  assign n1289 = block_ready ? 1'b1 : hashing_started_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:187:33 */
  assign n1290 = block_ready ? mode : mode_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:182:33 */
  assign n1292 = n1283 ? 4'b0011 : n1286;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:182:33 */
  assign n1293 = n1283 ? d : n1287;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:182:33 */
  assign n1295 = n1283 ? 1'b1 : n1289;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:182:33 */
  assign n1296 = n1283 ? mode : n1290;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:180:17 */
  assign n1298 = output_busy ? 4'b0111 : n1292;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:180:17 */
  assign n1299 = output_busy ? cnt_output_size_r : n1293;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:180:17 */
  assign n1300 = output_busy ? hashing_started_r : n1295;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:180:17 */
  assign n1301 = output_busy ? mode_r : n1296;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:179:13 */
  assign n1303 = cstate == 4'b0111;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:197:39 */
  assign n1304 = $unsigned(cnt_output_size_r) > $unsigned(b);
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:200:25 */
  assign n1305 = b[10:0];  // trunc
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:202:58 */
  assign n1306 = cnt_output_size_r[10:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:206:58 */
  assign n1307 = msg_end & block_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:210:33 */
  assign n1310 = block_ready ? 4'b0010 : 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:210:33 */
  assign n1311 = block_ready ? d : cnt_output_size_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:210:33 */
  assign n1313 = block_ready ? hashing_started_r : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:210:33 */
  assign n1314 = block_ready ? mode : mode_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:206:33 */
  assign n1316 = n1307 ? 4'b0011 : n1310;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:206:33 */
  assign n1317 = n1307 ? d : n1311;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:206:33 */
  assign n1318 = n1307 ? hashing_started_r : n1313;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:206:33 */
  assign n1319 = n1307 ? mode : n1314;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:203:33 */
  assign n1321 = output_busy ? 4'b0110 : n1316;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:203:33 */
  assign n1322 = output_busy ? cnt_output_size_r : n1317;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:203:33 */
  assign n1324 = output_busy ? 1'b0 : n1318;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:203:33 */
  assign n1325 = output_busy ? mode_r : n1319;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:197:17 */
  assign n1327 = n1304 ? 4'b1000 : n1321;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:197:17 */
  assign n1328 = n1304 ? cnt_output_size_r : n1322;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:197:17 */
  assign n1329 = n1304 ? n1305 : n1306;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:197:17 */
  assign n1330 = n1304 ? hashing_started_r : n1324;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:197:17 */
  assign n1331 = n1304 ? mode_r : n1325;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:196:25 */
  assign n1333 = cstate == 4'b0100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:223:58 */
  assign n1334 = msg_end & block_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:228:33 */
  assign n1337 = block_ready ? 4'b0010 : 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:228:33 */
  assign n1338 = block_ready ? d : cnt_output_size_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:228:33 */
  assign n1340 = block_ready ? 1'b1 : hashing_started_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:228:33 */
  assign n1341 = block_ready ? mode : mode_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:223:33 */
  assign n1343 = n1334 ? 4'b0011 : n1337;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:223:33 */
  assign n1344 = n1334 ? d : n1338;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:223:33 */
  assign n1346 = n1334 ? 1'b1 : n1340;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:223:33 */
  assign n1347 = n1334 ? mode : n1341;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:221:33 */
  assign n1349 = output_busy ? 4'b0110 : n1343;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:221:33 */
  assign n1350 = output_busy ? cnt_output_size_r : n1344;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:221:33 */
  assign n1351 = output_busy ? hashing_started_r : n1346;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:221:33 */
  assign n1352 = output_busy ? mode_r : n1347;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:220:25 */
  assign n1354 = cstate == 4'b0110;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:238:32 */
  assign n1355 = ~ziroundnr;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:244:66 */
  assign n1356 = cnt_output_size_r - b;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:241:21 */
  assign n1359 = output_busy ? 4'b1001 : 4'b0100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:241:21 */
  assign n1360 = output_busy ? cnt_output_size_r : n1356;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:240:17 */
  assign n1362 = ziroundnr ? n1359 : 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:240:17 */
  assign n1363 = ziroundnr ? n1360 : cnt_output_size_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:238:17 */
  assign n1365 = n1355 ? 4'b1000 : n1362;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:238:17 */
  assign n1366 = n1355 ? cnt_output_size_r : n1363;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:237:13 */
  assign n1368 = cstate == 4'b1000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:252:33 */
  assign n1369 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:253:62 */
  assign n1370 = cnt_output_size_r - b;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:252:17 */
  assign n1372 = n1369 ? 4'b0100 : cstate;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:252:17 */
  assign n1373 = n1369 ? n1370 : cnt_output_size_r;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:251:13 */
  assign n1375 = cstate == 4'b1001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:109:9 */
  assign n1376 = {n1375, n1368, n1354, n1333, n1303, n1282, n1253, n1238, n1225, n1199};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:109:9 */
  always @*
    case (n1376)
      10'b1000000000: n1379 = n1372;
      10'b0100000000: n1379 = n1365;
      10'b0010000000: n1379 = n1349;
      10'b0001000000: n1379 = n1327;
      10'b0000100000: n1379 = n1298;
      10'b0000010000: n1379 = n1276;
      10'b0000001000: n1379 = n1251;
      10'b0000000100: n1379 = n1236;
      10'b0000000010: n1379 = n1220;
      10'b0000000001: n1379 = 4'b0001;
      default: n1379 = 4'bX;
    endcase
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:109:9 */
  always @*
    case (n1376)
      10'b1000000000: n1381 = n1373;
      10'b0100000000: n1381 = n1366;
      10'b0010000000: n1381 = n1350;
      10'b0001000000: n1381 = n1328;
      10'b0000100000: n1381 = n1299;
      10'b0000010000: n1381 = n1277;
      10'b0000001000: n1381 = cnt_output_size_r;
      10'b0000000100: n1381 = cnt_output_size_r;
      10'b0000000010: n1381 = n1221;
      10'b0000000001: n1381 = cnt_output_size_r;
      default: n1381 = 32'bX;
    endcase
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:109:9 */
  always @*
    case (n1376)
      10'b1000000000: n1383 = output_size_r;
      10'b0100000000: n1383 = output_size_r;
      10'b0010000000: n1383 = output_size_r;
      10'b0001000000: n1383 = n1329;
      10'b0000100000: n1383 = output_size_r;
      10'b0000010000: n1383 = n1261;
      10'b0000001000: n1383 = output_size_r;
      10'b0000000100: n1383 = output_size_r;
      10'b0000000010: n1383 = output_size_r;
      10'b0000000001: n1383 = output_size_r;
      default: n1383 = 11'bX;
    endcase
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:109:9 */
  always @*
    case (n1376)
      10'b1000000000: n1385 = hashing_started_r;
      10'b0100000000: n1385 = hashing_started_r;
      10'b0010000000: n1385 = n1351;
      10'b0001000000: n1385 = n1330;
      10'b0000100000: n1385 = n1300;
      10'b0000010000: n1385 = n1279;
      10'b0000001000: n1385 = hashing_started_r;
      10'b0000000100: n1385 = hashing_started_r;
      10'b0000000010: n1385 = n1222;
      10'b0000000001: n1385 = hashing_started_r;
      default: n1385 = 1'bX;
    endcase
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:109:9 */
  always @*
    case (n1376)
      10'b1000000000: n1387 = mode_r;
      10'b0100000000: n1387 = mode_r;
      10'b0010000000: n1387 = n1352;
      10'b0001000000: n1387 = n1331;
      10'b0000100000: n1387 = n1301;
      10'b0000010000: n1387 = n1280;
      10'b0000001000: n1387 = mode_r;
      10'b0000000100: n1387 = mode_r;
      10'b0000000010: n1387 = n1223;
      10'b0000000001: n1387 = mode_r;
      default: n1387 = 2'bX;
    endcase
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:264:46 */
  assign n1391 = cstate == 4'b0101;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:265:17 */
  assign n1393 = cstate == 4'b0100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:264:65 */
  assign n1394 = n1391 | n1393;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:265:56 */
  assign n1395 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:265:40 */
  assign n1396 = n1395 & n1394;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:266:27 */
  assign n1398 = cstate == 4'b0111;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:266:55 */
  assign n1400 = cstate == 4'b0110;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:266:45 */
  assign n1401 = n1398 | n1400;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:267:21 */
  assign n1402 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:266:77 */
  assign n1403 = n1402 & n1401;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:265:63 */
  assign n1404 = n1396 | n1403;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:264:30 */
  assign n1405 = n1404 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:273:55 */
  assign n1409 = cstate == 4'b0010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:274:16 */
  assign n1411 = cstate == 4'b0011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:273:71 */
  assign n1412 = n1409 | n1411;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:274:45 */
  assign n1414 = pc == 5'b00100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:274:38 */
  assign n1415 = n1414 & n1412;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:273:41 */
  assign n1416 = n1415 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:276:32 */
  assign n1420 = cstate == 4'b0010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:276:58 */
  assign n1422 = cstate == 4'b0011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:276:48 */
  assign n1423 = n1420 | n1422;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:277:16 */
  assign n1425 = cstate == 4'b1000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:276:79 */
  assign n1426 = n1423 | n1425;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:276:19 */
  assign n1427 = n1426 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:279:34 */
  assign n1431 = cstate == 4'b0000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:279:55 */
  assign n1433 = cstate == 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:279:43 */
  assign n1434 = n1431 | n1433;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:279:63 */
  assign n1435 = n1434 | ziroundnr;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:279:20 */
  assign n1436 = n1435 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:290:19 */
  assign sf_gen_n1438 = n2881; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:283:9 */
  sr_reg_Bstruct_9842926af7ca0a8cca12604f945414f07b01e13d sf_gen (
    .rst(rst),
    .clk(clk),
    .set(sel_xor_set),
    .clr(sel_xor_clr),
    .\output (n2881));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:292:41 */
  assign n1443 = cstate == 4'b0000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:292:61 */
  assign n1445 = cstate == 4'b0011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:292:82 */
  assign n1446 = ziroundnr & n1445;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:292:50 */
  assign n1447 = n1443 | n1446;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:292:114 */
  assign n1449 = cstate == 4'b1000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:292:130 */
  assign n1450 = ziroundnr & n1449;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:292:103 */
  assign n1451 = n1447 | n1450;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:292:28 */
  assign n1452 = n1451 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:294:58 */
  assign n1456 = cstate == 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:294:65 */
  assign n1457 = block_ready & n1456;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:295:59 */
  assign n1459 = cstate == 4'b0101;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:295:88 */
  assign n1461 = cstate == 4'b0100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:295:78 */
  assign n1462 = n1459 | n1461;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:295:127 */
  assign n1463 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:295:111 */
  assign n1464 = n1463 & n1462;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:295:133 */
  assign n1465 = block_ready & n1464;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:294:88 */
  assign n1466 = n1457 | n1465;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:296:60 */
  assign n1468 = cstate == 4'b0111;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:296:88 */
  assign n1470 = cstate == 4'b0110;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:296:78 */
  assign n1471 = n1468 | n1470;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:296:110 */
  assign n1472 = block_ready & n1471;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:296:148 */
  assign n1473 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:296:132 */
  assign n1474 = n1473 & n1472;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:295:156 */
  assign n1475 = n1466 | n1474;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:293:52 */
  assign n1476 = n1475 & sel_xor_wire;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:293:28 */
  assign n1477 = n1476 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:300:40 */
  assign n1481 = cstate == 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:300:47 */
  assign n1482 = block_ready & n1481;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:301:65 */
  assign n1484 = cstate == 4'b0010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:301:81 */
  assign n1485 = ziroundnr & n1484;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:300:70 */
  assign n1486 = n1482 | n1485;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:302:37 */
  assign n1488 = cstate == 4'b0100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:302:74 */
  assign n1489 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:302:58 */
  assign n1490 = n1489 & n1488;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:302:80 */
  assign n1491 = block_ready & n1490;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:302:124 */
  assign n1492 = $unsigned(cnt_output_size_r) <= $unsigned(b);
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:302:102 */
  assign n1493 = n1492 & n1491;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:301:102 */
  assign n1494 = n1486 | n1493;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:303:65 */
  assign n1496 = cstate == 4'b0101;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:303:100 */
  assign n1497 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:303:84 */
  assign n1498 = n1497 & n1496;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:303:106 */
  assign n1499 = block_ready & n1498;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:302:130 */
  assign n1500 = n1494 | n1499;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:304:59 */
  assign n1502 = cstate == 4'b0111;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:304:87 */
  assign n1504 = cstate == 4'b0110;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:304:77 */
  assign n1505 = n1502 | n1504;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:304:125 */
  assign n1506 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:304:109 */
  assign n1507 = n1506 & n1505;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:304:131 */
  assign n1508 = block_ready & n1507;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:303:129 */
  assign n1509 = n1500 | n1508;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:300:26 */
  assign n1510 = n1509 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:306:38 */
  assign n1514 = cstate == 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:306:45 */
  assign n1515 = block_ready & n1514;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:306:80 */
  assign n1517 = cstate == 4'b0010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:306:97 */
  assign n1518 = ziroundnr & n1517;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:306:117 */
  assign n1519 = block_ready & n1518;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:306:68 */
  assign n1520 = n1515 | n1519;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:307:57 */
  assign n1522 = cstate == 4'b0011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:307:78 */
  assign n1523 = ziroundnr & n1522;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:306:140 */
  assign n1524 = n1520 | n1523;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:308:30 */
  assign n1526 = cstate == 4'b1000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:308:46 */
  assign n1527 = ziroundnr & n1526;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:307:99 */
  assign n1528 = n1524 | n1527;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:306:25 */
  assign n1529 = n1528 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:309:39 */
  assign n1533 = cstate == 4'b0010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:309:65 */
  assign n1535 = cstate == 4'b0011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:309:55 */
  assign n1536 = n1533 | n1535;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:309:96 */
  assign n1538 = cstate == 4'b1000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:309:86 */
  assign n1539 = n1536 | n1538;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:309:127 */
  assign n1540 = ~ziroundnr;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:309:113 */
  assign n1541 = n1540 & n1539;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:309:25 */
  assign n1542 = n1541 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:311:38 */
  assign n1546 = cstate == 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:311:45 */
  assign n1547 = block_ready & n1546;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:312:57 */
  assign n1549 = cstate == 4'b0010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:312:87 */
  assign n1550 = ~ziroundnr;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:312:73 */
  assign n1551 = n1550 & n1549;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:311:68 */
  assign n1552 = n1547 | n1551;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:313:58 */
  assign n1554 = cstate == 4'b0010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:313:75 */
  assign n1555 = ziroundnr & n1554;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:313:109 */
  assign n1556 = ~msg_end;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:313:115 */
  assign n1557 = block_ready & n1556;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:313:138 */
  assign n1558 = n1557 | msg_end;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:313:95 */
  assign n1559 = n1558 & n1555;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:312:94 */
  assign n1560 = n1552 | n1559;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:314:57 */
  assign n1562 = cstate == 4'b0011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:313:159 */
  assign n1563 = n1560 | n1562;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:315:33 */
  assign n1565 = cstate == 4'b0100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:315:70 */
  assign n1566 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:315:54 */
  assign n1567 = n1566 & n1565;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:315:76 */
  assign n1568 = block_ready & n1567;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:315:120 */
  assign n1569 = $unsigned(cnt_output_size_r) <= $unsigned(b);
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:315:98 */
  assign n1570 = n1569 & n1568;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:314:79 */
  assign n1571 = n1563 | n1570;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:316:57 */
  assign n1573 = cstate == 4'b0101;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:316:92 */
  assign n1574 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:316:76 */
  assign n1575 = n1574 & n1573;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:316:98 */
  assign n1576 = block_ready & n1575;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:315:126 */
  assign n1577 = n1571 | n1576;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:317:59 */
  assign n1579 = cstate == 4'b0111;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:317:87 */
  assign n1581 = cstate == 4'b0110;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:317:77 */
  assign n1582 = n1579 | n1581;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:317:125 */
  assign n1583 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:317:109 */
  assign n1584 = n1583 & n1582;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:317:131 */
  assign n1585 = block_ready & n1584;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:316:121 */
  assign n1586 = n1577 | n1585;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:318:33 */
  assign n1588 = cstate == 4'b1000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:317:154 */
  assign n1589 = n1586 | n1588;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:311:25 */
  assign n1590 = n1589 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:322:41 */
  assign n1594 = cstate == 4'b0001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:322:48 */
  assign n1595 = block_ready & n1594;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:322:70 */
  assign n1596 = msg_end & n1595;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:323:65 */
  assign n1598 = cstate == 4'b0010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:323:81 */
  assign n1599 = block_ready & n1598;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:323:103 */
  assign n1600 = msg_end & n1599;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:323:121 */
  assign n1601 = ziroundnr & n1600;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:322:89 */
  assign n1602 = n1596 | n1601;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:324:65 */
  assign n1604 = cstate == 4'b0101;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:324:100 */
  assign n1605 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:324:84 */
  assign n1606 = n1605 & n1604;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:324:106 */
  assign n1607 = block_ready & n1606;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:324:128 */
  assign n1608 = msg_end & n1607;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:323:142 */
  assign n1609 = n1602 | n1608;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:325:65 */
  assign n1611 = cstate == 4'b0100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:325:102 */
  assign n1612 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:325:86 */
  assign n1613 = n1612 & n1611;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:325:108 */
  assign n1614 = block_ready & n1613;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:325:130 */
  assign n1615 = msg_end & n1614;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:325:170 */
  assign n1616 = $unsigned(cnt_output_size_r) <= $unsigned(b);
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:325:148 */
  assign n1617 = n1616 & n1615;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:324:147 */
  assign n1618 = n1609 | n1617;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:326:67 */
  assign n1620 = cstate == 4'b0111;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:326:95 */
  assign n1622 = cstate == 4'b0110;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:326:85 */
  assign n1623 = n1620 | n1622;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:326:132 */
  assign n1624 = ~output_busy;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:326:116 */
  assign n1625 = n1624 & n1623;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:326:138 */
  assign n1626 = block_ready & n1625;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:326:160 */
  assign n1627 = msg_end & n1626;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:325:176 */
  assign n1628 = n1618 | n1627;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:322:28 */
  assign n1629 = n1628 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:83:17 */
  always @(posedge clk)
    n1631 <= n1182;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:83:17 */
  always @(posedge clk)
    n1632 <= n1184;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:83:17 */
  always @(posedge clk)
    n1633 <= n1186;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:83:17 */
  always @(posedge clk)
    n1634 <= n1188;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm2.vhd:83:17 */
  always @(posedge clk)
    n1635 <= n1190;
endmodule

module keccak_fsm1_Bnocounter
  (input  clk,
   input  rst,
   input  [31:0] c,
   input  load_next_block,
   input  final_segment,
   output ein,
   output en_ctr,
   output en_len,
   output en_output_len,
   output clr_len,
   output sel_dec_size,
   output last_word,
   output [1:0] spos,
   output block_ready_set,
   output msg_end_set,
   input  src_ready,
   output src_read,
   input  [1:0] mode);
  wire zjfin;
  wire lj;
  wire ej;
  wire [4:0] wc;
  wire [2:0] cstate_fsm1;
  wire [2:0] nstate;
  wire f;
  wire lf;
  wire ef;
  wire zc0;
  wire set_start_pad;
  wire clr_start_pad;
  wire start_pad;
  wire [1:0] spos_sig;
  wire set_full_block;
  wire clr_full_block;
  wire full_block;
  wire zc_more_than_block;
  wire comp_lb_e0;
  wire comp_lb_e0_128;
  wire comp_lb_e0_256;
  wire comp_lb_e0_512;
  wire [31:0] mw;
  wire [31:0] mw_seg_2;
  wire [4:0] n825;
  wire n827;
  wire n828;
  wire [4:0] n831;
  wire n833;
  wire n834;
  wire [3:0] n837;
  wire n839;
  wire n840;
  wire n843;
  wire n844;
  wire n846;
  wire n847;
  wire n849;
  wire n850;
  wire n853;
  wire [31:0] n854;
  wire n857;
  wire [31:0] n858;
  wire n861;
  wire [31:0] n862;
  wire n866;
  wire [31:0] n867;
  wire n870;
  wire [31:0] n871;
  wire n874;
  wire [31:0] n875;
  wire n879;
  wire n880;
  wire n883;
  wire n884;
  wire sr_final_segment_n892;
  localparam n895 = 1'b0;
  localparam [4:0] n896 = 5'b00000;
  wire [4:0] word_counter_gen_n897;
  wire [31:0] n902;
  wire [4:0] n903;
  wire n904;
  wire n905;
  wire [2:0] n910;
  wire n915;
  wire [2:0] n918;
  wire n920;
  wire n921;
  wire [2:0] n924;
  wire n926;
  wire n927;
  wire n928;
  wire n929;
  wire n930;
  wire n931;
  wire n932;
  wire n933;
  wire n934;
  wire n935;
  wire n936;
  wire n937;
  wire n938;
  wire n939;
  wire n940;
  wire n941;
  wire [2:0] n944;
  wire [2:0] n946;
  wire [2:0] n948;
  wire n950;
  wire n951;
  wire [2:0] n954;
  wire n956;
  wire [4:0] n957;
  reg [2:0] n960;
  wire n964;
  wire n965;
  wire n966;
  wire n968;
  wire n969;
  wire n970;
  wire n971;
  wire n972;
  wire n973;
  wire n974;
  wire n975;
  wire n979;
  wire n980;
  wire n981;
  wire n982;
  wire n983;
  wire n984;
  wire n985;
  wire n986;
  wire n987;
  wire n988;
  wire n989;
  wire n990;
  wire n991;
  wire n995;
  wire n996;
  wire n997;
  wire n998;
  wire n999;
  wire n1000;
  wire n1001;
  wire n1002;
  wire n1003;
  wire n1004;
  wire n1005;
  wire n1006;
  wire n1007;
  wire n1008;
  wire n1012;
  wire n1013;
  wire n1014;
  wire n1015;
  wire n1016;
  wire n1017;
  wire n1021;
  wire n1023;
  wire n1024;
  wire n1025;
  wire n1026;
  wire n1030;
  wire n1031;
  wire n1032;
  wire n1035;
  wire n1037;
  wire n1038;
  wire n1039;
  wire n1042;
  wire n1044;
  wire n1045;
  wire n1046;
  wire n1050;
  wire n1051;
  wire n1052;
  wire n1054;
  wire n1055;
  wire n1056;
  wire n1057;
  wire n1058;
  wire n1059;
  wire n1060;
  wire n1061;
  wire n1062;
  wire n1066;
  wire n1068;
  wire n1069;
  wire n1071;
  wire n1072;
  wire n1073;
  wire sr_full_block_n1075;
  wire n1080;
  wire n1081;
  wire n1082;
  wire n1086;
  wire n1087;
  wire n1088;
  wire n1089;
  wire sr_pos1_n1091;
  wire n1096;
  wire n1097;
  wire n1098;
  wire n1099;
  wire n1100;
  wire n1101;
  wire n1102;
  wire [1:0] n1103;
  wire n1106;
  wire n1107;
  wire n1108;
  wire n1109;
  wire n1110;
  wire n1111;
  wire [1:0] n1112;
  wire n1116;
  wire n1117;
  wire n1118;
  wire n1122;
  wire n1123;
  wire n1124;
  wire n1125;
  wire n1126;
  wire n1127;
  wire n1128;
  wire n1129;
  wire n1133;
  wire n1134;
  wire n1135;
  wire n1136;
  wire n1137;
  wire n1138;
  wire n1142;
  wire n1143;
  wire n1144;
  wire n1145;
  wire n1146;
  wire n1147;
  wire n1148;
  wire n1149;
  wire n1150;
  reg [2:0] n1152;
  wire n2876;
  wire [4:0] n2877;
  wire n2878;
  wire n2879;
  assign ein = ej; //(module output)
  assign en_ctr = n1062; //(module output)
  assign en_len = n1039; //(module output)
  assign en_output_len = n1046; //(module output)
  assign clr_len = n1150; //(module output)
  assign sel_dec_size = set_full_block; //(module output)
  assign last_word = n1138; //(module output)
  assign spos = spos_sig; //(module output)
  assign block_ready_set = n1008; //(module output)
  assign msg_end_set = n1017; //(module output)
  assign src_read = n975; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:52:16 */
  assign zjfin = n905; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:52:23 */
  assign lj = n1073; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:52:27 */
  assign ej = n991; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:53:16 */
  assign wc = word_counter_gen_n897; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:58:16 */
  assign cstate_fsm1 = n1152; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:58:29 */
  assign nstate = n960; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:60:16 */
  assign f = sr_final_segment_n892; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:60:19 */
  assign lf = n1026; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:60:23 */
  assign ef = n1032; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:61:16 */
  assign zc0 = n880; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:63:16 */
  assign set_start_pad = n1118; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:63:31 */
  assign clr_start_pad = n1129; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:63:46 */
  assign start_pad = sr_pos1_n1091; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:64:16 */
  assign spos_sig = n1103; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:65:16 */
  assign set_full_block = n1082; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:65:32 */
  assign clr_full_block = n1089; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:65:48 */
  assign full_block = sr_full_block_n1075; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:67:16 */
  assign zc_more_than_block = n884; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:67:36 */
  assign comp_lb_e0 = n844; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:68:12 */
  assign comp_lb_e0_128 = n828; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:68:28 */
  assign comp_lb_e0_256 = n834; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:68:44 */
  assign comp_lb_e0_512 = n840; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:70:12 */
  assign mw = n854; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:70:16 */
  assign mw_seg_2 = n867; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:73:33 */
  assign n825 = c[10:6]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:73:47 */
  assign n827 = n825 == 5'b00000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:73:27 */
  assign n828 = n827 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:74:33 */
  assign n831 = c[10:6]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:74:47 */
  assign n833 = n831 == 5'b00000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:74:27 */
  assign n834 = n833 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:75:33 */
  assign n837 = c[9:6]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:75:47 */
  assign n839 = n837 == 4'b0000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:75:27 */
  assign n840 = n839 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:77:46 */
  assign n843 = mode == 2'b10;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:77:36 */
  assign n844 = n843 ? comp_lb_e0_128 : n847;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:78:46 */
  assign n846 = mode == 2'b00;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:77:53 */
  assign n847 = n846 ? comp_lb_e0_256 : n850;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:79:46 */
  assign n849 = mode == 2'b01;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:78:53 */
  assign n850 = n849 ? comp_lb_e0_512 : comp_lb_e0_256;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:82:42 */
  assign n853 = mode == 2'b00;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:82:32 */
  assign n854 = n853 ? 32'b00000000000000000000010001000000 : n858;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:83:42 */
  assign n857 = mode == 2'b01;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:82:49 */
  assign n858 = n857 ? 32'b00000000000000000000001001000000 : n862;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:84:42 */
  assign n861 = mode == 2'b10;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:83:49 */
  assign n862 = n861 ? 32'b00000000000000000000010101000000 : 32'b00000000000000000000010001000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:87:50 */
  assign n866 = mode == 2'b00;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:87:40 */
  assign n867 = n866 ? 32'b00000000000000000000000000010001 : n871;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:88:50 */
  assign n870 = mode == 2'b01;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:87:57 */
  assign n871 = n870 ? 32'b00000000000000000000000000001001 : n875;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:89:50 */
  assign n874 = mode == 2'b10;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:88:57 */
  assign n875 = n874 ? 32'b00000000000000000000000000010101 : 32'b00000000000000000000000000010001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:92:27 */
  assign n879 = c == 32'b00000000000000000000000000000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:92:20 */
  assign n880 = n879 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:93:42 */
  assign n883 = $unsigned(c) >= $unsigned(mw);
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:93:35 */
  assign n884 = n883 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:101:76 */
  assign sr_final_segment_n892 = n2876; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:100:9 */
  sr_reg_Bstruct_c4ea21bb365bbeeaf5f2c654883e56d11e43c44e sr_final_segment (
    .rst(rst),
    .clk(clk),
    .set(ef),
    .clr(lf),
    .\output (n2876));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:111:19 */
  assign word_counter_gen_n897 = n2877; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:104:9 */
  countern_Bcountern_5_1_1 word_counter_gen (
    .clk(clk),
    .rst(1'b0),
    .load(lj),
    .en(ej),
    .\input (5'b00000),
    .\output (n2877));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:113:62 */
  assign n902 = mw_seg_2 - 32'b00000000000000000000000000000001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:113:32 */
  assign n903 = n902[4:0];  // trunc
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:113:30 */
  assign n904 = wc == n903;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:113:22 */
  assign n905 = n904 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:119:25 */
  assign n910 = rst ? 3'b000 : nstate;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:131:25 */
  assign n915 = cstate_fsm1 == 3'b000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:134:33 */
  assign n918 = src_ready ? 3'b001 : 3'b011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:133:25 */
  assign n920 = cstate_fsm1 == 3'b001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:140:53 */
  assign n921 = ~load_next_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:140:33 */
  assign n924 = n921 ? 3'b011 : 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:139:25 */
  assign n926 = cstate_fsm1 == 3'b011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:146:61 */
  assign n927 = ~f;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:146:74 */
  assign n928 = ~zc0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:146:67 */
  assign n929 = n927 | n928;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:146:80 */
  assign n930 = n929 | full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:146:54 */
  assign n931 = n930 & src_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:147:49 */
  assign n932 = ~zjfin;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:147:40 */
  assign n933 = n931 | n932;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:149:67 */
  assign n934 = ~full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:149:52 */
  assign n935 = n934 & zjfin;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:149:73 */
  assign n936 = f & n935;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:151:50 */
  assign n937 = ~src_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:151:56 */
  assign n938 = zjfin & n937;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:151:78 */
  assign n939 = ~f;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:151:72 */
  assign n940 = n939 & n938;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:151:84 */
  assign n941 = zc0 & n940;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:151:33 */
  assign n944 = n941 ? 3'b001 : 3'b011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:149:33 */
  assign n946 = n936 ? 3'b100 : n944;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:146:33 */
  assign n948 = n933 ? 3'b010 : n946;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:145:25 */
  assign n950 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:158:54 */
  assign n951 = ~load_next_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:158:34 */
  assign n954 = n951 ? 3'b100 : 3'b001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:157:20 */
  assign n956 = cstate_fsm1 == 3'b100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:130:17 */
  assign n957 = {n956, n950, n926, n920, n915};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:130:17 */
  always @*
    case (n957)
      5'b10000: n960 = n954;
      5'b01000: n960 = n948;
      5'b00100: n960 = n924;
      5'b00010: n960 = n918;
      5'b00001: n960 = 3'b001;
      default: n960 = 3'bX;
    endcase
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:168:44 */
  assign n964 = cstate_fsm1 == 3'b001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:168:77 */
  assign n965 = ~src_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:168:63 */
  assign n966 = n965 & n964;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:169:30 */
  assign n968 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:169:57 */
  assign n969 = ~src_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:169:43 */
  assign n970 = n969 & n968;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:170:14 */
  assign n971 = ~zc0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:170:20 */
  assign n972 = n971 | full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:169:63 */
  assign n973 = n972 & n970;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:168:84 */
  assign n974 = n966 | n973;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:168:25 */
  assign n975 = n974 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:174:37 */
  assign n979 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:174:67 */
  assign n980 = ~src_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:175:14 */
  assign n981 = ~zc0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:175:25 */
  assign n982 = ~f;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:175:20 */
  assign n983 = n981 | n982;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:175:31 */
  assign n984 = n983 | full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:174:73 */
  assign n985 = n984 & n980;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:176:28 */
  assign n986 = f & zc0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:176:55 */
  assign n987 = ~full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:176:40 */
  assign n988 = n987 & n986;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:175:53 */
  assign n989 = n985 | n988;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:174:51 */
  assign n990 = n989 & n979;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:174:19 */
  assign n991 = n990 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:178:50 */
  assign n995 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:178:63 */
  assign n996 = zjfin & n995;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:179:25 */
  assign n997 = ~src_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:179:40 */
  assign n998 = ~zc0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:179:51 */
  assign n999 = ~f;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:179:46 */
  assign n1000 = n998 | n999;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:179:57 */
  assign n1001 = n1000 | full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:179:31 */
  assign n1002 = n1001 & n997;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:180:36 */
  assign n1003 = f & zc0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:180:63 */
  assign n1004 = ~full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:180:48 */
  assign n1005 = n1004 & n1003;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:179:79 */
  assign n1006 = n1002 | n1005;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:178:80 */
  assign n1007 = n1006 & n996;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:178:32 */
  assign n1008 = n1007 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:183:46 */
  assign n1012 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:183:59 */
  assign n1013 = zjfin & n1012;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:184:20 */
  assign n1014 = ~full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:183:75 */
  assign n1015 = n1014 & n1013;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:184:26 */
  assign n1016 = f & n1015;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:183:28 */
  assign n1017 = n1016 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:186:37 */
  assign n1021 = cstate_fsm1 == 3'b000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:186:63 */
  assign n1023 = cstate_fsm1 == 3'b100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:186:80 */
  assign n1024 = load_next_block & n1023;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:186:46 */
  assign n1025 = n1021 | n1024;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:186:19 */
  assign n1026 = n1025 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:189:37 */
  assign n1030 = cstate_fsm1 == 3'b001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:189:56 */
  assign n1031 = final_segment & n1030;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:189:19 */
  assign n1032 = n1031 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:191:39 */
  assign n1035 = ~src_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:191:61 */
  assign n1037 = cstate_fsm1 == 3'b001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:191:45 */
  assign n1038 = n1037 & n1035;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:191:23 */
  assign n1039 = n1038 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:192:42 */
  assign n1042 = ~src_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:192:64 */
  assign n1044 = cstate_fsm1 == 3'b001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:192:48 */
  assign n1045 = n1044 & n1042;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:192:26 */
  assign n1046 = n1045 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:193:46 */
  assign n1050 = cstate_fsm1 == 3'b011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:193:63 */
  assign n1051 = load_next_block & n1050;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:194:31 */
  assign n1052 = zc_more_than_block & n1051;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:195:30 */
  assign n1054 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:195:58 */
  assign n1055 = ~full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:195:43 */
  assign n1056 = n1055 & n1054;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:195:78 */
  assign n1057 = ~src_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:195:64 */
  assign n1058 = n1057 & n1056;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:195:92 */
  assign n1059 = ~zc0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:195:84 */
  assign n1060 = n1059 & n1058;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:194:61 */
  assign n1061 = n1052 | n1060;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:193:23 */
  assign n1062 = n1061 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:198:38 */
  assign n1066 = cstate_fsm1 == 3'b000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:198:63 */
  assign n1068 = cstate_fsm1 == 3'b011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:198:47 */
  assign n1069 = n1066 | n1068;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:199:22 */
  assign n1071 = cstate_fsm1 == 3'b100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:198:81 */
  assign n1072 = n1069 | n1071;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:198:19 */
  assign n1073 = n1072 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:208:19 */
  assign sr_full_block_n1075 = n2878; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:202:9 */
  sr_reg_Bstruct_c4ea21bb365bbeeaf5f2c654883e56d11e43c44e sr_full_block (
    .rst(rst),
    .clk(clk),
    .set(set_full_block),
    .clr(clr_full_block),
    .\output (n2878));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:210:49 */
  assign n1080 = cstate_fsm1 == 3'b011;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:210:66 */
  assign n1081 = zc_more_than_block & n1080;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:210:31 */
  assign n1082 = n1081 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:212:49 */
  assign n1086 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:212:62 */
  assign n1087 = zjfin & n1086;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:212:78 */
  assign n1088 = ej & n1087;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:212:31 */
  assign n1089 = n1088 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:222:19 */
  assign sr_pos1_n1091 = n2879; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:216:9 */
  sr_reg_Bstruct_c4ea21bb365bbeeaf5f2c654883e56d11e43c44e sr_pos1 (
    .rst(rst),
    .clk(clk),
    .set(set_start_pad),
    .clr(clr_start_pad),
    .\output (n2879));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:224:44 */
  assign n1096 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:224:72 */
  assign n1097 = ~full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:224:57 */
  assign n1098 = n1097 & n1096;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:224:78 */
  assign n1099 = f & n1098;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:225:17 */
  assign n1100 = comp_lb_e0 & n1099;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:225:52 */
  assign n1101 = ~start_pad;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:225:38 */
  assign n1102 = n1101 & n1100;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:224:26 */
  assign n1103 = n1102 ? 2'b00 : n1112;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:226:40 */
  assign n1106 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:226:68 */
  assign n1107 = ~full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:226:53 */
  assign n1108 = n1107 & n1106;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:226:74 */
  assign n1109 = f & n1108;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:226:86 */
  assign n1110 = comp_lb_e0 & n1109;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:227:26 */
  assign n1111 = start_pad & n1110;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:225:59 */
  assign n1112 = n1111 ? 2'b01 : 2'b11;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:230:48 */
  assign n1116 = cstate_fsm1 == 3'b001;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:230:67 */
  assign n1117 = final_segment & n1116;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:230:30 */
  assign n1118 = n1117 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:232:48 */
  assign n1122 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:232:76 */
  assign n1123 = ~full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:232:61 */
  assign n1124 = n1123 & n1122;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:232:82 */
  assign n1125 = f & n1124;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:233:17 */
  assign n1126 = comp_lb_e0 & n1125;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:233:38 */
  assign n1127 = start_pad & n1126;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:233:58 */
  assign n1128 = ej & n1127;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:232:30 */
  assign n1129 = n1128 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:236:44 */
  assign n1133 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:236:57 */
  assign n1134 = zjfin & n1133;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:237:20 */
  assign n1135 = ~full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:236:73 */
  assign n1136 = n1135 & n1134;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:237:26 */
  assign n1137 = f & n1136;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:236:26 */
  assign n1138 = n1137 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:241:42 */
  assign n1142 = cstate_fsm1 == 3'b010;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:241:70 */
  assign n1143 = ~full_block;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:241:55 */
  assign n1144 = n1143 & n1142;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:241:76 */
  assign n1145 = f & n1144;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:242:17 */
  assign n1146 = comp_lb_e0 & n1145;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:242:52 */
  assign n1147 = ~src_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:242:38 */
  assign n1148 = n1147 & n1146;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:242:58 */
  assign n1149 = ej & n1148;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:241:24 */
  assign n1150 = n1149 ? 1'b1 : 1'b0;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_fsm1.vhd:118:17 */
  always @(posedge clk)
    n1152 <= n910;
endmodule

module keccak_datapath_Bstruct_3
  (input  clk,
   input  rst,
   input  [63:0] din,
   output [63:0] dout,
   input  en_len,
   input  en_output_len,
   input  en_ctr,
   input  ein,
   output [31:0] c,
   output [31:0] d,
   output final_segment,
   output [1:0] mode,
   input  sel_xor,
   input  sel_final,
   input  wr_state,
   input  ld_rdctr,
   input  en_rdctr,
   input  clr_len,
   input  sel_dec_size,
   input  [1:0] spos,
   input  last_word,
   input  sel_piso,
   input  wr_piso,
   input  [1:0] mode_ctrl,
   input  [10:0] output_size,
   input  last_out_word);
  wire [31:0] din_a;
  wire [31:0] din_b;
  wire [1343:0] from_sipo;
  wire [1599:0] from_concat;
  wire [1599:0] to_xor;
  wire [1599:0] from_round;
  wire [1599:0] from_xor;
  wire [1599:0] to_register;
  wire [1599:0] to_round;
  wire [1343:0] to_piso;
  wire [4:0] rd_ctr;
  wire [63:0] rc;
  wire [63:0] swap_din;
  wire [31:0] block_size;
  wire [1343:0] se_result;
  wire [63:0] din_padded;
  wire [31:0] c_wire;
  wire [31:0] c_wire_in;
  wire [31:0] d_len_wire;
  wire [7:0] sel_pad_type_lookup;
  wire [7:0] sel_din_lookup;
  wire [7:0] sel_din;
  wire [7:0] sel_pad_location;
  wire [7:0] sel_dout;
  wire [63:0] dout_wire;
  wire [1:0] shake_mode_wire;
  wire n114;
  wire [31:0] n117;
  wire [31:0] n118;
  wire [31:0] n119;
  wire [31:0] n121;
  wire [28:0] n122;
  wire [31:0] n124;
  wire [1:0] n125;
  wire [31:0] n126;
  wire [1:0] n127;
  wire [31:0] n129;
  wire [1:0] n131;
  wire n138;
  wire [31:0] n139;
  wire n142;
  wire [31:0] n143;
  wire n146;
  wire [31:0] n147;
  wire [31:0] n149;
  wire [31:0] n150;
  wire [31:0] n152;
  wire [2:0] n153;
  wire n161;
  wire n162;
  wire [7:0] n163;
  wire [2:0] n164;
  wire n172;
  wire [7:0] n173;
  wire [2:0] n174;
  wire [63:0] \pad_unit.dout_output ;
  wire [31:0] n183;
  wire [31:0] n184;
  wire [7:0] n193;
  wire [7:0] n196;
  wire [7:0] n198;
  wire [7:0] n200;
  wire [31:0] n201;
  wire [7:0] n210;
  wire [7:0] n213;
  wire [7:0] n215;
  wire [7:0] n217;
  wire [31:0] n218;
  wire [63:0] n219;
  wire [1343:0] in_buf_n220;
  wire [575:0] n223;
  wire [1599:0] n225;
  wire n227;
  wire [1599:0] n228;
  wire [1599:0] n230;
  wire n232;
  wire [1599:0] n233;
  wire [1087:0] n234;
  wire [1599:0] n236;
  wire [1599:0] n238;
  wire [1599:0] n239;
  wire [1599:0] n240;
  wire [1599:0] state_n241;
  localparam [4:0] n246 = 5'b00000;
  wire [4:0] ctr_n247;
  wire [63:0] n250;
  wire [7:0] n259;
  wire [7:0] n262;
  wire [7:0] n264;
  wire [7:0] n266;
  wire [7:0] n268;
  wire [7:0] n270;
  wire [7:0] n272;
  wire [7:0] n274;
  wire [63:0] n275;
  wire [63:0] n276;
  wire [7:0] n285;
  wire [7:0] n288;
  wire [7:0] n290;
  wire [7:0] n292;
  wire [7:0] n294;
  wire [7:0] n296;
  wire [7:0] n298;
  wire [7:0] n300;
  wire [63:0] n301;
  wire [63:0] n302;
  wire [7:0] n311;
  wire [7:0] n314;
  wire [7:0] n316;
  wire [7:0] n318;
  wire [7:0] n320;
  wire [7:0] n322;
  wire [7:0] n324;
  wire [7:0] n326;
  wire [63:0] n327;
  wire [63:0] n328;
  wire [7:0] n337;
  wire [7:0] n340;
  wire [7:0] n342;
  wire [7:0] n344;
  wire [7:0] n346;
  wire [7:0] n348;
  wire [7:0] n350;
  wire [7:0] n352;
  wire [63:0] n353;
  wire [63:0] n354;
  wire [7:0] n363;
  wire [7:0] n366;
  wire [7:0] n368;
  wire [7:0] n370;
  wire [7:0] n372;
  wire [7:0] n374;
  wire [7:0] n376;
  wire [7:0] n378;
  wire [63:0] n379;
  wire [63:0] n380;
  wire [7:0] n389;
  wire [7:0] n392;
  wire [7:0] n394;
  wire [7:0] n396;
  wire [7:0] n398;
  wire [7:0] n400;
  wire [7:0] n402;
  wire [7:0] n404;
  wire [63:0] n405;
  wire [63:0] n406;
  wire [7:0] n415;
  wire [7:0] n418;
  wire [7:0] n420;
  wire [7:0] n422;
  wire [7:0] n424;
  wire [7:0] n426;
  wire [7:0] n428;
  wire [7:0] n430;
  wire [63:0] n431;
  wire [63:0] n432;
  wire [7:0] n441;
  wire [7:0] n444;
  wire [7:0] n446;
  wire [7:0] n448;
  wire [7:0] n450;
  wire [7:0] n452;
  wire [7:0] n454;
  wire [7:0] n456;
  wire [63:0] n457;
  wire [63:0] n458;
  wire [7:0] n467;
  wire [7:0] n470;
  wire [7:0] n472;
  wire [7:0] n474;
  wire [7:0] n476;
  wire [7:0] n478;
  wire [7:0] n480;
  wire [7:0] n482;
  wire [63:0] n483;
  wire [63:0] n484;
  wire [7:0] n493;
  wire [7:0] n496;
  wire [7:0] n498;
  wire [7:0] n500;
  wire [7:0] n502;
  wire [7:0] n504;
  wire [7:0] n506;
  wire [7:0] n508;
  wire [63:0] n509;
  wire [63:0] n510;
  wire [7:0] n519;
  wire [7:0] n522;
  wire [7:0] n524;
  wire [7:0] n526;
  wire [7:0] n528;
  wire [7:0] n530;
  wire [7:0] n532;
  wire [7:0] n534;
  wire [63:0] n535;
  wire [63:0] n536;
  wire [7:0] n545;
  wire [7:0] n548;
  wire [7:0] n550;
  wire [7:0] n552;
  wire [7:0] n554;
  wire [7:0] n556;
  wire [7:0] n558;
  wire [7:0] n560;
  wire [63:0] n561;
  wire [63:0] n562;
  wire [7:0] n571;
  wire [7:0] n574;
  wire [7:0] n576;
  wire [7:0] n578;
  wire [7:0] n580;
  wire [7:0] n582;
  wire [7:0] n584;
  wire [7:0] n586;
  wire [63:0] n587;
  wire [63:0] n588;
  wire [7:0] n597;
  wire [7:0] n600;
  wire [7:0] n602;
  wire [7:0] n604;
  wire [7:0] n606;
  wire [7:0] n608;
  wire [7:0] n610;
  wire [7:0] n612;
  wire [63:0] n613;
  wire [63:0] n614;
  wire [7:0] n623;
  wire [7:0] n626;
  wire [7:0] n628;
  wire [7:0] n630;
  wire [7:0] n632;
  wire [7:0] n634;
  wire [7:0] n636;
  wire [7:0] n638;
  wire [63:0] n639;
  wire [63:0] n640;
  wire [7:0] n649;
  wire [7:0] n652;
  wire [7:0] n654;
  wire [7:0] n656;
  wire [7:0] n658;
  wire [7:0] n660;
  wire [7:0] n662;
  wire [7:0] n664;
  wire [63:0] n665;
  wire [63:0] n666;
  wire [7:0] n675;
  wire [7:0] n678;
  wire [7:0] n680;
  wire [7:0] n682;
  wire [7:0] n684;
  wire [7:0] n686;
  wire [7:0] n688;
  wire [7:0] n690;
  wire [63:0] n691;
  wire [63:0] n692;
  wire [7:0] n701;
  wire [7:0] n704;
  wire [7:0] n706;
  wire [7:0] n708;
  wire [7:0] n710;
  wire [7:0] n712;
  wire [7:0] n714;
  wire [7:0] n716;
  wire [63:0] n717;
  wire [63:0] n718;
  wire [7:0] n727;
  wire [7:0] n730;
  wire [7:0] n732;
  wire [7:0] n734;
  wire [7:0] n736;
  wire [7:0] n738;
  wire [7:0] n740;
  wire [7:0] n742;
  wire [63:0] n743;
  wire [63:0] n744;
  wire [7:0] n753;
  wire [7:0] n756;
  wire [7:0] n758;
  wire [7:0] n760;
  wire [7:0] n762;
  wire [7:0] n764;
  wire [7:0] n766;
  wire [7:0] n768;
  wire [63:0] n769;
  wire [63:0] n770;
  wire [7:0] n779;
  wire [7:0] n782;
  wire [7:0] n784;
  wire [7:0] n786;
  wire [7:0] n788;
  wire [7:0] n790;
  wire [7:0] n792;
  wire [7:0] n794;
  wire [63:0] n795;
  wire [63:0] out_buf_n796;
  wire [1343:0] n799;
  wire [1343:0] n800;
  reg [31:0] n801;
  reg [31:0] n802;
  reg [1:0] n803;
  wire [7:0] n806; // mem_rd
  wire [7:0] n809; // mem_rd
  wire [7:0] n812; // mem_rd
  wire [1343:0] n2872;
  wire [1599:0] n2873;
  wire [4:0] n2874;
  wire [63:0] n2875;
  assign dout = \pad_unit.dout_output ; //(module output)
  assign c = c_wire; //(module output)
  assign d = d_len_wire; //(module output)
  assign final_segment = n114; //(module output)
  assign mode = shake_mode_wire; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:57:16 */
  assign din_a = n183; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:57:23 */
  assign din_b = n184; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:58:12 */
  assign from_sipo = in_buf_n220; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:60:16 */
  assign from_concat = n228; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:60:29 */
  assign to_xor = n238; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:60:49 */
  assign from_xor = n239; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:60:59 */
  assign to_register = n240; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:60:72 */
  assign to_round = state_n241; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:63:12 */
  assign to_piso = n799; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:64:16 */
  assign rd_ctr = ctr_n247; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:65:21 */
  assign swap_din = n219; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:75:12 */
  assign block_size = n139; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:78:12 */
  assign se_result = n800; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:82:16 */
  assign c_wire = n801; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:82:24 */
  assign c_wire_in = n150; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:82:35 */
  assign d_len_wire = n802; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:84:16 */
  assign sel_pad_type_lookup = n806; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:84:37 */
  assign sel_din_lookup = n809; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:85:16 */
  assign sel_din = n173; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:85:25 */
  assign sel_pad_location = n163; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:85:43 */
  assign sel_dout = n812; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:87:12 */
  assign dout_wire = out_buf_n796; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:88:12 */
  assign shake_mode_wire = n803; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:97:37 */
  assign n114 = din[63]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:107:46 */
  assign n117 = din[31:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:108:25 */
  assign n118 = en_ctr ? c_wire_in : c_wire;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:106:25 */
  assign n119 = en_len ? n117 : n118;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:104:25 */
  assign n121 = clr_len ? 32'b00000000000000000000000000000000 : n119;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:116:47 */
  assign n122 = din[60:32]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:116:42 */
  assign n124 = {3'b000, n122};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:117:39 */
  assign n125 = din[62:61]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:115:13 */
  assign n126 = en_output_len ? n124 : d_len_wire;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:115:13 */
  assign n127 = en_output_len ? n125 : shake_mode_wire;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:112:13 */
  assign n129 = rst ? 32'b00000000000000000000000000000000 : n126;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:112:13 */
  assign n131 = rst ? 2'b00 : n127;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:123:59 */
  assign n138 = shake_mode_wire == 2'b00;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:123:38 */
  assign n139 = n138 ? 32'b00000000000000000000010001000000 : n143;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:124:59 */
  assign n142 = shake_mode_wire == 2'b01;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:123:66 */
  assign n143 = n142 ? 32'b00000000000000000000001001000000 : n147;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:125:59 */
  assign n146 = shake_mode_wire == 2'b10;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:124:66 */
  assign n147 = n146 ? 32'b00000000000000000000010101000000 : 32'b00000000000000000000010001000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:128:29 */
  assign n149 = c_wire - block_size;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:128:42 */
  assign n150 = sel_dec_size ? n149 : n152;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:128:78 */
  assign n152 = c_wire - 32'b00000000000000000000000001000000;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:133:77 */
  assign n153 = c_wire[5:3]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:134:54 */
  assign n161 = spos[0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:134:58 */
  assign n162 = ~n161;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:134:45 */
  assign n163 = n162 ? 8'b00000000 : sel_pad_type_lookup;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:136:72 */
  assign n164 = c_wire[5:3]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:137:45 */
  assign n172 = spos[1]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:137:36 */
  assign n173 = n172 ? 8'b11111111 : sel_din_lookup;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:140:75 */
  assign n174 = output_size[5:3]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:142:9 */
  keccak_bytepad_Bstruct_64 pad_unit (
    .din_input(din),
    .sel_pad_location(sel_pad_location),
    .sel_din(sel_din),
    .last_word(last_word),
    .mode(shake_mode_wire),
    .dout_input(dout_wire),
    .sel_dout(sel_dout),
    .last_out_word(last_out_word),
    .din_output(din_padded),
    .dout_output(\pad_unit.dout_output ));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:158:28 */
  assign n183 = din_padded[31:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:159:28 */
  assign n184 = din_padded[63:32]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:500:81 */
  assign n193 = din_a[7:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:500:81 */
  assign n196 = din_a[15:8]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:500:81 */
  assign n198 = din_a[23:16]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:500:81 */
  assign n200 = din_a[31:24]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:496:26 */
  assign n201 = {n193, n196, n198, n200};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:500:81 */
  assign n210 = din_b[7:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:500:81 */
  assign n213 = din_b[15:8]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:500:81 */
  assign n215 = din_b[23:16]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:500:81 */
  assign n217 = din_b[31:24]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:496:26 */
  assign n218 = {n210, n213, n215, n217};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:160:53 */
  assign n219 = {n201, n218};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:164:67 */
  assign in_buf_n220 = n2872; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:162:5 */
  sipo_Bbehavioral_1344_64 in_buf (
    .clk(clk),
    .en(ein),
    .\input (swap_din),
    .\output (n2872));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:166:31 */
  assign n223 = from_sipo[575:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:166:63 */
  assign n225 = {n223, 1024'b0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:167:40 */
  assign n227 = mode_ctrl == 2'b01;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:167:25 */
  assign n228 = n227 ? n225 : n233;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:168:32 */
  assign n230 = {from_sipo, 256'b0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:168:60 */
  assign n232 = mode_ctrl == 2'b10;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:167:47 */
  assign n233 = n232 ? n230 : n236;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:169:31 */
  assign n234 = from_sipo[1087:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:169:62 */
  assign n236 = {n234, 512'b00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:171:35 */
  assign n238 = sel_xor ? 1600'b0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 : from_round;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:172:36 */
  assign n239 = from_concat ^ to_xor;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:173:33 */
  assign n240 = sel_final ? from_xor : from_round;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:183:19 */
  assign state_n241 = n2873; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:176:9 */
  regn_Bstruct_1600_cff588bd0114761108cce8606ec6021ff729e20e state (
    .clk(clk),
    .rst(rst),
    .en(wr_state),
    .\input (to_register),
    .\output (n2873));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:187:9 */
  keccak_cons_Bkeccak_cons_1 rd_cons (
    .addr(rd_ctr),
    .rc(rc));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:190:9 */
  keccak_round_Bmrogawski_round rd (
    .rin(to_round),
    .rc(rc),
    .rout(from_round));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:202:19 */
  assign ctr_n247 = n2874; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:194:9 */
  countern_Bcountern_5_1_1 ctr (
    .clk(clk),
    .rst(rst),
    .load(ld_rdctr),
    .en(en_rdctr),
    .\input (5'b00000),
    .\output (n2874));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n250 = to_round[1599:1536]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n259 = se_result[1287:1280]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n262 = se_result[1295:1288]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n264 = se_result[1303:1296]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n266 = se_result[1311:1304]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n268 = se_result[1319:1312]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n270 = se_result[1327:1320]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n272 = se_result[1335:1328]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n274 = se_result[1343:1336]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n275 = {n259, n262, n264, n266, n268, n270, n272, n274};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n276 = to_round[1535:1472]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n285 = se_result[1223:1216]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n288 = se_result[1231:1224]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n290 = se_result[1239:1232]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n292 = se_result[1247:1240]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n294 = se_result[1255:1248]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n296 = se_result[1263:1256]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n298 = se_result[1271:1264]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n300 = se_result[1279:1272]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n301 = {n285, n288, n290, n292, n294, n296, n298, n300};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n302 = to_round[1471:1408]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n311 = se_result[1159:1152]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n314 = se_result[1167:1160]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n316 = se_result[1175:1168]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n318 = se_result[1183:1176]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n320 = se_result[1191:1184]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n322 = se_result[1199:1192]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n324 = se_result[1207:1200]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n326 = se_result[1215:1208]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n327 = {n311, n314, n316, n318, n320, n322, n324, n326};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n328 = to_round[1407:1344]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n337 = se_result[1095:1088]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n340 = se_result[1103:1096]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n342 = se_result[1111:1104]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n344 = se_result[1119:1112]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n346 = se_result[1127:1120]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n348 = se_result[1135:1128]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n350 = se_result[1143:1136]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n352 = se_result[1151:1144]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n353 = {n337, n340, n342, n344, n346, n348, n350, n352};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n354 = to_round[1343:1280]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n363 = se_result[1031:1024]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n366 = se_result[1039:1032]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n368 = se_result[1047:1040]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n370 = se_result[1055:1048]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n372 = se_result[1063:1056]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n374 = se_result[1071:1064]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n376 = se_result[1079:1072]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n378 = se_result[1087:1080]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n379 = {n363, n366, n368, n370, n372, n374, n376, n378};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n380 = to_round[1279:1216]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n389 = se_result[967:960]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n392 = se_result[975:968]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n394 = se_result[983:976]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n396 = se_result[991:984]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n398 = se_result[999:992]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n400 = se_result[1007:1000]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n402 = se_result[1015:1008]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n404 = se_result[1023:1016]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n405 = {n389, n392, n394, n396, n398, n400, n402, n404};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n406 = to_round[1215:1152]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n415 = se_result[903:896]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n418 = se_result[911:904]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n420 = se_result[919:912]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n422 = se_result[927:920]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n424 = se_result[935:928]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n426 = se_result[943:936]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n428 = se_result[951:944]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n430 = se_result[959:952]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n431 = {n415, n418, n420, n422, n424, n426, n428, n430};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n432 = to_round[1151:1088]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n441 = se_result[839:832]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n444 = se_result[847:840]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n446 = se_result[855:848]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n448 = se_result[863:856]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n450 = se_result[871:864]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n452 = se_result[879:872]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n454 = se_result[887:880]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n456 = se_result[895:888]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n457 = {n441, n444, n446, n448, n450, n452, n454, n456};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n458 = to_round[1087:1024]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n467 = se_result[775:768]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n470 = se_result[783:776]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n472 = se_result[791:784]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n474 = se_result[799:792]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n476 = se_result[807:800]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n478 = se_result[815:808]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n480 = se_result[823:816]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n482 = se_result[831:824]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n483 = {n467, n470, n472, n474, n476, n478, n480, n482};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n484 = to_round[1023:960]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n493 = se_result[711:704]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n496 = se_result[719:712]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n498 = se_result[727:720]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n500 = se_result[735:728]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n502 = se_result[743:736]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n504 = se_result[751:744]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n506 = se_result[759:752]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n508 = se_result[767:760]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n509 = {n493, n496, n498, n500, n502, n504, n506, n508};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n510 = to_round[959:896]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n519 = se_result[647:640]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n522 = se_result[655:648]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n524 = se_result[663:656]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n526 = se_result[671:664]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n528 = se_result[679:672]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n530 = se_result[687:680]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n532 = se_result[695:688]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n534 = se_result[703:696]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n535 = {n519, n522, n524, n526, n528, n530, n532, n534};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n536 = to_round[895:832]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n545 = se_result[583:576]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n548 = se_result[591:584]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n550 = se_result[599:592]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n552 = se_result[607:600]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n554 = se_result[615:608]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n556 = se_result[623:616]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n558 = se_result[631:624]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n560 = se_result[639:632]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n561 = {n545, n548, n550, n552, n554, n556, n558, n560};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n562 = to_round[831:768]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n571 = se_result[519:512]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n574 = se_result[527:520]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n576 = se_result[535:528]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n578 = se_result[543:536]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n580 = se_result[551:544]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n582 = se_result[559:552]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n584 = se_result[567:560]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n586 = se_result[575:568]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n587 = {n571, n574, n576, n578, n580, n582, n584, n586};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n588 = to_round[767:704]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n597 = se_result[455:448]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n600 = se_result[463:456]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n602 = se_result[471:464]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n604 = se_result[479:472]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n606 = se_result[487:480]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n608 = se_result[495:488]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n610 = se_result[503:496]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n612 = se_result[511:504]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n613 = {n597, n600, n602, n604, n606, n608, n610, n612};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n614 = to_round[703:640]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n623 = se_result[391:384]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n626 = se_result[399:392]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n628 = se_result[407:400]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n630 = se_result[415:408]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n632 = se_result[423:416]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n634 = se_result[431:424]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n636 = se_result[439:432]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n638 = se_result[447:440]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n639 = {n623, n626, n628, n630, n632, n634, n636, n638};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n640 = to_round[639:576]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n649 = se_result[327:320]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n652 = se_result[335:328]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n654 = se_result[343:336]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n656 = se_result[351:344]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n658 = se_result[359:352]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n660 = se_result[367:360]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n662 = se_result[375:368]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n664 = se_result[383:376]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n665 = {n649, n652, n654, n656, n658, n660, n662, n664};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n666 = to_round[575:512]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n675 = se_result[263:256]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n678 = se_result[271:264]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n680 = se_result[279:272]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n682 = se_result[287:280]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n684 = se_result[295:288]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n686 = se_result[303:296]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n688 = se_result[311:304]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n690 = se_result[319:312]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n691 = {n675, n678, n680, n682, n684, n686, n688, n690};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n692 = to_round[511:448]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n701 = se_result[199:192]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n704 = se_result[207:200]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n706 = se_result[215:208]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n708 = se_result[223:216]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n710 = se_result[231:224]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n712 = se_result[239:232]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n714 = se_result[247:240]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n716 = se_result[255:248]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n717 = {n701, n704, n706, n708, n710, n712, n714, n716};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n718 = to_round[447:384]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n727 = se_result[135:128]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n730 = se_result[143:136]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n732 = se_result[151:144]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n734 = se_result[159:152]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n736 = se_result[167:160]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n738 = se_result[175:168]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n740 = se_result[183:176]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n742 = se_result[191:184]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n743 = {n727, n730, n732, n734, n736, n738, n740, n742};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n744 = to_round[383:320]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n753 = se_result[71:64]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n756 = se_result[79:72]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n758 = se_result[87:80]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n760 = se_result[95:88]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n762 = se_result[103:96]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n764 = se_result[111:104]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n766 = se_result[119:112]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n768 = se_result[127:120]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n769 = {n753, n756, n758, n760, n762, n764, n766, n768};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:206:33 */
  assign n770 = to_round[319:256]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n779 = se_result[7:0]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n782 = se_result[15:8]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n784 = se_result[23:16]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n786 = se_result[31:24]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n788 = se_result[39:32]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n790 = se_result[47:40]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n792 = se_result[55:48]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:511:61 */
  assign n794 = se_result[63:56]; // extract
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/sha3_pkg.vhd:508:26 */
  assign n795 = {n779, n782, n784, n786, n788, n790, n792, n794};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:218:19 */
  assign out_buf_n796 = n2875; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:211:5 */
  piso_Bbehavioral_1344_64 out_buf (
    .clk(clk),
    .en(wr_piso),
    .sel(sel_piso),
    .\input (to_piso),
    .\output (n2875));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:63:12 */
  assign n799 = {n275, n301, n327, n353, n379, n405, n431, n457, n483, n509, n535, n561, n587, n613, n639, n665, n691, n717, n743, n769, n795};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:78:12 */
  assign n800 = {n250, n276, n302, n328, n354, n380, n406, n432, n458, n484, n510, n536, n562, n588, n614, n640, n666, n692, n718, n744, n770};
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:103:17 */
  always @(posedge clk)
    n801 <= n121;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:103:17 */
  always @(posedge clk)
    n802 <= n129;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:103:17 */
  always @(posedge clk)
    n803 <= n131;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:133:58 */
  wire [7:0] n804[7:0] ; // memory
    assign n804[7] = 8'b00000001;
  assign n804[6] = 8'b00000010;
  assign n804[5] = 8'b00000100;
  assign n804[4] = 8'b00001000;
  assign n804[3] = 8'b00010000;
  assign n804[2] = 8'b00100000;
  assign n804[1] = 8'b01000000;
  assign n804[0] = 8'b10000000;
  assign n806 = n804[n153];
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:133:58 */
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:136:53 */
  wire [7:0] n807[7:0] ; // memory
    assign n807[7] = 8'b11111110;
  assign n807[6] = 8'b11111100;
  assign n807[5] = 8'b11111000;
  assign n807[4] = 8'b11110000;
  assign n807[3] = 8'b11100000;
  assign n807[2] = 8'b11000000;
  assign n807[1] = 8'b10000000;
  assign n807[0] = 8'b00000000;
  assign n809 = n807[n164];
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:136:53 */
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:140:51 */
  wire [7:0] n810[7:0] ; // memory
    assign n810[7] = 8'b11111110;
  assign n810[6] = 8'b11111100;
  assign n810[5] = 8'b11111000;
  assign n810[4] = 8'b11110000;
  assign n810[3] = 8'b11100000;
  assign n810[2] = 8'b11000000;
  assign n810[1] = 8'b10000000;
  assign n810[0] = 8'b11111111;
  assign n812 = n810[n174];
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_datapath.vhd:140:51 */
endmodule

module keccak_control_Bstruct
  (input  clk,
   input  rst,
   input  src_ready,
   output src_read,
   input  dst_ready,
   output dst_write,
   output clr_len,
   output sel_dec_size,
   output last_word,
   output [1:0] spos,
   output ein,
   output en_ctr,
   output en_len,
   output en_output_len,
   output sel_cin,
   output sel_xor,
   output sel_final,
   output ld_rdctr,
   output en_rdctr,
   output wr_state,
   input  final_segment,
   output sel_out,
   output wr_piso,
   input  [31:0] c,
   input  [31:0] d,
   input  [1:0] mode,
   output [1:0] mode_ctrl,
   output [10:0] output_size,
   output last_out_word);
  wire block_ready_set;
  wire msg_end_set;
  wire load_next_block;
  wire block_ready_clr;
  wire msg_end_clr;
  wire block_ready;
  wire msg_end;
  wire output_write_set;
  wire output_busy_set;
  wire output_busy;
  wire output_write;
  wire output_write_clr;
  wire output_busy_clr;
  wire ein_wire;
  wire en_ctr_wire;
  wire en_len_wire;
  wire en_output_len_wire;
  wire wr_piso_wire;
  wire src_read_wire;
  wire dst_write_wire;
  wire sel_out_wire;
  wire sel_out_wire2;
  wire sel_xor_wire;
  wire wr_state_wire;
  wire sel_final_wire;
  wire ld_rdctr_wire;
  wire en_rdctr_wire;
  wire eo_wire;
  wire [10:0] output_size_wire;
  wire \fsm1_gen.clr_len ;
  wire \fsm1_gen.sel_dec_size ;
  wire \fsm1_gen.last_word ;
  wire [1:0] \fsm1_gen.spos ;
  wire [1:0] \fsm2_gen.mode_ctrl ;
  wire \fsm3_gen.last_out_word ;
  wire n78;
  wire n79;
  wire sr_blk_ready_n80;
  wire sr_msg_end_n83;
  wire sr_output_write_n86;
  wire sr_output_busy_n89;
  wire n101;
  localparam n102 = 1'bZ;
  reg n103;
  reg n104;
  reg n105;
  reg n106;
  reg n107;
  reg n108;
  wire n2868;
  wire n2869;
  wire n2870;
  wire n2871;
  assign src_read = src_read_wire; //(module output)
  assign dst_write = dst_write_wire; //(module output)
  assign clr_len = \fsm1_gen.clr_len ; //(module output)
  assign sel_dec_size = \fsm1_gen.sel_dec_size ; //(module output)
  assign last_word = \fsm1_gen.last_word ; //(module output)
  assign spos = \fsm1_gen.spos ; //(module output)
  assign ein = ein_wire; //(module output)
  assign en_ctr = en_ctr_wire; //(module output)
  assign en_len = en_len_wire; //(module output)
  assign en_output_len = en_output_len_wire; //(module output)
  assign sel_cin = n102; //(module output)
  assign sel_xor = n103; //(module output)
  assign sel_final = n104; //(module output)
  assign ld_rdctr = n105; //(module output)
  assign en_rdctr = n106; //(module output)
  assign wr_state = n107; //(module output)
  assign sel_out = sel_out_wire2; //(module output)
  assign wr_piso = wr_piso_wire; //(module output)
  assign mode_ctrl = \fsm2_gen.mode_ctrl ; //(module output)
  assign output_size = output_size_wire; //(module output)
  assign last_out_word = \fsm3_gen.last_out_word ; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:57:46 */
  assign load_next_block = n79; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:59:16 */
  assign block_ready = sr_blk_ready_n80; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:59:29 */
  assign msg_end = sr_msg_end_n83; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:61:16 */
  assign output_busy = sr_output_busy_n89; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:62:16 */
  assign output_write = sr_output_write_n86; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:68:16 */
  assign wr_piso_wire = n101; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:69:30 */
  assign sel_out_wire2 = n108; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:81:9 */
  keccak_fsm1_Bnocounter fsm1_gen (
    .clk(clk),
    .rst(rst),
    .c(c),
    .load_next_block(load_next_block),
    .final_segment(final_segment),
    .src_ready(src_ready),
    .mode(mode),
    .ein(ein_wire),
    .en_ctr(en_ctr_wire),
    .en_len(en_len_wire),
    .en_output_len(en_output_len_wire),
    .clr_len(\fsm1_gen.clr_len ),
    .sel_dec_size(\fsm1_gen.sel_dec_size ),
    .last_word(\fsm1_gen.last_word ),
    .spos(\fsm1_gen.spos ),
    .block_ready_set(block_ready_set),
    .msg_end_set(msg_end_set),
    .src_read(src_read_wire));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:106:9 */
  keccak_fsm2_Bbeh fsm2_gen (
    .clk(clk),
    .rst(rst),
    .block_ready(block_ready),
    .msg_end(msg_end),
    .output_busy(output_busy),
    .d(d),
    .mode(mode),
    .wr_state(wr_state_wire),
    .sel_xor(sel_xor_wire),
    .sel_final(sel_final_wire),
    .ld_rdctr(ld_rdctr_wire),
    .en_rdctr(en_rdctr_wire),
    .block_ready_clr(block_ready_clr),
    .msg_end_clr(msg_end_clr),
    .lo(sel_out_wire),
    .output_write_set(output_write_set),
    .output_busy_set(output_busy_set),
    .output_size(output_size_wire),
    .mode_ctrl(\fsm2_gen.mode_ctrl ));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:129:9 */
  sha3_fsm3_Bbeh_64 fsm3_gen (
    .clk(clk),
    .rst(rst),
    .output_write(output_write),
    .dst_ready(dst_ready),
    .output_size(output_size_wire),
    .eo(eo_wire),
    .output_write_clr(output_write_clr),
    .output_busy_clr(output_busy_clr),
    .dst_write(dst_write_wire),
    .last_out_word(\fsm3_gen.last_out_word ));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:143:29 */
  assign n78 = ~block_ready;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:143:46 */
  assign n79 = n78 | block_ready_clr;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:153:19 */
  assign sr_blk_ready_n80 = n2868; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:147:9 */
  sr_reg_Bstruct_c4ea21bb365bbeeaf5f2c654883e56d11e43c44e sr_blk_ready (
    .rst(rst),
    .clk(clk),
    .set(block_ready_set),
    .clr(block_ready_clr),
    .\output (n2868));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:162:19 */
  assign sr_msg_end_n83 = n2869; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:156:9 */
  sr_reg_Bstruct_c4ea21bb365bbeeaf5f2c654883e56d11e43c44e sr_msg_end (
    .rst(rst),
    .clk(clk),
    .set(msg_end_set),
    .clr(msg_end_clr),
    .\output (n2869));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:171:19 */
  assign sr_output_write_n86 = n2870; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:165:9 */
  sr_reg_Bstruct_c4ea21bb365bbeeaf5f2c654883e56d11e43c44e sr_output_write (
    .rst(rst),
    .clk(clk),
    .set(output_write_set),
    .clr(output_write_clr),
    .\output (n2870));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:180:19 */
  assign sr_output_busy_n89 = n2871; // (signal)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:174:9 */
  sr_reg_Bstruct_c4ea21bb365bbeeaf5f2c654883e56d11e43c44e sr_output_busy (
    .rst(rst),
    .clk(clk),
    .set(output_busy_set),
    .clr(output_busy_clr),
    .\output (n2871));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:204:33 */
  assign n101 = eo_wire | sel_out_wire2;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:192:17 */
  always @(posedge clk)
    n103 <= sel_xor_wire;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:192:17 */
  always @(posedge clk)
    n104 <= sel_final_wire;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:192:17 */
  always @(posedge clk)
    n105 <= ld_rdctr_wire;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:192:17 */
  always @(posedge clk)
    n106 <= en_rdctr_wire;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:192:17 */
  always @(posedge clk)
    n107 <= wr_state_wire;
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_control.vhd:192:17 */
  always @(posedge clk)
    n108 <= sel_out_wire;
endmodule

module keccak_top
  (input  rst,
   input  clk,
   input  src_ready,
   output src_read,
   input  dst_ready,
   output dst_write,
   input  [63:0] din,
   output [63:0] dout);
  wire ein;
  wire final_segment;
  wire sel_xor;
  wire sel_final;
  wire wr_state;
  wire en_ctr;
  wire [31:0] c;
  wire [31:0] d;
  wire en_len;
  wire en_output_len;
  wire ld_rdctr;
  wire en_rdctr;
  wire sel_piso;
  wire wr_piso;
  wire [1:0] spos;
  wire [1:0] mode;
  wire [1:0] mode_ctrl;
  wire sel_dec_size;
  wire clr_len;
  wire last_word;
  wire last_out_word;
  wire [10:0] output_size;
  wire \control_gen.src_read ;
  wire \control_gen.dst_write ;
  wire \control_gen.sel_cin ;
  wire [63:0] \datapath_gen.dout ;
  assign src_read = \control_gen.src_read ; //(module output)
  assign dst_write = \control_gen.dst_write ; //(module output)
  assign dout = \datapath_gen.dout ; //(module output)
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_top.vhd:44:9 */
  keccak_control_Bstruct control_gen (
    .clk(clk),
    .rst(rst),
    .src_ready(src_ready),
    .dst_ready(dst_ready),
    .final_segment(final_segment),
    .c(c),
    .d(d),
    .mode(mode),
    .src_read(\control_gen.src_read ),
    .dst_write(\control_gen.dst_write ),
    .clr_len(clr_len),
    .sel_dec_size(sel_dec_size),
    .last_word(last_word),
    .spos(spos),
    .ein(ein),
    .en_ctr(en_ctr),
    .en_len(en_len),
    .en_output_len(en_output_len),
    .sel_cin(),
    .sel_xor(sel_xor),
    .sel_final(sel_final),
    .ld_rdctr(ld_rdctr),
    .en_rdctr(en_rdctr),
    .wr_state(wr_state),
    .sel_out(sel_piso),
    .wr_piso(wr_piso),
    .mode_ctrl(mode_ctrl),
    .output_size(output_size),
    .last_out_word(last_out_word));
  /*# /workspace/scratch/8c6eb979d526/pqc-project/integrated/.pqc_runs/mldsa-portable-cjjutg8m/ref_combined/src/keccak_top.vhd:78:9 */
  keccak_datapath_Bstruct_3 datapath_gen (
    .clk(clk),
    .rst(rst),
    .din(din),
    .en_len(en_len),
    .en_output_len(en_output_len),
    .en_ctr(en_ctr),
    .ein(ein),
    .sel_xor(sel_xor),
    .sel_final(sel_final),
    .wr_state(wr_state),
    .ld_rdctr(ld_rdctr),
    .en_rdctr(en_rdctr),
    .clr_len(clr_len),
    .sel_dec_size(sel_dec_size),
    .spos(spos),
    .last_word(last_word),
    .sel_piso(sel_piso),
    .wr_piso(wr_piso),
    .mode_ctrl(mode_ctrl),
    .output_size(output_size),
    .last_out_word(last_out_word),
    .dout(\datapath_gen.dout ),
    .c(c),
    .d(d),
    .final_segment(final_segment),
    .mode(mode));
endmodule

