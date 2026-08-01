"""Synthesis backend interface.

IMPORTANT: backends are not interchangeable measurements.
  vivado -> post-route closure on a checkpoint (place + route)
  genus   -> post-synthesis only, no place-and-route, zero wire load
A number from one backend may never be compared against the other.
Every result carries `stage` and `config` so this cannot be lost.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class FmaxResult:
    backend: str                 # "vivado" | "genus"
    stage: str                   # "post_route" | "post_synth"
    tag: str
    closing_period_ns: Optional[float]
    closing_fmax_mhz: Optional[float]
    slack_at_close: Optional[float]
    config: dict = field(default_factory=dict)   # effort, directives, corner, blackboxing
    trace: list = field(default_factory=list)    # [{period, met, slack, runtime_s}]

    def to_json(self):
        return asdict(self)


class SynthBackend:
    name: str = "abstract"
    stage: str = "unknown"

    def config_fingerprint(self) -> dict:
        """Everything that would change the number if varied."""
        raise NotImplementedError

    def measure_fmax(self, target, tag, lo_ns, hi_ns) -> FmaxResult:
        raise NotImplementedError


def assert_comparable(a: FmaxResult, b: FmaxResult):
    """Refuse to compare two results measured differently. F3: effort alone
    moves Genus Fmax by 10.9%, larger than the deltas being measured."""
    if a.backend != b.backend:
        raise ValueError(f"backend mismatch: {a.backend} vs {b.backend}")
    if a.stage != b.stage:
        raise ValueError(f"stage mismatch: {a.stage} vs {b.stage}")
    if a.config != b.config:
        diff = {k: (a.config.get(k), b.config.get(k))
                for k in set(a.config) | set(b.config)
                if a.config.get(k) != b.config.get(k)}
        raise ValueError(f"config mismatch, not comparable: {diff}")
    return True
