"""
2026 Eurovision market signals – Stand: 14. Mai 2026.

Enthält:
  1. Wettquoten (decimal odds, Durchschnitt aus 15 Bookmaker-Quellen)
     → werden in Gewinnwahrscheinlichkeiten umgerechnet (Buchmacher-Marge entfernt)

  2. Rehearsal Press Scores (wiwibloggs.com, Durchschnitt der Journalistenbewertungen)
     → Skala 1–10; 0 = noch nicht verfügbar
"""

# ── Getrennte Jury- und Televote-Wettquoten ───────────────────────────────────
# Stand: 15. Mai 2026 – Durchschnitt aus 12 Bookmaker-Quellen:
# Betsson, Unibet, Bet365, EpicBet, Bwin, CoolBet,
# Ladbrokes, Boyle Sports, 7Bet, William Hill, Betfred, Betway
# Quelle: eurovisionworld.com/odds/eurovision-jury
#         eurovisionworld.com/odds/eurovision-tele

# Jury-Odds: wer gewinnt die Jury-Abstimmung?
ODDS_JURY_2026: dict[str, float] = {
    "AU":  2.6,   # Australien      – JURY-FAVORIT (30%)
    "FI":  4.6,   # Finnland        – (17%)
    "FR":  5.2,   # Frankreich      – (15%)
    "DK":  5.8,   # Dänemark        – (13%)
    "CZ":  8.7,   # Tschechien      – (9%)
    "GR": 29.0,   # Griechenland    – (3%)
    "MT": 32.9,   # Malta           – (2%)
    "RO": 46.6,   # Rumänien        – (2%)
    "IT": 54.8,   # Italien         – (1%)
    "HR": 59.6,   # Kroatien        – (1%)
    "SE": 60.7,   # Schweden        – (1%)
    "UA": 66.2,   # Ukraine         – (1%)
    "BG": 85.2,   # Bulgarien       – (1%)
    "CY": 121.7,  # Zypern
    "IL": 132.1,  # Israel
    "AL": 132.5,  # Albanien
    "GB": 170.8,  # Großbritannien
    "MD": 234.2,  # Moldawien
    "LT": 238.3,  # Litauen
    "NO": 250.8,  # Norwegen
    "BE": 263.3,  # Belgien
    "RS": 271.7,  # Serbien
    "PL": 275.8,  # Polen
    "DE": 334.2,  # Deutschland
    "AT": 392.5,  # Österreich
    # Nicht-Finalisten
    "GE": 501.0, "EE": 501.0, "ME": 501.0,
    "PT": 501.0, "SM": 501.0, "AM": 501.0,
    "LU": 501.0, "CH": 501.0, "LV": 501.0, "AZ": 501.0,
}

# Televote-Odds: wer gewinnt die Televoting-Abstimmung?
ODDS_TELE_2026: dict[str, float] = {
    "IL":  1.86,  # Israel          – TELE-FAVORIT (40%)
    "GR":  4.62,  # Griechenland    – (16%)
    "FI":  6.04,  # Finnland        – (12%)
    "RO": 11.25,  # Rumänien        – (7%)
    "MD": 14.58,  # Moldawien       – (5%)
    "BG": 21.08,  # Bulgarien       – (4%)
    "UA": 23.00,  # Ukraine         – (3%)
    "IT": 26.42,  # Italien         – (3%)
    "DK": 52.33,  # Dänemark
    "FR": 54.25,  # Frankreich
    "AU": 59.42,  # Australien
    "SE": 61.17,  # Schweden
    "CY": 70.42,  # Zypern
    "HR": 83.33,  # Kroatien
    "MT": 103.33, # Malta
    "CZ": 161.67, # Tschechien
    "RS": 163.33, # Serbien
    "GB": 173.75, # Großbritannien
    "DE": 198.75, # Deutschland
    "AL": 199.17, # Albanien
    "NO": 209.17, # Norwegen
    "PL": 221.67, # Polen
    "LT": 225.83, # Litauen
    "BE": 288.33, # Belgien
    "AT": 300.83, # Österreich
    # Nicht-Finalisten
    "GE": 501.0, "EE": 501.0, "ME": 501.0,
    "PT": 501.0, "SM": 501.0, "AM": 501.0,
    "LU": 501.0, "CH": 501.0, "LV": 501.0, "AZ": 501.0,
}

# Allgemeine Gewinnquoten (Fallback, falls jury/tele nicht separat verfügbar)
ODDS_WIN_2026 = ODDS_JURY_2026  # nicht mehr primär verwendet

# ── Rehearsal Press Scores (wiwibloggs.com + escxtra.com) ────────────────────
# Durchschnitt der Journalistenbewertungen nach den Generalproben
# Skala: 1.0 (schlecht) bis 10.0 (perfekt), 0.0 = noch nicht verfügbar
# Stand: wird nach den Finalproben (ca. 15.-16. Mai) befüllt
REHEARSAL_SCORES_2026: dict[str, float] = {
    "AL": 0.0, "AM": 0.0, "AU": 0.0, "AT": 0.0, "AZ": 0.0,
    "BE": 0.0, "BG": 0.0, "HR": 0.0, "CY": 0.0, "CZ": 0.0,
    "DK": 0.0, "EE": 0.0, "FI": 0.0, "FR": 0.0, "GE": 0.0,
    "DE": 0.0, "GR": 0.0, "IL": 0.0, "IT": 0.0, "LV": 0.0,
    "LT": 0.0, "LU": 0.0, "MT": 0.0, "MD": 0.0, "ME": 0.0,
    "NO": 0.0, "PL": 0.0, "PT": 0.0, "RO": 0.0, "SM": 0.0,
    "RS": 0.0, "SE": 0.0, "CH": 0.0, "UA": 0.0, "GB": 0.0,
}


# ─────────────────────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────────────────────────────────────────

def odds_to_prob(odds_dict: dict[str, float]) -> dict[str, float]:
    """
    Decimal odds → faire Gewinnwahrscheinlichkeit (Buchmacher-Marge entfernt).
    Länder mit Odds=0 werden übersprungen.
    Rückgabe: {cc: prob} normalisiert auf Summe=1.
    """
    raw = {cc: 1.0 / o for cc, o in odds_dict.items() if o > 0}
    if not raw:
        return {}
    total = sum(raw.values())
    return {cc: p / total for cc, p in raw.items()}


def rehearsal_score_norm(scores: dict[str, float]) -> dict[str, float]:
    """Normalisiert Rehearsal Scores auf [0, 1]. Fehlende = 0.5 (neutral)."""
    known = {cc: s for cc, s in scores.items() if s > 0}
    if not known:
        return {cc: 0.5 for cc in scores}
    max_s = max(known.values())
    min_s = min(known.values())
    rng = max_s - min_s if max_s > min_s else 1.0
    result = {}
    for cc in scores:
        s = scores.get(cc, 0.0)
        if s > 0:
            result[cc] = (s - min_s) / rng
        else:
            result[cc] = 0.5
    return result


def get_market_data(finalists: list[str]) -> dict:
    """
    Gibt aufbereitete Market-Signale zurück.
    Verwendet getrennte Jury- und Televote-Odds.
    """
    jury_probs  = odds_to_prob(ODDS_JURY_2026)
    tele_probs  = odds_to_prob(ODDS_TELE_2026)
    rehearsal   = rehearsal_score_norm(REHEARSAL_SCORES_2026)

    n = len(finalists)
    result = {}
    for cc in finalists:
        result[cc] = {
            "odds_win_prob":        jury_probs.get(cc, 1.0 / n),  # Fallback für alten Code
            "odds_jury_prob":       jury_probs.get(cc, 1.0 / n),
            "odds_tele_prob":       tele_probs.get(cc, 1.0 / n),
            "rehearsal_score_norm": rehearsal.get(cc, 0.5),
        }
    return result


if __name__ == "__main__":
    probs = odds_to_prob(ODDS_WIN_2026)
    if probs:
        print("Gewinnwahrscheinlichkeiten (aus Wettquoten):")
        for cc, p in sorted(probs.items(), key=lambda x: -x[1]):
            print(f"  {cc}: {p*100:.1f}%")
    else:
        print("Noch keine Odds eingetragen.")

    known_r = {cc: s for cc, s in REHEARSAL_SCORES_2026.items() if s > 0}
    if known_r:
        rehearsal = rehearsal_score_norm(REHEARSAL_SCORES_2026)
        print(f"\nRehearsal Scores ({len(known_r)} Länder bekannt):")
        for cc, s in sorted(known_r.items(), key=lambda x: -x[1]):
            print(f"  {cc}: {s:.1f}/10  (norm={rehearsal[cc]:.3f})")
    else:
        print("\nNoch keine Rehearsal Scores eingetragen.")
