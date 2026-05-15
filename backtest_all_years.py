"""
LOYO-CV Backtest über alle Validierungsjahre.

Für jedes Jahr wird das Modell auf allen früheren Jahren trainiert und dann
auf das Test-Jahr angewendet. Zeigt Jury- und Tele-Spearman pro Jahr.
"""
import sys, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from build_dataset import (
    FEATURE_GROUPS, build_prediction_rows,
    _bilateral_history, _poll_features, _load_youtube,
    _running_orders, _language_features, _historical_performance,
    _sf_rank_features, _eurojury_features,
)
from fetch_voting import build_long_table
from train import MODEL_PARAMS
from config import YEARS_TRAIN, DIR_PROCESSED
from data_odds_history import odds_win_prob
from xgboost import XGBRegressor

POINTS_AWARDED = [12, 10, 8, 7, 6, 5, 4, 3, 2, 1]
ALL_GROUPS = list(FEATURE_GROUPS.keys()) + ["F_odds"]


def _allocate(scores, exclude_cc):
    s = scores.drop(labels=[exclude_cc], errors="ignore")
    ranked = s.sort_values(ascending=False)
    return {cc: pts for pts, (cc, _) in zip(POINTS_AWARDED, ranked.items())}


def _country_totals(feat_df, voters, col):
    totals = defaultdict(int)
    for voter in voters:
        sub = feat_df[feat_df["from_country"] == voter].set_index("to_country")
        if col not in sub.columns:
            continue
        for cc, pts in _allocate(sub[col], voter).items():
            totals[cc] += pts
    return dict(totals)


def _signal_to_esc_pts(signal, voters, finalists):
    totals = defaultdict(float)
    for voter in voters:
        ranked = sorted(
            [cc for cc in finalists if cc != voter],
            key=lambda cc: signal.get(cc, 0.0), reverse=True,
        )
        for pts, cc in zip(POINTS_AWARDED, ranked):
            totals[cc] += pts
    return dict(totals)


print("=" * 72)
print("  Eurovision LOYO-CV Backtest – Jury vs Televote")
print("=" * 72)

all_rows      = build_long_table(YEARS_TRAIN)
train_df_full = pd.read_csv(Path(DIR_PROCESSED) / "training_data.csv")
weights       = json.loads((Path(DIR_PROCESSED) / "weights.json").read_text())

val_years = [y for y in YEARS_TRAIN if y > min(YEARS_TRAIN)]

results = []

print(f"\n{'Jahr':<6} {'Wähler':>6} {'Länder':>7} {'Spearman Jury':>14} {'Spearman Tele':>14} {'Spearman Total':>15}  Odds")
print("-" * 72)

for year in val_years:
    finals    = [r for r in all_rows if r["year"] == year and r.get("round", "final") == "final"]
    if not finals:
        continue
    finalists = list({r["to_country"] for r in finals})
    voters    = list({r["from_country"] for r in finals})

    bilateral = _bilateral_history(all_rows, target_year=year)
    poll      = _poll_features(year, finalists)
    youtube   = _load_youtube(year, finalists)
    running   = _running_orders(year, all_rows)
    language  = _language_features(year, finalists)
    hist_perf = _historical_performance(year, all_rows)
    sf_rank   = _sf_rank_features(year, finalists)
    eurojury  = _eurojury_features(year, finalists)

    feat_df = build_prediction_rows(
        voters, finalists, bilateral, poll, youtube, running, language, hist_perf,
        sf_rank=sf_rank, eurojury=eurojury,
    )

    train_df = train_df_full[train_df_full["year"] < year]
    if train_df.empty:
        continue

    group_preds = {}
    for grp, cols in FEATURE_GROUPS.items():
        present = [c for c in cols if c in train_df.columns and c in feat_df.columns]
        if not present:
            continue
        jm = XGBRegressor(**MODEL_PARAMS)
        tm = XGBRegressor(**MODEL_PARAMS)
        jm.fit(train_df[present], train_df["jury_pts"], verbose=False)
        tm.fit(train_df[present], train_df["tele_pts"], verbose=False)
        feat_sub = feat_df.copy()
        feat_sub[f"jury_{grp}"] = np.clip(jm.predict(feat_df[present]), 0, None)
        feat_sub[f"tele_{grp}"] = np.clip(tm.predict(feat_df[present]), 0, None)
        group_preds[grp] = {
            "jury": _country_totals(feat_sub, voters, f"jury_{grp}"),
            "tele": _country_totals(feat_sub, voters, f"tele_{grp}"),
        }

    odds_prob = odds_win_prob(year)
    has_odds  = bool(odds_prob)
    if has_odds:
        odds_pts = _signal_to_esc_pts(odds_prob, voters, finalists)
        group_preds["F_odds"] = {"jury": odds_pts, "tele": odds_pts}

    # Gewichtete Scores
    scores_jury  = defaultdict(float)
    scores_tele  = defaultdict(float)
    for grp in ALL_GROUPS:
        if grp not in group_preds:
            continue
        wj = weights["jury"].get(grp, 0)
        wt = weights["tele"].get(grp, 0)
        for cc in finalists:
            scores_jury[cc] += wj * group_preds[grp]["jury"].get(cc, 0)
            scores_tele[cc] += wt * group_preds[grp]["tele"].get(cc, 0)

    scores_total = {cc: scores_jury[cc] + scores_tele[cc] for cc in finalists}

    # Echte Ergebnisse
    actual_jury  = defaultdict(int)
    actual_tele  = defaultdict(int)
    for r in finals:
        actual_jury[r["to_country"]] += r["jury_pts"]
        actual_tele[r["to_country"]] += r["tele_pts"]
    actual_total = {cc: actual_jury[cc] + actual_tele[cc] for cc in finalists}

    pred_j   = [scores_jury[cc]  for cc in finalists]
    pred_t   = [scores_tele[cc]  for cc in finalists]
    pred_tot = [scores_total[cc] for cc in finalists]
    act_j    = [actual_jury[cc]  for cc in finalists]
    act_t    = [actual_tele[cc]  for cc in finalists]
    act_tot  = [actual_total[cc] for cc in finalists]

    rj,  _ = spearmanr(act_j,   pred_j)
    rt,  _ = spearmanr(act_t,   pred_t)
    rtot,_ = spearmanr(act_tot, pred_tot)

    odds_tag = "✓" if has_odds else "–"
    print(f"{year:<6} {len(voters):>6} {len(finalists):>7} {rj:>14.3f} {rt:>14.3f} {rtot:>15.3f}  {odds_tag}")

    results.append({"year": year, "jury": rj, "tele": rt, "total": rtot, "odds": has_odds})

# Zusammenfassung
df = pd.DataFrame(results)
print("-" * 72)
print(f"{'Ø gesamt':<13} {df['jury'].mean():>14.3f} {df['tele'].mean():>14.3f} {df['total'].mean():>15.3f}")
df_odds = df[df["odds"]]
df_no   = df[~df["odds"]]
if not df_odds.empty:
    print(f"{'Ø mit Odds':<13} {df_odds['jury'].mean():>14.3f} {df_odds['tele'].mean():>14.3f} {df_odds['total'].mean():>15.3f}  (2021-2025)")
if not df_no.empty:
    print(f"{'Ø ohne Odds':<13} {df_no['jury'].mean():>14.3f} {df_no['tele'].mean():>14.3f} {df_no['total'].mean():>15.3f}  (2017-2019)")

print()
print("Interpretation:")
print("  r > 0.7  = sehr gut   (Top-10 fast vollständig korrekt)")
print("  r > 0.5  = gut        (grobe Rangfolge stimmt)")
print("  r > 0.3  = schwach    (Tendenz erkennbar)")
print("  r < 0.3  = schlecht   (kaum besser als Zufall)")
