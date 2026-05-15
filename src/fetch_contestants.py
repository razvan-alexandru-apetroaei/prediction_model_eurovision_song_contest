"""
Download contestant metadata (country, artist, song, bpm, tone, YouTube URLs)
from the EurovisionAPI GitHub dataset.

Output: data/raw/voting/{year}_meta.json  →  {country_code: {artist, song, bpm, tone, yt_url}}
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from config import EUROVISION_API_BASE, DIR_RAW_VOTING

GITHUB_CONTENTS = (
    "https://api.github.com/repos/EurovisionAPI/dataset/contents/data/senior"
)
_SESSION = requests.Session()
_SESSION.headers.update({"Accept": "application/vnd.github+json"})


def _list_contestants(year: int) -> list[tuple[int, str]]:
    """Return [(contestantId, country_code_upper), …] via GitHub Contents API."""
    url = f"{GITHUB_CONTENTS}/{year}/contestants"
    r = _SESSION.get(url, timeout=15)
    r.raise_for_status()
    items = []
    for item in r.json():
        m = re.match(r"^(\d+)_([a-z]+)$", item["name"])
        if m:
            items.append((int(m.group(1)), m.group(2).upper()))
    return sorted(items)


def _fetch_contestant(year: int, cid: int, cc: str) -> dict:
    url = f"{EUROVISION_API_BASE}/{year}/contestants/{cid}_{cc.lower()}/contestant.json"
    r = _SESSION.get(url, timeout=15)
    r.raise_for_status()
    return r.json()


def _extract_yt_id(urls: list[str]) -> str:
    """Extract a YouTube video ID from embed URLs."""
    for u in (urls or []):
        m = re.search(r"(?:embed/|v=|youtu\.be/)([A-Za-z0-9_-]{11})", u)
        if m:
            return m.group(1)
    return ""


def fetch_year_meta(year: int, output_dir=DIR_RAW_VOTING, force=False) -> dict[str, dict]:
    """
    Return {country_code: {artist, song, bpm, tone, yt_id}} for a single year.
    Results are cached at {year}_meta.json.
    """
    path = Path(output_dir) / f"{year}_meta.json"
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8"))

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    contestants = _list_contestants(year)
    meta = {}
    for cid, cc in contestants:
        try:
            data = _fetch_contestant(year, cid, cc)
            meta[cc] = {
                "artist": data.get("artist", ""),
                "song":   data.get("song", ""),
                "bpm":    data.get("bpm") or 0,
                "tone":   data.get("tone") or "",
                "yt_id":  _extract_yt_id(data.get("videoUrls", [])),
            }
        except requests.HTTPError as e:
            print(f"    {year}/{cc}: HTTP {e.response.status_code}")
        time.sleep(0.15)

    path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


def fetch_all_meta(years=None, output_dir=DIR_RAW_VOTING, force=False) -> dict[int, dict]:
    if years is None:
        from config import YEARS_TRAIN
        years = YEARS_TRAIN
    all_meta = {}
    for year in years:
        print(f"  {year}: fetching contestant metadata…")
        try:
            all_meta[year] = fetch_year_meta(year, output_dir, force)
            print(f"         -> {len(all_meta[year])} countries")
        except Exception as e:
            print(f"         -> error: {e}")
        time.sleep(0.5)
    return all_meta


def load_meta(year: int, data_dir=DIR_RAW_VOTING) -> dict[str, dict]:
    path = Path(data_dir) / f"{year}_meta.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


# ── 2026 metadata (manually specified in config, no API needed for basic info) ─

def build_2026_meta() -> dict[str, dict]:
    """
    Return {country_code: {artist, song, bpm, tone, yt_id}} for 2026.
    BPM and YouTube ID are filled in after fetch_spotify / fetch_youtube runs.
    """
    from config import ENTRIES_2026
    meta = {}
    for entry in ENTRIES_2026:
        meta[entry["code"]] = {
            "artist": entry["artist"],
            "song":   entry["song"],
            "bpm":    0,
            "tone":   "",
            "yt_id":  "",
        }
    return meta


if __name__ == "__main__":
    print("Fetching contestant metadata (2016–2025)…")
    fetch_all_meta()
    print("Done.")
