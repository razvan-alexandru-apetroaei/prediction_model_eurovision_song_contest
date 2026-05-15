"""
Historische pre-finale Wettquoten (Median über alle verfügbaren Bookmaker).
Quelle: eurovisionworld.com/odds

Getrennte Jury- und Televote-Odds verfügbar: 2021, 2022, 2023, 2024, 2025
Nur kombinierte Odds (Fallback):             2016, 2017, 2018, 2019

Verwendung:
    from data_odds_history import odds_jury_prob, odds_tele_prob, odds_win_prob
    jury = odds_jury_prob(2025)   # {cc: prob}  – Jury-Wettquoten
    tele = odds_tele_prob(2025)   # {cc: prob}  – Tele-Wettquoten
    win  = odds_win_prob(2025)    # {cc: prob}  – kombiniert (Fallback / Legacy)
"""

# ── Getrennte Jury-Wettquoten 2021–2025 (eurovisionworld.com/odds/eurovision-YEAR-jury)
HISTORICAL_JURY_ODDS: dict[int, dict[str, float]] = {

    2021: {
        "FR": 2.31,  "MT": 3.69,  "CH": 5.48,  "IT": 14.27, "PT": 16.45,
        "BG": 16.91, "IS": 21.36, "UA": 27.64, "SE": 46.45, "CY": 46.27,
        "FI": 59.09, "LT": 90.09, "GR": 101.45,"RU": 101.45,"BE": 103.55,
        "AZ": 101.45,"SM": 109.09,"IL": 127.36, "NO": 133.36,"MD": 133.36,
        "NL": 151.45,"GB": 179.09,"RS": 176.27, "AL": 176.27,"DE": 186.36,
        "ES": 186.36,
    },

    2022: {
        "GB": 2.81,  "UA": 3.71,  "SE": 3.70,  "IT": 7.61,  "PL": 17.67,
        "ES": 25.33, "AU": 35.67, "GR": 35.67, "NL": 38.33, "RS": 58.00,
        "PT": 69.00, "AZ": 74.33, "NO": 68.33, "CH": 75.00, "FR": 97.33,
        "CZ": 116.67,"BE": 108.67,"FI": 116.33,"MD": 126.33,"AM": 127.67,
        "EE": 130.00,"IS": 147.33,"LT": 180.33,"RO": 215.00,"DE": 311.00,
    },

    2023: {
        "SE": 1.25,  "FR": 7.00,  "ES": 9.00,  "IT": 15.00, "FI": 18.00,
        "CH": 30.00, "IL": 35.00, "UA": 40.00, "NO": 40.00, "AM": 50.00,
        "EE": 50.00, "AT": 65.00, "GB": 100.00,"CZ": 100.00,"SI": 200.00,
        "CY": 150.00,"BE": 150.00,"MD": 200.00,"HR": 200.00,"DE": 200.00,
        "AU": 200.00,"RS": 250.00,"PL": 250.00,"PT": 250.00,"LT": 250.00,
        "AL": 350.00,
    },

    2024: {
        "CH": 1.70,  "FR": 3.00,  "IT": 8.50,  "HR": 8.00,  "IL": 15.00,
        "UA": 50.00, "AM": 35.00, "SE": 150.00,"RS": 100.00,"GR": 100.00,
        "NO": 150.00,"IE": 250.00,"PT": 200.00,"GE": 200.00,"EE": 85.00,
        "GB": 250.00,"DE": 250.00,"LV": 50.00, "LT": 250.00,"AT": 150.00,
        "FI": 250.00,"SI": 300.00,"CY": 300.00,"LU": 250.00,"ES": 250.00,
    },

    2025: {
        "AT": 1.80,  "FR": 2.50,  "CH": 6.00,  "NL": 8.00,  "SE": 15.00,
        "AL": 60.00, "IT": 51.00, "IL": 41.00, "GR": 60.00, "FI": 60.00,
        "EE": 70.00, "GB": 80.00, "ES": 101.00,"UA": 90.00, "MT": 101.00,
        "LU": 101.00,"SM": 101.00,"PL": 101.00,"DK": 151.00,"LV": 101.00,
        "DE": 101.00,"PT": 251.00,"NO": 251.00,"IS": 251.00,"LT": 251.00,
        "AM": 251.00,
    },
}

# ── Getrennte Televote-Wettquoten 2021–2025 (eurovisionworld.com/odds/eurovision-YEAR-tele)
HISTORICAL_TELE_ODDS: dict[int, dict[str, float]] = {

    2021: {
        "IT": 2.45,  "UA": 3.35,  "FI": 8.50,  "FR": 10.00, "IS": 9.00,
        "MT": 18.00, "SM": 30.00, "CH": 25.00, "LT": 50.00, "NO": 75.00,
        "RS": 75.00, "CY": 100.00,"PT": 100.00,"BG": 85.00, "GR": 125.00,
        "AZ": 125.00,"RU": 125.00,"SE": 125.00,"MD": 150.00,"ES": 200.00,
        "DE": 250.00,"GB": 250.00,"IL": 250.00,"AL": 300.00,"NL": 300.00,
        "BE": 250.00,
    },

    2022: {
        "UA": 1.14,  "ES": 19.00, "SE": 17.00, "GB": 21.00, "MD": 29.00,
        "NO": 34.00, "IT": 34.00, "RS": 29.00, "PL": 41.00, "GR": 41.00,
        "NL": 51.00, "AU": 81.00, "CZ": 51.00, "FI": 67.00, "EE": 151.00,
        "PT": 101.00,"FR": 67.00, "AM": 151.00,"AZ": 151.00,"RO": 251.00,
        "BE": 251.00,"CH": 251.00,"IS": 251.00,"LT": 251.00,"DE": 401.00,
    },

    2023: {
        "FI": 1.40,  "UA": 4.85,  "SE": 5.00,  "NO": 20.00, "IL": 30.00,
        "HR": 50.00, "AT": 65.00, "DE": 60.00, "FR": 90.00, "CZ": 85.00,
        "IT": 125.00,"MD": 125.00,"ES": 100.00,"PL": 150.00,"BE": 150.00,
        "GB": 175.00,"AM": 200.00,"RS": 200.00,"AU": 200.00,"LT": 250.00,
        "CH": 200.00,"CY": 250.00,"EE": 250.00,"SI": 300.00,"PT": 300.00,
        "AL": 500.00,
    },

    2024: {
        "IL": 1.45,  "HR": 2.75,  "UA": 10.00, "IE": 30.00, "CH": 50.00,
        "FI": 60.00, "IT": 65.00, "FR": 100.00,"GR": 100.00,"AM": 100.00,
        "AT": 150.00,"NO": 150.00,"LT": 150.00,"SE": 150.00,"GE": 150.00,
        "ES": 200.00,"RS": 150.00,"EE": 200.00,"GB": 200.00,"CY": 200.00,
        "DE": 300.00,"SI": 300.00,"LU": 200.00,"PT": 300.00,"LV": 250.00,
    },

    2025: {
        "SE": 1.40,  "IL": 5.50,  "EE": 6.00,  "FI": 7.50,  "AT": 21.00,
        "AL": 51.00, "NL": 26.00, "FR": 26.00, "PL": 101.00,"UA": 101.00,
        "MT": 101.00,"DE": 151.00,"CH": 151.00,"ES": 201.00,"LT": 201.00,
        "IT": 201.00,"SM": 251.00,"GB": 501.00,"IS": 101.00,"GR": 251.00,
        "DK": 251.00,"LV": 251.00,"NO": 251.00,"LU": 251.00,"PT": 251.00,
        "AM": 251.00,
    },
}

# ── Kombinierte Gewinnquoten (Legacy + Fallback für 2016–2019) ────────────────
# Median Decimal Odds pro Land pro Jahr (pre-Final)
HISTORICAL_ODDS: dict[int, dict[str, float]] = {

    2016: {
        "RU": 1.85,  "AU": 2.85,  "UA": 11.0,  "SE": 17.0,
        "FR": 18.0,  "MT": 25.0,  "AM": 30.0,  "GB": 60.0,
        "NL": 55.0,  "BE": 65.0,  "LV": 65.0,  "IL": 80.0,
        "AT": 80.0,  "BG": 100.0, "ES": 100.0, "PL": 100.0,
        "RS": 100.0, "IT": 65.0,  "CY": 150.0, "LT": 150.0,
        "AZ": 200.0, "HU": 200.0, "HR": 200.0, "CZ": 200.0,
        "DE": 230.0, "GE": 225.0,
    },

    2017: {
        "BG": 2.73,  "PT": 2.79,  "IT": 7.34,  "BE": 8.31,
        "RO": 20.1,  "SE": 24.6,  "HR": 41.1,  "MD": 52.3,
        "GB": 52.4,  "AM": 120.1, "NO": 117.3, "FR": 106.4,
        "NL": 139.6, "AU": 156.1, "DK": 157.1, "AZ": 165.4,
        "HU": 182.4, "DE": 217.1, "PL": 226.1, "GR": 248.1,
        "AT": 250.1, "BY": 265.6, "CY": 282.4, "UA": 350.4,
        "IL": 387.3, "ES": 449.4,
    },

    2018: {
        "CY": 2.10,  "IL": 3.10,  "DE": 8.00,  "IE": 18.0,
        "LT": 30.0,  "IT": 25.0,  "EE": 25.0,  "SE": 35.0,
        "NO": 35.0,  "FI": 50.0,  "GB": 50.0,  "FR": 50.0,
        "MD": 50.0,  "DK": 65.0,  "CZ": 70.0,  "AU": 75.0,
        "HU": 90.0,  "BG": 100.0, "AT": 125.0, "ES": 125.0,
        "NL": 150.0, "UA": 150.0, "SI": 200.0, "PT": 250.0,
        "AL": 400.0, "RS": 500.0,
    },

    2019: {
        "NL": 1.55,  "IT": 6.00,  "CH": 8.00,  "AU": 13.0,
        "SE": 15.0,  "AZ": 20.0,  "NO": 20.0,  "IS": 35.0,
        "RU": 45.0,  "FR": 60.0,  "CY": 100.0, "DK": 100.0,
        "EE": 100.0, "ES": 125.0, "MK": 150.0, "CZ": 150.0,
        "MT": 150.0, "GR": 150.0, "RS": 200.0, "GB": 200.0,
        "SI": 200.0, "BY": 200.0, "IL": 300.0, "AL": 300.0,
        "DE": 400.0, "SM": 400.0,
    },

    2021: {
        "IT": 3.25,  "FR": 3.75,  "MT": 5.00,  "FI": 13.0,
        "IS": 17.0,  "UA": 13.0,  "CH": 17.0,  "LT": 41.0,
        "SE": 41.0,  "SM": 67.0,  "NO": 67.0,  "PT": 81.0,
        "BG": 85.0,  "CY": 101.0, "AZ": 126.0, "GR": 151.0,
        "RS": 151.0, "IL": 251.0, "NL": 251.0, "BE": 301.0,
        "GB": 301.0, "MD": 501.0, "DE": 501.0, "ES": 501.0,
        "AL": 501.0,
    },

    2022: {
        "UA": 1.29,  "SE": 6.25,  "ES": 10.5,  "GB": 13.0,
        "IT": 34.0,  "NO": 67.0,  "PL": 67.0,  "RS": 67.0,
        "GR": 81.0,  "MD": 81.0,  "NL": 101.0, "FI": 126.0,
        "AU": 200.0, "EE": 201.0, "CZ": 251.0, "PT": 251.0,
        "AM": 251.0, "DE": 301.0, "FR": 276.0, "AZ": 301.0,
        "IS": 301.0, "RO": 301.0, "CH": 351.0, "BE": 401.0,
        "LT": 301.0,
    },

    2023: {
        "SE": 1.62,  "FI": 3.25,  "IL": 13.0,  "UA": 21.0,
        "IT": 24.0,  "NO": 26.0,  "FR": 67.0,  "BE": 81.0,
        "GB": 81.0,  "ES": 101.0, "PL": 101.0, "HR": 101.0,
        "AU": 151.0, "AT": 151.0, "CH": 151.0, "AM": 151.0,
        "CY": 151.0, "DE": 251.0, "CZ": 201.0, "EE": 201.0,
        "MD": 251.0, "LT": 501.0, "SI": 251.0, "PT": 501.0,
        "RS": 501.0, "AL": 501.0,
    },

    2024: {
        "HR": 1.57,  "IL": 5.00,  "CH": 5.50,  "FR": 15.0,
        "IE": 29.0,  "UA": 51.0,  "FI": 57.0,  "IT": 67.0,
        "GR": 151.0, "AT": 151.0, "GB": 151.0, "SE": 201.0,
        "LT": 201.0, "NO": 201.0, "AM": 201.0, "GE": 251.0,
        "CY": 251.0, "EE": 251.0, "DE": 301.0, "PT": 401.0,
        "LV": 401.0, "LU": 401.0, "RS": 401.0,
    },

    2025: {
        "SE": 1.62,  "AT": 4.00,  "FR": 11.5,  "FI": 17.0,
        "EE": 30.0,  "NL": 40.0,  "AL": 51.0,  "CH": 61.0,
        "IL": 61.0,  "MT": 81.0,  "IT": 101.0, "DE": 126.0,
        "DK": 151.0, "GB": 151.0, "GR": 151.0, "UA": 151.0,
        "IS": 151.0, "LU": 176.0, "SM": 201.0, "PL": 201.0,
        "LV": 201.0, "NO": 201.0, "LT": 201.0, "AM": 251.0,
        "PT": 251.0,
    },
}


def _to_prob(raw: dict[str, float]) -> dict[str, float]:
    """Decimal Odds → faire Gewinnwahrscheinlichkeit (Marge entfernt)."""
    if not raw:
        return {}
    inv = {cc: 1.0 / o for cc, o in raw.items() if o > 0}
    total = sum(inv.values())
    return {cc: p / total for cc, p in inv.items()}


def odds_jury_prob(year: int) -> dict[str, float]:
    """Jury-Wettquoten → Wahrscheinlichkeiten. Leer wenn keine getrennten Daten."""
    return _to_prob(HISTORICAL_JURY_ODDS.get(year, {}))


def odds_tele_prob(year: int) -> dict[str, float]:
    """Televote-Wettquoten → Wahrscheinlichkeiten. Leer wenn keine getrennten Daten."""
    return _to_prob(HISTORICAL_TELE_ODDS.get(year, {}))


def odds_win_prob(year: int) -> dict[str, float]:
    """
    Kombinierte Gewinnquoten → Wahrscheinlichkeit (Legacy/Fallback).
    Für 2021–2025: nutze odds_jury_prob / odds_tele_prob stattdessen.
    """
    raw = HISTORICAL_ODDS.get(year, {})
    if not raw:
        return {}
    return _to_prob(raw)
