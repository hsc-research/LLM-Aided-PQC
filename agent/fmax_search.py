#!/usr/bin/env python3
"""Find the fastest *observed* routed setup-closing point in a bounded search.

Place-and-route results need not be monotonic. Endpoint checks and a bisection
heuristic are useful sampling, not a proof of a global maximum. Historical
closing_* JSON fields are retained for consumers; failed/incomplete searches
leave those fields null even if an earlier individual probe closed.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

if __package__:
    from .ppa_reader import timing_from_text
    from .run_safety import run_process
else:
    from ppa_reader import timing_from_text
    from run_safety import run_process


RECIPE = {"place": "ExtraTimingOpt", "phys_opt": "Explore", "route": "Explore"}


def _quote(value):
    value = str(value)
    for old, new in (("\\", "\\\\"), ('"', '\\"'), ("$", "\\$"),
                     ("[", "\\["), ("]", "\\]"), ("{", "\\{"), ("}", "\\}"), ("\n", "\\n"), ("\r", "\\r")):
        value = value.replace(old, new)
    return '"' + value + '"'


def build_tcl(checkpoint, period, report):
    return f"""if {{[catch {{
open_checkpoint {_quote(checkpoint)}
set clk_ports [get_ports -quiet {{clk clk_i}}]
if {{[llength $clk_ports] == 0}} {{ set clk_ports [get_ports -quiet *clk*] }}
if {{[llength $clk_ports] != 1}} {{ error "Expected exactly one clock input" }}
create_clock -period {period:.12g} -name clk $clk_ports
opt_design
place_design -directive {RECIPE['place']}
phys_opt_design -directive {RECIPE['phys_opt']}
route_design -directive {RECIPE['route']}
report_route_status -file {_quote(str(report) + '.route')}
report_timing_summary -file {_quote(report)}
report_utilization -file {_quote(str(report) + '.util')}
puts "PQC_FMAX_PROBE_DONE"
}} message]}} {{ puts stderr $message; exit 1 }}
exit 0
"""


def validate_route(text):
    """Require positive routing evidence, not just absence of one warning.

    UG906 Report Route Status omits optional zero-count error categories.
    Routable and fully-routed counts plus the routing-error total are required.
    """
    def count(label, required=True):
        match = re.search(r"#\s*of\s+" + re.escape(label) + r"\.*\s*:\s*([\d,]+)\s*:", text, re.I)
        if match is None:
            if required:
                raise ValueError(f"missing route-status count: {label}")
            return None
        return int(match[1].replace(",", ""))
    routable = count("routable nets")
    routed = count("fully routed nets")
    errors = count("nets with routing errors")
    if routable <= 0 or routed != routable or errors:
        raise ValueError("design is not fully routed without routing errors")
    for label in ("unrouted nets", "nets with some unrouted pins", "nets with antennas/islands", "nets with resource conflicts"):
        if count(label, required=False):
            raise ValueError(f"route-status reports {label}")


def validate_timing(text, period):
    result = timing_from_text(text, period, require_summary=True)
    # A detailed constrained setup path proves that the summary is not an empty
    # all-zero table, and preserves the downstream worst-path report contract.
    setup_slacks = []
    for match in re.finditer(r"Slack\s+\((MET|VIOLATED)\)\s*:\s*([+-]?[\d.eE+-]+)ns(.*?)(?=Slack\s+\(|\Z)", text, re.S):
        detail = match[3]
        if re.search(r"Path Type:\s*Setup\b", detail):
            if not re.search(r"Source:\s*\S+", detail) or not re.search(r"Destination:\s*\S+", detail):
                raise ValueError("setup path lacks endpoints")
            setup_slacks.append(float(match[2]))
    if not setup_slacks or not math.isclose(min(setup_slacks), result["wns_ns"], abs_tol=0.001):
        raise ValueError("global WNS is not corroborated by a detailed setup path")
    periods = [float(value) for value in re.findall(r"period=([\d.eE+-]+)ns", text)]
    if not periods or any(not math.isfinite(value) or not math.isclose(value, period, abs_tol=0.00051) for value in periods):
        raise ValueError("report clock period does not match the requested single-clock probe")
    return result


def probe(checkpoint, tag, period, run_dir, *, attempts=2, timeout=7200, vivado="vivado"):
    """Each attempt has a unique directory; a prior report can never be read."""
    started = time.monotonic()
    failures = []
    for attempt in range(1, attempts + 1):
        work = Path(tempfile.mkdtemp(prefix=f"p{period}-a{attempt}-", dir=run_dir))
        report = work / "timing.rpt"
        script = work / "probe.tcl"
        script.write_text(build_tcl(checkpoint, period, report))
        try:
            result = run_process([vivado, "-mode", "batch", "-notrace", "-source", str(script),
                                  "-journal", str(work / "vivado.jou"), "-log", str(work / "vivado.log")],
                                 cwd=work, timeout=timeout, log_path=work / "process.log")
            output = (result.stdout or "") + (result.stderr or "")
            if result.returncode:
                raise ValueError(f"Vivado exited {result.returncode}")
            if not re.search(r"^PQC_FMAX_PROBE_DONE\s*$", output, re.M) or re.search(r"^\s*ERROR:", output, re.M):
                raise ValueError("Vivado completion marker missing or error output present")
            validate_route(Path(str(report) + ".route").read_text())
            timing = validate_timing(report.read_text(), period)
            return {"period_ns": period, "valid": True, "met": timing["timing_met"],
                    "wns_ns": timing["wns_ns"], "report_path": str(report),
                    "attempts": attempt, "failures": failures,
                    "runtime_s": round(time.monotonic() - started, 3)}
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            failures.append({"attempt": attempt, "error": str(exc), "run_dir": str(work)})
    return {"period_ns": period, "valid": False, "met": None, "wns_ns": None,
            "attempts": attempts, "failures": failures,
            "runtime_s": round(time.monotonic() - started, 3)}


def search(checkpoint, tag, lo_ns=6.0, hi_ns=12.0, *, iterations=5, attempts=2,
           timeout=7200, vivado="vivado", output_dir=None, legacy_dir="/tmp"):
    result = {"tag": tag, "closing_period_ns": None, "closing_fmax_mhz": None,
              "wns_at_close": None, "backend": "vivado", "stage": "post_route",
              "measurement_scope": "single_clock_setup_only",
              "search_method": "endpoint_checked_bisection_heuristic",
              "global_maximum_proven": False, "search_complete": False,
              "measurement_valid": False, "trace": [], "config": dict(RECIPE)}
    try:
        if not isinstance(tag, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", tag):
            raise ValueError("tag must contain only letters, digits, underscore, dot or dash")
        if isinstance(lo_ns, bool) or isinstance(hi_ns, bool):
            raise ValueError("period bounds must be finite positive numbers")
        lo, hi = float(lo_ns), float(hi_ns)
        if not (math.isfinite(lo) and math.isfinite(hi) and 0 < lo < hi):
            raise ValueError("require finite 0 < lo_ns < hi_ns")
        if round(lo, 2) != lo or round(hi, 2) != hi:
            raise ValueError("period bounds must use at most two decimal places")
        if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations < 0:
            raise ValueError("iterations must be a nonnegative integer")
        if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
            raise ValueError("attempts must be a positive integer")
        if isinstance(timeout, bool) or not math.isfinite(float(timeout)) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        checkpoint = Path(checkpoint).resolve()
        if not checkpoint.is_file():
            raise ValueError(f"checkpoint does not exist: {checkpoint}")
        root = Path(output_dir) if output_dir is not None else Path.cwd() / ".pqc_runs" / "fmax"
        root.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix=f"{tag}-", dir=root))
        result.update({"run_dir": str(work), "requested_bounds_ns": [lo, hi],
                       "iterations_requested": iterations})
    except (OSError, TypeError, ValueError) as exc:
        result.update(status="INVALID_INPUT", error=str(exc))
        return result

    def measure(period):
        observation = probe(checkpoint, tag, period, work, attempts=attempts,
                            timeout=timeout, vivado=vivado)
        result["trace"].append(observation)
        return observation

    try:
        low = measure(lo)
        high = measure(hi)
        if not low["valid"] or not high["valid"]:
            result.update(status="INCOMPLETE", error="invalid endpoint probe")
            return result
        if not low["met"] and high["met"]:
            for _ in range(iterations):
                mid = round((lo + hi) / 2, 2)
                if not lo < mid < hi:
                    break
                sample = measure(mid)
                if not sample["valid"]:
                    result.update(status="INCOMPLETE", error="invalid intermediate probe")
                    return result
                if sample["met"]:
                    hi = mid
                else:
                    lo = mid
        result["search_complete"] = True
        result["nonmonotonic_observed"] = any(
            first["met"] and not second["met"] and first["period_ns"] < second["period_ns"]
            for first in result["trace"] for second in result["trace"])
        closed = [sample for sample in result["trace"] if sample["met"]]
        if not closed:
            result.update(status="NO_CLOSURE_OBSERVED", error="no measured setup-closing point in sampled periods")
            return result
        best = min(closed, key=lambda sample: sample["period_ns"])
        # Stable aliases are published only after a complete valid search. The
        # private report path remains the authoritative artifact in the result.
        alias = Path(legacy_dir) / f"fsrch_{tag}_{best['period_ns']}.rpt"
        alias.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=alias.parent, delete=False) as stream:
            staging = Path(stream.name)
        try:
            shutil.copyfile(best["report_path"], staging)
            os.replace(staging, alias)
        finally:
            staging.unlink(missing_ok=True)
        result.update(status="OBSERVED_CLOSURE", measurement_valid=True,
                      closing_period_ns=best["period_ns"],
                      closing_fmax_mhz=round(1000 / best["period_ns"], 1),
                      wns_at_close=best["wns_ns"], report_path=best["report_path"],
                      legacy_report_path=str(alias), final_sampled_bracket_ns=[lo, hi],
                      lower_bound_closed=low["met"], upper_bound_closed=high["met"])
        return result
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        result.update(status="INCOMPLETE", error=str(exc), search_complete=False)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint")
    parser.add_argument("tag")
    parser.add_argument("lo_ns", nargs="?", type=float, default=6.0)
    parser.add_argument("hi_ns", nargs="?", type=float, default=12.0)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=7200)
    args = parser.parse_args(argv)
    result = search(args.checkpoint, args.tag, args.lo_ns, args.hi_ns,
                    iterations=args.iterations, timeout=args.timeout)
    print(json.dumps(result, allow_nan=False))
    return 0 if result["measurement_valid"] and result["search_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
