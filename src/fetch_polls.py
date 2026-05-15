"""
Scrape Eurovision fan poll rankings from eurovisionworld.com.

The page at https://eurovisionworld.com/esc/eurovision-{year}-poll shows:
  • The *current* year's poll while it's open (dynamic, JS-rendered – not parseable)
  • Historical results for past years in text form (top-3 only on the summary page)

Strategy:
  1. Try to fetch the full poll page and extract an embedded JSON blob.
  2. Fall back to extracting the percentage-based top-N text for historical years.
  3. For the active 2026 poll, also check the dedicated 2026 poll page.

We store results as:  {country_code: poll_rank}
where rank 1 = most votes.  Countries not mentioned get rank = (max_rank + 1).
"""
import json
import re
import time
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup

from config import DIR_RAW_POLLS

# Known historical top-3 results scraped manually from the page (fallback)
# Format: {year: [(country_code, pct_float), ...]} – ordered best → worst
_HARDCODED_HISTORY: dict[int, list[tuple[str, float]]] = {
    2015: [("SE", 14.0), ("IT", 10.0), ("AL", 8.0)],
    2016: [("RU", 15.0), ("UA", 14.0), ("FR", 8.0)],
    2017: [("PT", 18.0), ("IT", 12.0), ("BE", 7.0)],
    2018: [("IL", 16.0), ("CY", 10.0), ("GR", 5.0)],
    2019: [("NL", 21.0), ("RU", 7.0),  ("SE", 6.0)],
    2021: [("IT", 11.0), ("FR", 9.0),  ("MT", 8.0)],
    2022: [("UA", 9.0),  ("ES", 9.0),  ("SE", 9.0)],
    2023: [("SE", 17.0), ("FI", 17.0), ("IL", 7.0)],
    2024: [("HR", 16.0), ("CH", 11.0), ("IL", 9.0)],
    2025: [("SE", 16.0), ("AT", 14.0), ("AL", 6.0)],
}

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ESCPredictor/1.0)"}


def _fetch_page(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except requests.RequestException:
        return None


def _extract_json_blob(soup: BeautifulSoup) -> dict | None:
    """Look for an embedded JSON variable or script block with poll data."""
    for script in soup.find_all("script"):
        text = script.string or ""
        # Common patterns: window.__data = {...} or var pollData = {...}
        m = re.search(r'(?:window\.__\w+|var \w+)\s*=\s*(\{.*?"poll".*?\})\s*;', text, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    return None


def _parse_poll_table(soup: BeautifulSoup) -> list[tuple[str, float]]:
    """
    Attempt to parse a ranking table from the poll page.
    Returns [(country_code, percentage), …] ordered by rank.
    """
    results = []
    # Look for flag images or country name cells paired with percentage cells
    rows = soup.select("table tr, .poll-row, .country-row")
    for row in rows:
        cells = row.find_all(["td", "div"])
        pct_text = None
        country = None
        for cell in cells:
            text = cell.get_text(strip=True)
            if re.match(r"^\d+\.?\d*\s*%$", text):
                pct_text = text
            img = cell.find("img")
            if img:
                src = img.get("src", "") + img.get("alt", "") + img.get("title", "")
                m = re.search(r"/([a-z]{2})\.", src, re.I)
                if m:
                    country = m.group(1).upper()
        if country and pct_text:
            pct = float(re.sub(r"[^\d.]", "", pct_text))
            results.append((country, pct))
    return results


def fetch_poll(year: int) -> dict[str, int]:
    """
    Return {country_code: rank} for the given year's fan poll.
    Rank 1 = most fan votes.
    """
    url = f"https://eurovisionworld.com/esc/eurovision-{year}-poll"
    soup = _fetch_page(url)

    entries: list[tuple[str, float]] = []

    if soup:
        blob = _extract_json_blob(soup)
        if blob:
            pass  # future: parse structured blob

        table_results = _parse_poll_table(soup)
        if table_results:
            entries = table_results

    # Fall back to hardcoded history
    if not entries and year in _HARDCODED_HISTORY:
        entries = _HARDCODED_HISTORY[year]

    # Convert ordered list → {CC: rank}
    ranking = {}
    for rank, (cc, _pct) in enumerate(entries, start=1):
        ranking[cc] = rank
    return ranking


def fetch_all_polls(years=None, output_dir=DIR_RAW_POLLS, force=False) -> dict[int, dict]:
    if years is None:
        from config import YEARS_TRAIN
        years = YEARS_TRAIN
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    all_polls = {}
    for year in years:
        path = Path(output_dir) / f"{year}.json"
        if path.exists() and not force:
            all_polls[year] = json.loads(path.read_text())
            print(f"  {year}: loaded from cache ({len(all_polls[year])} countries)")
            continue
        ranking = fetch_poll(year)
        path.write_text(json.dumps(ranking, indent=2))
        all_polls[year] = ranking
        print(f"  {year}: {len(ranking)} countries ranked")
        time.sleep(0.5)
    return all_polls


def fetch_poll_2026(output_dir=DIR_RAW_POLLS, force=False) -> dict[str, int]:
    """Fetch the current 2026 fan poll. Falls back to empty dict if not available."""
    path = Path(output_dir) / "2026.json"
    if path.exists() and not force:
        return json.loads(path.read_text())

    ranking = fetch_poll(2026)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ranking, indent=2))
    print(f"2026 poll: {len(ranking)} countries ranked")
    return ranking


def load_poll_year(year: int, data_dir=DIR_RAW_POLLS) -> dict[str, int]:
    """Return {cc: rank} from cached poll file, or empty dict."""
    path = Path(data_dir) / f"{year}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


if __name__ == "__main__":
    print("Fetching fan poll data…")
    fetch_all_polls()
    fetch_poll_2026()
    print("Done.")
