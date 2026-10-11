import sys, xml.etree.ElementTree as ET
sys.path.insert(0,'/home/claude/tda7294/gen')
from circuit import nets
t=ET.parse(sys.argv[1]).getroot()
got={}
for n in t.iter('net'):
    nm=n.get('name').lstrip('/')
    nodes=sorted((x.get('ref'),x.get('pin')) for x in n.iter('node'))
    if nm.startswith('unconnected') or nm.startswith('Net-('): 
        if not all(r.startswith('U1') for r,_ in nodes): print('ODD',nm,nodes)
        continue
    got[nm]=nodes
want={k:sorted(v) for k,v in nets().items()}
ok=True
for k in sorted(set(got)|set(want)):
    if got.get(k)!=want.get(k): ok=False; print('MISMATCH',k,'\n got ',got.get(k),'\n want',want.get(k))
print('NETLIST MATCH' if ok else 'FAIL', len(want),'nets')
