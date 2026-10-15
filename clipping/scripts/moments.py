# -*- coding: utf-8 -*-
"""Find the most action-dense windows in gameplay footage.

Whisper is the wrong tool here. Gameplay has no speech worth transcribing --
what marks a good moment is gunfire, explosions and killstreaks, which show up
as sustained audio energy, plus visual cuts. So we score on:

  loudness  : RMS energy per window (the action)
  peaks     : count of sharp transients (individual shots / hits)
  scene     : visual scene-change density from ffmpeg

Usage: python moments.py <video> [--len 18] [--n 6] [--out moments.json]
"""
import argparse, json, os, re, subprocess, sys, tempfile, wave
import numpy as np

SR = 8000  # audio analysis rate; plenty for energy envelopes


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding='utf-8', errors='ignore', **kw)


def duration(path):
    r = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=nw=1:nk=1', path])
    return float(r.stdout.strip())


def audio_envelope(path):
    """Decode to mono 8k PCM and return per-0.1s RMS envelope."""
    tmp = os.path.join(tempfile.gettempdir(), 'clip_env.wav')
    r = run(['ffmpeg', '-y', '-v', 'error', '-i', path,
             '-ac', '1', '-ar', str(SR), '-vn', tmp])
    if not os.path.exists(tmp):
        raise RuntimeError('audio extract failed: ' + r.stderr[:300])
    with wave.open(tmp, 'rb') as w:
        raw = w.readframes(w.getnframes())
    os.remove(tmp)
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    hop = SR // 10                       # 0.1s buckets
    n = len(a) // hop
    a = a[:n * hop].reshape(n, hop)
    rms = np.sqrt((a ** 2).mean(axis=1) + 1e-12)
    return rms


def scene_times(path, thresh=0.35):
    """Timestamps of visual scene changes."""
    r = run(['ffmpeg', '-v', 'info', '-i', path,
             '-filter:v', "select='gt(scene,%s)',showinfo" % thresh,
             '-f', 'null', '-'])
    return [float(m) for m in re.findall(r'pts_time:([\d.]+)', r.stderr)]


def score(video, win, topn):
    dur = duration(video)
    env = audio_envelope(video)          # 10 samples/sec
    scenes = np.array(scene_times(video))
    w = int(win * 10)
    if len(env) <= w:
        raise SystemExit('video shorter than window')

    # sustained loudness over the window
    csum = np.concatenate([[0.0], np.cumsum(env)])
    loud = (csum[w:] - csum[:-w]) / w

    # transient density: samples jumping well above the local floor
    floor = np.median(env)
    trans = (env > floor * 2.2).astype(np.float32)
    tsum = np.concatenate([[0.0], np.cumsum(trans)])
    peaks = (tsum[w:] - tsum[:-w]) / w

    starts = np.arange(len(loud)) / 10.0
    if len(scenes):
        sc = np.array([((scenes >= s) & (scenes < s + win)).sum() for s in starts], dtype=np.float32)
    else:
        sc = np.zeros(len(starts), dtype=np.float32)

    def norm(x):
        p5, p95 = np.percentile(x, 5), np.percentile(x, 95)
        return np.clip((x - p5) / (p95 - p5 + 1e-9), 0, 1)

    total = 0.5 * norm(loud) + 0.3 * norm(peaks) + 0.2 * norm(sc)

    # greedy non-overlapping pick, keeping a gap so clips do not repeat footage
    order = np.argsort(-total)
    picked, gap = [], int(win * 10 * 0.9)
    for i in order:
        if all(abs(int(i) - int(p)) > gap for p in picked):
            picked.append(int(i))
        if len(picked) >= topn:
            break
    picked.sort()

    return dur, [dict(start=round(i / 10.0, 2), end=round(i / 10.0 + win, 2),
                      score=round(float(total[i]), 3),
                      loud=round(float(norm(loud)[i]), 3),
                      peaks=round(float(norm(peaks)[i]), 3),
                      scenes=int(sc[i])) for i in picked]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--len', type=float, default=18.0, help='clip length seconds')
    ap.add_argument('--n', type=int, default=6, help='how many moments')
    ap.add_argument('--out', default=os.path.join(os.environ.get('CLIP_HOME', os.getcwd()), 'work', 'moments.json'))
    a = ap.parse_args()

    dur, moments = score(a.video, a.len, a.n)
    json.dump(dict(video=a.video, duration=dur, win=a.len, moments=moments),
              open(a.out, 'w'), indent=1)
    print('source %.1fs -> %d moments of %.0fs' % (dur, len(moments), a.len))
    print('%-8s %-8s %6s %6s %6s %6s' % ('START', 'END', 'SCORE', 'LOUD', 'PEAKS', 'CUTS'))
    for m in moments:
        print('%-8.1f %-8.1f %6.3f %6.3f %6.3f %6d'
              % (m['start'], m['end'], m['score'], m['loud'], m['peaks'], m['scenes']))
    print('\nwrote', a.out)


if __name__ == '__main__':
    main()
