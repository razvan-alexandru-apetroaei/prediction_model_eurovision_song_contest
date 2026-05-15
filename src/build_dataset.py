"""
Feature engineering: combine all signal groups into training matrix.

One row = (year, round, from_country, to_country).

Signal groups
-------------
[A] HISTORICAL VOTING + GEO PROXIMITY
    jury_bias_3y      – avg jury pts from->to last 3 years (all rounds)
    tele_bias_3y      – avg televote pts from->to last 3 years
    jury_bias_5y      – same, 5 years
    tele_bias_5y      – same, 5 years
    ever_gave_12_jury – from ever gave 12 jury pts to to?
    ever_gave_12_tele – same for televote
    geo_proximity     – exp(-dist_km/1500): cultural/diaspora proximity

[B] COMMUNITY POLL
    poll_score_norm   – normalised OGAE score [0,1]
    poll_top3         – binary: in top 3 of poll?

[C] YOUTUBE / STREAMING
    log_views         – log10(YouTube views + 1)
    views_rank_norm   – view count rank normalised [0,1]

[E] CONTEST CONTEXT
    running_order_norm – position in final / n_finalists
    sf_pts_norm        – semi-final total pts / max SF pts (0.5 = auto-qualifier)
    is_english         – 1 if song primarily in English, 0 otherwise

Targets: jury_pts, tele_pts
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from config import DIR_RAW_VOTING, DIR_PROCESSED, YEARS_TRAIN
from fetch_voting import build_long_table

FEATURE_GROUPS = {
    "A_historical_voting": [
        "jury_bias_3y", "tele_bias_3y",
        "jury_bias_5y", "tele_bias_5y",
        "ever_gave_12_jury", "ever_gave_12_tele",
        "geo_proximity",
        "diaspora_norm",
    ],
    "B_community_poll": [
        "poll_score_norm",
        "poll_top3",
    ],
    "C_youtube": [
        "log_views",
        "views_rank_norm",
    ],
    "E_contest_context": [
        "running_order_norm",
        "running_order_late",  # Bonus für späte Slots (pimp-slot Effekt, letzte 25%)
        "is_english",
        "hist_tele_norm",
        "hist_jury_norm",
        "sf_rank_norm",      # Halbfinal-Rang normiert (1.0=Sieger, 0.5=Auto-Qualifier)
    ],
    "G_eurojury": [
        "eurojury_norm",     # Eurojury-Score normiert [0,1]
        "eurojury_top3",     # Binary: Top-3 in Eurojury
    ],
}
FEATURE_COLS = [f for cols in FEATURE_GROUPS.values() for f in cols]


# ─────────────────────────────────────────────────────────────────────────────
# [A] Bilateral voting history + geo proximity
# ─────────────────────────────────────────────────────────────────────────────

def _bilateral_history(rows: list[dict], target_year: int) -> dict[tuple, dict]:
    from data_geo import get_proximity
    from data_diaspora import diaspora_score
    encounters: dict[tuple, dict[tuple, dict]] = defaultdict(dict)
    for row in rows:
        if row["year"] >= target_year:
            continue
        key = (row["from_country"], row["to_country"])
        enc_key = (row["year"], row.get("round", "final"))
        existing = encounters[key].get(enc_key)
        if existing is None or row["jury_pts"] + row["tele_pts"] > existing["jury"] + existing["tele"]:
            encounters[key][enc_key] = {
                "jury": row["jury_pts"],
                "tele": row["tele_pts"],
                "year": row["year"],
            }

    result = {}
    for pair, enc_map in encounters.items():
        all_enc = list(enc_map.values())
        biases = {}
        for w in [3, 5]:
            recent = [e for e in all_enc if e["year"] >= target_year - w]
            if recent:
                biases[f"jury_bias_{w}y"] = sum(e["jury"] for e in recent) / len(recent)
                biases[f"tele_bias_{w}y"] = sum(e["tele"] for e in recent) / len(recent)
            else:
                biases[f"jury_bias_{w}y"] = 0.0
                biases[f"tele_bias_{w}y"] = 0.0
        biases["ever_gave_12_jury"] = int(any(e["jury"] == 12 for e in all_enc))
        biases["ever_gave_12_tele"] = int(any(e["tele"] == 12 for e in all_enc))
        biases["geo_proximity"]  = get_proximity(pair[0], pair[1])
        biases["diaspora_norm"]  = diaspora_score(pair[0], pair[1])
        result[pair] = biases
    return result


def _default_bilateral(from_cc: str, to_cc: str) -> dict:
    from data_geo import get_proximity
    from data_diaspora import diaspora_score
    return {
        "jury_bias_3y": 0.0, "tele_bias_3y": 0.0,
        "jury_bias_5y": 0.0, "tele_bias_5y": 0.0,
        "ever_gave_12_jury": 0, "ever_gave_12_tele": 0,
        "geo_proximity": get_proximity(from_cc, to_cc),
        "diaspora_norm": diaspora_score(from_cc, to_cc),
    }


# ─────────────────────────────────────────────────────────────────────────────
# [B] Community poll
# ─────────────────────────────────────────────────────────────────────────────

def _load_poll(year: int) -> dict[str, float]:
    if year == 2026:
        from data_2026 import combined_poll_score_2026
        return combined_poll_score_2026()
    from data_polls import ogae_poll_score
    return ogae_poll_score(year)


def _poll_features(year: int, all_ccs: list[str]) -> dict[str, dict]:
    scores = _load_poll(year)
    top3 = set(sorted(scores, key=scores.get, reverse=True)[:3])
    max_score = max(scores.values(), default=1)
    result = {}
    for cc in all_ccs:
        s = scores.get(cc, 0.0)
        result[cc] = {
            "poll_score_norm": s / max(max_score, 1e-9),
            "poll_top3":       int(cc in top3),
        }
    return result


# ─────────────────────────────────────────────────────────────────────────────
# [C] YouTube
# ─────────────────────────────────────────────────────────────────────────────

def _load_youtube(year: int, all_ccs: list[str]) -> dict[str, dict]:
    if year == 2026:
        from data_2026 import YOUTUBE_VIEWS_2026 as raw
        views = {cc: raw.get(cc, 0) for cc in all_ccs}
    else:
        yt_dir = Path(DIR_RAW_VOTING).parent / "youtube"
        path   = yt_dir / f"{year}.json"
        if path.exists():
            cached = json.loads(path.read_text())
            views = {cc: cached.get(cc, {}).get("view_count", 0) for cc in all_ccs}
        else:
            views = {cc: 0 for cc in all_ccs}

    sorted_ccs = sorted(all_ccs, key=lambda c: views.get(c, 0), reverse=True)
    n = max(len(sorted_ccs), 1)
    rank_map = {cc: (n - i) / n for i, cc in enumerate(sorted_ccs)}

    return {
        cc: {
            "log_views":       math.log10(views.get(cc, 0) + 1),
            "views_rank_norm": rank_map.get(cc, 0.0),
        }
        for cc in all_ccs
    }


# ─────────────────────────────────────────────────────────────────────────────
# [E] Contest context
# ─────────────────────────────────────────────────────────────────────────────

def _sf_points(year: int, all_ccs: list[str], all_rows: list[dict]) -> dict[str, float]:
    """
    Normalised semi-final total points per country.
    Auto-qualifiers (Big 5 + host, no SF data) get 0.5 as neutral.
    """
    sf_rows = [r for r in all_rows
               if r["year"] == year and r.get("round", "final") in ("semifinal1", "semifinal2")]
    if not sf_rows:
        return {cc: 0.5 for cc in all_ccs}

    totals: dict[str, int] = defaultdict(int)
    for r in sf_rows:
        totals[r["to_country"]] += r["jury_pts"] + r["tele_pts"]

    max_pts = max(totals.values(), default=1)
    result = {}
    for cc in all_ccs:
        if cc in totals:
            result[cc] = totals[cc] / max_pts
        else:
            result[cc] = 0.5  # auto-qualifier
    return result


def _running_orders(year: int, all_rows: list[dict]) -> dict[str, dict]:
    """
    Normalised running position in the final.
    Rückgabe: {cc: {"running_order_norm": float, "running_order_late": float}}
      - running_order_norm: lineare Position (0=erster, 1=letzter)
      - running_order_late: Pimp-Slot-Bonus – letzte 25% → [0,1], Rest → 0
        (bekannter Eurovision-Effekt: späte Slots performen beim Televote besser)

    Für 2026: Startreihenfolge aus config.RUNNING_ORDER_2026 (bekannt).
    """
    if year == 2026:
        from config import RUNNING_ORDER_2026
        order_map: dict[str, int] = RUNNING_ORDER_2026
    else:
        final_rows = [r for r in all_rows
                      if r["year"] == year and r.get("round", "final") == "final"]
        if not final_rows:
            return {}
        order_map = {}
        for r in final_rows:
            cc = r["to_country"]
            if cc not in order_map:
                order_map[cc] = r.get("running_order", 0)

    n = max(order_map.values(), default=1)
    result = {}
    threshold = 0.75 * n   # ab Slot 75% = "späte Zone"
    for cc, pos in order_map.items():
        norm = pos / max(n, 1)
        late = max(0.0, (pos - threshold) / max(n - threshold, 1))
        result[cc] = {"running_order_norm": norm, "running_order_late": late}
    return result


def _historical_performance(target_year: int, all_rows: list[dict]) -> dict[str, dict]:
    """
    Average jury and tele totals per country in finals before target_year.
    Normalised by max across all countries.
    Countries that rarely appear get lower scores (not inflated by absences).
    """
    from collections import defaultdict
    finals = [r for r in all_rows
              if r["year"] < target_year and r.get("round", "final") == "final"]

    cc_years: dict[str, dict[int, dict]] = defaultdict(dict)
    for r in finals:
        cc = r["to_country"]
        y  = r["year"]
        if y not in cc_years[cc]:
            cc_years[cc][y] = {"jury": 0, "tele": 0}
        cc_years[cc][y]["jury"] += r["jury_pts"]
        cc_years[cc][y]["tele"] += r["tele_pts"]

    # Average over years the country actually appeared
    avgs: dict[str, dict] = {}
    for cc, ymap in cc_years.items():
        avgs[cc] = {
            "jury": sum(v["jury"] for v in ymap.values()) / len(ymap),
            "tele": sum(v["tele"] for v in ymap.values()) / len(ymap),
        }

    max_jury = max((v["jury"] for v in avgs.values()), default=1)
    max_tele = max((v["tele"] for v in avgs.values()), default=1)
    return {
        cc: {
            "hist_jury_norm": v["jury"] / max_jury,
            "hist_tele_norm": v["tele"] / max_tele,
        }
        for cc, v in avgs.items()
    }


def _language_features(year: int, all_ccs: list[str]) -> dict[str, int]:
    from data_language import song_language
    lang = song_language(year)
    return {cc: lang.get(cc, 0) for cc in all_ccs}


# ─────────────────────────────────────────────────────────────────────────────
# [E] Halbfinal-Rang (aus rohen JSON-Dateien)
# ─────────────────────────────────────────────────────────────────────────────

def _sf_rank_features(year: int, all_ccs: list[str]) -> dict[str, float]:
    """
    Liest den Halbfinal-Rang direkt aus den rohen JSON-Dateien.
    Rückgabe: {cc: sf_rank_norm} wobei 1.0 = Sieger, ~0.0 = letzter Platz.
    Auto-Qualifier (Big 5 + Gastgeber) erhalten 0.5 als neutralen Wert.
    Für 2026: verwendet SF_RANK_2026 aus config.py (manuelle SF-Ergebnisse).
    """
    # 2026: SF-Ergebnisse manuell aus config.py
    if year == 2026:
        from config import SF_RANK_2026
        return {cc: SF_RANK_2026.get(cc, 0.5) for cc in all_ccs}

    raw_dir = Path(DIR_RAW_VOTING)
    # Lade Contestant-Mapping: {id_str: cc}
    cont_file = raw_dir / f"{year}_contestants.json"
    if not cont_file.exists():
        return {cc: 0.5 for cc in all_ccs}
    contestants = json.loads(cont_file.read_text())

    result: dict[str, float] = {}
    for sf in ("semifinal1", "semifinal2"):
        sf_file = raw_dir / f"{year}_{sf}.json"
        if not sf_file.exists():
            continue
        sf_data = json.loads(sf_file.read_text())
        perfs = sf_data.get("performances", [])
        n = len(perfs)
        for p in perfs:
            cid = str(p["contestantId"])
            cc = contestants.get(cid, contestants.get(int(cid) if cid.isdigit() else cid))
            if cc and cc not in result:
                rank = p.get("place", n)
                result[cc] = (n - rank) / max(n - 1, 1)   # 1.0 = Platz 1

    # Auto-Qualifier bekommen neutralen Wert 0.5
    return {cc: result.get(cc, 0.5) for cc in all_ccs}


# ─────────────────────────────────────────────────────────────────────────────
# [G] Eurojury
# ─────────────────────────────────────────────────────────────────────────────

def _eurojury_features(year: int, all_ccs: list[str]) -> dict[str, dict]:
    """
    Eurojury-Score für alle Finalisten.
    Verfügbar: 2016-2022. Fehlende Jahre → alle Werte 0.
    """
    from data_eurojury import eurojury_score
    scores = eurojury_score(year)
    if not scores:
        return {cc: {"eurojury_norm": 0.0, "eurojury_top3": 0} for cc in all_ccs}
    top3 = set(sorted(scores, key=scores.get, reverse=True)[:3])
    max_s = max(scores.values(), default=1)
    return {
        cc: {
            "eurojury_norm":  scores.get(cc, 0.0) / max(max_s, 1e-9),
            "eurojury_top3":  int(cc in top3),
        }
        for cc in all_ccs
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main build
# ─────────────────────────────────────────────────────────────────────────────

def build_training_data(years=None, output_dir=DIR_PROCESSED) -> pd.DataFrame:
    if years is None:
        years = YEARS_TRAIN
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    all_rows = build_long_table(years)
    records  = []

    for year in years:
        year_rows = [r for r in all_rows if r["year"] == year]
        if not year_rows:
            continue

        all_ccs  = list({r["to_country"] for r in year_rows})
        bilateral = _bilateral_history(all_rows, target_year=year)
        poll      = _poll_features(year, all_ccs)
        youtube   = _load_youtube(year, all_ccs)
        running   = _running_orders(year, all_rows)
        language  = _language_features(year, all_ccs)
        hist_perf = _historical_performance(year, all_rows)
        sf_rank   = _sf_rank_features(year, all_ccs)
        eurojury  = _eurojury_features(year, all_ccs)

        for row in year_rows:
            from_cc = row["from_country"]
            to_cc   = row["to_country"]
            if from_cc == to_cc:
                continue

            bil = bilateral.get((from_cc, to_cc), _default_bilateral(from_cc, to_cc))

            rec = {
                "year":         year,
                "round":        row.get("round", "final"),
                "from_country": from_cc,
                "to_country":   to_cc,
                # [A]
                "jury_bias_3y":      bil["jury_bias_3y"],
                "tele_bias_3y":      bil["tele_bias_3y"],
                "jury_bias_5y":      bil["jury_bias_5y"],
                "tele_bias_5y":      bil["tele_bias_5y"],
                "ever_gave_12_jury": bil["ever_gave_12_jury"],
                "ever_gave_12_tele": bil["ever_gave_12_tele"],
                "geo_proximity":     bil["geo_proximity"],
                "diaspora_norm":     bil["diaspora_norm"],
                # [B]
                **poll.get(to_cc, {"poll_score_norm": 0.0, "poll_top3": 0}),
                # [C]
                **youtube.get(to_cc, {"log_views": 0.0, "views_rank_norm": 0.0}),
                # [E]
                **running.get(to_cc, {"running_order_norm": 0.5, "running_order_late": 0.0}),
                "is_english":         language.get(to_cc, 0),
                "hist_tele_norm":     hist_perf.get(to_cc, {}).get("hist_tele_norm", 0.0),
                "hist_jury_norm":     hist_perf.get(to_cc, {}).get("hist_jury_norm", 0.0),
                "sf_rank_norm":       sf_rank.get(to_cc, 0.5),
                # [G]
                **eurojury.get(to_cc, {"eurojury_norm": 0.0, "eurojury_top3": 0}),
                # targets
                "jury_pts": row["jury_pts"],
                "tele_pts": row["tele_pts"],
            }
            records.append(rec)

    df = pd.DataFrame(records)
    out = Path(output_dir) / "training_data.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df):,} rows -> {out}")
    return df


def build_prediction_rows(
    voting_countries: list[str],
    candidate_countries: list[str],
    bilateral:  dict[tuple, dict],
    poll:       dict[str, dict],
    youtube:    dict[str, dict],
    running:    dict[str, dict],
    language:   dict[str, int],
    hist_perf:  dict[str, dict],
    sf_rank:    dict[str, float] | None = None,
    eurojury:   dict[str, dict]  | None = None,
) -> pd.DataFrame:
    """Feature matrix for prediction (2026 or hindcast)."""
    records = []
    for from_cc in voting_countries:
        for to_cc in candidate_countries:
            if from_cc == to_cc:
                continue
            bil = bilateral.get((from_cc, to_cc), _default_bilateral(from_cc, to_cc))
            rec = {
                "from_country": from_cc,
                "to_country":   to_cc,
                "jury_bias_3y":      bil["jury_bias_3y"],
                "tele_bias_3y":      bil["tele_bias_3y"],
                "jury_bias_5y":      bil["jury_bias_5y"],
                "tele_bias_5y":      bil["tele_bias_5y"],
                "ever_gave_12_jury": bil["ever_gave_12_jury"],
                "ever_gave_12_tele": bil["ever_gave_12_tele"],
                "geo_proximity":     bil["geo_proximity"],
                "diaspora_norm":     bil["diaspora_norm"],
                **poll.get(to_cc,    {"poll_score_norm": 0.0, "poll_top3": 0}),
                **youtube.get(to_cc, {"log_views": 0.0, "views_rank_norm": 0.0}),
                **running.get(to_cc, {"running_order_norm": 0.5, "running_order_late": 0.0}),
                "is_english":         language.get(to_cc, 0),
                "hist_tele_norm":     hist_perf.get(to_cc, {}).get("hist_tele_norm", 0.0),
                "hist_jury_norm":     hist_perf.get(to_cc, {}).get("hist_jury_norm", 0.0),
                "sf_rank_norm":       (sf_rank or {}).get(to_cc, 0.5),
                **((eurojury or {}).get(to_cc, {"eurojury_norm": 0.0, "eurojury_top3": 0})),
            }
            records.append(rec)
    return pd.DataFrame(records)


if __name__ == "__main__":
    df = build_training_data()
    print("\nFeature means by signal group:")
    for group, cols in FEATURE_GROUPS.items():
        present = [c for c in cols if c in df.columns]
        print(f"  [{group}]: {df[present].mean().round(3).to_dict()}")
    print("\nTarget distributions:")
    print(f"  jury_pts:  mean={df['jury_pts'].mean():.2f}, std={df['jury_pts'].std():.2f}")
    print(f"  tele_pts:  mean={df['tele_pts'].mean():.2f}, std={df['tele_pts'].std():.2f}")
