"""Deterministic source checks; no EDA tools, external API or network calls."""
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'tools'))
from build_mldsa_startup_derivative import build,sha,mask,rewrite_state,REFERENCE_MANIFESTS

# Standalone staging location and final integrated location are both supported.
SOURCE=REPO/'asic/rtl/mldsa_startup'
FROZEN=SOURCE if (SOURCE/'guarded-baseline/manifest.json').exists() else REPO/'release'
REFERENCE=REPO/'reference'

class StartupSources(unittest.TestCase):
    def test_restart_marker_is_required(self):
        from check_mldsa_startup_kats import check_restart_evidence
        kat='ML-DSA-II.KeyGen, KAT # 0 completed in 123 clock cycles\n'
        self.assertEqual(check_restart_evidence('ASIC_RESTARTS_PASS count=2\n'+kat)['observed_aborts'],2)
        for bad in (kat, 'ASIC_RESTARTS_PASS count=1\n'+kat, kat+'ASIC_RESTARTS_PASS count=2\n',
                    'ASIC_RESTARTS_PASS count=2\nASIC_RESTARTS_PASS count=2\n'+kat):
            with self.assertRaises(ValueError):check_restart_evidence(bad)

    def test_no_powerup_state(self):
        for arm in ('guarded-baseline','corrected-candidate'):
            manifest=json.loads((FROZEN/arm/'manifest.json').read_text())
            self.assertEqual(manifest['top'],'combined_top_asic')
            self.assertEqual(len(manifest['sources']),36)
            self.assertEqual([r['path'] for r in manifest['sources']],sorted(r['path'] for r in manifest['sources']))
            for row in manifest['sources']:
                p=FROZEN/arm/row['path']
                self.assertEqual(sha(p),row['sha256'])
                self.assertNotRegex(mask(p.read_text()),r'\binitial\b|\$readmem[hb]')

    def test_same_boot_and_memory_overhead(self):
        for name in ('mldsa_sameclock_ff_ram.v','combined_top_asic.v','dual_port_rom.v'):
            a=FROZEN/'guarded-baseline/rtl'/name;b=FROZEN/'corrected-candidate/rtl'/name
            self.assertEqual(a.read_bytes(),b.read_bytes())

    def test_ram_banks_and_clock(self):
        for arm in ('guarded-baseline','corrected-candidate'):
            top=(FROZEN/arm/'rtl/combined_top.v').read_text()
            banks=re.findall(r'mldsa_sameclock_ff_ram #\(\.WIDTH\(96\), \.LENGTH\((\d+)\)\)',top)
            self.assertEqual(banks,['4096']+['1024']*6)
            self.assertNotIn('clk,clk',top)
            self.assertEqual(top.count('(clk, asic_boot_reset, asic_scrub_enable, asic_scrub_address,'),7)

    def test_boot_is_distinct_from_ordinary_reset(self):
        s=(SOURCE/'combined_top_asic.v').read_text()
        self.assertIn('if (boot_rst)',s)
        self.assertNotIn('if (rst)',s)
        self.assertIn("boot_address == 12'd4095",s)
        self.assertIn('.rst(rst | hold_core)',s)
        self.assertIn('.start(start & ~hold_core)',s)
        self.assertIn('.valid_i(valid_i & ~hold_core)',s)

    def test_80_byte_storage_not_padded(self):
        for arm in ('guarded-baseline','corrected-candidate'):
            s=(FROZEN/arm/'rtl/makehint.v').read_text()
            self.assertEqual(s.count('reg [7:0] hint_addr [79:0];'),1)
            self.assertIn('wire [7:0] asic_hint_read [127:0];',s)
            self.assertEqual(s.count('asic_hint_read[ctr*8+k]'),5)
            self.assertEqual(s.count('hint_addr[num_hints'),4)

    def test_supported_hint_read_bounds(self):
        maxima={}
        for level,omega in ((2,80),(3,55),(5,75)):
            observed=[]
            for ctr in range(256):
                if level==2:
                    count=8 if 8*ctr<omega else 0
                elif 8*(ctr+1)<omega:count=8
                elif 8*ctr<omega:count=7 if level==3 else 3
                else:count=0
                observed.extend(8*ctr+k for k in range(count))
            self.assertTrue(all(0<=i<80 for i in observed));maxima[level]=max(observed)
        self.assertEqual(maxima,{2:79,3:54,5:74})

    def test_redundant_initializers_are_classified(self):
        for arm in ('guarded-baseline','corrected-candidate'):
            m=json.loads((FROZEN/arm/'manifest.json').read_text())
            rows=[e for group in m['startup_audit'].values() for e in group]
            self.assertEqual(sum(e['kind']=='combinational_initializer_removed' for e in rows),40)
            self.assertTrue(any(e['kind']=='read_only_constant' for e in rows))
            self.assertTrue(any(e['kind']=='unsupported_selector_default' for e in rows))
            self.assertTrue(any(e['kind']=='inactive_read_mux_definition' for e in rows))

    def test_unknown_initial_driver_rejected(self):
        with self.assertRaisesRegex(ValueError,'no driver'):
            rewrite_state('module a(input clk, output [3:0] y); reg [3:0] t=0; assign y=t; endmodule','unknown.v')

    def test_bad_reference_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ref=Path(td)/'ref';ref.mkdir();(ref/'manifest.json').write_text(json.dumps({'variant':'guarded-baseline'}))
            with self.assertRaisesRegex(ValueError,'exact pinned'):
                build(ref,Path(td)/'out',SOURCE)

    def test_occupied_output_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'out';out.mkdir();(out/'existing').write_text('keep')
            with self.assertRaisesRegex(ValueError,'absent or empty'):
                build('missing-reference',out,SOURCE)
            self.assertEqual((out/'existing').read_text(),'keep')

    def test_reproducible_from_verified_exports(self):
        if not REFERENCE.exists():
            from tools.export_mldsa_verified import export
        for arm in ('guarded-baseline','corrected-candidate'):
            with tempfile.TemporaryDirectory() as td:
                ref=REFERENCE/arm
                if not ref.exists():
                    ref=Path(td)/'ref';export(ref,arm)
                out=Path(td)/'rebuilt'
                actual=build(ref,out,SOURCE)
                expected=json.loads((FROZEN/arm/'manifest.json').read_text())
                self.assertEqual(actual,expected)
                for row in actual['sources']:
                    self.assertEqual((out/row['path']).read_bytes(),(FROZEN/arm/row['path']).read_bytes())

if __name__=='__main__':unittest.main()
