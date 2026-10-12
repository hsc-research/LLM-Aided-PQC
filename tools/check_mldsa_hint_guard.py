#!/usr/bin/env python3
"""Four-state RTL check for the optional canonical HintBitUnpack guard.

The Python oracle implements FIPS 204 Algorithm 21's encoding predicates.
This checks the guard module, not the full ML-DSA datapath.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from agent.run_safety import hashes, run_process
PARAMS = {2: (80, 4), 3: (55, 6), 5: (75, 8)}


def canonical_hint(encoded, omega, k):
    if len(encoded) != omega + k:
        return False
    index = 0
    for polynomial in range(k):
        end = encoded[omega + polynomial]
        if end < index or end > omega:
            return False
        if any(encoded[j - 1] >= encoded[j] for j in range(index + 1, end)):
            return False
        index = end
    return not any(encoded[index:omega])


def cases():
    rng = random.Random(204)
    result = []
    for level, (omega, k) in PARAMS.items():
        # Empty hints, empty interior polynomials, and the omega boundary.
        result.append((level, bytes(omega+k), "empty"))
        result.append((level, bytes([*range(omega), *([omega]*k)]), "maximum"))
        for _ in range(64):
            # Keep at least two first-polynomial indices and unused padding
            # so each targeted malformed construction is genuinely invalid.
            total = rng.randrange(2, omega)
            lengths = [2] + [0]*(k-1)
            for __ in range(total-2):
                lengths[rng.randrange(k)] += 1
            indices, ends = [], []
            for size in lengths:
                indices.extend(sorted(rng.sample(range(256), size)))
                ends.append(len(indices))
            good = bytearray(indices + [0]*(omega-total) + ends)
            variants = {"canonical": good}
            bad = good.copy(); bad[omega] = omega+1; variants["count_overflow"] = bad
            bad = good.copy(); bad[omega+1] = bad[omega]-1; variants["count_decrease"] = bad
            bad = good.copy(); bad[1] = bad[0]; variants["duplicate_index"] = bad
            bad = good.copy(); bad[0], bad[1] = bad[1], bad[0]; variants["unsorted_index"] = bad
            bad = good.copy(); bad[total] = 1; variants["nonzero_padding"] = bad
            for kind, encoded in variants.items():
                if canonical_hint(encoded, omega, k) != (kind == "canonical"):
                    raise RuntimeError(f"bad test generator: {kind}")
                result.append((level, bytes(encoded), kind))
        for _ in range(64):
            result.append((level, rng.randbytes(omega+k), "random_encoding"))
    return result


def run_check():
    parent = Path(os.environ.get("PQC_RUN_DIR", REPO / ".pqc_runs"))
    parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="mldsa-hint-guard-", dir=parent)).resolve()
    source = REPO / "verification/mldsa_osh/mldsa_hint_guard.v"
    selected = cases()
    packed = []
    totals = {"valid": 0, "invalid": 0}
    for level, encoded, kind in selected:
        omega, k = PARAMS[level]
        invalid = int(not canonical_hint(encoded, omega, k))
        totals["invalid" if invalid else "valid"] += 1
        packed.append(f"{(level << 673) | (invalid << 672) | int.from_bytes(encoded, 'big'):0169x}")
    vectors = work / "vectors.hex"
    vectors.write_text("\n".join(packed)+"\n")
    tb = work / "tb_hint_guard.v"
    tb.write_text(f'''`timescale 1ns/1ps
module tb_hint_guard;
  reg [675:0] vectors [0:{len(selected)-1}];
  reg [2:0] level;
  reg [671:0] hint;
  wire invalid;
  integer i;
  mldsa_hint_guard dut(level, hint, invalid);
  initial begin
    $readmemh("vectors.hex", vectors);
    for (i=0; i<{len(selected)}; i=i+1) begin
      {{level,hint}} = {{vectors[i][675:673],vectors[i][671:0]}};
      #1;
      if (invalid !== vectors[i][672])
        $fatal(1,"MLDSA_HINT_GUARD mismatch at case %0d, expected %b got %b",i,vectors[i][672],invalid);
    end
    $display("MLDSA_HINT_GUARD PASS cases={len(selected)}");
    $finish;
  end
endmodule
''')
    before = hashes([source, tb, vectors])
    result = {"status": "FAIL", "scope": "standalone canonical hint guard four-state RTL", "run_dir": str(work),
              "cases": len(selected), "case_counts": totals, "input_hashes": before, "commands": []}
    try:
        for name, argv in [("compile", ["iverilog", "-g2012", "-s", "tb_hint_guard", "-o", str(work/"guard.vvp"), str(source), str(tb)]),
                           ("sim", ["vvp", str(work/"guard.vvp")])]:
            result["commands"].append(argv)
            run = run_process(argv, cwd=work, timeout=120, log_path=work/(name+".log"))
            result[name+"_returncode"] = run.returncode
            if run.returncode:
                raise RuntimeError(run.stdout)
            if name == "sim" and f"MLDSA_HINT_GUARD PASS cases={len(selected)}" not in run.stdout:
                raise RuntimeError("missing exact guard completion marker")
        if hashes(before) != before:
            raise RuntimeError("guard input changed")
        result["executable_hashes"] = hashes([work/"guard.vvp"])
        result["status"] = "PASS"
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        result["reason"] = str(exc)
    (work/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


if __name__ == "__main__":
    result=run_check();print(json.dumps(result,indent=2));raise SystemExit(result["status"]!="PASS")
