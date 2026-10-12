"""Read Vivado reports without turning estimates into measured closure.

``timing_met`` describes setup slack only. Post-synthesis timing and power are
estimates; neither a routed frequency nor complete timing sign-off is implied.
"""
import math
from pathlib import Path
import re

_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"


def _finite_number(token):
    token = token.strip().replace(",", "")
    if not re.fullmatch(_NUMBER, token):
        raise ValueError(f"invalid numeric report value: {token!r}")
    value = float(token)
    if not math.isfinite(value):
        raise ValueError("non-finite numeric report value")
    return value


def _resource(text, labels):
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) >= 4 and cells[1].rstrip("*").strip() in labels:
            value = _finite_number(cells[2])
            if value < 0:
                raise ValueError("negative resource count")
            return int(value) if value.is_integer() else value
    return None


def extract_first_int(text, label):
    """Compatibility helper for pipe-delimited utilization reports."""
    value = _resource(text, {label.strip("| ")})
    return int(value) if value is not None and float(value).is_integer() else value


def extract_wns(text):
    """Read global setup WNS, never an arbitrary clock-table or hold value.

    A malformed global summary is an error, even if a later path looks valid.
    Detailed setup paths are accepted for standalone ``report_timing`` files.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^\s*WNS\(ns\)\s+TNS\(ns\)", line):
            for row in lines[index + 1:]:
                if not row.strip() or set(row.strip()) <= {"-", " "}:
                    continue
                cells = row.split()
                if len(cells) < 4 or not cells[3].isdigit() or int(cells[3]) <= 0:
                    raise ValueError("timing summary has no constrained setup endpoints")
                return _finite_number(cells[0])
            raise ValueError("missing global timing summary row")
    values = []
    for match in re.finditer(r"Slack\s+\((MET|VIOLATED)\)\s*:\s*(\S+)(.*?)(?=Slack\s+\(|\Z)", text, re.S):
        token = re.sub(r"ns$", "", match.group(2))
        value = _finite_number(token)
        if (match.group(1) == "MET") != (value >= 0):
            raise ValueError("slack status disagrees with numeric value")
        if re.search(r"Path Type:\s*Setup\b", match.group(3)):
            values.append(value)
    return min(values) if values else None


def parse_util(filepath):
    text = Path(filepath).read_text()
    result = {
        "luts": _resource(text, {"Slice LUTs", "CLB LUTs"}),
        "ffs": _resource(text, {"Slice Registers", "CLB Registers"}),
        "bram": _resource(text, {"Block RAM Tile"}),
        "dsp": _resource(text, {"DSPs", "DSP48E1", "DSP48E2"}),
    }
    for key in ("luts", "ffs", "dsp"):
        if result[key] is not None and not isinstance(result[key], int):
            raise ValueError(f"non-integer resource count: {key}")
    return result


def parse_power(filepath):
    try:
        text = Path(filepath).read_text()
    except OSError:
        return {"total_w": None, "dynamic_w": None, "static_w": None}
    result = {}
    for key, label in (("total_w", "Total On-Chip Power (W)"),
                       ("dynamic_w", "Dynamic (W)"),
                       ("static_w", "Device Static (W)")):
        try:
            result[key] = _resource(text, {label})
        except ValueError:
            result[key] = None
    return result


def timing_from_text(text, period=5.000, require_summary=False):
    if isinstance(period, bool):
        raise ValueError("period must be finite and positive")
    period = float(period)
    if not math.isfinite(period) or period <= 0:
        raise ValueError("period must be finite and positive")
    if re.search(r"routing\s+is\s+not\s+complete", text, re.I):
        raise ValueError("timing report says routing is incomplete")
    if require_summary and not re.search(r"^\s*WNS\(ns\)\s+TNS\(ns\)", text, re.M):
        raise ValueError("missing global setup timing summary")
    # Validate every detailed slack too: do not accept a corrupt MET label or
    # silently ignore a NaN path just because the summary happens to parse.
    for match in re.finditer(r"Slack\s+\((MET|VIOLATED)\)\s*:\s*(\S+)", text):
        slack = _finite_number(re.sub(r"ns$", "", match.group(2)))
        if (match.group(1) == "MET") != (slack >= 0):
            raise ValueError("slack status disagrees with numeric value")
    wns = extract_wns(text)
    detailed_setup = []
    for match in re.finditer(r"Slack\s+\((MET|VIOLATED)\)\s*:\s*(\S+)(.*?)(?=Slack\s+\(|\Z)", text, re.S):
        if re.search(r"Path Type:\s*Setup\b", match[3]):
            detailed_setup.append(_finite_number(re.sub(r"ns$", "", match[2])))
    if detailed_setup and wns is not None and not math.isclose(min(detailed_setup), wns, abs_tol=0.001):
        raise ValueError("global WNS disagrees with detailed setup paths")
    if require_summary and not detailed_setup:
        raise ValueError("no detailed constrained setup path found")
    if wns is None:
        raise ValueError("no finite setup slack found")
    return {"wns_ns": wns, "fmax_mhz": None, "timing_met": wns >= 0,
            "period_ns": period, "timing_scope": "setup_only",
            "fmax_method": "not_measured"}


def parse_timing(filepath, period=5.000):
    return timing_from_text(Path(filepath).read_text(), period)


def read_ppa(module, param_set, synth_out="synth_out", period=5.000):
    prefix = Path(synth_out) / module / f"{module}_{param_set}"
    try:
        util = parse_util(f"{prefix}_util.rpt")
        missing = [name for name, value in util.items() if value is None]
        if missing:
            raise ValueError("missing utilization values: " + ", ".join(missing))
        timing = timing_from_text(Path(f"{prefix}_timing.rpt").read_text(), period, require_summary=True)
    except (OSError, ValueError) as exc:
        return {"module": module, "param_set": param_set,
                "error": f"invalid Vivado reports: {exc}", "measurement_valid": False}
    power = parse_power(f"{prefix}_power.rpt")
    return {"module": module, "param_set": param_set, **util, **timing, **power,
            "backend": "vivado", "stage": "post_synth",
            "measurement_valid": True, "power_method": "post_synthesis_estimate"}


if __name__ == "__main__":
    import json
    print(json.dumps(read_ppa("poly_mult", "hqc128"), allow_nan=False))
