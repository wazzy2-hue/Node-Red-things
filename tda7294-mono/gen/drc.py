import sys, pcbnew, re, collections
b=pcbnew.LoadBoard(sys.argv[1])
t=next(t for t in b.GetTracks() if t.GetNetname()=='OUT')
print('OUT class:', t.GetNetClassName(), 'clearance', pcbnew.ToMM(t.GetOwnClearance(t.GetLayer())))
pcbnew.WriteDRCReport(b,'/tmp/claude-0/drc.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)
txt=open('/tmp/claude-0/drc.rpt').read()
c=collections.Counter(re.findall(r'^\[(\w+)\]',txt,re.M)); print(dict(c))
blocks=re.split(r'\n(?=\[)',txt)
for bl in blocks:
    m=re.match(r'\[(\w+)\]',bl)
    if m and m.group(1) not in ('silk_overlap','silk_over_copper','lib_footprint_issues','silk_edge_clearance'): print(bl.strip()[:600])
print(re.findall(r'\*\* Found \d+ unconnected pads \*\*',txt))
