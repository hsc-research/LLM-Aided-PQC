# HQC Agent - Synthesizer
# Generates a TCL script and runs Vivado OOC synthesis on a module.
# Returns parsed PPA results via ppa_reader.

import glob
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

if __package__:
    from .ppa_reader import read_ppa
    from .run_safety import run_process
else:
    from ppa_reader import read_ppa
    from run_safety import run_process

REPO_ROOT = Path(__file__).resolve().parents[1]
# MLDSA_ROOT is the external ML-DSA checkout, containing ref_combined/src.
MLDSA_ROOT = Path(os.environ.get("MLDSA_ROOT", str(REPO_ROOT.parent / "ML-DSA-OSH-main"))).expanduser().resolve()
_PRIS = str(MLDSA_ROOT / "ref_combined" / "src")


def _repo_glob(pattern, recursive=False):
    """Source manifests must not depend on the caller's current directory."""
    return ["./" + os.path.relpath(path, REPO_ROOT)
            for path in glob.glob(str(REPO_ROOT / pattern), recursive=recursive)]


def tcl_quote(value):
    """Quote one Tcl word, including paths with spaces and substitutions."""
    value = str(value)
    for old, new in (("\\", "\\\\"), ('"', '\\"'), ("$", "\\$"),
                     ("[", "\\["), ("]", "\\]"), ("{", "\\{"), ("}", "\\}"), ("\n", "\\n"), ("\r", "\\r")):
        value = value.replace(old, new)
    return '"' + value + '"'


def _identifier(value, name):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        raise ValueError(f"invalid {name}")
    return value


def _period(value):
    if isinstance(value, bool):
        raise ValueError("period must be finite and positive")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("period must be finite and positive")
    return value

VIVADO = "vivado"
PART   = "xc7a200tfbg676-1"

# When the MODULE_SOURCES key is a variant label, map it to the real top module.
TOP_OVERRIDE = {
    "sampler_s_pristine": "sampler_s",     "sampler_s_opt": "sampler_s",
    "sampler_y_pristine": "sampler_y_ext", "sampler_y_opt": "sampler_y_ext",
    "sampler_a_pristine": "sampler_a_ext", "sampler_a_opt": "sampler_a_ext",
    "bf2x2_baseline": "butterfly2x2", "bf2x2_optimized": "butterfly2x2",
}

MODULE_SOURCES = {
    "poly_mult": [
        "./build/keygen/clog2.v",
        "./build/keygen/loc_based_adder.v",
        "./build/keygen/xor_based_adder.v",
        "./build/keygen/mem_dual.v",
        "./build/keygen/mem_single.v",
        "./build/keygen/poly_mult.v",
    ]
}

VHDL_SOURCES = {}  # module -> list of .vhd files (read via read_vhdl before synth)

HDR_FIRST = ("clog2.v", "keccak_pkg.v")
INCLUDE_DIRS = "./build/keygen ./build/encap ./build/decap ./hardware/common/shake256/rtl ./hardware/common"

def ordered_sources(module):
    """Header/macro files first; single source of truth for read order."""
    return sorted(MODULE_SOURCES[module],
                  key=lambda p: (0 if p.split('/')[-1] in HDR_FIRST else 1))

def synth_flags(module):
    """Per-design synth_design extra flags (defines, include dirs)."""
    fl = f" -include_dirs {{{INCLUDE_DIRS}}}"
    if module.startswith("hqc_joint"):
        fl += " -verilog_define SHARED=1 -verilog_define SHARED_ENCAP=1"
    return fl

def build_tcl(module, param_set, period=5.000, *, part=PART, ooc=True,
              synth_out="synth_out", repo_root="."):
    """Render the exact settings reported in the backend fingerprint."""
    _identifier(module, "module")
    _identifier(param_set, "parameter set")
    _identifier(part, "part")
    period = _period(period)
    if not isinstance(ooc, bool):
        raise ValueError("ooc must be a boolean")
    root = Path(repo_root).resolve()
    sources = ordered_sources(module)
    if not sources:
        raise ValueError(f"empty source manifest for {module}; check MLDSA_ROOT")
    top = _identifier(TOP_OVERRIDE.get(module, module), "top module")
    source_lines = " ".join(tcl_quote(root / path) for path in sources)
    vhdl = VHDL_SOURCES.get(module, [])
    vhdl_block = ""
    if vhdl:
        vhdl_block = "read_vhdl [list " + " ".join(tcl_quote(root / path) for path in vhdl) + "]\n"
    include_dirs = " ".join(tcl_quote(root / path) for path in INCLUDE_DIRS.split())
    defines = " -verilog_define SHARED=1 -verilog_define SHARED_ENCAP=1" if module.startswith("hqc_joint") else ""
    mode = " -mode out_of_context" if ooc else ""
    out = Path(synth_out) / module
    prefix = out / f"{module}_{param_set}"
    # An explicit catch exits nonzero even on Vivado versions whose batch Tcl
    # errors otherwise leave an ambiguous process status.
    return f"""if {{[catch {{
file mkdir {tcl_quote(out)}
{vhdl_block}read_verilog [list {source_lines}]
synth_design -top {top} -part {part}{mode} -include_dirs [list {include_dirs}]{defines} -generic parameter_set={param_set}
set clk_ports [get_ports -quiet {{clk clk_i}}]
if {{[llength $clk_ports] == 0}} {{ set clk_ports [get_ports -quiet *clk*] }}
if {{[llength $clk_ports] != 1}} {{ error "Expected exactly one clock input" }}
create_clock -period {period:.12g} -name clk $clk_ports
report_utilization -file {tcl_quote(str(prefix) + '_util.rpt')}
report_power -file {tcl_quote(str(prefix) + '_power.rpt')}
report_timing_summary -file {tcl_quote(str(prefix) + '_timing.rpt')}
puts "PQC_SYNTHESIS_DONE"
}} message]}} {{ puts stderr $message; exit 1 }}
exit 0
"""


def run_synthesis(module, param_set, repo_root=".", period=5.000, *,
                  part=PART, ooc=True, timeout=3600):
    """Measure only reports produced by this invocation; never reuse old ones.

    Each run retains its Tcl/log/reports under .pqc_runs for diagnosis. Validated
    reports are additionally published at the historical synth_out paths.
    """
    if module not in MODULE_SOURCES:
        return {"error": f"module {module} not registered in synthesizer", "measurement_valid": False}
    run_dir = None
    try:
        period = _period(period)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        _identifier(module, "module")
        _identifier(param_set, "parameter set")
        root = Path(repo_root).resolve()
        sources = ordered_sources(module) + VHDL_SOURCES.get(module, [])
        if not sources:
            raise ValueError(f"empty source manifest for {module}; check MLDSA_ROOT")
        missing = [str(root / path) for path in sources if not (root / path).is_file()]
        if missing:
            raise ValueError("missing selected RTL sources (check repo_root/MLDSA_ROOT): " + ", ".join(missing))
        runs = root / ".pqc_runs" / "vivado"
        runs.mkdir(parents=True, exist_ok=True)
        run_dir = Path(tempfile.mkdtemp(prefix=f"{module}-", dir=runs))
        out = run_dir / "reports"
        tcl_path = run_dir / "synth.tcl"
        tcl_path.write_text(build_tcl(module, param_set, period, part=part, ooc=ooc,
                                      synth_out=out, repo_root=root))
        result = run_process([VIVADO, "-mode", "batch", "-nojournal", "-nolog", "-notrace",
                              "-source", str(tcl_path)], cwd=run_dir, timeout=timeout,
                             log_path=run_dir / "process.log")
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0:
            raise RuntimeError(f"Vivado failed (exit {result.returncode}): {output[-1000:]}")
        if not re.search(r"^PQC_SYNTHESIS_DONE\s*$", output, re.M) or re.search(r"^\s*ERROR:", output, re.M):
            raise RuntimeError("Vivado did not complete cleanly; see process.log")
        measured = read_ppa(module, param_set, synth_out=out, period=period)
        measured["run_dir"] = str(run_dir)
        if "error" in measured:
            return measured
        # Atomic per-file publishing is for existing report readers only. All
        # validation above uses the private run directory, never these aliases.
        destination = root / "synth_out" / module
        destination.mkdir(parents=True, exist_ok=True)
        for report in (out / module).glob("*.rpt"):
            with tempfile.NamedTemporaryFile(dir=destination, delete=False) as stream:
                staging = Path(stream.name)
            try:
                shutil.copyfile(report, staging)
                os.replace(staging, destination / report.name)
            finally:
                staging.unlink(missing_ok=True)
        measured["_config"] = {"backend": "vivado", "part": part,
                               "period_ns": period, "ooc": ooc}
        return measured
    except (OSError, TypeError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return {"error": str(exc), "measurement_valid": False,
                "run_dir": str(run_dir) if run_dir else None}


def _hqc_joint(pristine=False):
    import glob as _g, os as _o
    pris = sorted(p for p in _repo_glob("./hardware/**/*.v", recursive=True) if "/tb/" not in p)
    if pristine:
        return pris
    d = {}
    for dd in ("./build/keygen","./build/encap","./build/decap"):
        for p in _repo_glob(dd+"/*.v"):
            d[_o.path.basename(p)] = p
    for p in pris:
        b = _o.path.basename(p)
        if b not in d:
            d[b] = p
    return sorted(d.values())
def _hqc_op_pristine(op):
    import glob as _g, os as _o
    d = {}
    for p in _hqc_joint(True):
        b = _o.path.basename(p)
        if b not in d or "shake256" not in p:
            d[b] = p
    return sorted(d.values())
def _mirror_pristine(ref_key):
    import glob as _g, os as _o
    want = [_o.path.basename(p) for p in MODULE_SOURCES[ref_key]]
    allh = _repo_glob("./hardware/**/*.v", recursive=True)
    out = []
    for b in want:
        cands = [p for p in allh if _o.path.basename(p) == b and "/tb/" not in p]
        cands.sort(key=lambda p: "shake256" in p if b == "clog2.v" else 0)
        assert cands, f"no pristine source for {b}"
        out.append(cands[0])
    return out
TOP_OVERRIDE["keygen_pristine"] = "keygen"
MODULE_SOURCES["hqc_joint_pristine"] = _hqc_joint(True)
def _hqc_joint_opt():
    import glob as _g, os as _o
    pris = {}
    for p in _hqc_joint(True):
        b = _o.path.basename(p)
        if b not in pris or "shake256" not in p:
            pris[b] = p  # prefer non-shake256 copy on basename collision
    SWAP = ("encap.v","encrypt_parallel.v","encrypt.v","fixed_weight_ct.v",
            "fixed_weight.v","hqc_rsdecod_err_val.v","syncfifo.v",
            "v_minus_uy.v","xor_based_adder.v","mem_single_dist.v")
    for dd in ("./build/keygen","./build/encap","./build/decap"):
        for p in _repo_glob(dd+"/*.v"):
            b = _o.path.basename(p)
            if b in SWAP:
                pris[b] = p
    # tracked joint-design overrides (e.g. registered pm client select)
    for p in _repo_glob("./build/joint_design/*.v"):
        pris[_o.path.basename(p)] = p
    return sorted(pris.values())
MODULE_SOURCES["hqc_joint_opt"] = _hqc_joint_opt()
TOP_OVERRIDE["hqc_joint_pristine"] = "hqc_kem_joint_design"
TOP_OVERRIDE["hqc_joint_opt"] = "hqc_kem_joint_design"
MODULE_SOURCES["keygen"] = [
    "./build/keygen/clog2.v",
    "./build/keygen/keygen.v",
    "./build/keygen/vect_set_random.v",
    "./build/keygen/fixed_weight.v",
    "./build/keygen/onegen.v",
    "./build/keygen/fixed_weight_ct.v",
    "./build/keygen/onegen_ct.v",
    "./build/keygen/hqc_barrett_red.v",
    "./build/keygen/poly_mult.v",
    "./build/keygen/mem_single.v",
    "./build/keygen/mem_dual.v",
    "./build/keygen/loc_based_adder.v",
    "./build/keygen/xor_based_adder.v",
    "./build/keygen/keccak_top.v",
    "./build/keygen/keccak_pkg.v",
    "./build/keygen/keccak_math.v",
    "./build/keygen/control_path.v",
    "./build/keygen/data_path.v",
    "./build/keygen/rc.v",
    "./build/keygen/state_ram.v",
    "./build/keygen/stateram_inference.v",
    "./build/keygen/transform.v",
]


MODULE_SOURCES["fixed_weight"] = [
    "./build/keygen/clog2.v",
    "./build/keygen/fixed_weight.v",
    "./build/keygen/onegen.v",
    "./build/keygen/fixed_weight_ct.v",
    "./build/keygen/onegen_ct.v",
    "./build/keygen/hqc_barrett_red.v",
    "./build/keygen/mem_single.v",
    "./build/keygen/mem_dual.v",
    "./build/keygen/keccak_top.v",
    "./build/keygen/keccak_pkg.v",
    "./build/keygen/keccak_math.v",
    "./build/keygen/control_path.v",
    "./build/keygen/data_path.v",
    "./build/keygen/rc.v",
    "./build/keygen/state_ram.v",
    "./build/keygen/stateram_inference.v",
    "./build/keygen/transform.v",
]

MODULE_SOURCES["decap"] = [
    "./build/decap/add_fft.v",
    "./build/decap/barrett_red_gen.v",
    "./build/decap/cdw_xor_tmp.v",
    "./build/decap/clog2.v",
    "./build/decap/concat_code.v",
    "./build/decap/control_path.v",
    "./build/decap/data_path.v",
    "./build/decap/decap.v",
    "./build/decap/decrypt.v",
    "./build/decap/encap.v",
    "./build/decap/encrypt.v",
    "./build/decap/encrypt_parallel.v",
    "./build/decap/fft_leaves_butterfly.v",
    "./build/decap/fft_part1.v",
    "./build/decap/fft_part2.v",
    "./build/decap/fft_retrieve_error_poly.v",
    "./build/decap/fixed_weight.v",
    "./build/decap/fixed_weight_ct.v",
    "./build/decap/fixed_weight_cww.v",
    "./build/decap/gf_mul.v",
    "./build/decap/gfmul.v",
    "./build/decap/hqc_barrett_red.v",
    "./build/decap/hqc_decod_top.v",
    "./build/decap/hqc_rmdecod_ctrl.v",
    "./build/decap/hqc_rmdecod_expnsum.v",
    "./build/decap/hqc_rmdecod_findpeaks.v",
    "./build/decap/hqc_rmdecod_hadamard.v",
    "./build/decap/hqc_rmdecod_top.v",
    "./build/decap/hqc_rsdecod_elp.v",
    "./build/decap/hqc_rsdecod_err_val.v",
    "./build/decap/hqc_rsdecod_roots.v",
    "./build/decap/hqc_rsdecod_syndromes.v",
    "./build/decap/hqc_rsdecod_top.v",
    "./build/decap/hqc_rsdecod_zpoly.v",
    "./build/decap/karatsuba_small.v",
    "./build/decap/keccak_math.v",
    "./build/decap/keccak_pkg.v",
    "./build/decap/keccak_top.v",
    "./build/decap/loc_based_adder.v",
    "./build/decap/mem_dual.v",
    "./build/decap/mem_single.v",
    "./build/decap/mem_single_dist.v",
    "./build/decap/mod34.v",
    "./build/decap/onegen.v",
    "./build/decap/onegen_ct.v",
    "./build/decap/poly_mult.v",
    "./build/decap/rc.v",
    "./build/decap/reed_muller_encode.v",
    "./build/decap/reed_solomon_encode.v",
    "./build/decap/rm_encoder.v",
    "./build/decap/state_ram.v",
    "./build/decap/stateram_inference.v",
    "./build/decap/syncfifo.v",
    "./build/decap/transform.v",
    "./build/decap/v_minus_uy.v",
    "./build/decap/xor_based_adder.v",
]


MODULE_SOURCES["encap"] = [
    "./build/encap/barrett_red_gen.v",
    "./build/encap/cdw_xor_tmp.v",
    "./build/encap/clog2.v",
    "./build/encap/concat_code.v",
    "./build/encap/control_path.v",
    "./build/encap/data_path.v",
    "./build/encap/encap.v",
    "./build/encap/encrypt.v",
    "./build/encap/encrypt_parallel.v",
    "./build/encap/fixed_weight.v",
    "./build/encap/fixed_weight_ct.v",
    "./build/encap/fixed_weight_cww.v",
    "./build/encap/gf_mul.v",
    "./build/encap/hqc_barrett_red.v",
    "./build/encap/karatsuba_small.v",
    "./build/encap/keccak_math.v",
    "./build/encap/keccak_pkg.v",
    "./build/encap/keccak_top.v",
    "./build/encap/loc_based_adder.v",
    "./build/encap/mem_dual.v",
    "./build/encap/mem_single.v",
    "./build/encap/mem_single_dist.v",
    "./build/encap/mod34.v",
    "./build/encap/onegen.v",
    "./build/encap/onegen_ct.v",
    "./build/encap/poly_mult.v",
    "./build/encap/rc.v",
    "./build/encap/reed_muller_encode.v",
    "./build/encap/reed_solomon_encode.v",
    "./build/encap/rm_encoder.v",
    "./build/encap/state_ram.v",
    "./build/encap/stateram_inference.v",
    "./build/encap/transform.v",
    "./build/encap/xor_based_adder.v",
]

MODULE_SOURCES["butterfly"] = [
    _PRIS + "/Barrett_8380417.v",
    "./agent/mldsa/mldsa_src/butterfly.v",
]
MODULE_SOURCES["bf2x2_baseline"] = [
    _PRIS + "/Barrett_8380417.v",
    "./asic/arms/bf2x2_baseline/butterfly.v",
    "./asic/arms/bf2x2_baseline/butterfly2x2.v",
]
MODULE_SOURCES["bf2x2_optimized"] = [
    _PRIS + "/Barrett_8380417.v",
    "./asic/arms/bf2x2_optimized/butterfly.v",
    "./asic/arms/bf2x2_optimized/butterfly2x2.v",
]

MODULE_SOURCES["expandmask_ext"] = [
    "./agent/mldsa/mldsa_src/rejection_y.v",
    _PRIS + "/sampler_y_ext.v",
    _PRIS + "/expandmask_ext.v",
]
MODULE_SOURCES["gen_a_ext"] = [
    _PRIS + "/rejection_a.v",
    _PRIS + "/sampler_a_ext.v",
    _PRIS + "/gen_a_ext.v",
]
MODULE_SOURCES["rejection_a"] = [
    "./agent/mldsa/mldsa_src/rejection_a.v",
]

MODULE_SOURCES["decomposer_unit"] = [
    _PRIS + "/decomposer_unit.v",
]

MODULE_SOURCES["coeff_decomposer"] = [
    "./agent/mldsa/mldsa_src/decomp_map1.v",
    "./agent/mldsa/mldsa_src/coeff_decomposer.v",
]

MODULE_SOURCES["rejection_y"] = [
    "./agent/mldsa/mldsa_src/rejection_y.v",
]
MODULE_SOURCES["rejection_s"] = [
    "./agent/mldsa/mldsa_src/rejection_s.v",
]
MODULE_SOURCES["keccak_hqc"] = [
    "./build/keygen/keccak_top.v",
    "./build/keygen/keccak_pkg.v",
    "./build/keygen/keccak_math.v",
    "./build/keygen/state_ram.v",
    "./build/keygen/stateram_inference.v",
    "./build/keygen/control_path.v",
    "./build/keygen/data_path.v",
    "./build/keygen/rc.v",
    "./build/keygen/transform.v",
]
TOP_OVERRIDE["keccak_hqc"] = "keccak_top"
MODULE_SOURCES["makehint"] = [
    "./agent/mldsa/mldsa_src/makehint.v",
]


MODULE_SOURCES["gen_c"] = [
    "./agent/mldsa/mldsa_src/gen_c.v",
]

MODULE_SOURCES["decoder"] = [
    "./agent/mldsa/mldsa_src/decoder.v",
]

MODULE_SOURCES["usehint"] = [
    "./agent/mldsa/mldsa_src/usehint.v",
]

# Composite targets: sampler wrappers, pristine vs optimized rejection cores
MODULE_SOURCES["sampler_s_pristine"] = [_PRIS + "/sampler_s.v", _PRIS + "/rejection_s.v"]
MODULE_SOURCES["sampler_s_opt"]      = [_PRIS + "/sampler_s.v", "./agent/mldsa/mldsa_src/rejection_s.v"]
MODULE_SOURCES["sampler_y_pristine"] = [_PRIS + "/sampler_y_ext.v", _PRIS + "/rejection_y.v"]
MODULE_SOURCES["sampler_y_opt"]      = [_PRIS + "/sampler_y_ext.v", "./agent/mldsa/mldsa_src/rejection_y.v"]
MODULE_SOURCES["sampler_a_pristine"] = [_PRIS + "/sampler_a_ext.v", _PRIS + "/rejection_a.v"]
MODULE_SOURCES["sampler_a_opt"]      = [_PRIS + "/sampler_a_ext.v", "./agent/mldsa/mldsa_src/rejection_a.v"]

# --- combined_top: full-chip integration (advisor sequence) ---
import glob as _glob
_TRK  = "./agent/mldsa/mldsa_src"
def _combined_vlist():
    pris = {__import__('os').path.basename(p): p for p in _glob.glob(_PRIS + "/*.v")}
    for p in _repo_glob(_TRK + "/*.v"):
        b = __import__('os').path.basename(p)
        if b in pris:
            pris[b] = p   # tracked override
    return sorted(pris.values())
MODULE_SOURCES["encoder"] = [_PRIS + "/uncenter_coeff.v", _PRIS + "/zero_strip.v", "./agent/mldsa/mldsa_src/encoder.v"]
MODULE_SOURCES["combined_top"]          = _combined_vlist()
def _selective_vlist(keep=("encoder.v",)):
    pris = {__import__('os').path.basename(p): p for p in _glob.glob(_PRIS + "/*.v")}
    for p in _repo_glob(_TRK + "/*.v"):
        b = __import__('os').path.basename(p)
        if b in pris and b in keep:
            pris[b] = p
    return sorted(pris.values())
MODULE_SOURCES["combined_top_selective"] = _selective_vlist()
VHDL_SOURCES["combined_top_selective"] = sorted(_glob.glob(_PRIS + "/*.vhd"))
TOP_OVERRIDE["combined_top_selective"] = "combined_top"
MODULE_SOURCES["combined_top_pristine"] = sorted(_glob.glob(_PRIS + "/*.v"))
VHDL_SOURCES["combined_top"]          = sorted(_glob.glob(_PRIS + "/*.vhd"))
VHDL_SOURCES["combined_top_pristine"] = sorted(_glob.glob(_PRIS + "/*.vhd"))
TOP_OVERRIDE["combined_top_pristine"] = "combined_top"

MODULE_SOURCES["keygen_pristine"] = _mirror_pristine("keygen")
TOP_OVERRIDE["keygen_pristine"] = "keygen"


def main(argv=None):
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", nargs="?", default="poly_mult")
    parser.add_argument("param_set", nargs="?", default="hqc128")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--period", type=float, default=5.0)
    parser.add_argument("--part", default=PART)
    args = parser.parse_args(argv)
    result = run_synthesis(args.module, args.param_set, args.repo_root, args.period, part=args.part)
    print(json.dumps(result, allow_nan=False))
    return 1 if "error" in result else 0


if __name__ == "__main__":
    raise SystemExit(main())
