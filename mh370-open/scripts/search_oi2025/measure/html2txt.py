import sys, re, html
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.out=[]; s.skip=0; s.imgs=[]; s.links=[]
    def handle_starttag(s, t, a):
        a=dict(a)
        if t in ('script','style','noscript'): s.skip+=1
        if t=='img':
            src=a.get('data-orig-file') or a.get('data-src') or a.get('src')
            s.imgs.append((src, a.get('alt',''), a.get('data-image-title',''), a.get('data-large-file','')))
            s.out.append(f"\n[IMG {src} alt={a.get('alt','')!r}]\n")
        if t=='a' and a.get('href'):
            s.links.append(a['href'])
            h=a['href']
            if any(k in h.lower() for k in ('.kml','.kmz','.png','.jpg','.jpeg','.pdf','.csv','.txt','.xlsx','drive.google','dropbox')):
                s.out.append(f"[LINK {h}]")
        if t in ('p','br','div','li','h1','h2','h3','h4','tr','article'): s.out.append("\n")
    def handle_endtag(s,t):
        if t in ('script','style','noscript'): s.skip-=1
    def handle_data(s,d):
        if not s.skip: s.out.append(d)
p=P(); p.feed(open(sys.argv[1],encoding='utf-8',errors='replace').read())
txt=re.sub(r'\n\s*\n+','\n\n',''.join(p.out))
open(sys.argv[2],'w').write(txt)
print(len(txt), 'chars;', len(p.imgs),'imgs')
