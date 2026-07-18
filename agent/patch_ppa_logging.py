#!/usr/bin/env python3
"""(c) Log PPA on every accepted edit going forward.
Patches the accept-record construction in mldsa/orchestrator.py,
mldsa/orchestrator_latency.py, and hqc/transfer_orchestrator.py to include
luts/ffs/dsp/total_w/dynamic_w from the post-edit synthesis result dict, when
present. Idempotent: skips files already containing the marker. Run from repo
root: python3 agent/patch_ppa_logging.py
NOTE: anchors are best-effort; each patch asserts before writing and reports
per-file. If an anchor misses, paste the file's accept-logging block and adjust.
"""
import re, sys, os

FILES = [
    "agent/mldsa/orchestrator.py",
    "agent/mldsa/orchestrator_latency.py",
    "agent/hqc/transfer_orchestrator.py",
]
MARKER = "# ppa-logged"

def patch(path):
    if not os.path.exists(path):
        return f"{path}: MISSING"
    s = open(path).read()
    if MARKER in s:
        return f"{path}: already patched"
    # Find a log/record dict that contains "verdict" and "gain" being written on accept.
    # Generic approach: right after any line assigning a synth result dict named `res`
    # or `result` that is later logged, append PPA extraction. Safer: wrap the json
    # log write — find `"verdict": "ACCEPTED"` construction lines.
    m = re.search(r'(\{[^{}]*"verdict"\s*:\s*"ACCEPTED"[^{}]*\})', s)
    if not m:
        return f"{path}: no ACCEPTED record literal found — patch manually"
    lit = m.group(1)
    if lit.rstrip().endswith("}"):
        new_lit = lit[:-1].rstrip().rstrip(",") + (
            ', **{k: res.get(k) for k in ("luts","ffs","dsp","total_w","dynamic_w")'
            ' if isinstance(res, dict) and res.get(k) is not None}}  ' + MARKER)
        s2 = s.replace(lit, new_lit, 1)
        open(path, "w").write(s2)
        return f"{path}: patched (verify `res` is the synth-result dict in scope)"
    return f"{path}: unexpected literal shape — patch manually"

if __name__ == "__main__":
    for f in FILES:
        print(patch(f))
    print("\nVerify each patched site compiles and that the synth-result variable is "
          "named `res` in that scope (rename in the patch if not). Then future "
          "ACCEPTED records carry luts/ffs/dsp/total_w/dynamic_w, and the dashboard "
          "can grow P/A trend lines from real logged data.")
