# Eurovision Song Contest Prediction Model

A machine learning system for predicting Eurovision Song Contest results, built from scratch in Python. The model combines **7 independent signal sources** into a weighted ensemble — with separate predictions for jury vote and televote.

**Author:** Razvan-Alexandru Apetroaei  
**Program:** M.Sc. Mathematics in Data Science — Technical University of Munich (TUM)

---

## Results (Out-of-Sample, LOYO-CV 2022–2025)

| Metric | Value |
|--------|-------|
| Jury Spearman r | 0.673 |
| Televote Spearman r | **0.827** |
| Mean absolute rank error | 4.0 places |
| Median rank error | 3 places |
| Top-5 accuracy (2024) | **5/5** |

Validated via **Leave-One-Year-Out Cross-Validation**: for each test year, the model is trained exclusively on prior years — no data leakage.

---

## Architecture

```
Raw Data (voting history, polls, YouTube, betting odds, Eurojury)
    │
    ├── Signal A: Bilateral voting history + diaspora networks
    ├── Signal B: Community polls (OGAE + Aussievision)
    ├── Signal C: YouTube views
    ├── Signal E: Contest context (running order, language, SF rank)
    ├── Signal F: Betting odds — jury and televote separately
    └── Signal G: Eurojury (alumni panel, ~35–43 national juries)
         │
         ▼
    XGBoost Regressor (one jury model + one televote model per signal group)
         │
         ▼
    ESC Voter Simulation (each of ~35 voting countries awards 12-10-8-7-6-5-4-3-2-1)
         │
         ▼
    Weighted combination (weights optimized via LOYO-CV + Differential Evolution)
         │
         ▼
    Prediction: jury_pts + tele_pts per country
```

---

## Technical Details

### Signal Groups & Optimized Weights

| Group | Signal | Jury weight | Tele weight |
|-------|--------|-------------|-------------|
| **F** | Betting odds (jury/tele split) | 54.3% | 23.9% |
| **A** | Historical voting + diaspora | 22.5% | 41.2% |
| **G** | Eurojury alumni panel | 7.8% | 8.8% |
| **E** | Contest context | 7.1% | 8.4% |
| **B** | Community poll | 5.9% | 0.5% |
| **C** | YouTube views | 2.4% | 17.2% |

### Weight Optimization
Weights are optimized to maximize mean Spearman rank correlation across all LOYO-CV validation years. The optimization pipeline uses:
1. **Differential Evolution** (global search, `popsize=25`, `maxiter=3000`) to escape local optima
2. **SLSQP polishing** (local refinement from the best DE solution + 10 random restarts)
3. Simplex constraint enforced via internal normalization (weights sum to 1, all ≥ 0)

Jury and televote weights are optimized **independently**, reflecting the structural difference between the two voting systems.

### XGBoost Models
One XGBoost regressor per signal group per vote type (jury / televote), trained on ~6,000 pairwise rows (voter country → candidate country). Target variables: `jury_pts` and `tele_pts` per pair. Features are group-specific (e.g., 3- and 5-year bilateral voting bias, diaspora index, geographic proximity for group A).

### ESC Voter Simulation
After XGBoost prediction, each of the ~35 voting countries (25 finalists + 10 semi-final eliminated countries that still vote in the final) independently ranks all other countries by predicted score and awards 12–10–8–7–6–5–4–3–2–1 points to its top 10. This mirrors the actual Eurovision voting mechanism and aggregates predictions into a realistic points total.

### Betting Odds as a Signal
Pre-final decimal odds from 12 bookmakers (eurovisionworld.com) are converted to fair probabilities (bookmaker margin removed, normalized to sum = 1). Crucially, **jury odds and televote odds are treated as separate signals** — reflecting that jury favorites (e.g. Australia) and televote favorites (e.g. Israel) differ substantially. Historical split odds are available for 2021–2025, making the training and inference consistent.

### Bilateral Voting History
For each voter–candidate pair, a 3-year and 5-year average jury/televote bias is computed from historical finals data. This captures persistent voting patterns (e.g. Greek diaspora in Germany, Nordic bloc voting) that are the strongest non-market predictor of televote outcomes.

### Running Order Effect
The model includes a `running_order_late` feature capturing the "pimp slot" effect: entries in the last 25% of the show receive a measurable televote boost due to recency bias. Formally:

```
running_order_late = max(0, (position - 0.75·n) / (n - 0.75·n))
```

---

## Stack

- **Python 3.11**
- **XGBoost** — gradient boosted trees for per-group score prediction
- **SciPy** — Differential Evolution + SLSQP for weight optimization
- **pandas / NumPy** — data pipeline and feature engineering
- **Spearman rank correlation** — primary evaluation metric

---

## Project Structure

```
eurovision-predictor/
├── src/
│   ├── predict.py           # Main prediction pipeline
│   ├── build_dataset.py     # Feature engineering (all signal groups)
│   ├── train.py             # XGBoost training + model persistence
│   ├── fetch_voting.py      # Load and parse voting data
│   └── fetch_youtube.py     # YouTube Data API integration
├── data/
│   ├── raw/                 # Voting, poll, YouTube raw data (2016–2025)
│   └── processed/           # weights.json, training_data.csv
├── config.py                # 2026 entries, YEARS_TRAIN, paths, running order
├── data_2026_market.py      # 2026 betting odds (jury + tele) + rehearsal scores
├── data_odds_history.py     # Historical jury/tele odds 2021–2025
├── data_eurojury.py         # Eurojury scores 2016–2026
├── data_language.py         # Song language per entry per year
├── data_geo.py              # Geographic proximity + diaspora index
├── optimize_weights.py      # LOYO-CV weight optimization (DE + SLSQP)
├── hindcast_detail.py       # Per-country hindcast 2022–2025
├── check_overfitting.py     # Optimized vs. equal weights comparison
└── check_weights_comparison.py  # Old vs. new weights on same data
```

---

## Quickstart

```bash
pip install -r requirements.txt

# Generate 2026 prediction
py -3.11 src/predict.py

# Rebuild training data
py -3.11 src/build_dataset.py

# Re-optimize weights (~5–10 min)
py -3.11 optimize_weights.py

# Run hindcast for 2022–2025
py -3.11 hindcast_detail.py
```

---

## Eurovision 2026 Prediction (as of May 15, 2026)

Grand Final — May 16, 2026, Wiener Stadthalle, Vienna

| Rank | Country | Artist | Jury | Tele | Total |
|------|---------|--------|------|------|-------|
| 1 | Finland | Linda Lampenius & Pete Parkkonen | 252 | 143 | **395** |
| 2 | Australia | Delta Goodrem | 313 | 35 | **348** |
| 3 | Greece | Akylas | 145 | 201 | **346** |
| 4 | France | Monroe | 211 | 43 | **254** |
| 5 | Denmark | Søren Torpegaard Lund | 184 | 68 | **252** |
| 6 | Romania | Alexandra Căpitănescu | 96 | 125 | **221** |
| 7 | Malta | Aidan | 120 | 100 | **220** |
| 8 | Israel | Noam Bettan | 16 | 196 | **212** |
| 9 | Italy | Sal Da Vinci | 115 | 86 | **201** |
| 10 | Czechia | Daniel Žižka | 141 | 48 | **189** |

*Australia: strong jury favorite (29% jury odds) but weak televote (1.2% tele odds) — the model captures this split correctly.*  
*Israel: near-zero jury points (0.6% jury odds) but dominant televote signal (38.9% tele odds).*
