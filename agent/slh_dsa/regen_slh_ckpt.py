#!/usr/bin/env python3
"""Rebuild an SLH-DSA post-synthesis checkpoint from an explicit RTL tree.

SPHINCSLET requires setting.v and clog2.v as GLOBAL INCLUDES. The default RTL
is the checked-in slh_src tree and its actual selected parameter set is retained.
Reports/checkpoints from earlier invocations never establish success.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
if __package__:
    from ..run_safety import hashes, run_process
    from ..synthesizer import tcl_quote
else:
    sys.path.insert(0, str(HERE.parent))
    from run_safety import hashes, run_process
    from synthesizer import tcl_quote

RTL = HERE / "slh_src"
CKPT = REPO / "synth_out/slh_dsa/post_synth.dcp"
PART = "xc7a200tfbg676-1"
# Keep the historical synthesis recipe; routed closure is a separate measurement.
REGEN_PERIOD_NS = 12.0
XDC = """set_false_path -from [get_ports rstn]
set_false_path -from [get_ports i_FSM_start]
set_false_path -from [get_ports i_msg_in_size*]
"""
# i_sig_mode is a live selector, not a tie-off, and remains timed.


def configuration(setting):
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", Path(setting).read_text(), flags=re.S)
    selected = re.findall(r"^\s*`define\s+(PARAM_(?:128|192|256)[FS])\b", text, re.M)
    if len(selected) != 1:
        raise ValueError(f"expected one SLH parameter selection, found {selected}")
    return {"parameter_set": selected[0],
            "hash": "SHAKE" if re.search(r"^\s*`define\s+SHAKE\b", text, re.M) else "SHA2"}


def build_tcl(rtl, sources, work, part=PART):
    work, rtl = Path(work), Path(rtl)
    files = " ".join(tcl_quote(source) for source in sources)
    includes = " ".join(tcl_quote(rtl / suffix) for suffix in ("sphincslet", "imports/global_include"))
    xdc = work / "constraints.xdc"
    return f"""if {{[catch {{
create_project slh_regen {tcl_quote(work / 'project')} -part {tcl_quote(part)} -force
add_files [list {files}]
set_property include_dirs [list {includes}] [current_fileset]
set_property is_global_include true [get_files {tcl_quote(rtl / 'sphincslet/setting.v')}]
set_property is_global_include true [get_files {tcl_quote(rtl / 'imports/global_include/clog2.v')}]
add_files -fileset constrs_1 {tcl_quote(xdc)}
set_property used_in_synthesis true [get_files {tcl_quote(xdc)}]
set_property top top [current_fileset]
update_compile_order -fileset sources_1
synth_design -top top -part {tcl_quote(part)} -mode out_of_context
set clk_ports [get_ports -quiet clk]
if {{[llength $clk_ports] != 1}} {{ error "Expected exactly one clk input" }}
create_clock -period {REGEN_PERIOD_NS:.3f} -name clk $clk_ports
write_checkpoint -force {tcl_quote(work / 'post_synth.dcp')}
puts "PQC_SLH_REGEN_DONE"
}} message]}} {{ puts stderr $message; exit 1 }}
exit 0
"""


def regenerate(rtl_dir=RTL, out_dcp=CKPT, *, timeout=7200, vivado="vivado", run_root=None):
    work = None
    try:
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        rtl, checkpoint = Path(rtl_dir).resolve(), Path(out_dcp).resolve()
        if not rtl.is_dir():
            raise ValueError(f"RTL directory missing: {rtl}")
        required = [rtl / suffix for suffix in ("sphincslet/setting.v", "imports/global_include/clog2.v", "sphincslet/top.v")]
        for source in required:
            if not source.is_file():
                raise ValueError(f"required SLH source missing: {source}")
        config = configuration(required[0])
        sources = sorted(path for path in rtl.rglob("*.v") if path.name != "tb.v")
        before = hashes(sources)
        parent = Path(run_root) if run_root is not None else Path(os.environ.get("PQC_RUN_DIR", str(REPO / ".pqc_runs")))
        parent.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="slh-regen-", dir=parent)).resolve()
        (work / "constraints.xdc").write_text(XDC)
        script = work / "regen.tcl"
        script.write_text(build_tcl(rtl, sources, work))
        result = run_process([vivado, "-mode", "batch", "-notrace", "-source", str(script),
                              "-nojournal", "-log", str(work / "vivado.log")],
                             cwd=work, timeout=timeout, log_path=work / "process.log")
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode:
            raise RuntimeError(f"Vivado exited {result.returncode}: {output[-1000:]}")
        if not re.search(r"^PQC_SLH_REGEN_DONE\s*$", output, re.M) or re.search(r"^\s*ERROR:", output, re.M):
            raise RuntimeError("SLH checkpoint regeneration did not complete cleanly")
        fresh = work / "post_synth.dcp"
        if not fresh.is_file() or not fresh.stat().st_size:
            raise RuntimeError("Vivado did not produce a fresh nonempty checkpoint")
        if sorted(path for path in rtl.rglob("*.v") if path.name != "tb.v") != sources or hashes(sources) != before:
            raise RuntimeError("SLH sources changed during checkpoint generation")
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=checkpoint.parent, delete=False) as stream:
            staging = Path(stream.name)
        try:
            shutil.copyfile(fresh, staging)
            os.replace(staging, checkpoint)
        finally:
            staging.unlink(missing_ok=True)
        return {"status": "OK", "checkpoint": str(checkpoint), "run_dir": str(work),
                "stage": "post_synth", "part": PART, "period_ns": REGEN_PERIOD_NS,
                "configuration": config, "source_hashes": before}
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return {"status": "ERROR", "error": str(exc), "run_dir": str(work) if work else None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rtl_dir", nargs="?", default=str(RTL))
    parser.add_argument("out_dcp", nargs="?", default=str(CKPT))
    parser.add_argument("--timeout", type=float, default=7200)
    args = parser.parse_args(argv)
    result = regenerate(args.rtl_dir, args.out_dcp, timeout=args.timeout)
    print(json.dumps(result, allow_nan=False))
    return 0 if result["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
