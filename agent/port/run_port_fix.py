"""Autonomous port fix: propose -> apply -> 3-stage gate -> accept or revert.

Stage 2 runs Genus in asic/portwork/ so it cannot collide with other jobs
(documentation standard section 10).
"""
import sys, os, json, shutil, subprocess, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from propose_fix import propose, apply_edit, apply_move
from port_gate import stage1_pure_reorder, stage3_kat
from fix_templates import TEMPLATES

REPO = "/mnt/c/PQC/hqc"
HOST = "engr"
LOG  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "port_log.jsonl")
BUILDS = ["keygen", "encap", "decap", "joint_design"]


def genus_accepts(fname):
    """Stage 2. Returns (ok, detail)."""
    subprocess.run(["rsync", "-az", f"{REPO}/build/joint_design/{fname}",
                    f"{HOST}:~/pqc/hqc/build/joint_design/"], check=True)
    # Genus stays resident after read_hdl finishes, so run it in the
    # background, poll the log, then reap. Blocking here cost 15 min per file.
    import time
    subprocess.run(["ssh", HOST,
        "cd ~/pqc/hqc/asic/portwork && nohup bash -c 'GENUS_FILE="
        "../../build/joint_design/" + fname + " timeout 300 genus -no_gui "
        "-f parse_check.tcl' > /dev/null 2>&1 &"], capture_output=True)
    for _ in range(60):
        time.sleep(5)
        chk = subprocess.run(["ssh", HOST,
            "L=$(ls -t ~/pqc/hqc/asic/portwork/genus.log* | head -n 1); "
            "grep -cE '^PARSE_OK$|^Error' $L"], capture_output=True, text=True)
        if chk.stdout.strip() not in ("", "0"):
            break
    subprocess.run(["ssh", HOST, "pkill -u alco9414 -f parse_check.tcl"],
                   capture_output=True)
    # Match the emitted line only. "PARSE_OK" also appears in the echoed
    # source line, so a plain count returns 2 on success.
    r = subprocess.run(["ssh", HOST,
        "grep -c '^PARSE_OK$' $(ls -t ~/pqc/hqc/asic/portwork/genus.log* | head -n 1)"],
        capture_output=True, text=True)
    if r.stdout.strip() not in ("", "0"):
        return True, "genus accepts"
    e = subprocess.run(["ssh", HOST,
        "grep -m 1 -A 2 '^Error' $(ls -t ~/pqc/hqc/asic/portwork/genus.log* | head -n 1)"],
        capture_output=True, text=True)
    return False, e.stdout.strip()[:400]


def record(e):
    e["ts"] = datetime.datetime.now().isoformat(timespec="seconds")
    open(LOG, "a").write(json.dumps(e) + "\n")


def run(fname, code, error_text, do_kat=True):
    src_path = f"{REPO}/hardware/{fname}"          # caller passes relative path
    if not os.path.exists(src_path):
        return record_and_return({"verdict": "escalate", "file": fname,
                                  "reason": f"source not found: {src_path}"})

    tpl = TEMPLATES.get(code, {})
    if not tpl.get("autonomous"):
        return record_and_return({"verdict": "refuse", "file": fname, "code": code,
                                  "reason": tpl.get("constraint", "not autonomous")})

    base = os.path.basename(fname)
    bak = src_path + ".bak"
    shutil.copy(src_path, bak)
    print(f"[{base}] proposing fix for {code}")
    edit = propose(code, base, open(src_path).read(), error_text)
    if edit.get("verdict") not in ("edit", "move"):
        os.remove(bak)
        return record_and_return({"verdict": "refuse", "file": base, "code": code,
                                  "reason": edit.get("reason"), "raw": edit.get("raw"),
                                  "usage": edit.get("_usage")})

    # A hoist must not delete anything. Allowing deletions in a VLOGPT-20 fix
    # would skip stage 1, the strongest check, so refuse instead.
    if edit.get("deletes") and code != "VLOGPT-22":
        shutil.copy(bak, src_path); os.remove(bak)
        return record_and_return({"verdict": "refuse", "file": base, "code": code,
                                  "reason": f"proposal for {code} contained deletions; "
                                            f"only VLOGPT-22 may delete",
                                  "usage": edit.get("_usage")})

    if edit["verdict"] == "move":
        mv = edit.get("moves")
        if mv is None and edit.get("first_line") is not None:
            mv = [{"first_line": edit["first_line"],
                   "last_line": edit["last_line"],
                   "after_line": edit["after_line"]}]
        mv = mv or []                                    # deletes-only proposal
        mv = sorted(mv, key=lambda m: m["first_line"], reverse=True)
        ok, msg = True, ""
        for m in mv:
            ok, d = apply_move(src_path, m["first_line"], m["last_line"],
                               m["after_line"])
            msg += d + "; "
            if not ok:
                break
        if ok and edit.get("deletes"):
            lines = open(src_path).readlines()
            for ln in sorted(edit["deletes"], reverse=True):
                if 1 <= ln <= len(lines):
                    msg += f"deleted L{ln}: {lines[ln-1].strip()[:40]}; "
                    del lines[ln-1]
            open(src_path, "w").writelines(lines)
    else:
        ok, msg = apply_edit(src_path, edit)
    print(f"  apply: {msg}")
    if not ok:
        shutil.copy(bak, src_path); os.remove(bak)
        return record_and_return({"verdict": "apply_fail", "file": base,
                                  "code": code, "reason": msg})

    gate = []
    if edit.get("deletes"):
        # A deletion is not a reordering, so stage 1 cannot apply. The
        # guarantee comes from stage 2 plus KAT. Record the skip explicitly
        # so the record cannot imply a check that never ran.
        ok, d = True, "skipped: proposal contains deletions"
        gate.append(("pure_reorder", None, d))
    else:
        ok, d = stage1_pure_reorder(bak, src_path)
        gate.append(("pure_reorder", ok, d))
    print(f"  stage1: {d}")
    if ok:
        # propagate to build dirs before the tool and KAT see them
        for b in BUILDS:
            bp = f"{REPO}/build/{b}/{base}"
            if os.path.exists(bp):
                shutil.copy(src_path, bp)
        ok, d = genus_accepts(base); gate.append(("tool_accepts", ok, d))
        print(f"  stage2: {d}")
    if ok and do_kat:
        ok, d = stage3_kat("python3 agent/hqc/kat_gate.py", cwd=REPO)
        gate.append(("kat", ok, d)); print(f"  stage3: {d}")
    elif ok:
        gate.append(("kat", None, "skipped by request"))

    if not ok:
        shutil.copy(bak, src_path)
        for b in BUILDS:
            bp = f"{REPO}/build/{b}/{base}"
            if os.path.exists(bp): shutil.copy(bak, bp)
        print("  REVERTED")
        return record_and_return({"verdict": "gate_fail", "file": base, "code": code,
                                  "gate": gate, "usage": edit.get("_usage")})

    os.remove(bak)
    return record_and_return({"verdict": "ACCEPTED", "file": base, "code": code,
                              "rationale": edit.get("rationale"),
                              "gate": gate, "usage": edit.get("_usage")})


def record_and_return(e):
    record(e); print(f"  verdict: {e['verdict']}")
    return e
