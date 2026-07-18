#!/usr/bin/env python3
"""Chip-aware orchestrator (v2): closure-first, top-down target selection.

Loop: closure baseline -> post-route critical cone -> map to RTL file ->
dispatch block orchestrator -> re-integrate -> re-judge at closure ->
accept/revert -> repeat. Acceptance judge = TRUE CLOSING FMAX, never
block WNS, never projections.

Usage: python3 agent/chip_orchestrator.py <design> [--max-rounds N] [--dry]
  design in: mldsa (combined_top), hqc (hqc_joint_opt)
Stage 1 (this version): steps 1-2 + dispatch RECOMMENDATION, human runs the
block orchestrator and re-judge explicitly. Full auto in stage 2 after the
mapping is validated.
"""
import sys, os, re, json, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DESIGNS = {
    "mldsa": {
        "key": "combined_top",
        "ckpt": "./synth_out/sweep_combined_top/post_synth_grade1.dcp",
        "bracket": (10.0, 18.0),
        "hier2file": {
            "ENCODER": "agent/mldsa/mldsa_src/encoder.v",
            "DECODER": "agent/mldsa/mldsa_src/decoder.v",
            "GEN_C":   "agent/mldsa/mldsa_src/gen_c.v",
            "CHALLENGE_SAMPLER": "agent/mldsa/mldsa_src/gen_c.v",
            "MAKEHINT": "agent/mldsa/mldsa_src/makehint.v",
            "USEHINT": "agent/mldsa/mldsa_src/usehint.v",
            "DECOMPOSER": "agent/mldsa/mldsa_src/coeff_decomposer.v",
            "BUTTERFLY": "agent/mldsa/mldsa_src/butterfly.v",
            "REJ": "agent/mldsa/mldsa_src/rejection_s.v",
        },
        "orchestrator": "agent/mldsa/orchestrator.py",
    },
    "hqc": {
        "key": "hqc_joint_opt",
        "ckpt": "./synth_out/sweep_hqc_joint_opt/post_synth_grade1.dcp",
        "bracket": (6.0, 10.0),
        "hier2file": {
            "FIXEDWEIGHT": "build/keygen/fixed_weight_ct.v",
            "ENCAP": "build/encap/encap.v",
            "DECAP": "build/decap/decap.v",
            "POLY_MULT": "build/keygen/poly_mult.v",
            "KECCAK": "build/keygen/keccak_top.v",
            "ENCRYPT": "build/encap/encrypt.v",
        },
        "orchestrator": "agent/hqc/transfer_orchestrator.py",
    },
}

def closure_search(ckpt, tag, lo, hi):
    r = subprocess.run([sys.executable, os.path.join(HERE, "fmax_search.py"),
                        ckpt, tag, str(lo), str(hi),
                        "Default", "Default", "Default"],
                       capture_output=True, text=True)
    m = re.search(r'\{.*"closing_period_ns".*\}', r.stdout)
    return json.loads(m.group(0)) if m else None

def worst_path_at_close(tag, period):
    # read the MET report closest to closing period: worst path start/end
    rpt = f"/tmp/fsrch_{tag}_{period}.rpt"
    if not os.path.exists(rpt):
        return None
    txt = open(rpt).read()
    m = re.search(r"Slack \((?:MET|VIOLATED)\)\s*:.*?Source:\s*(\S+).*?Destination:\s*(\S+)",
                  txt, re.S)
    return {"source": m.group(1), "dest": m.group(2)} if m else None

def map_to_file(path_rec, hier2file):
    for endpoint in (path_rec["dest"], path_rec["source"]):
        top_inst = endpoint.split("/")[0].upper()
        for k, f in hier2file.items():
            if k in top_inst:
                return top_inst, f
    return None, None

def main():
    design = sys.argv[1]
    cfg = DESIGNS[design]
    tag = f"chipv2_{design}_{int(time.time())%100000}"
    print(f"[1] closure baseline: {cfg['key']}")
    base = closure_search(cfg["ckpt"], tag, *cfg["bracket"])
    assert base and base["closing_fmax_mhz"], f"closure search failed: {base}"
    print(json.dumps(base))
    print(f"[2] worst path at closure ({base['closing_period_ns']}ns):")
    p = worst_path_at_close(tag, base["closing_period_ns"])
    assert p, "no path parsed from closing report"
    print(json.dumps(p))
    inst, f = map_to_file(p, cfg["hier2file"])
    print(f"[3] DISPATCH RECOMMENDATION: instance={inst} file={f}")
    rec = {"design": design, "closure": base, "worst_path": p,
           "dispatch_instance": inst, "dispatch_file": f,
           "orchestrator": cfg["orchestrator"], "ts": time.strftime("%F %T")}
    open(os.path.join(HERE, "chip_orchestrator_log.jsonl"), "a").write(json.dumps(rec)+"\n")
    print(f"[4] next (human): run {cfg['orchestrator']} on the mapped block, "
          f"re-integrate, then re-run this script; accept only if closing fmax rises.")

if __name__ == "__main__":
    main()
