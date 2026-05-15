"""
Eurovision 2026 Prediction Pipeline
=====================================
Full pipeline runner.  Execute steps selectively via command-line flags.

Usage
-----
  python run.py                    # run full pipeline
  python run.py --fetch            # only fetch raw data
  python run.py --build            # only build feature matrix (needs fetched data)
  python run.py --train            # only train models (needs built dataset)
  python run.py --predict          # only predict 2026 (needs trained models)
  python run.py --fetch --predict  # fetch + predict (skip rebuild/retrain if cached)

Optional flags:
  --force-fetch    re-download even if cached files exist
  --spotify        fetch Spotify features (requires SPOTIFY_CLIENT_ID/SECRET)
  --youtube        fetch YouTube stats  (requires YOUTUBE_API_KEY or scrapes)
"""
import argparse
import sys
import time
from pathlib import Path

# Add src/ to path so imports work without installing the package
sys.path.insert(0, str(Path(__file__).parent / "src"))


def step_fetch(force: bool, do_spotify: bool, do_youtube: bool):
    from fetch_voting import fetch_all_voting
    from fetch_polls import fetch_all_polls, fetch_poll_2026
    from fetch_contestants import fetch_all_meta, build_2026_meta
    from fetch_spotify import fetch_features_for_year
    from fetch_youtube import fetch_youtube_stats
    from config import YEARS_TRAIN

    print("\n== [1/4] Fetching historical voting data ==")
    fetch_all_voting(force=force)

    print("\n== [2/4] Fetching contestant metadata ==")
    all_meta = fetch_all_meta(force=force)

    print("\n== [3/4] Fetching fan polls (eurovisionworld) ==")
    fetch_all_polls(force=force)
    fetch_poll_2026(force=force)

    if do_spotify:
        print("\n== [4a/4] Fetching Spotify audio features ==")
        for year, meta in all_meta.items():
            print(f"  {year}…")
            fetch_features_for_year(year, meta, force=force)
        # 2026
        meta_2026 = build_2026_meta()
        print("  2026…")
        fetch_features_for_year(2026, meta_2026, force=force)

    if do_youtube:
        print("\n== [4b/4] Fetching YouTube view counts ==")
        for year, meta in all_meta.items():
            print(f"  {year}…")
            fetch_youtube_stats(year, meta, force=force)
        meta_2026 = build_2026_meta()
        print("  2026…")
        fetch_youtube_stats(2026, meta_2026, force=force)


def step_build():
    print("\n== Building feature dataset ==")
    from build_dataset import build_training_data
    df = build_training_data()
    print(f"  Dataset: {len(df):,} rows")


def step_train():
    print("\n== Training jury & televote models ==")
    from train import run_training
    run_training()


def step_predict(finalists: list[str] | None = None):
    print("\n== Predicting Eurovision 2026 ==")
    from predict import predict_2026
    predict_2026(finalists=finalists)


def main():
    parser = argparse.ArgumentParser(description="Eurovision 2026 Predictor")
    parser.add_argument("--fetch",    action="store_true", help="Fetch raw data")
    parser.add_argument("--build",    action="store_true", help="Build feature dataset")
    parser.add_argument("--train",    action="store_true", help="Train models")
    parser.add_argument("--predict",  action="store_true", help="Generate predictions")
    parser.add_argument("--force-fetch", action="store_true", help="Re-download even if cached")
    parser.add_argument("--spotify",  action="store_true", help="Fetch Spotify features")
    parser.add_argument("--youtube",  action="store_true", help="Fetch YouTube stats")
    parser.add_argument(
        "--finalists", nargs="+", metavar="CC",
        help="ISO codes of grand-final countries (e.g. AT SE FR …). "
             "Defaults to all 35 entries.",
    )
    args = parser.parse_args()

    # If no step flags given, run everything
    run_all = not any([args.fetch, args.build, args.train, args.predict])

    t0 = time.time()

    if run_all or args.fetch:
        step_fetch(
            force=args.force_fetch,
            do_spotify=args.spotify,
            do_youtube=args.youtube,
        )

    if run_all or args.build:
        step_build()

    if run_all or args.train:
        step_train()

    if run_all or args.predict:
        step_predict(finalists=args.finalists)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
