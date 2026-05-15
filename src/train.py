"""
Train two XGBoost regression models:
  1. jury_model    – predicts jury points given from country -> to country
  2. tele_model    – predicts televote points

Feature importances are reported both per-feature and grouped by the 4 signal
types (A=Historical Voting, B=Community Poll, C=YouTube, D=Spotify Proxy),
so you can see exactly how much each signal contributes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

from config import DIR_PROCESSED, YEARS_TRAIN
from build_dataset import FEATURE_COLS, FEATURE_GROUPS

MODEL_PARAMS = {
    "n_estimators":     500,
    "max_depth":        5,
    "learning_rate":    0.04,
    "subsample":        0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,
    "reg_alpha":        0.1,
    "reg_lambda":       1.0,
    "random_state":     42,
    "n_jobs":           -1,
}


def load_training_data(data_dir=DIR_PROCESSED) -> pd.DataFrame:
    path = Path(data_dir) / "training_data.csv"
    if not path.exists():
        raise FileNotFoundError("Run build_dataset.py first.")
    return pd.read_csv(path)


def cross_validate(df: pd.DataFrame, target: str) -> float:
    """Leave-one-year-out CV; returns mean MAE across years."""
    maes = []
    for test_year in YEARS_TRAIN:
        train = df[df["year"] != test_year]
        test  = df[df["year"] == test_year]
        if test.empty or train.empty:
            continue
        model = XGBRegressor(**MODEL_PARAMS)
        model.fit(train[FEATURE_COLS], train[target], verbose=False)
        preds = np.clip(model.predict(test[FEATURE_COLS]), 0, 12)
        maes.append(mean_absolute_error(test[target], preds))
    return float(np.mean(maes)) if maes else float("nan")


def train_model(df: pd.DataFrame, target: str) -> XGBRegressor:
    model = XGBRegressor(**MODEL_PARAMS)
    model.fit(df[FEATURE_COLS], df[target], verbose=False)
    return model


def save_model(model: XGBRegressor, name: str, data_dir=DIR_PROCESSED):
    path = Path(data_dir) / f"{name}.json"
    model.save_model(str(path))


def load_model(name: str, data_dir=DIR_PROCESSED) -> XGBRegressor:
    path = Path(data_dir) / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} – run train.py first.")
    model = XGBRegressor()
    model.load_model(str(path))
    return model


def train_group_models(df: pd.DataFrame, data_dir=DIR_PROCESSED):
    """Train one jury+tele model per feature group and save them."""
    from build_dataset import FEATURE_GROUPS
    for grp, cols in FEATURE_GROUPS.items():
        present = [c for c in cols if c in df.columns]
        if not present:
            continue
        for target in ["jury_pts", "tele_pts"]:
            prefix = "jury" if "jury" in target else "tele"
            model = XGBRegressor(**MODEL_PARAMS)
            model.fit(df[present], df[target], verbose=False)
            save_model(model, f"{prefix}_model_{grp}", data_dir)
    print("  Saved per-group models.")


def load_group_models(data_dir=DIR_PROCESSED) -> dict:
    """Load all per-group models. Returns {grp: {jury: model, tele: model}}."""
    from build_dataset import FEATURE_GROUPS
    models = {}
    for grp in FEATURE_GROUPS:
        jury_path = Path(data_dir) / f"jury_model_{grp}.json"
        tele_path = Path(data_dir) / f"tele_model_{grp}.json"
        if jury_path.exists() and tele_path.exists():
            j = XGBRegressor(); j.load_model(str(jury_path))
            t = XGBRegressor(); t.load_model(str(tele_path))
            models[grp] = {"jury": j, "tele": t}
    return models


def _importance_table(
    jury_model: XGBRegressor,
    tele_model: XGBRegressor,
) -> pd.DataFrame:
    """Build per-feature and per-group importance table."""
    imp = pd.DataFrame({
        "feature":    FEATURE_COLS,
        "jury_gain":  jury_model.feature_importances_,
        "tele_gain":  tele_model.feature_importances_,
    })
    # Assign signal group
    feat_to_group = {
        f: grp
        for grp, feats in FEATURE_GROUPS.items()
        for f in feats
    }
    imp["signal_group"] = imp["feature"].map(feat_to_group)
    # Normalise importances to percentages
    imp["jury_pct"]  = imp["jury_gain"]  / imp["jury_gain"].sum()  * 100
    imp["tele_pct"]  = imp["tele_gain"]  / imp["tele_gain"].sum()  * 100
    return imp.sort_values("jury_pct", ascending=False)


def print_importance(imp: pd.DataFrame):
    print("\n" + "=" * 72)
    print("FEATURE IMPORTANCE  (% of total model gain)")
    print("=" * 72)
    print(f"{'Feature':<26} {'Group':<26} {'Jury%':>7} {'Tele%':>7}")
    print("-" * 72)
    for _, row in imp.iterrows():
        print(f"  {row['feature']:<24} {row['signal_group']:<26} "
              f"{row['jury_pct']:>6.1f}%  {row['tele_pct']:>6.1f}%")

    # Group-level summary
    grp = imp.groupby("signal_group")[["jury_pct", "tele_pct"]].sum()
    print("\n" + "=" * 72)
    print("SIGNAL GROUP SUMMARY")
    print("=" * 72)
    print(f"{'Signal group':<34} {'Jury %':>8} {'Tele %':>8}")
    print("-" * 72)
    for g, row in grp.sort_values("jury_pct", ascending=False).iterrows():
        label = {
            "A_historical_voting": "[A] Historical Voting",
            "B_community_poll":    "[B] Community Poll (OGAE + Fan)",
            "C_youtube":           "[C] YouTube Views",
            "D_spotify_proxy":     "[D] Spotify Proxy (BPM/Key)",
        }.get(g, g)
        print(f"  {label:<32} {row['jury_pct']:>7.1f}%  {row['tele_pct']:>7.1f}%")
    print("=" * 72)


def run_training(data_dir=DIR_PROCESSED):
    print("Loading training data...")
    df = load_training_data(data_dir)
    n_years   = df["year"].nunique()
    n_cands   = df["to_country"].nunique()
    n_voters  = df["from_country"].nunique()
    print(f"  {len(df):,} rows | {n_years} years | "
          f"{n_cands} candidates | {n_voters} voters")

    # Check all feature groups have non-zero variance (signals are active)
    print("\nData coverage per signal group:")
    for grp, cols in FEATURE_GROUPS.items():
        present = [c for c in cols if c in df.columns]
        nonzero = (df[present] != 0).any(axis=1).mean() * 100
        print(f"  {grp}: {nonzero:.0f}% of rows have at least one non-zero feature")

    print("\nLeave-one-year-out cross-validation...")
    jury_mae = cross_validate(df, "jury_pts")
    tele_mae = cross_validate(df, "tele_pts")
    print(f"  Jury  MAE: {jury_mae:.3f} pts/voter")
    print(f"  Tele  MAE: {tele_mae:.3f} pts/voter")
    print(f"  (Baseline for comparison: always predict 0 -> "
          f"MAE={df['jury_pts'].mean():.3f})")

    print("\nTraining final models on all years...")
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    jury_model = train_model(df, "jury_pts")
    tele_model = train_model(df, "tele_pts")
    save_model(jury_model, "jury_model", data_dir)
    save_model(tele_model, "tele_model", data_dir)
    print("  Saved jury_model.json + tele_model.json")
    train_group_models(df, data_dir)

    imp = _importance_table(jury_model, tele_model)
    imp_path = Path(data_dir) / "feature_importance.csv"
    imp.to_csv(imp_path, index=False)
    print_importance(imp)

    return jury_model, tele_model


if __name__ == "__main__":
    run_training()
