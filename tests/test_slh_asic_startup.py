"""Contract/unit checks; synthetic report fixtures are never RTL evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import export_slh_verified as ex
import export_slh_asic_verified as asic
import slh_asic_startup as startup
import slh_asic_control as control
import slh_asic_widths as widths
import slh_asic_diagnostics as diagnostics

class StartupTests(unittest.TestCase):
    def stage(self,path,variant='corrected-baseline',parameter='128f'):
        original,_=ex.prepare_sources(ex.VARIANTS[variant],path,parameter)
        changes=startup.boot_variant(path)
        control.control_variant(path)
        widths.width_variant(path)
        diagnostics.diagnostics_variant(path,parameter)
        return original,changes

    def test_fpga_source_preservation_and_explicit_boundary(self):
        root=ex.VARIANTS['corrected-baseline'];before=ex.portable.rtl_hashes(root)
        with tempfile.TemporaryDirectory() as t:
            rtl=Path(t)/'rtl';_,changes=self.stage(rtl)
            self.assertEqual(set(c['path'] for c in changes),set(startup.PINS))
            self.assertIn('i_boot_reset', (rtl/'sphincslet/top.v').read_text())
            self.assertIn('o_boot_ready', (rtl/'sphincslet/top.v').read_text())
            self.assertNotIn('initial', (rtl/'imports/fifo.v').read_text())
            with self.assertRaisesRegex(ValueError,'reviewed corrected bytes'):startup.boot_variant(rtl)
        self.assertEqual(before,ex.portable.rtl_hashes(root))

    def test_asic_pair_only_has_original_sha_differences(self):
        with tempfile.TemporaryDirectory() as t:
            hashes=[]
            for i,v in enumerate(ex.VARIANTS):
                rtl=Path(t)/str(i);self.stage(rtl,v,'192f');hashes.append(ex.portable.rtl_hashes(rtl))
            differences={n for n in hashes[0] if hashes[0][n]!=hashes[1][n]}
            self.assertEqual(differences,ex.CORE_DIFFERENCES)

    def test_stale_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            rtl=Path(t)/'rtl';ex.prepare_sources(ex.VARIANTS['corrected-baseline'],rtl,'128f')
            p=rtl/'imports/mem_dual.v';p.write_text(p.read_text()+'// unexpected\n')
            with self.assertRaisesRegex(ValueError,'reviewed corrected bytes'):startup.boot_variant(rtl)

    def qualification_fixture(self,rtl):
        original,_=self.stage(rtl)
        report=json.loads((ROOT/'docs/verification'/ex.RECORDS[('corrected-baseline','128f')]).read_text())
        # Synthetic contract fixture; does not run RTL and is never saved/exported.
        report.update(evidence_kind='asic_boot_vendor_rtl_differential',asic_startup=True,asic_control_ff=True,asic_explicit_widths=True,address_monitor_sha256=ex.sha(Path(diagnostics.__file__)),width_transform_sha256=ex.sha(Path(widths.__file__)),startup_inputs_unchanged=True,control_transform_sha256=ex.sha(Path(control.__file__)),
            staged_source_sha256=ex.portable.rtl_hashes(rtl),startup_transform_sha256=ex.sha(Path(startup.__file__)),
            startup_template_sha256={p.name:ex.sha(p) for p in sorted(startup.TEMPLATES.glob('*.v'))})
        for c in report['cases']:
            c['boot_ready_observed']=True;c['consumed_address_contract']=True
            c['consumed_address_reports']=['SLH_ASIC_ADDRESS_REPORT '+n+' writes=1 consumed=1 invalid_unconsumed=1 dual_write_collisions=0 unknown_consume=0 consumed_invalid=0' for n in ('tile0_small','tile0_big','W_MEM')]
        kwargs=dict(parameter='128f',original_hashes=original,staged_hashes=ex.portable.rtl_hashes(rtl),inputs=report['input_sha256'])
        return report,kwargs

    def test_asic_qualification_rejects_wrong_or_incomplete_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            r,kwargs=self.qualification_fixture(Path(t)/'rtl');asic.validate_asic_qualification(r,**kwargs)
            for field,bad in [('asic_startup',False),('evidence_kind','portable_vendor_rtl_differential'),
                              ('startup_transform_sha256','stale'),('status','FAIL')]:
                v=copy.deepcopy(r);v[field]=bad
                with self.subTest(field=field),self.assertRaises(ValueError):asic.validate_asic_qualification(v,**kwargs)
            for field in ('boot_ready_observed','negative_control_qualified'):
                v=copy.deepcopy(r);v['cases'][1][field]=False
                with self.subTest(field=field),self.assertRaises(ValueError):asic.validate_asic_qualification(v,**kwargs)
            v=copy.deepcopy(r);v['cases'][0]['consumed_address_reports'][0]=v['cases'][0]['consumed_address_reports'][1]
            with self.assertRaises(ValueError):asic.validate_asic_qualification(v,**kwargs)
            v=copy.deepcopy(r);v['cases']=v['cases'][:1]
            with self.assertRaises(ValueError):asic.validate_asic_qualification(v,**kwargs)

    def test_focused_inventory_rejects_omissions_and_inner_failures(self):
        component=json.loads((ROOT/'docs/verification/slh-asic-components-2026-10-12.json').read_text())
        ctrl=json.loads((ROOT/'docs/verification/slh-asic-control-2026-10-12.json').read_text())
        asic.validate_focused_reports(component,ctrl)
        for field in ('tests','generic_mapping','staged_qualification','reference_source_sha256'):
            altered=copy.deepcopy(component);altered[field]=[]
            with self.subTest(field=field),self.assertRaises(ValueError):asic.validate_focused_reports(altered,ctrl)
        altered=copy.deepcopy(component);altered['tests'][0]['status']='FAIL'
        with self.assertRaises(ValueError):asic.validate_focused_reports(altered,ctrl)
        altered=copy.deepcopy(ctrl);altered['test_inputs_sha256']={}
        with self.assertRaises(ValueError):asic.validate_focused_reports(component,altered)
        altered=copy.deepcopy(ctrl);altered['cases'][0]['checks']=0
        with self.assertRaises(ValueError):asic.validate_focused_reports(component,altered)
        altered=copy.deepcopy(component);altered['generic_mapping'][0]['ff_bits']+=1
        with self.assertRaises(ValueError):asic.validate_focused_reports(altered,ctrl)

    def test_original_export_validator_still_rejects_asic_record(self):
        with tempfile.TemporaryDirectory() as t:
            r,kwargs=self.qualification_fixture(Path(t)/'rtl')
            with self.assertRaises(ValueError):ex.validate_qualification(r,**kwargs)

if __name__=='__main__':unittest.main()
