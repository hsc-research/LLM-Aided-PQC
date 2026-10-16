"""Read saved Vivado reports and a checkpoint without admitting or repairing a run.

Runs only open_checkpoint/property queries in Vivado. Original run files are
never written. Any corrected metadata exists only in a disposable diagnostic
copy, whose results cannot be used as a controller response or qualification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from agent import vivado_qualification as q
from agent.run_safety import hashes
from agent.whole_design import digest, require
from tools.export_target_profiles import tcl_word

# Exact agent/vivado_qualification.tcl at PR17 commit 01e137c9252a.
# This historical producer emitted current_design NAME as meta top. Opening its
# saved DCP may assign a new NAME, so container labels cannot be compared across
# sessions. Never apply this interpretation to an unknown/new producer.
LEGACY_NAME_PRODUCER_SHA256 = 'c034c5bbde87842887190e1b38ccee1e9236b1ccff749ca9f19aa3cfea771a5c'

EVALUATED_REPORTS = ('objects.tsv', 'tool-version.txt', 'check_timing.rpt',
                     'timing.rpt', 'utilization.rpt', 'paths.rpt',
                     'synthesis.log', 'effective.xdc')


def checkpoint_identity(checkpoint, executable='vivado', timeout=600):
    """Query loaded checkpoint properties, never a caller-provided top name."""
    with tempfile.TemporaryDirectory(prefix='pqc-checkpoint-identity-') as tmp:
        script = Path(tmp) / 'identity.tcl'
        lines = ['if {[catch {', 'open_checkpoint ' + tcl_word(checkpoint)]
        for key, expression in (('tool_version', '[version -short]'),
                                ('design_name', '[get_property NAME [current_design]]'),
                                ('top', '[get_property TOP [current_design]]'),
                                ('part', '[get_property PART [current_design]]')):
            lines.append('puts "PQC_DIAG_' + key + ' [binary encode hex [encoding convertto utf-8 ' + expression + ']]"')
        lines += ['} message]} {puts stderr $message; exit 1}', 'exit 0']
        script.write_text('\n'.join(lines) + '\n')
        completed = subprocess.run([executable, '-mode', 'batch', '-nojournal', '-nolog',
                                    '-source', str(script)], cwd=tmp, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   timeout=timeout, check=False)
        require(completed.returncode == 0,
                'Checkpoint property probe failed: ' + completed.stdout[-4000:])
        identity = {}
        for line in completed.stdout.splitlines():
            if not line.startswith('PQC_DIAG_'):
                continue
            key, _, encoded = line.partition(' ')
            key = key.removeprefix('PQC_DIAG_')
            require(key in ('tool_version', 'design_name', 'top', 'part') and key not in identity,
                    'Unexpected or duplicate checkpoint identity field')
            identity[key] = bytes.fromhex(encoded).decode('utf-8')
        require(set(identity) == {'tool_version', 'design_name', 'top', 'part'}
                and all(value.strip() for value in identity.values()),
                'Missing checkpoint identity properties')
        return identity


def diagnose(measurement, executable='vivado', timeout=600):
    measurement = Path(measurement).absolute()
    require(not any(path.is_symlink() for path in (measurement, *measurement.parents)),
            'Symlinked measurement directory')
    run = measurement / 'vivado'
    require(not run.is_symlink(), 'Symlinked Vivado report directory')
    paths = [measurement / 'request.json', measurement / 'response.json', *[run / name for name in q.RAW_REPORTS]]
    invalid = [str(path) for path in paths if not path.is_file() or path.is_symlink() or path.stat().st_size == 0]
    require(not invalid, 'Missing, empty or symlinked evidence: ' + ', '.join(invalid))
    before = hashes(paths)
    request = json.loads(q._text(measurement / 'request.json'))
    manifest = json.loads(q._text(run / 'input-manifest.json'))
    cfg = request['configuration']
    response = json.loads(q._text(measurement / 'response.json', 128 * 1024 * 1024))
    require(response['request_sha256'] == before[str(measurement / 'request.json')]
            and response['configuration'] == cfg
            and response['source_hashes'] == request['source_hashes']
            and response.get('executed') is True and response.get('tool_returncode') == 0,
            'Saved response does not bind a successful tool invocation to this request')
    for name in q.RAW_REPORTS:
        saved = response['reports'].get(name, {})
        require(saved.get('path') == 'vivado/' + name
                and saved.get('sha256') == before[str(run / name)],
                'Report differs from original saved response: ' + name)
    require(manifest.get('schema') == q.SCHEMA and manifest['request_sha256'] == before[str(measurement / 'request.json')]
            and manifest['configuration_sha256'] == digest(cfg)
            and manifest['source_hashes'] == request['source_hashes']
            and manifest['immutable_hashes'] == cfg['immutable_hashes']
            and manifest['source_read_order'] == cfg['source_read_order'],
            'Saved request/input manifest disagreement')
    require(hashes(request['source_hashes']) == request['source_hashes'], 'Frozen source bytes changed')
    # Producer files may have been updated since the failed run. Retain the
    # original identity and explicitly disclose that difference; never rebind it.
    producers = manifest['producer_hashes']
    require(isinstance(producers, dict) and set(producers) == set(q.dependencies())
            and set(producers) <= set(cfg['immutable_hashes'])
            and all(value == cfg['immutable_hashes'][path] for path, value in producers.items()),
            'Original producer identity disagrees with frozen configuration')
    immutable = {path: value for path, value in cfg['immutable_hashes'].items() if path not in producers}
    require(hashes(immutable) == immutable, 'Frozen non-producer input bytes changed')
    result = {'status': 'DIAGNOSTIC_ONLY', 'admission_eligible': False,
              'original_run_modified': False, 'measurement': str(measurement),
              'original_producer_hashes': producers,
              'diagnostic_parser_hashes': hashes(q.dependencies()),
              'diagnostic_tool_sha256': hashes([__file__])[str(Path(__file__).resolve())],
              'producer_drift': [path for path, value in hashes(q.dependencies()).items() if producers.get(path) != value],
              'original_evidence_sha256': before, 'checks': {},
              'note': 'No qualification or controller response is produced. Temporary metadata correction is diagnostic only.'}

    def check(name, operation, summary=lambda value: value):
        try:
            value = operation()
            result['checks'][name] = {'status': 'PARSED', 'summary': summary(value)}
            return value
        except (ValueError, RuntimeError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
            result['checks'][name] = {'status': 'BLOCKED', 'error': str(error)}
            return None

    objects = check('object_inventory', lambda: q.parse_objects(q._text(run / 'objects.tsv', 128 * 1024 * 1024)),
                    lambda value: {'meta': value['meta'], 'cells': len(value['cell']), 'paths': len(value['path'])})
    check('check_timing', lambda: q.parse_check_timing(q._text(run / 'check_timing.rpt')))
    check('timing_summary', lambda: q.parse_timing_summary(q._text(run / 'timing.rpt')))
    check('utilization', lambda: q.parse_util(run / 'utilization.rpt'))
    if objects is not None:
        locations = check('source_locations', lambda: q._locations(objects, request['source_hashes']),
                          lambda value: {'direct': sum(row['confidence'] == 'direct_source_property' for row in value.values()),
                                         'unknown': sum(row['confidence'] != 'direct_source_property' for row in value.values())})
        if locations is not None:
            check('critical_paths', lambda: q._paths(objects, q._text(run / 'paths.rpt'), locations,
                                                     cfg['measurement'].get('critical_path_count', 5)),
                  lambda value: {'paths': len(value), 'without_source_ownership': sum(not row['responsible_files'] for row in value)})
        check('io_exceptions', lambda: q._io_exceptions(cfg, {row[0]: row for row in objects['port']}, run),
              lambda value: {'approved_count': len(value[0]), 'unsupported_effective_exceptions': value[1]})
    identity = check('checkpoint_identity', lambda: checkpoint_identity(run / 'synthesized.dcp', executable, timeout))
    if identity is not None and objects is not None:
        def evaluate_copy():
            require(identity['top'] == cfg['top'], 'Checkpoint top differs from frozen configuration')
            require(identity['part'] == cfg['measurement']['part']
                    and identity['tool_version'] == cfg['measurement']['tool_version'],
                    'Checkpoint part/tool version differs from frozen configuration')
            # Reopening a DCP can change NAME (design_1 -> checkpoint_synthesized).
            # Only the exact known NAME-producing script permits interpreting an
            # old mismatch as a container label. The hash-bound checkpoint TOP
            # above remains the independent identity, never the expected string.
            original = objects['meta']['top']
            producer_tcl = str(Path(q.__file__).with_suffix('.tcl').resolve())
            require(original == identity['top'] or
                    producers.get(producer_tcl) == LEGACY_NAME_PRODUCER_SHA256,
                    'Top metadata mismatch is not from the known legacy NAME producer')
            def row(*fields):
                return '\t'.join(value.encode().hex() for value in fields) + '\n'
            old = row('meta', 'top', original)
            new = row('meta', 'top', identity['top'])
            text = q._text(run / 'objects.tsv', 128 * 1024 * 1024)
            require(text.count(old) == 1, 'Expected one exact original top metadata row')
            with tempfile.TemporaryDirectory(prefix='pqc-report-diagnostic-') as tmp:
                temporary = Path(tmp)
                for name in EVALUATED_REPORTS:
                    if name != 'objects.tsv':
                        shutil.copyfile(run / name, temporary / name)
                (temporary / 'objects.tsv').write_text(text.replace(old, new))
                observations = q.evaluate(temporary, request)
                result['diagnostic_metadata_interpretation'] = {'original_top_field': original,
                    'checkpoint_top': identity['top'], 'reopened_design_name': identity['design_name'],
                    'legacy_name_producer': producers.get(producer_tcl) == LEGACY_NAME_PRODUCER_SHA256,
                    'basis': 'Saved checkpoint TOP property; original bytes unchanged'}
                return {'gates': observations['gates'], 'blockers': observations['blockers'],
                        'metrics': observations['metrics'], 'structural_counts': observations['structural']['counts'],
                        'uncovered_port_count': len(observations['constraints']['uncovered_ports'])}
        check('combined_diagnostic_evaluation', evaluate_copy)
    require(hashes(paths) == before and hashes(request['source_hashes']) == request['source_hashes']
            and hashes(immutable) == immutable, 'Evidence changed during diagnosis; discard diagnostic results')
    require(hashes(q.dependencies()) == result['diagnostic_parser_hashes']
            and hashes([__file__])[str(Path(__file__).resolve())] == result['diagnostic_tool_sha256'],
            'Diagnostic implementation changed while reading evidence; discard results')
    result['evidence_unchanged_verified'] = True
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--measurement', required=True, help='Existing 002-measure directory; never written')
    parser.add_argument('--vivado', default='vivado')
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args(argv)
    try:
        require(args.timeout > 0, 'Positive checkpoint timeout required')
        result = diagnose(args.measurement, args.vivado, args.timeout)
    except (ValueError, RuntimeError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'DIAGNOSTIC_BLOCKED', 'admission_eligible': False, 'error': str(error)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
