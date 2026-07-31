import re, sys, glob
DECL = re.compile(r'^\s*(?:reg|wire|integer)\s*(?:\[[^\]]*\]\s*)?([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*[;,=]')
PORT = re.compile(r'^\s*(?:input|output|inout)\b')
for path in sorted(glob.glob(sys.argv[1])):
    lines = open(path, errors='ignore').read().split('\n')
    ports, decls, incmt = set(), {}, False
    for i, ln in enumerate(lines):
        if '/*' in ln: incmt = True
        if '*/' in ln: incmt = False; continue
        if incmt or ln.strip().startswith('//'): continue
        pm = PORT.match(ln)
        if pm:
            for n in re.findall(r'\b([A-Za-z_]\w*)\s*[,;)]', ln): ports.add(n)
            continue
        m = DECL.match(ln)
        if m and m.group(1) not in decls and m.group(1) not in ports:
            decls[m.group(1)] = i
    hits = []
    for name, dline in decls.items():
        pat = re.compile(r'\b' + re.escape(name) + r'\b')
        for i, ln in enumerate(lines[:dline]):
            s = ln.strip()
            if s.startswith('//') or '/*' in s or PORT.match(ln): continue
            if pat.search(ln):
                hits.append((name, i+1, dline+1)); break
    if hits:
        print(f"{path.split('/')[-1]}: {len(hits)}  " +
              ", ".join(f"{n}(L{u}->L{d})" for n,u,d in sorted(hits, key=lambda x:x[1])[:4]))
