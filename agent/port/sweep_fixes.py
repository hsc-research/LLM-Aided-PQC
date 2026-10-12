"""Retired remote port-fix sweep. No network or mutation on import."""
try:
    from .run_port_fix import MESSAGE
except ImportError:
    from run_port_fix import MESSAGE


def probe(basename):
    raise RuntimeError(MESSAGE)


if __name__ == "__main__":
    raise SystemExit(MESSAGE)
