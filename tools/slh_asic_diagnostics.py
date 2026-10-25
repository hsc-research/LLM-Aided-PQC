#!/usr/bin/env python3
"""Simulation-only consumed-read diagnostics for non-power-of-two SLH RAMs."""
from pathlib import Path
import difflib
import slh_asic_startup as boot

MONITOR = r'''
// Simulation-only monitor. The prior-cycle address belongs to registered q.
module slh_memory_watch #(parameter DEPTH=80, AW=7, NAME="memory")(
  input clk, enabled, input [AW-1:0] a0,a1, input w0,w1,consume0,consume1
);
  reg valid0=0,valid1=0;
  integer invalid_unconsumed=0,consumed=0,writes=0;
  always @(posedge clk) begin
    if (!enabled) begin valid0<=0;valid1<=0; end
    else begin
      if ((consume0 !== 1'b0 && consume0 !== 1'b1) || (consume1 !== 1'b0 && consume1 !== 1'b1))
        $fatal(1,"SLH unknown consumed-read control: %s",NAME);
      if (w0===1'b1 && w1===1'b1 && a0===a1)
        $fatal(1,"SLH undefined simultaneous dual write: %s",NAME);
      if (consume0 === 1'b1) begin
        consumed=consumed+1;
        if (valid0 !== 1'b1) $fatal(1,"SLH consumed invalid address: %s port0",NAME);
      end else if (valid0 !== 1'b1) invalid_unconsumed=invalid_unconsumed+1;
      if (consume1 === 1'b1) begin
        consumed=consumed+1;
        if (valid1 !== 1'b1) $fatal(1,"SLH consumed invalid address: %s port1",NAME);
      end else if (valid1 !== 1'b1) invalid_unconsumed=invalid_unconsumed+1;
      if(w0===1'b1) begin
        writes=writes+1;
        if((a0<=DEPTH)!==1'b1) $fatal(1,"SLH invalid write address: %s port0",NAME);
      end
      if(w1===1'b1) begin
        writes=writes+1;
        if((a1<=DEPTH)!==1'b1) $fatal(1,"SLH invalid write address: %s port1",NAME);
      end
      valid0 <= w0 ? 1'b1 : (a0<=DEPTH);
      valid1 <= w1 ? 1'b1 : (a1<=DEPTH);
    end
  end
  task report;
    begin $display("SLH_ASIC_ADDRESS_REPORT %s writes=%0d consumed=%0d invalid_unconsumed=%0d dual_write_collisions=0 unknown_consume=0 consumed_invalid=0",NAME,writes,consumed,invalid_unconsumed);end
  endtask
endmodule
'''

def diagnostics_variant(rtl,parameter):
    p=Path(rtl)/'sphincslet/tb.v';before=p.read_bytes();text=before.decode()
    tiles=['top_md0.hash_tile_md0'] if parameter=='128f' else ['top_md0.hash_tile_md0.DUT_SHA256','top_md0.hash_tile_md0.DUT_SHA512']
    instances=[];reports=[]
    hash_depth=80 if parameter=='128f' else 171
    w_depth=36 if parameter=='128f' else 52
    for n,tile in enumerate(tiles):
        for bank,short,gen,condition in [('SMALL_MEM','small','genblk1.HASH_SM','condition_s'),('BIG_MEM','big','genblk2.HASH_BM','condition_b')]:
            name=f'watch_{n}_{short}';h=tile+'.'+gen;m=tile+'.'+bank
            consume=f'(({tile}.mode == 0) && ({h}.shifter_init || {h}.shifter_next) && ({h}.append_mask_partial || (!{h}.append_mask && !{h}.append_zeros))) || {tile}.{condition}'
            instances.append(f'''slh_memory_watch #(.DEPTH({hash_depth}),.AW({hash_depth.bit_length()}),.NAME("tile{n}_{short}")) {name}(
.clk(clk),.enabled(boot_ready && !rst),.a0({m}.address_0),.a1({m}.address_1),.w0({m}.wren_0),.w1({m}.wren_1),.consume0({consume}),.consume1(1'b0));''')
            reports.append(f'    {name}.report();')
    m='top_md0.W_MEM';w='top_md0.wots_xmss_fsm_md0.md1'
    # Conservative over-approximation: every mode-0 active-WOTS q is counted,
    # including cycles in which an individual data/iteration guard ignores it.
    consume=f'({w}.WOTS_start && {w}.mode == 0)'
    consume1=f'({w}.i_wots_chain_flag && (({w}.opcode == 1 && {w}.chain_cnt != {w}.CC) || {w}.opcode == 4 || {w}.opcode == 6))'
    instances.append(f'''slh_memory_watch #(.DEPTH({w_depth}),.AW({w_depth.bit_length()}),.NAME("W_MEM")) watch_w(
.clk(clk),.enabled(boot_ready && !rst),.a0({m}.address_0),.a1({m}.address_1),.w0({m}.wren_0),.w1({m}.wren_1),.consume0({consume}),.consume1({consume1}));''')
    reports.append('    watch_w.report();')
    text=boot.replace(text,'    $finish;', '\n'.join(reports)+'\n    $finish;')
    text=boot.replace(text,'endmodule','\n'+'\n'.join(instances)+'\nendmodule')+MONITOR
    p.write_text(text)
    return [{'path':'sphincslet/tb.v','before_sha256':boot.sha(before),'after_sha256':boot.sha(p.read_bytes()),'derivative':'simulation_only_consumed_address_checks','diff':''.join(difflib.unified_diff(before.decode().splitlines(True),text.splitlines(True),fromfile='asic-widths/sphincslet/tb.v',tofile='asic-diagnostics/sphincslet/tb.v'))}]
