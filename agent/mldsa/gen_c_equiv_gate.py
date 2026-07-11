# gen_c lockstep equivalence gate: pristine REF vs candidate DUT.
# Usage: python3 gen_c_equiv_gate.py [candidate_rtl_path]
import subprocess, os, shutil, tempfile, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
CHECK_DIR = os.path.join(HERE, "gen_c_check")
PRISTINE = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src/gen_c.v"
TB = "tb_gen_c_equiv.v"
def run_equiv(candidate=None):
    work = tempfile.mkdtemp(prefix="genc_equiv_")
    try:
        shutil.copy(os.path.join(CHECK_DIR, TB), work)
        src = open(PRISTINE).read()
        ref = re.sub(r"\bmodule\s+gen_c\b", "module gen_c_ref", src, count=1)
        open(os.path.join(work, "gen_c_ref.v"), "w").write(ref)
        dut_src = candidate if candidate else PRISTINE
        shutil.copy(dut_src, os.path.join(work, "gen_c.v"))
        r = subprocess.run(["iverilog", "-g2012", "-o", "equiv.vvp", "-s", "tb_gen_c_equiv",
                            TB, "gen_c_ref.v", "gen_c.v"],
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
