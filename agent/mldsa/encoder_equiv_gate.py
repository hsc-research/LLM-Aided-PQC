#!/usr/bin/env python3
"""Encoder latency-tolerant equivalence gate.
Pristine (gold) vs candidate under identical stimulus; output streams sampled
on each DUT's own valid_o&&ready_o and compared by value+order per
(sec_lvl x encode_mode) config. Verifies latency-CHANGING candidates
correctly (same scheme as the validated coeff_decomposer latency-tolerant
gate). Gold deps are isolated copies, so candidate edits to
uncenter_coeff.v / zero_strip.v are also caught.

Usage: python3 agent/mldsa/encoder_equiv_gate.py [candidate_dir]
  candidate_dir default: agent/mldsa/mldsa_src (files encoder.v,
  uncenter_coeff.v, zero_strip.v; missing files fall back to pristine).
Contract: run_equiv(candidate_dir) -> {"status","reason","words"}.
"""
import os, re, sys, json, shutil, subprocess, tempfile

PRISTINE = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_CAND = os.path.join(REPO, "agent/mldsa/mldsa_src")
TB = os.path.join(HERE, "encoder_check", "tb_encoder.v")
FILES = ("encoder.v", "uncenter_coeff.v", "zero_strip.v")

def _gold_rename(src):
    src = re.sub(r"\bmodule encoder\b", "module encoder_gold", src)
    src = re.sub(r"\bmodule uncenter_coeff\b", "module uncenter_coeff_gold", src)
    src = re.sub(r"\bmodule zero_strip\b", "module zero_strip_gold", src)
    src = src.replace("uncenter_coeff UNCENTER", "uncenter_coeff_gold UNCENTER")
    src = src.replace("zero_strip Z_STRIP", "zero_strip_gold Z_STRIP")
    return src

def run_equiv(candidate_dir=None):
    cand = candidate_dir or DEFAULT_CAND
    work = tempfile.mkdtemp(prefix="encgate_")
    try:
        srcs = [TB]
        for f in FILES:
            # gold from pristine, renamed + isolated
            g = os.path.join(work, "gold_" + f)
            open(g, "w").write(_gold_rename(open(os.path.join(PRISTINE, f)).read()))
            srcs.append(g)
            # candidate: candidate_dir if present, else pristine
            cp = os.path.join(cand, f)
            if not os.path.exists(cp):
                cp = os.path.join(PRISTINE, f)
            c = os.path.join(work, f)
            shutil.copy(cp, c)
            srcs.append(c)
        sim = os.path.join(work, "sim")
        r = subprocess.run(["iverilog", "-o", sim] + srcs,
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return {"status": "FAIL", "reason": "compile: " + r.stderr[-300:]}
        r = subprocess.run(["vvp", sim], capture_output=True, text=True, timeout=600)
        out = r.stdout
        words = sum(int(m) for m in re.findall(r"done: (\d+) words", out))
        if "GATE RESULT: PASS" in out:
            return {"status": "PASS", "reason": "all 18 configs stream-match", "words": words}
        fails = [l for l in out.splitlines() if "MISMATCH" in l]
        return {"status": "FAIL", "reason": (fails[0] if fails else "no PASS marker"),
                "words": words}
    finally:
        shutil.rmtree(work, ignore_errors=True)

if __name__ == "__main__":
    cd = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(run_equiv(cd), indent=2))
