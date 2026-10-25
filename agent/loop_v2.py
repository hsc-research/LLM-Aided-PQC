"""Agent loop v2: extract -> propose -> gated apply -> synth verdict ->
KAT verdict -> human commit gate. Auto-revert on assertion failure, synth
failure, marginal gain (< MIN_GAIN_NS), or KAT failure. One experiment per
invocation; the human commits."""
import sys, os, subprocess, json, glob, re
sys.path.insert(0, os.path.dirname(__file__))
import edit_ops, optimizer_v2
from synthesizer import run_synthesis

MIN_GAIN_NS = 0.05

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True, timeout=7200).stdout

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
    """Excerpt gatherer: signals from the board, UNTRUNCATED, plus an explicit
    inventory of optimizations already present so the proposer never re-proposes
    an existing flag (lesson: maiden flight #2 refusal)."""
    import re
    sigs = set(re.findall(r"(\w+)_reg(?:_reg)?\[", paths_text))
    out = []
    flags = sh(f"grep -rn 'reg wr_in_range\\|reg rd_at_last\\|reg cnt_lt_mu\\|"
               f"reg mod_weight\\|ram_style' build/{module}/*.v")
    out.append(f"--- EXISTING OPTIMIZATIONS IN THIS BUILD (do not re-propose; "
               f"lines pairing these flags are MACHINERY, not targets) ---\n{flags}")
    # Whole always-blocks containing each board signal: counts become reading.
    import glob
    for vf in glob.glob(f"build/{module}/*.v"):
        txt = open(vf).read()
        if not any(s in txt for s in sigs):
            continue
        blocks, cur, in_blk = [], [], False
        for ln in txt.split("\n"):
            if ln.strip().startswith("always"):
                in_blk, cur = True, [ln]
            elif in_blk:
                cur.append(ln)
                if ln.strip().startswith("end") and len(ln) - len(ln.lstrip()) == 0:
                    in_blk = False
                    blk = "\n".join(cur)
                    if any(s in blk for s in sigs):
                        blocks.append(blk)
        if blocks:
            out.append(f"--- COMPLETE always-blocks from {vf} mentioning board "
                       f"signals ---\n" + "\n...\n".join(blocks[:4]))
    return "\n".join(out)

def _run_candidate(module, level):
    if module not in ("keygen", "encap", "decap") or level not in ("hqc128", "hqc192", "hqc256"):
        raise ValueError("Unsupported HQC module or parameter set")
    print(f"=== AGENT EXPERIMENT: {module}/{level} ===")
    board, detail = gather(module, level)
    print(board)
    pre_wns = run_synthesis_wns_from_board(board)
    excerpts = excerpts_for(board + detail, module)
    proposal = optimizer_v2.propose(board + "\n" + detail, excerpts)
    print(json.dumps(proposal, indent=2))
    if proposal["verdict"] != "experiment":
        print(f"NO ACTION: {proposal['reason']}"); return
    backups = None
    for attempt in range(2):
        try:
            backups = edit_ops.apply_experiment(proposal["experiment"],
                                                 allowed_paths=[p for op in ("keygen", "encap", "decap") for p in glob.glob(f"build/{op}/*.v")])
            break
        except AssertionError as e:
            print(f"GATE REFUSED (no bytes written): {e}")
            if attempt == 1:
                return
            # Feedback pass: hand the model ground truth for every op target
            # so counts become reading, not guessing. One retry only.
            fb = [f"YOUR EXPERIMENT WAS REFUSED: {e}", "GROUND TRUTH FOLLOWS:"]
            # Never interpolate untrusted proposal strings into a shell command.
            for fs in proposal.get("experiment", {}).get("files", []):
                try:
                    path = edit_ops.validate_path(fs.get("path"), [p for op in ("keygen", "encap", "decap") for p in glob.glob(f"build/{op}/*.v")])
                except edit_ops.EditError:
                    continue
                fb.append(f"--- source {path} ---")
                fb.append(path.read_text()[:12000])
            fb.append("Revise your experiment with counts derived from these "
                      "lines. Distinguish assignments (your pair sites) from "
                      "comparisons. Return the full corrected JSON.")
            proposal = optimizer_v2.propose(board + "\n" + detail, excerpts,
                                            recon_notes="\n".join(fb))
            print(json.dumps(proposal, indent=2))
            if proposal["verdict"] != "experiment":
                print(f"NO ACTION on retry: {proposal['reason']}"); return
    if backups is None:
        return
    print("Applied. Synth verdict...")
    res = run_synthesis(module, level)
    if "error" in res or res["wns_ns"] is None:
        print("SYNTH FAILED -> revert"); edit_ops.revert(backups); return
    gain = res["wns_ns"] - pre_wns
    print(f"WNS {pre_wns} -> {res['wns_ns']} (gain {gain:+.3f})")
    if gain < MIN_GAIN_NS:
        print(f"MARGINAL (< {MIN_GAIN_NS}) -> revert"); edit_ops.revert(backups); return
    print("Improvement real. KAT verdict...")
    from run_safety import run_process, gate_passed
    kat = run_process([sys.executable, "agent/hqc/kat_gate.py"])
    print(kat.stdout)
    if not gate_passed(kat):
        print("KAT FAIL -> revert"); edit_ops.revert(backups); return
    print("=== EXPERIMENT VERIFIED. Backups kept; review and commit manually. ===")
    print(f"Suggested slug: {proposal['experiment']['name']}; reason: {proposal['reason']}")
    return True

def run_synthesis_wns_from_board(board):
    import re
    m = re.search(r"^\s*1\s+(-?\d+\.\d+)", board, re.M)
    if not m:
        raise ValueError("No baseline slack in timing board")
    return float(m.group(1))

def run(module, level):
    """Legacy HQC experiment wrapped in the same rollback/locking primitives."""
    if module not in ("keygen", "encap", "decap") or level not in ("hqc128", "hqc192", "hqc256"):
        raise ValueError("Unsupported HQC module or parameter set")
    from run_safety import RunLock, SourceTransaction
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with RunLock(root), SourceTransaction(root, ["build/keygen", "build/encap", "build/decap"]) as transaction:
        if _run_candidate(module, level):
            transaction.accept()

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
