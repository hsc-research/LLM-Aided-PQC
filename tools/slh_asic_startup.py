#!/usr/bin/env python3
"""Reviewed, fail-closed ASIC boot transform of corrected portable SLH RTL.

Only disposable staged trees are supported. Never changes the FPGA source trees.
The templates are synthesizable RTL; no memory compiler, initialization file,
power-up value or technology library is used.
"""
from pathlib import Path
import difflib
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'asic/rtl/slh_startup'
# Hash-pinned corrected portable inputs, common to both qualified SHA variants.
PINS = {'imports/mem_dual.v': 'cc473dbdda4f8b27b3cc2f1ba4f63a89906151898d64c361d916085c06cc469b', 'imports/mem_single.v': 'f685a74dc32dfc9275984a8f4e7bb921b3427d6841a4f4d12a54c5fc8a2e1d50', 'imports/fifo.v': '4b78d74a860211e1e623778c3b4615286be965512bb00e3fd91c2939fdf87a2b', 'sphincslet/top.v': 'f98db6f0a6785a2a50d861bea3bea4c73f0b613950875e40935a71185e8225fc', 'sphincslet/hash_tile/hash_tile.v': '8269a3c06ac080a201817726898d5ee358168e6efb1e9d55e82cfe005ca1c2bb', 'sphincslet/hash_tile/two_hash_tile.v': 'beefe895e6f7c31212b9e1d7fbe228944e21cde04a05f954a42ea67995b35a67', 'sphincslet/hash_tile/hash_mem_interface_sha.v': 'a87cb87a1c55efa2c197fcdd4e1f113205290ef098facbda6c3845843c1a692a', 'sphincslet/hash_tile/hash_mem_interface_shake256.v': 'b36666e4f5fe040edf767df832776d0e260a6f98d226dd2dfef26e7b36a02449', 'sphincslet/tb.v': '653e8f68b76875004ae278374b73e172c09e6327d3e46f66d8454e8bb34f20a8'}

def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace(text, old, new, count=1):
    if text.count(old) != count:
        raise ValueError('ASIC startup transformation anchor changed: ' + repr(old))
    return text.replace(old, new)


def add_ports(text, reset):
    pattern = r'(input\s+wire\s+' + reset + r'\s*,)'
    text, count = re.subn(pattern, r'\1\ninput wire i_boot_reset,\noutput wire o_boot_ready,', text)
    if count != 1:
        raise ValueError('ASIC boot port anchor changed')
    return text


def body_start(text):
    return text.index(');', text.index('module ')) + 2


def boot_variant(rtl):
    """Apply the startup derivative after select_parameter/portability/auth fixes."""
    rtl = Path(rtl)
    changes = []
    for name, wanted in PINS.items():
        path = rtl / name
        before = path.read_bytes()
        if sha(before) != wanted:
            raise ValueError('ASIC startup input differs from reviewed corrected bytes: ' + name)
        text = before.decode()
        if name in ('imports/mem_dual.v', 'imports/mem_single.v', 'imports/fifo.v'):
            text = (TEMPLATES / Path(name).name).read_text()
        elif name.endswith('/top.v'):
            text = add_ports(text, 'rstn')
            pos = body_start(text)
            body = text[pos:]
            body = re.sub(r'\brstn\b', 'core_rstn', body)
            body = re.sub(r'\bi_FSM_start\b', 'core_start', body)
            body = re.sub(r'\bo_sig_valid\b', 'core_sig_valid', body)
            body = re.sub(r'\bo_FSM_done\b', 'core_done', body)
            # Port names must retain the callee's original interface.
            for port, internal in [('rstn','core_rstn'),('i_FSM_start','core_start'),
                                   ('o_sig_valid','core_sig_valid'),('o_FSM_done','core_done')]:
                body = re.sub(r'\.' + internal + r'\b', '.' + port, body)
            declarations = '''
// Boot is separate from ordinary operation reset. Do not issue/load until ready.
wire hash_boot_ready;
assign o_boot_ready = hash_boot_ready && !i_boot_reset;
wire core_rstn = rstn && o_boot_ready;
wire core_start = i_FSM_start && o_boot_ready;
wire core_sig_valid;
wire core_done;
assign o_sig_valid = core_sig_valid && o_boot_ready;
assign o_FSM_done = core_done && o_boot_ready;
'''
            text = text[:pos] + declarations + body
            text = replace(text, 'if(seed_valid) begin', 'if(seed_valid && o_boot_ready) begin')
            pattern = r'(hash_tile_md0\s*\(\s*)'
            text, n = re.subn(pattern, r'\1.i_boot_reset(i_boot_reset),\n.o_boot_ready(hash_boot_ready),\n', text)
            if n != 3: raise ValueError('top hash instance count changed')
            for inst in ('H_MSG_MEM', 'INDICES_MEM', 'W_MEM', 'MEM_64BIT_1'):
                text, n = re.subn(r'(' + inst + r'\s*\(\s*)',
                                  r'\1.i_boot_reset(i_boot_reset || !o_boot_ready),\n.o_boot_ready(),\n', text)
                if n != 1: raise ValueError('top memory instance changed: ' + inst)
        elif name.endswith('/two_hash_tile.v'):
            text = add_ports(text, 'rst')
            pos = body_start(text)
            text = text[:pos] + '''
wire boot_ready_sha256, boot_ready_sha512;
assign o_boot_ready = boot_ready_sha256 && boot_ready_sha512 && !i_boot_reset;
''' + text[pos:]
            for inst, signal in [('DUT_SHA256','boot_ready_sha256'),('DUT_SHA512','boot_ready_sha512')]:
                text, n = re.subn(r'(' + inst + r'\s*\(\s*)',
                                  r'\1.i_boot_reset(i_boot_reset),\n.o_boot_ready(' + signal + '),\n', text)
                if n != 1: raise ValueError('two-hash instance changed')
        elif name.endswith('/hash_tile.v'):
            text = add_ports(text, 'rst')
            pos = body_start(text)
            body = re.sub(r'\brst\b', 'core_rst', text[pos:])
            body = re.sub(r'\.core_rst\b', '.rst', body)
            text = text[:pos] + '''
wire small_boot_ready, big_boot_ready;
assign o_boot_ready = small_boot_ready && big_boot_ready && !i_boot_reset;
wire core_rst = rst || !o_boot_ready;
''' + body
            text = replace(text, 'reg [2:0] m_s_state = 0;',
                           'reg [2:0] m_s_state; // initialized by existing synchronous reset')
            for inst, signal in [('SMALL_MEM','small_boot_ready'),('BIG_MEM','big_boot_ready')]:
                text, n = re.subn(r'(' + inst + r'\s*\(\s*)',
                                  r'\1.i_boot_reset(i_boot_reset),\n.o_boot_ready(' + signal + '),\n', text)
                if n != 1: raise ValueError('hash memory instance changed')
            text = replace(text, '.i_clk(clk),', '.i_clk(clk),\n    .i_boot_reset(!o_boot_ready),', 2)
        elif name.endswith('/hash_mem_interface_sha.v'):
            text = replace(text, 'reg [3:0] h_state                  =   0;',
                           'reg [3:0] h_state; // initialized by existing synchronous reset')
        elif name.endswith('/hash_mem_interface_shake256.v'):
            text = replace(text, 'reg [2:0] h_state              =   0;',
                           'reg [2:0] h_state; // initialized by existing synchronous reset')
        elif name.endswith('/tb.v'):
            text = replace(text, 'reg rst;', 'reg rst;\nreg boot_reset;\nwire boot_ready;')
            text = replace(text, 'top_md0 (', 'top_md0 (\n.i_boot_reset(boot_reset),\n.o_boot_ready(boot_ready),')
            text = replace(text, "    rst <= 1'b1;\n    FSM_start <= 1'b0;\n    #100; \n    rst <= 1'b0;", '''    rst <= 1'b1;
    boot_reset <= 1'b1;
    FSM_start <= 1'b0;
    #100;
    boot_reset <= 1'b0;
    wait (boot_ready === 1'b1);
    @(negedge clk);
    $display("SLH_ASIC_BOOT_READY");
    rst <= 1'b0;''')
            # The testbench-only signature RAM is INIT=0 and has no startup state.
            text, n = re.subn(r'(SIG_MEM\s*\(\s*)',
                              r'\1.i_boot_reset(boot_reset || !boot_ready),\n.o_boot_ready(),\n', text)
            if n != 1: raise ValueError('signature memory instance changed')
            text += '''
// The testbench is outside the design and does not synthesize.
'''
        else:
            raise ValueError('unexpected ASIC transform file: ' + name)
        path.write_text(text)
        changes.append({'path': name, 'before_sha256': sha(before), 'after_sha256': sha(path.read_bytes()),
                        'diff': ''.join(difflib.unified_diff(before.decode().splitlines(True), text.splitlines(True),
                                                          fromfile='corrected-portable/'+name, tofile='asic-boot/'+name))})
    return changes
