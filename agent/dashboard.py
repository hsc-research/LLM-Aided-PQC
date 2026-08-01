#!/usr/bin/env python3
"""PQC Agent Dashboard v3 — narrative UI backend.
Usage: python3 agent/dashboard.py  ->  http://localhost:5000
Read-only; safe while orchestrators / Minerva / Vivado run.
Serves static front end from agent/dashboard_static/."""
import json, os, time, subprocess
from flask import Flask, jsonify, send_from_directory

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "dashboard_static")
LOGS = {
    "latency":      os.path.join(HERE, "mldsa", "latency_log.jsonl"),
    "orchestrator": os.path.join(HERE, "mldsa", "orchestrator_log.jsonl"),
    "flight":       os.path.join(HERE, "flight_log.jsonl"),
    "transfer":     os.path.join(HERE, "hqc", "transfer_log.jsonl"),
    "flow_sweep":   os.path.join(HERE, "flow_sweep_log.jsonl"),
    "chip":         os.path.join(HERE, "chip_orchestrator_log.jsonl"),
    "port":         os.path.join(HERE, "port", "port_log.jsonl"),
}
RUNLOG = os.path.join(HERE, "mldsa", "fullkat_run.log")

BASELINES_JSON = os.path.join(HERE, "dashboard_baselines.json")
def load_baselines():
    try:
        return json.load(open(BASELINES_JSON))
    except Exception:
        return {"designs": {}}




TIER_LABEL = {
    "latency":      "Latency tier (pipelining)",
    "orchestrator": "Latency-preserving tier",
    "flight":       "HQC flight log",
    "transfer":     "Cross-design transfer",
    "flow_sweep":   "Flow-space search",
    "chip":         "Chip-level closure loop",
    "port":         "Cross-toolchain port fixes",
}

VERDICT_EXPLAIN = {
    "ACCEPTED": "Win: edit passed all correctness checks and improved timing enough to keep.",
    "gate_fail": "Wrong outputs in simulation. Auto-reverted; divergence fed back to the model.",
    "synth_fail": "Correct but Vivado synthesis errored. Auto-reverted.",
    "no_action": "Model inspected the code and correctly declined to edit.",
    "refused": "Orchestrator rejected the proposal before applying (bad anchors / closed strategy).",
    "abort": "Run stopped before any edit (pre-checks failed).",
    "retries_exhausted": "All attempts failed. Files reset to last-good state.",
    "kat_fail": "Full-KAT caught a functional error. Auto-reverted.",
    "apply_fail": "Edit anchors did not match the source. Nothing applied.",
    "parse_error": "A log line could not be read.",
    "NO_TARGET (out-of-scope cone)": "Worst chip path is outside block-orchestrator scope (e.g. shared Keccak).",
}

def _v(v):
    v = str(v or "")
    if v.startswith("marginal"): return "marginal"
    return v

STATUS_KIND = {  # card color class per verdict
    "ACCEPTED": "win", "marginal": "marginal",
    "gate_fail": "fail", "synth_fail": "fail", "kat_fail": "fail",
    "retries_exhausted": "fail", "abort": "fail", "apply_fail": "fail",
    "no_action": "neutral", "refused": "neutral", "parse_error": "neutral",
}

def narrative(r, src):
    """One-sentence PR-style story for a record."""
    v = _v(r.get("verdict"))
    blk = r.get("block") or r.get("module") or r.get("dispatch_instance") or "design"
    strat = r.get("strategy") or ""
    gain = r.get("gain")
    reason = str(r.get("reason") or r.get("design") or "")[:180]
    if src == "chip":
        c = r.get("closure") or {}
        f = c.get("closing_fmax_mhz")
        s = f"Chip closure {f} MHz" if f else "Chip closure run"
        if r.get("verdict"): s += f" — {r['verdict']}"
        if r.get("dispatch_instance"): s += f"; worst path in {r['dispatch_instance']}"
        return s
    if v == "ACCEPTED":
        g = f"+{gain}ns" if isinstance(gain, (int, float)) else "accepted"
        return f"{strat or 'Edit'} on {blk}: {g}. Passed every correctness gate."
    if v == "marginal":
        return f"{strat or 'Edit'} on {blk} was correct but gained too little; auto-reverted."
    if v == "no_action":
        return f"Model examined {blk} and declined: {reason or 'no safe lever found.'}"
    if v in ("gate_fail", "kat_fail"):
        return f"{strat or 'Edit'} on {blk} produced wrong outputs; auto-reverted. {reason}"
    if v == "apply_fail":
        return f"Edit anchors missed on {blk}; nothing applied. {reason}"
    if v == "retries_exhausted":
        return f"All retries on {blk} failed; state reset clean."
    return f"{v or 'event'} on {blk}. {reason}".strip()

def read_jsonl(path):
    if not os.path.exists(path): return []
    out = []
    for line in open(path, errors="replace"):
        line = line.strip()
        if not line: continue
        try: out.append(json.loads(line))
        except json.JSONDecodeError: out.append({"verdict": "parse_error", "raw": line[:160]})
    return out

def pg(pat):
    try:
        r = subprocess.run(["pgrep", "-f", pat], capture_output=True, text=True)
        return bool(r.stdout.strip())
    except Exception:
        return False

app = Flask(__name__, static_folder=STATIC, static_url_path="/static")

@app.route("/api/data")
def data():
    logs = {k: read_jsonl(p) for k, p in LOGS.items()}
    # flatten to unified attempt cards, newest first
    cards, run_costs_total, gains_total, accepted_total, attempts_total = [], 0.0, 0.0, 0, 0
    series = []  # cumulative gain over record index for trend chart
    for src, recs in logs.items():
        cur_cost = 0.0
        prev_cum = 0.0
        for i, r in enumerate(recs):
            v = _v(r.get("verdict"))
            c = r.get("cost_usd")
            cost_delta = None
            if isinstance(c, (int, float)):
                cost_delta = round(c - prev_cum, 4) if c >= prev_cum else round(c, 4)
                prev_cum = c
                cur_cost = c
            if v in ("retries_exhausted", "ACCEPTED", "no_action"):
                prev_cum = 0.0
            if v in ("retries_exhausted", "ACCEPTED", "no_action"):
                run_costs_total += cur_cost; cur_cost = 0.0
            g = r.get("gain")
            if v == "ACCEPTED" and isinstance(g, (int, float)):
                gains_total += g; accepted_total += 1
            attempts_total += 1
            cards.append({
                "src": src, "tier": TIER_LABEL.get(src, src), "idx": i,
                "ts": r.get("ts"), "verdict": v, "kind": STATUS_KIND.get(v, "neutral"),
                "block": r.get("block") or r.get("module") or r.get("dispatch_instance") or r.get("file"),
                "strategy": r.get("strategy") or r.get("code"), "gain": g,
                "cost": cost_delta if cost_delta is not None else r.get("cost_usd"), "model": r.get("model"),
                "story": narrative(r, src),
                "detail": {k2: r.get(k2) for k2 in
                           ("reason", "design", "edits", "closure", "post", "worst_path",
                            "gate", "rationale", "usage")
                           if r.get(k2) is not None},
            })
        run_costs_total += cur_cost
    # order: keep log order per source but interleave by ts string when present; fallback stable
    cards.sort(key=lambda c: str(c.get("ts") or ""), reverse=True)
    for c in reversed(cards):
        if c["verdict"] == "ACCEPTED" and isinstance(c["gain"], (int, float)):
            prev = series[-1][1] if series else 0.0
            series.append([c.get("ts") or "", round(prev + c["gain"], 3)])

    live = {"lines": 0, "tail": "", "age_s": None}
    if os.path.exists(RUNLOG):
        lines = open(RUNLOG, errors="replace").read().splitlines()
        live = {"lines": len(lines), "tail": "\n".join(lines[-8:]),
                "age_s": int(time.time() - os.path.getmtime(RUNLOG))}

    procs = {
        "block_orch": pg("orchestrator_latency|mldsa/orchestrator.py"),
        "chip_orch":  pg("chip_orchestrator"),
        "minerva":    pg("run.py -tp"),
        "vivado":     pg("vivado"),
        "xsim":       pg("xsimk"),
    }
    if procs["chip_orch"]:
        status, state = "CHIP LOOP RUNNING — closure search / dispatch in progress.", "run"
    elif procs["block_orch"] and procs["xsim"]:
        status, state = "AGENT RUNNING — simulating a candidate against the NIST vectors.", "run"
    elif procs["block_orch"]:
        status, state = "AGENT RUNNING — proposing, applying, or synthesizing.", "run"
    elif procs["minerva"]:
        status, state = "MINERVA RUNNING — GMU frequency-search sweep in progress.", "run"
    elif procs["vivado"]:
        status, state = "VIVADO RUNNING — a synthesis/implementation job is active.", "run"
    else:
        last = cards[0] if cards else None
        if last and last["verdict"] == "ACCEPTED":
            status, state = f"IDLE — last event was a WIN on {last.get('block')}.", "win"
        elif last and last["kind"] == "fail":
            status, state = "IDLE — last run ended without a passing edit (state reset clean).", "fail"
        else:
            status, state = "IDLE — no agent process running.", "idle"

    # per-block absolute-WNS trajectories: start at measured baseline, step by each accepted gain
    traj = {}
    for c in sorted([c for c in cards if c["verdict"] == "ACCEPTED"
                     and isinstance(c.get("gain"), (int, float)) and c.get("block")],
                    key=lambda c: str(c.get("ts") or "")):
        b = str(c["block"])
        all_bases = {k: v["base"] for d in load_baselines().get("designs", {}).values()
                     for k, v in d.get("cores", {}).items() if v.get("base") is not None}
        base = all_bases.get(b)
        if base is None: continue
        pts = traj.setdefault(b, [["baseline", base]])
        pts.append([c.get("ts") or "", round(pts[-1][1] + c["gain"], 3)])

    bl = load_baselines()
    designs = {}
    for dk, d in bl.get("designs", {}).items():
        cores = [{"block": k, "base": v.get("base"), "now": v.get("now")}
                 for k, v in d.get("cores", {}).items()]
        designs[dk] = {"label": d.get("label", dk), "chip": d.get("chip"), "cores": cores}

    return jsonify({
        "cards": cards[:200], "series": series, "designs": designs, "traj": traj,
        "explain": VERDICT_EXPLAIN,
        "totals": {"attempts": attempts_total, "accepted": accepted_total,
                   "gain_ns": round(gains_total, 3), "cost_usd": round(run_costs_total, 3)},
        "live": live, "procs": procs, "status": status, "state": state,
        "now": time.strftime("%H:%M:%S"),
    })

@app.route("/api/rules")
def rules():
    p = os.path.join(HERE, "learned_rules.jsonl")
    recs = read_jsonl(p)
    return jsonify({"rules": recs[-60:]})

@app.route("/api/minerva")
def minerva():
    import xml.etree.ElementTree as ET, glob
    out = []
    for x in glob.glob(os.path.join(HERE, "..", "minerva_ws", "*", "minerva_status", "*_MS.xml")):
        try:
            t = ET.parse(x)
            root = t.getroot()
            e = {"alg": root.attrib.get("AlgName"), "results": []}
            for r in root.iter():
                if r.tag == "Minerva_TP_Opt":
                    e["results"].append(dict(r.attrib))
            out.append(e)
        except Exception:
            pass
    return jsonify({"minerva": out, "running": pg("run.py -tp")})

@app.route("/")
def index():
    return send_from_directory(STATIC, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)


