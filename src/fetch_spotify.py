"""
Fetch Spotify audio features for Eurovision entries using the Web API.

Requires:  SPOTIFY_CLIENT_ID  and  SPOTIFY_CLIENT_SECRET  (env vars or config.py).
Uses Client Credentials flow – no user login needed.

Audio features stored per country per year:
  danceability, energy, valence, tempo, acousticness,
  instrumentalness, liveness, speechiness, loudness, key, mode
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, DIR_RAW_SPOTIFY


class SpotifyClient:
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE  = "https://api.spotify.com/v1"

    def __init__(self):
        self._token: str | None = None

    def _authenticate(self):
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            raise RuntimeError(
                "Spotify credentials missing. Set SPOTIFY_CLIENT_ID and "
                "SPOTIFY_CLIENT_SECRET as environment variables."
            )
        r = requests.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
            timeout=10,
        )
        r.raise_for_status()
        self._token = r.json()["access_token"]

    def _get(self, path: str, **params) -> dict:
        if not self._token:
            self._authenticate()
        r = requests.get(
            f"{self.API_BASE}/{path}",
            headers={"Authorization": f"Bearer {self._token}"},
            params=params,
            timeout=10,
        )
        if r.status_code == 401:
            self._authenticate()
            return self._get(path, **params)
        r.raise_for_status()
        return r.json()

    def search_track(self, artist: str, song: str) -> str | None:
        """Return Spotify track ID for the best match, or None."""
        query = f"track:{song} artist:{artist}"
        data = self._get("search", q=query, type="track", limit=1, market="DE")
        items = data.get("tracks", {}).get("items", [])
        return items[0]["id"] if items else None

    def audio_features(self, track_id: str) -> dict:
        data = self._get(f"audio-features/{track_id}")
        return {
            "danceability":     data.get("danceability", 0),
            "energy":           data.get("energy", 0),
            "valence":          data.get("valence", 0),
            "tempo":            data.get("tempo", 0),
            "acousticness":     data.get("acousticness", 0),
            "instrumentalness": data.get("instrumentalness", 0),
            "liveness":         data.get("liveness", 0),
            "speechiness":      data.get("speechiness", 0),
            "loudness":         data.get("loudness", 0),
            "key":              data.get("key", -1),
            "mode":             data.get("mode", 0),
            "duration_ms":      data.get("duration_ms", 0),
        }


_client = SpotifyClient()


def fetch_features_for_year(
    year: int,
    meta: dict[str, dict],
    output_dir=DIR_RAW_SPOTIFY,
    force=False,
) -> dict[str, dict]:
    """
    Fetch Spotify audio features for all countries in `meta` for `year`.
    `meta` is {country_code: {artist, song, …}}.
    Results cached at data/raw/spotify/{year}.json.
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
        artist = info.get("artist", "")
        song   = info.get("song", "")
        try:
            track_id = _client.search_track(artist, song)
            if track_id:
                features = _client.audio_features(track_id)
                features["track_id"] = track_id
                cached[cc] = features
                print(f"    {year}/{cc}: {song!r} -> {track_id}")
            else:
                print(f"    {year}/{cc}: not found on Spotify")
                cached[cc] = {}
            changed = True
        except Exception as e:
            print(f"    {year}/{cc}: error – {e}")
        time.sleep(0.15)

    if changed:
        path.write_text(json.dumps(cached, indent=2), encoding="utf-8")
    return cached


def load_spotify(year: int, data_dir=DIR_RAW_SPOTIFY) -> dict[str, dict]:
    path = Path(data_dir) / f"{year}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


AUDIO_FEATURE_COLS = [
    "danceability", "energy", "valence", "tempo",
    "acousticness", "instrumentalness", "liveness",
    "speechiness", "loudness", "key", "mode",
]


if __name__ == "__main__":
    from fetch_contestants import fetch_all_meta
    print("Fetching Spotify audio features…")
    all_meta = fetch_all_meta()
    for year, meta in all_meta.items():
        print(f"  {year}…")
        fetch_features_for_year(year, meta)
    print("Done.")
