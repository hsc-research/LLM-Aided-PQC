#!/usr/bin/env python3
"""Tier-3: agent-driven implementation-flow search. Sonnet proposes the next
place/phys_opt/route directive combo from the sweep history; deterministic
code validates, runs (reusing post-synth checkpoint), logs. Model is
untrusted: proposals outside the legal vocabulary are refused.
Usage: python3 agent/flow_orchestrator.py <module> <period> [--pristine] [--max-runs N]
Requires: synth_out/sweep_<key>/post_synth.dcp (run flow_sweep.py once first,
or this script synthesizes the checkpoint if missing).
"""
import sys, os, re, json, time, subprocess, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from synthesizer import MODULE_SOURCES, VHDL_SOURCES, PART, TOP_OVERRIDE

MODEL = "claude-sonnet-4-5"
API_KEY = os.environ.get("ANTHROPIC_API_KEY") or open(os.path.expanduser("~/.anthropic_key")).read().strip()
LOG = os.path.join(HERE, "flow_sweep_log.jsonl")

PLACE = ["Default","Explore","ExtraNetDelay_high","ExtraNetDelay_low",
         "SSI_SpreadLogic_high","SSI_SpreadLogic_low","AltSpreadLogic_high",
         "AltSpreadLogic_medium","AltSpreadLogic_low","ExtraPostPlacementOpt",
         "ExtraTimingOpt","SpreadSLLs","BalanceSLLs","EarlyBlockPlacement"]
PHYS  = ["Default","Explore","AggressiveExplore","AggressiveFanoutOpt",
         "AlternateReplication","AddRetime","ExploreWithHoldFix"]
ROUTE = ["Default","Explore","AggressiveExplore","NoTimingRelaxation",
         "MoreGlobalIterations","HigherDelayCost","AlternateCLBRouting"]

def history(key, period):
    h = []
    if os.path.exists(LOG):
        for ln in open(LOG):
            try: r = json.loads(ln)
            except: continue
            if r.get("module") == key and abs(r.get("period",0) - period) < 1e-6:
                h.append(r)
    return h

def ask(key, period, hist):
    tried = [(r["place"], r["phys_opt"], r["route"]) for r in hist]
    hist_txt = "\n".join(f"- {r['place']}/{r['phys_opt']}/{r['route']}: "
                         f"fmax {r.get('fmax_mhz')} MHz (WNS {r.get('wns')})"
                         for r in hist)
    prompt = f"""You are searching Vivado implementation directives for {key} on {PART}, clock period {period} ns.

TRIED SO FAR (do not repeat):
{hist_txt}

VALID VOCABULARY (choose exactly one from each list):
place_design: {PLACE}
phys_opt_design: {PHYS}
route_design: {ROUTE}

KNOWN PRIOR (validated on this design): the optimum is constraint-dependent —
at tight constraints (5.0 ns) broad Explore beat Aggressive; at loose
constraints (8.62 ns) Aggressive won. AggressiveExplore route costs 2-10x
wall time. Balance expected gain against exploring genuinely different
placement families rather than variations of a tried one.

Respond ONLY with JSON:
{{"place": "...", "phys_opt": "...", "route": "...", "reasoning": "one sentence"}}
or {{"verdict": "converged", "reasoning": "one sentence"}} if the history shows
diminishing returns (best unlikely to improve >0.5%)."""
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({"model": MODEL, "max_tokens": 300,
                         "messages": [{"role":"user","content":prompt}]}).encode(),
        headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req) as f:
        resp = json.load(f)
    cost = resp["usage"]["input_tokens"]*3e-6 + resp["usage"]["output_tokens"]*15e-6
    txt = resp["content"][0]["text"]
    m = re.search(r"\{.*\}", txt, re.S)
    return json.loads(m.group(0)), cost

def run_combo(key, period, out, ckpt, pl, po, rt):
    tag = f"{pl}__{po}__{rt}"
    rpt = f"{out}/timing_{tag}.rpt"
    tcl = f"""open_checkpoint {ckpt}
opt_design
place_design -directive {pl}
phys_opt_design -directive {po}
route_design -directive {rt}
report_timing_summary -file {rpt}
puts "=== IMPL {tag} DONE ==="
"""
    open(f"{out}/impl_{tag}.tcl","w").write(tcl)
    t0 = time.time()
    subprocess.run(["vivado","-mode","batch","-source",f"{out}/impl_{tag}.tcl",
                    "-journal",f"{out}/impl_{tag}.jou","-log",f"{out}/impl_{tag}.log"], text=True)
    txt = open(rpt).read() if os.path.exists(rpt) else ""
    m = re.search(r"Slack \((?:VIOLATED|MET)\)\s*:\s*(-?[\d.]+)", txt)
    wns = float(m.group(1)) if m else None
    fmax = round(1000.0/(period - wns),1) if wns is not None else None
    return wns, fmax, round(time.time()-t0,1)

def main():
    module = sys.argv[1]; period = float(sys.argv[2])
    key = module + ("_pristine" if "--pristine" in sys.argv else "")
    max_runs = int(sys.argv[sys.argv.index("--max-runs")+1]) if "--max-runs" in sys.argv else 4
    out = f"./synth_out/sweep_{key}"; ckpt = f"{out}/post_synth.dcp"
    assert os.path.exists(ckpt), f"no checkpoint at {ckpt}; run flow_sweep.py once first"
    total_cost = 0.0
    for i in range(max_runs):
        hist = history(key, period)
        prop, cost = ask(key, period, hist)
        total_cost += cost
        print(f"[api] call {i+1} | ${total_cost:.4f} | {prop}")
        if prop.get("verdict") == "converged":
            open(LOG,"a").write(json.dumps({"module":key,"period":period,
                "verdict":"converged","reasoning":prop["reasoning"],
                "agent":True,"ts":time.strftime("%H:%M:%S")})+"\n")
            break
        pl,po,rt = prop["place"], prop["phys_opt"], prop["route"]
        if pl not in PLACE or po not in PHYS or rt not in ROUTE:
            print("REFUSED: outside vocabulary"); continue
        if (pl,po,rt) in [(r.get("place"),r.get("phys_opt"),r.get("route")) for r in hist]:
            print("REFUSED: already tried"); continue
        wns,fmax,rs = run_combo(key,period,out,ckpt,pl,po,rt)
        rec = {"module":key,"period":period,"place":pl,"phys_opt":po,"route":rt,
               "wns":wns,"fmax_mhz":fmax,"runtime_s":rs,"agent":True,
               "reasoning":prop["reasoning"],"ts":time.strftime("%H:%M:%S")}
        open(LOG,"a").write(json.dumps(rec)+"\n")
        print(f"{pl}/{po}/{rt}: fmax {fmax} MHz | {rs}s")
    best = max((r for r in history(key,period) if r.get("fmax_mhz")),
               key=lambda r: r["fmax_mhz"], default=None)
    print("=== BEST OVERALL ===\n", json.dumps(best, indent=2))

if __name__ == "__main__":
    main()
