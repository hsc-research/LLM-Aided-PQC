# makehint lockstep equivalence gate. Usage: python3 makehint_equiv_gate.py [candidate]
import subprocess, os, shutil, tempfile, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
CHECK_DIR = os.path.join(HERE, "makehint_check")
PRISTINE = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src/makehint.v"
TB = "tb_makehint_equiv.v"
def run_equiv(candidate=None):
    work = tempfile.mkdtemp(prefix="mh_equiv_")
    try:
        shutil.copy(os.path.join(CHECK_DIR, TB), work)
        src = open(PRISTINE).read()
        ref = re.sub(r"\bmodule\s+makehint\b", "module makehint_ref", src, count=1)
        open(os.path.join(work, "makehint_ref.v"), "w").write(ref)
        shutil.copy(candidate if candidate else PRISTINE, os.path.join(work, "makehint.v"))
        r = subprocess.run(["iverilog","-g2012","-o","e.vvp","-s","tb_makehint_equiv",
                            TB,"makehint_ref.v","makehint.v"],cwd=work,capture_output=True,text=True,timeout=120)
        if r.returncode != 0:
            return {"status":"FAIL","reason":"compile failed: "+r.stderr[-300:]}
        r = subprocess.run(["vvp","e.vvp"],cwd=work,capture_output=True,text=True,timeout=600)
        out = r.stdout
        if "EQUIV RESULT: PASS" in out:
            c = re.search(r"checked (\d+)", out)
            return {"status":"PASS","reason":"lockstep match","checked":int(c.group(1)) if c else 0}
        first = next((l for l in out.splitlines() if "MISMATCH" in l), "")
        return {"status":"FAIL","reason":first or "no PASS line: "+out[-200:]}
    finally:
        shutil.rmtree(work, ignore_errors=True)
if __name__ == "__main__":
    print(json.dumps(run_equiv(sys.argv[1] if len(sys.argv)>1 else None), indent=2))
