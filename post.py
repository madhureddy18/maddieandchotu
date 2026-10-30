"""Post the next Reel in queue/ to Instagram (@maddieandchotu). Runs on GitHub Actions - see .github/workflows/post.yml.

queue/001-intro.mp4 + queue/001-intro.txt (caption)  -> posted in filename order, one per run.
After posting, the video is removed from queue/ and a line is added to posted.md.

Instagram (Instagram Login API) fetches the video from a public link, so the repo is public and the video is
served by GitHub Pages (correct video/mp4 type); raw.githubusercontent.com is the fallback.

Env: IG_TOKEN (secret), GITHUB_REPOSITORY (set by Actions). Optional: DRY_RUN=1.
"""
import datetime as dt
import os
import sys
import time
from pathlib import Path

import requests

GRAPH, VER = "https://graph.instagram.com", "v26.0"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
ROOT = Path(__file__).parent
QUEUE = ROOT / "queue"


def err(r):
    try:
        e = r.json().get("error") or {}
        return f"{r.status_code}: {e.get('message') or r.text[:300]}"
    except Exception:
        return f"{r.status_code}: {r.text[:300]}"


def next_video():
    vids = sorted(p for p in QUEUE.glob("*.mp4"))
    return vids[0] if vids else None


def public_urls(video):
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    rel = video.relative_to(ROOT).as_posix()
    return [f"https://{owner.lower()}.github.io/{repo}/{rel}",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/{rel}"]


def reachable(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=30)
        return r.ok and int(r.headers.get("content-length") or 1) > 50_000
    except Exception:
        return False


def publish(token, video_url, caption):
    me = requests.get(f"{GRAPH}/{VER}/me", params={"fields": "user_id,username", "access_token": token}, timeout=30)
    if not me.ok:
        raise RuntimeError("Instagram rejected the token - " + err(me))
    uid, user = me.json().get("user_id") or me.json()["id"], me.json().get("username")
    print(f"posting as @{user}")
    h = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{GRAPH}/{VER}/{uid}/media", headers=h, timeout=60,
                      json={"media_type": "REELS", "video_url": video_url, "caption": caption[:2200], "share_to_feed": True})
    if not r.ok:
        raise RuntimeError("Instagram didn't accept the video - " + err(r))
    cid = r.json()["id"]
    t0, code = time.time(), ""
    while time.time() - t0 < 900:
        time.sleep(15)
        s = requests.get(f"{GRAPH}/{VER}/{cid}", headers=h, params={"fields": "status_code,status"}, timeout=30)
        if s.ok:
            code = s.json().get("status_code", "")
            print("  instagram status:", code)
            if code == "FINISHED":
                break
            if code in ("ERROR", "EXPIRED"):
                raise RuntimeError(f"Instagram couldn't process the video ({s.json().get('status', code)})")
    if code != "FINISHED":
        raise RuntimeError("Instagram took too long to process the video")
    for attempt in range(4):
        p = requests.post(f"{GRAPH}/{VER}/{uid}/media_publish", headers=h, json={"creation_id": cid}, timeout=60)
        if p.ok:
            break
        time.sleep(10 * (attempt + 1))
    if not p.ok:
        raise RuntimeError("Instagram publish failed - " + err(p))
    mid = p.json()["id"]
    q = requests.get(f"{GRAPH}/{VER}/{mid}", headers=h, params={"fields": "permalink"}, timeout=30)
    return q.json().get("permalink", "") if q.ok else ""


def main():
    video = next_video()
    if not video:
        print("Queue is empty - nothing to post. Add videos to queue/.")
        return 0
    cap_file = video.with_suffix(".txt")
    caption = cap_file.read_text(encoding="utf-8").strip() if cap_file.exists() else ""
    print(f"next up: {video.name} ({video.stat().st_size / 1e6:.1f} MB), caption {len(caption)} chars")
    urls = [u for u in public_urls(video) if reachable(u)]
    if not urls:
        raise SystemExit("The video isn't publicly reachable yet (is GitHub Pages on? wait a minute after pushing)")
    if os.environ.get("DRY_RUN") == "1":
        print("dry run - would post from", urls[0])
        return 0
    token = os.environ.get("IG_TOKEN", "").strip()
    if not token:
        raise SystemExit("IG_TOKEN secret is missing (Settings > Secrets and variables > Actions)")
    last = None
    for url in urls:
        try:
            print("video link:", url)
            link = publish(token, url, caption)
            break
        except RuntimeError as e:
            last = e
            print("  failed:", e)
    else:
        raise SystemExit(f"Posting failed: {last}")
    print("POSTED:", link)
    when = dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    with open(ROOT / "posted.md", "a", encoding="utf-8") as f:
        f.write(f"- {when} - {video.stem} - {link or 'posted'}\n")
    video.unlink()
    if cap_file.exists():
        cap_file.unlink()
    left = len(list(QUEUE.glob("*.mp4")))
    print(f"{left} video(s) left in the queue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
