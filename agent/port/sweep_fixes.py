"""Work through the confirmed-defect file list: probe -> extract first error
-> propose -> gate. One file at a time; each KAT is minutes."""
import sys, os, subprocess, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_port_fix import run

HOST = "engr"
REPO = "/mnt/c/PQC/hqc"

# (source path under hardware/, basename)
TARGETS = [
    "encap/reed_muller_encode.v",
    "decap/fft_part1.v",
    "common/shake256/rtl/state_ram.v",
    "keygen/vect_set_random.v",
    "common/fixed_weight/fixed_weight.v",
    "common/fixed_weight/fixed_weight_ct.v",
    "common/fixed_weight/fixed_weight_cww.v",
    "keygen/keygen.v",
    "encap/encap.v",
    "encap/encrypt.v",
    "encap/encrypt_parallel.v",
    "decap/decap.v",
]


def probe(basename):
    """Run Genus parse check, return (code, error_text)."""
    subprocess.run(["ssh", HOST,
        f"cd ~/pqc/hqc/asic/portwork && GENUS_FILE=../../build/joint_design/{basename} "
        f"timeout 900 genus -no_gui -f parse_check.tcl > /dev/null 2>&1"],
        capture_output=True)
    r = subprocess.run(["ssh", HOST,
        "grep -m 1 -B 4 -A 6 'Error' $(ls -t ~/pqc/hqc/asic/portwork/genus.log* | head -n 1)"],
        capture_output=True, text=True)
    txt = r.stdout
    if not txt.strip():
        return None, ""
    import re
    m = re.search(r"\[([A-Z]+-\d+)\]", txt)
    return (m.group(1) if m else None), txt


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for rel in TARGETS:
        base = os.path.basename(rel)
        if only and only != base:
            continue
        if not os.path.exists(f"{REPO}/hardware/{rel}"):
            print(f"[{base}] SKIP: not at hardware/{rel}"); continue
        print(f"\n=== {base} ===")
        code, err = probe(base)
        if not code:
            print(f"  no error found, already clean"); continue
        print(f"  first error: {code}")
        run(rel, code, err, do_kat=True)
        time.sleep(2)
