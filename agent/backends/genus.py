"""Retired machine-specific SSH backend. Use agent.asic_synthesis instead.

This compatibility shim fails before connecting to any host. The legacy backend
ignored remote exit codes, reused reports, allowed blackboxes, and mislabeled
library area. Historical measurements are not revalidated by this change.
"""
try:
    from .base import SynthBackend
except ImportError:
    from backends.base import SynthBackend


class GenusBackend(SynthBackend):
    name = "genus"
    stage = "post_synth"

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "Legacy SSH GenusBackend is disabled. Use agent.asic_synthesis "
            "or scripts/run_asic_tool.py with a reviewed site configuration.")
