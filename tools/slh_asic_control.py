#!/usr/bin/env python3
"""Explicit ASIC-only latch lowering, separate from boot initialization.

Hash-tile invalid states gain safe combinational defaults; reset and all legal
transitions restrict state to 0..7. XMSS retains history using a clocked register
and combinational bypass. Equivalence is at settled/sampled clock cycles with
its existing posedge-owned decoder inputs, not arbitrary asynchronous inputs.
"""
from pathlib import Path
import re
import difflib
import slh_asic_startup as startup
PINS = {'sphincslet/hash_tile/hash_tile.v': 'c9b4c3bf675d4b56576f38070eac888aa83219ee397811983ea3369a16137003', 'sphincslet/fsm/XMSS_FSM.v': '9afd281ee04338911c265674cbb6f47e5151bffeb91f4349e098394ed3fd3e26'}

def control_variant(rtl):
    changes=[]
    for name,wanted in PINS.items():
        p=Path(rtl)/name;before=p.read_bytes()
        if startup.sha(before)!=wanted:raise ValueError('ASIC control input differs from reviewed bytes: '+name)
        text=before.decode()
        if name.endswith('/hash_tile.v'):
            anchor='''    default: begin
        s_h_start <= 0;
        b_h_start <= 0;
        done_reg <= 0;
'''
            text=startup.replace(text,anchor,anchor+'''        // Unreachable after reset: every legal transition assigns state 0..7.
        output_enable <= 0;
        s_h_ADDR_update <= 0;
''')
        else:
            anchor='''`else
always@(cnt, ch_cnt, LR_flag, LR_flag2, hash_done_1d, flag_last, XMSS_start) begin
    case(cnt)
    4'd4: begin'''
            replacement='''`else
// SHA2 decoder sources cnt/ch_cnt/XMSS_start/LR_flag2 are posedge registers.
// Capture the previous settled output before those sources update, retaining
// the vendor's cnt=4/5, !XMSS_start hold behavior without a transparent latch.
reg sig_read_history;
always @(posedge clk or negedge rstn) begin
    if (!rstn) sig_read_history <= 1'b0;
    else sig_read_history <= o_sig_read_mem_r;
end
always @(*) begin
    o_sig_read_mem_r = sig_read_history;
    case(cnt)
    4'd4: begin'''
            text=startup.replace(text,anchor,replacement)
            # Only this SHA2 decoder becomes blocking combinational assignments.
            pos=text.index(replacement);end=text.index('\n`endif',pos)
            text=text[:pos]+text[pos:end].replace('o_sig_read_mem_r <=','o_sig_read_mem_r =')+text[end:]
        p.write_text(text)
        changes.append({'path':name,'before_sha256':startup.sha(before),'after_sha256':startup.sha(p.read_bytes()),
            'derivative':'asic_clocked_history_and_illegal_state_defaults',
            'diff':''.join(difflib.unified_diff(before.decode().splitlines(True),text.splitlines(True),fromfile='asic-boot/'+name,tofile='asic-boot-control-ff/'+name))})
    return changes
