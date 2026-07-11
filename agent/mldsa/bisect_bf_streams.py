#!/usr/bin/env python3
import shutil, os, glob, subprocess, sys, re
BASE = "/mnt/c/PQC/hqc/agent/mldsa"
ED = BASE + "/mldsa_src"
PRISTINE = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src"

DBG = '''
    // DEBUG STREAM DUMP
    integer dbg_i = 0, dbg_o = 0;
    always @(posedge clk) begin
        if (validi && dbg_i < 3000) begin
            $display("BFI %m %0d %h %h %h", mode, datai, zetai, acci);
            dbg_i = dbg_i + 1;
        end
        if (valido && dbg_o < 3000) begin
            $display("BFO %m %0d %h", mode, datao);
            dbg_o = dbg_o + 1;
        end
    end
endmodule'''

def build(name, use_edited):
    d = os.path.join(BASE, name)
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for p in glob.glob(ED + "/*.v"):
        shutil.copy(p, d)
    # base state for the 3 target files: PRISTINE originals (never mldsa_src, never parked)
    for b in ("butterfly.v", "butterfly2x2.v", "operation_module.v"):
        shutil.copy(os.path.join(PRISTINE, b), d)
    if use_edited:
        # construct edited by RUNNING the apply scripts against this dir
        for scr in ("apply_butterfly_dsp.py", "apply_bf2x2_zeta.py", "apply_opmod_retap.py"):
            r = subprocess.run([sys.executable, os.path.join(BASE, scr), d],
                               capture_output=True, text=True)
            assert r.returncode == 0, f"{scr} failed: {r.stdout[-300:]}{r.stderr[-300:]}"
        # verify edit markers actually present
        bt = open(os.path.join(d, "butterfly.v")).read()
        b2 = open(os.path.join(d, "butterfly2x2.v")).read()
        om = open(os.path.join(d, "operation_module.v")).read()
        assert bt.count("mult_p") >= 3, "butterfly edit missing"
        assert "z2_sr[9]" in b2 or "[9:0]" in b2, "bf2x2 edit missing"
        assert "addr1_sr[23]" in om, "opmod edit missing"
    f = os.path.join(d, "butterfly2x2.v")
    s = open(f).read()
    assert s.count("endmodule") == 1
    open(f, "w").write(s.replace("endmodule", DBG))
    return d

dp = build("dbg_pristine", False)
de = build("dbg_edited",  True)

def run(d, tag):
    r = subprocess.run([sys.executable, BASE + "/full_kat_gate.py", d,
                        "--vectors", "1"], capture_output=True, text=True)
    shutil.copy(BASE + "/fullkat_run.log", BASE + f"/dbglog_{tag}.log")
    print(tag, "gate exit:", r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[-200:])

run(dp, "pristine")
run(de, "edited")

def parse(path):
    streams = {}
    for line in open(path):
        m = re.match(r"(BFI|BFO) (\S+) (\d+) (.*)", line.strip())
        if m:
            key = (m.group(2), m.group(1))  # (instance, dir)
            streams.setdefault(key, []).append((m.group(3), m.group(4)))
    return streams

sp, se = parse(BASE + "/dbglog_pristine.log"), parse(BASE + "/dbglog_edited.log")
print("\n=== STREAM COMPARE (latency-agnostic) ===")
for key in sorted(set(sp) | set(se)):
    a, b = sp.get(key, []), se.get(key, [])
    n = min(len(a), len(b))
    div = next((i for i in range(n) if a[i] != b[i]), None)
    status = f"DIVERGE@{div}" if div is not None else f"match({n})"
    print(f"{key[0]} {key[1]}: pristine={len(a)} edited={len(b)} {status}")
    if div is not None:
        print(f"   pristine[{div}]: {a[div]}")
        print(f"   edited  [{div}]: {b[div]}")
        for j in range(max(0,div-2), div):
            print(f"   ctx[{j}] p:{a[j]}  e:{b[j]}")
