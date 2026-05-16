"""
2026 Eurovision market signals – Stand: 15. Mai 2026 (Finaltag, aktuellste Quoten).

Enthält:
  1. Wettquoten (decimal odds, Durchschnitt aus 11 Bookmaker-Quellen)
     → werden in Gewinnwahrscheinlichkeiten umgerechnet (Buchmacher-Marge entfernt)

  2. Rehearsal Press Scores (wiwibloggs.com, Durchschnitt der Journalistenbewertungen)
     → Skala 1–10; 0 = noch nicht verfügbar
"""

# ── Getrennte Jury- und Televote-Wettquoten ───────────────────────────────────
# Stand: 15. Mai 2026 (Finaltag) – Durchschnitt aus 11 Bookmaker-Quellen:
# Betsson, Bwin, Bet365, Epic Bet, Ladbrokes, Unibet,
# 7Bet, Boyle Sports, Cool Bet, Betway, William Hill
# Quelle: eurovisionworld.com/odds/eurovision-jury
#         eurovisionworld.com/odds/eurovision-tele

# Jury-Odds: wer gewinnt die Jury-Abstimmung?
# Ø aus 4 Bookmarkern: Betsson, 7Bet, Ladbrokes, Betway
ODDS_JURY_2026: dict[str, float] = {
    "AU":   1.80,  # Australien      – JURY-FAVORIT (42%)
    "FI":   4.00,  # Finnland        – (19%)
    "DK":   8.50,  # Dänemark        – (9%)
    "FR":   8.50,  # Frankreich      – (9%)
    "CZ":   9.00,  # Tschechien      – (8%)
    "MT":  40.25,  # Malta           – (2%)
    "GR":  42.75,  # Griechenland    – (2%)
    "RO":  53.25,  # Rumänien        – (1%)
    "HR":  66.00,  # Kroatien        – (1%)
    "IT":  66.50,  # Italien         – (1%)
    "SE":  81.00,  # Schweden        – (1%)
    "UA":  86.00,  # Ukraine         – (1%)
    "BG":  91.00,  # Bulgarien       – (1%)
    "CY": 138.25,  # Zypern
    "AL": 140.75,  # Albanien
    "IL": 163.25,  # Israel
    "GB": 188.25,  # Großbritannien
    "MD": 250.75,  # Moldawien
    "LT": 263.25,  # Litauen
    "PL": 263.25,  # Polen
    "NO": 325.75,  # Norwegen
    "RS": 325.75,  # Serbien
    "DE": 363.25,  # Deutschland
    "BE": 375.75,  # Belgien
    "AT": 413.25,  # Österreich
    # Nicht-Finalisten
    "GE": 501.0, "EE": 501.0, "ME": 501.0,
    "PT": 501.0, "SM": 501.0, "AM": 501.0,
    "LU": 501.0, "CH": 501.0, "LV": 501.0, "AZ": 501.0,
}

# Televote-Odds: wer gewinnt die Televoting-Abstimmung?
# Ø aus 11 Bookmarkern: Unibet, Bet365, CoolBet, Betway, Betsson, Epic Bet,
#                        Boyle Sports, 7Bet, Ladbrokes, Bwin, William Hill
ODDS_TELE_2026: dict[str, float] = {
    "IL":   1.70,  # Israel          – TELE-FAVORIT (45%)
    "FI":   5.07,  # Finnland        – (18%)
    "GR":   8.82,  # Griechenland    – (7%)
    "BG":  13.14,  # Bulgarien       – (6%)
    "RO":  13.45,  # Rumänien        – (5%)
    "MD":  20.91,  # Moldawien       – (3%)
    "IT":  22.18,  # Italien         – (3%)
    "AU":  33.09,  # Australien      – (3%)
    "UA":  34.27,  # Ukraine         – (2%)
    "DK":  65.45,  # Dänemark
    "SE":  90.64,  # Schweden
    "FR":  95.45,  # Frankreich
    "CY":  96.45,  # Zypern
    "HR": 103.64,  # Kroatien
    "MT": 128.09,  # Malta
    "CZ": 200.82,  # Tschechien
    "RS": 200.82,  # Serbien
    "GB": 214.45,  # Großbritannien
    "AL": 228.09,  # Albanien
    "PL": 255.36,  # Polen
    "NO": 259.82,  # Norwegen
    "DE": 264.45,  # Deutschland
    "LT": 269.00,  # Litauen
    "BE": 332.64,  # Belgien
    "AT": 341.73,  # Österreich
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
