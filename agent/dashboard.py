#!/usr/bin/env python3
"""Local agent dashboard v2: plain-English status + logs.
Usage: python3 agent/dashboard.py  ->  http://localhost:5000
Read-only; safe while the orchestrator runs."""
import json, os, time, subprocess
from flask import Flask, jsonify, Response

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = {
    "latency":      os.path.join(HERE, "mldsa", "latency_log.jsonl"),
    "orchestrator": os.path.join(HERE, "mldsa", "orchestrator_log.jsonl"),
    "flight":       os.path.join(HERE, "flight_log.jsonl"),
}
RUNLOG = os.path.join(HERE, "mldsa", "fullkat_run.log")

VERDICT_EXPLAIN = {
    "ACCEPTED": "Win: edit passed all correctness checks AND improved timing enough to keep. Committed manually after review.",
    "gate_fail": "Edit produced wrong outputs in simulation (correctness check failed). Auto-reverted; divergence info fed back to the model for the next try.",
    "synth_fail": "Edit passed correctness but Vivado synthesis errored. Auto-reverted.",
    "no_action": "Model looked at the code and decided no safe improvement exists. Nothing changed.",
    "refused": "Orchestrator rejected the model's proposal before applying it (bad anchors, repeat attempt, or closed strategy).",
    "abort": "Run stopped before any edit (pre-checks failed).",
    "retries_exhausted": "Model made multiple attempts, none passed. Files reset to last-good state.",
    "parse_error": "A log line could not be read.",
}

app = Flask(__name__)

def read_jsonl(path):
    if not os.path.exists(path): return []
    out = []
    for line in open(path):
        line = line.strip()
        if not line: continue
        try: out.append(json.loads(line))
        except json.JSONDecodeError: out.append({"verdict": "parse_error", "raw": line[:120]})
    return out

def marginal_note(v):
    return ("Edit was correct but timing gain too small to keep (threshold 0.05ns). Auto-reverted."
            if str(v).startswith("marginal") else None)

def agent_running():
    try:
        r = subprocess.run(["pgrep", "-f", "orchestrator_latency|orchestrator.py"],
                           capture_output=True, text=True)
        return bool(r.stdout.strip())
    except Exception:
        return False

def sim_running():
    try:
        r = subprocess.run(["pgrep", "-f", "xsimk"], capture_output=True, text=True)
        return bool(r.stdout.strip())
    except Exception:
        return False

@app.route("/api/data")
def data():
    logs = {k: read_jsonl(p) for k, p in LOGS.items()}
    summary = []
    for src, recs in logs.items():
        acc = [r for r in recs if r.get("verdict") == "ACCEPTED"]
        gains = [r.get("gain", 0) for r in acc if isinstance(r.get("gain"), (int, float))]
        cost = 0.0
        for r in recs:
            c = r.get("cost_usd")
            if isinstance(c, (int, float)) and c > cost and r.get("verdict") in ("retries_exhausted", "ACCEPTED"):
                pass
        # cost_usd is cumulative within a run; sum the final record of each run
        run_costs, cur = [], 0.0
        for r in recs:
            c = r.get("cost_usd")
            if isinstance(c, (int, float)):
                cur = c
            if r.get("verdict") in ("retries_exhausted", "ACCEPTED", "no_action"):
                run_costs.append(cur); cur = 0.0
        if cur: run_costs.append(cur)
        summary.append({"source": src, "records": len(recs), "accepted": len(acc),
                        "total_gain_ns": round(sum(gains), 3),
                        "total_cost_usd": round(sum(run_costs), 3)})
    live = {"lines": 0, "tail": "", "age_s": None}
    if os.path.exists(RUNLOG):
        lines = open(RUNLOG, errors="replace").read().splitlines()
        live = {"lines": len(lines), "tail": "\n".join(lines[-6:]),
                "age_s": int(time.time() - os.path.getmtime(RUNLOG))}
    # plain-english "what is happening right now"
    running, simming = agent_running(), sim_running()
    lat = logs["latency"]
    last = lat[-1] if lat else None
    if running and simming:
        status = ("AGENT RUNNING — currently simulating a candidate edit against all 75 NIST "
                  "test vectors (~90s per run). Watch 'lines' climb below.")
        state = "run"
    elif running:
        status = ("AGENT RUNNING — between simulations: asking the LLM for a proposal, "
                  "applying edits, or synthesizing. New table rows appear per attempt.")
        state = "run"
    elif last and last.get("verdict") == "ACCEPTED":
        status = f"IDLE — last run ended in a WIN on '{last.get('block')}' (+{last.get('gain')}ns). Review and commit."
        state = "win"
    elif last and last.get("verdict") == "retries_exhausted":
        status = ("IDLE — last run used all retries without a passing edit. Files were reset "
                  "to last-good state. See attempts below for how close it got.")
        state = "fail"
    else:
        status = "IDLE — no orchestrator process running."
        state = "idle"
    return jsonify({"logs": logs, "summary": summary, "live": live, "status": status,
                    "state": state, "explain": VERDICT_EXPLAIN,
                    "now": time.strftime("%H:%M:%S")})

PAGE = """<!doctype html><html><head><title>PQC Agent Dashboard</title><meta charset="utf-8">
<style>
body{font-family:ui-monospace,Consolas,monospace;background:#0d1117;color:#c9d1d9;margin:20px;max-width:1200px}
h1{font-size:18px;color:#e6edf3}h2{font-size:14px;color:#8b949e;margin:20px 0 4px}
.sub{font-size:11px;color:#8b949e;margin:0 0 8px}
#status{padding:10px 14px;border-radius:6px;font-size:13px;margin:10px 0;border:1px solid #30363d}
.s-run{background:#0c2d6b33;border-color:#1f6feb}.s-win{background:#033d1633;border-color:#3fb950}
.s-fail{background:#67060c33;border-color:#f85149}.s-idle{background:#161b22}
table{border-collapse:collapse;width:100%;font-size:12px}
th,td{border:1px solid #21262d;padding:4px 8px;text-align:left;vertical-align:top}
th{background:#161b22;color:#8b949e}tr:hover{background:#161b22}
.v-ACCEPTED{color:#3fb950;font-weight:bold}
.v-gate_fail,.v-synth_fail,.v-abort,.v-retries_exhausted{color:#f85149}
.v-no_action,.v-refused{color:#d29922}.v-marginal{color:#a371f7}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;background:#21262d;margin-right:8px;font-size:12px}
#live{background:#161b22;border:1px solid #21262d;padding:8px;white-space:pre-wrap;font-size:11px;max-height:110px;overflow:auto}
.gain-pos{color:#3fb950}.gain-neg{color:#f85149}
small{color:#484f58}
#legend{font-size:11px;color:#8b949e;background:#161b22;border:1px solid #21262d;padding:8px;border-radius:6px;margin:8px 0}
#legend b{color:#c9d1d9}
details{margin:2px 0}summary{cursor:pointer}
</style></head><body>
<h1>PQC Agent Dashboard <small id="clock"></small></h1>
<div id="status" class="s-idle">loading…</div>
<div id="summary"></div>
<details id="legend"><summary>What do the verdicts mean? (click)</summary><div id="legendbody"></div></details>
<h2>Live simulation output</h2>
<p class="sub">Tail of the current/most-recent correctness run. "WRONG" lines = mismatched output bytes vs the official NIST answers. "testbench done" + zero WRONG = pass.</p>
<div id="live"></div>
<h2>Latency tier — pipelining edits (change cycle timing, full 75-vector check)</h2>
<p class="sub">Autonomous attempts to insert pipeline registers. Each row = one propose→apply→verify cycle. gate_fail rows include the model's design idea; the divergence data is fed back so the next attempt improves.</p>
<div id="latency"></div>
<h2>Latency-preserving tier — same-cycle logic rewrites</h2>
<p class="sub">Older autonomous tier: rewrites that must produce identical outputs on identical cycles.</p>
<div id="orch"></div>
<h2>HQC flight log</h2>
<p class="sub">Historical record from the HQC accelerator work: wins, refusals, no-actions.</p>
<div id="flight"></div>
<script>
function esc(s){return String(s==null?"":s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]))}
function vclass(v){v=String(v||"");if(v.startsWith("marginal"))return"v-marginal";return"v-"+v}
function gcell(g){if(typeof g!=="number")return"";return `<span class="${g>=0?'gain-pos':'gain-neg'}">${g>0?'+':''}${g}</span>`}
function table(recs){
  if(!recs.length)return"<small>empty</small>";
  const cols=["ts","block","verdict","strategy","gain","cost_usd","model","reason","design"];
  let h="<table><tr>"+cols.map(c=>`<th>${c}</th>`).join("")+"</tr>";
  for(const r of recs.slice().reverse().slice(0,40)){
    h+="<tr>"+cols.map(c=>{
      let v=r[c];
      if(c==="verdict")return`<td class="${vclass(v)}" title="${esc(v)}">${esc(v)}</td>`;
      if(c==="gain")return`<td>${gcell(v)}</td>`;
      if(c==="reason"||c==="design")return`<td>${esc(String(v||"").slice(0,140))}</td>`;
      return`<td>${esc(v)}</td>`;
    }).join("")+"</tr>";
  }
  return h+"</table>";
}
async function tick(){
  try{
    const d=await(await fetch("/api/data")).json();
    document.getElementById("clock").textContent="updated "+d.now;
    const st=document.getElementById("status");
    st.textContent=d.status; st.className="s-"+d.state;
    document.getElementById("summary").innerHTML=d.summary.map(s=>
      `<span class="pill">${s.source}: ${s.records} attempts, <b class="v-ACCEPTED">${s.accepted} wins</b>${s.total_gain_ns?`, ${s.total_gain_ns}ns gained`:""}${s.total_cost_usd?`, <b>$${s.total_cost_usd} API</b>`:""}</span>`).join("");
    document.getElementById("legendbody").innerHTML=Object.entries(d.explain).map(([k,v])=>
      `<div><b class="${vclass(k)}">${k}</b> — ${esc(v)}</div>`).join("");
    document.getElementById("live").textContent=(d.live.tail||"(no run log)")+
      (d.live.age_s!=null?`\n[log last updated ${d.live.age_s}s ago — if agent is running and this exceeds ~120s, the sim may be hung]`:"");
    document.getElementById("latency").innerHTML=table(d.logs.latency);
    document.getElementById("orch").innerHTML=table(d.logs.orchestrator);
    document.getElementById("flight").innerHTML=table(d.logs.flight);
  }catch(e){document.getElementById("clock").textContent="fetch error";}
}
tick();setInterval(tick,5000);
</script></body></html>"""

@app.route("/")
def index():
    return Response(PAGE, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
