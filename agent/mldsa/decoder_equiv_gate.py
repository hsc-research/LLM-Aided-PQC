# decoder lockstep equivalence gate: pristine REF vs candidate DUT.
# Usage: python3 decoder_equiv_gate.py [candidate_rtl_path]
import subprocess, os, shutil, tempfile, sys, json, re
from pathlib import Path
try:
    from .gate_result import lockstep_result, pristine_source
except ImportError:
    from gate_result import lockstep_result, pristine_source
HERE = os.path.dirname(os.path.abspath(__file__))
CHECK_DIR = os.path.join(HERE, "decoder_check")
PRISTINE = pristine_source("decoder.v")
TB = "tb_decoder_equiv.v"
def run_equiv(candidate=None):
    work = tempfile.mkdtemp(prefix="dec_equiv_")
    try:
        shutil.copy(os.path.join(CHECK_DIR, TB), work)
        src = Path(PRISTINE).read_text()
        ref = re.sub(r"\bmodule\s+decoder\b", "module decoder_ref", src, count=1)
        Path(work, "decoder_ref.v").write_text(ref)
        dut_src = candidate if candidate else PRISTINE
        shutil.copy(dut_src, os.path.join(work, "decoder.v"))
        r = subprocess.run(["iverilog", "-g2012", "-o", "equiv.vvp", "-s", "tb_decoder_equiv",
                            TB, "decoder_ref.v", "decoder.v"],
                           cwd=work, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return {"status": "FAIL", "reason": "compile failed: " + r.stderr[-300:]}
        r = subprocess.run(["vvp", "equiv.vvp"], cwd=work, capture_output=True, text=True, timeout=600)
        return lockstep_result(r)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "FAIL", "reason": str(exc)}
    finally:
        shutil.rmtree(work, ignore_errors=True)
if __name__ == "__main__":
    result = run_equiv(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
