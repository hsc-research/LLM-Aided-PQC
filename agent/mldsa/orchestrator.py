"""Orchestrator v1: deterministic loop for ML-DSA block PPA optimization.
extract paths -> classify per validated policy -> LLM fills exactly TWO
slots (strategy pick + one str-replace pair) -> gate -> synth ->
accept/revert -> log. The model never chooses targets, never emits
free-form code, never changes latency.

Usage:
  python3 agent/mldsa/orchestrator.py <block> [param_set] [--from-pristine]
  blocks: rejection_a rejection_s rejection_y makehint
  --from-pristine: reset tracked source to pristine first (validation mode:
                   re-derive a known win from scratch).
"""
import sys, os, re, json, shutil, importlib, time
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "agent"))
os.chdir(REPO)

import anthropic
from synthesizer import run_synthesis
import path_extractor

MODEL       = "claude-sonnet-4-6"
MIN_GAIN_NS = 0.05
LOG         = os.path.join(HERE, "orchestrator_log.jsonl")
PRISTINE    = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src"

BLOCKS = {
    # block: (tracked source, gate module name, baseline wns_ns, baseline luts)
    "rejection_a": ("agent/mldsa/mldsa_src/rejection_a.v", "rejection_a_equiv_gate", -2.857, None),
    "rejection_s": ("agent/mldsa/mldsa_src/rejection_s.v", "rejection_s_equiv_gate", -2.486, None),
    "rejection_y": ("agent/mldsa/mldsa_src/rejection_y.v", "rejection_y_equiv_gate", -4.230, 1313),
    "makehint":    ("agent/mldsa/mldsa_src/makehint.v",    "makehint_equiv_gate",    -0.633, None),
    "gen_c":       ("agent/mldsa/mldsa_src/gen_c.v",       "gen_c_equiv_gate",       -5.233, 2141),
    "decoder":     ("agent/mldsa/mldsa_src/decoder.v",     "decoder_equiv_gate",     -4.806, 2138),
    # coeff_decomposer: CLOSED (placement-coupled, 5 failed restructurings). Not registered.
}

POLICY = """VALIDATED STRATEGY MENU (pick exactly one, or no_action):
1. flag_precompute: compare logic on already-registered inputs feeding CE/write-index
   decode -> register the flag from pre-register inputs. (n=3, best pattern.)
2. constant_lut: small-domain (<=4-bit input) arithmetic chain -> constant LUT. (n=1)
3. sign_select: compare-then-conditional-subtract idiom -> single subtract, select on
   sign bit. (n=2)
4. shifter_mux_reduce: variable shifter ONLY if the reachable shift-amount set is
   already proven closed in findings. NEVER propose new probes; if unproven, no_action
   with reason "shifter unproven".
5. max_fanout_16: route-bound (route% >= ~70) + high-fanout source register ->
   (* max_fanout = 16 *) on the SOURCE REGISTER declaration. Never on combinational
   always@(*) regs (regressed twice). 16 not 8.
FORBIDDEN (never propose): arithmetic-divide rewrites, unpipelined DSP inference,
ANY latency/cycle-schedule change (lockstep gate will fail), width-narrowing on
placement-sensitive paths, sensitivity-list-only edits, edits to coeff_decomposer.
OUTPUT: JSON only, one of:
{"verdict":"experiment","strategy":"<menu name>","reason":"<1 sentence>",
 "edits":[{"old":"<exact unique substring>","new":"<replacement>"}, ...]}
{"verdict":"no_action","reason":"<1 sentence>"}
1 to 4 edit pairs. Each "old" MUST occur exactly once in the file, byte-exact
including whitespace. Edits are applied in order, all-or-nothing.
For flag_precompute you typically need: (a) declare the flag reg at module
scope, (b) assign the flag at EVERY update site of the source register,
computed from the SAME pre-register expressions, (c) swap the consumer
compare to the flag. A flag nobody consumes is dead logic and changes nothing.
The edit must be latency-neutral: same outputs on the same cycles."""

def log(rec):
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print("LOG:", rec.get("verdict"), rec.get("reason", ""))

def classify(paths):
    """Deterministic pre-classification of top-3 paths. Tags are hints, not
    exclusions: the model must weigh the whole menu against the RTL."""
    tags = []
    for i, pth in enumerate(paths[:3]):
        pt = []
        if pth["route_pct"] >= 70: pt.append("route-heavy")
        if pth["logic_pct"] >= 40: pt.append("logic-heavy")
        if pth["levels"] >= 12: pt.append(f"deep({pth['levels']}lv)")
        tags.append(f"path{i}[slack {pth['slack']}]: {','.join(pt) or 'mixed'}"
                    f" {pth['source'][:40]} -> {pth['dest'][:40]}")
    tags.append("NOTE: route-heavy does NOT exclude flag_precompute; shortening "
                "logic into a registered flag also removes routed nets. Consider "
                "the full menu against the RTL structure before max_fanout_16.")
    return tags

def call_llm(block, rtl, board, tags):
    client = anthropic.Anthropic()
    prompt = (f"BLOCK: {block} (ML-DSA, Artix-7 xc7a200tfbg676-1, 200 MHz OOC).\n"
              f"CODE-COMPUTED CLASSIFICATION (authoritative): {tags}\n\n"
              f"TOP TIMING PATHS:\n{board}\n\nFULL RTL:\n{rtl}\n\n"
              "Fill exactly two slots: strategy + str-replace pair. JSON only.")
    for attempt in range(2):
        r = client.messages.create(model=MODEL, max_tokens=2000,
            system=POLICY, messages=[{"role": "user", "content": prompt}])
        txt = r.content[0].text
        i, j = txt.find("{"), txt.rfind("}")
        if i != -1 and j > i:
            try:
                return json.loads(txt[i:j+1])
            except json.JSONDecodeError as e:
                err = str(e)
        else:
            err = "no JSON object found"
        print(f"RAW MODEL OUTPUT (attempt {attempt+1}):\n{txt[:800]}")
        prompt += f"\n\nYOUR PREVIOUS REPLY WAS NOT VALID JSON ({err}). Reply with ONLY the JSON object, no prose, no code fences."
    raise SystemExit("LLM failed to produce valid JSON twice; aborting.")

def main():
    block = sys.argv[1]
    # ML-DSA sources have no parameter_set generic; Vivado ignores it.
    # "mldsa" is just a label for report filenames/logs.
    param_set = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "mldsa"
    src, gate_name, base_wns, base_luts = BLOCKS[block]
    gate = importlib.import_module(f"mldsa.{gate_name}") if False else None
    sys.path.insert(0, os.path.join(REPO, "agent", "mldsa"))
    gate = importlib.import_module(gate_name)

    if "--from-pristine" in sys.argv:
        shutil.copy(src, src + ".tracked_bak")
        shutil.copy(os.path.join(PRISTINE, os.path.basename(src)), src)
        print("VALIDATION MODE: tracked source reset to pristine (backup: .tracked_bak)")

    # 0. gate self-check on current source BEFORE any edit
    g = gate.run_equiv(src)
    if g["status"] != "PASS":
        log({"block": block, "verdict": "abort", "reason": "pre-edit gate self-check FAIL: " + g["reason"]})
        sys.exit(1)
    print("Pre-edit gate self-check: PASS")

    # 1. extract paths
    rpt = path_extractor.run_extraction(block, param_set, 10)
    if not rpt:
        log({"block": block, "verdict": "abort", "reason": "path extraction failed"}); sys.exit(1)
    paths = path_extractor.parse_paths(rpt)
    if not paths:
        log({"block": block, "verdict": "abort", "reason": "no paths parsed"}); sys.exit(1)
    pre_wns = paths[0]["slack"]
    tags = classify(paths)
    print(f"Worst slack {pre_wns} | classification: {tags}")

    # 2. LLM: two slots only
    board = json.dumps(paths, indent=1)
    rtl = open(src).read()
    failed, dead = [], []
    if os.path.exists(LOG):
        for line in open(LOG):
            r = json.loads(line)
            if r.get("block") != block or not r.get("strategy"):
                continue
            v = str(r.get("verdict", ""))
            if v == "gate_fail" or v == "synth_fail":
                failed.append(r["strategy"])
            elif v.startswith("marginal"):
                m = re.search(r"marginal_([+-][\d.]+)", v)
                g = float(m.group(1)) if m else -1.0
                if g < -0.02:
                    failed.append(r["strategy"])       # genuinely regressed
                else:
                    dead.append(r["strategy"])          # netlist no-op / dead edit
    if failed:
        tags = list(tags) + [f"STRATEGIES THAT REGRESSED OR FAILED THE GATE on this block (do not repeat): {sorted(set(failed))}"]
    if dead:
        tags = list(tags) + [f"PRIOR ATTEMPTS AT {sorted(set(dead))} produced ZERO netlist change (dead edit: "
            "likely a flag that no consumer reads, or an attribute on a pruned net). "
            "These strategies remain VALID — the previous EDIT was wrong, not the strategy. "
            "If you retry, ensure every new signal is actually consumed on the critical path."]
    accepted = []
    if os.path.exists(LOG):
        for line in open(LOG):
            r = json.loads(line)
            if r.get("block") == block and r.get("verdict") == "ACCEPTED":
                accepted.append(r)
    if accepted:
        hist = "; ".join(f"{r['strategy']}: {json.dumps(r.get('edits'))[:200]}" for r in accepted)
        tags = list(tags) + [f"EDITS ALREADY APPLIED AND ACCEPTED on this block (present in the RTL "
            f"you were given; do NOT re-apply, duplicate, or paraphrase them — a strategy already "
            f"accepted on a cone is exhausted for that cone): {hist}"]
    prop = call_llm(block, rtl, board, tags)
    print(json.dumps({k: v for k, v in prop.items() if k != "old" and k != "new"}, indent=1))
    if prop["verdict"] != "experiment":
        log({"block": block, "verdict": "no_action", "reason": prop["reason"]}); return

    # 3. assertion-gated apply (assert count==1 per edit), all-or-nothing
    edits = prop.get("edits") or ([{"old": prop["old"], "new": prop["new"]}]
                                  if "old" in prop else None)
    if not edits or not (1 <= len(edits) <= 4):
        log({"block": block, "verdict": "refused", "reason": "bad edits slot"}); return
    work = rtl
    for k, e in enumerate(edits):
        n = work.count(e["old"])
        if n != 1:
            log({"block": block, "verdict": "refused",
                 "reason": f"edit{k} anchor count {n} != 1: {e['old'][:60]}"}); return
        work = work.replace(e["old"], e["new"])
    shutil.copy(src, src + ".bak")
    open(src, "w").write(work)
    print("applied")   # mandatory confirmation per protocol

    def revert(why):
        shutil.copy(src + ".bak", src)
        log({"block": block, "verdict": why, "strategy": prop.get("strategy"),
             "reason": prop.get("reason", ""), "edits": edits})
        print("REVERTED:", why)

    # 4. gate
    g = gate.run_equiv(src)
    if g["status"] != "PASS":
        revert("gate_fail"); return
    print(f"Gate PASS ({g.get('checked', '?')} checked)")

    # 5. synth + compare
    res = run_synthesis(block, param_set)
    if "error" in res:
        revert("synth_fail"); return
    gain = res["wns_ns"] - pre_wns
    dl = (res["luts"] - base_luts) if (base_luts and res.get("luts")) else None
    print(f"WNS {pre_wns} -> {res['wns_ns']} (gain {gain:+.3f})"
          + (f", LUTs {base_luts} -> {res['luts']} ({dl:+d})" if dl is not None else ""))

    # 6. accept/revert
    lut_win = dl is not None and dl < 0 and gain > -0.010  # LUT win allowed if WNS-neutral
    if gain >= MIN_GAIN_NS or lut_win:
        log({"block": block, "verdict": "ACCEPTED", "strategy": prop["strategy"],
             "wns_pre": pre_wns, "wns_post": res["wns_ns"], "gain": round(gain, 3),
             "luts": res.get("luts"), "edits": edits})
        print("=== ACCEPTED. .bak kept; review diff and commit manually. ===")
    else:
        revert(f"marginal_{gain:+.3f}")

if __name__ == "__main__":
    main()
