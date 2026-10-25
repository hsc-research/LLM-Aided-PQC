"""Explicit FPGA selector correction; no vendor EDA or external API required."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.export_mldsa_fpga_latch_corrected import (ROOT, VARIANTS, REPORT_ROOT, correct_selector,
                                                    export, validate_evidence, sha)
from tools.export_mldsa_verified import export as reference_export
from tools.export_target_profiles import export_profile, verify_profile, fingerprint


class FpgaLatchCorrectionTests(unittest.TestCase):
    def test_only_two_defaults_change_for_both_variants(self):
        for variant, reference in VARIANTS.items():
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as tmp:
                tmp=Path(tmp); reference_export(tmp/'reference',reference)
                manifest=export(tmp/'corrected',variant)
                old=json.loads((tmp/'reference/manifest.json').read_text())
                self.assertEqual(len(manifest['sources']),35)
                for a,b in zip(old['sources'],manifest['sources']):
                    self.assertEqual(a['path'],b['path'])
                    if a['path']=='rtl/gen_c.v':
                        self.assertEqual(correct_selector((tmp/'reference'/a['path']).read_text()),
                                         (tmp/'corrected'/b['path']).read_text())
                    else:self.assertEqual(a,b)
                self.assertEqual((tmp/'reference/zetas.txt').read_bytes(),(tmp/'corrected/zetas.txt').read_bytes())

    def test_transform_fails_closed_on_repeat_or_changed_anchor(self):
        text=(ROOT/'third_party/mldsa_osh/upstream/ref_combined/src/gen_c.v').read_text()
        with self.assertRaises(ValueError):correct_selector(correct_selector(text))
        with self.assertRaises(ValueError):correct_selector(text.replace('ctilde_out_len = 0;','ctilde_out_len = 1;'))

    def test_profiles_explicit_fpga_only_and_remain_target_unqualified(self):
        for variant in VARIANTS:
            with self.subTest(variant=variant),tempfile.TemporaryDirectory() as tmp:
                tmp=Path(tmp)
                a=export_profile('mldsa',variant,None,'fpga',tmp/'a')
                b=export_profile('mldsa',variant,None,'fpga',tmp/'b')
                self.assertEqual(a,b)
                self.assertFalse(a['qualification']['target_tool_qualified'])
                self.assertEqual(a['boundary']['clock_ports'],['clk'])
                self.assertEqual(a,verify_profile(tmp/'a/profile.json'))
                with self.assertRaises(ValueError):export_profile('mldsa',variant,None,'asic',tmp/'bad')
                altered=copy.deepcopy(a);altered['target']['kind']='asic';altered['target']['memory_implementation']='flops'
                altered['profile_fingerprint']=fingerprint(altered)
                (tmp/'a/profile.json').write_text(json.dumps(altered))
                with self.assertRaises(ValueError):verify_profile(tmp/'a/profile.json')

    def test_evidence_rejects_claim_only_or_changed_sources(self):
        variant=next(iter(VARIANTS));root=ROOT/REPORT_ROOT/variant
        good=json.loads((root/'result.json').read_text())
        for mutation in ('status','source','coverage','inventory','selector','missing_selector','missing_compile'):
            bad=copy.deepcopy(good)
            if mutation=='status':bad['status']='FAIL'
            elif mutation=='source':bad['source_hashes']['rtl/gen_c.v']='0'*64
            elif mutation=='coverage':bad['coverage']['keygen:seed-0']['completed']=1
            elif mutation=='inventory':bad['evidence_files_sha256']={}
            elif mutation=='missing_selector':bad['evidence_files_sha256'].pop('selector/result.json')
            elif mutation=='missing_compile':bad['evidence_files_sha256'].pop('keygen/compile.log')
            else:bad['supported_selector_differential']='FAIL'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                validate_evidence(bad,root,variant,good['source_hashes'],good['data_sha256'])

if __name__=='__main__':unittest.main()
