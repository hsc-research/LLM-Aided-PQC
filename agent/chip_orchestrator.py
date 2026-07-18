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
        "bracket": (12.0, 13.5),
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
        "kat_gate": ["python3", "agent/mldsa/full_kat_gate.py", "agent/mldsa/mldsa_src"],
    },
    "hqc": {
        "key": "hqc_joint_opt",
        "ckpt": "./synth_out/sweep_hqc_joint_opt/post_synth_grade1.dcp",
        "bracket": (6.0, 10.0),
        "hier2file": {
            "FIXEDWEIGHT": "build/keygen/fixed_weight_ct.v",
            "ENCAP": "build/encap/encap.v",
            "DECAP": "build/decap/decap.v",
            "POLY_MULT": "build/joint_design/hqc_kem_joint_design.v",  # input cones = shared-mux fan-in, joint-top scope
            "V_MINUS_UY": "build/decap/v_minus_uy.v",
            "VECTSETRAND": "build/keygen/vect_set_random.v",
            "KECCAK": "build/keygen/keccak_top.v",
            "ENCRYPT": "build/encap/encrypt.v",
        },
        "orchestrator": "agent/hqc/transfer_orchestrator.py",
        "kat_gate": ["python3", "agent/hqc/joint_kat_gate.py"],
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

def regen_ckpt(cfg):
    """Re-synthesize the chip from current tracked sources into cfg['ckpt'].
    Required between dispatch and re-judge: closure_search judges a post-synth
    checkpoint, so a block edit is invisible until the dcp is rebuilt."""
    import subprocess
    sys.path.insert(0, os.path.join(HERE, ".."))
    from synthesizer import MODULE_SOURCES, VHDL_SOURCES, PART, TOP_OVERRIDE, ordered_sources, synth_flags
    key = cfg["key"]
    srcs = ordered_sources(key); vhdl = VHDL_SOURCES.get(key, [])
    top = TOP_OVERRIDE.get(key, key)
    period = cfg.get("regen_period_ns", 8.600)
    vb = "read_vhdl {\n  " + "\n  ".join(vhdl) + "\n}\n" if vhdl else ""
    nl = chr(10)
    tcl = (vb + "read_verilog {" + nl + "  " + nl.join(srcs) + nl + "}" + nl +
           f"synth_design -top {top} -part {PART}{synth_flags(key)}" + nl +
           "set clk_port [lindex [get_ports -quiet {clk clk_i}] 0]" + nl +
           'if {$clk_port eq ""} { set clk_port [lindex [get_ports -quiet *clk*] 0] }' + nl +
           "create_clock -period " + f"{period:.3f}" + " -name clk [get_ports $clk_port]" + nl +
           f"write_checkpoint -force {cfg['ckpt']}" + nl + 'puts "REGEN DONE"' + nl)
    tf = "/tmp/regen_ckpt.tcl"
    open(tf, "w").write(tcl)
    r = subprocess.run(["vivado","-mode","batch","-source",tf,"-nojournal","-nolog"],
                       capture_output=True, text=True)
    assert "REGEN DONE" in r.stdout, "checkpoint regen failed"

def main():
    design = sys.argv[1]
    cfg = DESIGNS[design]
    tag = f"chipv2_{design}_{int(time.time())%100000}"
    print(f"[0] regen checkpoint from current tracked sources")
    regen_ckpt(cfg)
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
    if "--dispatch" not in sys.argv:
        print(f"[4] next (human): run {cfg['orchestrator']} on the mapped block, "
              f"re-integrate, then re-run this script; accept only if closing fmax rises.")
        return
    # ---- stage 2: auto-dispatch ----
    import subprocess
    if f is None:
        print("[4] no dispatch target: worst-path instance is outside the block-orchestrator "
              "scope (e.g. shared Keccak, interconnect). Chip loop ends; architectural tier owns this cone.")
        rec["verdict"] = "NO_TARGET (out-of-scope cone)"
        open(os.path.join(HERE, "chip_orchestrator_log.jsonl"), "a").write(json.dumps(rec)+chr(10))
        return
    blk = os.path.splitext(os.path.basename(f))[0]
    print(f"[4] AUTO-DISPATCH: {cfg['orchestrator']} {blk}")
    r = subprocess.run(["python3", cfg["orchestrator"], blk],
                       capture_output=True, text=True, timeout=7200)
    print(r.stdout[-2000:])
    if "ACCEPTED" not in r.stdout:
        print("[5] block orchestrator produced no accepted edit -- chip loop ends.")
        return
    gate = cfg.get("kat_gate")
    if gate:
        print(f"[5a] functional KAT gate: {' '.join(gate)}")
        g = subprocess.run(gate, capture_output=True, text=True, timeout=7200)
        print(g.stdout[-800:])
        out = g.stdout or ""
        # accept either convention: '"status": "PASS"' (mldsa json) or 'GATE: PASS' (hqc)
        gate_pass = (g.returncode == 0) and ('"status": "PASS"' in out or "GATE: PASS" in out) and '"status": "FAIL"' not in out and "GATE: FAIL" not in out
        if not gate_pass:
            print("[5a] KAT GATE FAILED — edit is functionally broken; reverting tracked sources and ending chip loop.")
            subprocess.run(["git", "checkout", "--", f], capture_output=True, text=True)  # revert only the dispatched file
            rec["verdict"] = "KAT_FAIL (edit reverted)"
            open(os.path.join(HERE, "chip_orchestrator_log.jsonl"), "a").write(json.dumps(rec)+chr(10))
            return
        print("[5a] KAT gate PASS")
    print("[5] re-synth chip checkpoint (updated tracked sources)")
    regen_ckpt(cfg)
    print("[6] re-judge at closure")
    tag2 = tag + "_r2"
    post = closure_search(cfg["ckpt"], tag2, *cfg["bracket"])
    print(json.dumps(post))
    verdict = "ACCEPT" if post["closing_fmax_mhz"] > base["closing_fmax_mhz"] else "REJECT (revert block edit)"
    print(f"[7] CHIP VERDICT: {base['closing_fmax_mhz']} -> {post['closing_fmax_mhz']} MHz : {verdict}")
    rec["post"] = post; rec["verdict"] = verdict
    open(os.path.join(HERE, "chip_orchestrator_log.jsonl"), "a").write(json.dumps(rec)+"\n")

if __name__ == "__main__":
    main()
