"""Post Reels to Instagram (@maddieandchotu). Runs on GitHub Actions, driven by the website (index.html).

queue/<id>.mp4 + queue/<id>.json  {"caption": "...", "at": "2026-10-31T08:00:00+05:30" | null, "name": "..."}
  - at = null      -> draft, never posted automatically
  - at = a time    -> posted by the scheduled check once that time has passed
  - "Post now"     -> the website starts this workflow with the item's id
After posting, the video leaves the queue and is added to posted.json (shown on the website).

Instagram (Instagram Login API) downloads the video from a public link: GitHub Pages serves it (video/mp4).
Env: IG_TOKEN, GITHUB_REPOSITORY, POST_ID (optional), DRY_RUN=1 (optional).
"""
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import requests

GRAPH, VER = "https://graph.instagram.com", "v26.0"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
ROOT = Path(__file__).parent
QUEUE = ROOT / "queue"
POSTED = ROOT / "posted.json"


def err(r):
    try:
        e = r.json().get("error") or {}
        return f"{r.status_code}: {e.get('message') or r.text[:300]}"
    except Exception:
        return f"{r.status_code}: {r.text[:300]}"


def now():
    return dt.datetime.now(IST)


def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save(p, obj):
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def items():
    return [(v, load(v.with_suffix(".json"))) for v in sorted(QUEUE.glob("*.mp4"))]


def due_items():
    out = []
    for v, m in items():
        at = m.get("at")
        if not at or m.get("status") == "failed":
            continue
        try:
            if dt.datetime.fromisoformat(at) <= now():
                out.append((v, m))
        except ValueError:
            pass
    return out


def public_url(video):
    """GitHub Pages link to the video; waits a few minutes for Pages to publish a fresh upload."""
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    rel = video.relative_to(ROOT).as_posix()
    pages = f"https://{owner.lower()}.github.io/{repo}/{rel}"
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{rel}"
    for i in range(20):
        try:
            r = requests.head(pages, allow_redirects=True, timeout=30)
            if r.ok and int(r.headers.get("content-length") or 0) > 50_000:
                return pages
        except Exception:
            pass
        print("  waiting for GitHub Pages to publish the video..." if i == 0 else "  ...", flush=True)
        time.sleep(15)
    print("  Pages link not ready, trying the raw GitHub link")
    return raw


def publish(token, video_url, caption):
    me = requests.get(f"{GRAPH}/{VER}/me", params={"fields": "user_id,username", "access_token": token}, timeout=30)
    if not me.ok:
        raise RuntimeError("Instagram rejected the token - " + err(me))
    uid = me.json().get("user_id") or me.json()["id"]
    print(f"posting as @{me.json().get('username')}", flush=True)
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
            print("  instagram:", code, flush=True)
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


def post_one(token, video, meta):
    jf = video.with_suffix(".json")
    try:
        link = publish(token, public_url(video), meta.get("caption", ""))
    except Exception as e:
        meta.update(status="failed", error=str(e)[:300], tried=now().isoformat(timespec="seconds"))
        save(jf, meta)
        print("FAILED:", e)
        return False
    print("POSTED:", link)
    hist = load(POSTED) if POSTED.exists() else []
    hist = hist if isinstance(hist, list) else []
    hist.insert(0, {"id": video.stem, "name": meta.get("name", ""), "caption": meta.get("caption", ""),
                    "url": link, "posted": now().isoformat(timespec="seconds")})
    save(POSTED, hist)
    video.unlink()
    jf.unlink(missing_ok=True)
    return True


def main():
    token = os.environ.get("IG_TOKEN", "").strip()
    if not token:
        raise SystemExit("MADDIEANDCHOTUIGTOKEN secret is missing (Settings > Secrets and variables > Actions)")
    pid = os.environ.get("POST_ID", "").strip()
    if pid:
        v = QUEUE / f"{pid}.mp4"
        if not v.exists():
            raise SystemExit(f"{pid} isn't in the queue (already posted or deleted?)")
        todo = [(v, load(v.with_suffix(".json")))]
    else:
        todo = due_items()
    if os.environ.get("DRY_RUN") == "1":
        me = requests.get(f"{GRAPH}/{VER}/me", params={"fields": "username", "access_token": token}, timeout=30)
        if not me.ok:
            raise SystemExit("Instagram rejected the token - " + err(me))
        print(f"dry run OK - token works for @{me.json().get('username')}; due now: {[v.name for v, _ in todo]}")
        return 0
    if not todo:
        print("Nothing due.")
        return 0
    ok = all([post_one(token, v, m) for v, m in todo])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
