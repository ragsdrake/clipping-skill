# Clipping skill for Claude Code

Brands on Whop (Content Rewards, Clipping Culture) pay per 1,000 views for short
vertical clips cut from their footage. This skill lets Claude Code do the work:
find a campaign worth joining, cut clips in the layout that actually gets views,
post them, and submit the links for payment.

I ran this every day for about a month. The skill keeps what I learned, including
why clips got rejected and which layout the top clippers on a campaign use.

## What's in it

```
clipping/
├─ SKILL.md               the skill: setup, rules, campaign picking, what works
├─ campaign.example.json  copy to work/campaign.json and fill in your brief
└─ scripts/
   ├─ rank.py      rank campaigns from the scraped Content Rewards list
   ├─ scan.py      read each brief, flag country gates and signup traps
   ├─ moments.py   find the most action-packed seconds (audio energy + scene cuts)
   ├─ cut_v2.py    cut a letterboxed 9:16 clip, then check the frame count
   └─ perf.py      after 24 hours: which clips cleared the payout bar
```

## Install

1. Copy the `clipping` folder into `~/.claude/skills/`.
2. Install Python 3.10+, `numpy` (`pip install numpy`) and
   [ffmpeg](https://ffmpeg.org/download.html) (`ffmpeg` and `ffprobe` on PATH).
3. Add a Playwright browser with its own profile, so your logins are saved:

   ```bash
   claude mcp add playwright-clipping -- npx -y @playwright/mcp@latest --user-data-dir <a folder for this profile> --allow-unrestricted-file-access
   ```

4. Open Claude Code in an empty folder for your clipping work and say
   **"set up clipping"**.

## The first run

The first time, Claude does two things before it cuts anything:

1. It connects your accounts. It opens Whop, YouTube Studio and any other
   platform you post to in that browser. You sign in yourself; Claude never asks
   for or types a password. Then it walks you through connecting your channel
   inside Content Rewards and asks before you approve the Google screen.
2. It asks what you want: which platforms, which niches, your country and your
   audience's, how many clips a day, whether to show you each clip before it
   goes up, and what hours to post. The answers go into `clip-config.json`, and
   it reads that file at the start of every session.

## Ground rules it follows

- It doesn't post, join a campaign or delete anything without your yes
  (unless you set `review_before_posting` to `false`).
- No view inflation of any kind. Platforms ban channels for it and campaigns
  drop creators for it.
- It reads each campaign's rules again before cutting, because they change.

Campaign rules, rates and site layouts change often. If a script stops
matching the page, tell Claude to fix the parser.

## License

MIT
