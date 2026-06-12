import re, zipfile, tempfile

tmp = tempfile.mkdtemp()
with zipfile.ZipFile('synth_out_baseline_20260520.zip') as z:
    z.extractall(tmp)

def parse_util(path):
    txt = open(path).read()
    out = {}
    for label, key in [(r'Slice LUTs', 'LUT'), (r'Slice Registers', 'FF'),
                       (r'Block RAM Tile', 'BRAM'), (r'DSPs', 'DSP')]:
        m = re.search(rf'\|\s*{label}\*?\s*\|\s*([\d.]+)\s*\|', txt)
        out[key] = float(m.group(1)) if m else None
    return out

print(f"{'Module':<8} {'Metric':<6} {'Baseline':>10} {'Current':>10} {'Delta':>10}")
print("-" * 50)
for mod in ['keygen', 'encap', 'decap']:
    base = parse_util(f'{tmp}/synth_out/{mod}/{mod}_hqc128_util.rpt')
    curr = parse_util(f'synth_out/{mod}/{mod}_hqc128_util.rpt')
    for k in ['LUT', 'FF', 'BRAM', 'DSP']:
        b, c = base[k], curr[k]
        if b is None or c is None:
            print(f"{mod:<8} {k:<6} {'PARSE FAIL':>10}"); continue
        print(f"{mod:<8} {k:<6} {b:>10g} {c:>10g} {c-b:>+10g}")
    print("-" * 50)
