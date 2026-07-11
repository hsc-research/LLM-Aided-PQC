#!/usr/bin/env python3
import shutil, os, glob, subprocess, sys, re
BASE = "/mnt/c/PQC/hqc/agent/mldsa"
ED, PK = BASE + "/mldsa_src", BASE + "/parked"

DBG = '''
    // DEBUG WRITE-STREAM DUMP
    integer dbg_w = 0;
    always @(posedge clk) begin
        if (web1 && dbg_w < 20000) begin
            $display("WR1 %m %0d %h %h", mode, addrb1, dib1); dbg_w = dbg_w + 1;
        end
        if (web2 && dbg_w < 20000) begin
            $display("WR2 %m %0d %h %h", mode, addrb2, dib2); dbg_w = dbg_w + 1;
        end
    end
endmodule'''

def build(name, use_edited):
    d = os.path.join(BASE, name)
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for p in glob.glob(ED + "/*.v"):
        shutil.copy(p, d)
    if use_edited:
        for b in ("butterfly.v", "butterfly2x2.v", "operation_module.v"):
            shutil.copy(os.path.join(PK, b), d)
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
    shutil.copy(BASE + "/fullkat_run.log", BASE + f"/dbglog_{tag}.log")

run(dp, "pristine")
run(de, "edited")

def parse(path):
    streams = {}
    for line in open(path):
        m = re.match(r"(WR[12]) (\S+) (\d+) (\S+) (\S+)", line.strip())
        if m:
            key = (m.group(2), m.group(1), m.group(3))  # (inst, port, mode)
            streams.setdefault(key, []).append((m.group(4), m.group(5)))
    return streams

sp, se = parse(BASE + "/dbglog_pristine.log"), parse(BASE + "/dbglog_edited.log")
print("=== WRITE STREAM COMPARE (inst/port/mode, latency-agnostic) ===")
for key in sorted(set(sp) | set(se)):
    a, b = sp.get(key, []), se.get(key, [])
    n = min(len(a), len(b))
    div = next((i for i in range(n) if a[i] != b[i]), None)
    status = f"DIVERGE@{div}" if div is not None else f"match({n})"
    print(f"{key}: p={len(a)} e={len(b)} {status}")
    if div is not None:
        for j in range(max(0,div-2), min(div+3, n)):
            mk = "->" if j == div else "  "
            print(f" {mk}[{j}] p:{a[j]}  e:{b[j]}")
