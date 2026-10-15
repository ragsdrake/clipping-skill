# -*- coding: utf-8 -*-
"""Fetch each campaign's page + brief doc; extract per-platform rates and GEO gates.

GEO is the real filter. Most US-brand campaigns require >=50% North America
audience and ask for a screen recording of your analytics as proof. An
account outside those countries cannot meet that, so CPM ranking alone is worthless.

Run: python scan.py [N]
"""
import json, io, re, sys, urllib.request, concurrent.futures as cf

import os as _os
# Everything lives under CLIP_HOME (default: the folder you run from).
HOME = _os.environ.get('CLIP_HOME', _os.getcwd())
WORK = _os.path.join(HOME, 'work')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'}


def get(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers=UA)
        return urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'ignore')
    except Exception:
        return ''


def strip_html(h):
    h = re.sub(r'<script[\s\S]*?</script>', ' ', h)
    h = re.sub(r'<style[\s\S]*?</style>', ' ', h)
    t = re.sub(r'<[^>]+>', '\n', h)
    for a, b in (('&amp;', '&'), ('&#x27;', "'"), ('&quot;', '"'), ('&nbsp;', ' ')):
        t = t.replace(a, b)
    return re.sub(r'\n{2,}', '\n', '\n'.join(s.strip() for s in t.split('\n') if s.strip()))


# The \b matters. Without it "10 % used" (the budget label) matched "% us"
# and flagged every single campaign as blocked.
#
# Briefs are NOT always English. ARZ Urus gates on Spain via "PORCENTAJE DE
# ESPANA" and passed the English-only regex. Any non-English geo term must be
# here or the filter silently lets a blocked campaign through.
BLOCK = re.compile(
    r'(\d{1,3}\s*%\s*(north america|\bus\b|\busa\b|united states|tier\s*1|english[- ]speaking))'
    r'|(minimum\s+\d{1,3}\s*%\s*(north america|\bus\b|tier))'
    r'|(tier\s*3\s+traffic)'
    r'|(\bus\s*/\s*canada\b)'
    r'|(audience requirement)'
    r'|(no tier\s*3)'
    r'|(tier\s*1\s+(only|audience|traffic))'
    r'|(\bus[- ]based audience)'
    r'|(majority\s+(\bus\b|american|north american))'
    # Spanish
    r'|(porcentaje\s+(minimo\s+)?(de\s+)?espa)'
    r'|(audiencia\s+(minima|de\s+espa|hispanohablante))'
    r'|(publico\s+espanol)'
    # German
    r'|(deutschsprachig)|(publikum\s+aus\s+deutschland)|(dach[- ]raum)'
    # French
    r'|(audience\s+francophone)|(public\s+francais)',
    re.I)

# Things that make a campaign unusable for an automated pipeline even when the
# geography is open.
SIGNUP = re.compile(
    r'(must\s+(create|open|sign\s*up|register).{0,40}(card|account|wallet))'
    r'|(debit\s+card)|(affiliate\s+link\s+(in|to)\s+bio)|(referral\s+link\s+required)',
    re.I)
NO_AI = re.compile(r'(no\s+ai\s+content)|(prohibido\s+el\s+uso\s+de\s+ia)|(ai\s+content\s*[:\-]?\s*(not allowed|banned|prohibited))'
                   r'|(hard\s+nos?\s*:?[^\n]{0,40}\bai\b)', re.I)
FILMING = re.compile(r'\b(film|record yourself|on[- ]camera|face\s*cam|selfie|show your face)\b', re.I)

GEO_HINT = re.compile(
    r'(tier\s*[123][^\n]{0,70})'
    r'|(north america[^\n]{0,70})'
    r'|(audience requirement[^\n]{0,90})'
    r'|(US/Canada[^\n]{0,70})',
    re.I)

PLATFORMS = ('YouTube', 'TikTok', 'Instagram', 'X', 'Facebook')


def scan(c):
    m = re.search(r'campaigns/([0-9a-f-]{36})', c.get('href') or '')
    if not m:
        return None
    cid = m.group(1)
    html = get('https://contentrewards.com/discover/' + cid)
    if not html:
        return None
    txt = strip_html(html)

    plat = {}
    for p in PLATFORMS:
        mm = re.search(p + r'\n\$([\d.]+) per 1k views\n\$([\d.]+) min\n\$([\d.]+) max', txt)
        if mm:
            plat[p] = dict(cpm=float(mm.group(1)), min=float(mm.group(2)), max=float(mm.group(3)))

    doc_ids = set(re.findall(r'docs\.google\.com/document/d/([\w-]{20,})', html))
    brief = ''
    for d in list(doc_ids)[:2]:
        brief += get('https://docs.google.com/document/d/%s/export?format=txt' % d)[:9000]

    # Judge the GEO gate ONLY on the brief. Page chrome caused false positives.
    blocked = bool(BLOCK.search(brief)) if brief else None
    hints = [h.group(0).strip() for h in GEO_HINT.finditer(brief)][:4]

    return dict(id=cid, title=c['title'], cpm=c['cpm'], rem=c['rem'],
                creators=c['creators'], per=c['per'], platforms=plat,
                has_brief=bool(brief), geo_blocked=blocked, geo_hints=hints,
                brief=brief[:6000])


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    rows = json.load(io.open(_os.path.join(WORK, 'campaigns.json'), encoding='utf-8'))
    top = [r for r in rows if r['rem'] > 800][:n]

    out = []
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(scan, top):
            if r:
                out.append(r)
    json.dump(out, io.open(_os.path.join(WORK, 'scan.json'), 'w', encoding='utf-8'), indent=1)

    ok = [r for r in out if r['geo_blocked'] is False]
    bad = [r for r in out if r['geo_blocked'] is True]
    unk = [r for r in out if r['geo_blocked'] is None]
    print('scanned %d | briefs %d | GEO-OPEN %d | GEO-BLOCKED %d | no-brief %d'
          % (len(out), sum(1 for r in out if r['has_brief']), len(ok), len(bad), len(unk)))
    print()
    print('%-40s %5s %9s %6s %9s  %s'
          % ('GEO-OPEN (no country gate)', 'CPM', 'REMAIN', 'CRTRS', '$/CRTR', 'PLATFORMS'))
    for r in sorted(ok, key=lambda x: -x['per'])[:14]:
        print('%-40s %5.2f %9s %6d %9s  %s'
              % (r['title'][:40], r['cpm'], format(r['rem'], ',.0f'), r['creators'],
                 format(r['per'], ',.0f'), ','.join(r['platforms'].keys()) or '-'))
    print()
    print('GEO-BLOCKED (needs US / Tier-1 audience):')
    for r in sorted(bad, key=lambda x: -x['per'])[:8]:
        print('  x %-38s %s' % (r['title'][:38], (r['geo_hints'] or ['-'])[0][:70]))
    print()
    print('NO BRIEF FOUND (rules are behind Join, must check by hand):')
    for r in sorted(unk, key=lambda x: -x['per'])[:6]:
        print('  ? %-38s $%s left, %d creators'
              % (r['title'][:38], format(r['rem'], ',.0f'), r['creators']))


if __name__ == '__main__':
    main()
