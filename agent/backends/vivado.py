"""Vivado post-synthesis estimates, distinct from routed closure search."""
if __package__ and "." in __package__:
    from ..synthesizer import run_synthesis
    from .base import SynthBackend
else:
    from synthesizer import run_synthesis
    from backends.base import SynthBackend


class VivadoBackend(SynthBackend):
    name = "vivado"
    stage = "post_synth"

    def __init__(self, part="xc7a200tfbg676-1", period=5.000, ooc=True):
        self.part, self.period, self.ooc = part, period, ooc

    def config_fingerprint(self):
        return {"backend": "vivado", "part": self.part,
                "period_ns": self.period, "ooc": self.ooc}

    def synthesize(self, module, param_set, repo_root="."):
        result = run_synthesis(module, param_set, repo_root, self.period,
                               part=self.part, ooc=self.ooc)
        if "error" not in result:
            result["_config"] = self.config_fingerprint()
            result["backend"] = self.name
            result["stage"] = self.stage
        return result
