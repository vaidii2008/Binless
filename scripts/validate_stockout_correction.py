"""Measure how well the stockout correction recovers sales hidden by simulated sell-outs."""

import argparse

import numpy as np
import pandas as pd

from forecasting.data import daily_from_frn
from forecasting.evaluation import last_weeks
from forecasting.metrics import bias, wape
from forecasting.stockouts import (
    correct_for_stockouts,
    hourly_profile,
    profile_groups,
    simulate_sellouts,
)

PROFILES = {
    "Global profile": "all_products",
    "Category profile": "category_id",
    "Category and day profile": "profile_group",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/frn/stores_50/train.parquet")
    parser.add_argument("--weeks", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    daily = daily_from_frn(pd.read_parquet(args.data)).assign(all_products=0)
    daily["profile_group"] = profile_groups(daily)
    test_window = last_weeks(daily, args.weeks)
    history = daily[~test_window]
    days = daily[test_window & (daily["stockout_hours"] == 0) & (daily["sales"] > 0)]
    cut_hours = np.random.default_rng(args.seed).integers(10, 21, size=len(days))
    simulated = simulate_sellouts(days, cut_hours)

    estimates = {"No correction": simulated["sales"]}
    for label, by in PROFILES.items():
        profile = hourly_profile(history, by)
        estimates[label] = correct_for_stockouts(simulated, profile, by)

    scores = {
        label: {
            "wape": wape(days["sales"], estimate),
            "bias": bias(days["sales"], estimate),
            "days_estimated": estimate.notna().mean(),
        }
        for label, estimate in estimates.items()
    }
    print(f"{len(days)} fully stocked days, sold out at random from 10:00 to 20:00")
    print(pd.DataFrame(scores).T.round(3).to_string())


if __name__ == "__main__":
    main()
