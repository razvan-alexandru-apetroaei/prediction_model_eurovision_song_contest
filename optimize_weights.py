"""
Optimize per-group signal weights for jury and televote separately.

Groups optimized via LOYO-CV Spearman:
  A – Historisches Voting + Diaspora  (XGBoost)
  B – Community Poll (OGAE + Aussie)  (XGBoost)
  C – YouTube Views                   (XGBoost)
  E – Kontext (Auftrittsreihenfolge, Sprache, Hist. Performance) (XGBoost)
  F – Wettquoten (pre-Final Odds)     (Signal → ESC-Punkte, identisch zu A-E)

Für jede Gruppe A-E wird ein eigener XGBoost trainiert (LOYO-CV).
Gruppe F wird direkt aus historischen Wettquoten (data_odds_history.py) berechnet.
Für Jahre ohne Odds-Daten (2016-2019) liefert F keinen Beitrag.

Ergebnis wird in data/processed/weights.json gespeichert und von predict.py gelesen.
"""
import sys, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from scipy.stats import spearmanr
from scipy.optimize import minimize, differential_evolution

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from build_dataset import (
    FEATURE_GROUPS, _bilateral_history, _poll_features, _load_youtube,
    _running_orders, _language_features, _historical_performance,
    _sf_rank_features, _eurojury_features,
    build_prediction_rows,
)
from fetch_voting import build_long_table
from train import MODEL_PARAMS
from config import YEARS_TRAIN, DIR_PROCESSED
from data_odds_history import odds_jury_prob, odds_tele_prob

POINTS_AWARDED = [12, 10, 8, 7, 6, 5, 4, 3, 2, 1]

# Gruppen-Reihenfolge: A/B/C/E per XGBoost, F per Odds-Signal
MODEL_GROUPS = list(FEATURE_GROUPS.keys())        # [A, B, C, E]
ALL_GROUPS   = MODEL_GROUPS + ["F_odds"]           # [A, B, C, E, F]

# ── Gewichts-Constraints ──────────────────────────────────────────────────────
# Maximales Gewicht pro Gruppe (None = unbegrenzt)
MAX_WEIGHT = {
    "F_odds":              None,
    "A_historical_voting": None,
    "B_community_poll":    None,
    "C_youtube":           None,
    "E_contest_context":   None,
    "G_eurojury":          None,
}
MIN_COMMUNITY = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────────────────────────────────────────

def _allocate(scores: pd.Series, exclude_cc: str) -> dict[str, int]:
    s = scores.drop(labels=[exclude_cc], errors="ignore")
    ranked = s.sort_values(ascending=False)
    return {cc: pts for pts, (cc, _) in zip(POINTS_AWARDED, ranked.items())}


def _signal_to_esc_pts(signal: dict[str, float],
                        voters: list[str],
                        finalists: list[str]) -> dict[str, float]:
    """ESC-Voter-Simulation: Top-10 bekommen 12-10-8-7-6-5-4-3-2-1 Punkte."""
    totals: dict[str, float] = defaultdict(float)
    for voter in voters:
        ranked = sorted(
            [cc for cc in finalists if cc != voter],
            key=lambda cc: signal.get(cc, 0.0),
            reverse=True,
        )
        for pts, cc in zip(POINTS_AWARDED, ranked):
            totals[cc] += pts
    return dict(totals)


def _signal_to_linear_pts(signal: dict[str, float],
                           voters: list[str],
                           finalists: list[str]) -> dict[str, float]:
    """
    Voter-Simulation mit linearem Punkt-Abfall über ALLE Länder (kein Top-10-Klippe).
    Rang 1 → n-1 Punkte, Rang 2 → n-2, ..., letzter Rang → 1 Punkt.
    Gleiche Voter-Mechanik wie XGBoost-Gruppen → gleiche Größenordnung (Hunderte).
    Geeignet für globale Signale (Odds), die für alle Wähler identisch sind.
    """
    totals: dict[str, float] = defaultdict(float)
    for voter in voters:
        others = [cc for cc in finalists if cc != voter]
        ranked = sorted(others, key=lambda cc: signal.get(cc, 0.0), reverse=True)
        n = len(ranked)
        for i, cc in enumerate(ranked):
            totals[cc] += float(n - i)   # Rang 1 → n Pkt, Rang n → 1 Pkt
    return dict(totals)


def _country_totals_from_raw(feat_df: pd.DataFrame, voters: list[str],
                              raw_col: str) -> dict[str, int]:
    totals = defaultdict(int)
    for voter in voters:
        sub = feat_df[feat_df["from_country"] == voter].set_index("to_country")
        if raw_col not in sub.columns:
            continue
        for cc, pts in _allocate(sub[raw_col], voter).items():
            totals[cc] += pts
    return dict(totals)


def _actual_totals(year: int, all_rows: list[dict]) -> dict[str, dict]:
    finals = [r for r in all_rows if r["year"] == year and r.get("round", "final") == "final"]
    t = defaultdict(lambda: {"jury": 0, "tele": 0})
    for r in finals:
        t[r["to_country"]]["jury"] += r["jury_pts"]
        t[r["to_country"]]["tele"] += r["tele_pts"]
    return {cc: {"jury": v["jury"], "tele": v["tele"], "total": v["jury"] + v["tele"]}
            for cc, v in t.items()}


# ─────────────────────────────────────────────────────────────────────────────
# LOYO-CV Gruppen-Vorhersagen sammeln
# ─────────────────────────────────────────────────────────────────────────────

def collect_group_predictions(all_rows: list[dict]) -> dict[int, dict]:
    """
    LOYO-CV: Für jedes Test-Jahr Gruppen-Totals berechnen (trainiert auf allen früheren Jahren).

    Rückgabe: {year: {group: {"jury": {cc: pts}, "tele": {cc: pts}}}}

    F_odds wird nur für Jahre mit verfügbaren historischen Odds eingetragen (2021+).
    Für Jahre ohne Odds (2016-2019) fehlt der F_odds-Schlüssel → kein Beitrag in der Optimierung.
    """
    train_df_full = pd.read_csv(Path(DIR_PROCESSED) / "training_data.csv")
    val_years = [y for y in YEARS_TRAIN if y > min(YEARS_TRAIN)]
    results = {}

    for year in val_years:
        print(f"  -> {year}", end="", flush=True)
        finals = [r for r in all_rows if r["year"] == year and r.get("round", "final") == "final"]
        if not finals:
            print(" (keine Finaldaten, übersprungen)")
            continue

        finalists = list({r["to_country"] for r in finals})
        voters    = list({r["from_country"] for r in finals})

        bilateral  = _bilateral_history(all_rows, target_year=year)
        poll       = _poll_features(year, finalists)
        youtube    = _load_youtube(year, finalists)
        running    = _running_orders(year, all_rows)
        language   = _language_features(year, finalists)
        hist_perf  = _historical_performance(year, all_rows)
        sf_rank    = _sf_rank_features(year, finalists)
        eurojury   = _eurojury_features(year, finalists)

        feat_df = build_prediction_rows(
            voters, finalists, bilateral, poll, youtube, running, language, hist_perf,
            sf_rank=sf_rank, eurojury=eurojury,
        )

        train_df = train_df_full[train_df_full["year"] < year]
        if train_df.empty:
            print(" (kein Trainingsdaten, übersprungen)")
            continue

        group_preds = {}

        # ── A/B/C/E: XGBoost ─────────────────────────────────────────────────
        from xgboost import XGBRegressor
        for grp, cols in FEATURE_GROUPS.items():
            present = [c for c in cols if c in train_df.columns and c in feat_df.columns]
            if not present:
                continue
            j_model = XGBRegressor(**MODEL_PARAMS)
            t_model = XGBRegressor(**MODEL_PARAMS)
            j_model.fit(train_df[present], train_df["jury_pts"], verbose=False)
            t_model.fit(train_df[present], train_df["tele_pts"], verbose=False)

            feat_sub = feat_df.copy()
            feat_sub[f"jury_{grp}"] = np.clip(j_model.predict(feat_df[present]), 0, None)
            feat_sub[f"tele_{grp}"] = np.clip(t_model.predict(feat_df[present]), 0, None)

            group_preds[grp] = {
                "jury": _country_totals_from_raw(feat_sub, voters, f"jury_{grp}"),
                "tele": _country_totals_from_raw(feat_sub, voters, f"tele_{grp}"),
            }

        # ── F: Historische Wettquoten (Jury und Tele getrennt) ───────────────
        # Jury-Odds → Jury-Signal, Tele-Odds → Tele-Signal.
        # ESC-Voter-Simulation: jeder Wähler gibt 12-10-8-7-6-5-4-3-2-1 laut Odds-Rang.
        jury_prob = odds_jury_prob(year)
        tele_prob = odds_tele_prob(year)
        has_odds  = bool(jury_prob) or bool(tele_prob)
        if has_odds:
            jury_pts_f = _signal_to_esc_pts(jury_prob, voters, finalists) if jury_prob else {}
            tele_pts_f = _signal_to_esc_pts(tele_prob, voters, finalists) if tele_prob else {}
            group_preds["F_odds"] = {
                "jury": jury_pts_f,
                "tele": tele_pts_f,
            }
            grp_label = "A/B/C/E/G/F" if "G_eurojury" in group_preds else "A/B/C/E/F"
            print(f" [{grp_label}]", end="")
        else:
            grp_label = "A/B/C/E/G" if "G_eurojury" in group_preds else "A/B/C/E"
            print(f" [{grp_label}]", end="")

        results[year] = group_preds
        print()

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Gewichts-Optimierung via Differential Evolution + SLSQP-Polishing
# ─────────────────────────────────────────────────────────────────────────────

def optimize_weights(group_preds: dict, all_rows: list[dict], target: str) -> tuple:
    """
    Findet Gewichte die Spearman-r für `target` maximieren.
    Strategie: Differential Evolution (global) → SLSQP-Polishing (lokal).
    Simplex-Constraint (Summe=1) wird durch interne Normalisierung erzwungen.
    """
    val_years = sorted(group_preds.keys())
    n_grps    = len(ALL_GROUPS)

    def neg_spearman(w):
        # Normalisierung auf Simplex (Summe=1, alle>=0)
        w = np.abs(w)
        total = w.sum()
        if total < 1e-9:
            return 0.0
        w = w / total

        rs = []
        for year in val_years:
            actual   = _actual_totals(year, all_rows)
            grp_data = group_preds[year]
            all_ccs  = list(actual.keys())

            pred_scores = np.zeros(len(all_ccs))
            for grp, wi in zip(ALL_GROUPS, w):
                if grp not in grp_data:
                    continue
                key    = "tele" if target == "tele" else "jury"
                totals = grp_data[grp].get(key, {})
                for j, cc in enumerate(all_ccs):
                    pred_scores[j] += wi * totals.get(cc, 0)

            actual_scores = np.array([actual[cc][target] for cc in all_ccs])
            if len(set(pred_scores)) < 2 or len(set(actual_scores)) < 2:
                continue
            r, _ = spearmanr(actual_scores, pred_scores)
            if not np.isnan(r):
                rs.append(r)
        return -np.mean(rs) if rs else 0.0

    bounds = [(0.0, 1.0)] * n_grps

    # Phase 1: Differential Evolution (globale Suche)
    res_de = differential_evolution(
        neg_spearman, bounds, seed=42,
        maxiter=3000, tol=1e-9,
        popsize=25, mutation=(0.5, 1.5), recombination=0.9,
        workers=1, polish=False,
    )

    # Phase 2: SLSQP-Polishing vom besten DE-Punkt aus (+ 10 zufällige Starts)
    constraints = [{"type": "eq", "fun": lambda w: np.abs(w).sum() - 1.0}]
    best_val = res_de.fun
    best_x   = res_de.x.copy()

    candidates = [res_de.x]
    rng = np.random.default_rng(0)
    for _ in range(10):
        candidates.append(rng.dirichlet(np.ones(n_grps)))

    for w0 in candidates:
        res = minimize(neg_spearman, w0, method="SLSQP",
                       bounds=bounds, constraints=constraints,
                       options={"maxiter": 5000, "ftol": 1e-10})
        if res.fun < best_val:
            best_val = res.fun
            best_x   = res.x.copy()

    w_opt = np.abs(best_x)
    w_opt /= w_opt.sum()
    return w_opt, -best_val


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("  Eurovision Weight Optimizer – LOYO-CV (Spearman)")
    print("  Gruppen: A (Voting+Diaspora), B (Poll), C (YouTube),")
    print("           E (Kontext), F (Wettquoten)")
    print("=" * 65)

    print("\n[1] Lade Voting-Daten...")
    all_rows = build_long_table(YEARS_TRAIN)

    print("\n[2] Berechne LOYO-CV Gruppen-Totals...")
    group_preds = collect_group_predictions(all_rows)

    LABELS = {
        "A_historical_voting": "[A] Historisches Voting + Diaspora",
        "B_community_poll":    "[B] Community Poll",
        "C_youtube":           "[C] YouTube Views",
        "E_contest_context":   "[E] Kontext",
        "F_odds":              "[F] Wettquoten (pre-Final)",
        "G_eurojury":          "[G] Eurojury (Alumni-Panel)",
    }

    results = {}
    print()
    for target in ["jury", "tele"]:
        print(f"\n[3] Optimiere Gewichte für: {target.upper()}")
        w_opt, best_r = optimize_weights(group_preds, all_rows, target)
        results[target] = {grp: float(round(w, 4)) for grp, w in zip(ALL_GROUPS, w_opt)}

        print(f"  OK Bestes LOYO Spearman r = {best_r:.4f}")
        print(f"  Gewichte:")
        for grp, w in zip(ALL_GROUPS, w_opt):
            bar = "#" * int(w * 40)
            print(f"    {LABELS.get(grp, grp):<38} {w*100:>5.1f}%  {bar}")

    out = Path(DIR_PROCESSED) / "weights.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"\nOK Gewichte gespeichert → {out}")
    print("\nNächster Schritt: py -3.11 src/predict.py")
