"""Genus backend. Dispatches synthesis to the remote ECE server over ssh.
Genus is not installed locally; Vivado is not installed remotely."""
import subprocess, re, os
from backends.base import SynthBackend

HOST   = "engr"
REMOTE = "~/pqc/hqc/asic"
CORNER = "GPDK045_SVT_slow_0p9V_125C"


class GenusBackend(SynthBackend):
    name = "genus"
    stage = "post_synth"

    def __init__(self, effort="high", blackbox_memories=True, period=5.000,
                 srcdir=None, outdir=None, tcl="genus_fmax_arm.tcl"):
        self.effort = effort
        self.blackbox = blackbox_memories
        self.period = period
        self.srcdir = srcdir      # remote path, e.g. ../arms/v_minus_uy_baseline
        self.outdir = outdir      # remote path, e.g. ~/pqc/hqc/asic/out/vmu_baseline
        self.tcl = tcl

    def config_fingerprint(self):
        return {"backend": "genus", "effort": self.effort,
                "corner": CORNER, "blackbox_memories": self.blackbox,
                "period_ns": self.period, "wire_load": "none",
                "place_and_route": False}

    def _ssh(self, cmd, timeout=7200):
        return subprocess.run(["ssh", HOST, cmd], capture_output=True,
                              text=True, timeout=timeout)

    def synthesize(self, module, param_set, srcdir=None, outdir=None, tcl=None):
        srcdir = srcdir or self.srcdir
        outdir = outdir or self.outdir
        tcl    = tcl or self.tcl
        if not srcdir or not outdir:
            return {"error": "GenusBackend needs srcdir and outdir"}
        env = (f"GENUS_PERIOD={self.period:.3f} GENUS_TOP={module} "
               f"GENUS_SRCDIR={srcdir} GENUS_OUTDIR={outdir}")
        r = self._ssh(f"cd {REMOTE}/scripts && {env} "
                      f"timeout 7200 genus -no_gui -f {tcl} > /dev/null 2>&1; echo EXIT=$?")
        rpt = f"{outdir}/{module}_p{self.period:.3f}_timing.rpt"
        t = self._ssh(f"cat {rpt} 2>/dev/null").stdout
        m = re.search(r"Path 1:\s+(MET|VIOLATED)\s+\(([-0-9]+)\s*ps\)", t)
        if not m:
            return {"error": f"no parsable timing report at {rpt}"}
        # guard: reject if the reported path ends at a blackbox pin
        if self.blackbox and re.search(r"Endpoint:.*(RAM|ram|MEM|mem)\b", t):
            return {"error": "critical path terminates at a blackboxed memory; "
                             "number does not measure the design"}
        a = self._ssh(f"cat {outdir}/{module}_p{self.period:.3f}_area.rpt 2>/dev/null").stdout
        am = re.search(r"^\s*" + re.escape(module) + r"\s+\S+\s+(\d+)\s+([\d.]+)", a, re.M)
        slack_ns = int(m.group(2)) / 1000.0
        return {
            "module": module, "param_set": param_set,
            # ASIC analogues of the FPGA keys. Not interchangeable with them.
            "cells": int(am.group(1)) if am else None,
            "area_um2": float(am.group(2)) if am else None,
            "luts": None, "ffs": None, "bram": None, "dsp": None,
            "wns_ns": slack_ns,
            "fmax_mhz": None,          # only meaningful after binary search
            "timing_met": m.group(1) == "MET",
            "total_w": None, "dynamic_w": None, "static_w": None,
            "_config": self.config_fingerprint(),
        }
