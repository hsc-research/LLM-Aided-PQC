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
from pathlib import Path

try:
    from .gate_result import encoder_result, pristine_source
except ImportError:
    from gate_result import encoder_result, pristine_source
PRISTINE = pristine_source()
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_CAND = os.path.join(REPO, "agent/mldsa/mldsa_src")
TB = os.path.join(HERE, "encoder_check", "tb_encoder.v")
FILES = ("encoder.v", "uncenter_coeff.v", "zero_strip.v")

def _gold_rename(src):
    src = re.sub(r"\bmodule encoder\b", "module encoder_gold", src)
    # debug tap: gold drain events
    src = src.replace(
        "PISO <= (PISO >> W) | ({192'd0, stripped} << piso_len_next);",
        "begin PISO <= (PISO >> W) | ({192'd0, stripped} << piso_len_next); $display(\"GOLDPOP t=%0t word=%h len=%0d ins=1\", $time, PISO[63:0], piso_len); end")
    src = re.sub(r"\bmodule uncenter_coeff\b", "module uncenter_coeff_gold", src)
    src = re.sub(r"\bmodule zero_strip\b", "module zero_strip_gold", src)
    src = src.replace("uncenter_coeff UNCENTER", "uncenter_coeff_gold UNCENTER")
    src = src.replace("zero_strip Z_STRIP", "zero_strip_gold Z_STRIP")
    return src

def run_equiv(candidate_dir=None):
    cand = candidate_dir or DEFAULT_CAND
    work = tempfile.mkdtemp(prefix="encgate_")
    try:
        if not os.path.isdir(cand):
            return {"status": "FAIL", "reason": "candidate directory missing: " + str(cand)}
        if not os.path.isfile(os.path.join(cand, "encoder.v")):
            return {"status": "FAIL", "reason": "candidate encoder.v missing"}
        srcs = [TB]
        for f in FILES:
            # gold from pristine, renamed + isolated
            g = os.path.join(work, "gold_" + f)
            Path(g).write_text(_gold_rename(Path(PRISTINE, f).read_text()))
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
        with open(os.path.join(work, "sim.log"), "w") as stream:
            stream.write(r.stdout or "")
        return encoder_result(r)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "FAIL", "reason": str(exc)}
    finally:
        shutil.rmtree(work, ignore_errors=True)

if __name__ == "__main__":
    cd = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_equiv(cd)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
