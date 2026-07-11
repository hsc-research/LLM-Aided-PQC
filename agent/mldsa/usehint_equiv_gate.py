# usehint lockstep equivalence gate: pristine REF vs candidate DUT.
# Usage: python3 usehint_equiv_gate.py [candidate_rtl_path]
import subprocess, os, shutil, tempfile, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
CHECK_DIR = os.path.join(HERE, "usehint_check")
PRISTINE = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src/usehint.v"
TB = "tb_usehint_equiv.v"
def run_equiv(candidate=None):
    work = tempfile.mkdtemp(prefix="uh_equiv_")
    try:
        shutil.copy(os.path.join(CHECK_DIR, TB), work)
        src = open(PRISTINE).read()
        ref = re.sub(r"\bmodule\s+usehint\b", "module usehint_ref", src, count=1)
        open(os.path.join(work, "usehint_ref.v"), "w").write(ref)
        dut_src = candidate if candidate else PRISTINE
        shutil.copy(dut_src, os.path.join(work, "usehint.v"))
        r = subprocess.run(["iverilog", "-g2012", "-o", "equiv.vvp", "-s", "tb_usehint_equiv",
                            TB, "usehint_ref.v", "usehint.v"],
                           cwd=work, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return {"status": "FAIL", "reason": "compile failed: " + r.stderr[-300:]}
        r = subprocess.run(["vvp", "equiv.vvp"], cwd=work, capture_output=True, text=True, timeout=600)
        out = r.stdout
        if "EQUIV RESULT: PASS" in out:
            checked = re.search(r"checked (\d+)", out)
            return {"status": "PASS", "reason": "lockstep match",
                    "checked": int(checked.group(1)) if checked else 0}
        first = next((l for l in out.splitlines() if "MISMATCH" in l or "COVERAGE" in l), "")
        return {"status": "FAIL", "reason": first or "no PASS line: " + out[-200:]}
    finally:
        shutil.rmtree(work, ignore_errors=True)
if __name__ == "__main__":
    print(json.dumps(run_equiv(sys.argv[1] if len(sys.argv) > 1 else None), indent=2))
