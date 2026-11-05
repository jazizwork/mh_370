import sys, json
import xml.etree.ElementTree as ET
K='{http://www.opengis.net/kml/2.2}'
src=open(sys.argv[1],'rb').read()
assert b'<!ENTITY' not in src
root=ET.fromstring(src)
out=[]
for pm in root.iter(K+'Placemark'):
    nm=pm.find(K+'name'); nm=nm.text if nm is not None else ''
    for g in pm.iter():
        t=g.tag.split('}')[-1]
        if t in ('Point','LineString','LinearRing'):
            c=g.find(K+'coordinates')
            pts=[[float(v) for v in s.split(',')[:2]] for s in c.text.split()]
            out.append({'name':nm,'type':t,'coords':pts})
json.dump(out,open(sys.argv[2],'w'))
for o in out: print(o['name'],o['type'],len(o['coords']), o['coords'][:3] if len(o['coords'])<20 else o['coords'][:2])
