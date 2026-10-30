# @maddieandchotu auto-poster

Free Instagram Reels auto-posting with GitHub Actions. No servers.

- Put a video in `queue/` as `NNN-name.mp4` with its caption in `NNN-name.txt` (same name).
- It posts the next one (lowest number first) every day at **8:00 AM** and **7:30 PM** India time.
- After posting, the video is removed from `queue/` and logged in `posted.md`.
- **Post right now:** Actions → "Post next Reel" → Run workflow.
- **Change times:** edit the two `cron` lines in `.github/workflows/post.yml` (UTC = India time − 5:30).
- GitHub can start scheduled runs 5–30 minutes late.

## One-time setup
1. Settings → Pages → Source: *Deploy from a branch* → `main` / `(root)` → Save.
2. Settings → Secrets and variables → Actions → New secret `IG_TOKEN` = your @maddieandchotu Instagram token.
3. (Recommended) Secret `GH_PAT` = fine-grained GitHub token for this repo with *Secrets: Read and write*, so the weekly job can keep the Instagram token alive forever.

Note: the repo is public because Instagram downloads the video from a public link. Videos are visible here until they're posted.
