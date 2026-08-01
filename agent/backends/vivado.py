"""Vivado backend. Wraps existing synthesizer.py unchanged so FPGA
results stay reproducible."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from synthesizer import run_synthesis
from backends.base import SynthBackend


class VivadoBackend(SynthBackend):
    name = "vivado"
    stage = "post_synth"      # run_synthesis is OOC synth; fmax_search.py is post_route

    def __init__(self, part="xc7a200tfbg676-1", period=5.000, ooc=True):
        self.part, self.period, self.ooc = part, period, ooc

    def config_fingerprint(self):
        return {"backend": "vivado", "part": self.part,
                "period_ns": self.period, "ooc": self.ooc}

    def synthesize(self, module, param_set, repo_root="."):
        r = run_synthesis(module, param_set, repo_root, self.period)
        if "error" not in r:
            r["_config"] = self.config_fingerprint()
        return r
