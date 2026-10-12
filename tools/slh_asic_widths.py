#!/usr/bin/env python3
"""Explicit, value-preserving ASIC elaboration widths after boot/control ports.

Makes original Verilog port truncations/constant widths explicit. Does not
replace out-of-range data with zeros; use selected-hierarchy deferred parsing.
"""
from pathlib import Path
import re
import difflib
import slh_asic_startup as startup
PINS={'sphincslet/top.v': 'e800468afd92d1a96b91afd9cc3a794742a8cf366f08e10ef599ebe8b8af7409', 'sphincslet/hash_tile/two_hash_tile.v': 'f1ba41034467581e2aa677444d849483c893acb7f5faa26bdc2c06c9ab569fdc', 'sphincslet/hash_tile/hash_tile.v': '9b17aac480681e7fc01a43ac764549251d1ca0102b5e88bf10881da9bfce25b0', 'sphincslet/hash_tile/hash_mem_interface_sha.v': '678b1f5a30291e21517bbd17eec90fd62f3fee5755bff1d1add7de785fb4196a', 'sphincslet/fsm/FSM.v': '1ffe81f373b7950adc3cfd13c81b7c9d09fde4f7ab02c1e6779ce1d6f929b940', 'sphincslet/fsm/XMSS_FSM.v': 'edd693bb2fa2321ae84534c64a315ae5fc71ccf8dfce8be59d7aa04cf77afb09'}

def width_variant(rtl):
    changes=[]
    for name,wanted in PINS.items():
        p=Path(rtl)/name;before=p.read_bytes()
        if startup.sha(before)!=wanted:raise ValueError('ASIC width input differs from reviewed bytes: '+name)
        text=before.decode()
        if name.endswith('/top.v') or name.endswith('/two_hash_tile.v'):
            text,n=re.subn(r'(\.i_[sb]_rd_en\s*\()0(\s*\))',r"\g<1>1'b0\2",text)
            if n!=4:raise ValueError('read-enable width anchors changed')
            if name.endswith('/top.v'):
                text=startup.replace(text,'wire [INDICE_WD-1:0] indices_mem_in0;', '''wire [INDICE_WD-1:0] indices_mem_in0;
// The 128f vendor producer exposes 15 bits; its consumer kept the low 12.
wire [((parameter_set == "128f") ? 15 : INDICE_WD)-1:0] indices_mem_full;
assign indices_mem_in0 = indices_mem_full[INDICE_WD-1:0];''')
                text=startup.replace(text,'.o_data0       (indices_mem_in0         )','.o_data0       (indices_mem_full        )')
                text=startup.replace(text,".data_1   (19'd0            )",".data_1   ({INDICE_WD{1'b0}})")
        elif name.endswith('/hash_tile.v'):
            text=startup.replace(text,'.i_start(mode == STREAMING? 0 : b_h_start)',".i_start(mode == STREAMING? 1'b0 : b_h_start)",2)
            for signal in ('condition_s_wen2','condition_s_wen2_d'):
                text=startup.replace(text,'.wren_1(i_b_wr_en? 1 : '+signal+'? 1 : 0)',".wren_1(i_b_wr_en? 1'b1 : "+signal+"? 1'b1 : 1'b0)")
        elif name.endswith('/hash_mem_interface_sha.v'):
            text=startup.replace(text,'.work_factor(0)',".work_factor(1'b0)")
        elif name.endswith('/FSM.v'):
            # Only XMSS narrows layer_addr; WOTS retains its full 32-bit port.
            text=startup.replace(text,'.layer_addr      (layer_addr_reg    )','.layer_addr      (layer_addr_reg[7:0])')
            text=startup.replace(text,'.HT_mode         (mode          )','.HT_mode         (mode[0]       )')
        elif name.endswith('/XMSS_FSM.v'):
            text=startup.replace(text,'wire                     LR_flag2;', 'wire                     LR_flag2;\nwire                     LR_flag2_pre; // existing driven one-bit net, now explicit')
        else:raise ValueError('unexpected ASIC width file')
        p.write_text(text)
        changes.append({'path':name,'before_sha256':startup.sha(before),'after_sha256':startup.sha(p.read_bytes()),
            'derivative':'explicit_original_port_truncations_and_constant_widths',
            'diff':''.join(difflib.unified_diff(before.decode().splitlines(True),text.splitlines(True),fromfile='asic-control-ff/'+name,tofile='asic-explicit-widths/'+name))})
    return changes
