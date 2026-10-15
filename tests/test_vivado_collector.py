"""Real Tcl / synthetic object API tests, not licensed Vivado measurements."""
import re
from pathlib import Path
import subprocess
import tempfile
import unittest

from agent import vivado_qualification as qualification
from tools.export_target_profiles import tcl_word


MEMORY_PROPERTY = re.compile(r'^(WRITE_MODE|READ_WIDTH|WRITE_WIDTH|DO[AB]_REG|INIT|SRVAL|RAM_MODE|SIM_COLLISION_CHECK)')
OPTIONAL = ('REF_TYPE', 'PRIMITIVE_SUBGROUP', 'FILE_NAME', 'LINE_NUMBER')


def row(*values):
    return '\t'.join(str(value).encode('utf-8').hex() for value in values) + '\n'


def cell(index, **properties):
    return {'NAME': f'top/gen[{index}]/r{{one}}', 'REF_NAME': 'FDRE',
            'PRIMITIVE_TYPE': 'REGISTER.FLOP.FDRE', **properties}


class CollectorTests(unittest.TestCase):
    def run_collector(self, cells, *, mismatch='', failing=''):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = Path(qualification.__file__).with_suffix('.tcl').read_text()
            helpers = script.split('set pqc_f [open objects.tsv w]', 1)[0]
            setup = ['set fixture [dict create]', 'set cells {}']
            for index, properties in enumerate(cells):
                obj = f'object{index}'
                setup.append('lappend cells ' + tcl_word(obj))
                for property_name, value in properties.items():
                    setup.append('dict set fixture ' + ' '.join(map(tcl_word, (obj, property_name, value))))
            setup += ['set mismatched_property ' + tcl_word(mismatch), 'set failing_property ' + tcl_word(failing)]
            stubs = '''
set list_calls 0
set query_calls 0
set maximum_query_size 0
proc list_property {object} {
    incr ::list_calls
    return [dict keys [dict get $::fixture $object]]
}
proc get_property {property objects} {
    incr ::query_calls
    set count [llength $objects]
    if {$count > $::maximum_query_size} {set ::maximum_query_size $count}
    if {$property eq $::failing_property} {error "SYNTHETIC property read failure: $property"}
    set result {}
    foreach object $objects {
        if {![dict exists $::fixture $object $property]} {error "Queried absent property $property"}
        lappend result [dict get $::fixture $object $property]
    }
    if {$property eq $::mismatched_property} {return [lrange $result 1 end]}
    # Actual UG835 API semantics: singleton returns a scalar, not a Tcl list.
    if {$count == 1} {return [lindex $result 0]}
    return $result
}
rename pqc_progress original_progress
proc pqc_progress {stream message} {
    original_progress $stream $message
    if {[string match {primitive inventory: *} $message]} {
        set reader [open objects.tsv r]
        set text [read $reader]
        close $reader
        set visible 0
        foreach line [split $text "\n"] {
            if {[string match {63656c6c\t*} $line]} {incr visible}
        }
        puts "VISIBLE_CELLS $visible"
    }
}
set stream [open objects.tsv w]
fconfigure $stream -encoding utf-8 -translation lf
set failed [catch {pqc_collect_cells $stream $cells} message]
close $stream
puts "STATS $list_calls $query_calls $maximum_query_size"
if {$failed} {puts stderr $message; exit 1}
'''
            (root / 'collector.tcl').write_text(helpers + '\n'.join(setup) + '\n' + stubs)
            result = subprocess.run(['tclsh', str(root / 'collector.tcl')], cwd=root, text=True,
                                    capture_output=True, timeout=30, check=False)
            return result, (root / 'objects.tsv').read_text()

    def expected(self, cells):
        # Independently express the old producer's row ordering/field semantics.
        result = row('meta', 'primitive_count', len(cells))
        for properties in cells:
            name, ref = properties['NAME'], properties['REF_NAME']
            result += row('cell', name, ref, properties['PRIMITIVE_TYPE'],
                          *(properties.get(p, '') for p in OPTIONAL))
            if re.match(r'^(RAM|ROM|SRL)', ref):
                for property_name, value in properties.items():
                    if MEMORY_PROPERTY.match(property_name):
                        result += row('memory_property', name, property_name, value)
        return result

    def test_heterogeneous_properties_and_generated_names_match_previous_rows(self):
        cells = [cell(0, REF_TYPE='FLOP', PRIMITIVE_SUBGROUP='FLOP', FILE_NAME='/rtl/one.v', LINE_NUMBER='1'),
                 cell(1, FILE_NAME='', LINE_NUMBER=''),
                 cell(2, NAME='top/gen[2]/r{a b}\\雪\nsecond line', REF_TYPE='FLOP'),
                 cell(3)]
        result, output = self.run_collector(cells)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, self.expected(cells))
        self.assertIn('STATS 4 ', result.stdout)
        self.assertIn('primitive inventory complete: 4/4', result.stdout)

    def test_singleton_scalars_preserve_empty_spaces_unicode_and_list_like_values(self):
        for value in ('', '/rtl/path with spaces/雪.v', '{literal} [0] back\\slash', 'a\nb'):
            with self.subTest(value=value):
                cells = [cell(0, NAME='top/with space[0]/{name}', REF_NAME='RAMB36E1',
                              FILE_NAME=value, LINE_NUMBER='', INIT_00=value)]
                result, output = self.run_collector(cells)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output, self.expected(cells))

    def test_singleton_subset_and_batch_tail_keep_scalar_values_exact(self):
        cells = [cell(i) for i in range(257)]
        cells[3]['FILE_NAME'] = '/rtl/path with spaces/a\\b.v'
        cells[-1]['FILE_NAME'] = ''
        result, output = self.run_collector(cells)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, self.expected(cells))
        self.assertIn('VISIBLE_CELLS 256', result.stdout)
        self.assertIn('primitive inventory complete: 257/257', result.stdout)

    def test_every_memory_initialization_and_mode_property_is_preserved(self):
        properties = {'REF_NAME': 'RAMB36E1', 'PRIMITIVE_TYPE': 'BLOCKRAM.BRAM.RAMB36E1',
                      'WRITE_MODE_A': 'READ_FIRST', 'READ_WIDTH_A': '36', 'WRITE_WIDTH_A': '36',
                      'DOA_REG': '1', 'DOB_REG': '0', 'SRVAL_A': "36'h0", 'RAM_MODE': 'TDP',
                      'SIM_COLLISION_CHECK': 'ALL', 'UNRELATED_PROPERTY': 'not part of original audit'}
        properties.update({f'INIT_{i:02X}': f"256'h{i:064x}" for i in range(128)})
        properties.update({f'INITP_{i:02X}': f"256'h{i:064x}" for i in range(16)})
        cells = [cell(0, **properties), cell(1, REF_NAME='SRL16E', INIT="16'h1234"),
                 cell(2, REF_NAME='ROM32X1', INIT="32'h0"), cell(3, REF_NAME='RAM32M', INIT_A='')]
        result, output = self.run_collector(cells)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, self.expected(cells))
        self.assertIn(row('memory_property', cells[0]['NAME'], 'INIT_7F', properties['INIT_7F']), output)
        self.assertIn(row('memory_property', cells[0]['NAME'], 'INITP_0F', properties['INITP_0F']), output)

    def test_queries_are_bounded_and_progress_covers_multiple_batches(self):
        cells = [cell(i, REF_TYPE='FLOP', FILE_NAME='/rtl/one.v', LINE_NUMBER=str(i + 1)) for i in range(600)]
        result, output = self.run_collector(cells)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, self.expected(cells))
        self.assertIn('STATS 600 18 256', result.stdout)
        self.assertIn('VISIBLE_CELLS 256', result.stdout)
        self.assertIn('VISIBLE_CELLS 512', result.stdout)
        for count in (256, 512, 600):
            self.assertIn(f'{count}/600', result.stdout)

    def test_empty_collection_does_not_query_or_claim_qualified_inventory(self):
        result, output = self.run_collector([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, row('meta', 'primitive_count', 0))
        self.assertIn('STATS 0 0 0', result.stdout)
        with self.assertRaisesRegex(ValueError, 'Primitive inventory mismatch'):
            qualification.parse_objects(output + row('meta', 'schema', qualification.SCHEMA) +
                                        row('meta', 'complete', 1))

    def test_mandatory_and_optional_cardinality_mismatch_fail_closed(self):
        for property_name in ('NAME', 'REF_NAME', 'PRIMITIVE_TYPE', 'FILE_NAME', 'INIT_00'):
            with self.subTest(property=property_name):
                cells = [cell(i, REF_NAME='RAMB36E1', FILE_NAME='/rtl/a.v', INIT_00='value') for i in range(2)]
                result, output = self.run_collector(cells, mismatch=property_name)
                self.assertEqual(result.returncode, 1)
                self.assertIn('Property result cardinality mismatch: ' + property_name, result.stderr)
                self.assertNotIn('primitive inventory complete', result.stdout)
                self.assertNotIn(row('meta', 'complete', 1), output)

    def test_property_errors_are_not_replaced_with_empty_evidence(self):
        result, output = self.run_collector([cell(0, FILE_NAME='/rtl/a.v')], failing='FILE_NAME')
        self.assertEqual(result.returncode, 1)
        self.assertIn('SYNTHETIC property read failure: FILE_NAME', result.stderr)
        self.assertNotIn('primitive inventory complete', result.stdout)
        self.assertNotIn(row('meta', 'complete', 1), output)


if __name__ == '__main__':
    unittest.main()
