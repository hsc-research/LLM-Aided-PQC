"""Cross-design transfer experiment: ML-DSA-learned priors applied
autonomously to HQC blocks. Reuses the ML-DSA orchestrator POLICY verbatim
(single source of truth) with the HQC full-KAT gate.
Usage: python3 agent/hqc/transfer_orchestrator.py <module> <level>
  e.g.  python3 agent/hqc/transfer_orchestrator.py encap hqc128
Logs to agent/hqc/transfer_log.jsonl. Every verdict, cost, and edit recorded.
"""
import sys, os, re, json, shutil, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "agent"))
os.chdir(REPO)
import anthropic
from synthesizer import run_synthesis, MODULE_SOURCES
import path_extractor

MODEL = "claude-sonnet-4-6"
if "--model" in sys.argv:
    MODEL = {"opus": "claude-opus-4-8", "sonnet": "claude-sonnet-4-6"}.get(
        sys.argv[sys.argv.index("--model") + 1], sys.argv[sys.argv.index("--model") + 1])
MIN_GAIN_NS = 0.05
LOG = os.path.join(HERE, "transfer_log.jsonl")
PRICES = {"claude-opus-4-8": (15.0, 75.0), "claude-sonnet-4-6": (3.0, 15.0)}
USAGE = {"calls": 0, "in_tok": 0, "out_tok": 0}

def usage_cost():
    pi, po = PRICES.get(MODEL, (3.0, 15.0))
    return round(USAGE["in_tok"]/1e6*pi + USAGE["out_tok"]/1e6*po, 4)

# POLICY imported verbatim from the ML-DSA orchestrator: the transfer claim
# is that these priors were learned on ML-DSA and apply unchanged.
sys.path.insert(0, os.path.join(REPO, "agent", "mldsa"))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "mldsa_orch", os.path.join(REPO, "agent", "mldsa", "orchestrator.py"))
_m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(_m)
except SystemExit:
    pass
POLICY = _m.POLICY
classify = _m.classify

def log(rec):
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    rec["model"] = MODEL
    rec["cost_usd"] = usage_cost()
    rec["api_calls"] = USAGE["calls"]
    open(LOG, "a").write(json.dumps(rec) + "\n")
    print("LOG:", rec.get("verdict"), str(rec.get("reason", ""))[:100])

def call_llm(block, rtl, board, tags):
    client = anthropic.Anthropic()
    prompt = (f"BLOCK: {block} (HQC KEM accelerator, Artix-7 xc7a200tfbg676-1, 200 MHz OOC).\n"
              f"NOTE: your strategy menu and rules were validated on a DIFFERENT design "
              f"(ML-DSA). Apply them to this HQC block only where the structural "
              f"preconditions genuinely hold; no_action is the correct answer when "
              f"they do not.\n"
              f"CODE-COMPUTED CLASSIFICATION: {tags}\n\n"
              f"TOP TIMING PATHS:\n{board}\n\nFULL RTL:\n{rtl}\n\n"
              "Fill exactly two slots: strategy + str-replace pair(s). JSON only.")
    for attempt in range(2):
        r = client.messages.create(model=MODEL, max_tokens=4000,
            system=POLICY, messages=[{"role": "user", "content": prompt}])
        USAGE["calls"] += 1; USAGE["in_tok"] += r.usage.input_tokens
        USAGE["out_tok"] += r.usage.output_tokens
        print(f"[api] call {USAGE['calls']} | run total ${usage_cost()}")
        txt = r.content[0].text
        i, j = txt.find("{"), txt.rfind("}")
        if i != -1 and j > i:
            try: return json.loads(txt[i:j+1])
            except json.JSONDecodeError: pass
        prompt += "\n\nInvalid JSON; resend ONLY the JSON object."
    raise SystemExit("no valid JSON")

def main():
    module = sys.argv[1]; level = sys.argv[2]
    srcs = MODULE_SOURCES[module]
    rpt = path_extractor.run_extraction(module, level, 10)
    paths = path_extractor.parse_paths(rpt)
    pre = paths[0]["slack"]
    tags = classify(paths)
    print(f"Worst slack {pre} | {tags}")
    # target file = the source whose registers appear in the top path
    src_file = None
    for f in srcs:
        base = os.path.basename(f)
        if re.sub(r"\.v$", "", base) in paths[0]["source"] + paths[0]["dest"] or len(srcs) == 1:
            src_file = f; break
    src_file = src_file or srcs[0]
    rtl = open(src_file).read()
    prop = call_llm(module, rtl, json.dumps(paths[:5], indent=1), tags)
    if prop.get("verdict") != "experiment":
        log({"module": module, "verdict": "no_action", "reason": prop.get("reason", "")}); return
    edits = prop.get("edits") or []
    if not (1 <= len(edits) <= 4):
        log({"module": module, "verdict": "refused", "reason": "bad edits slot"}); return
    work = rtl
    for k, e in enumerate(edits):
        n = work.count(e["old"])
        if n != 1:
            log({"module": module, "verdict": "refused",
                 "reason": f"edit{k} anchor count {n}", "strategy": prop.get("strategy")}); return
        work = work.replace(e["old"], e["new"])
    shutil.copy(src_file, src_file + ".bak")
    open(src_file, "w").write(work)
    print("applied")
    def revert(why):
        shutil.copy(src_file + ".bak", src_file)
        log({"module": module, "verdict": why, "strategy": prop.get("strategy"),
             "reason": prop.get("reason", ""), "edits": edits})
        print("REVERTED:", why)
    kat = subprocess.run(["python3", "agent/hqc/kat_gate.py"],
                         capture_output=True, text=True).stdout
    if "KAT RESULT: PASS" not in kat:
        revert("kat_fail"); return
    print("KAT PASS")
    res = run_synthesis(module, level)
    if "error" in res:
        revert("synth_fail"); return
    gain = round(res["wns_ns"] - pre, 3)
    print(f"WNS {pre} -> {res['wns_ns']} ({gain:+.3f})")
    if gain >= MIN_GAIN_NS:
        log({"module": module, "verdict": "ACCEPTED", "strategy": prop["strategy"],
             "wns_pre": pre, "wns_post": res["wns_ns"], "gain": gain, "edits": edits})
        print("=== ACCEPTED (TRANSFER WIN). .bak kept; review + commit manually. ===")
    else:
        revert(f"marginal_{gain:+.3f}")

if __name__ == "__main__":
    main()
