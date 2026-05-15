"""
Song language per Eurovision year — 1 = primarily English, 0 = native/other.
Sources: Eurovision official site, wiki.
Only finale participants listed; missing entries default to 0.
"""

SONG_LANGUAGE: dict[int, dict[str, int]] = {
    2016: {
        "AM": 1, "AT": 1, "AU": 1, "AZ": 0, "BE": 1, "BG": 1,
        "CY": 1, "CZ": 1, "DE": 1, "EE": 1, "FR": 0, "GB": 1,
        "GE": 0, "GR": 0, "HR": 1, "HU": 0, "IE": 1, "IL": 1,
        "IS": 1, "IT": 0, "LT": 1, "LV": 1, "ME": 0, "MT": 1,
        "NO": 1, "PL": 0, "RO": 0, "RS": 1, "RU": 0, "SE": 1,
        "SI": 1, "SM": 1, "UA": 0, "UK": 1,
    },
    2017: {
        "AL": 0, "AM": 1, "AT": 1, "AU": 1, "AZ": 1, "BE": 1,
        "BG": 1, "BY": 0, "CH": 1, "CY": 1, "CZ": 1, "DE": 1,
        "DK": 1, "EE": 1, "FI": 1, "FR": 0, "GB": 1, "GR": 1,
        "HR": 1, "HU": 0, "IE": 1, "IL": 1, "IS": 1, "IT": 0,
        "LT": 0, "ME": 1, "MK": 0, "MT": 1, "NO": 1, "PL": 1,
        "PT": 0, "RO": 0, "RS": 0, "SE": 1, "SM": 1, "UK": 1,
    },
    2018: {
        "AL": 0, "AT": 1, "AU": 1, "AZ": 1, "BE": 1, "BG": 1,
        "BY": 0, "CH": 1, "CY": 1, "CZ": 1, "DE": 1, "DK": 1,
        "EE": 1, "ES": 0, "FI": 1, "FR": 1, "GB": 1, "GR": 1,
        "HR": 1, "HU": 1, "IE": 1, "IL": 1, "IT": 0, "LT": 1,
        "LV": 0, "MD": 0, "ME": 0, "MK": 0, "MT": 1, "NO": 1,
        "PL": 1, "PT": 0, "RO": 0, "RS": 0, "SE": 1, "SI": 1,
        "SK": 0, "UA": 1, "UK": 1,
    },
    2019: {
        "AL": 0, "AM": 1, "AT": 1, "AU": 1, "AZ": 1, "BE": 1,
        "CH": 1, "CY": 1, "CZ": 1, "DE": 1, "DK": 1, "EE": 0,
        "ES": 0, "FI": 1, "FR": 0, "GB": 1, "GR": 1, "HR": 1,
        "HU": 1, "IL": 0, "IS": 0, "IT": 0, "LT": 1, "LV": 0,
        "MD": 0, "ME": 1, "MK": 0, "MT": 1, "NO": 1, "PL": 1,
        "PT": 0, "RO": 0, "RS": 0, "RU": 1, "SE": 1, "SI": 1,
        "SM": 1, "UK": 1,
    },
    2021: {
        "AL": 0, "AT": 0, "AU": 1, "AZ": 1, "BE": 1, "BG": 0,
        "CH": 1, "CY": 1, "DE": 1, "EE": 1, "ES": 0, "FI": 1,
        "FR": 0, "GB": 1, "GE": 0, "GR": 1, "HR": 0, "IE": 1,
        "IL": 1, "IS": 0, "IT": 0, "LT": 0, "MD": 0, "MT": 1,
        "NO": 1, "PT": 0, "RO": 0, "RS": 0, "RU": 0, "SE": 1,
        "SI": 0, "SM": 1, "UA": 0, "UK": 1,
    },
    2022: {
        "AL": 0, "AT": 1, "AU": 1, "AZ": 1, "BE": 1, "BG": 0,
        "CH": 0, "CY": 1, "CZ": 1, "DE": 1, "EE": 1, "ES": 0,
        "FI": 1, "FR": 0, "GB": 1, "GR": 1, "HR": 0, "IS": 0,
        "IT": 0, "LT": 1, "LV": 0, "MD": 0, "ME": 0, "MT": 1,
        "NO": 1, "PL": 0, "PT": 0, "RO": 0, "RS": 0, "SE": 1,
        "SI": 1, "SM": 1, "UA": 0, "UK": 1,
    },
    2023: {
        "AL": 0, "AM": 0, "AT": 1, "AU": 1, "AZ": 1, "BE": 1,
        "CH": 1, "CY": 1, "CZ": 1, "DE": 1, "EE": 1, "ES": 0,
        "FI": 0, "FR": 0, "GB": 1, "GE": 0, "GR": 1, "HR": 0,
        "IL": 1, "IS": 1, "IT": 0, "LT": 1, "MD": 0, "ME": 1,
        "MT": 1, "NO": 1, "PL": 1, "PT": 0, "RO": 0, "RS": 0,
        "SE": 1, "SI": 0, "SM": 1, "UA": 0, "UK": 1,
    },
    2024: {
        "AL": 0, "AM": 1, "AT": 1, "AU": 1, "AZ": 1, "BE": 1,
        "CH": 0, "CY": 1, "CZ": 1, "DE": 1, "DK": 1, "EE": 1,
        "ES": 0, "FI": 1, "FR": 0, "GB": 1, "GE": 0, "GR": 1,
        "HR": 0, "IE": 1, "IL": 1, "IS": 0, "IT": 0, "LT": 0,
        "LU": 0, "LV": 0, "MD": 0, "MT": 1, "NO": 1, "PL": 1,
        "PT": 0, "RS": 0, "SE": 1, "SI": 1, "SM": 1, "UA": 0,
        "UK": 1,
    },
    2025: {
        "AL": 0, "AM": 0, "AT": 0, "AU": 1, "AZ": 1, "BE": 1,
        "CH": 0, "CY": 1, "CZ": 1, "DE": 1, "DK": 1, "EE": 1,
        "ES": 0, "FI": 0, "FR": 0, "GB": 1, "GE": 0, "GR": 1,
        "IE": 1, "IL": 1, "IS": 0, "IT": 0, "LT": 1, "LU": 1,
        "LV": 0, "MD": 0, "MT": 1, "NO": 1, "PL": 1, "PT": 0,
        "RS": 0, "SE": 0, "SI": 0, "SM": 0, "UA": 0, "UK": 1,
    },
}

# 2026 finale entries
SONG_LANGUAGE_2026: dict[str, int] = {
    # 1=Englisch, 0=andere Sprache
    "AL": 0,  # "Nân"             – Albanisch
    "AM": 1,  # Nicht-Finalist    – Englisch (Fallback)
    "AT": 0,  # "Tanzschein"      – Deutsch
    "AU": 1,  # "Eclipse"         – Englisch
    "AZ": 1,  # Nicht-Finalist
    "BE": 1,  # "Dancing on the Ice" – Englisch
    "BG": 0,  # "Bangaranga"      – Bulgarisch
    "CH": 1,  # Nicht-Finalist
    "CY": 1,  # "Jalla"           – Englisch/Mix
    "CZ": 1,  # "Crossroads"      – Englisch
    "DE": 1,  # "Fire"            – Englisch
    "DK": 0,  # "Før vi går hjem" – Dänisch
    "EE": 1,  # Nicht-Finalist
    "FI": 0,  # "Liekinheitin"    – Finnisch
    "FR": 0,  # "Regarde !"       – Französisch
    "GB": 0,  # "Eins, Zwei, Drei"– Deutsch
    "GE": 0,  # Nicht-Finalist
    "GR": 0,  # "Ferto"           – Griechisch
    "HR": 0,  # "Andromeda"       – Kroatisch
    "IL": 1,  # "Michelle"        – Englisch
    "IT": 0,  # "Per sempre sì"   – Italienisch
    "LT": 0,  # "Sólo quiero más" – Spanisch
    "LU": 1,  # Nicht-Finalist
    "LV": 0,  # Nicht-Finalist
    "MD": 0,  # "Viva, Moldova"   – Rumänisch
    "ME": 0,  # Nicht-Finalist
    "MT": 1,  # "Bella"           – Englisch
    "NO": 1,  # "Ya ya ya"        – Englisch
    "PL": 1,  # "Pray"            – Englisch
    "PT": 0,  # Nicht-Finalist
    "RO": 1,  # "Choke Me"        – Englisch
    "RS": 0,  # "Kraj mene"       – Serbisch
    "SE": 1,  # "My System"       – Englisch
    "SM": 1,  # Nicht-Finalist
    "UA": 0,  # "Ridnym"          – Ukrainisch
}


def song_language(year: int) -> dict[str, int]:
    if year == 2026:
        return SONG_LANGUAGE_2026
    return SONG_LANGUAGE.get(year, {})
