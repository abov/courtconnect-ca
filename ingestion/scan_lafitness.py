"""Scan public LA Fitness club pages (ids 1-1799) for CA/NV clubs and whether they list racquetball.
Usage: .venv/Scripts/python.exe -I ingestion/scan_lafitness.py out.csv  (appends id,name,address,phone,racquetball; ~30 min, throttled)."""
import re,sys,time,csv,urllib.request,html
out=sys.argv[1]
w=csv.writer(open(out,'a',newline='',encoding='utf-8'))
for i in range(1,1800):
    try:
        req=urllib.request.Request(f"https://www.lafitness.com/Pages/clubhome.aspx?clubid={i}",headers={"User-Agent":"Mozilla/5.0 CourtConnect-research"})
        t=urllib.request.urlopen(req,timeout=25).read().decode('utf-8','ignore')
    except Exception as e:
        continue
    m=re.search(r'id="clubInfoAddress"[^>]*>(.*?)</span>',t,re.S)
    if not m: continue
    addr=html.unescape(re.sub(r'<br\s*/?>',', ',m.group(1))).strip()
    if not re.search(r',\s*(CA|NV)\s+\d{5}',addr): 
        time.sleep(0.3); continue
    n=re.search(r'<title>\s*([^<]*?)\s*</title>',t,re.S)
    h=re.search(r'<h1[^>]*>(.*?)</h1>',t,re.S)
    ph=re.search(r'id="clubInfoPhone"[^>]*>([^<]*)',t)
    rb='racquetball' in t.lower().split('amenit')[-1] if False else bool(re.search(r'Racquetball\*?\s*<',t))
    w.writerow([i,re.sub(r'<[^>]+>','',h.group(1)).strip() if h else '',addr,ph.group(1).strip() if ph else '',int(rb)])
    time.sleep(0.4)
