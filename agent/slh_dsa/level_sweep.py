#!/usr/bin/env python3
"""SLH-DSA security-level sweep: all six SLH-DSA parameter sets, both arms.

For each of 128s/128f/192s/192f/256s/256f:
  1. stage a scratch tree with setting.v switched to that parameter set
  2. BASELINE arm: gate (generates the golden signature for this level),
     regen checkpoint, bracket probe, closure search
  3. OPTIMIZED arm: same, but the tree carries the CSA edit. The gate must
     reproduce the BASELINE golden signature bit-for-bit; the arms differ
     only in adder structure, so their signatures must be identical.

Baseline runs first at every level, because the optimized arm is judged
against the golden the baseline produced. A level whose baseline gate fails
is skipped entirely rather than measured.

Nothing here touches agent/slh_dsa/pristine or agent/slh_dsa/slh_src. Each
config gets its own scratch tree under /mnt/c/PQC/slh_sweep/<cfg>_<arm>/.

Usage:
  python3 agent/slh_dsa/level_sweep.py [cfg ...]     default: all six
  python3 agent/slh_dsa/level_sweep.py --probe-only  brackets only, no closure
"""
import os, re, sys, json, glob, time, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
os.chdir(REPO)

CFGS = ["128s", "128f", "192s", "192f", "256s", "256f"]
ARMS = ["baseline", "optimized"]
SRC = {"baseline": os.path.join(REPO, "agent/slh_dsa/pristine"),
       "optimized": os.path.join(REPO, "agent/slh_dsa/slh_src")}

SWEEP = "/mnt/c/PQC/slh_sweep"
SIMD  = "/mnt/c/PQC/slh_sim/a/b/c/d"
DATA  = "/mnt/c/PQC/slh_sim/TECS_v8.srcs/sources_1/imports/data_sha2"
GOLD  = os.path.join(REPO, "agent/slh_dsa/gate/levels")
OUT   = os.path.join(HERE, "level_sweep_results.jsonl")
PART  = "xc7a200tfbg676-1"

# Brackets are PROVEN per config, not assumed: the probe asserts LO violates
# and HI meets before any search runs (F12). These are only starting guesses;
# the prober widens until both ends are proven.
GUESS = {"128s": (10.0, 14.0), "128f": (10.0, 14.0),
         "192s": (10.0, 16.0), "192f": (10.0, 16.0),
         "256s": (10.0, 18.0), "256f": (10.0, 18.0)}


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def stage(cfg, arm):
    """Scratch tree = arm source with setting.v switched to cfg."""
    d = f"{SWEEP}/{cfg}_{arm}"
    if os.path.exists(d):
        shutil.rmtree(d)
    shutil.copytree(SRC[arm], d)
    p = f"{d}/sphincslet/setting.v"
    s = open(p).read()
    for c in CFGS:
        tok = f"`define PARAM_{c.upper()}"
        s = s.replace(f"//{tok}\n", f"{tok}\n").replace(f"{tok}\n", f"//{tok}\n")
    tok = f"`define PARAM_{cfg.upper()}"
    assert s.count(f"//{tok}\n") == 1, f"{cfg}: expected exactly one commented {tok}"
    s = s.replace(f"//{tok}\n", f"{tok}\n")
    enabled = [c for c in CFGS if re.search(rf"^`define PARAM_{c.upper()}$", s, re.M)]
    assert enabled == [cfg], f"{cfg}: enabled set is {enabled}"
    open(p, "w").write(s)
    return d


def gate(rtl, cfg, arm):
    """Run the vendor testbench. Baseline freezes the golden; optimized
    must reproduce it byte-for-byte."""
    gold = f"{GOLD}/SIG_{cfg}.hex"
    produced = f"{DATA}/SIG_file0_{cfg}_w.hex"
    if os.path.exists(produced):
        os.remove(produced)
    env = dict(os.environ, SLH_RTL=rtl)
    r = sh(["bash", f"{SIMD}/run_sim.sh"], cwd=SIMD, env=env, timeout=7200)
    ok_compile = "xvlog errors: 0" in r.stdout and "xelab errors: 0" in r.stdout
    if not ok_compile:
        return {"status": "ERROR", "reason": "compile/elab errors"}
    if not os.path.exists(produced):
        return {"status": "FAIL", "reason": "no signature produced"}
    if "The signature is matched" not in r.stdout:
        return {"status": "FAIL", "reason": "verify did not report match"}
    if arm == "baseline":
        os.makedirs(GOLD, exist_ok=True)
        shutil.copy(produced, gold)
        return {"status": "PASS", "reason": "golden frozen", "golden": gold}
    if not os.path.exists(gold):
        return {"status": "ERROR", "reason": "no baseline golden for this cfg"}
    same = open(gold, "rb").read() == open(produced, "rb").read()
    return {"status": "PASS" if same else "FAIL",
            "reason": "matches baseline golden" if same else "signature differs from baseline golden"}


def regen(rtl, ckpt, period=14.0):
    r = sh(["python3", "agent/slh_dsa/regen_slh_ckpt.py", rtl, ckpt], timeout=7200)
    return "wrote" in r.stdout, r.stdout[-400:]


def route_at(ckpt, period, tag):
    """One place-and-route at a fixed period. Returns WNS or None."""
    rpt = f"/tmp/sweep_{tag}_{period:.2f}.rpt"
    tcl = f"""open_checkpoint {ckpt}
create_clock -period {period:.3f} -name clk [get_ports clk]
catch {{opt_design}}
place_design -directive ExtraTimingOpt
phys_opt_design -directive Explore
route_design -directive Explore
report_timing_summary -file {rpt}
report_utilization -file {rpt}.util
puts "SWEEP POINT DONE"
"""
    tf = f"/tmp/sweep_{tag}.tcl"
    open(tf, "w").write(tcl)
    sh(["vivado", "-mode", "batch", "-source", tf, "-nojournal", "-nolog"], timeout=7200)
    if not os.path.exists(rpt):
        return None
    m = re.search(r"^\s*(-?[\d.]+)\s+(-?[\d.]+)\s+\d+\s+\d+", open(rpt).read(), re.M)
    return float(m.group(1)) if m else None


def prove_bracket(ckpt, tag, lo, hi):
    """F12: LO must VIOLATE and HI must MEET. Widen until both hold."""
    for _ in range(4):
        w_hi = route_at(ckpt, hi, tag)
        if w_hi is None:
            return None
        if w_hi < 0:
            hi += 2.0
            continue
        break
    else:
        return None
    for _ in range(4):
        w_lo = route_at(ckpt, lo, tag)
        if w_lo is None:
            return None
        if w_lo >= 0:
            lo -= 2.0
            if lo <= 1.0:
                return None
            continue
        break
    else:
        return None
    return (lo, hi)


def closure(ckpt, tag, lo, hi):
    r = sh(["python3", "agent/fmax_search.py", ckpt, tag, str(lo), str(hi)], timeout=28800)
    m = re.search(r'\{.*"closing_period_ns".*\}', r.stdout)
    return json.loads(m.group(0)) if m else None


def rec(d):
    d["ts"] = time.strftime("%F %T")
    with open(OUT, "a") as f:
        f.write(json.dumps(d) + "\n")
    print("REC:", json.dumps({k: d[k] for k in ("cfg", "arm", "status") if k in d}))
    return d


def main():
    cfgs = [a for a in sys.argv[1:] if a in CFGS] or CFGS
    probe_only = "--probe-only" in sys.argv
    os.makedirs(SWEEP, exist_ok=True)

    for cfg in cfgs:
        for arm in ARMS:                       # baseline ALWAYS first
            tag = f"slh_{cfg}_{arm}"
            print(f"\n===== {cfg} {arm} =====", flush=True)
            rtl = stage(cfg, arm)

            g = gate(rtl, cfg, arm)
            print(f"gate: {g['status']} ({g['reason']})", flush=True)
            if g["status"] != "PASS":
                rec({"cfg": cfg, "arm": arm, "status": "gate_" + g["status"].lower(),
                     "reason": g["reason"], "rtl": rtl})
                if arm == "baseline":
                    print(f"{cfg}: baseline gate failed, skipping optimized arm")
                    break
                continue

            ckpt = f"/mnt/c/PQC/slh_test/sweep_{cfg}_{arm}.dcp"
            ok, msg = regen(rtl, ckpt)
            if not ok:
                rec({"cfg": cfg, "arm": arm, "status": "regen_fail",
                     "reason": msg, "rtl": rtl})
                continue

            br = prove_bracket(ckpt, tag, *GUESS[cfg])
            if not br:
                rec({"cfg": cfg, "arm": arm, "status": "bracket_fail",
                     "reason": "could not prove a bracket", "rtl": rtl})
                continue
            print(f"bracket proven: {br}", flush=True)

            if probe_only:
                rec({"cfg": cfg, "arm": arm, "status": "bracket_only",
                     "bracket": br, "ckpt": ckpt, "rtl": rtl})
                continue

            c = closure(ckpt, tag, *br)
            if not c:
                rec({"cfg": cfg, "arm": arm, "status": "closure_fail",
                     "bracket": br, "rtl": rtl})
                continue
            rec({"cfg": cfg, "arm": arm, "status": "OK", "bracket": br,
                 "closure": c, "ckpt": ckpt, "rtl": rtl, "gate": g,
                 "tag": tag})

    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
