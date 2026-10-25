`timescale 1ns/1ps
module tb_makehint_read_view;
 reg clk=0,rst=0;
 reg [2:0] sec_lvl=2;
 reg [95:0] poly0_ie=0,poly1_ie=0;
 reg poly_valid_ie=0,hint_ready_o=0;
 wire [63:0] old_hint,new_hint;
 wire old_ready,new_ready,old_reject,new_reject,old_valid,new_valid;
 integer ctr_test,level_test,state_test,rej_test,pattern,k,checks=0;
 reg [31:0] rng=32'hbc243da7;
 makehint_reference reference_dut(.clk(clk),.rst(rst),.sec_lvl(sec_lvl),.poly0_ie(poly0_ie),.poly1_ie(poly1_ie),.poly_valid_ie(poly_valid_ie),.poly_ready_i(old_ready),.reject_hint(old_reject),.hint_o(old_hint),.hint_valid_o(old_valid),.hint_ready_o(hint_ready_o));
 makehint changed_dut(.clk(clk),.rst(rst),.sec_lvl(sec_lvl),.poly0_ie(poly0_ie),.poly1_ie(poly1_ie),.poly_valid_ie(poly_valid_ie),.poly_ready_i(new_ready),.reject_hint(new_reject),.hint_o(new_hint),.hint_valid_o(new_valid),.hint_ready_o(hint_ready_o));
 initial begin
  // Clock is intentionally held low. Exercise the combinational interface with
  // identical arbitrary sequential state in both implementations.
  for(pattern=0;pattern<4;pattern=pattern+1)begin
   for(k=0;k<80;k=k+1)begin
    rng=rng^(rng<<13);rng=rng^(rng>>17);rng=rng^(rng<<5);
    reference_dut.hint_addr[k]=rng;changed_dut.hint_addr[k]=rng;
   end
   for(k=0;k<8;k=k+1)begin
    reference_dut.poly_hint_cnt[k]=k*31+pattern;changed_dut.poly_hint_cnt[k]=k*31+pattern;
   end
   reference_dut.hint_addr[0]=8'bx;changed_dut.hint_addr[0]=8'bx;
   for(level_test=0;level_test<3;level_test=level_test+1)begin
    sec_lvl=(level_test==0)?2:(level_test==1)?3:5;
    for(state_test=0;state_test<2;state_test=state_test+1)begin
     reference_dut.state=state_test;changed_dut.state=state_test;
     for(rej_test=0;rej_test<2;rej_test=rej_test+1)begin
      reference_dut.rej=rej_test;changed_dut.rej=rej_test;
      for(ctr_test=0;ctr_test<256;ctr_test=ctr_test+1)begin
       reference_dut.ctr=ctr_test;changed_dut.ctr=ctr_test;
       #1;
       if({old_hint,old_ready,old_reject,old_valid}!=={new_hint,new_ready,new_reject,new_valid})
        $fatal(1,"hint view mismatch level=%0d state=%0d reject=%0d ctr=%0d",sec_lvl,state_test,rej_test,ctr_test);
       if((^{new_hint,new_ready,new_reject,new_valid}) === 1'bx)$fatal(1,"unknown observable output");
       checks=checks+1;
      end
     end
    end
   end
  end
  $display("ASIC_HINT_READ_VIEW_PASS exhaustive_control_cases=%0d",checks);
  $finish;
 end
endmodule
