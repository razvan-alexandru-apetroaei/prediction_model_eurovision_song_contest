"""
Eurojury (Euro Jury) Jury-Vote-Ergebnisse für ESC Grand Finals 2016–2026.
Quelle: eurovoix.com – jährliche Abstimmung von ~35-43 nationalen Jurys
bestehend aus ehemaligen ESC-Teilnehmern und Eurovision-Enthusiasten.

Verwendung:
    from data_eurojury import eurojury_score
    scores = eurojury_score(2022)  # {cc: normalised_score [0,1]}

Verfügbar: 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2026
Nicht verfügbar: 2025 (Eurojury pausierte 2025 – kein Wettbewerb)

Datenquelle:
  2016-2022: manuell aus eurovoix.com
  2023: Excel-Datei von eurovoix.com (43 Jurys, Jury-Vote-Total)
  2024: Excel-Datei von eurovoix.com (Jury-Vote-Total)
  2026: aussievision.net (35 Jurys, Jury-Vote)

Hinweis: enthält alle teilnehmenden Länder (inkl. Halbfinal-Ausscheider).
Für das Modell werden nur Finalisten des jeweiligen Jahres verwendet.
"""

EUROJURY_HISTORY: dict[int, dict[str, int]] = {

    2016: {
        "FR": 344, "AU": 342, "ES": 282, "SE": 264, "UA": 263,
        "RU": 226, "BG": 224, "MT": 216, "BE": 178, "HR": 177,
        "NL": 174, "IT": 148, "GB": 137, "CZ": 123, "LV": 117,
        "AZ": 115, "AM": 108, "CY": 105, "RS": 100, "IS": 92,
        "IL": 88,  "PL": 80,  "NO": 75,  "EE": 66,  "HU": 64,
        "AT": 63,  "LT": 55,  "DE": 55,  "DK": 54,  "SM": 28,
        "BY": 21,  "GR": 17,  "AL": 15,  "MD": 10,  "ME": 9,
        "GE": 38,  # Georgia in 2016 Eurojury
    },

    2017: {
        "IT": 401, "SE": 271, "BE": 245, "AU": 243, "PT": 225,
        "BG": 214, "NL": 162, "FR": 152, "AT": 142, "HR": 126,
        "GB": 125, "DK": 124, "AZ": 122, "FI": 113, "ES": 100,
        "CH": 97,  "NO": 85,  "RS": 75,  "IL": 66,  "AL": 65,
        "LV": 64,  "MD": 60,  "CZ": 57,  "HU": 53,  "RU": 51,
        "PL": 48,  "MT": 47,  "CY": 47,  "RO": 42,  "EE": 40,
        "ME": 39,  "GR": 35,  "GE": 34,  "UA": 33,  "AM": 30,
        "LT": 24,  "DE": 23,  "SM": 22,  "SI": 20,  "BY": 90,
        "IS": 62,  "MK": 107,
    },

    2018: {
        "IL": 393, "CZ": 261, "BG": 246, "FR": 228, "CY": 204,
        "EE": 203, "SE": 199, "AU": 192, "FI": 181, "BE": 166,
        "AT": 128, "DE": 107, "DK": 107, "CH": 105, "GR": 104,
        "NO": 103, "IT": 98,  "PT": 59,  "ES": 50,  "NL": 47,
        "LV": 46,  "HU": 46,  "LT": 43,  "GB": 41,  "UA": 39,
        "MT": 39,  "AL": 35,  "IE": 34,  "RS": 12,  "PL": 11,
        "AZ": 11,  "MD": 1,   "SI": 16,  "SM": 13,
    },

    2019: {
        "SE": 202, "NL": 192, "IT": 171, "CH": 106, "GR": 101,
        "AM": 94,  "RU": 92,  "GB": 85,  "FR": 79,  "AZ": 72,
        "CZ": 71,  "MT": 67,  "CY": 66,  "DK": 66,  "BE": 50,
        "NO": 45,  "IS": 37,  "EE": 35,  "ES": 34,  "SI": 33,
        "PT": 31,  "LV": 29,  "IL": 29,  "RS": 29,  "HU": 28,
        "RO": 17,  "AU": 16,  "FI": 14,  "PL": 14,  "DE": 9,
        "AL": 6,   "AT": 6,   "SM": 0,   "ME": 0,   "LT": 0,
        "GE": 4,   "MK": 43,
    },

    2021: {
        "MT": 286, "CH": 257, "FR": 219, "IL": 210, "IS": 204,
        "IT": 163, "SE": 127, "CY": 123, "BG": 107, "FI": 77,
        "GB": 76,  "PT": 74,  "DE": 68,  "LT": 60,  "AZ": 58,
        "UA": 56,  "ES": 49,  "GR": 44,  "NO": 44,  "NL": 31,
        "SM": 29,  "BE": 24,  "RU": 20,  "RS": 13,  "MD": 7,
        "AL": 4,
    },

    2022: {
        "GB": 287, "IT": 240, "SE": 192, "UA": 182, "ES": 175,
        "AU": 137, "BE": 123, "FI": 111, "NL": 104, "CH": 89,
        "NO": 88,  "GR": 87,  "FR": 86,  "AM": 73,  "PT": 63,
        "RS": 60,  "PL": 49,  "AZ": 35,  "EE": 33,  "DE": 29,
        "IS": 29,  "MD": 20,  "CZ": 19,  "LT": 14,  "RO": 0,
    },

    # 2023: Jury-Vote-Total (43 Jurys). Quelle: eurovoix.com Excel
    2023: {
        "SE": 354, "FR": 237, "IT": 186, "GB": 124, "NO": 117,
        "ES": 110, "CH": 109, "BE": 104, "CY": 101, "FI": 93,
        "AT": 82,  "IL": 78,  "NL": 74,  "DK": 72,  "CZ": 60,
        "UA": 60,  "AM": 58,  "MT": 56,  "IE": 48,  "AU": 42,
        "DE": 36,  "GR": 28,  "EE": 26,  "PL": 26,  "AZ": 25,
        "RS": 25,  "PT": 25,  "SI": 24,  "HR": 24,  "LV": 22,
        "GE": 22,  "IS": 16,  "LT": 13,  "MD": 8,   "AL": 8,
        "RO": 1,   "SM": 0,
    },

    # 2024: Jury-Vote-Total. Quelle: eurovoix.com Excel
    2024: {
        "FR": 295, "IT": 288, "CH": 280, "BE": 189, "DE": 154,
        "HR": 152, "IL": 110, "GR": 83,  "AM": 81,  "GB": 76,
        "DK": 74,  "RS": 71,  "NL": 70,  "SE": 68,  "UA": 62,
        "GE": 61,  "ES": 56,  "CZ": 55,  "AL": 50,  "AT": 46,
        "NO": 37,  "PT": 36,  "IE": 34,  "LV": 34,  "PL": 26,
        "AZ": 25,  "CY": 13,  "IS": 12,  "MD": 10,  "EE": 9,
        "LU": 9,   "MT": 9,   "LT": 8,   "SI": 8,   "SM": 7,
        "AU": 6,   "FI": 6,
    },

    # 2025: Eurojury pausierte – kein Wettbewerb 2025

    # 2026: Jury-Vote (35 Jurys). Quelle: aussievision.net
    2026: {
        "DK": 213, "FI": 197, "AU": 184, "GR": 171, "FR": 158,
        "CY": 117, "SE": 99,  "IT": 93,  "AL": 86,  "CZ": 73,
        "HR": 70,  "IL": 57,  "RO": 51,  "MD": 50,  "MT": 44,
        "BG": 44,  "CH": 43,  "NO": 42,  "LU": 38,  "PL": 37,
        "AM": 30,  "BE": 28,  "DE": 27,  "GE": 26,  "LT": 20,
        "UA": 20,  "ME": 18,  "EE": 13,  "PT": 11,  "AZ": 11,
        "RS": 9,   "GB": 4,   "AT": 3,   "SM": 1,   "LV": 0,
    },
}


def eurojury_score(year: int) -> dict[str, float]:
    """
    Gibt {cc: normalisierter_Score [0,1]} zurück.
    Leeres Dict wenn keine Daten verfügbar (2023+).
    """
    raw = EUROJURY_HISTORY.get(year, {})
    if not raw:
        return {}
    max_pts = max(raw.values(), default=1)
    if max_pts == 0:
        return {cc: 0.0 for cc in raw}
    return {cc: pts / max_pts for cc, pts in raw.items()}
