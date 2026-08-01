"""Cross-toolchain port fix loop.

Reads the FIRST Genus error cluster only (everything after is cascade noise),
classifies it against the taxonomy, and either escalates to the human or
proposes a fix and runs it through the three-stage gate.

Every attempt is logged, including refusals and escalations. A refusal is a
result, not a failure.
"""
import re, json, subprocess, shutil, os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_templates import classify

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "port_log.jsonl")
HOST = "engr"


def newest_log(remote_dir="~/pqc/hqc/asic/scripts"):
    r = subprocess.run(["ssh", HOST, f"ls -t {remote_dir}/genus.log* | head -n 1"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def first_error(logpath):
    """First error only. Genus aborts on the first cluster; later errors are
    artifacts of that abort (F1 diagnostic hazard)."""
    r = subprocess.run(["ssh", HOST, f"grep -n -m 1 -B 8 -A 4 'Error' {logpath}"],
                       capture_output=True, text=True)
    txt = r.stdout
    m = re.search(r"\[([A-Z]+-\d+)\]", txt)
    code = m.group(1) if m else None
    f = re.search(r"in file '([^']+)' on line (\d+)", txt)
    return {"code": code, "file": f.group(1) if f else None,
            "line": int(f.group(2)) if f else None, "raw": txt[-1200:]}


def record(entry):
    entry["ts"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(LOG, "a") as fh:
        fh.write(json.dumps(entry) + "\n")
    print(f"  logged: {entry['verdict']}")


def triage(err):
    """Decide what to do. Returns (action, template)."""
    if not err["code"]:
        return "escalate", {"reason": "no error code parsed"}
    kind, tpl = classify(err["code"])
    if kind == "build_config":
        return "build_config", tpl
    if kind == "unknown":
        return "escalate", {"reason": f"unknown code {err['code']}, not in taxonomy"}
    if not tpl.get("autonomous"):
        return "escalate", tpl
    return "propose", tpl


if __name__ == "__main__":
    lp = sys.argv[1] if len(sys.argv) > 1 else newest_log()
    err = first_error(lp)
    action, tpl = triage(err)
    print(f"log={lp}")
    print(f"first error: {err['code']} in {err['file']}:{err['line']}")
    print(f"action: {action}")
    if tpl.get("constraint"):
        print(f"constraint: {tpl['constraint']}")
    record({"verdict": action, "code": err["code"], "file": err["file"],
            "line": err["line"], "template": tpl.get("name"),
            "autonomous": tpl.get("autonomous")})
