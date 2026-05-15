"""
Fetch YouTube view counts for Eurovision entries.

Two modes:
  1. YouTube Data API v3  (requires YOUTUBE_API_KEY – most accurate)
  2. Scrape the /watch page as fallback (no key needed, best-effort)

Stores {country_code: {view_count, like_count, yt_id}} per year.
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from config import YOUTUBE_API_KEY

_ROOT = Path(__file__).parent.parent
DIR_RAW_YOUTUBE = str(_ROOT / "data" / "raw" / "youtube")
YT_API = "https://www.googleapis.com/youtube/v3"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ESCPredictor/1.0)"}


# ── YouTube Data API v3 ───────────────────────────────────────────────────────

def _api_video_stats(video_id: str) -> dict:
    url = f"{YT_API}/videos"
    r = requests.get(
        url,
        params={"part": "statistics", "id": video_id, "key": YOUTUBE_API_KEY},
        timeout=10,
    )
    r.raise_for_status()
    items = r.json().get("items", [])
    if not items:
        return {}
    stats = items[0].get("statistics", {})
    return {
        "view_count": int(stats.get("viewCount", 0)),
        "like_count": int(stats.get("likeCount", 0)),
    }


# ── Scrape fallback ───────────────────────────────────────────────────────────

def _scrape_views(video_id: str) -> int:
    """Parse view count from YouTube watch page (no API key needed)."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    r = requests.get(url, headers=_HEADERS, timeout=15)
    # Primary pattern: JSON blob in page source
    for pattern in [
        r'"viewCount":"(\d+)"',
        r'"viewCount":\{"simpleText":"([\d,]+)"',
        r'"videoViewCountRenderer".*?"([\d,]+)\s*views?"',
    ]:
        m = re.search(pattern, r.text)
        if m:
            return int(re.sub(r"\D", "", m.group(1)))
    return 0


def _get_stats(yt_id: str) -> dict:
    if not yt_id:
        return {"view_count": 0, "like_count": 0}
    if YOUTUBE_API_KEY:
        try:
            return _api_video_stats(yt_id)
        except Exception:
            pass
    # fallback: scrape
    views = _scrape_views(yt_id)
    return {"view_count": views, "like_count": 0}


# ── Public interface ──────────────────────────────────────────────────────────

def fetch_youtube_stats(
    year: int,
    meta: dict[str, dict],
    output_dir=DIR_RAW_YOUTUBE,
    force=False,
) -> dict[str, dict]:
    """
    Fetch YouTube stats for each country in `meta` for `year`.
    `meta` is {country_code: {yt_id, …}}.
    Results cached at data/raw/youtube/{year}.json.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = Path(output_dir) / f"{year}.json"
    cached: dict[str, dict] = {}
    if path.exists() and not force:
        cached = json.loads(path.read_text(encoding="utf-8"))

    changed = False
    for cc, info in meta.items():
        if cc in cached:
            continue
        yt_id = info.get("yt_id", "")
        stats = _get_stats(yt_id)
        stats["yt_id"] = yt_id
        cached[cc] = stats
        print(f"    {year}/{cc}: {stats['view_count']:,} views")
        changed = True
        time.sleep(0.3)

    if changed:
        path.write_text(json.dumps(cached, indent=2), encoding="utf-8")
    return cached


def load_youtube(year: int, data_dir=DIR_RAW_YOUTUBE) -> dict[str, dict]:
    path = Path(data_dir) / f"{year}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    from fetch_contestants import fetch_all_meta
    print("Fetching YouTube stats…")
    all_meta = fetch_all_meta()
    for year, meta in all_meta.items():
        print(f"  {year}…")
        fetch_youtube_stats(year, meta)
    print("Done.")
