#!/usr/bin/env python3
"""Bounded, fail-closed conversion of the two pinned ML-DSA source exports.

This is not a general Verilog parser. Unsupported source constructs abort.
Original source files and existing source exports are never modified.
"""
from pathlib import Path
import argparse, hashlib, json, re, shutil, sys


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def mask(s):
    return re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|\(\*(?!\))[\s\S]*?\*\)', lambda m: re.sub(r'[^\n]', ' ', m[0]), s)

REFERENCE_MANIFESTS = {
    'guarded-baseline': 'c754617eebc16623ef75136ad9edd628a61df0459c65843d703a514ab55d3449',
    'corrected-candidate': 'e136e93035cdfe8291c0102085474a014db49b7ba610dddb4c78ba8330542919',
}

TOKEN = re.compile(r'\\\S+|[A-Za-z_$][\w$]*|<=|==|!=|>=|[()\[\]{};,:=]|[^\s]')
class Scan:
    def __init__(self,s):
        self.s=s; self.clean=mask(s); self.t=list(TOKEN.finditer(self.clean))
    def word(self,i): return self.t[i][0]
    def balanced(self,i):
        pair={'(':')','[':']','{':'}'}; close=pair[self.word(i)]; depth=1; i+=1
        while depth:
            if self.word(i)==close: depth-=1
            elif self.word(i) in pair: i=self.balanced(i); continue
            i+=1
        return i
    def stmt(self,i):
        w=self.word(i)
        if w=='begin':
            i+=1
            while self.word(i)!='end': i=self.stmt(i)
            return i+1
        if w in ('if','for','while','repeat'):
            i=self.balanced(i+1); i=self.stmt(i)
            if i<len(self.t) and self.word(i)=='else': i=self.stmt(i+1)
            return i
        if w in ('case','casex','casez'):
            i=self.balanced(i+1); depth=1
            while depth:
                if self.word(i) in ('case','casex','casez'): depth+=1
                elif self.word(i)=='endcase': depth-=1
                i+=1
            return i
        while self.word(i)!=';':
            if self.word(i) in ('(','[','{'): i=self.balanced(i)
            else: i+=1
        return i+1
    def span(self,a,b): return self.t[a].start(), self.t[b-1].end()


def assigns(text):
    """Assigned base names, excluding comparison operators and loop indices."""
    s=re.sub(r'\bfor\s*\([^)]*\)', '', mask(text))
    return set(re.findall(r'\b([A-Za-z_]\w*)\s*(?:\[[^;\n]*?\]\s*)?(?:<=(?!=)|=(?!=))',s))


def rewrite_state(s,name):
    scan=Scan(s); edits=[]; initials=[]; procs=[]; audit=[]
    for i,t in enumerate(scan.t):
        if t[0] not in ('initial','always'): continue
        a=i+1
        if t[0]=='always':
            if scan.word(a)!='@': raise ValueError('unsupported always: '+name)
            a+=1
            if scan.word(a)=='(': a=scan.balanced(a)
            else: a+=1
        b=scan.stmt(a); left,right=scan.span(i,b); body_left,body_right=scan.span(a,b)
        body=s[body_left:body_right]
        if t[0]=='always':
            procs.append({'left':left,'right':right,'body_left':body_left,'body':body,
                          'clocked':bool(re.search(r'\b(?:posedge|negedge)\b',s[left:body_left])),
                          'writes':assigns(body),'reset':[]})
        else:
            if scan.word(a)!='begin': raise ValueError('unsupported initial block: '+name)
            k=a+1
            while scan.word(k)!='end':
                end=scan.stmt(k); x,y=scan.span(k,end)
                initials.append(s[x:y]); k=end
            edits.append((left,right,''))
    # Explicit declaration initializers, all single numeric constants in this pin.
    for m in re.finditer(r'(?<![\\\w])reg\s*(?:\[[^\]\n]+\]\s*)?([^;\n]+)',scan.clean):
        if any(p['left']<=m.start()<p['right'] for p in procs): continue
        for a in re.finditer(r'\b([A-Za-z_]\w*)\s*=\s*([^,;\n)]+)',m[0]):
            reg,value=a[1],a[2].strip()
            if not re.fullmatch(r"[0-9]+(?:'[bhd][0-9a-fA-F]+)?",value): raise ValueError('unsupported initializer '+a[0])
            lo=m.start()+a.start()+a[0].find('='); hi=m.start()+a.end()
            edits.append((lo,hi,'')); initials.append(reg+' = '+value+';')
    # Generated VHDL constants have no procedural writer: convert arrays to nets.
    if name=='keccak_top_ghdl.v':
        constants=[]
        for init in initials:
            if len(assigns(init))!=1: raise ValueError('unexpected constant assignment')
            constants.append('assign '+init)
        names=set().union(*(assigns(i) for i in initials))
        for reg in names:
            if any(reg in p['writes'] for p in procs): raise ValueError('constant has a driver')
            m=re.search(r'\breg(\s+\[[^\]]+\]\s+'+re.escape(reg)+r'\s*\[[^\]]+\]\s*;)',scan.clean)
            if not m: raise ValueError('constant array declaration absent')
            edits.append((m.start(),m.start()+3,'wire'))
        # Each assignment belongs to its enclosing module, so replace the matching
        # initial block in place instead of appending at file scope.
        n=0
        for index,(l,r,repl) in enumerate(edits):
            if scan.clean[l:r].lstrip().startswith('initial'):
                inner=s[l:r]; stmts=re.findall(r'(\w+\[[0-9]+\]\s*=\s*[^;]+;)',mask(inner))
                edits[index]=(l,r,'\n'.join('  assign '+x for x in stmts)); n+=len(stmts)
        if n!=len(initials): raise ValueError('constant assignment coverage mismatch')
        audit=[{'kind':'constant_table','registers':sorted(names),'words':n}]
    else:
        for init in initials:
            targets=assigns(init)
            if not targets: raise ValueError('empty initialization: '+init)
            owners=[p for p in procs if p['writes']&targets]
            if not owners:
                if len(targets)==1 and len(re.findall(r'\b'+re.escape(next(iter(targets)))+r'\b',scan.clean))==1:
                    audit.append({'kind':'unused_initializer_removed','registers':sorted(targets),'original_statement':init})
                    continue
                # Read-only initialized signals in this exact source are static
                # constants, not state. Split their declaration into a wire.
                if name != 'butterfly.v' or targets not in ({'ajlen2_FNTT'}, {'ajlen2_MODM'}):
                    raise ValueError(f'no driver for {name}: {init}')
                reg=next(iter(targets))
                # Process after ordinary edits so declaration-initializer spans
                # remain stable. The net has its original 24-bit width.
                audit.append({'kind':'read_only_constant','registers':[reg],'original_statement':init})
                continue
            if len(owners)!=1: raise ValueError(f'multiple drivers for {name}: {init}')
            p=owners[0]
            if not targets<=p['writes']: raise ValueError('split loop initialization')
            if p['clocked']:
                # Preserve blocking assignment in the pre-existing mixed-blocking
                # FIFO; no other clock block has initialized blocking targets.
                nonblock=bool(re.search(r'\b(?:'+ '|'.join(map(re.escape,targets))+r')\s*(?:\[[^;\n]*?\]\s*)?<=',mask(p['body'])))
                # A whole array's existing assignments may be mixed; Verilator
                # requires the boot writes to use the same operator as fifo[0..3].
                blocking=(name=='ntt_fifo_piso.v' and targets=={'fifo'})
                moved=init if blocking else re.sub(r'(?<![=!<>])=(?!=)', '<=', init)
                # Loop header is elaboration/simulation control and stays blocking.
                moved=re.sub(r'for\s*\(([^)]*)\)',lambda m:'for ('+m[1].replace('<=','=')+')',moved)
                p['reset'].append(moved)
                kind='explicit_boot_reset'
            else: kind='combinational_initializer_removed'
            audit.append({'kind':kind,'registers':sorted(targets),'original_statement':init})
        for p in procs:
            if p['reset']:
                reset='\n'.join('        '+x for x in dict.fromkeys(p['reset']))
                new='begin\n    if (asic_boot_reset) begin\n'+reset+'\n    end else '+p['body']+'\nend'
                edits.append((p['body_left'],p['right'],new))
    for l,r,repl in sorted(edits,reverse=True): s=s[:l]+repl+s[r:]
    for entry in audit:
        if entry['kind']=='read_only_constant':
            reg=entry['registers'][0]
            if reg=='ajlen2_FNTT':
                s,n=re.subn(r',\s*ajlen2_FNTT\s*;', ';\n    wire [23:0] ajlen2_FNTT = 24\'d0;',s)
            else:
                s,n=re.subn(r'(?<![\\\w])reg\s*\[23:0\]\s*ajlen2_MODM\s*;', 'wire [23:0] ajlen2_MODM = 24\'d0;',s)
            if n!=1: raise ValueError('constant declaration shape changed')
    return s,audit,any(p['reset'] for p in procs)


def module_records(files):
    mods={}
    for name,s in files.items():
        sc=Scan(s)
        for i,t in enumerate(sc.t):
            if t[0]!='module': continue
            mod=sc.word(i+1); j=i+2
            if sc.word(j)=='#': j=sc.balanced(j+1)
            if sc.word(j)!='(': raise ValueError('unsupported module header')
            end=sc.balanced(j)
            mods[mod]={'file':name,'port_start':sc.t[j].end(),'port_end':sc.t[end-1].start(),
                       'ansi':bool(re.search(r'\binput\b',s[sc.t[j].end():sc.t[end-1].start()]))}
    return mods


def wire_boot_ports(files,requires):
    mods=module_records(files); calls=[]
    for name,s in files.items():
        sc=Scan(s); current=None
        for i,t in enumerate(sc.t):
            if t[0]=='module': current=sc.word(i+1); continue
            if t[0] not in mods or (i and sc.word(i-1)=='module'): continue
            j=i+1
            if sc.word(j)=='#': j=sc.balanced(j+1)
            if not re.fullmatch(r'[A-Za-z_]\w*',sc.word(j)): continue
            j+=1
            if sc.word(j)!='(': continue
            end=sc.balanced(j); start=sc.t[j].end()
            calls.append((current,t[0],name,start,sc.t[end-1].start()))
    while True:
        expanded=requires|{p for p,c,*_ in calls if c in requires}
        if expanded==requires: break
        requires=expanded
    edits={name:[] for name in files}
    for mod in requires:
        x=mods[mod]
        # Append, preserving all existing positional-port ordering.
        suffix=',\n    '+('input ' if x['ansi'] else '')+'asic_boot_reset'
        edits[x['file']].append((x['port_end'],x['port_end'],suffix))
        if not x['ansi']:
            # Port-list closing ); follows immediately.
            end=files[x['file']].index(';',x['port_end'])+1
            edits[x['file']].append((end,end,'\n    input asic_boot_reset;\n'))
    for p,c,name,start,end in calls:
        if c in requires:
            named=mask(files[name][start:end]).strip().startswith('.')
            edits[name].append((end,end,', '+('.asic_boot_reset(asic_boot_reset)' if named else 'asic_boot_reset')))
    for name in files:
        for l,r,repl in sorted(edits[name],reverse=True): files[name]=files[name][:l]+repl+files[name][r:]
    return sorted(requires)


def build(reference,out,components):
    reference=Path(reference).resolve(); out=Path(out).resolve(); components=Path(components).resolve()
    if out.exists() and any(out.iterdir()): raise ValueError('output must be absent or empty')
    manifest=json.loads((reference/'manifest.json').read_text())
    if sha(reference/'manifest.json') != REFERENCE_MANIFESTS.get(manifest.get('variant')):
        raise ValueError('reference must be an exact pinned verified Verilog export')
    files={}; audit={}; requires=set(); before={}
    for row in manifest['sources']:
        path=reference/row['path']; name=path.name
        if sha(path)!=row['sha256']: raise ValueError('reference hash mismatch: '+name)
        before[name]=row['sha256']
        if name=='dual_port_ram.v': continue
        if name=='dual_port_rom.v':
            files[name]=(components/'dual_port_rom.v').read_text(); continue
        transformed,detail,needs=rewrite_state(path.read_text(),name)
        if name=='gen_c.v':
            # The source supports only sec_lvl=2/3/5. All three already assign
            # both values. Define the otherwise unsupported selector explicitly
            # so synthesis cannot infer hidden state at this combinational mux.
            old='''        default: begin
            W1_LEN = 0;
            TAU    = 0;
            ctilde_out_len = 0;'''
            new=old+'''
            C_SIPO_START = 0;
            ch = 0;'''
            if transformed.count(old)!=1: raise ValueError('gen_c level-default anchor changed')
            transformed=transformed.replace(old,new)
            detail.append({'kind':'unsupported_selector_default','registers':['C_SIPO_START','ch'],
                           'note':'Default zero only for sec_lvl other than 2/3/5; supported assignments unchanged. Removes two inferred latches.'})
        if name=='makehint.v':
            old='    reg [7:0] hint_addr [79:0];'
            view='''
    // Storage remains exactly 80 bytes. Complete the read mux with constants
    // for addresses outside that storage. Supported output paths access 0..79.
    wire [7:0] asic_hint_read [127:0];
    genvar asic_hint_byte;
    generate
        for (asic_hint_byte=0; asic_hint_byte<128; asic_hint_byte=asic_hint_byte+1) begin : asic_hint_read_view
            if (asic_hint_byte < 80)
                assign asic_hint_read[asic_hint_byte] = hint_addr[asic_hint_byte];
            else
                assign asic_hint_read[asic_hint_byte] = 8'b0;
        end
    endgenerate
'''
            if transformed.count(old)!=1 or transformed.count('hint_addr[ctr*8+k]')!=5:
                raise ValueError('makehint read-view anchors changed')
            transformed=transformed.replace(old,old+view).replace('hint_addr[ctr*8+k]','asic_hint_read[ctr*8+k]')
            detail.append({'kind':'inactive_read_mux_definition','registers':['hint_addr'],
                           'storage_words':80,'constant_only_read_view_words':48,
                           'note':'Only dynamic reads changed; all writes and 80-byte storage retained. Supported output-read bounds are 0..79 / 0..54 / 0..74 for levels 2/3/5.'})
        files[name]=transformed
        if detail: audit[name]=detail
        if needs:
            # These pinned stateful sources each contain exactly one module.
            names=re.findall(r'\bmodule\s+(\w+)',mask(transformed))
            if len(names)!=1: raise ValueError('ambiguous boot-port owner')
            requires.add(names[0])
    added=wire_boot_ports(files,requires)
    top=files['combined_top.v']
    top=top.replace('module combined_top #(','module mldsa_asic_core #(')
    top=top.replace('input asic_boot_reset','input asic_boot_reset,\n    input asic_scrub_enable,\n    input [11:0] asic_scrub_address')
    # Exact seven same-clock banks; reject any source change in shape/clocking.
    pat=re.compile(r'dual_port_ram #\(\.WIDTH\(96\), \.LENGTH\((4096|1024)\)\)\s+BRAM_([0-6]) \(clk,clk,')
    def ram(m):
        return f'mldsa_sameclock_ff_ram #(.WIDTH(96), .LENGTH({m[1]}))\n        BRAM_{m[2]} (clk, asic_boot_reset, asic_scrub_enable, asic_scrub_address,'
    top,n=pat.subn(ram,top)
    if n!=7: raise ValueError('expected seven same-clock RAM banks')
    files['combined_top.v']=top
    for name in ('mldsa_sameclock_ff_ram.v','combined_top_asic.v'):
        files[name]=(components/name).read_text()
    out.mkdir(parents=True); (out/'rtl').mkdir()
    for name,s in files.items():
        if re.search(r'\binitial\b',mask(s)): raise ValueError('residual initial in '+name)
        (out/'rtl'/name).write_text(s)
    result={'schema_version':1,'source_variant':manifest['variant'],'top':'combined_top_asic',
            'reference_manifest_sha256':sha(reference/'manifest.json'),'reference_source_hashes':before,
            'sources':[{'path':'rtl/'+n,'sha256':sha(out/'rtl'/n)} for n in sorted(files)],
            'boot_port_modules':added,'startup_audit':audit,
            'contract':{'boot_reset':'synchronous active high; assert across at least one clock edge',
                        'ready_cycles':4096,'normal_rst_clears_memory':False,'same_clock_banks':{'4096x96':1,'1024x96':6}},
            'functional_qualification':False}
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'sources.f').write_text('\n'.join(x['path'] for x in result['sources'])+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--reference',required=True); p.add_argument('--out',required=True); p.add_argument('--components',required=True)
    a=p.parse_args(); print(json.dumps(build(a.reference,a.out,a.components),indent=2))
