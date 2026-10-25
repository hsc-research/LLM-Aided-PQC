# makehint lockstep equivalence gate. Usage: python3 makehint_equiv_gate.py [candidate]
import subprocess, os, shutil, tempfile, sys, json, re
from pathlib import Path
try:
    from .gate_result import lockstep_result, pristine_source
except ImportError:
    from gate_result import lockstep_result, pristine_source
HERE = os.path.dirname(os.path.abspath(__file__))
CHECK_DIR = os.path.join(HERE, "makehint_check")
PRISTINE = pristine_source("makehint.v")
TB = "tb_makehint_equiv.v"
def run_equiv(candidate=None):
    work = tempfile.mkdtemp(prefix="mh_equiv_")
    try:
        shutil.copy(os.path.join(CHECK_DIR, TB), work)
        src = Path(PRISTINE).read_text()
        ref = re.sub(r"\bmodule\s+makehint\b", "module makehint_ref", src, count=1)
        Path(work, "makehint_ref.v").write_text(ref)
        shutil.copy(candidate if candidate else PRISTINE, os.path.join(work, "makehint.v"))
        r = subprocess.run(["iverilog","-g2012","-o","e.vvp","-s","tb_makehint_equiv",
                            TB,"makehint_ref.v","makehint.v"],cwd=work,capture_output=True,text=True,timeout=120)
        if r.returncode != 0:
            return {"status":"FAIL","reason":"compile failed: "+r.stderr[-300:]}
        r = subprocess.run(["vvp","e.vvp"],cwd=work,capture_output=True,text=True,timeout=600)
        return lockstep_result(r)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "FAIL", "reason": str(exc)}
    finally:
        shutil.rmtree(work, ignore_errors=True)
if __name__ == "__main__":
    result = run_equiv(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
