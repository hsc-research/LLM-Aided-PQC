"""No-EDA tests of the verified ML-DSA source handoff."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.export_mldsa_verified import REPO, export, validate_report


class MLDSAExportTests(unittest.TestCase):
    def report(self):
        return json.loads((REPO/'docs/verification/mldsa-portable-2026-10-12/candidate_corrected_pass/result.json').read_text())

    def test_report_requires_exact_variant_and_coverage(self):
        good=self.report();validate_report(good,'corrected-candidate')
        for mutate in (
            lambda r:r.update(status='FAIL'),
            lambda r:r.update(variant='candidate'),
            lambda r:r['coverage']['verify'].update(known_valid=36,known_invalid=9),
            lambda r:r['coverage']['sign'].update(status='FAIL'),
            lambda r:r['coverage']['keygen'].update(simulator_returncode=1),
            lambda r:r['coverage']['verify_canonical']['vectors'].__setitem__(0,r['coverage']['verify_canonical']['vectors'][1]),
            lambda r:r['coverage']['sign'].update(completed=44),
        ):
            bad=copy.deepcopy(good);mutate(bad)
            with self.assertRaises(ValueError):validate_report(bad,'corrected-candidate')

    def test_report_rejects_boolean_and_float_integer_fields(self):
        good=self.report()
        for mutate in (
            lambda r:r['coverage']['keygen']['vectors'][0].update(cycles=True),
            lambda r:r['coverage']['keygen']['vectors'][0].update(kat=False),
            lambda r:r['coverage']['keygen']['vectors'][0].update(kat=0.0),
            lambda r:r['coverage']['keygen'].update(simulator_returncode=False),
            lambda r:r['coverage']['keygen'].update(completed=75.0),
            lambda r:r['coverage']['verify_mutations'].update(known_valid=False),
        ):
            bad=copy.deepcopy(good);mutate(bad)
            with self.assertRaises(ValueError):validate_report(bad,'corrected-candidate')

    def test_both_exact_verilog_arms(self):
        for variant in ('guarded-baseline','corrected-candidate'):
            with tempfile.TemporaryDirectory() as folder:
                result=export(Path(folder)/'out',variant)
                manifest=json.loads(Path(result['manifest']).read_text())
                self.assertEqual(len(manifest['sources']),35)
                self.assertEqual(manifest['top'],'combined_top')
                self.assertEqual(manifest['sources'][-1]['path'],'rtl/combined_top.v')
                for row in manifest['sources']:
                    actual=hashlib.sha256((Path(result['out'])/row['path']).read_bytes()).hexdigest()
                    self.assertEqual(actual,row['sha256'])

    def test_mixed_manifest_never_compiles_duplicate_keccak(self):
        with tempfile.TemporaryDirectory() as folder:
            result=export(Path(folder)/'out','corrected-candidate','mixed')
            manifest=json.loads(Path(result['manifest']).read_text())
            self.assertEqual(sum(x['language']=='vhdl2008' for x in manifest['sources']),16)
            self.assertEqual(len(manifest['sources']),50)
            self.assertEqual(manifest['sources'][0]['path'],'rtl/sha3_pkg.vhd')
            self.assertFalse((Path(result['out'])/'rtl/keccak_top_ghdl.v').exists())

    def test_exports_deterministic_and_nonoverwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            outputs=[Path(folder)/name for name in ('first','second')]
            for out in outputs:export(out)
            snapshots=[{str(p.relative_to(out)):p.read_bytes() for p in out.rglob('*') if p.is_file()} for out in outputs]
            self.assertEqual(snapshots[0],snapshots[1])
            with self.assertRaisesRegex(ValueError,'never overwritten'):export(outputs[0])


if __name__=='__main__':unittest.main()
