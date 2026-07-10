"""Agent loop v2.1: code-side target selection -> machine-computed ground
truth -> model designs ONE experiment -> dry-run echo (model confirms its
own diff) -> gated apply -> synth -> KAT -> human commit. Failure protocol:
gate refusal gets one ground-truth retry; second refusal, synth fail,
marginal, or KAT fail skip-lists the cluster; KAT fail also halts the run."""
import sys, os, json, shutil, subprocess, difflib, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import edit_ops, optimizer_v2, target_selector, ground_truth
from synthesizer import run_synthesis

MIN_GAIN_NS = 0.05
FLIGHT_LOG = "agent/flight_log.jsonl"

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

def log(rec):
    with open(FLIGHT_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")

def dry_run_diff(experiment):
    """Apply ops to copies in a temp dir; return unified diff text."""
    diffs = []
    with tempfile.TemporaryDirectory() as td:
        exp = json.loads(json.dumps(experiment))
        for fs in exp["files"]:
            tmp = os.path.join(td, os.path.basename(fs["path"]))
            shutil.copy(fs["path"], tmp)
            fs["__orig"], fs["path"] = fs["path"], tmp
        edit_ops.apply_experiment(exp)            # raises on any gate
        for fs in exp["files"]:
            a = open(fs["__orig"]).read().splitlines(keepends=True)
            b = open(fs["path"]).read().splitlines(keepends=True)
            diffs.append("".join(difflib.unified_diff(
                a, b, fs["__orig"], "proposed", n=2)))
    return "\n".join(diffs)

def run(module, level):
    rpt = f"./synth_out/paths/{module}_{level}_top20.rpt"
    if not os.path.exists(rpt):
        print(sh(f"python3 agent/path_extractor.py {module} {level} 20"))
    target = target_selector.select(rpt, module, level)
    if not target:
        print("NO LIVE TARGETS; run ends."); return
    gt = ground_truth.gather(target)
    print(f"TARGET (code-selected): {target['src_reg']} worst {target['worst']} "
          f"in {gt['file']}, {gt['n_sites']} sites, {gt['n_compares']} live compares")
    gt_text = json.dumps({k: gt[k] for k in
        ["file", "register", "assignment_sites", "live_compares",
         "existing_flag_machinery", "comb_sens_lists_with_reg"]}, indent=1)
    blocks = "\n...\n".join(gt["always_blocks"])
    board = open(rpt).read()[:4000]
    recon = (f"CODE-SELECTED TARGET (you do not choose targets): {target['src_reg']}, "
             f"worst slack {target['worst']}. MACHINE-COMPUTED INVENTORY (authoritative; "
             f"use these counts verbatim):\n{gt_text}\n\nCOMPLETE ALWAYS-BLOCKS:\n{blocks}")
    proposal = optimizer_v2.propose(board, "", recon_notes=recon)
    print(json.dumps(proposal, indent=2))
    if proposal["verdict"] != "experiment":
        target_selector.save_skip(target["key"], f"model: {proposal['reason'][:80]}")
        log({"target": target["key"], "verdict": "no_action"}); return

    for attempt in range(2):
        try:
            diff = dry_run_diff(proposal["experiment"])
            break
        except AssertionError as e:
            print(f"GATE REFUSED in dry run: {e}")
            if attempt == 1:
                target_selector.save_skip(target["key"], f"2x gate refusal: {e}"[:100])
                log({"target": target["key"], "verdict": "refused", "err": str(e)}); return
            proposal = optimizer_v2.propose(board, "", recon_notes=recon +
                f"\n\nYOUR EXPERIMENT WAS REFUSED: {e}\nRevise using the inventory counts.")
            print(json.dumps(proposal, indent=2))
            if proposal["verdict"] != "experiment":
                log({"target": target["key"], "verdict": "no_action_retry"}); return

    print("DRY-RUN DIFF:\n" + diff[:3000])
    confirm = optimizer_v2.propose(
        "CONFIRMATION STEP", "",
        recon_notes=f"This unified diff is exactly what your experiment produces:\n{diff[:6000]}\n"
        'If correct, return {"verdict":"experiment","reason":"confirmed", '
        '"expected_gain_ns":<your estimate>,"experiment":<the SAME experiment JSON>}. '
        "If wrong, return the corrected experiment or no_action.")
    if confirm["verdict"] != "experiment":
        target_selector.save_skip(target["key"], "model rejected own diff")
        log({"target": target["key"], "verdict": "self_rejected"}); return

    backups = edit_ops.apply_experiment(confirm["experiment"])
    pre = target["worst"]
    res = run_synthesis(module, level)
    if "error" in res:
        edit_ops.revert(backups); target_selector.save_skip(target["key"], "synth fail")
        log({"target": target["key"], "verdict": "synth_fail"}); return
    sh(f"python3 agent/path_extractor.py {module} {level} 20")
    new_t = target_selector.parse_board(rpt)
    new_worst_cluster = min((p["slack"] for p in new_t if p["src_reg"] == target["src_reg"]),
                            default=0.0)
    gain = new_worst_cluster - pre
    print(f"CLUSTER {pre} -> {new_worst_cluster} (gain {gain:+.3f}); module WNS {res['wns_ns']}")
    if gain < MIN_GAIN_NS:
        edit_ops.revert(backups); target_selector.save_skip(target["key"], f"marginal {gain:+.3f}")
        log({"target": target["key"], "verdict": "marginal", "gain": gain}); return
    kat = sh("python3 agent/hqc/kat_gate.py"); print(kat)
    if "KAT RESULT: PASS" not in kat:
        edit_ops.revert(backups); target_selector.save_skip(target["key"], "KAT FAIL")
        log({"target": target["key"], "verdict": "KAT_FAIL"})
        print("KAT FAIL: run HALTED for human review."); sys.exit(1)
    log({"target": target["key"], "verdict": "VERIFIED", "gain": gain,
         "wns": res["wns_ns"]})
    print("=== VERIFIED. Backups kept; review and commit manually. ===")

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
