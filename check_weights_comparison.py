"""
Vergleicht alte vs neue Gewichte auf denselben (neuen) Daten.
Zeigt ob der Rückgang vom Optimizer kommt, nicht von den neuen Daten.
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

# Alte Gewichte (vor Eurojury 2023/2024, nach DE-Optimizer mit running_order_late)
WEIGHTS_OLD = {
    "jury": {"A_historical_voting": 0.389, "B_community_poll": 0.037, "C_youtube": 0.047,
             "E_contest_context": 0.149, "G_eurojury": 0.124, "F_odds": 0.254},
    "tele": {"A_historical_voting": 0.268, "B_community_poll": 0.027, "C_youtube": 0.068,
             "E_contest_context": 0.218, "G_eurojury": 0.015, "F_odds": 0.405},
}

# Neue Gewichte (nach Eurojury 2023/2024)
WEIGHTS_NEW = json.loads((Path(DIR_PROCESSED)/"weights.json").read_text())

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
val_years = [y for y in YEARS_TRAIN if y > min(YEARS_TRAIN)]

print("Alte Gewichte auf NEUEN Daten  vs  Neue Gewichte auf NEUEN Daten")
print("(Wenn alte besser: Problem ist der Optimizer, nicht die Daten)")
print()
print(f"{'Jahr':<6} {'Alt Jury':>9} {'Neu Jury':>9} {'Diff':>6}   {'Alt Total':>10} {'Neu Total':>10} {'Diff':>6}")
print("-" * 65)

old_jury_rs, new_jury_rs = [], []
old_tot_rs,  new_tot_rs  = [], []

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

    actual_jury  = defaultdict(int); actual_tele = defaultdict(int)
    for r in finals:
        actual_jury[r["to_country"]] += r["jury_pts"]
        actual_tele[r["to_country"]] += r["tele_pts"]
    actual_total = {cc: actual_jury[cc]+actual_tele[cc] for cc in finalists}

    def score(w):
        sj, st = defaultdict(float), defaultdict(float)
        for grp in ALL_GROUPS:
            if grp not in group_preds: continue
            for cc in finalists:
                sj[cc] += w["jury"].get(grp, 0) * group_preds[grp]["jury"].get(cc, 0)
                st[cc] += w["tele"].get(grp, 0) * group_preds[grp]["tele"].get(cc, 0)
        stot = {cc: sj[cc]+st[cc] for cc in finalists}
        rj, _ = spearmanr([actual_jury[cc]  for cc in finalists], [sj[cc]   for cc in finalists])
        rt, _ = spearmanr([actual_total[cc] for cc in finalists], [stot[cc] for cc in finalists])
        return rj, rt

    rj_old, rt_old = score(WEIGHTS_OLD)
    rj_new, rt_new = score(WEIGHTS_NEW)

    dj = rj_new - rj_old
    dt = rt_new - rt_old
    flag_j = "✓" if dj >= 0 else "✗"
    flag_t = "✓" if dt >= 0 else "✗"
    print(f"{year:<6} {rj_old:>9.3f} {rj_new:>9.3f} {dj:>+6.3f}{flag_j}  {rt_old:>10.3f} {rt_new:>10.3f} {dt:>+6.3f}{flag_t}")
    old_jury_rs.append(rj_old); new_jury_rs.append(rj_new)
    old_tot_rs.append(rt_old);  new_tot_rs.append(rt_new)

print("-" * 65)
avg_oj = np.mean(old_jury_rs); avg_nj = np.mean(new_jury_rs)
avg_ot = np.mean(old_tot_rs);  avg_nt = np.mean(new_tot_rs)
print(f"{'Ø':<6} {avg_oj:>9.3f} {avg_nj:>9.3f} {avg_nj-avg_oj:>+6.3f}   {avg_ot:>10.3f} {avg_nt:>10.3f} {avg_nt-avg_ot:>+6.3f}")
print()
if avg_nj < avg_oj:
    print("DIAGNOSE: Neue Daten sind gut – aber der Optimizer hat schlechtere")
    print("          Gewichte gefunden (lokales Optimum). Alte Gewichte")
    print("          behalten wäre besser gewesen!")
else:
    print("DIAGNOSE: Neue Gewichte sind besser. Verbesserung kommt von den Daten.")
