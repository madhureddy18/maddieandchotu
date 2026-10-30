# Maddie & Chotu Studio

Your own free website for posting Reels to **@maddieandchotu**: **https://madhureddy18.github.io/maddieandchotu/**

- Videos made by Claude land in `queue/` ready to go: title, caption, 5 hashtags (Instagram's limit), first comment, audio name, cover image and a posting tip. Tap one, check it, then **Post now** or **Schedule**.
- You can also add your own video from the site.
- Nothing posts unless you schedule it or press Post now.
- Scheduled Reels are checked every 15 minutes (GitHub can start a few minutes late). Post now takes ~1–4 minutes.
- Posted Reels show up under "Posted" with a link to Instagram.

`tools/make_cover.py` makes a cover (frame + title).

How it works: the site saves videos into `queue/` in this repo; GitHub Actions (`.github/workflows/post.yml`) posts them with the official Instagram API. Free, no servers.

## Secrets (Settings → Secrets and variables → Actions)
- `MADDIEANDCHOTUIGTOKEN` – the @maddieandchotu Instagram token.
- `IG_TOKEN` – a fine-grained GitHub token for this repo with *Secrets: Read and write* (the weekly job uses it to keep the Instagram token alive).

The website asks for a fine-grained GitHub token with **Contents** and **Actions** = *Read and write* (it's stored only in your browser).

Note: the repo is public because Instagram downloads videos from a public link.
