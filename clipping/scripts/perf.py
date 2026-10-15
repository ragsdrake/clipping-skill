# -*- coding: utf-8 -*-
"""Join what we posted against what it got, and say what to do next.

The whole point: a YouTube Short on this campaign pays $1.75 per 1,000 views and
has a $5.25 minimum. So a Short under 3,000 views pays nothing at all. That is
the bar, not "did it do okay".

Feed it a views dump scraped from Studio (see --help for the one-liner) and it
prints every hook ranked, which ones cleared the bar, and which ones to stop
reusing.

Usage:
  python perf.py                       # read out/posted.json + out/perf.json
  python perf.py --hours 24            # only judge posts at least 24h old
"""
import argparse, datetime as dt, json, os, sys

OUT = os.path.join(os.environ.get('CLIP_HOME', os.getcwd()), 'out')
RATE_PER_1K = 1.75
MIN_PAYOUT = 5.25
BREAK_EVEN = int(MIN_PAYOUT / RATE_PER_1K * 1000)   # 3000 views

SCRAPE_HINT = """
To refresh out/perf.json, open the Shorts list in the persistent browser:

  https://studio.youtube.com/channel/<YOUR_CHANNEL_ID>/videos/short

wait ~3s, then browser_evaluate this and save the result to out/perf.json:

  () => { const ids=[...document.querySelectorAll('a[href*="/video/"]')]
            .map(a=>a.getAttribute('href').split('/')[2])
            .filter((v,i,s)=>s.indexOf(v)===i);
          const rows=document.body.innerText.split('\\n').filter(x=>x.trim());
          return {ids, rows}; }

Then map each id to its views column. Views are the 2nd-to-last number in a row.
"""


def load(name, default):
    p = os.path.join(OUT, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def age_hours(stamp):
    if not stamp:
        return None
    try:
        t = dt.datetime.fromisoformat(stamp)
    except ValueError:
        return None
    now = dt.datetime.now(t.tzinfo) if t.tzinfo else dt.datetime.now()
    return (now - t).total_seconds() / 3600.0


def main():
    ap = argparse.ArgumentParser(epilog=SCRAPE_HINT,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--hours', type=float, default=24.0,
                    help='ignore posts younger than this; they have not settled yet')
    a = ap.parse_args()

    posted = load('posted.json', [])
    views = load('perf.json', {})
    if isinstance(views, dict) and 'views' in views:
        views = views['views']

    if not posted:
        print('posted.json is empty. Nothing has been posted yet.')
        return
    if not views:
        print('No out/perf.json yet, so there are no view counts to judge.')
        print(SCRAPE_HINT)
        return

    rows, waiting = [], []
    for p in posted:
        vid = p.get('video_id')
        v = views.get(vid)
        h = age_hours(p.get('published_at'))
        if v is None:
            continue
        if h is not None and h < 0:
            waiting.append((p.get('title', vid), 'not out yet'))
            continue
        if h is not None and h < a.hours:
            waiting.append((p.get('title', vid), f'{h:.1f}h old'))
            continue
        rows.append({'title': p.get('title', vid), 'id': vid, 'views': int(v),
                     'hours': round(h, 1) if h else None,
                     'paid': round(min(int(v) / 1000 * RATE_PER_1K, 2500), 2)
                     if int(v) >= BREAK_EVEN else 0.0})

    if not rows:
        print(f'Nothing is older than {a.hours:g}h yet. Check back later.')
        for t, h in waiting:
            print(f'  waiting  {h:>12}  {t}')
        return

    rows.sort(key=lambda r: -r['views'])
    best, worst = rows[0], rows[-1]
    cleared = [r for r in rows if r['views'] >= BREAK_EVEN]
    earned = sum(r['paid'] for r in rows)

    print(f'\n{len(rows)} posts judged. Break-even is {BREAK_EVEN:,} views '
          f'(${MIN_PAYOUT:.2f} minimum at ${RATE_PER_1K:.2f}/1k).\n')
    print(f'{"views":>8}  {"paid":>7}  {"age":>6}  hook')
    print('-' * 64)
    for r in rows:
        mark = ' ' if r['views'] >= BREAK_EVEN else 'x'
        print(f'{r["views"]:>8,}  ${r["paid"]:>6.2f}  {str(r["hours"] or "?"):>5}h  {mark} {r["title"]}')

    for t, h in waiting:
        print(f'{"-":>8}  {"-":>7}  {h:>12}    (not judged) {t}')

    print(f'\nEarning: {len(cleared)} of {len(rows)} cleared the bar. '
          f'${earned:.2f} total.')

    print('\nWhat to do next')
    if not cleared:
        print(f'  Nothing cleared {BREAK_EVEN:,} views, so nothing has earned anything.')
        print('  That is a first-second problem, not a title problem. On Shorts the')
        print('  viewer decides before they read anything. Change the opening frame:')
        print('  start on the kill or the explosion, not the walk-up. Re-cut with a')
        print('  tighter window (--len 12) and score only the top-scoring moments.')
    else:
        print(f'  Best: "{best["title"]}" at {best["views"]:,} views. Reuse that hook shape.')
        if worst["views"] < BREAK_EVEN:
            print(f'  Worst: "{worst["title"]}" at {worst["views"]:,}. Retire that hook.')
        if len(rows) < 2:
            print('  One post is not a pattern. Judge the hook after three.')
        elif best['views'] >= 3 * max(worst['views'], 1):
            print('  The spread is wide, so the hook really is doing the work here.')
            print('  Write the next batch as variations of the best one.')
        else:
            print('  The spread is narrow, so the hook is not the lever. The footage')
            print('  is. Pull fresher source footage before cutting more.')

    used = {p.get('title', '') for p in posted}
    print(f'\n  {len(used)} hooks used so far. Never repeat one verbatim.')


if __name__ == '__main__':
    main()
