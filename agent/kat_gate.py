# HQC Agent - KAT (Known-Answer Test) Correctness Gate
# Runs the full keygen -> encap -> decap simulation chain and verifies that the
# shared secret from encap matches the shared secret from decap across all three
# security levels. Returns PASS only if all three match.
#
# This is the hard correctness constraint: any RTL change that breaks the
# shared-secret match is rejected regardless of its PPA.
#
# NOTE: This runs full behavioral simulation and is much slower than synthesis
# (several minutes). Use it to confirm a candidate before accepting it, not on
# every tweak.

import subprocess
import shutil
import os
import glob

REPO_ROOT = "."
VIVADO = "vivado"

# Simulation output directories (xsim working dirs)
KEYGEN_SIM = "test_keygen/test_keygen.sim/sim_1/behav/xsim"
ENCAP_SIM  = "test_encap/test_encap.sim/sim_1/behav/xsim"
DECAP_SIM  = "test_decap/test_decap.sim/sim_1/behav/xsim"

PARAM_SETS = ["128", "192", "256"]

def _run_tcl(tcl_path, label):
    print(f"  Running {label} simulation (this takes a few minutes)...")
    result = subprocess.run(
        [VIVADO, "-mode", "batch", "-nojournal", "-nolog", "-notrace",
         "-source", tcl_path],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        return False, f"{label} sim failed: {result.stderr[-800:]}"
    return True, "ok"

def _copy(pattern, dest_dir):
    files = glob.glob(pattern)
    os.makedirs(dest_dir, exist_ok=True)
    for f in files:
        shutil.copy(f, dest_dir)
    return len(files)

def _clean_projects():
    import shutil as sh
    for d in ["test_keygen", "test_encap", "test_decap"]:
        if os.path.isdir(d):
            sh.rmtree(d, ignore_errors=True)

def run_kat():
    print("KAT GATE: running full keygen -> encap -> decap verification")
    print("=" * 55)
    print("  Cleaning previous simulation projects...")
    _clean_projects()

    # Stage 1: keygen
    ok, msg = _run_tcl("./build/keygen/tb/keygen.tcl", "keygen")
    if not ok:
        return {"status": "FAIL", "stage": "keygen", "reason": msg}

    # Copy keygen outputs (s, h, x, y) into encap testbench dir
    n = _copy(f"{KEYGEN_SIM}/{{s,h,x,y}}_*.in", "build/encap/tb/")
    # glob doesn't expand braces; do it explicitly
    for prefix in ["s", "h", "x", "y"]:
        _copy(f"{KEYGEN_SIM}/{prefix}_*.in", "build/encap/tb/")

    # Stage 2: encap
    ok, msg = _run_tcl("./build/encap/tb/encap.tcl", "encap")
    if not ok:
        return {"status": "FAIL", "stage": "encap", "reason": msg}

    # Copy keygen + encap outputs into decap testbench dir
    for prefix in ["s", "h", "x", "y"]:
        _copy(f"{KEYGEN_SIM}/{prefix}_*.in", "build/decap/tb/")
    for prefix in ["u", "v", "d"]:
        _copy(f"{ENCAP_SIM}/{prefix}_*.in", "build/decap/tb/")

    # Stage 3: decap
    ok, msg = _run_tcl("./build/decap/tb/decap.tcl", "decap")
    if not ok:
        return {"status": "FAIL", "stage": "decap", "reason": msg}

    # Stage 4: compare shared secrets
    results = {}
    all_match = True
    for p in PARAM_SETS:
        enc_file = f"{ENCAP_SIM}/ss_output_{p}.out"
        dec_file = f"{DECAP_SIM}/ss_output_{p}.out"
        if not os.path.exists(enc_file) or not os.path.exists(dec_file):
            results[p] = "MISSING"
            all_match = False
            continue
        with open(enc_file) as f:
            enc = f.read().strip()
        with open(dec_file) as f:
            dec = f.read().strip()
        match = (enc == dec)
        results[p] = "MATCH" if match else "MISMATCH"
        if not match:
            all_match = False

    return {
        "status": "PASS" if all_match else "FAIL",
        "stage": "compare",
        "per_param": results
    }

if __name__ == "__main__":
    outcome = run_kat()
    print("\n" + "=" * 55)
    print("KAT RESULT:", outcome["status"])
    if "per_param" in outcome:
        for p, r in outcome["per_param"].items():
            print(f"  HQC-{p}: {r}")
    if outcome["status"] == "FAIL":
        print("Reason:", outcome.get("reason", outcome.get("per_param")))
