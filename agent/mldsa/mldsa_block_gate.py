# ML-DSA Block-level KAT Gate (coeff_decomposer). Returns {"status":"PASS"|"FAIL",...}
# Runs sec_lvl 2 AND 3 (both decomposition branches). PASS only if all pass.
import subprocess, os, shutil, tempfile, sys
try:
    from .gate_result import block_result
except ImportError:
    from gate_result import block_result
HERE      = os.path.dirname(os.path.abspath(__file__))
CHECK_DIR = os.path.join(HERE, "mldsa_check")
MLDSA_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mldsa_src")
TB="tb_coeff_decomposer.v"; GEN="gen_vectors.py"; DEP="decomp_map1.v"; TARGET="coeff_decomposer.v"
NVEC="200"; SEC_LEVELS=["2","3"]
def _run(cmd, cwd, timeout=120):
    try:
        r=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,timeout=timeout)
        return r.returncode,r.stdout,r.stderr
    except subprocess.TimeoutExpired:
        return 124,"","timeout"
def _one_level(work, sec_lvl):
    rc,out,err=_run([sys.executable,GEN,NVEC,sec_lvl],work)
    if rc!=0: return False,f"gen failed (sec={sec_lvl}): {err[-200:]}",0
    rc,out,err=_run(["iverilog","-g2012",f"-DTB_SEC_LVL={sec_lvl}","-o","block_kat.vvp",
                     "-s","tb_coeff_decomposer",TB,TARGET,DEP],work)
    if rc!=0: return False,f"compile failed (sec={sec_lvl}): {err[-300:]}",0
    rc,out,err=_run(["vvp","block_kat.vvp"],work)
    return block_result(rc, out, err, expected=int(NVEC))
def run_block_kat(candidate_rtl=None):
    work=tempfile.mkdtemp(prefix="mldsa_kat_")
    try:
        shutil.copy(os.path.join(CHECK_DIR,TB),work)
        shutil.copy(os.path.join(CHECK_DIR,GEN),work)
        shutil.copy(os.path.join(MLDSA_SRC,DEP),work)
        tp=candidate_rtl if candidate_rtl else os.path.join(MLDSA_SRC,TARGET)
        shutil.copy(tp,os.path.join(work,TARGET))
        results={}
        for lvl in SEC_LEVELS:
            ok,reason,checked=_one_level(work,lvl)
            results[lvl]={"ok":ok,"reason":reason,"checked":checked}
            if not ok: return {"status":"FAIL","reason":reason,"levels":results}
        return {"status":"PASS","reason":"all levels match","levels":results}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status":"FAIL","reason":str(exc)}
    finally:
        shutil.rmtree(work,ignore_errors=True)
if __name__=="__main__":
    import sys,json
    result = run_block_kat(sys.argv[1] if len(sys.argv)>1 else None)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
