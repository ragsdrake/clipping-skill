import json,io,re,sys,os
# Everything lives under CLIP_HOME (default: the folder you run from).
HOME = os.environ.get('CLIP_HOME', os.getcwd())
def num(s):
    s=str(s).strip().lstrip('$')
    m=1
    if s and s[-1] in 'kK': m=1000; s=s[:-1]
    elif s and s[-1] in 'mM': m=1000000; s=s[:-1]
    try: return float(s)*m
    except: return 0.0

src = sys.argv[1] if len(sys.argv)>1 else os.path.join(HOME, 'work', 'cr-full.json')
d = json.load(io.open(src, encoding='utf-8'))
rows, seen = [], set()
for c in d['cards']:
    p = c['text'].split('|')
    # pattern: agency, age, title, desc..., paid, /, total, creators, $x/1k, Join Campaign
    try:
        i = p.index('/')
    except ValueError:
        continue
    paid, total, creators = p[i-1], p[i+1], p[i+2]
    cpm = next((x for x in p[i:] if re.match(r'^\$[\d.]+/1k$', x)), None)
    if not cpm: continue
    title = p[2] if len(p) > 2 else p[0]
    if title in seen: continue
    seen.add(title)
    tot, pd, cr = num(total), num(paid), num(creators)
    if cr < 1: cr = 1
    rem = tot - pd
    rows.append(dict(title=title[:46], agency=p[0][:20], age=p[1], cpm=float(cpm[1:-3]),
                     rem=rem, tot=tot, creators=int(cr), per=rem/cr, href=c['href'],
                     desc=' '.join(p[3:i-1])[:400]))
rows.sort(key=lambda r: -r['per'])
json.dump(rows, io.open(os.path.join(HOME, 'work', 'campaigns.json'),'w',encoding='utf-8'), indent=1)
print("%-46s %-14s %5s %9s %6s %9s" % ("CAMPAIGN","AGENCY","CPM","REMAIN","CREATR","$/CREATOR"))
for r in rows[:18]:
    print("%-46s %-14s %5.2f %9s %6d %9s" % (r['title'],r['agency'],r['cpm'],
          format(r['rem'],',.0f'),r['creators'],format(r['per'],',.0f')))
print()
print("parsed %d unique campaigns | total headroom $%s" % (len(rows), format(sum(r['rem'] for r in rows),',.0f')))
