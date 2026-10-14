"""Replay the exact historical baseline through the current exported adapter.

Select an already-installed Verilator via PATH. No installation, APIs, or EDA.
The output directory must be new. Run this script from any working directory.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agent.mldsa.exported_kat_adapter import dependencies, verify
from agent.run_safety import hashes
from tools.export_target_profiles import export_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    profile = out / 'profile'
    export_profile('mldsa', 'fpga-latch-corrected-baseline', None, 'fpga', profile)
    historical = ROOT / 'docs/verification/fpga-agent-feedback-2026-10-13/exact-export-kat/request.json'
    request = json.loads(historical.read_text())
    old = str(Path(request['configuration']['source_read_order'][0]).parents[2])

    def relocate(value):
        if isinstance(value, str):
            return value.replace(old, str(profile))
        if isinstance(value, list):
            return [relocate(item) for item in value]
        if isinstance(value, dict):
            return {relocate(key): relocate(item) for key, item in value.items()}
        return value

    request = relocate(request)
    # Confirm the re-export matches historical source bytes, not just filenames.
    if hashes(request['source_hashes']) != request['source_hashes']:
        raise ValueError('Export no longer matches the historical baseline')
    request['configuration']['immutable_hashes'] = hashes(
        dependencies() + [str(profile / 'source-bundle/zetas.txt')])
    (out / 'request.json').write_text(json.dumps(request, indent=2) + '\n')
    verify(out / 'request.json', out / 'response.json')


if __name__ == '__main__':
    main()
