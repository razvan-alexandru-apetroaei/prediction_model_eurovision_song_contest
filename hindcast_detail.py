"""
Detaillierter Hindcast für 2023, 2024, 2025:
Zeigt vorhergesagtes Ranking vs. echtes Ergebnis pro Land.
"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
from pathlib import Path
from collections import defaultdict
from scipy.stats import spearmanr

sys.path.insert(0, ".")
sys.path.insert(0, "src")
from build_dataset import (FEATURE_GROUPS, build_prediction_rows, _bilateral_history,
    _poll_features, _load_youtube, _running_orders, _language_features,
    _historical_performance, _sf_rank_features, _eurojury_features)
from fetch_voting import build_long_table
from train import MODEL_PARAMS
from config import YEARS_TRAIN, DIR_PROCESSED
from data_odds_history import odds_jury_prob, odds_tele_prob
from xgboost import XGBRegressor

POINTS_AWARDED = [12, 10, 8, 7, 6, 5, 4, 3, 2, 1]
ALL_GROUPS = list(FEATURE_GROUPS.keys()) + ["F_odds"]

def _allocate(scores, exclude_cc):
    s = scores.drop(labels=[exclude_cc], errors="ignore")
    return {cc: pts for pts, (cc, _) in zip(POINTS_AWARDED, s.sort_values(ascending=False).items())}

def _totals(feat_df, voters, col):
    t = defaultdict(int)
    for v in voters:
        sub = feat_df[feat_df["from_country"]==v].set_index("to_country")
        if col in sub.columns:
            for cc, pts in _allocate(sub[col], v).items(): t[cc] += pts
    return dict(t)

def _odds_pts(sig, voters, finalists):
    t = defaultdict(float)
    for v in voters:
        ranked = sorted([c for c in finalists if c!=v], key=lambda c: sig.get(c,0), reverse=True)
        for pts, cc in zip(POINTS_AWARDED, ranked): t[cc] += pts
    return dict(t)

all_rows      = build_long_table(YEARS_TRAIN)
train_df_full = pd.read_csv(Path(DIR_PROCESSED)/"training_data.csv")
weights       = json.loads((Path(DIR_PROCESSED)/"weights.json").read_text())

COUNTRY_NAMES = {
    "AL":"Albania","AM":"Armenia","AU":"Australia","AT":"Austria","AZ":"Azerbaijan",
    "BE":"Belgium","BG":"Bulgaria","HR":"Croatia","CY":"Cyprus","CZ":"Czechia",
    "DK":"Denmark","EE":"Estonia","FI":"Finland","FR":"France","GE":"Georgia",
    "DE":"Germany","GR":"Greece","HU":"Hungary","IS":"Iceland","IE":"Ireland",
    "IL":"Israel","IT":"Italy","LV":"Latvia","LT":"Lithuania","LU":"Luxembourg",
    "MT":"Malta","MD":"Moldova","ME":"Montenegro","NL":"Netherlands","MK":"N.Macedonia",
    "NO":"Norway","PL":"Poland","PT":"Portugal","RO":"Romania","SM":"San Marino",
    "RS":"Serbia","SI":"Slovenia","ES":"Spain","SE":"Sweden","CH":"Switzerland",
    "UA":"Ukraine","GB":"United Kingdom",
}

for year in [2023, 2024, 2025]:
    finals    = [r for r in all_rows if r["year"]==year and r.get("round","final")=="final"]
    if not finals:
        print(f"\n{year}: Keine Daten.")
        continue
    finalists = list({r["to_country"] for r in finals})
    voters    = list({r["from_country"] for r in finals})

    feat_df = build_prediction_rows(
        voters, finalists,
        _bilateral_history(all_rows, target_year=year),
        _poll_features(year, finalists), _load_youtube(year, finalists),
        _running_orders(year, all_rows), _language_features(year, finalists),
        _historical_performance(year, all_rows),
        sf_rank=_sf_rank_features(year, finalists),
        eurojury=_eurojury_features(year, finalists),
    )
    train_df = train_df_full[train_df_full["year"] < year]

    group_preds = {}
    for grp, cols in FEATURE_GROUPS.items():
        present = [c for c in cols if c in train_df.columns and c in feat_df.columns]
        if not present: continue
        jm, tm = XGBRegressor(**MODEL_PARAMS), XGBRegressor(**MODEL_PARAMS)
        jm.fit(train_df[present], train_df["jury_pts"], verbose=False)
        tm.fit(train_df[present], train_df["tele_pts"], verbose=False)
        fs = feat_df.copy()
        fs[f"jury_{grp}"] = np.clip(jm.predict(feat_df[present]), 0, None)
        fs[f"tele_{grp}"] = np.clip(tm.predict(feat_df[present]), 0, None)
        group_preds[grp] = {"jury": _totals(fs, voters, f"jury_{grp}"),
                            "tele": _totals(fs, voters, f"tele_{grp}")}

    jp = odds_jury_prob(year)
    tp = odds_tele_prob(year)
    if jp or tp:
        group_preds["F_odds"] = {
            "jury": _odds_pts(jp, voters, finalists) if jp else {},
            "tele": _odds_pts(tp, voters, finalists) if tp else {},
        }

    sj, st = defaultdict(float), defaultdict(float)
    for grp in ALL_GROUPS:
        if grp not in group_preds: continue
        for cc in finalists:
            sj[cc] += weights["jury"].get(grp,0) * group_preds[grp]["jury"].get(cc,0)
            st[cc] += weights["tele"].get(grp,0) * group_preds[grp]["tele"].get(cc,0)
    stot = {cc: sj[cc]+st[cc] for cc in finalists}

    actual_jury  = defaultdict(int)
    actual_tele  = defaultdict(int)
    for r in finals:
        actual_jury[r["to_country"]]  += r["jury_pts"]
        actual_tele[r["to_country"]]  += r["tele_pts"]
    actual_total = {cc: actual_jury[cc]+actual_tele[cc] for cc in finalists}

    pred_ranked   = sorted(finalists, key=lambda cc: stot[cc], reverse=True)
    actual_ranked = sorted(finalists, key=lambda cc: actual_total[cc], reverse=True)
    actual_rank   = {cc: i+1 for i, cc in enumerate(actual_ranked)}

    rj, _ = spearmanr([actual_jury[cc]  for cc in finalists], [sj[cc]  for cc in finalists])
    rt, _ = spearmanr([actual_tele[cc]  for cc in finalists], [st[cc]  for cc in finalists])
    rto,_ = spearmanr([actual_total[cc] for cc in finalists], [stot[cc] for cc in finalists])

    ej_active = any(v["eurojury_norm"]>0 for v in _eurojury_features(year, finalists).values())

    print(f"\n{'='*70}")
    print(f"  HINDCAST {year}  |  Jury r={rj:.3f}  Tele r={rt:.3f}  Total r={rto:.3f}"
          f"  |  Eurojury: {'✓' if ej_active else '–'}  Odds: {'✓' if (jp or tp) else '–'}")
    print(f"{'='*70}")
    print(f"{'Rk':>3} {'Land':<18} {'Jury':>5} {'Tele':>5} {'Total':>6}  "
          f"{'Echter Rk':>9} {'Echte Pkte':>10}  {'Diff':>5}")
    print("-"*70)

    for i, cc in enumerate(pred_ranked):
        pred_rk  = i + 1
        act_rk   = actual_rank[cc]
        diff     = act_rk - pred_rk   # positiv = wir haben zu hoch platziert
        diff_str = f"{diff:+d}" if diff != 0 else "="
        flag     = "" if abs(diff) <= 3 else "  ⚠" if abs(diff) <= 6 else "  ✗"
        name     = COUNTRY_NAMES.get(cc, cc)
        print(f"{pred_rk:>3} {name:<18} {sj[cc]:>5.0f} {st[cc]:>5.0f} {stot[cc]:>6.0f}"
              f"  Rang {act_rk:>2}  {actual_total[cc]:>6} Pkte  {diff_str:>5}{flag}")

    # Top-5 Trefferquote
    pred_top5   = set(pred_ranked[:5])
    actual_top5 = set(actual_ranked[:5])
    hits = len(pred_top5 & actual_top5)
    print(f"\n  Top-5 korrekt vorhergesagt: {hits}/5  {pred_top5 & actual_top5}")
    pred_top10   = set(pred_ranked[:10])
    actual_top10 = set(actual_ranked[:10])
    hits10 = len(pred_top10 & actual_top10)
    print(f"  Top-10 korrekt vorhergesagt: {hits10}/10")
