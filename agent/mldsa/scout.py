"""Scout: rank untouched ML-DSA blocks by baseline WNS. No LLM, no edits.
Registers each candidate in MODULE_SOURCES on the fly, synths, ranks.
Usage: python3 agent/mldsa/scout.py <module1> <module2> ...
       (module name = filename without .v, must be self-contained or
        list deps by editing DEPS below)"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "agent"))
os.chdir(REPO)
from synthesizer import run_synthesis, MODULE_SOURCES

PRISTINE = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src"
DEPS = {}   # module -> extra source files, if hierarchical

results = []
for mod in sys.argv[1:]:
    srcs = [f"{PRISTINE}/{mod}.v"] + [f"{PRISTINE}/{d}" for d in DEPS.get(mod, [])]
    missing = [s for s in srcs if not os.path.exists(s)]
    if missing:
        print(f"{mod}: MISSING {missing}"); continue
    MODULE_SOURCES[mod] = srcs
    res = run_synthesis(mod, "mldsa")
    if "error" in res:
        print(f"{mod}: SYNTH FAIL {res['error'][:200]}"); continue
    results.append((res.get("wns_ns"), mod, res.get("luts"), res.get("ffs")))
    print(f"{mod}: WNS {res.get('wns_ns')}  LUTs {res.get('luts')}  FFs {res.get('ffs')}")

print("\n=== RANKED (worst WNS first) ===")
for wns, mod, luts, ffs in sorted(results, key=lambda r: (r[0] is None, r[0])):
    print(f"{wns}\t{mod}\tLUTs {luts}")
