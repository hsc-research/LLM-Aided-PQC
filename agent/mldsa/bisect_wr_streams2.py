#!/usr/bin/env python3
import shutil, os, glob, subprocess, sys, re
BASE = "/mnt/c/PQC/hqc/agent/mldsa"
ED = BASE + "/mldsa_src"
PRISTINE = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src"
DBG = '''
    // DEBUG WRITE/READ STREAM DUMP
    integer dbg_w = 0;
    always @(posedge clk) begin
        if (web1 && dbg_w < 20000) begin
            $display("WR1 %m %0d %h %h", mode, addrb1, dib1); dbg_w = dbg_w + 1;
        end
        if (web2 && dbg_w < 20000) begin
            $display("WR2 %m %0d %h %h", mode, addrb2, dib2); dbg_w = dbg_w + 1;
        end
        if (en_addr && dbg_w < 20000) begin
            $display("RDA %m %0d %h", mode, addra1); dbg_w = dbg_w + 1;
        end
    end
endmodule'''
def build(name, use_edited):
    d = os.path.join(BASE, name)
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for p in glob.glob(ED + "/*.v"):
        shutil.copy(p, d)
    for b in ("butterfly.v", "butterfly2x2.v", "operation_module.v"):
        shutil.copy(os.path.join(PRISTINE, b), d)
    if use_edited:
        for scr in ("apply_butterfly_dsp.py", "apply_bf2x2_zeta.py", "apply_opmod_retap.py", "apply_butterfly_areg.py"):
            r = subprocess.run([sys.executable, os.path.join(BASE, scr), d],
                               capture_output=True, text=True)
            assert r.returncode == 0, f"{scr} failed: {r.stdout[-300:]}{r.stderr[-300:]}"
        bt = open(os.path.join(d, "butterfly.v")).read()
        assert bt.count("mult_p") >= 3, "butterfly edit missing"
    f = os.path.join(d, "operation_module.v")
    s = open(f).read()
    assert s.count("endmodule") == 1
    open(f, "w").write(s.replace("endmodule", DBG))
    return d
dp = build("dbg_pristine", False)
de = build("dbg_edited",  True)
def run(d, tag):
    subprocess.run([sys.executable, BASE + "/full_kat_gate.py", d,
                    "--vectors", "1"], capture_output=True, text=True)
    shutil.copy(BASE + "/fullkat_run.log", BASE + f"/dbglogw_{tag}.log")
run(dp, "pristine")
run(de, "edited")
def parse(path):
    streams = {}
    for line in open(path):
        m = re.match(r"(WR[12]|RDA) (\S+) (\d+) (.*)", line.strip())
        if m:
            key = (m.group(1), m.group(3))  # (port, mode)
            streams.setdefault(key, []).append(m.group(4))
    return streams
sp, se = parse(BASE + "/dbglogw_pristine.log"), parse(BASE + "/dbglogw_edited.log")
print("=== WR/RD STREAM COMPARE (port/mode, latency-agnostic) ===")
for key in sorted(set(sp) | set(se)):
    a, b = sp.get(key, []), se.get(key, [])
    n = min(len(a), len(b))
    div = next((i for i in range(n) if a[i] != b[i]), None)
    status = f"DIVERGE@{div}" if div is not None else f"match({n})"
    print(f"{key}: p={len(a)} e={len(b)} {status}")
    if div is not None:
        for j in range(max(0,div-3), min(div+4, n)):
            mk = "->" if j == div else "  "
            print(f" {mk}[{j}] p:{a[j]}  e:{b[j]}")
