#!/usr/bin/env python3
"""Export separately qualified SLH ASIC boot sources; invokes no EDA tool."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import tempfile
import sys
import export_slh_verified as fpga
import slh_asic_startup as startup
import slh_asic_control as control
import slh_asic_widths as widths
import slh_asic_diagnostics as diagnostics
import audit_slh_asic_netlist as netlist_audit

ROOT = fpga.ROOT
VARIANTS = {'asic-boot-baseline':'corrected-baseline', 'asic-boot-candidate':'corrected-candidate'}
RECORDS = {(v,p):'slh-asic-boot-'+v.removeprefix('asic-boot-')+'-'+p+'-2026-10-12.json'
           for v in VARIANTS for p in ('128f','192f')}


def validate_address_reports(case, parameter):
    expected={'tile0_small','tile0_big','W_MEM'}
    if parameter=='192f':expected|={'tile1_small','tile1_big'}
    pattern=re.compile(r'SLH_ASIC_ADDRESS_REPORT (\w+) writes=(\d+) consumed=(\d+) invalid_unconsumed=(\d+) dual_write_collisions=0 unknown_consume=0 consumed_invalid=0')
    lines=case.get('consumed_address_reports',[])
    if len(lines)!=len(expected):raise ValueError('incomplete consumed-address report set')
    names=set()
    for line in lines:
        match=pattern.fullmatch(line)
        if match is None or match[1] in names or int(match[3])<=0:
            raise ValueError('malformed, duplicated or inactive consumed-address monitor')
        names.add(match[1])
    if names!=expected:raise ValueError('wrong consumed-address monitor names')


def validate_asic_qualification(report, *, parameter, original_hashes, staged_hashes, inputs):
    fpga.validate_qualification(report,parameter=parameter,original_hashes=original_hashes,
        staged_hashes=staged_hashes,inputs=inputs,expected_evidence_kind='asic_boot_vendor_rtl_differential')
    if not (report.get('asic_startup') is True
            and report.get('asic_control_ff') is True
            and report.get('asic_explicit_widths') is True
            and report.get('address_monitor_sha256') == fpga.sha(Path(diagnostics.__file__))
            and report.get('width_transform_sha256') == fpga.sha(Path(widths.__file__))
            and report.get('startup_inputs_unchanged') is True
            and report.get('control_transform_sha256') == fpga.sha(Path(control.__file__))
            and report.get('startup_transform_sha256') == fpga.sha(Path(startup.__file__))
            and report.get('startup_template_sha256') == {p.name:fpga.sha(p) for p in sorted(startup.TEMPLATES.glob('*.v'))}
            and all(c.get('boot_ready_observed') is True and c.get('consumed_address_contract') is True for c in report['cases'])):
        raise ValueError('ASIC report does not match the explicit startup transform/templates and boot witness')
    for case in report['cases']:validate_address_reports(case,parameter)


def validate_focused_reports(component, control_report):
    expected_sources={'tools/check_slh_asic_components.py','tools/slh_asic_startup.py','tools/slh_asic_control.py','tools/slh_asic_widths.py',
        *('asic/rtl/slh_startup/'+n+'.v' for n in ('mem_dual','mem_single','fifo')),
        *('verification/slh_asic_startup/'+n+'.sv' for n in ('tb_memories','tb_control','tb_startup'))}
    if component.get('status')!='PASS' or component.get('inputs_unchanged') is not True or set(component.get('source_sha256',{}))!=expected_sources:
        raise ValueError('focused component evidence is incomplete')
    pair={(v,p) for v in ('corrected-baseline','corrected-candidate') for p in ('128f','192f')}
    rows=component.get('staged_qualification',[])
    if len(rows)!=4 or {(r.get('variant'),r.get('parameter_set')) for r in rows}!=pair or any(r.get('staged_sources_unchanged') is not True for r in rows):
        raise ValueError('focused startup source inventory is incomplete or duplicated')
    keys={(v,p,'whole_top_boot_restart_and_normal_reset') for v,p in pair}|{(None,None,n) for n in ('postboot_memory_fifo_equivalence','nonpower_valid_invalid_unknown_addresses','mem_dual_file_rejection','mem_single_file_rejection')}
    tests=component.get('tests',[])
    if len(tests)!=8 or {(r.get('variant'),r.get('parameter_set'),r.get('test')) for r in tests}!=keys or any(r.get('status')!='PASS' for r in tests):
        raise ValueError('focused component case inventory is incomplete or contains failure')
    for case in tests:
        if case['test'] in ('postboot_memory_fifo_equivalence','nonpower_valid_invalid_unknown_addresses') and 'SLH_ASIC_MEMORIES_PASS cycles=2000' not in case.get('output',''):
            raise ValueError('focused memory scoreboard did not complete2000 cycles')
    mappings={('mem_dual','-set WIDTH 8 -set DEPTH 7 -set INIT 1'):84,('mem_single','-set WIDTH 8 -set DEPTH 8 -set INIT 1'):76,('fifo','-set BW 8 -set LGFLEN 3'):72,
        ('mem_dual','-set WIDTH 64 -set DEPTH 80 -set INIT 1'):5320,('mem_dual','-set WIDTH 64 -set DEPTH 171 -set INIT 1'):11145,
        ('mem_dual','-set WIDTH 4 -set DEPTH 36 -set INIT 0'):156,('mem_dual','-set WIDTH 4 -set DEPTH 52 -set INIT 0'):220}
    rows=component.get('generic_mapping',[])
    if len(rows)!=7 or {(r.get('top'),r.get('parameters')) for r in rows}!=set(mappings):raise ValueError('focused FF mapping inventory is incomplete')
    for r in rows:
        if r.get('status')!='PASS' or type(r.get('ff_bits')) is not int or r['ff_bits']!=mappings[(r['top'],r['parameters'])] or any(type(r.get(k)) is not int or r[k]!=0 for k in ('remaining_memories','remaining_latches','power_up_init_attributes')):
            raise ValueError('focused FF mapping failed or changed expected storage')
    if set(component.get('reference_source_sha256',{}))!={'agent/slh_dsa/pristine/imports/'+n for n in ('mem_dual.v','mem_single.v','fifo.v','global_include/clog2.v')}:
        raise ValueError('focused memory reference source inventory is incomplete')
    if set(control_report.get('test_inputs_sha256',{}))!={'tools/check_slh_asic_control.py','verification/slh_asic_startup/tb_control.sv'}:
        raise ValueError('focused control input inventory is incomplete')
    cases=control_report.get('cases',[])
    if control_report.get('status')!='PASS' or len(cases)!=2 or {r.get('CH_len') for r in cases}!={2,4} or any(r.get('status')!='PASS' or type(r.get('checks')) is not int or r['checks']!=12294 for r in cases):
        raise ValueError('focused decoder cycle-equivalence coverage is incomplete')


def validate_structure(report, variant, parameter, original, staged):
    zero_keys=('remaining_memories','remaining_latches','power_up_init_attributes','undriven_or_conflicting_drivers')
    if not (report.get('status')=='PASS' and report.get('variant')==VARIANTS[variant]
            and report.get('parameter_set')=='SHA2-'+parameter
            and report.get('runner_sha256')==fpga.sha(ROOT/'tools/check_slh_asic_structure.py')
            and report.get('source_sha256')==original
            and report.get('design_source_sha256')=={n:h for n,h in staged.items() if n!='sphincslet/tb.v'}
            and report.get('staged_sources_unchanged') is True and report.get('original_sources_unchanged') is True
            and all(type(report.get(k)) is int and report[k]==0 for k in zero_keys)
            and type(report.get('ff_bits')) is int and report['ff_bits']>0
            and report.get('netlist_sha256') and report.get('mapping_script_sha256')):
        raise ValueError('whole-top FF structural evidence is missing, stale, failed or mismatched')


def export_sources(variant, parameter, out):
    if (variant,parameter) not in RECORDS:
        raise ValueError('ASIC boot export supports explicit baseline/candidate SHA2-128f/192f only')
    out=Path(out).resolve()
    if any(out==r or out.is_relative_to(r) or r.is_relative_to(out) for r in fpga.VARIANTS.values()):
        raise ValueError('export overlaps a protected original tree')
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError('export destination must be absent or empty')
    out.parent.mkdir(parents=True,exist_ok=True)
    record=ROOT/'docs/verification'/RECORDS[(variant,parameter)]
    report_bytes=record.read_bytes(); report=json.loads(report_bytes)
    partner_variant='asic-boot-candidate' if variant=='asic-boot-baseline' else 'asic-boot-baseline'
    partner_record=ROOT/'docs/verification'/RECORDS[(partner_variant,parameter)]
    partner_bytes=partner_record.read_bytes(); partner=json.loads(partner_bytes)
    functional_audit_records={v:ROOT/'docs/verification'/('slh-asic-functional-audit-'+v.removeprefix('asic-boot-')+'-'+parameter+'-2026-10-12.json') for v in (variant,partner_variant)}
    functional_audit_bytes={v:p.read_bytes() for v,p in functional_audit_records.items()}
    functional_audits={v:json.loads(b) for v,b in functional_audit_bytes.items()}
    for v,expected_report in ((variant,report_bytes),(partner_variant,partner_bytes)):
        audit=functional_audits[v]
        expected_files={'compile.log','compile-command.json','baseline.log','signature-memory-bitflip.log','baseline-command.json','signature-memory-bitflip-command.json','baseline-produced.hex','signature-memory-bitflip-produced.hex'}
        files=audit.get('portable_files_sha256',{})
        if not (audit.get('status')=='PASS' and audit.get('functional_report_sha256')==hashlib.sha256(expected_report).hexdigest()
                and audit.get('auditor_sha256')==fpga.sha(ROOT/'tools/audit_slh_asic_functional.py')
                and audit.get('checker_sha256')==fpga.sha(ROOT/'tools/check_slh_portable.py')
                and len(files)==8 and {Path(n).name for n in files}==expected_files
                and len(audit.get('cases',[]))==2 and {c.get('case') for c in audit['cases']}=={'baseline','signature-memory-bitflip'}
                and all(c.get('status')=='PASS' for c in audit['cases'])):
            raise ValueError('raw functional artifact audit is missing, failed or mismatched')
        if any(fpga.sha(ROOT/name)!=h for name,h in files.items()):raise ValueError('portable functional evidence file changed')
    structure_records={v:ROOT/'docs/verification'/('slh-asic-structure-'+v.removeprefix('asic-boot-')+'-'+parameter+'-2026-10-12.json') for v in (variant,partner_variant)}
    structure_bytes={v:p.read_bytes() for v,p in structure_records.items()}
    structures={v:json.loads(b) for v,b in structure_bytes.items()}
    audit_records={v:ROOT/'docs/verification'/('slh-asic-netlist-audit-'+v.removeprefix('asic-boot-')+'-'+parameter+'-2026-10-12.json') for v in (variant,partner_variant)}
    audit_bytes={v:p.read_bytes() for v,p in audit_records.items()}
    for v,b in audit_bytes.items():
        audit=json.loads(b)
        artifacts=audit.get('portable_artifacts_sha256',{})
        if len(artifacts)!=2 or {Path(n).name for n in artifacts}!={'mapping.ys','mapping.log'}:
            raise ValueError('mapping script/log evidence is incomplete')
        for name,h in artifacts.items():
            if fpga.sha(ROOT/name)!=h or h!=structures[v]['mapping_script_sha256' if Path(name).name=='mapping.ys' else 'mapping_log_sha256']:
                raise ValueError('mapping script/log evidence changed')
        if not (audit.get('status')=='PASS' and audit.get('structural_report_sha256')==hashlib.sha256(structure_bytes[v]).hexdigest()
                and audit.get('netlist_sha256')==structures[v]['netlist_sha256']
                and audit.get('auditor_sha256')==fpga.sha(Path(netlist_audit.__file__))
                and all(type(audit.get(k)) is int and audit[k]==0 for k in ('blackbox_or_whitebox_modules','tri_state_cells','unmapped_cells','remaining_memories','remaining_latches','power_up_init_attributes'))):
            raise ValueError('whole-netlist audit is missing, failed or mismatched')
    focused_paths={n:ROOT/'docs/verification'/('slh-asic-'+n+'-2026-10-12.json') for n in ('components','control')}
    focused_bytes={n:p.read_bytes() for n,p in focused_paths.items()}
    focused={n:json.loads(b) for n,b in focused_bytes.items()}
    validate_focused_reports(focused['components'],focused['control'])
    if any(fpga.sha(ROOT/name)!=h for name,h in focused['components']['source_sha256'].items()):
        raise ValueError('focused component source evidence is stale')
    if any(fpga.sha(ROOT/name)!=h for name,h in focused['components']['reference_source_sha256'].items()):
        raise ValueError('focused memory reference evidence is stale')
    if focused['control'].get('transform_sha256')!=fpga.sha(Path(control.__file__)) or any(fpga.sha(ROOT/name)!=h for name,h in focused['control']['test_inputs_sha256'].items()):
        raise ValueError('focused control evidence is stale')
    with tempfile.TemporaryDirectory(prefix='.slh-asic-export-',dir=out.parent) as t:
        work=Path(t)/'bundle'
        predecessor=fpga.export_sources(VARIANTS[variant],parameter,work)
        source=fpga.VARIANTS[VARIANTS[variant]]
        changes=startup.boot_variant(work/'rtl') + control.control_variant(work/'rtl') + widths.width_variant(work/'rtl') + diagnostics.diagnostics_variant(work/'rtl',parameter)
        staged=fpga.portable.rtl_hashes(work/'rtl')
        inputs={Path(p).name:h for p,h in fpga.portable.gate.check_harness(source,parameter,source/'imports').items()}
        validate_asic_qualification(report,parameter=parameter,original_hashes=predecessor['original_source_sha256'],
                                    staged_hashes=staged,inputs=inputs)
        other=Path(t)/'partner-rtl'
        partner_original,_=fpga.prepare_sources(fpga.VARIANTS[VARIANTS[partner_variant]],other,parameter)
        startup.boot_variant(other); control.control_variant(other); widths.width_variant(other); diagnostics.diagnostics_variant(other,parameter); partner_staged=fpga.portable.rtl_hashes(other)
        validate_asic_qualification(partner,parameter=parameter,original_hashes=partner_original,
                                    staged_hashes=partner_staged,inputs=inputs)
        for v,expected in ((variant,staged),(partner_variant,partner_staged)):
            matched=[r for r in focused['components']['staged_qualification'] if r.get('variant')==VARIANTS[v] and r.get('parameter_set')==parameter]
            if len(matched)!=1 or {n:h for n,h in matched[0]['staged_source_sha256'].items() if n!='sphincslet/tb.v'}!={n:h for n,h in expected.items() if n!='sphincslet/tb.v'}:
                raise ValueError('focused whole-top startup evidence does not match the derivative')
        validate_structure(structures[variant],variant,parameter,predecessor['original_source_sha256'],staged)
        validate_structure(structures[partner_variant],partner_variant,parameter,partner_original,partner_staged)
        differences=sorted(n for n in set(staged)|set(partner_staged) if staged.get(n)!=partner_staged.get(n))
        if set(differences)!=fpga.CORE_DIFFERENCES:
            raise ValueError('ASIC pair differs beyond the reviewed SHA cores')
        evidence=work/'evidence'
        (evidence/'qualification.json').rename(evidence/'predecessor_qualification.json')
        (evidence/'partner_qualification.json').rename(evidence/'predecessor_partner_qualification.json')
        if (evidence/'qualification.log.txt').exists():
            (evidence/'qualification.log.txt').rename(evidence/'predecessor_qualification.log.txt')
        (evidence/'qualification.json').write_bytes(report_bytes)
        (evidence/'partner_qualification.json').write_bytes(partner_bytes)
        (evidence/'functional_audit.json').write_bytes(functional_audit_bytes[variant])
        (evidence/'partner_functional_audit.json').write_bytes(functional_audit_bytes[partner_variant])
        for name,wanted in functional_audits[variant]['portable_files_sha256'].items():
            target=evidence/'functional_logs'/Path(name).name;target.parent.mkdir(exist_ok=True)
            shutil.copyfile(ROOT/name,target)
            if fpga.sha(target)!=wanted:raise ValueError('functional artifact changed while exporting')
        for v in (variant,partner_variant):
            prefix='' if v==variant else 'partner_'
            for name,wanted in json.loads(audit_bytes[v])['portable_artifacts_sha256'].items():
                target=evidence/(prefix+'mapping')/Path(name).name;target.parent.mkdir(exist_ok=True)
                shutil.copyfile(ROOT/name,target)
                if fpga.sha(target)!=wanted:raise ValueError('mapping artifact changed while exporting')
        for name,wanted in functional_audits[partner_variant]['portable_files_sha256'].items():
            target=evidence/'partner_functional_logs'/Path(name).name;target.parent.mkdir(exist_ok=True)
            shutil.copyfile(ROOT/name,target)
            if fpga.sha(target)!=wanted:raise ValueError('partner functional artifact changed while exporting')
        (evidence/'structure.json').write_bytes(structure_bytes[variant])
        (evidence/'partner_structure.json').write_bytes(structure_bytes[partner_variant])
        (evidence/'netlist_audit.json').write_bytes(audit_bytes[variant])
        (evidence/'partner_netlist_audit.json').write_bytes(audit_bytes[partner_variant])
        for name,b in focused_bytes.items():(evidence/('focused_'+name+'.json')).write_bytes(b)
        if record.with_suffix('.txt').exists():
            shutil.copyfile(record.with_suffix('.txt'),evidence/'qualification.log.txt')
        patch=work/'changes.patch';patch.write_text(patch.read_text()+''.join(c['diff'] for c in changes))
        manifest=predecessor
        manifest.update(variant=variant,target='asic',language_standard='Verilog-2005',qualification_status='PASS',memory_implementation='synthesizable RTL mapped to generic FFs; no SRAM compiler',
            qualified_staged_source_sha256=staged,tested_cases=report['cases'])
        manifest['exporter_provenance']={'path':'tools/export_slh_asic_verified.py','sha256':fpga.sha(Path(__file__)),
            'support_sha256':{str(p.relative_to(ROOT)):fpga.sha(p) for p in (Path(fpga.__file__),Path(startup.__file__),Path(control.__file__),Path(widths.__file__),Path(diagnostics.__file__))}}
        manifest['transformations'] += [{k:v for k,v in c.items() if k!='diff'} for c in changes]
        manifest['qualification_report']={'path':'evidence/qualification.json','repository_path':str(record.relative_to(ROOT)),'sha256':fpga.sha(record)}
        manifest['functional_artifact_audit']={'path':'evidence/functional_audit.json','repository_path':str(functional_audit_records[variant].relative_to(ROOT)),'sha256':fpga.sha(functional_audit_records[variant])}
        manifest['focused_evidence']=[{'path':'evidence/focused_'+n+'.json','repository_path':str(p.relative_to(ROOT)),'sha256':fpga.sha(p)} for n,p in focused_paths.items()]
        manifest['netlist_audit']={'path':'evidence/netlist_audit.json','repository_path':str(audit_records[variant].relative_to(ROOT)),'sha256':fpga.sha(audit_records[variant])}
        manifest['structural_report']={'path':'evidence/structure.json','repository_path':str(structure_records[variant].relative_to(ROOT)),'sha256':fpga.sha(structure_records[variant]),'scope':'whole-top generic FF/logic lowering, no standard-cell or PPA claim'}
        manifest['predecessor_qualification_report']={'path':'evidence/predecessor_qualification.json','sha256':fpga.sha(evidence/'predecessor_qualification.json'), 'scope':'corrected portable predecessor; does not itself qualify ASIC derivative'}
        manifest['generic_ff_lowering']={'reader':'read_verilog -defer (Verilog-2005, selected source ordering/includes)',
            'passes':['hierarchy -check -top top','proc','opt','memory -nomap','memory_map','opt','techmap','opt','check -assert'],
            'reason':'ordinary memory optimization coalesces static read ports before FF lowering; no setundef, technology library or SRAM compiler',
            'recorded_script':'evidence/mapping/mapping.ys','recorded_log':'evidence/mapping/mapping.log',
            'scope':'generic structural check only, not standard-cell mapping or PPA; recorded script retains original staged paths'}
        manifest['startup_contract']={
            'reset':'i_boot_reset, active-high synchronous; assert across at least one rising clk edge after power-up',
            'ready':'o_boot_ready; low during reset/scrub; issue inputs and starts only after high',
            'scrub_cycles_after_deassertion':81 if parameter=='128f' else 172,
            'scrubbed_storage':'all INIT=1 hash-tile memory words, including vendor extra [DEPTH] word',
            'preserved_storage':'INIT=0 top memories and FIFO data arrays are not zeroed',
            'fifo':'boot-only pointer reset; normal rstn does not clear pointers',
            'normal_reset':'rstn remains active-low operation reset; it does not rerun boot or clear storage',
            'boot_restart':'repeat initialization while inactive, then reload runtime inputs; active-operation abort/recovery is not qualified',
            'outputs':'signature-valid and completion held low before ready; other data outputs invalid until normal protocol reads',
            'signature_memory':'external and testbench-only; no production keys or signatures baked into RTL'}
        manifest['runtime_controls'].update(i_boot_reset='active-high synchronous power-up/reboot initialization',o_boot_ready='all hash-memory scrubs complete; input/start acceptance allowed')
        manifest['constants']=[{'source':'rtl/sphincslet/sha/'+name+'.v','kind':'static synthesizable SHA constants, no runtime file initialization'} for name in ('sha256_k_constants','sha512_k_constants','sha512_h_constants')]
        manifest['memories']=[
            {'source':'rtl/imports/mem_dual.v','module':'mem_dual','kind':'generic FF-targeted RTL','depth_semantics':'DEPTH+1 words; unchanged','initialization':'INIT=1 explicit serial scrub; INIT=0 none; nonempty FILE fails elaboration','timing':'unchanged postboot registered reads, local write-first and other-port read-old; no portable same-address dual-write priority','invalid_addresses':'read-only full-address-space wire view uses explicit X for nonexistent words; simulation X is synthesis dont-care, not physical X; valid storage is never zero-filled'},
            {'source':'rtl/imports/mem_single.v','module':'mem_single','kind':'uninstantiated generic RTL compatibility module','initialization':'explicit boot scrub if INIT=1; nonempty FILE fails elaboration','timing':'read-first preserved'},
            {'source':'rtl/imports/fifo.v','module':'fifo','kind':'generic FF RTL FIFO','initialization':'explicit boot pointer reset; data array overwritten before successful read'},
            {'source':'rtl/sphincslet/tb.v','instance':'SIG_MEM','kind':'testbench-only external signature store; excluded from design source list'}]
        manifest['memory_instances']=[
            {'instance':'top.H_MSG_MEM','width':64,'declared_words':513,'address_bits':9,'boot_scrub':False},
            {'instance':'top.INDICES_MEM','width':12 if parameter=='128f' else 14,'declared_words':65,'address_bits':6,'boot_scrub':False},
            {'instance':'top.W_MEM','width':4,'declared_words':37 if parameter=='128f' else 53,'address_bits':6,'boot_scrub':False},
            {'instance':'top.MEM_64BIT_1','width':64,'declared_words':513,'address_bits':9,'boot_scrub':False},
            {'instances':'hash_tile SMALL_MEM/BIG_MEM','count':2 if parameter=='128f' else 4,'width':64,'declared_words':81 if parameter=='128f' else 172,'boot_scrub':True},
            {'instances':'hash_tile S_FIFO_INSTANCE/B_FIFO_INSTANCE','count':2 if parameter=='128f' else 4,'width':64,'words':8,'boot_scrub':False,'boot_pointer_reset':True}]
        for key in ('sources','simulation_sources'):
            for entry in manifest[key]:entry['sha256']=fpga.sha(work/entry['path'])
        manifest['source_relationship'].update(comparison_group='asic-boot-SHA2-'+parameter,partner_variant=partner_variant,
            partner_qualified=True,partner_qualification_report=str(partner_record.relative_to(ROOT)),partner_qualification_sha256=fpga.sha(partner_record),
            only_same_parameter_differences=differences)
        manifest['limits']=[
            'Whole functional evidence is historical vendor differential, not independent FIPS 205/ACVP or certification.',
            'No standard-cell mapping, place/route, timing, area, power or PPA result is implied.',
            'Generic RTL requires memory_map (or equivalent FF lowering); no SRAM macro or memory compiler is supplied.',
            'ASIC-only clocked-history/bypass control derivative preserves settled-cycle behavior under the original synchronous source contract; arbitrary asynchronous equivalence is not claimed.',
            'Non-power-of-two out-of-range reads and same-address dual writes retain the vendor undefined contract.',
            'Only corrected SHA2-128f and SHA2-192f are qualified; SHAKE and other modes are not covered.',
            'Use identical external signature storage, clock/reset, constraints and memory lowering within a same-parameter pair.',
            'Source-specific notices are retained; repository LICENSE/NOTICE do not replace component licenses.']
        (work/'README.txt').write_text('SLH ASIC boot source handoff\n\nVariant: '+variant+'; SHA2-'+parameter+'\n'
            'New top ports: i_boot_reset and o_boot_ready. Assert boot reset across a clock edge at power-up, deassert it, then wait for ready before loading input or starting work.\n'
            'Boot scrub lasts '+str(manifest['startup_contract']['scrub_cycles_after_deassertion'])+' clocks after deassertion. Normal rstn never repeats scrub.\n'
            'Memories are generic synthesizable RTL for FF lowering; no SRAM compiler. Supply the external signature memory separately and equivalently in both arms.\n'
            'The exact derivative passed corrected historical full-signature, positive-verification and live-corruption controls in both arms. This is not independent FIPS 205 certification or a PPA result.\n'
            'sources.f excludes testbench; simulation_sources.f includes it. Verify SHA256SUMS. See manifest.json for scope and startup semantics.\n')
        (work/'manifest.json').unlink();(work/'SHA256SUMS').unlink()
        manifest['bundle_files_sha256']={str(p.relative_to(work)):fpga.sha(p) for p in sorted(work.rglob('*')) if p.is_file()}
        fpga.write_json(work/'manifest.json',manifest)
        checksums={str(p.relative_to(work)):fpga.sha(p) for p in sorted(work.rglob('*')) if p.is_file()}
        (work/'SHA256SUMS').write_text(''.join(h+'  '+name+'\n' for name,h in checksums.items()))
        if any(functional_audit_records[v].read_bytes()!=b for v,b in functional_audit_bytes.items()) or any(fpga.sha(ROOT/n)!=h for audit in functional_audits.values() for n,h in audit['portable_files_sha256'].items()):
            raise ValueError('functional artifact evidence changed during export')
        if any(audit_records[v].read_bytes()!=b for v,b in audit_bytes.items()) or any(focused_paths[n].read_bytes()!=b for n,b in focused_bytes.items()):
            raise ValueError('additional evidence changed during export')
        if any(structure_records[v].read_bytes()!=b for v,b in structure_bytes.items()):
            raise ValueError('structural report changed during export')
        if record.read_bytes()!=report_bytes or partner_record.read_bytes()!=partner_bytes:
            raise ValueError('qualification report changed during export')
        if fpga.portable.rtl_hashes(source)!=predecessor['original_source_sha256'] or fpga.portable.rtl_hashes(fpga.VARIANTS[VARIANTS[partner_variant]])!=partner_original:
            raise ValueError('original FPGA sources changed during ASIC export')
        if out.exists():out.rmdir()
        work.rename(out)
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--variant',choices=VARIANTS,required=True);p.add_argument('--parameter-set',choices=('128f','192f'),required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    try:m=export_sources(a.variant,a.parameter_set,a.out)
    except (OSError,ValueError,RuntimeError) as e:print('SLH ASIC export ERROR: '+str(e),file=sys.stderr);return 2
    print(json.dumps({'status':'EXPORTED','variant':a.variant,'parameter_set':m['parameter_set'],'manifest':str(a.out/'manifest.json')},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
