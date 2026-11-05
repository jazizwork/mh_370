import sys, re, csv
import xml.etree.ElementTree as ET
K='{http://www.opengis.net/kml/2.2}'
D='data/raw/oi2025_search/caption_kml/extracted/'
files={'A7806_P1_2025-02-08_to_03-06':D+'kmz_Armada-78-06-2025-02-08-to-2025-03-06-Phase1/doc.kml',
       'A7806_P2_2025-03-06_to_04-08':D+'ARMADA 78 06 - Phase 2 -2025-03-06-to-2025-04-08-MH370-CAPTION.net.kml',
       'A8605_P3_2025-12-23_to_2026-01-28':D+'ARMADA 86 05 - Phase 3 - 2025-12-30-to-2026-01-23-MH370-CAPTION.net.kml'}
w=csv.writer(open(sys.argv[1],'w')); w.writerow(['leg','time_utc','lat','lon','sog_kts','cog_deg'])
for leg,f in files.items():
    src=open(f,'rb').read(); assert b'<!ENTITY' not in src
    root=ET.fromstring(src); n=0
    for pm in root.iter(K+'Placemark'):
        nm=(pm.find(K+'name').text or '')
        m=re.match(r'(\d{4}-\d\d-\d\d \d\d:\d\d)Z\s+([-\d.]+)kts,\s*([-\d.]+)',nm)
        if not m: continue
        pt=pm.find('.//'+K+'Point/'+K+'coordinates')
        if pt is None: continue
        lon,lat=[float(v) for v in pt.text.strip().split(',')[:2]]
        sog=m.group(2); cog=m.group(3)
        w.writerow([leg,m.group(1).replace(' ','T')+'Z',lat,lon,'' if sog=='-' else sog,'' if cog=='-' else cog]); n+=1
    print(leg,n)
