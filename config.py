"""Central configuration: API keys, constants, 2026 contest entries."""
import os
from pathlib import Path

# Project root = directory containing this file
_ROOT = Path(__file__).parent

# ── API credentials ──────────────────────────────────────────────────────────
# Set these as environment variables or fill in here.
SPOTIFY_CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
YOUTUBE_API_KEY       = os.getenv("YOUTUBE_API_KEY", "")

# ── Training years ────────────────────────────────────────────────────────────
# Nur 2021–2025: getrennte Jury- UND Tele-Wettquoten verfügbar (eurovisionworld.com)
# 2016–2019 weggelassen: nur kombinierte Odds → inkonsistent mit Jury/Tele-Split
# 2020 entfällt (COVID-Absage)
YEARS_TRAIN = [2021, 2022, 2023, 2024, 2025]

# ── Data paths (absolute, always relative to project root) ───────────────────
DIR_RAW_VOTING  = str(_ROOT / "data" / "raw" / "voting")
DIR_RAW_POLLS   = str(_ROOT / "data" / "raw" / "polls")
DIR_RAW_SPOTIFY = str(_ROOT / "data" / "raw" / "spotify")
DIR_PROCESSED   = str(_ROOT / "data" / "processed")
DIR_PREDICTIONS = str(_ROOT / "data" / "predictions")

# ── EurovisionAPI (GitHub raw, no auth needed) ────────────────────────────────
EUROVISION_API_BASE = (
    "https://raw.githubusercontent.com/EurovisionAPI/dataset/main/data/senior"
)

# ── Eurovision 2026 Grand Final entries (25 Länder, Wien) ─────────────────────
# Auto-Qualifier (Big 5 + Gastgeber Österreich): AT, FR, DE, IT, GB
# Halbfinale 1 (12. Mai): GR, FI, BE, SE, MD, IL, RS, HR, LT, PL qualifiziert
# Halbfinale 2 (14. Mai): BG, UA, NO, AU, RO, MT, CY, AL, DK, CZ qualifiziert
# Ausgeschieden (stimmen im Finale aber ab): AM, AZ, EE, GE, LV, LU, ME, PT, SM, CH
VOTERS_ONLY_2026 = ["AM", "AZ", "EE", "GE", "LV", "LU", "ME", "PT", "SM", "CH"]
ENTRIES_2026 = [
    {"country": "Albania",        "code": "AL", "artist": "Alis",                             "song": "Nân"},
    {"country": "Australia",      "code": "AU", "artist": "Delta Goodrem",                    "song": "Eclipse"},
    {"country": "Austria",        "code": "AT", "artist": "Cosmó",                            "song": "Tanzschein"},
    {"country": "Belgium",        "code": "BE", "artist": "Essyla",                           "song": "Dancing on the Ice"},
    {"country": "Bulgaria",       "code": "BG", "artist": "Dara",                             "song": "Bangaranga"},
    {"country": "Croatia",        "code": "HR", "artist": "Lelek",                            "song": "Andromeda"},
    {"country": "Cyprus",         "code": "CY", "artist": "Antigoni",                         "song": "Jalla"},
    {"country": "Czechia",        "code": "CZ", "artist": "Daniel Žižka",                     "song": "Crossroads"},
    {"country": "Denmark",        "code": "DK", "artist": "Søren Torpegaard Lund",            "song": "Før vi går hjem"},
    {"country": "Finland",        "code": "FI", "artist": "Linda Lampenius & Pete Parkkonen", "song": "Liekinheitin"},
    {"country": "France",         "code": "FR", "artist": "Monroe",                           "song": "Regarde !"},
    {"country": "Germany",        "code": "DE", "artist": "Sarah Engels",                     "song": "Fire"},
    {"country": "Greece",         "code": "GR", "artist": "Akylas",                           "song": "Ferto"},
    {"country": "Israel",         "code": "IL", "artist": "Noam Bettan",                      "song": "Michelle"},
    {"country": "Italy",          "code": "IT", "artist": "Sal Da Vinci",                     "song": "Per sempre sì"},
    {"country": "Lithuania",      "code": "LT", "artist": "Lion Ceccah",                      "song": "Sólo quiero más"},
    {"country": "Malta",          "code": "MT", "artist": "Aidan",                            "song": "Bella"},
    {"country": "Moldova",        "code": "MD", "artist": "Satoshi",                          "song": "Viva, Moldova"},
    {"country": "Norway",         "code": "NO", "artist": "Jonas Lovv",                       "song": "Ya ya ya"},
    {"country": "Poland",         "code": "PL", "artist": "Alicja",                           "song": "Pray"},
    {"country": "Romania",        "code": "RO", "artist": "Alexandra Căpitănescu",            "song": "Choke Me"},
    {"country": "Serbia",         "code": "RS", "artist": "Lavina",                           "song": "Kraj mene"},
    {"country": "Sweden",         "code": "SE", "artist": "Felicia",                          "song": "My System"},
    {"country": "Ukraine",        "code": "UA", "artist": "Leléka",                           "song": "Ridnym"},
    {"country": "United Kingdom", "code": "GB", "artist": "Look Mum No Computer",             "song": "Eins, Zwei, Drei"},
]

# Startreihenfolge 2026 Grand Final (16. Mai, Wiener Stadthalle)
RUNNING_ORDER_2026 = {
    "DK":  1,  "DE":  2,  "IL":  3,  "BE":  4,  "AL":  5,
    "GR":  6,  "UA":  7,  "AU":  8,  "RS":  9,  "MT": 10,
    "CZ": 11,  "BG": 12,  "HR": 13,  "GB": 14,  "FR": 15,
    "MD": 16,  "FI": 17,  "PL": 18,  "LT": 19,  "SE": 20,
    "CY": 21,  "IT": 22,  "NO": 23,  "RO": 24,  "AT": 25,
}

# SF-Ränge 2026 (normiert): SF-Qualifier bekommen 0.75, Auto-Qualifier 0.5
# Exakte Ränge innerhalb des SFs nicht verfügbar → einheitlicher Qualifier-Bonus
SF_RANK_2026 = {
    # Auto-Qualifier (kein SF)
    "AT": 0.5, "FR": 0.5, "DE": 0.5, "IT": 0.5, "GB": 0.5,
    # SF1-Qualifier (12. Mai)
    "GR": 0.75, "FI": 0.75, "BE": 0.75, "SE": 0.75, "MD": 0.75,
    "IL": 0.75, "RS": 0.75, "HR": 0.75, "LT": 0.75, "PL": 0.75,
    # SF2-Qualifier (14. Mai)
    "BG": 0.75, "UA": 0.75, "NO": 0.75, "AU": 0.75, "RO": 0.75,
    "MT": 0.75, "CY": 0.75, "AL": 0.75, "DK": 0.75, "CZ": 0.75,
}

# ISO-3166 alpha-2 → display name mapping (superset, covers all voter countries)
COUNTRY_NAMES = {
    "AL": "Albania", "AM": "Armenia", "AU": "Australia", "AT": "Austria",
    "AZ": "Azerbaijan", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia",
    "CY": "Cyprus", "CZ": "Czechia", "DK": "Denmark", "EE": "Estonia",
    "FI": "Finland", "FR": "France", "GE": "Georgia", "DE": "Germany",
    "GR": "Greece", "HU": "Hungary", "IS": "Iceland", "IE": "Ireland",
    "IL": "Israel", "IT": "Italy", "LV": "Latvia", "LT": "Lithuania",
    "LU": "Luxembourg", "MT": "Malta", "MD": "Moldova", "MC": "Monaco",
    "ME": "Montenegro", "NL": "Netherlands", "MK": "North Macedonia",
    "NO": "Norway", "PL": "Poland", "PT": "Portugal", "RO": "Romania",
    "SM": "San Marino", "RS": "Serbia", "SI": "Slovenia", "ES": "Spain",
    "SE": "Sweden", "CH": "Switzerland", "UA": "Ukraine", "GB": "United Kingdom",
}
