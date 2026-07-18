#!/usr/bin/env python3
# HQC Joint-Design KAT Gate
# Validates build/joint_design tracked overrides (e.g. registered pm client
# select) through the FULL joint design: keygen TB -> encap TB -> decap TB,
# then compares encap ss_output vs decap test_ss_output.
# PASS only if shared secrets match exactly. Watchdog kills hung Vivado.
#
# Usage: python3 agent/hqc/joint_kat_gate.py [--all]
#   default: hqc128 only (inner loop). --all: 128/192/256 (pre-commit).
import subprocess, os, sys, glob, shutil, signal, time

REPO = "."
VIVADO = "vivado"
SIMDIR = "test_joint_design/test_joint_design.sim/sim_1/behav/xsim"
TIMEOUT_S = 3600  # per sim
LEVELS = ["hqc128", "hqc192", "hqc256"] if "--all" in sys.argv else ["hqc128"]
SUF = {"hqc128": "128", "hqc192": "192", "hqc256": "256"}

def stage():
    os.makedirs("build/joint_design/tb", exist_ok=True)
    srcs = ["hardware/joint_design/*.v", "hardware/keygen/*.v",
            "hardware/decap/*.v", "hardware/encap/*.v",
            "hardware/common/fixed_weight/*", "hardware/common/memory/*",
            "hardware/common/clog2.v", "hardware/common/poly_mult/poly_mult.v",
            "hardware/common/shake256/rtl/*", "hardware/common/adders/*",
            "hardware/common/barrett_reduction/*"]
    for pat in srcs:
        for p in glob.glob(pat):
            if os.path.isfile(p):
                shutil.copy(p, "build/joint_design/")
    shutil.copy("hardware/joint_design/tcl/joint_design.tcl", "build/joint_design/tb/")
    for p in glob.glob("hardware/joint_design/tb/*"):
        shutil.copy(p, "build/joint_design/tb/")
    shutil.copy("hardware/encap/memory_files/seed_align.py", "build/joint_design/")
    # tracked overrides win over pristine copies
    r = subprocess.run(["git", "checkout", "--", "build/joint_design/"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("git checkout of overrides failed:", r.stderr); sys.exit(2)
    # seeds
    subprocess.run(["python3", "build/joint_design/seed_align.py", "seed_align",
                    "0", "40", "pk_seed.in", "yes"], check=True)
    subprocess.run(["python3", "build/joint_design/seed_align.py", "seed_align",
                    "0", "40", "sk_seed.in", "yes"], check=True)
    for f in ("pk_seed.in", "sk_seed.in"):
        shutil.move(f, os.path.join("build/joint_design/tb", f))

def run_sim(tb_top, level, runtime_us, extra_files=()):
    adds = "\n".join(f"add_files -fileset sim_1 -norecurse {p}" for p in extra_files)
    tcl = f"""source ./build/joint_design/tb/joint_design.tcl
{adds}
set_property top {tb_top} [get_filesets sim_1]
set_property generic parameter_set=\\"{level}\\" [get_filesets sim_1]
set_property -name {{xsim.simulate.runtime}} -value {{{runtime_us}us}} -objects [get_filesets sim_1]
launch_simulation
"""
    path = f"/tmp/jkg_{tb_top}_{level}.tcl"
    open(path, "w").write(tcl)
    shutil.rmtree("test_joint_design", ignore_errors=True)
    print(f"  [{level}] {tb_top} (watchdog {TIMEOUT_S}s)...")
    proc = subprocess.Popen(
        [VIVADO, "-mode", "batch", "-nojournal", "-nolog", "-notrace",
         "-source", path],
        cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, preexec_fn=os.setsid)
    try:
        out, _ = proc.communicate(timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        print(f"  WATCHDOG KILL: {tb_top} {level}"); return False, "timeout"
    if proc.returncode != 0:
        return False, out[-800:]
    return True, "ok"

def seed_inputs(files):
    for f in files:
        src = os.path.join(SIMDIR, f)
        # outputs of prior stage live in SIMDIR of the *previous* project;
        # we saved them to /tmp/jkg_stash before rmtree
        stash = os.path.join("/tmp/jkg_stash", f)
        if os.path.isfile(stash):
            shutil.copy(stash, os.path.join(SIMDIR))

def stash_outputs(patterns):
    os.makedirs("/tmp/jkg_stash", exist_ok=True)
    for pat in patterns:
        for p in glob.glob(os.path.join(SIMDIR, pat)):
            shutil.copy(p, "/tmp/jkg_stash/")

def place_stash():
    # decap/encap sims read .in files from xsim cwd == SIMDIR;
    # but SIMDIR only exists after launch... so instead we drop the files
    # in repo root fallback AND SIMDIR post-create is impossible pre-launch.
    # xsim also searches the parent of xsim.dir; joint_design.tcl project cwd
    # covers repo root. Simplest robust choice: copy stash into repo root.
    for p in glob.glob("/tmp/jkg_stash/*"):
        shutil.copy(p, ".")

def run_standalone(tcl, label):
    print(f"  standalone {label} sim...")
    proc = subprocess.Popen(
        [VIVADO, "-mode", "batch", "-nojournal", "-nolog", "-notrace",
         "-source", tcl],
        cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, preexec_fn=os.setsid)
    try:
        out, _ = proc.communicate(timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        return False, "timeout"
    return (proc.returncode == 0), out[-800:]

KEYGEN_SIM = "test_keygen/test_keygen.sim/sim_1/behav/xsim"
ENCAP_SIM  = "test_encap/test_encap.sim/sim_1/behav/xsim"

def main():
    t0 = time.time()
    stage()
    shutil.rmtree("/tmp/jkg_stash", ignore_errors=True)
    os.makedirs("/tmp/jkg_stash", exist_ok=True)
    overall = True
    # Stage A/B: standalone keygen + encap generate binary .in stimulus
    # (requires build/keygen and build/encap staged; reuse existing artifacts
    # if present, else fail loudly)
    for d in ("build/keygen/tb/keygen.tcl", "build/encap/tb/encap.tcl"):
        if not os.path.isfile(d):
            print(f"missing {d}: run the standalone build staging first"); sys.exit(2)
    for proj in ("test_keygen", "test_encap", "test_joint_design"):
        shutil.rmtree(proj, ignore_errors=True)
    ok, msg = run_standalone("./build/keygen/tb/keygen.tcl", "keygen")
    if not ok: print("KEYGEN FAIL:", msg); sys.exit(1)
    # keygen outputs -> encap tb dir (binary .in, per Makefile flow)
    for lv in LEVELS:
        sfx = SUF[lv]
        for name in (f"s_{sfx}.in", f"h_{sfx}.in", f"x_{sfx}.in", f"y_{sfx}.in"):
            p = os.path.join(KEYGEN_SIM, name)
            if not os.path.isfile(p):
                print("keygen output missing:", name); sys.exit(1)
            shutil.copy(p, "build/encap/tb/")
            shutil.copy(p, "/tmp/jkg_stash/")
    ok, msg = run_standalone("./build/encap/tb/encap.tcl", "encap")
    if not ok: print("ENCAP FAIL:", msg); sys.exit(1)
    for lv in LEVELS:
        sfx = SUF[lv]
        for name in (f"u_{sfx}.in", f"v_{sfx}.in", f"d_{sfx}.in",
                     f"s_{sfx}.in", f"ss_output_{sfx}.out"):
            p = os.path.join(ENCAP_SIM, name)
            if not os.path.isfile(p):
                print("encap output missing:", name); sys.exit(1)
            shutil.copy(p, "/tmp/jkg_stash/")
    # Stage C: joint decap TB (DUT with tracked overrides incl. registered
    # pm client select; exercises decap + encap_inside_decap mux arms)
    for lv in LEVELS:
        sfx = SUF[lv]
        ins = [os.path.abspath(p) for p in glob.glob("build/joint_design/*.mem")] + \
              [os.path.join("/tmp/jkg_stash", n) for n in
               (f"s_{sfx}.in", f"h_{sfx}.in", f"x_{sfx}.in", f"y_{sfx}.in",
                f"u_{sfx}.in", f"v_{sfx}.in", f"d_{sfx}.in")]
        ok, msg = run_sim("hqc_joint_design_decap_tb", lv, 100000, ins)
        if not ok: print("JOINT DECAP FAIL:", msg); overall = False; break
        dec = os.path.join(SIMDIR, f"test_ss_output_{sfx}.out")
        enc = os.path.join("/tmp/jkg_stash", f"ss_output_{sfx}.out")
        if not os.path.isfile(dec):
            print(f"[{lv}] joint decap wrote no ss output"); overall = False; break
        e, d = open(enc).read().strip(), open(dec).read().strip()
        if e and e == d:
            print(f"[{lv}] SS MATCH ({len(e)} hex chars) — PASS")
        else:
            print(f"[{lv}] SS MISMATCH — FAIL (enc {len(e)} vs dec {len(d)})")
            overall = False; break
    dt = time.time() - t0
    print("=" * 50)
    print(f"JOINT KAT GATE: {'PASS' if overall else 'FAIL'} ({dt:.0f}s)")
    sys.exit(0 if overall else 1)

if __name__ == "__main__":
    main()
