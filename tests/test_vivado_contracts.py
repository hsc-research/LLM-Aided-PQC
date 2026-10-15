"""Execute the entire producer against strict documented API contracts, not EDA."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from agent import vivado_qualification as q
from tools.export_target_profiles import tcl_word

STUB = r'''
set pqc_path_count 1
set props [dict create design [dict create NAME combined_top PART xc7a200tfbg676-1] \
 c1 [dict create NAME {top/gen[0]/r\one} REF_NAME FDRE PRIMITIVE_TYPE REGISTER.FLOP.FDRE] \
 c2 [dict create NAME {top/gen[1]/r two} REF_NAME FDRE PRIMITIVE_TYPE REGISTER.FLOP.FDRE] \
 clk [dict create NAME clk PERIOD 15 IS_GENERATED 0 SOURCE_PINS clk_i] \
 port [dict create NAME valid_o CLASS port DIRECTION OUT] \
 setup [dict create STARTPOINT_PIN a/Q ENDPOINT_PIN b/D SLACK 1.0] \
 hold [dict create STARTPOINT_PIN b/Q ENDPOINT_PIN a/D SLACK 0.1]]
foreach name {MDRV-1 LUTLP-1 INBB-3} {
 dict set props $name [dict create NAME $name CLASS $drc_class IS_ENABLED 1]
}
if {$scenario eq "wrong_name"} {dict set props MDRV-1 NAME valid_o}
if {$scenario eq "wrong_class"} {dict set props MDRV-1 CLASS port}
if {$scenario eq "disabled"} {dict set props MDRV-1 IS_ENABLED 0}
if {$scenario eq "bad_port"} {dict set props port CLASS cell}
proc get_property {property objects} {
 if {$::scenario eq "drc_property_error" && $property eq $::failing_drc_property && [lsearch -exact $objects MDRV-1] >= 0} {error "DRC property read failed: $property"}
 if {$::scenario eq "property_error" && $property eq "SLACK"} {error "Property read failed"}
 set result {}
 foreach object $objects {
  if {![dict exists $::props $object $property]} {error "Unsupported property $property on $object"}
  lappend result [dict get $::props $object $property]
 }
 if {[llength $objects] == 1} {return [lindex $result 0]}
 return $result
}
proc list_property {object} {return [dict keys [dict get $::props $object]]}
proc current_design {} {return design}
proc version {args} {return 2022.2}
proc get_cells {args} {
 if {$args eq {-hierarchical -filter {IS_PRIMITIVE == 1}}} {return {c1 c2}}
 if {[lindex $args 0] eq "-of_objects" && [llength $args] == 2} {
  if {$::scenario eq "path_cells_error"} {error "Path relation failed"}
  switch -- [lindex $args 1] {setup {return {c1 c2}} hold {return {c2}} default {error "Unsupported cell relation"}}
 }
 if {$args eq {-hierarchical -filter {IS_PRIMITIVE == 1 && (PRIMITIVE_SUBGROUP == LATCH || REF_NAME =~ LD*)}} || $args eq {-hierarchical -filter {IS_BLACKBOX == 1}}} {return {}}
 error "Unsupported get_cells arguments"
}
proc get_clocks {args} {
 if {$args eq {}} {return clk}
 if {$args ne {-quiet -of_objects port}} {error "Unexpected clock association query"}
 if {$::scenario eq "foreign_clock"} {return MDRV-1}
 return {}
}
proc get_ports {} {return port}
proc get_timing_paths {args} {
 set allowed 0
 foreach delay {max min} {
  foreach candidate [list [list -delay_type $delay -max_paths 1 -nworst 1] [list -to port -delay_type $delay -max_paths 1 -nworst 1] [list -to port -delay_type $delay -max_paths 1 -nworst 1 -user_ignored]] {
   if {$args eq $candidate} {set allowed 1}
  }
 }
 if {!$allowed} {error "Unexpected timing paths arguments"}
 if {[lsearch -exact $args -user_ignored] >= 0} {return {}}
 if {[lindex $args [expr {[lsearch -exact $args -delay_type]+1}]] eq "max"} {return setup}
 return hold
}
proc get_drc_checks {names} {
 if {$names ne {MDRV-1 LUTLP-1 INBB-3}} {error "Incorrect check lookup"}
 if {$::scenario eq "drc_lookup_error"} {error "DRC check lookup failed"}
 if {$::scenario eq "empty"} {return {}}
 if {$::scenario eq "extra"} {return {MDRV-1 LUTLP-1 INBB-3 INBB-3}}
 if {$::scenario eq "missing"} {return {MDRV-1 LUTLP-1}}
 if {$::scenario eq "duplicate"} {return {MDRV-1 LUTLP-1 LUTLP-1}}
 return $names
}
proc report_drc {args} {
 if {$::scenario eq "drc_report_error"} {error "DRC report failed"}
 if {[llength $args] != 7 || [lrange $args 3 end] ne {-name pqc_structural -file structural_drc.rpt}} {error "Unexpected DRC report arguments"}
 set names [lindex $args [expr {[lsearch -exact $args -checks]+1}]]
 if {[lsort $names] ne [lsort {MDRV-1 LUTLP-1 INBB-3}]} {error "Incorrect report selection"}
 if {[lsearch -exact $args -no_waivers] < 0} {error "Waivers permitted"}
 puts "DRC_REPORT_COMPLETED"
 set ::drc_ran 1
}
proc get_drc_violations {args} {
 if {$args ne {-name pqc_structural}} {error "Unexpected violation lookup"}
 if {$::scenario eq "drc_query_error"} {error "DRC violation query failed"}
 if {$::scenario eq "violation"} {
  dict set ::props violation [dict create NAME MDRV-1#1 SEVERITY Error]
  return violation
 }
 return {}
}
foreach {command expected} {
 check_timing {-verbose -file check_timing.rpt}
 report_clocks {-file clocks.rpt}
 report_exceptions {-coverage -file exceptions.rpt}
 write_xdc {effective.xdc}
 report_timing_summary {-delay_type min_max -report_unconstrained -file timing.rpt}
} {
 proc $command {args} [format {if {![string equal $args %s]} {error "Unexpected report arguments"}} [list $expected]]
}
proc report_timing {args} {
 if {[llength $args] != 3 || [lindex $args 0] ne "-of_objects" || [lindex $args 2] ne "-return_string"} {
  error "Unsupported report_timing combination"
 }
 return "Exact path [lindex $args 1]"
}
'''

class FullCollectorContracts(unittest.TestCase):
    def run_script(self, scenario='ok', drc_class='rule_check', failing_property=''):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = 'set scenario ' + tcl_word(scenario) + '\n'
            script += 'set drc_class ' + tcl_word(drc_class) + '\n'
            script += 'set failing_drc_property ' + tcl_word(failing_property) + '\n' + STUB
            script += '\nsource ' + tcl_word(str(Path(q.__file__).with_suffix('.tcl'))) + '\n'
            (root / 'test.tcl').write_text(script)
            result = subprocess.run(['tclsh', 'test.tcl'], cwd=root, capture_output=True, text=True)
            output = (root / 'objects.tsv').read_text()
            report = (root / 'paths.rpt').read_text() if (root / 'paths.rpt').exists() else ''
            return result, output, report

    def test_full_producer_uses_exact_path_membership(self):
        result, output, report = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = q.parse_objects(output)
        self.assertEqual(rows['path_cell'], [['setup-1', r'top/gen[0]/r\one'],
                         ['setup-1', 'top/gen[1]/r two'], ['hold-1', 'top/gen[1]/r two']])
        self.assertEqual(rows['port'], [['valid_o', 'OUT', '0']])
        self.assertEqual(len(rows['port_timing']), 2)
        self.assertIn('Exact path setup', report)
        self.assertIn('Exact path hold', report)

    def test_documented_drc_classes_reach_report_with_exact_enabled_names(self):
        for drc_class in ('rule_check', 'drc_check'):
            with self.subTest(drc_class=drc_class):
                result, output, _ = self.run_script(drc_class=drc_class)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('DRC_REPORT_COMPLETED', result.stdout)
                self.assertEqual(q.parse_objects(output)['drc_check'],
                                 [[name, '1'] for name in ('MDRV-1', 'LUTLP-1', 'INBB-3')])

    def test_unknown_or_empty_drc_class_stops_before_report(self):
        for drc_class in ('', 'cell', 'port', 'net', 'drc_violation',
                          'rule_check_extra', 'rule_check drc_check', 'RULE_CHECK'):
            with self.subTest(drc_class=drc_class):
                result, output, _ = self.run_script(drc_class=drc_class)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Invalid structural DRC object class:', result.stderr)
                self.assertIn('(expected rule_check or drc_check)', result.stderr)
                self.assertNotIn('DRC_REPORT_COMPLETED', result.stdout)
                with self.assertRaises(ValueError):
                    q.parse_objects(output)

    def test_required_drc_property_errors_stop_before_report(self):
        for property_name in ('CLASS', 'NAME', 'IS_ENABLED'):
            with self.subTest(property_name=property_name):
                result, output, _ = self.run_script('drc_property_error', failing_property=property_name)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('DRC property read failed: ' + property_name, result.stderr)
                self.assertNotIn('DRC_REPORT_COMPLETED', result.stdout)
                with self.assertRaises(ValueError):
                    q.parse_objects(output)

    def test_nonempty_drc_violation_is_preserved_and_blocks_qualification(self):
        from tests.test_vivado_qualification import QualificationTests, encoded
        result, output, _ = self.run_script('violation')
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = q.parse_objects(output)
        self.assertEqual(rows['drc_violation'], [['MDRV-1#1', 'Error']])
        fixture = QualificationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.fixture()
        objects = fixture.run / 'objects.tsv'
        with objects.open('a') as stream:
            for violation in rows['drc_violation']:
                stream.write(encoded('drc_violation', *violation))
        evaluated = q.evaluate(fixture.run, fixture.request)
        self.assertEqual(evaluated['gates']['structural'], 'BLOCKED')
        self.assertEqual(evaluated['structural']['counts']['multiple_driver_violations'], 1)

    def test_invalid_checks_and_port_associations_fail_closed(self):
        for scenario in ('wrong_name', 'wrong_class', 'disabled', 'empty', 'extra', 'missing', 'duplicate', 'drc_lookup_error', 'bad_port', 'foreign_clock', 'property_error', 'path_cells_error', 'drc_report_error', 'drc_query_error'):
            with self.subTest(scenario=scenario):
                result, output, _ = self.run_script(scenario)
                self.assertNotEqual(result.returncode, 0)
                with self.assertRaises(ValueError):
                    q.parse_objects(output)

if __name__ == '__main__':
    unittest.main()
