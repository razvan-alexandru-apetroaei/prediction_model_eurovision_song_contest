"""Vergleich: optimierte Gewichte vs. gleichmäßige Gewichte → misst Optimizer-Overfitting."""
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

all_rows = build_long_table(YEARS_TRAIN)
train_df_full = pd.read_csv(Path(DIR_PROCESSED)/"training_data.csv")
weights_opt = json.loads((Path(DIR_PROCESSED)/"weights.json").read_text())

val_years = [y for y in YEARS_TRAIN if y > min(YEARS_TRAIN)]

header = f"{'Jahr':<6} {'Opt Jury':>9} {'Gleich Jury':>11} {'Opt Total':>10} {'Gleich Total':>13}"
print(header)
print("-" * 55)

opt_rs, eq_rs = [], []
for year in val_years:
    finals = [r for r in all_rows if r["year"]==year and r.get("round","final")=="final"]
    if not finals: continue
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

    actual_jury = defaultdict(int); actual_tele = defaultdict(int)
    for r in finals:
        actual_jury[r["to_country"]] += r["jury_pts"]
        actual_tele[r["to_country"]] += r["tele_pts"]
    actual_total = {cc: actual_jury[cc]+actual_tele[cc] for cc in finalists}

    def compute_scores(weights_dict):
        sj, st = defaultdict(float), defaultdict(float)
        for grp in ALL_GROUPS:
            if grp not in group_preds: continue
            wj = weights_dict["jury"].get(grp, 0)
            wt = weights_dict["tele"].get(grp, 0)
            for cc in finalists:
                sj[cc] += wj * group_preds[grp]["jury"].get(cc, 0)
                st[cc] += wt * group_preds[grp]["tele"].get(cc, 0)
        stot = {cc: sj[cc]+st[cc] for cc in finalists}
        rj, _ = spearmanr([actual_jury[cc]  for cc in finalists], [sj[cc]   for cc in finalists])
        rt, _ = spearmanr([actual_total[cc] for cc in finalists], [stot[cc] for cc in finalists])
        return rj, rt

    active = [g for g in ALL_GROUPS if g in group_preds]
    n = len(active)
    eq_w = {"jury": {g: 1/n for g in active}, "tele": {g: 1/n for g in active}}

    rj_opt, rt_opt = compute_scores(weights_opt)
    rj_eq,  rt_eq  = compute_scores(eq_w)

    diff_j = rj_opt - rj_eq
    diff_t = rt_opt - rt_eq
    print(f"{year:<6} {rj_opt:>9.3f} {rj_eq:>11.3f} {diff_j:>+8.3f}    {rt_opt:>6.3f} {rt_eq:>9.3f} {diff_t:>+8.3f}")
    opt_rs.append((rj_opt, rt_opt)); eq_rs.append((rj_eq, rt_eq))

print("-" * 70)
avg_oj = np.mean([x[0] for x in opt_rs]); avg_ej = np.mean([x[0] for x in eq_rs])
avg_ot = np.mean([x[1] for x in opt_rs]); avg_et = np.mean([x[1] for x in eq_rs])
print(f"{'Ø':<6} {avg_oj:>9.3f} {avg_ej:>11.3f} {avg_oj-avg_ej:>+8.3f}    {avg_ot:>6.3f} {avg_et:>9.3f} {avg_ot-avg_et:>+8.3f}")
print()
print(f"Mehrwert Optimierung: Jury +{avg_oj-avg_ej:.3f},  Total +{avg_ot-avg_et:.3f}")
print()
if avg_oj - avg_ej < 0.03:
    print("-> Overfitting-Warnung: Optimizer bringt kaum Mehrwert.")
    print("   Gleichmäßige Gewichte wären fast genauso gut.")
else:
    print("-> Optimierung bringt echten Mehrwert (kein reines Overfitting).")
