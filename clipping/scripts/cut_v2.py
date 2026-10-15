# -*- coding: utf-8 -*-
"""Cut MW4 moments into the layout that is actually winning this campaign.

WHY THIS EXISTS (2026-09-08)
----------------------------
Our first six Shorts got 6 views between them. cut.py was built on the theory
that a clever curiosity hook over a full-bleed 9:16 frame stops the scroll. We
tested that theory against the field and it is wrong for this campaign.

Evidence: 90 Shorts from other clippers running THIS EXACT campaign (found by
searching the mandated caption line, which every one of them must carry).
Median 18.5 views. 19 cleared 1,000. Of those 19 winners:

  * 17-18 are LETTERBOXED, not full-bleed. Text band on top, the untouched 16:9
    gameplay strip in the middle, the MW4 logo big underneath. cut.py went the
    other way on the last pass and that made things worse, not better.
  * Their on-screen text is not clever. It is keyword-loaded and literal:
    "MODERN WARFARE 4 GAMEPLAY IS HERE", "Modern Warfare 4 Multiplayer
    Gameplay", "MW4 Open Beta". Ours said "THIS LOBBY WAS COOKED", which tells
    a viewer nothing and tells YouTube nothing.
  * ALL 19 use the campaign's own ad copy as the video TITLE, plus @CallofDuty.
    Not a hook. The literal sponsor line.
  * Median like rate 1.18%, so those views are real traffic, not bought.

So this script copies the winning shape and drops the clever-hook theory.
Layout, top to bottom: text band -> full-width 16:9 gameplay -> MW4 logo ->
required beta line. Nothing is cropped off the gameplay any more.

Usage: python cut_v2.py --n 1 --batch 2

The MW4 text below is the worked example. For your own campaign, put a
work/campaign.json next to it (see campaign.example.json) and it wins.
"""
import argparse, json, os, subprocess, sys

HOME = os.environ.get('CLIP_HOME', os.getcwd())
WORK = os.path.join(HOME, 'work')
# Heavy sans fonts. Windows paths by default; set CLIP_FONT_HEAVY /
# CLIP_FONT_BOLD on macOS or Linux (any .ttf works).
FONT_HEAVY = os.environ.get('CLIP_FONT_HEAVY', 'C:/Windows/Fonts/ariblk.ttf')
FONT_BOLD = os.environ.get('CLIP_FONT_BOLD', 'C:/Windows/Fonts/arialbd.ttf')
LOGO = os.path.join(WORK, 'logo.png')
LEDGER = os.path.join(WORK, 'source_ledger.json')

# REQUIRED verbatim on screen by the campaign brief. Cannot be removed.
ONSCREEN_REQUIRED = 'MW4 Open Beta  -  This Weekend'

# REQUIRED verbatim in the caption. Do not paraphrase.
REQUIRED_PHRASE = ('Pre-order Modern Warfare 4 today and play day one, '
                   'October 23rd')

# Top banner. Deliberately literal and keyword-heavy -- this is what the 19
# winners do. Line 2 is optional (pass '' for a single-line banner).
BANNERS = [
    ("MODERN WARFARE 4", "MULTIPLAYER GAMEPLAY"),
    ("MODERN WARFARE 4", "GAMEPLAY IS HERE"),
    ("MW4 OPEN BETA", "MULTIPLAYER GAMEPLAY"),
    ("MODERN WARFARE 4", "BETA GAMEPLAY"),
    ("MW4 MULTIPLAYER", "OPEN BETA WEEKEND"),
    ("MODERN WARFARE 4", "OPEN BETA IS LIVE"),
    ("MW4 BETA", "MULTIPLAYER GAMEPLAY"),
    ("MODERN WARFARE 4", "MULTIPLAYER IS BACK"),
    ("CALL OF DUTY MW4", "BETA GAMEPLAY"),
    ("MODERN WARFARE 4", "FIRST GAMEPLAY LOOK"),
]

# Two-line caption burned low in the gameplay strip. Line 2 is red, which is
# the emphasis trick every top clip in the sample used.
CAPTIONS = [
    ("THE NEW MOVEMENT TECH", "IS ACTUALLY INSANE"),
    ("THIS TTK", "LOOKS NASTY"),
    ("THE KILLSTREAKS", "GO HARD"),
    ("THIS BETA", "IS DIFFERENT"),
    ("THE GUNPLAY HERE", "IS UNREAL"),
    ("THIS MAP", "GOES CRAZY"),
    ("THE TIME TO KILL", "IS BRUTAL"),
    ("THIS LOADOUT", "IS CRACKED"),
    ("THE SLIDE CANCEL", "IS BACK"),
    ("THIS BETA WEEKEND", "IS STACKED"),
]

# Every one of the 19 winners titles the video with the sponsor line itself.
TITLE = (REQUIRED_PHRASE + ' @CallofDuty #ad #callofduty')

DESCRIPTION = (
    REQUIRED_PHRASE + "\n\n"
    "#Ad\n\n"
    "@callofduty\n\n"
    "#CallOfDuty #ModernWarfare4 #Shorts"
)

# Your campaign overrides the MW4 example above.
_cfg = os.path.join(WORK, 'campaign.json')
if os.path.exists(_cfg):
    with open(_cfg, encoding='utf-8') as _f:
        _c = json.load(_f)
    ONSCREEN_REQUIRED = _c.get('onscreen_required', '')
    REQUIRED_PHRASE = _c['required_phrase']
    BANNERS = [tuple(b) for b in _c['banners']]
    CAPTIONS = [tuple(c) for c in _c['captions']]
    TITLE = _c.get('title', REQUIRED_PHRASE + ' #ad')
    DESCRIPTION = _c.get('description', REQUIRED_PHRASE + '\n\n#Ad')
    LOGO = os.path.join(WORK, _c.get('logo', 'logo.png'))

# ---- geometry (1080x1920) -------------------------------------------------
W, H = 1080, 1920
STRIP_W, STRIP_H = 1080, 608       # untouched 16:9 gameplay
STRIP_Y = 660                      # centred-ish, above the Shorts UI
BANNER_Y = 330                     # text band sits above the strip
LOGO_W = 460
LOGO_Y = STRIP_Y + STRIP_H + 90


def ff_escape_path(p):
    return p.replace('\\', '/').replace(':', r'\:')


def ff_escape_text(t):
    return (t.replace('\\', r'\\\\')
             .replace("'", r"\'")
             .replace(':', r'\:')
             .replace('%', r'\%'))


def fit_size(text, max_px, cap, ratio=0.62):
    if not text:
        return cap
    return max(24, min(cap, int(max_px / (ratio * len(text)))))


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding='utf-8', errors='ignore')
    if r.returncode != 0:
        print('FFMPEG FAIL:', r.stderr[-1200:], file=sys.stderr)
        return False
    return True


def extract(src, start, dur, out):
    return run([
        'ffmpeg', '-y', '-v', 'error',
        '-ss', '%.2f' % start, '-i', src, '-t', '%.2f' % dur,
        '-vf', 'scale=1920:1080,setsar=1,fps=30',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
        out,
    ])


def style_filter(banner, caption):
    b1, b2 = banner
    c1, c2 = caption
    fh = ff_escape_path(FONT_HEAVY)
    fb = ff_escape_path(FONT_BOLD)

    # Arial Black is wide: ~0.80 of the point size per capital. A smaller
    # ratio here is what pushed the first render off both edges of the frame.
    b1_px = fit_size(b1, 990, 104, ratio=0.80)
    b2_px = fit_size(b2, 990, 104, ratio=0.80)
    b_px = min(b1_px, b2_px)          # same size on both lines, like theirs
    c_px = 52

    def dt(font, text, size, y, colour, border=0, bordercol='black@0.85'):
        return ("drawtext=fontfile='%s':text='%s':fontsize=%d:"
                "x=(w-text_w)/2:y=%d:fontcolor=%s:borderw=%d:bordercolor=%s"
                % (font, ff_escape_text(text), size, y, colour, border,
                   bordercol))

    parts = []
    # black canvas, gameplay strip pasted in untouched at full width
    # No :d= here. A duration on this source makes it the shortest input,
    # and shortest=1 on the overlay below then truncates the VIDEO to that
    # length while the audio keeps its full length. That shipped a 1-second
    # picture with 14 seconds of sound once (2026-09-08).
    # Infinite source + shortest=1 means the gameplay strip sets the length.
    parts.append("color=c=black:s=%dx%d:r=30[bg];" % (W, H))
    parts.append("[0:v]scale=%d:%d:flags=lanczos,setsar=1,"
                 "eq=contrast=1.08:saturation=1.14[strip];"
                 % (STRIP_W, STRIP_H))
    parts.append("[bg][strip]overlay=0:%d:shortest=1[withstrip];" % STRIP_Y)
    # MW4 logo under the strip
    parts.append("[1:v]format=rgba,scale=%d:-1[lg];" % LOGO_W)
    parts.append("[withstrip][lg]overlay=(W-w)/2:%d[wm];" % LOGO_Y)

    chain = []
    # banner, two lines
    chain.append(dt(fh, b1, b_px, BANNER_Y, 'white'))
    if b2:
        chain.append(dt(fh, b2, b_px, BANNER_Y + b_px + 14, 'white'))
    # caption burned into the bottom of the gameplay strip
    cap_y = STRIP_Y + STRIP_H - 150
    chain.append(dt(fh, c1, c_px, cap_y, 'white', 5))
    chain.append(dt(fh, c2, c_px, cap_y + c_px + 8, '#ff2d2d', 5))
    # required beta line under the logo
    if ONSCREEN_REQUIRED:
        req_px = fit_size(ONSCREEN_REQUIRED, 620, 40)
        chain.append(dt(fb, ONSCREEN_REQUIRED, req_px, LOGO_Y + 200,
                        'white@0.95', 3))

    parts.append("[wm]" + ",".join(chain) + "[v]")
    return "".join(parts)


def probe_frames(path):
    """Real decoded video frames. Container duration lies when the picture is
    truncated but the audio is not, so never judge a render by duration."""
    try:
        out = subprocess.check_output(
            ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
             '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', path],
            text=True).strip()
        return int(out.split(',')[0])
    except Exception:
        return -1


def style(seg, out, banner, caption):
    return run([
        'ffmpeg', '-y', '-v', 'error',
        '-i', seg, '-i', LOGO,
        '-filter_complex', style_filter(banner, caption),
        '-map', '[v]', '-map', '0:a',
        '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
        '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.1',
        '-r', '30',
        '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
        '-movflags', '+faststart',
        out,
    ])


def batch_slice(moments, n, batch):
    ranked = sorted(moments, key=lambda m: -m['score'])
    per = n * 2
    total = len(ranked) // per
    if batch < 1:
        sys.exit('--batch starts at 1')
    if batch > total:
        sys.exit('batch %d past the end (%d available)' % (batch, total))
    chunk = ranked[(batch - 1) * per: batch * per]
    payoffs, builds = chunk[:n], chunk[n:]
    return [(builds[i], payoffs[i]) for i in range(n)], total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=1)
    ap.add_argument('--batch', type=int, default=1)
    ap.add_argument('--moments', default=os.path.join(WORK, 'moments.json'))
    ap.add_argument('--src', default=None)
    ap.add_argument('--seglen', type=float, default=7.0)
    ap.add_argument('--out', default=os.path.join(HOME, 'out'))
    ap.add_argument('--prefix', default='mw4_v2')
    ap.add_argument('--offset', type=int, default=0,
                    help='shift banner/caption choice, so separate runs across '
                         'several sources do not repeat text')
    args = ap.parse_args()

    with open(args.moments, encoding='utf-8') as f:
        md = json.load(f)
    moments = md['moments'] if isinstance(md, dict) else md
    src = args.src or (md.get('source') if isinstance(md, dict) else None)
    if not src:
        with open(LEDGER, encoding='utf-8') as f:
            src = json.load(f)['active_source']

    pairs, total = batch_slice(moments, args.n, args.batch)
    os.makedirs(args.out, exist_ok=True)
    tmp = os.path.join(args.out, '_v2tmp')
    os.makedirs(tmp, exist_ok=True)

    made = []
    for i, (build, payoff) in enumerate(pairs):
        # Different strides, so a given banner is not permanently welded to one
        # caption. Ten clips in an evening that all read the same are exactly the
        # templated look YouTube's inauthentic-content policy targets.
        j = args.batch - 1 + i + args.offset
        banner = BANNERS[j % len(BANNERS)]
        caption = CAPTIONS[(j * 3 + 1) % len(CAPTIONS)]
        segs = []
        for k, m in enumerate((build, payoff)):
            s = os.path.join(tmp, 'seg%d_%d.mp4' % (i, k))
            st = max(0.0, float(m['start']))
            if not extract(src, st, args.seglen, s):
                sys.exit('extract failed')
            segs.append(s)
        lst = os.path.join(tmp, 'list%d.txt' % i)
        with open(lst, 'w', encoding='utf-8') as f:
            for s in segs:
                f.write("file '%s'\n" % s.replace('\\', '/'))
        joined = os.path.join(tmp, 'join%d.mp4' % i)
        if not run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
                    '-i', lst, '-c', 'copy', joined]):
            sys.exit('concat failed')
        out = os.path.join(args.out, '%s_clip%02d.mp4' % (args.prefix, i + 1))
        if not style(joined, out, banner, caption):
            sys.exit('style failed')
        # Frame gate. A render that loses its picture still reports the right
        # container duration, because the audio is mapped separately -- that is
        # how a 1-second video shipped on 2026-09-08. Count real frames.
        frames = probe_frames(out)
        want = int(round(args.seglen * 2 * 30))
        if frames < want * 0.9:
            sys.exit('render broken: %s has %d video frames, expected ~%d. '
                     'Do not upload it.' % (out, frames, want))
        made.append({
            'file': out, 'source': src, 'batch': args.batch,
            'banner': list(banner), 'caption': list(caption),
            'frames': frames,
            'onscreen': ONSCREEN_REQUIRED,
            'title': TITLE,
            'description': DESCRIPTION,
            'segments': [[m['start'], m['start'] + args.seglen]
                         for m in (build, payoff)],
            'layout': 'letterbox-v2',
        })
        print('made', out)

    with open(os.path.join(args.out, 'clips_v2.json'), 'w',
              encoding='utf-8') as f:
        json.dump(made, f, indent=1)
    print('batches available on this source:', total)


if __name__ == '__main__':
    main()
