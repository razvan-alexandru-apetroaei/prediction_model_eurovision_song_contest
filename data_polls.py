"""
Complete OGAE poll data for all training years (2016-2025, excl. 2020).
Source: eurovisionworld.com / OGAE official results
Points = raw OGAE network points (sum across ~37-43 national fan clubs).
Countries not listed received 0 points.
"""

OGAE_HISTORY: dict[int, dict[str, int]] = {
    2016: {
        "FR": 425, "RU": 392, "AU": 280, "BG": 175, "IT": 170,
        "ES": 155, "AT": 128, "LV": 110, "UA": 88,  "HU": 80,
        "SE": 79,  "HR": 63,  "CY": 59,  "IS": 44,  "RS": 42,
        "CZ": 36,  "AZ": 35,  "EE": 31,  "PL": 28,  "NO": 15,
        "AM": 13,  "IE": 8,   "SI": 6,   "MK": 6,   "MT": 6,
        "LT": 6,   "SM": 4,   "DE": 4,   "BE": 4,   "IL": 2,
    },
    2017: {
        "IT": 497, "BE": 335, "SE": 308, "FR": 277, "EE": 242,
        "PT": 122, "BG": 120, "MK": 107, "IL": 102, "FI": 64,
        "DK": 43,  "CH": 41,  "HU": 40,  "AU": 36,  "AZ": 34,
        "NO": 30,  "RO": 18,  "ME": 17,  "BY": 15,  "AT": 14,
        "CY": 13,  "LV": 12,  "GB": 12,  "IS": 9,   "AM": 7,
        "HR": 6,   "GR": 6,   "SM": 5,   "IE": 4,   "GE": 4,
        "PL": 4,   "NL": 3,   "RS": 3,   "CZ": 2,
        "AL": 0,   "DE": 0,   "LT": 0,   "MT": 0,   "MD": 0,
        "RU": 0,   "SI": 0,   "ES": 0,   "UA": 0,
    },
    2018: {
        "IL": 456, "FR": 352, "FI": 226, "AU": 202, "CZ": 181,
        "BG": 178, "BE": 143, "GR": 119, "CY": 106, "DK": 99,
        "SE": 91,  "EE": 88,  "IT": 75,  "AT": 70,  "DE": 34,
        "BY": 28,  "ES": 26,  "UA": 19,  "MK": 15,  "NO": 13,
        "PL": 5,   "IE": 5,   "LT": 5,   "AZ": 4,   "GB": 4,
        "LV": 3,   "MD": 2,   "RS": 2,   "RU": 1,
    },
    2019: {
        "IT": 411, "CH": 406, "NL": 401, "NO": 224, "CY": 218,
        "SE": 191, "AZ": 123, "IS": 114, "RU": 106, "GR": 89,
        "ES": 69,  "MT": 64,  "FR": 25,  "SM": 23,  "SI": 22,
        "DK": 19,  "PT": 19,  "BE": 17,  "MK": 13,  "AL": 10,
        "AM": 9,   "EE": 7,   "PL": 7,   "CZ": 6,   "GB": 6,
        "IL": 5,   "AU": 2,   "HU": 2,   "LV": 2,
    },
    # 2020 skipped (COVID cancellation)
    2021: {
        "MT": 363, "CH": 358, "FR": 318, "LT": 301, "CY": 238,
        "SM": 237, "SE": 105, "IT": 81,  "UA": 64,  "AZ": 59,
        "GR": 58,  "IS": 50,  "RO": 38,  "FI": 37,  "DK": 32,
        "HR": 30,  "RU": 23,  "NO": 19,  "MD": 17,  "IL": 14,
        "RS": 11,  "IE": 10,  "BG": 7,   "BE": 7,   "AU": 4,
        "GB": 4,   "EE": 4,   "LV": 3,   "ES": 1,
    },
    2022: {
        "SE": 393, "IT": 387, "ES": 294, "NL": 218, "GB": 204,
        "FR": 175, "PL": 144, "NO": 120, "AL": 88,  "AT": 73,
        "UA": 60,  "CY": 59,  "EE": 54,  "RS": 53,  "GR": 38,
        "FI": 37,  "CZ": 35,  "AU": 16,  "LT": 11,  "PT": 9,
        "LV": 7,   "MD": 6,   "HR": 4,   "BE": 2,   "DE": 2,
        "MT": 2,   "RO": 2,   "CH": 1,
    },
    2023: {
        "SE": 423, "FI": 394, "FR": 302, "NO": 263, "AT": 228,
        "IT": 226, "GB": 154, "CZ": 91,  "IL": 83,  "ES": 76,
        "SI": 34,  "MD": 32,  "CH": 23,  "BE": 21,  "RS": 17,
        "CY": 14,  "PT": 14,  "AM": 7,   "EE": 6,   "NL": 5,
        "LT": 5,   "AZ": 4,   "AU": 3,   "GE": 3,   "PL": 2,
        "DE": 2,   "MT": 2,   "HR": 1,   "GR": 1,
    },
    2024: {
        "HR": 356, "IT": 338, "CH": 290, "BE": 223, "FR": 188,
        "UA": 150, "AT": 129, "LT": 108, "ES": 103, "NL": 96,
        "GR": 91,  "GB": 81,  "SE": 59,  "IL": 53,  "NO": 43,
        "DK": 12,  "LU": 12,  "SI": 10,  "RS": 7,   "AU": 5,
        "EE": 5,   "CY": 4,   "AZ": 3,   "AM": 2,   "GE": 1,
        "PL": 1,
    },
    2025: {
        "SE": 421, "AT": 382, "NL": 278, "FI": 253, "MT": 164,
        "AL": 158, "FR": 137, "ES": 136, "EE": 85,  "NO": 71,
        "IL": 58,  "GR": 57,  "DE": 44,  "CH": 44,  "LU": 39,
        "SM": 36,  "CZ": 34,  "DK": 31,  "BE": 17,  "AU": 15,
        "PL": 8,   "IT": 8,   "GB": 7,   "IE": 6,   "LV": 2,
        "SI": 1,   "UA": 1,   "LT": 1,
    },
}


def ogae_poll_score(year: int) -> dict[str, float]:
    """
    Return {cc: normalised_score [0,1]} for the given year.
    Score = raw OGAE points / max points that year.
    Countries not in the poll get 0.0.
    """
    raw = OGAE_HISTORY.get(year, {})
    if not raw:
        return {}
    max_pts = max(raw.values(), default=1)
    return {cc: pts / max_pts for cc, pts in raw.items()}
