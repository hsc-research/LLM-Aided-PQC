#!/usr/bin/env python3
"""Local agent dashboard: reads orchestrator/latency/flight jsonl logs.
Usage: python3 agent/dashboard.py   ->  http://localhost:5000
Read-only; safe to run while the orchestrator is running."""
import json, os, time
from flask import Flask, jsonify, Response

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = {
    "orchestrator": os.path.join(HERE, "mldsa", "orchestrator_log.jsonl"),
    "latency":      os.path.join(HERE, "mldsa", "latency_log.jsonl"),
    "flight":       os.path.join(HERE, "flight_log.jsonl"),
}
RUNLOG = os.path.join(HERE, "mldsa", "fullkat_run.log")

app = Flask(__name__)

def read_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            out.append({"verdict": "parse_error", "raw": line[:120]})
    return out

@app.route("/api/data")
def data():
    logs = {k: read_jsonl(p) for k, p in LOGS.items()}
    summary = []
    for src, recs in logs.items():
        acc = [r for r in recs if r.get("verdict") == "ACCEPTED"]
        gains = [r.get("gain", 0) for r in acc if isinstance(r.get("gain"), (int, float))]
        summary.append({
            "source": src, "records": len(recs), "accepted": len(acc),
            "total_gain_ns": round(sum(gains), 3),
            "last_ts": recs[-1].get("ts", "") if recs else "",
        })
    live = {"lines": 0, "tail": "", "mtime": ""}
    if os.path.exists(RUNLOG):
        txt = open(RUNLOG, errors="replace").read()
        lines = txt.splitlines()
        live = {"lines": len(lines), "tail": "\n".join(lines[-6:]),
                "mtime": time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(RUNLOG)))}
    return jsonify({"logs": logs, "summary": summary, "live": live,
                    "now": time.strftime("%H:%M:%S")})

PAGE = """<!doctype html><html><head><title>LLM-Aided-PQC Agent Dashboard</title>
<meta charset="utf-8">
<style>
body{font-family:ui-monospace,Consolas,monospace;background:#0d1117;color:#c9d1d9;margin:20px}
h1{font-size:18px;color:#e6edf3} h2{font-size:14px;color:#8b949e;margin:18px 0 6px}
table{border-collapse:collapse;width:100%;font-size:12px}
th,td{border:1px solid #21262d;padding:4px 8px;text-align:left;vertical-align:top}
th{background:#161b22;color:#8b949e;position:sticky;top:0}
tr:hover{background:#161b22}
.v-ACCEPTED{color:#3fb950;font-weight:bold}
.v-gate_fail,.v-synth_fail,.v-abort,.v-retries_exhausted{color:#f85149}
.v-no_action,.v-refused{color:#d29922}
.v-marginal{color:#a371f7}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;background:#21262d;margin-right:8px;font-size:12px}
#live{background:#161b22;border:1px solid #21262d;padding:8px;white-space:pre-wrap;font-size:11px;max-height:120px;overflow:auto}
.gain-pos{color:#3fb950}.gain-neg{color:#f85149}
small{color:#484f58}
</style></head><body>
<h1>LLM-Aided-PQC Agent Dashboard <small id="clock"></small></h1>
<div id="summary"></div>
<h2>Live sim (fullkat_run.log) <small id="livemeta"></small></h2>
<div id="live"></div>
<h2>Latency tier (latency_log.jsonl)</h2>
<div id="latency"></div>
<h2>Latency-preserving tier (orchestrator_log.jsonl)</h2>
<div id="orch"></div>
<h2>HQC flight log (flight_log.jsonl)</h2>
<div id="flight"></div>
<script>
function esc(s){return String(s==null?"":s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]))}
function vclass(v){v=String(v||"");if(v.startsWith("marginal"))return"v-marginal";return"v-"+v}
function gcell(g){if(typeof g!=="number")return"";return `<span class="${g>=0?'gain-pos':'gain-neg'}">${g>0?'+':''}${g}</span>`}
function table(recs){
  if(!recs.length)return"<small>empty</small>";
  const cols=["ts","block","verdict","strategy","gain","wns_pre","wns_post","reason","design"];
  let h="<table><tr>"+cols.map(c=>`<th>${c}</th>`).join("")+"</tr>";
  for(const r of recs.slice().reverse().slice(0,60)){
    h+="<tr>"+cols.map(c=>{
      let v=r[c];
      if(c==="verdict")return`<td class="${vclass(v)}">${esc(v)}</td>`;
      if(c==="gain")return`<td>${gcell(v)}</td>`;
      if(c==="reason"||c==="design")return`<td>${esc(String(v||"").slice(0,110))}</td>`;
      return`<td>${esc(v)}</td>`;
    }).join("")+"</tr>";
  }
  return h+"</table>";
}
async function tick(){
  try{
    const d=await(await fetch("/api/data")).json();
    document.getElementById("clock").textContent="updated "+d.now;
    document.getElementById("summary").innerHTML=d.summary.map(s=>
      `<span class="pill">${s.source}: ${s.records} recs, <b class="v-ACCEPTED">${s.accepted} accepted</b>, ${s.total_gain_ns}ns total</span>`).join("");
    document.getElementById("livemeta").textContent=`${d.live.lines} lines, mtime ${d.live.mtime}`;
    document.getElementById("live").textContent=d.live.tail||"(no run log)";
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
