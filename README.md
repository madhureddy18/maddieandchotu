# Maddie & Chotu Studio

Your own free website for posting Reels to **@maddieandchotu**: **https://madhureddy18.github.io/maddieandchotu/**

- Upload a video, write the caption, then **Save draft**, **Schedule** (pick a date + time), or **Post now**.
- Nothing posts unless you schedule it or press Post now.
- Scheduled Reels are checked every 15 minutes (GitHub can start a few minutes late). Post now takes ~1–4 minutes.
- Posted Reels show up under "Posted" with a link to Instagram.

How it works: the site saves videos into `queue/` in this repo; GitHub Actions (`.github/workflows/post.yml`) posts them with the official Instagram API. Free, no servers.

## Secrets (Settings → Secrets and variables → Actions)
- `MADDIEANDCHOTUIGTOKEN` – the @maddieandchotu Instagram token.
- `IG_TOKEN` – a fine-grained GitHub token for this repo with *Secrets: Read and write* (the weekly job uses it to keep the Instagram token alive).

The website asks for a fine-grained GitHub token with **Contents** and **Actions** = *Read and write* (it's stored only in your browser).

Note: the repo is public because Instagram downloads videos from a public link.
