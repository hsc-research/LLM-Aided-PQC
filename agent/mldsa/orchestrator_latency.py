"""Orchestrator latency-tier v0: LLM-proposed latency-changing edits with
full-KAT gating and divergence-guided repair.
Loop: paths -> LLM proposes pipeline insertion + retap set (multi-file) ->
apply -> full-KAT -> FAIL: stream-bisect, feed divergence back, retry (<=3)
-> PASS: synth block, compare, ACCEPT/revert. Reset = git checkout.
Usage: python3 agent/mldsa/orchestrator_latency.py <block> [--retries N]
"""
import sys, os, re, json, shutil, subprocess, time, glob
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "agent"))
os.chdir(REPO)
import anthropic
from synthesizer import run_synthesis
import path_extractor

MODEL = "claude-sonnet-4-6"
MIN_GAIN_NS = 0.05
LOG = os.path.join(HERE, "latency_log.jsonl")
SRCDIR = "agent/mldsa/mldsa_src"
PRISTINE = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src"
# files the model may touch per target block (cluster = block + its schedulers)
CLUSTERS = {
    "butterfly": ["butterfly.v", "butterfly2x2.v", "operation_module.v"],
    "coeff_decomposer": ["coeff_decomposer.v", "decomp_map1.v"],
}
SYNTH_BLOCK = {"butterfly": "butterfly", "coeff_decomposer": "coeff_decomposer"}

POLICY = """You optimize FPGA timing via LATENCY-CHANGING pipeline edits on ML-DSA RTL
(Artix-7, 200MHz OOC). You may insert pipeline registers on the critical path and
retap ALL downstream consumers. Hard-won rules from verified wins:
1. Inserting a register inside a block shifts its output validity by +1 cycle.
   EVERY fixed-index consumer must be retapped: valid_sr taps, delay-pipe reads
   (widen the pipe first), zeta/operand delay lines, BRAM write-address taps.
2. COUNT CHAINED INSTANCES: if the edited module is instantiated in a chain
   (e.g. butterfly2x2 chains TWO butterfly stages for NTT modes), a +1 internal
   stage shifts system-visible timing by +1 PER CHAINED STAGE (+2 total). Address
   taps and drain counters in the scheduler shift by the TOTAL, per mode.
3. Mode-asymmetric latency is allowed (e.g. only INTT +1) but every mode's taps
   must be derived independently; do not pattern-match indices.
4. Widen any array/shift-register BEFORE reading a new index; update ALL loop
   bounds (initial, reset, shift) or X-propagation results.
5. Drain/pause counters that let writes land before the next round's reads must
   extend by the same total shift, else read-after-write hazards corrupt round 2+.
6. Only pipeline paths through DSP multipliers or deep carry chains; ADD/SUB-style
   modes not touching the target path stay untouched.
OUTPUT JSON ONLY:
{"verdict":"experiment","design":"<2-sentence retiming derivation incl. total shift per mode>",
 "edits":{"<filename.v>":[{"old":"<exact unique substring>","new":"..."}, ...], ...}}
or {"verdict":"no_action","reason":"<1 sentence>"}
Anchors byte-exact incl. whitespace, each occurring exactly once in its file."""

def log(rec):
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    open(LOG, "a").write(json.dumps(rec) + "\n")
    print("LOG:", rec.get("verdict"), rec.get("reason", rec.get("design", ""))[:120])

def git_reset(files):
    subprocess.run(["git", "checkout", "--"] + [f"{SRCDIR}/{f}" for f in files], check=True)

def apply_edits(edits):
    staged = {}
    for fn, pairs in edits.items():
        p = f"{SRCDIR}/{fn}"
        s = open(p).read()
        for k, e in enumerate(pairs):
            n = s.count(e["old"])
            if n != 1:
                return f"{fn} edit{k} anchor count {n}"
            s = s.replace(e["old"], e["new"])
        staged[p] = s
    for p, s in staged.items():
        open(p, "w").write(s)
    print("applied")
    return None

def full_kat():
    r = subprocess.run([sys.executable, f"{HERE}/full_kat_gate.py",
                        f"{REPO}/{SRCDIR}"], capture_output=True, text=True)
    i = r.stdout.find("{")
    return json.loads(r.stdout[i:]) if i != -1 else {"status": "FAIL", "reason": r.stdout[-300:]}

def bisect(cluster_files):
    """Instrumented 1-vector pristine-vs-current stream compare; returns first divergence text."""
    out = []
    DBG = ('\n    integer dbg_i=0,dbg_o=0;\n    always @(posedge clk) begin\n'
           '      if (validi && dbg_i<4000) begin $display("BFI %m %0d %h %h %h",mode,datai,zetai,acci); dbg_i=dbg_i+1; end\n'
           '      if (valido && dbg_o<4000) begin $display("BFO %m %0d %h",mode,datao); dbg_o=dbg_o+1; end\n'
           '    end\nendmodule')
    def build(name, pristine):
        d = os.path.join(HERE, name)
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        for p in glob.glob(f"{SRCDIR}/*.v"): shutil.copy(p, d)
        if pristine:
            for b in cluster_files: shutil.copy(os.path.join(PRISTINE, b), d)
        f = os.path.join(d, "butterfly2x2.v"); s = open(f).read()
        open(f, "w").write(s.replace("endmodule", DBG))
        return d
    logs = {}
    for tag, pr in (("p", True), ("e", False)):
        d = build("lat_dbg_" + tag, pr)
        subprocess.run([sys.executable, f"{HERE}/full_kat_gate.py", d, "--vectors", "1"],
                       capture_output=True, text=True)
        logs[tag] = open(f"{HERE}/fullkat_run.log").read()
        shutil.rmtree(d, ignore_errors=True)
    def parse(t):
        st = {}
        for ln in t.splitlines():
            m = re.match(r"(BFI|BFO) (\S+) (\d+) (.*)", ln.strip())
            if m: st.setdefault((m.group(2), m.group(1)), []).append((m.group(3), m.group(4)))
        return st
    sp, se = parse(logs["p"]), parse(logs["e"])
    for key in sorted(set(sp) | set(se)):
        a, b = sp.get(key, []), se.get(key, [])
        n = min(len(a), len(b))
        div = next((i for i in range(n) if a[i] != b[i]), None)
        if div is not None:
            ctx = "\n".join(f"  [{j}] pristine:{a[j]} edited:{b[j]}"
                            for j in range(max(0, div - 2), min(div + 2, n)))
            out.append(f"{key[1]} stream ({key[0]}) first divergence at transaction #{div}"
                       f" (mode,data):\n{ctx}")
        elif len(a) != len(b):
            out.append(f"{key[1]} stream length mismatch: pristine={len(a)} edited={len(b)}")
    return "\n".join(out) or "no divergence found in first 4000 transactions of instrumented streams"

def call_llm(messages):
    client = anthropic.Anthropic()
    msgs = list(messages)
    for a in range(3):
        r = client.messages.create(model=MODEL, max_tokens=8000, system=POLICY, messages=msgs)
        txt = r.content[0].text
        i, j = txt.find("{"), txt.rfind("}")
        if i != -1 and j > i:
            try:
                return json.loads(txt[i:j+1]), txt
            except json.JSONDecodeError as e:
                err = str(e)
        else:
            err = "no JSON found"
        msgs = msgs + [{"role": "assistant", "content": txt},
                       {"role": "user", "content": f"INVALID JSON ({err}). Resend ONLY the complete JSON object. If it was truncated, shorten edit set or split old anchors smaller."}]
    raise SystemExit("LLM failed valid JSON 3x")

def main():
    block = sys.argv[1]
    retries = int(sys.argv[sys.argv.index("--retries") + 1]) if "--retries" in sys.argv else 3
    files = CLUSTERS[block]
    # pre-check: tracked state must gate-PASS
    g = full_kat()
    if g["status"] != "PASS":
        log({"block": block, "verdict": "abort", "reason": "pre-edit full-KAT FAIL"}); sys.exit(1)
    print("Pre-edit full-KAT: PASS")
    rpt = path_extractor.run_extraction(SYNTH_BLOCK[block], "mldsa", 10)
    paths = path_extractor.parse_paths(rpt)
    pre_wns = paths[0]["slack"]
    rtl = "\n\n".join(f"=== {f} ===\n" + open(f"{SRCDIR}/{f}").read() for f in files)
    messages = [{"role": "user", "content":
        f"TARGET BLOCK: {block}. Files you may edit: {files}.\n"
        f"TOP PATHS:\n{json.dumps(paths[:5], indent=1)}\n\nRTL:\n{rtl}\n\n"
        "Propose ONE latency-changing pipeline edit set. JSON only."}]
    for attempt in range(retries + 1):
        prop, raw = call_llm(messages)
        if prop.get("verdict") != "experiment":
            log({"block": block, "verdict": "no_action", "reason": prop.get("reason", "")}); return
        print("DESIGN:", prop.get("design", "")[:300])
        err = apply_edits(prop["edits"])
        if err:
            messages += [{"role": "assistant", "content": raw},
                         {"role": "user", "content": f"APPLY FAILED: {err}. Fix anchors, resend full JSON."}]
            continue
        g = full_kat()
        if g["status"] == "PASS":
            res = run_synthesis(SYNTH_BLOCK[block], "mldsa")
            gain = round(res["wns_ns"] - pre_wns, 3)
            print(f"WNS {pre_wns} -> {res['wns_ns']} ({gain:+.3f})")
            if gain >= MIN_GAIN_NS:
                log({"block": block, "verdict": "ACCEPTED", "attempt": attempt,
                     "wns_pre": pre_wns, "wns_post": res["wns_ns"], "gain": gain,
                     "design": prop.get("design"), "edits": prop["edits"]})
                print("=== ACCEPTED. Review diff + commit manually. ==="); return
            git_reset(files)
            log({"block": block, "verdict": f"marginal_{gain:+.3f}", "attempt": attempt,
                 "design": prop.get("design"), "edits": prop["edits"]}); return
        div = bisect(files)
        print("DIVERGENCE:\n", div[:500])
        git_reset(files)
        log({"block": block, "verdict": "gate_fail", "attempt": attempt,
             "wrong": g.get("wrong_count"), "divergence": div[:800],
             "design": prop.get("design")})
        messages += [{"role": "assistant", "content": raw},
                     {"role": "user", "content":
                      f"GATE FAILED ({g.get('wrong_count')} wrong bytes). Latency-agnostic stream "
                      f"bisection (pristine vs your edit, value-order compare):\n{div}\n\n"
                      "Diagnose which retap is off (remember rule 2: total shift = per-stage shift x "
                      "chained instances). Resend the FULL corrected JSON edit set (applied to "
                      "ORIGINAL file state, not incremental)."}]
    log({"block": block, "verdict": "retries_exhausted"})
    print("Retries exhausted; tracked state reset clean.")

if __name__ == "__main__":
    main()
