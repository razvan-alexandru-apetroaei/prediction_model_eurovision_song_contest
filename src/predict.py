"""
Generate 2026 Eurovision predictions.

Signalgruppen (A/B/C/E/G per XGBoost, F per Wettquoten, H per Rehearsal):

  jury_final[cc] = w_A  * A_jury[cc]    ← Hist. Voting + Diaspora
                 + w_B  * B_jury[cc]    ← Community Poll (OGAE + Aussievision)
                 + w_C  * C_jury[cc]    ← YouTube Views
                 + w_E  * E_jury[cc]    ← Kontext (Laufnr, Sprache, Hist. Perf, SF-Rang)
                 + w_G  * G_jury[cc]    ← Eurojury Alumni-Panel (2016-2022)
                 + w_F  * F_jury[cc]    ← Wettquoten (LOYO-CV optimiert)
                 + w_H  * H_jury[cc]    ← Rehearsal Press Scores (manuell)

Gewichte A/B/C/E/G/F: per LOYO-CV Spearman optimiert (weights.json)
Gewicht H (Rehearsal): manuell (keine historischen Press-Score-Daten verfügbar)
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

from config import DIR_PROCESSED, DIR_PREDICTIONS, ENTRIES_2026, YEARS_TRAIN, VOTERS_ONLY_2026
from build_dataset import (
    FEATURE_GROUPS,
    _bilateral_history, _poll_features, _load_youtube,
    _running_orders, _language_features, _historical_performance,
    _sf_rank_features, _eurojury_features,
    build_prediction_rows,
)
from fetch_voting import build_long_table
from train import load_group_models

POINTS_AWARDED = [12, 10, 8, 7, 6, 5, 4, 3, 2, 1]

# H: Rehearsal Press Scores – manuelles Gewicht
REHEARSAL_WEIGHT = {"jury": 0.10, "tele": 0.05}


def _load_weights() -> dict:
    path = Path(DIR_PROCESSED) / "weights.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _allocate_points(scores: pd.Series, exclude_cc: str) -> dict[str, int]:
    s = scores.drop(labels=[exclude_cc], errors="ignore")
    ranked = s.sort_values(ascending=False)
    return {cc: pts for pts, (cc, _) in zip(POINTS_AWARDED, ranked.items())}


def _signal_to_esc_pts(signal: dict[str, float],
                        voters: list[str],
                        finalists: list[str]) -> dict[str, float]:
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


def _group_totals(feat_df: pd.DataFrame, voters: list[str],
                  group_models: dict, finalists: list[str]) -> dict[str, dict]:
    """XGBoost per-group → ESC-Punkte. {grp: {jury: {cc: pts}, tele: {cc: pts}}}"""
    result = {}
    for grp, cols in FEATURE_GROUPS.items():
        present = [c for c in cols if c in feat_df.columns]
        if grp not in group_models or not present:
            result[grp] = {"jury": {cc: 0 for cc in finalists},
                           "tele": {cc: 0 for cc in finalists}}
            continue
        models = group_models[grp]
        feat_df[f"jury_{grp}"] = np.clip(models["jury"].predict(feat_df[present]), 0, None)
        feat_df[f"tele_{grp}"] = np.clip(models["tele"].predict(feat_df[present]), 0, None)

        jury_t: dict[str, int] = defaultdict(int)
        tele_t: dict[str, int] = defaultdict(int)
        for voter in voters:
            sub = feat_df[feat_df["from_country"] == voter].set_index("to_country")
            for cc, pts in _allocate_points(sub[f"jury_{grp}"], voter).items():
                jury_t[cc] += pts
            for cc, pts in _allocate_points(sub[f"tele_{grp}"], voter).items():
                tele_t[cc] += pts
        result[grp] = {"jury": dict(jury_t), "tele": dict(tele_t)}
    return result


def predict_2026(
    finalists: list[str] | None = None,
    output_dir: str = DIR_PREDICTIONS,
) -> pd.DataFrame:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    all_entries = {e["code"]: e for e in ENTRIES_2026}
    if finalists is None:
        finalists = list(all_entries.keys())
    # Alle abstimmenden Länder: 25 Finalisten + 10 ausgeschiedene HF-Länder
    # (Ausgeschiedene können im Finale abstimmen, aber nicht gewinnen)
    voters = finalists + VOTERS_ONLY_2026

    # ── Gewichte aus weights.json (A/B/C/E/G/F) ──────────────────────────────
    saved_w   = _load_weights()
    jury_base = saved_w.get("jury", {})   # {grp: weight}, Summe = 1.0
    tele_base = saved_w.get("tele", {})

    # ── Market-Daten laden ────────────────────────────────────────────────────
    try:
        from data_2026_market import get_market_data, ODDS_JURY_2026, ODDS_TELE_2026, REHEARSAL_SCORES_2026
        market = get_market_data(finalists)
        odds_active      = any(v > 0 for v in ODDS_JURY_2026.values())
        rehearsal_active = any(v > 0 for v in REHEARSAL_SCORES_2026.values())
    except ImportError:
        market = {cc: {"odds_win_prob": 1/len(finalists), "odds_jury_prob": 1/len(finalists),
                       "odds_tele_prob": 1/len(finalists), "rehearsal_score_norm": 0.5} for cc in finalists}
        odds_active = rehearsal_active = False

    # ── Modelle laden ─────────────────────────────────────────────────────────
    group_models = load_group_models()

    # ── Signale berechnen ─────────────────────────────────────────────────────
    print("  [A] Bilateral voting history + Diaspora...")
    all_rows  = build_long_table(YEARS_TRAIN)
    bilateral = _bilateral_history(all_rows, target_year=2026)

    print("  [B] Community poll (OGAE + Aussievision)...")
    poll = _poll_features(2026, finalists)

    print("  [C] YouTube views...")
    youtube = _load_youtube(2026, finalists)

    print("  [E] Contest context (inkl. SF-Rang)...")
    running   = _running_orders(2026, all_rows)
    language  = _language_features(2026, finalists)
    hist_perf = _historical_performance(2026, all_rows)
    sf_rank   = _sf_rank_features(2026, finalists)   # 0.5 für alle (SF noch nicht gelaufen)

    print("  [G] Eurojury (Alumni-Panel)...")
    eurojury  = _eurojury_features(2026, finalists)  # 0.0 für alle (2026 nicht verfügbar)
    ej_available = any(v["eurojury_norm"] > 0 for v in eurojury.values())
    if ej_available:
        print(f"      → Eurojury-Daten verfügbar")
    else:
        print(f"      → keine 2026-Daten, Gruppe traegt 0 bei")

    print("  [F] Wettquoten (Jury- + Tele-Odds getrennt)...")
    f_source = "LOYO-CV" if "F_odds" in jury_base else "Fallback"
    if odds_active:
        n_odds = sum(1 for v in ODDS_JURY_2026.values() if v > 0)
        print(f"      → {n_odds} Laender verfuegbar  [Jury-Odds / Tele-Odds separat, Gewicht: {f_source}]")
    else:
        print("      → keine Daten, Gruppe deaktiviert")

    print("  [H] Rehearsal Press Scores...")
    if rehearsal_active:
        n_reh = sum(1 for v in REHEARSAL_SCORES_2026.values() if v > 0)
        print(f"      → {n_reh} Laender verfuegbar")
    else:
        print("      → keine Daten, Gruppe deaktiviert")

    # ── Feature-Matrix ────────────────────────────────────────────────────────
    feat_df = build_prediction_rows(
        voters, finalists, bilateral, poll, youtube, running, language, hist_perf,
        sf_rank=sf_rank, eurojury=eurojury,
    )

    # ── Gruppen-Totals (A/B/C/E/G via XGBoost) ───────────────────────────────
    grp_totals = _group_totals(feat_df, voters, group_models, finalists)

    # ── F: Odds → ESC-Voter-Simulation (Jury und Tele getrennt) ─────────────────
    jury_odds_signal = {cc: market[cc]["odds_jury_prob"] for cc in finalists}
    tele_odds_signal = {cc: market[cc]["odds_tele_prob"] for cc in finalists}
    jury_odds_pts = _signal_to_esc_pts(jury_odds_signal, voters, finalists) if odds_active else {}
    tele_odds_pts = _signal_to_esc_pts(tele_odds_signal, voters, finalists) if odds_active else {}

    # ── H: Rehearsal → ESC-Voter-Simulation ──────────────────────────────────
    reh_signal   = {cc: market[cc]["rehearsal_score_norm"] for cc in finalists}
    reh_esc_pts  = _signal_to_esc_pts(reh_signal, voters, finalists) if rehearsal_active else {}

    # ── Effektive Gewichte berechnen ──────────────────────────────────────────
    # H (Rehearsal): manuell, skaliert restliche Gewichte
    w_H_jury = REHEARSAL_WEIGHT["jury"] if rehearsal_active else 0.0
    w_H_tele = REHEARSAL_WEIGHT["tele"] if rehearsal_active else 0.0
    scale    = 1.0 - w_H_jury   # jury
    scale_t  = 1.0 - w_H_tele  # tele

    # A/B/C/E/G/F: aus weights.json, mit 0 für F wenn keine Odds
    def _effective_weights(base: dict, odds_ok: bool, scale: float) -> dict:
        w = dict(base)
        if not odds_ok:
            w["F_odds"] = 0.0
        total = sum(w.values()) or 1.0
        return {k: v / total * scale for k, v in w.items()}

    jury_w = _effective_weights(jury_base, odds_active, scale)
    tele_w = _effective_weights(tele_base, odds_active, scale_t)

    # ── Finale gewichtete Addition ────────────────────────────────────────────
    jury_final: dict[str, float] = defaultdict(float)
    tele_final: dict[str, float] = defaultdict(float)

    for grp in FEATURE_GROUPS:
        wj = jury_w.get(grp, 0.0)
        wt = tele_w.get(grp, 0.0)
        for cc in finalists:
            jury_final[cc] += wj * grp_totals[grp]["jury"].get(cc, 0)
            tele_final[cc] += wt * grp_totals[grp]["tele"].get(cc, 0)

    for cc in finalists:
        jury_final[cc] += jury_w.get("F_odds", 0) * jury_odds_pts.get(cc, 0)
        tele_final[cc] += tele_w.get("F_odds", 0) * tele_odds_pts.get(cc, 0)
        jury_final[cc] += w_H_jury * reh_esc_pts.get(cc, 0)
        tele_final[cc] += w_H_tele * reh_esc_pts.get(cc, 0)

    # ── Gewichtsübersicht ─────────────────────────────────────────────────────
    all_jury_w = {**jury_w, "H_rehearsal": w_H_jury}
    all_tele_w = {**tele_w, "H_rehearsal": w_H_tele}
    total_j = sum(all_jury_w.values())
    total_t = sum(all_tele_w.values())

    print(f"\n{'─'*65}")
    print(f"  Gewichte Jury  (Σ={total_j:.3f})  [F: {f_source}]")
    for grp, w in sorted(all_jury_w.items(), key=lambda x: -x[1]):
        if w > 0.001:
            bar = "█" * int(w * 40)
            print(f"    {grp:<26} {w*100:>5.1f}%  {bar}")
    print(f"  Gewichte Tele  (Σ={total_t:.3f})  [F: {f_source}]")
    for grp, w in sorted(all_tele_w.items(), key=lambda x: -x[1]):
        if w > 0.001:
            bar = "█" * int(w * 40)
            print(f"    {grp:<26} {w*100:>5.1f}%  {bar}")
    print(f"{'─'*65}")

    # ── Tabelle ───────────────────────────────────────────────────────────────
    lang_map = language
    rows = []
    for cc in finalists:
        info  = all_entries.get(cc, {"country": cc, "artist": "", "song": ""})
        jury  = round(jury_final[cc])
        tele  = round(tele_final[cc])
        total = jury + tele
        rows.append({
            "country":    info["country"],
            "code":       cc,
            "artist":     info["artist"],
            "song":       info["song"],
            "poll_score":    round(poll.get(cc, {}).get("poll_score_norm", 0) * 100, 1),
            "yt_log":        round(youtube.get(cc, {}).get("log_views", 0), 2),
            "odds_jury%":    round(market[cc]["odds_jury_prob"] * 100, 1),
            "odds_tele%":    round(market[cc]["odds_tele_prob"] * 100, 1),
            "jury_pts":      jury,
            "tele_pts":      tele,
            "total_pts":     total,
        })

    df = (
        pd.DataFrame(rows)
        .sort_values("total_pts", ascending=False)
        .reset_index(drop=True)
    )
    df.index += 1
    df.index.name = "rank"

    print(f"\n{'Rk':<4} {'Country':<18} {'Artist':<26} "
          f"{'Poll%':>6} {'YT':>5} {'JOdds%':>7} {'TOdds%':>7} "
          f"{'EN':>2} {'Jury':>5} {'Tele':>5} {'Total':>6}")
    print("-" * 96)
    for rank, row in df.iterrows():
        en = "Y" if lang_map.get(row["code"], 0) else "N"
        print(f"{rank:<4} {row['country']:<18} {row['artist']:<26} "
              f"{row['poll_score']:>5.1f}%"
              f" {row['yt_log']:>5.2f}"
              f" {row['odds_jury%']:>6.1f}%"
              f" {row['odds_tele%']:>6.1f}%"
              f" {en:>2}"
              f"{row['jury_pts']:>5} {row['tele_pts']:>5} {row['total_pts']:>6}")

    out_csv  = Path(output_dir) / "predictions_2026.csv"
    out_json = Path(output_dir) / "predictions_2026.json"
    df.to_csv(out_csv)
    df.reset_index().to_json(out_json, orient="records", indent=2, force_ascii=False)
    print(f"\nGespeichert → {out_csv}")
    return df


if __name__ == "__main__":
    predict_2026()
