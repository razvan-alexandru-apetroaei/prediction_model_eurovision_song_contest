"""
Download historical voting data (finals + semi-finals) from EurovisionAPI.

Rounds fetched per year: semifinal1, semifinal2, final.
Semi-final data fills gaps when a country missed the final (e.g. Australia
2021/2024/2025) and provides extra bilateral voting evidence.
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from config import EUROVISION_API_BASE, DIR_RAW_VOTING, YEARS_TRAIN

GITHUB_API  = "https://api.github.com/repos/EurovisionAPI/dataset/contents/data/senior"
ROUND_NAMES = ["semifinal1", "semifinal2", "final"]
_SESSION    = requests.Session()
_SESSION.headers.update({"Accept": "application/vnd.github+json"})


# ── contestant-id → country-code mapping ─────────────────────────────────────

def _fetch_contestant_map(year: int) -> dict[int, str]:
    url = f"{GITHUB_API}/{year}/contestants"
    r = _SESSION.get(url, timeout=15)
    r.raise_for_status()
    mapping = {}
    for item in r.json():
        m = re.match(r"^(\d+)_([a-z]+)$", item["name"])
        if m:
            mapping[int(m.group(1))] = m.group(2).upper()
    return mapping


def _cache_contestant_map(year: int, data_dir: str) -> dict[int, str]:
    path = Path(data_dir) / f"{year}_contestants.json"
    if path.exists():
        return {int(k): v for k, v in json.loads(path.read_text()).items()}
    mapping = _fetch_contestant_map(year)
    path.write_text(json.dumps(mapping))
    time.sleep(0.4)
    return mapping


# ── round fetch / cache ───────────────────────────────────────────────────────

def _fetch_round(year: int, round_name: str) -> dict | None:
    url = f"{EUROVISION_API_BASE}/{year}/rounds/{round_name}.json"
    r = _SESSION.get(url, timeout=15)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def fetch_all_voting(years=None, output_dir=DIR_RAW_VOTING, force=False):
    """Download all rounds (SF1, SF2, final) for each training year."""
    if years is None:
        years = YEARS_TRAIN
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for year in years:
        for rnd in ROUND_NAMES:
            path = Path(output_dir) / f"{year}_{rnd}.json"
            if path.exists() and not force:
                continue
            try:
                data = _fetch_round(year, rnd)
                if data is None:
                    continue
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                n = len(data.get("performances", []))
                print(f"  {year}/{rnd}: {n} performances")
            except requests.HTTPError as e:
                print(f"  {year}/{rnd}: HTTP {e.response.status_code}")
            time.sleep(0.3)


def load_final(year: int, data_dir=DIR_RAW_VOTING) -> dict:
    """Load cached final data (backward-compat, also tries old filename)."""
    for fname in [f"{year}_final.json", f"{year}.json"]:
        path = Path(data_dir) / fname
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"No final data for {year} – run fetch_all_voting()")


# ── unified long-format table (all rounds) ───────────────────────────────────

def _parse_round(data: dict, year: int, round_name: str, id_to_cc: dict[int, str]) -> list[dict]:
    rows = []
    for perf in data.get("performances", []):
        cid   = perf["contestantId"]
        to_cc = id_to_cc.get(cid, f"UNK{cid}")

        score_map: dict[str, dict] = {s["name"]: s for s in perf.get("scores", [])}
        jury_votes = score_map.get("jury",   {}).get("votes", {})
        tele_votes = score_map.get("public", {}).get("votes", {})
        jury_total = score_map.get("jury",   {}).get("points", 0)
        tele_total = score_map.get("public", {}).get("points", 0)

        for from_cc in set(list(jury_votes) + list(tele_votes)):
            if from_cc == "WLD":
                continue
            rows.append({
                "year":          year,
                "round":         round_name,
                "to_country":    to_cc,
                "from_country":  from_cc,
                "running_order": perf.get("running", 0),
                "place":         perf.get("place", 0),
                "jury_pts":      jury_votes.get(from_cc, 0),
                "tele_pts":      tele_votes.get(from_cc, 0),
                "jury_total":    jury_total,
                "tele_total":    tele_total,
            })
    return rows


def build_long_table(years=None, data_dir=DIR_RAW_VOTING) -> list[dict]:
    """
    Return one row per (year, round, to_country, from_country).
    Includes semi-finals and the final so bilateral history is not biased
    by countries that missed the final in some years.
    """
    if years is None:
        years = YEARS_TRAIN
    rows = []
    for year in years:
        id_to_cc = _cache_contestant_map(year, data_dir)
        for rnd in ROUND_NAMES:
            for fname in [f"{year}_{rnd}.json", f"{year}.json" if rnd == "final" else None]:
                if fname is None:
                    continue
                path = Path(data_dir) / fname
                if path.exists():
                    data = json.loads(path.read_text(encoding="utf-8"))
                    rows.extend(_parse_round(data, year, rnd, id_to_cc))
                    break
    return rows


if __name__ == "__main__":
    print("Fetching all rounds (SF1, SF2, final) for 2016-2025...")
    fetch_all_voting(force=False)
    print("Done.")
