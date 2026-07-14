# HQC Agent - PPA Reader
import re

def extract_first_int(text, label):
    for line in text.splitlines():
        if label in line:
            numbers = re.findall(r"\d+", line)
            if numbers:
                return int(numbers[0])
    return None

def extract_wns(text):
    for line in text.splitlines():
        if line.strip().startswith("clk"):
            numbers = re.findall(r"-?\d+\.\d+", line)
            if len(numbers) >= 6:
                return float(numbers[0])
    return None

def parse_util(filepath):
    with open(filepath, "r") as f:
        text = f.read()
    luts = extract_first_int(text, "Slice LUTs")
    ffs  = extract_first_int(text, "Slice Registers")
    bram = extract_first_int(text, "Block RAM Tile")
    dsp  = extract_first_int(text, "| DSPs")
    return {"luts": luts, "ffs": ffs, "bram": bram, "dsp": dsp}

def parse_power(filepath):
    try:
        with open(filepath, "r") as f:
            text = f.read()
    except OSError:
        return {"total_w": None, "dynamic_w": None, "static_w": None}
    def grab(label):
        for line in text.splitlines():
            if label in line:
                m = re.findall(r"\d+\.\d+", line)
                if m:
                    return float(m[0])
        return None
    return {"total_w":   grab("Total On-Chip Power (W)"),
            "dynamic_w": grab("Dynamic (W)"),
            "static_w":  grab("Device Static (W)")}

def parse_timing(filepath):
    with open(filepath, "r") as f:
        text = f.read()
    wns  = extract_wns(text)
    fmax = round(1000 / (5.000 - wns), 1) if wns is not None else None
    return {"wns_ns": wns, "fmax_mhz": fmax, "timing_met": wns >= 0 if wns is not None else None}

def read_ppa(module, param_set, synth_out="synth_out"):
    util_path   = f"{synth_out}/{module}/{module}_{param_set}_util.rpt"
    timing_path = f"{synth_out}/{module}/{module}_{param_set}_timing.rpt"
    power_path  = f"{synth_out}/{module}/{module}_{param_set}_power.rpt"
    util        = parse_util(util_path)
    timing      = parse_timing(timing_path)
    power       = parse_power(power_path)
    result = {
        "module":     module,
        "param_set":  param_set,
        "luts":       util["luts"],
        "ffs":        util["ffs"],
        "bram":       util["bram"],
        "dsp":        util["dsp"],
        "wns_ns":     timing["wns_ns"],
        "fmax_mhz":   timing["fmax_mhz"],
        "timing_met": timing["timing_met"],
        "total_w":    power["total_w"],
        "dynamic_w":  power["dynamic_w"],
        "static_w":   power["static_w"]
    }
    return result

if __name__ == "__main__":
    result = read_ppa("poly_mult", "hqc128")
    print(result)
