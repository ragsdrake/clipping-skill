---
name: clipping
description: Find paid clipping campaigns (Whop / Content Rewards / Clipping Culture), cut compliant vertical clips from the brand's own footage, post them and submit them for payment. Use for "make short clips and get paid per 1000 views", campaign scanning, cutting gameplay clips, or setting up clipping for the first time.
---

# Clipping

Brands pay per 1,000 views for short vertical clips cut from their own footage.
AdSense pays about $30 for a million Shorts views. A clipping campaign pays about
**$1,500 to $2,100 for the same million**, from the first clip that clears the
campaign's minimum.

The loop: read the live campaign list, pick one that fits, download the brand's
footage, find the most action-packed seconds, cut a 9:16 clip with the required
text, post it, and submit the link before the deadline.

---

## 0. First run: set up before anything else

If `clip-config.json` does not exist in the working folder (`CLIP_HOME`, default:
the folder Claude was started in), this is a first run. Do these two steps in
order and do not cut or post anything until both are done.

### Step 1: connect the browser and the accounts

Clipping needs a logged-in browser for Whop, YouTube Studio and any other
platform the user posts to. Use a **Playwright MCP server with its own profile
folder**, so logins stay on disk between sessions and never fight another
browser for the same profile.

1. Check that a Playwright MCP is loaded (tools named `mcp__playwright...__*`).
   If not, tell the user to add one and restart Claude Code:

   ```bash
   claude mcp add playwright-clipping -- npx -y @playwright/mcp@latest --user-data-dir <a folder for this profile> --allow-unrestricted-file-access
   ```

   `--user-data-dir` keeps the logins. `--allow-unrestricted-file-access` lets
   the browser upload clips from anywhere on disk; without it, uploads only work
   from inside the project folder. If Chrome for Testing is missing:
   `npx -y @playwright/mcp@latest install-browser chrome-for-testing`.
2. Open each login page in that browser and **hand over to the user**. They type
   their own passwords. Never ask for a password, never type one, never store one.
   - Whop: `https://whop.com/login` (Content Rewards and Clipping Culture run on Whop)
   - YouTube: `https://studio.youtube.com`
   - TikTok / Instagram / X: only the ones they said they post to
3. Connect each posting account inside Content Rewards: Settings → Connected
   accounts → Connect account. YouTube connects through a Google OAuth screen
   (read-only scopes). **Ask before clicking Continue**: it is a grant on their
   Google account.
4. Verify each login by reading page text, not the page title. Whop pages render
   a public version for signed-out visitors and look fine. Look for their username
   on the submissions page.

### Step 2: ask what they need

Ask these, one short message, and save the answers to `clip-config.json`:

| Question | Why it matters |
|---|---|
| Which platforms do you post to? (YouTube Shorts, TikTok, Instagram, X) | Rates and rules differ per platform |
| Which niches are fine? (gaming, podcasts, streamers, brands, anything) | Picks which campaigns to look at |
| Which country are you in, and where is your audience? | Many campaigns gate on audience country (see the rules) |
| How many clips a day? | Volume beats polish here (see "It is a lottery") |
| Post right away, or show you each clip first? | Default: show first |
| What hours can posts go out, in your time zone? | Aim at the campaign's target country |
| Channel names / handles to post on | Never post anywhere they did not name |

Example `clip-config.json`:

```json
{
  "platforms": ["youtube"],
  "channels": {"youtube": "@yourhandle"},
  "niches": ["gaming"],
  "home_country": "US",
  "clips_per_day": 5,
  "review_before_posting": true,
  "posting_hours_local": ["18:00", "19:00", "20:00"],
  "timezone": "America/New_York",
  "min_budget_left_usd": 3000
}
```

Re-read it at the start of every session. Change it only when the user says so.

---

## 1. The hard rules (breaking one loses the money)

These are the Clipping Culture global requirements as last read. **Read the
campaign's own brief and the global page again before every new campaign; they
change.**

1. **Audience: mostly Tier 1-2 countries.** On Clipping Culture, 30% or more
   Tier 3 audience gets you removed from the whole program, not one campaign.
   Check YouTube Studio → Analytics → Audience → Top geographies after about
   five posts, before scaling. If the user lives in a Tier 3 country, every
   title, keyword and posting time aims at the US and Europe.
2. **Engagement at least 0.20%.** 1,000 views needs 2 likes.
3. **Likes visible.** Hidden likes = automatic rejection.
4. **The post stays up 30 days.** Deleting early = rejection, maybe a ban.
5. **Submit the link within 30 minutes of posting** (check the campaign; some
   allow longer). Post and submit in the same run.
6. **Use only the brand's footage folder.** Clips from other sources get rejected.
7. **Campaign-specific lines.** Many briefs demand a verbatim caption line, a
   tag (`@brand`), `#Ad` on its own line, English only, no added music, a
   minimum length. Copy them exactly. Paraphrasing = rejection.

## 2. Picking a campaign

**Do not sort by budget ÷ creators.** The pool is a race, not a split. A campaign
with 4 creators often has 4 creators because nobody wants to watch it, and
$70,000 is effectively unlimited for one person.

1. **Hard filter:** open to the user's audience country, no filming yourself,
   no signup or debit card, enough budget left (default $3,000+).
2. **Then rank by how watchable the footage is.** Gameplay needs no language and
   has huge demand. An unknown person talking has none.
3. Reject on sight: *film yourself*, *on camera*, *must create a debit card*,
   *affiliate link in bio*.

**Check money LEFT, not money used.** The campaign list shows money used
("$793 / $24,000" can mean $24k of $24k is gone). Open the campaign page, read
the "remaining" line, and confirm the **Submit clip** button is enabled
**before cutting anything**. Clips cut for a finished campaign earn nothing and
still have to stay up.

## 3. Run it

```bash
python scripts/rank.py work/cr-full.json   # rank the scraped campaign list
python scripts/scan.py 45                  # read briefs, flag country gates
python scripts/moments.py work/source.mp4 --len 18 --n 6
python scripts/cut_v2.py --n 1 --batch 1   # letterbox layout
python scripts/perf.py                     # after 24h: what worked
```

All files live under `CLIP_HOME` (`work/` for inputs, `out/` for clips). Needs
Python 3.10+, `numpy`, and `ffmpeg` / `ffprobe` on PATH.

**Getting `work/cr-full.json`:** open `https://contentrewards.com/discover` in
the Playwright browser, scroll until all cards load, and evaluate:

```js
() => ({cards: [...document.querySelectorAll('a[href*="campaigns/"]')].map(a => ({
  href: a.href,
  text: a.innerText.split('\n').map(s => s.trim()).filter(Boolean).join('|')
}))})
```

Save the result to `work/cr-full.json`. If the site layout changed, fix the
parser in `rank.py` to match.

**Your campaign's text:** copy `campaign.example.json` to `work/campaign.json`,
fill in the brief's required phrase, banners and captions, and put the brand's
logo at `work/logo.png`. `cut_v2.py` uses it over the built-in MW4 example.

## 4. Verify every render by counting frames

A render once shipped with 1 second of picture under 14 seconds of sound. The
container duration looked right because audio was mapped separately. Count
real frames:

```bash
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 <file>
```

Expect frames ≈ fps × duration. Never upload a clip that fails this.
`cut_v2.py` checks it for you and refuses broken renders.

## 5. Measure the field before you theorise

The single best move. Every clipper on a campaign must carry the same verbatim
caption line, so that line finds all of them. Search YouTube (Shorts, this
month) for the exact sentence, sort by views, and you have the whole field:
same footage, same rules, different packaging. A free controlled experiment.

How to do it fast, from inside the logged-in browser with YouTube's InnerTube
search instead of scrolling:

- Shorts filter `sp=EgIQCQ%3D%3D`; this month + Shorts `EgQIBBAJ`. **Sort by
  views + the Shorts filter returns nothing.** Harvest unsorted, sort locally.
- Shorts come back as `shortsLockupViewModel`: title and views in
  `overlayMetadata`, id under `onTap.innertubeCommand.reelWatchEndpoint.videoId`.
- Filters drop on continuation pages. Use first pages of many queries.
- Set `context.client.gl='US'`, `hl='en'` so results are not skewed to the
  user's own country.
- `https://www.youtube.com/oembed?format=json&url=...` gives the channel name
  with no login.
- Tile the winners' first frames (`i.ytimg.com/vi/<id>/oardefault.jpg`, ffmpeg
  `xstack`) into one contact sheet. The layout pattern jumps out.
- Check like rate before copying anyone. Real traffic sits near 1%. Under 0.1%
  with high views means bought traffic.

**What it showed on a Call of Duty campaign (90 Shorts, 2026-09):** median 18.5
views, 19 of 90 cleared 1,000. Of those 19:

1. 17-18 were **letterboxed**: bold text band on top, the untouched 16:9 gameplay
   in the middle, a big logo underneath. Not full-bleed.
2. On-screen text was **literal and keyword-loaded** ("MODERN WARFARE 4 GAMEPLAY
   IS HERE"), not clever. On a new channel the text tells YouTube what the video is.
3. All 19 used the **sponsor's required sentence as the title**, plus the brand tag
   and `#ad`.
4. Two-line caption low on the gameplay, second line red.
5. 10-24 seconds long, mostly 11-17.

The top two wrapped the clip in a fake tweet with invented likes. Do not copy
that: it fabricates engagement and a verified account.

`cut_v2.py` builds the letterbox layout.

## 6. It is a lottery: post volume, judge at 24 hours

Rival channels on the same campaign, all 1-5 subscribers, some created that
same day, each had 1-view clips next to 1,300-view clips. About one clip in
three lands.

- **Channel age and subscriber count did not gate views.** A 1-subscriber
  channel beat a 46,000-subscriber one by 2x.
- **Volume wins.** The ones earning posted 5-13 clips a day.
- **Judge at 24 hours, and only after three or more posts.** One post is noise.
- **Know the break-even.** At $1.75/1k with a $5.25 minimum, a Short under
  3,000 views earns exactly $0. `perf.py` uses that bar; change `RATE_PER_1K`
  and `MIN_PAYOUT` for your campaign.

Reading `perf.py`'s verdict:

- Nothing cleared the bar → check distribution first (below), then go measure
  the field.
- Wide spread (best 3x the worst) → packaging matters; make variations of the winner.
- Narrow spread, all mediocre → the footage is the lever; get fresh footage.

**Check distribution before creative.** In YouTube Studio, open a video's Reach
tab. If the Shorts feed is only a few percent of traffic and devices say 100%
Computer, the feed is not showing the clips at all and every hook test is
unreadable. Desktop views are mostly you checking your own uploads.

**Never inflate views.** No opening your own videos repeatedly, view farms,
engagement pods or "unfreeze" tricks. YouTube terminates channels for it and
campaigns drop creators for bought traffic.

## 7. Posting times and audience

- Posting time is the biggest free lever. Aim at the campaign's target country:
  US campaigns → late morning to evening US Eastern.
- English only everywhere on the channel if the campaign is English.
- Native gaming words in titles: *insane, cracked, clutch, no way*.
- If the audience check shows too much Tier 3, stop and switch to a campaign
  targeted at the user's own country (Content Rewards runs `[UK]`, `[Mexico]`,
  `[Brazil]` and similar).

## 8. Uploading a Short in the browser (no API)

1. `studio.youtube.com/channel/<id>/videos/upload?d=ud` → `Select files`
2. `browser_file_upload` with the clip path
3. Wait ~9 s, then set title and description with
   `document.execCommand('insertText')` on the two `[contenteditable]` boxes
   (React ignores `.value`)
4. Radio: `No, it's not made for kids`
5. `Next` ×3, waiting for an enabled Next each time
6. **Never click Next or Publish while it still says "Checking N%" or
   "Uploading".** That causes "Processing abandoned". Wait for "Checks complete"
   or at least "Processing up to HD".
7. Public → Publish (or Schedule)
8. "Processing abandoned" in page text can be a **stale row** from an older
   upload behind the dialog. Confirm with a screenshot before calling it a failure.

## 9. Submitting on Whop

- **Do not work inside the Whop iframe.** `whop.com/<community>/...` renders the
  Content Rewards app in a cross-origin iframe where page reads return almost
  nothing. The same app serves itself directly on its own `*.apps.whop.com`
  origin with the same login. Find it from the iframe's `src`, then use
  `<origin>/c/<experience id>/campaigns/<campaign id>` and
  `<origin>/c/<experience id>/submissions`.
- **Submitting right after publishing can fail for ~10 minutes** ("We couldn't
  confirm exactly when this post went live"). Retry every 90 seconds. Use the
  `youtube.com/watch?v=` link.
- The acknowledgement checkbox's real `input` is hidden behind a styled `<span>`.
  Click the label text.
- Modal overlays steal clicks: `text=Join` can hit the button behind the dialog.
  Find the element inside the dialog by position.
- Open campaign pages through Discover on the apps origin. A direct `/preview`
  URL in a fresh tab can bounce back to the iframe.

## 10. Footage traps

- **Whisper is useless on gameplay**: no speech. Score on audio energy and scene
  cuts (`moments.py`). For streamer VODs with talking, do transcribe the peaks
  and skip moments with slurs or heavy swearing.
- **Use the 1080p derivative**, not the original master (212 MB vs 1.5 GB for
  the same 4 minutes on MediaSilo). 1080p is plenty for a 1080×1920 Short.
- **SharePoint throttles hard.** Five parallel downloads got an account 429'd for
  hours. One at a time, no `-N`. `yt-dlp --download-sections` fails on those
  manifests; `ffmpeg -ss` on the direct `source` URL works.
- **A cut-short download can exit 0.** ffmpeg once stopped at 1.8 s of a 16 s
  window and reported success. Count frames after every fetch.
- If the brief allows the streamer's own Twitch or YouTube VOD, that is often
  the fastest way around a throttled host. Check where the VOD stops being the
  campaign content (watch parties, other games).
- A game's licensed soundtrack can trigger a Content ID claim ("no impact to
  reach"). Expected, not a strike.
- Geo gates are not always in English: Spanish `PORCENTAJE DE ESPAÑA`, French
  `pays francophones`, German `deutschsprachig`. `scan.py` covers ES/DE/FR.
- Bash heredocs can collapse `\\` to `\` and break regexes. Write Python files
  with the Write tool.
- The Playwright browser sometimes drops its connection and loses all tabs.
  Logins survive on disk. Just navigate again.
- One profile folder can be open in only one browser at a time. Give clipping
  its own profile folder so other agents never lock it.

## 11. What only the human does

- Log in anywhere. Type passwords. Create accounts or channels.
- Grant OAuth (connecting a channel to Content Rewards).
- Join a campaign (it accepts the brand's terms): ask first.
- Open financial products. Skip campaigns that demand a debit card.
- Delete videos.
- Approve posting, unless `clip-config.json` says `review_before_posting: false`.
