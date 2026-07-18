"""Bounded-autonomous orchestrator for HQC joint-top shared-resource cones.
Targets build/joint_design/hqc_kem_joint_design.v (the shared-mux integration
file). Up to N attempts from the latency-neutral menu; each attempt:
propose -> anchored apply -> joint KAT gate -> full-chip synth filter ->
accept/revert. On exhaustion: ESCALATE_HUMAN with all attempted diffs logged.
Post-route closure remains the final judge (chip_orchestrator re-judge);
this loop's synth compare is a filter only.
Usage: python3 agent/hqc/joint_top_orchestrator.py [--attempts N] [--model m]
"""
import sys, os, re, json, shutil, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "agent"))
os.chdir(REPO)
import anthropic
from synthesizer import run_synthesis
import path_extractor
from learned_rules import rules_prompt_block, distill_rule

SRC = "build/joint_design/hqc_kem_joint_design.v"
MODULE = "hqc_joint_opt"
PARAM = "128"
LOG = os.path.join(HERE, "joint_top_log.jsonl")
MODEL = "claude-sonnet-4-6"
N_ATTEMPTS = 3
MIN_GAIN_NS = 0.05
if "--attempts" in sys.argv:
    N_ATTEMPTS = int(sys.argv[sys.argv.index("--attempts") + 1])
if "--model" in sys.argv:
    MODEL = sys.argv[sys.argv.index("--model") + 1]

POLICY = """You optimize the TOP-LEVEL INTEGRATION FILE of a shared-resource
PQC accelerator (HQC joint design: keygen/encap/decap share one POLY_MULT and
one SHAKE via operation-select muxes). LATENCY-NEUTRAL strategies only:
1. select_retime: register a mux-select decode that is stable across the
   owning operation. RULE (validated, hard constraint): 1-cycle START PULSES
   must stay on combinational selects — a registered select can swallow the
   first pulse after an ownership change and deadlock the design.
2. fanout_replicate: replicate a high-fanout registered control (max_fanout
   attribute or manual _rep register). Deprioritized on RAM-macro
   address/select ports (replication cannot shorten macro-pin broadcast).
3. control_precompute: compute a select/enable expression one cycle early
   from registered sources with a parallel copy; NEVER from a self-loop
   endpoint.
You may NOT: change any port, add latency to any data path, alter handshake
protocols, or touch anything inside ifdef arms that are compiled out.
Reply STRICT JSON only:
{"verdict":"experiment"|"no_action","strategy":"...","reason":"...",
 "edits":[{"old":"exact text","new":"replacement"}]}  (1-3 edits max)
"no_action" with a reason is a valid, respected answer."""

def log(rec):
    rec["ts"] = time.strftime("%F %T")
    open(LOG, "a").write(json.dumps(rec) + "\n")
    print("LOG:", rec.get("verdict"), str(rec.get("reason", ""))[:100])

def kat_gate():
    r = subprocess.run(["python3", "agent/hqc/joint_kat_gate.py"],
                       capture_output=True, text=True, timeout=7200)
    return r.returncode == 0 and "GATE: PASS" in r.stdout, r.stdout[-300:]

def call_llm(rtl, board, tags):
    client = anthropic.Anthropic()
    prompt = (f"CRITICAL-PATH BOARD (full-chip synth, worst first):\n{board}\n\n"
              + "\n".join(tags) + "\n\nINTEGRATION RTL:\n" + rtl)
    r = client.messages.create(model=MODEL, max_tokens=2000,
                               system=POLICY + rules_prompt_block("hqc"),
                               messages=[{"role": "user", "content": prompt}])
    txt = r.content[0].text
    m = re.search(r"\{.*\}", txt, re.S)
    try:
        return json.loads(m.group(0)) if m else {"verdict": "no_action", "reason": "unparseable"}
    except json.JSONDecodeError:
        return {"verdict": "no_action", "reason": "bad json"}

def main():
    # pre-flight: KAT self-check on current tree
    ok, tail = kat_gate()
    if not ok:
        log({"verdict": "abort", "reason": "pre-edit joint KAT self-check FAIL: " + tail})
        sys.exit(1)
    print("Pre-edit joint KAT: PASS")

    rpt = path_extractor.run_extraction(MODULE, PARAM, 8)
    paths = path_extractor.parse_paths(rpt) if rpt else []
    if not paths:
        log({"verdict": "abort", "reason": "no chip paths parsed"}); sys.exit(1)
    pre = paths[0]["slack"]
    print(f"Baseline chip worst slack: {pre}")

    attempted = []
    for attempt in range(1, N_ATTEMPTS + 1):
        print(f"=== ATTEMPT {attempt}/{N_ATTEMPTS} ===")
        rtl = open(SRC).read()
        board = json.dumps(paths[:8], indent=1)
        tags = [f"ATTEMPT {attempt} of {N_ATTEMPTS}."]
        if attempted:
            tags.append("PRIOR ATTEMPTS THIS RUN (do not repeat, byte-different edits required): "
                        + json.dumps([{"strategy": a["strategy"], "verdict": a["verdict"]}
                                      for a in attempted]))
        prop = call_llm(rtl, board, tags)
        if prop.get("verdict") != "experiment":
            log({"verdict": "no_action", "attempt": attempt, "reason": prop.get("reason", "")})
            attempted.append({"strategy": prop.get("strategy"), "verdict": "no_action"})
            break  # model says nothing left in menu — respect it
        edits = prop.get("edits") or []
        if not (1 <= len(edits) <= 3):
            log({"verdict": "refused", "attempt": attempt, "reason": "bad edits slot"})
            attempted.append({"strategy": prop.get("strategy"), "verdict": "refused"})
            continue
        work = rtl; bad = False
        for k, e in enumerate(edits):
            if work.count(e["old"]) != 1:
                log({"verdict": "refused", "attempt": attempt,
                     "reason": f"edit{k} anchor count != 1"}); bad = True; break
            work = work.replace(e["old"], e["new"])
        if bad:
            attempted.append({"strategy": prop.get("strategy"), "verdict": "refused"})
            continue
        open(SRC, "w").write(work)
        print("applied")

        def revert(why):
            subprocess.run(["git", "checkout", "--", SRC], capture_output=True)
            rec = {"verdict": why, "attempt": attempt,
                   "strategy": prop.get("strategy"), "edits": edits}
            log(rec); attempted.append({"strategy": prop.get("strategy"), "verdict": why,
                                        "edits": edits})
            print("REVERTED:", why)

        ok, tail = kat_gate()
        if not ok:
            revert("kat_fail"); continue
        print("Joint KAT PASS")
        res = run_synthesis(MODULE, PARAM)
        if "error" in res:
            revert("synth_fail"); continue
        gain = round(res["wns_ns"] - pre, 3)
        print(f"chip WNS {pre} -> {res['wns_ns']} ({gain:+.3f})")
        if gain >= MIN_GAIN_NS:
            rec = {"verdict": "ACCEPTED", "attempt": attempt,
                   "strategy": prop["strategy"], "wns_pre": pre,
                   "wns_post": res["wns_ns"], "gain": gain, "edits": edits}
            log(rec)
            try: distill_rule(anthropic.Anthropic(), MODEL, rec, "hqc")
            except Exception as e: print("rule distill skipped:", e)
            print("=== ACCEPTED (synth filter). POST-ROUTE JUDGE STILL REQUIRED "
                  "(chip_orchestrator re-judge). Source left applied; commit after judge. ===")
            return
        revert(f"marginal_{gain:+.3f}")

    log({"verdict": "ESCALATE_HUMAN",
         "reason": f"autonomous tier exhausted after {len(attempted)} attempt(s)",
         "attempts": attempted, "baseline_wns": pre})
    print("=== ESCALATE_HUMAN: bounded autonomous tier exhausted; attempted diffs "
          "preserved in joint_top_log.jsonl for the human session. ===")

if __name__ == "__main__":
    main()
