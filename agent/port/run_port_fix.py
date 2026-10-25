"""Retired remote port-fix experiment; source history remains in Git.

The old workflow used shared remote logs, process-name-wide termination, and
could accept changes without a correctness gate. No safe opt-in is provided.
"""
MESSAGE = (
    "Legacy remote port fixing is disabled before edits, API calls, SSH, or "
    "process termination. Review changes locally, run the applicable correctness "
    "gate, and use scripts/run_asic_tool.py for isolated synthesis. See asic/README.md.")


def genus_accepts(fname):
    raise RuntimeError(MESSAGE)


def run(fname, code, error_text, do_kat=True):
    raise RuntimeError(MESSAGE)


if __name__ == "__main__":
    raise SystemExit(MESSAGE)
