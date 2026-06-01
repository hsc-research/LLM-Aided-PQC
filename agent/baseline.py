# HQC Agent - Baseline Store
# Holds the recorded Phase 2 PPA numbers for all five modules.
# Any candidate result gets compared against these.

BASELINE = {
    ("poly_mult", "hqc128"): {"luts": 1363, "ffs": 368, "bram": 4, "dsp": 0, "wns_ns":  0.080, "fmax_mhz": 203.3},
    ("poly_mult", "hqc192"): {"luts": 1422, "ffs": 372, "bram": 4, "dsp": 0, "wns_ns": -0.258, "fmax_mhz": 193.0},
    ("poly_mult", "hqc256"): {"luts": 1431, "ffs": 346, "bram": 4, "dsp": 0, "wns_ns": -0.092, "fmax_mhz": 198.2},
    ("fixed_weight", "hqc128"): {"luts": 235, "ffs": 119, "bram": 2, "dsp": 0, "wns_ns": -2.064, "fmax_mhz": 161.7},
    ("fixed_weight", "hqc192"): {"luts": 226, "ffs": 120, "bram": 2, "dsp": 0, "wns_ns": -1.622, "fmax_mhz": 170.4},
    ("fixed_weight", "hqc256"): {"luts": 241, "ffs": 125, "bram": 2, "dsp": 0, "wns_ns": -1.618, "fmax_mhz": 170.5},
    ("keygen", "hqc128"): {"luts": 1199, "ffs": 727, "bram": 10.5, "dsp": 0, "wns_ns": -2.064, "fmax_mhz": 161.7},
    ("keygen", "hqc192"): {"luts": 1260, "ffs": 734, "bram": 10.5, "dsp": 0, "wns_ns": -1.165, "fmax_mhz": 178.6},
    ("keygen", "hqc256"): {"luts": 1262, "ffs": 752, "bram": 11,   "dsp": 0, "wns_ns": -0.822, "fmax_mhz": 184.9},
    ("encap", "hqc128"): {"luts": 2607, "ffs": 1993, "bram": 13,   "dsp": 0, "wns_ns": -1.317, "fmax_mhz": 176.3},
    ("encap", "hqc192"): {"luts": 2776, "ffs": 2263, "bram": 15.5, "dsp": 0, "wns_ns": -1.306, "fmax_mhz": 176.5},
    ("encap", "hqc256"): {"luts": 3264, "ffs": 2880, "bram": 15.5, "dsp": 0, "wns_ns": -1.055, "fmax_mhz": 179.5},
    ("decap", "hqc128"): {"luts": 7578, "ffs": 6462, "bram": 20,   "dsp": 0, "wns_ns": -2.233, "fmax_mhz": 159.4},
    ("decap", "hqc192"): {"luts": 8363, "ffs": 7764, "bram": 22.5, "dsp": 0, "wns_ns": -2.238, "fmax_mhz": 159.4},
    ("decap", "hqc256"): {"luts": 9316, "ffs": 9266, "bram": 22.5, "dsp": 0, "wns_ns": -2.242, "fmax_mhz": 159.3},
}

def compare(result):
    key = (result["module"], result["param_set"])
    if key not in BASELINE:
        return {"error": f"no baseline found for {key}"}

    base = BASELINE[key]
    delta = {}
    for metric in ("luts", "ffs", "bram", "dsp", "wns_ns", "fmax_mhz"):
        old = base[metric]
        new = result[metric]
        if old is not None and new is not None:
            change = new - old
            pct    = round((change / old) * 100, 1) if old != 0 else None
            better = _is_better(metric, change)
            delta[metric] = {"baseline": old, "candidate": new, "change": round(change, 3), "pct": pct, "better": better}

    return delta

def _is_better(metric, change):
    # For area metrics lower is better. For wns and fmax higher is better.
    if metric in ("luts", "ffs", "bram", "dsp"):
        return change < 0
    if metric in ("wns_ns", "fmax_mhz"):
        return change > 0
    return None
