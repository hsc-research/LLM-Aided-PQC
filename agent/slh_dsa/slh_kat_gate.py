#!/usr/bin/env python3
"""SLH-DSA functional gate, subprocess interface for chip_orchestrator.

Runs the vendor testbench (sign then verify) and diffs the produced
signature against the frozen golden reference. Exits 0 on PASS,
1 on FAIL, 2 on INCONCLUSIVE.

Usage: python3 agent/slh_dsa/slh_kat_gate.py [rtl_dir]

Scope note: this gate is DIFFERENTIAL, not absolute. The golden signature
was produced by unmodified SPHINCSLET RTL, so a PASS means "this edit
changed nothing observable", not "this design is correct". Corruption
validated 2026-08-25: corrupted golden -> exit 1, restored -> exit 0.
"""
import os, sys, subprocess, shutil, filecmp

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# The vendor testbench resolves data files as
#   ../../../../TECS_v8.srcs/sources_1/imports/<HASH_DATA>/
# relative to the simulation working directory, so the sim must run from a
# path exactly four levels below the data tree. Do not flatten this.
SIM_DIR = "/mnt/c/PQC/slh_sim/a/b/c/d"
DATA    = "/mnt/c/PQC/slh_sim/TECS_v8.srcs/sources_1/imports/data_sha2"
PRODUCED = os.path.join(DATA, "SIG_file0_128f_w.hex")
GOLDEN   = os.path.join(REPO, "agent", "slh_dsa", "gate", "SIG_file0_128f_w.hex")

DEFAULT_RTL = "/mnt/c/PQC/hqc/agent/slh_dsa/slh_src"


def run_equiv(rtl_dir=DEFAULT_RTL):
    """Returns {"status": "PASS"|"FAIL"|"ERROR", "reason": str}."""
    if not os.path.exists(GOLDEN):
        return {"status": "ERROR", "reason": f"golden missing: {GOLDEN}"}

    # Never read a stale signature: a sim that dies early would otherwise be
    # judged against the previous run's output.
    if os.path.exists(PRODUCED):
        os.remove(PRODUCED)

    env = dict(os.environ, SLH_RTL=rtl_dir)
    r = subprocess.run(["bash", os.path.join(SIM_DIR, "run_sim.sh")],
                       cwd=SIM_DIR, env=env, capture_output=True, text=True,
                       timeout=3600)
    out = r.stdout

    if "xvlog errors: 0" not in out:
        return {"status": "ERROR", "reason": "xvlog errors, see xvlog.log"}
    if "xelab errors: 0" not in out:
        return {"status": "ERROR", "reason": "xelab errors, see xelab.log"}
    if not os.path.exists(PRODUCED):
        return {"status": "FAIL", "reason": "no signature produced"}
    if not filecmp.cmp(GOLDEN, PRODUCED, shallow=False):
        return {"status": "FAIL", "reason": "signature differs from golden"}
    if "The signature is matched" not in out:
        return {"status": "FAIL", "reason": "testbench verify did not report match"}
    return {"status": "PASS", "reason": "signature matches golden, verify OK"}


if __name__ == "__main__":
    rtl = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RTL
    g = run_equiv(rtl)
    print(f"SLH-DSA GATE: {g['status']} - {g['reason']}")
    sys.exit({"PASS": 0, "FAIL": 1}.get(g["status"], 2))
