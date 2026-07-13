#!/usr/bin/env python3
# Full-design NIST KAT outer gate via Vivado xsim (mixed Verilog/VHDL).
# Usage: python3 full_kat_gate.py [tracked_src_dir]
#   No arg: pristine baseline. With arg (e.g. agent/mldsa/mldsa_src):
#   same-named files there OVERRIDE pristine in the compile set.
# PASS = "testbench done" printed and zero "WRONG" lines.
import subprocess, os, sys, json, glob, shutil, tempfile, time, re

ROOT   = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main"
SRC    = os.path.join(ROOT, "ref_combined/src")
TB     = os.path.join(ROOT, "ref_combined/src_tb/tb_keygen_top.v")
COMMON = os.path.join(ROOT, "common")
KAT    = os.path.join(ROOT, "KAT")
VIVADO_BIN = "/tools/Xilinx/2025.2/Vivado/bin"
TIMEOUT = 86400  # default 24h; override with --timeout SECS
LOGFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fullkat_run.log")
VECFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fullkat_vectors.json")

def parse_per_vector(out):
    vecs, cur = [], None
    for line in out.splitlines():
        m = re.search(r"KAT\s*#\s*(\d+)", line)
        if m:
            k = int(m.group(1))
            if cur is None or cur["kat"] != k:
                cur = next((v for v in vecs if v["kat"] == k), None)
                if cur is None:
                    cur = {"kat": k, "completed": False, "cycles": None, "wrong": 0}
                    vecs.append(cur)
            if "completed in" in line:
                cur["completed"] = True
                mc = re.search(r"completed in\s*(\d+)", line)
                if mc: cur["cycles"] = int(mc.group(1))
        if "WRONG" in line and cur is not None:
            cur["wrong"] += 1
    for v in vecs:
        v["pass"] = v["completed"] and v["wrong"] == 0
    return vecs

def run_full_kat(override_dir=None, vectors=None, timeout=TIMEOUT):
    work = tempfile.mkdtemp(prefix="mldsa_fullkat_")
    ok = False
    try:
        # assemble source set: pristine, then overrides replace by basename
        vfiles  = {os.path.basename(p): p for p in glob.glob(SRC + "/*.v")}
        vhfiles = {os.path.basename(p): p for p in glob.glob(SRC + "/*.vhd")}
        if override_dir:
            for p in glob.glob(os.path.join(override_dir, "*.v")):
                b = os.path.basename(p)
                if b in vfiles:
                    vfiles[b] = p
        # TB uses `include "../../common/mldsa_params.v" and reads KAT via
        # relative paths -> replicate directory layout in work dir
        os.makedirs(os.path.join(work, "ref_combined/src_tb"), exist_ok=True)
        os.makedirs(os.path.join(work, "common"), exist_ok=True)
        # copy the ENTIRE src_tb dir (TB + its sibling KAT/ROM data files:
        # xsim resolves $readmem paths against cwd, and the pristine tree
        # keeps flat copies of the data files next to the TB)
        for p_ in glob.glob(os.path.dirname(TB) + "/*"):
            if os.path.isfile(p_):
                shutil.copy(p_, os.path.join(work, "ref_combined/src_tb"))
        tb_dst = os.path.join(work, "ref_combined/src_tb", os.path.basename(TB))
        if vectors is not None:
            import re as _re2
            tbs = open(tb_dst).read()
            anchor = "localparam  NUM_TV = 25;"
            n = tbs.count(anchor)
            if n != 1:
                return {"status": "FAIL", "stage": "subset-patch",
                        "reason": f"NUM_TV anchor count {n} != 1"}
            tbs = tbs.replace(anchor, f"localparam  NUM_TV = {vectors};")
            open(tb_dst, "w").write(tbs)
        for p in glob.glob(COMMON + "/*"):
            shutil.copy(p, os.path.join(work, "common"))
        shutil.copytree(KAT, os.path.join(work, "KAT"))
        rundir = os.path.join(work, "ref_combined/src_tb")
        # belt-and-suspenders: flatten common/ and KAT/ data files into rundir
        for src_dir in (os.path.join(work, "common"), os.path.join(work, "KAT")):
            for p_ in glob.glob(src_dir + "/*"):
                if os.path.isfile(p_):
                    dst_ = os.path.join(rundir, os.path.basename(p_))
                    if not os.path.exists(dst_):
                        shutil.copy(p_, dst_)

        # shim: hoist ALL forward-referenced reg/wire declarations in combined_top.v
        # (xvlog rejects use-before-declaration; other tools allowed it)
        ct = vfiles.get("combined_top.v")
        if ct:
            import re as _re
            src_ct = open(ct).read()
            decl_re = _re.compile(r"^[ \t]*(reg|wire)(\s+(signed)?\s*(\[[^\]]+\])?)?\s+([A-Za-z_][A-Za-z0-9_]*(\s*\[[^\]]+\])?(\s*,\s*[A-Za-z_][A-Za-z0-9_]*(\s*\[[^\]]+\])?)*)\s*;\s*$", _re.M)
            hoisted = []
            def first_use(name, before):
                m = _re.search(r"\b" + _re.escape(name) + r"\b", before)
                return m is not None
            # iterate declarations bottom-up; hoist any whose name is used earlier
            for m in list(decl_re.finditer(src_ct)):
                names = [_re.split(r"\s*\[", n.strip())[0] for n in m.group(5).split(",")]
                body_before = src_ct[:m.start()]
                if any(first_use(n, body_before) for n in names):
                    hoisted.append(m.group(0).strip())
            if hoisted:
                for d in hoisted:
                    src_ct = src_ct.replace(d + "\n", "", 1) if d + "\n" in src_ct else src_ct.replace(d, "", 1)
                hdr_end = src_ct.find(");", src_ct.find("module combined_top")) + 2
                src_ct = src_ct[:hdr_end] + "\n    // xvlog shim: hoisted forward-referenced decls\n    " + "\n    ".join(hoisted) + "\n" + src_ct[hdr_end:]
                shim = os.path.join(work, "combined_top.v")
                open(shim, "w").write(src_ct)
                vfiles["combined_top.v"] = shim

        env = dict(os.environ)
        env["PATH"] = VIVADO_BIN + ":" + env.get("PATH", "")

        def x(cmd, tee=False):
            if not tee:
                return subprocess.run(cmd, cwd=rundir, capture_output=True,
                                      text=True, timeout=timeout, env=env, shell=True)
            # tee mode: stream stdout to LOGFILE live so progress is visible
            with open(LOGFILE, "w") as lf:
                lf.write(f"=== {cmd} ===\n"); lf.flush()
                proc = subprocess.Popen(cmd, cwd=rundir, stdout=subprocess.PIPE,
                                        start_new_session=True,
                                        stderr=subprocess.STDOUT, text=True,
                                        env=env, shell=True)
                import threading, signal as _sig
                timed_out_flag = {"v": False}
                def _watchdog():
                    timed_out_flag["v"] = True
                    try: os.killpg(os.getpgid(proc.pid), _sig.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        try: proc.kill()
                        except Exception: pass
                wd = threading.Timer(timeout, _watchdog)
                wd.start()
                lines = []
                for line in proc.stdout:
                    lf.write(line); lf.flush()
                    lines.append(line)
                wd.cancel()
                proc.wait()
                if timed_out_flag["v"]:
                    class R: pass
                    r = R(); r.returncode = -9
                    r.stdout = "".join(lines); r.stderr = ""
                    r.timed_out = True
                    return r
                class R: pass
                r = R(); r.returncode = proc.returncode
                r.stdout = "".join(lines); r.stderr = ""
                r.timed_out = False
                return r

        # multi-pass VHDL compile: retry failures until fixpoint (order-independent)
        pkgs = [v for b, v in sorted(vhfiles.items()) if b.endswith("_pkg.vhd")]
        rest = [v for b, v in sorted(vhfiles.items()) if not b.endswith("_pkg.vhd")]
        pending = pkgs + rest
        for _pass in range(len(pending) + 1):
            failed = []
            for f in pending:
                r = x(f'xvhdl "{f}"')
                if "ERROR" in r.stdout or r.returncode != 0:
                    failed.append(f)
            if not failed:
                break
            if len(failed) == len(pending):
                return {"status": "FAIL", "stage": "xvhdl",
                        "reason": "no progress; stuck on: " +
                                  ",".join(os.path.basename(f) for f in failed)}
            pending = failed
        else:
            return {"status": "FAIL", "stage": "xvhdl", "reason": "pass limit exceeded"}
        r = x("xvlog " + " ".join(f'"{p}"' for p in sorted(vfiles.values())) + " tb_keygen_top.v")
        if r.returncode != 0:
            return {"status": "FAIL", "stage": "xvlog", "reason": r.stdout[-400:] + r.stderr[-200:]}
        r = x("xelab tb_keygen_top -s kat_sim --timescale 1ns/1ps")
        if r.returncode != 0:
            return {"status": "FAIL", "stage": "xelab", "reason": r.stdout[-400:] + r.stderr[-200:]}
        t0 = time.time()
        r = x("xsim kat_sim -R", tee=True)   # -R: batch run-all-then-exit, no gui simmode, no wdb
        runtime = round(time.time() - t0, 1)
        out = r.stdout
        vecs  = parse_per_vector(out)
        json.dump(vecs, open(VECFILE, "w"), indent=1)
        wrong = [l for l in out.splitlines() if "WRONG" in l]
        done  = "testbench done" in out
        kats  = sum(1 for v in vecs if v["completed"])
        base  = {"kats_completed": kats, "runtime_s": runtime,
                 "per_vector_file": VECFILE,
                 "vector_pass": sum(1 for v in vecs if v.get("pass")),
                 "vector_fail": sum(1 for v in vecs if not v.get("pass"))}
        if getattr(r, "timed_out", False):
            inprog = vecs[-1]["kat"] if vecs else None
            return {"status": "FAIL", "stage": "sim-timeout",
                    "in_progress_vector": inprog, **base}
        if done and not wrong:
            ok = True
            return {"status": "PASS", "override": override_dir or "pristine",
                    "vectors": vectors or "full", **base}
        return {"status": "FAIL", "stage": "sim",
                "wrong_count": len(wrong),
                "first_wrong": wrong[0] if wrong else "no 'testbench done'", **base}
    finally:
        if ok:
            shutil.rmtree(work, ignore_errors=True)
        else:
            keep = work.replace("mldsa_fullkat_", "mldsa_fullkat_FAILED_")
            try: os.rename(work, keep); print(f"workdir preserved: {keep}", file=sys.stderr)
            except OSError: pass

if __name__ == "__main__":
    args = sys.argv[1:]
    vectors = None; timeout = TIMEOUT; override = None
    while args:
        a = args.pop(0)
        if a == "--vectors": vectors = int(args.pop(0))
        elif a == "--timeout": timeout = int(args.pop(0))
        else: override = a
    print(json.dumps(run_full_kat(override, vectors=vectors, timeout=timeout), indent=2))
