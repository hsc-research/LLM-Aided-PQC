"""Agent loop v2: extract -> propose -> gated apply -> synth verdict ->
KAT verdict -> human commit gate. Auto-revert on assertion failure, synth
failure, marginal gain (< MIN_GAIN_NS), or KAT failure. One experiment per
invocation; the human commits."""
import sys, os, subprocess, json
sys.path.insert(0, os.path.dirname(__file__))
import edit_ops, optimizer_v2
from synthesizer import run_synthesis

MIN_GAIN_NS = 0.05

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

def gather(module, level, n_detail=2):
    board = sh(f"python3 agent/path_extractor.py {module} {level} 20")
    rpt = f"./synth_out/paths/{module}_{level}_top20.rpt"
    detail = ""
    if os.path.exists(rpt):
        # First n_detail full delay tables for fingerprinting
        txt = open(rpt).read()
        chunks = txt.split("Slack (VIOLATED)")
        detail = "Slack (VIOLATED)".join([""] + chunks[1:n_detail+1])
    return board, detail

def excerpts_for(paths_text, module):
    """Crude excerpt gatherer: grep counters/signals named in the board out of
    the build dir so the proposer sees verbatim text its ops must match."""
    import re
    sigs = set(re.findall(r"(\w+)_reg(?:_reg)?\[", paths_text))
    out = []
    for sig in list(sigs)[:6]:
        hits = sh(f"grep -rn '{sig}' build/{module}/*.v | head -25")
        if hits:
            out.append(f"--- {sig} ---\n{hits}")
    return "\n".join(out)

def run(module, level):
    print(f"=== AGENT EXPERIMENT: {module}/{level} ===")
    board, detail = gather(module, level)
    print(board)
    pre_wns = run_synthesis_wns_from_board(board)
    excerpts = excerpts_for(board + detail, module)
    proposal = optimizer_v2.propose(board + "\n" + detail, excerpts)
    print(json.dumps(proposal, indent=2))
    if proposal["verdict"] != "experiment":
        print(f"NO ACTION: {proposal['reason']}"); return
    try:
        backups = edit_ops.apply_experiment(proposal["experiment"])
    except AssertionError as e:
        print(f"GATE REFUSED (no bytes written): {e}"); return
    print("Applied. Synth verdict...")
    res = run_synthesis(module, level)
    if "error" in res or res["wns_ns"] is None:
        print("SYNTH FAILED -> revert"); edit_ops.revert(backups); return
    gain = res["wns_ns"] - pre_wns
    print(f"WNS {pre_wns} -> {res['wns_ns']} (gain {gain:+.3f})")
    if gain < MIN_GAIN_NS:
        print(f"MARGINAL (< {MIN_GAIN_NS}) -> revert"); edit_ops.revert(backups); return
    print("Improvement real. KAT verdict...")
    kat = sh("python3 agent/kat_gate.py")
    print(kat)
    if "KAT RESULT: PASS" not in kat:
        print("KAT FAIL -> revert"); edit_ops.revert(backups); return
    print("=== EXPERIMENT VERIFIED. Backups kept; review and commit manually. ===")
    print(f"Suggested slug: {proposal['experiment']['name']}; reason: {proposal['reason']}")

def run_synthesis_wns_from_board(board):
    import re
    m = re.search(r"^\s*1\s+(-?\d+\.\d+)", board, re.M)
    return float(m.group(1)) if m else 0.0

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
