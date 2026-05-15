# Eurovision Predictor

Statistisches Vorhersagemodell für den Eurovision Song Contest. Kombiniert historische Abstimmungsdaten, Community-Polls, YouTube-Views, Wettquoten und Eurojury-Daten zu einer gewichteten Gesamtprognose — getrennt für Jury und Televote.

## Ergebnisse (LOYO-CV, 2022–2025)

| Metrik | Wert |
|--------|------|
| Jury Spearman r | 0.673 |
| Tele Spearman r | **0.827** |
| Ø Rangfehler | 4.0 Plätze |
| Median Rangfehler | 3 Plätze |

## Signalgruppen

| Gruppe | Signal | Jury-Gewicht | Tele-Gewicht |
|--------|--------|-------------|-------------|
| **F** | Wettquoten (Jury/Tele getrennt) | 54% | 24% |
| **A** | Historisches Voting + Diaspora | 23% | 41% |
| **G** | Eurojury (Alumni-Panel) | 8% | 9% |
| **E** | Kontext (Startreihenfolge, Sprache, SF-Rang) | 7% | 8% |
| **B** | Community Poll (OGAE + Aussievision) | 6% | 1% |
| **C** | YouTube Views | 2% | 17% |

Gewichte optimiert via **LOYO-CV** (Leave-One-Year-Out) + Differential Evolution + SLSQP.

## Architektur

```
Rohdaten (Voting, Polls, YouTube, Odds)
    ↓
XGBoost pro Signalgruppe (je Jury + Tele Modell)
    ↓
ESC-Voter-Simulation (12-10-8-7-6-5-4-3-2-1 pro Wählerland)
    ↓
Gewichtete Addition (Gewichte aus LOYO-CV)
    ↓
Vorhersage: jury_pts + tele_pts pro Land
```

## Setup

```bash
pip install -r requirements.txt
```

API-Keys als Umgebungsvariablen (optional, nur für Datenabruf):
```
YOUTUBE_API_KEY=...
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
```

## Verwendung

```bash
# Vorhersage generieren
py -3.11 src/predict.py

# Modell trainieren
py -3.11 src/build_dataset.py
py -3.11 src/train.py

# Gewichte optimieren (dauert ~5-10 Min)
py -3.11 optimize_weights.py

# Hindcast (2022-2025)
py -3.11 hindcast_detail.py

# Overfitting-Check
py -3.11 check_overfitting.py
```

## Dateistruktur

```
eurovision-predictor/
├── src/
│   ├── predict.py          # Hauptvorhersage
│   ├── build_dataset.py    # Feature-Engineering
│   ├── train.py            # XGBoost Training
│   ├── fetch_voting.py     # Abstimmungsdaten laden
│   └── fetch_youtube.py    # YouTube-Daten abrufen
├── data/
│   ├── raw/                # Rohdaten (Voting, Polls, YouTube)
│   └── processed/          # weights.json, training_data.csv
├── config.py               # Einträge 2026, YEARS_TRAIN, Pfade
├── data_2026_market.py     # Wettquoten + Rehearsal Scores 2026
├── data_odds_history.py    # Historische Jury/Tele-Odds 2021-2025
├── data_eurojury.py        # Eurojury-Scores 2016-2026
├── data_language.py        # Sprache pro Song/Jahr
├── data_geo.py             # Geographische Nähe + Diaspora
├── optimize_weights.py     # LOYO-CV Gewichtsoptimierung
├── hindcast_detail.py      # Detaillierter Rückblick 2023-2025
├── check_overfitting.py    # Optimizer vs. Gleichgewichte
└── check_weights_comparison.py  # Alte vs. neue Gewichte
```

## Methodik

### Trainingsdaten
Jahre 2021–2025 (getrennte Jury/Tele-Odds verfügbar). 2016–2019 ausgeschlossen da nur kombinierte Gewinnquoten vorhanden.

### Wettquoten
Getrennte Jury- und Televote-Odds von [eurovisionworld.com](https://eurovisionworld.com/odds). Buchmacher-Marge wird durch faire Wahrscheinlichkeiten ersetzt (normiert auf Summe=1).

### Voter-Simulation
Jedes der ~35 abstimmenden Länder (25 Finalisten + 10 ausgeschiedene HF-Länder) vergibt 12-10-8-7-6-5-4-3-2-1 Punkte laut vorhergesagtem Ranking. So entsteht ein simuliertes ESC-Punktesystem.

### Eurojury
Jährliches Alumni-Panel aus ehemaligen ESC-Teilnehmern (~35-43 nationale Jurys). Stark korreliert mit der echten Jury-Abstimmung. Daten: [aussievision.net](https://aussievision.net), [eurovoix.com](https://eurovoix.com).

## Eurovision 2026 – Vorhersage (Stand: 15. Mai 2026)

| Rk | Land | Jury | Tele | Total |
|----|------|------|------|-------|
| 1 | Finnland | 252 | 143 | **395** |
| 2 | Australien | 313 | 35 | **348** |
| 3 | Griechenland | 145 | 201 | **346** |
| 4 | Frankreich | 211 | 43 | **254** |
| 5 | Dänemark | 184 | 68 | **252** |

Vollständige Tabelle: `data/predictions/predictions_2026.csv`
