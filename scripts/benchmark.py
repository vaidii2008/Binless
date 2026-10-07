"""Benchmark forecasts and order policies on the final weeks of a FreshRetailNet-50K subset."""

import argparse
import logging
import time

import pandas as pd

from forecasting.baselines import moving_average_7, same_day_last_week
from forecasting.data import daily_from_frn
from forecasting.evaluation import evaluate, last_weeks, weekly_folds
from forecasting.features import add_features
from forecasting.model import fit_quantile_models, predict_quantiles
from forecasting.ordering import order_outcomes
from forecasting.stockouts import correct_for_stockouts, hourly_profile, profile_groups

QUANTILES = [0.5, 0.8, 0.9]

logger = logging.getLogger(__name__)


def backtest(daily: pd.DataFrame, n_weeks: int, target_column: str) -> pd.DataFrame:
    """Return quantile forecasts for the last n_weeks, retraining before each week."""
    features = add_features(daily, target_column)
    weekly_forecasts = []
    for start, end in weekly_folds(features, n_weeks):
        started = time.perf_counter()
        models = fit_quantile_models(features[features["date"] < start], QUANTILES)
        week = features[(features["date"] >= start) & (features["date"] < end)]
        weekly_forecasts.append(predict_quantiles(models, week))
        elapsed = time.perf_counter() - started
        logger.info("%s, week from %s: %.0fs", target_column, start.date(), elapsed)
    return pd.concat(weekly_forecasts).reindex(features.index)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/frn/stores_50/train.parquet")
    parser.add_argument("--weeks", type=int, default=4)
    args = parser.parse_args()

    daily = daily_from_frn(pd.read_parquet(args.data))
    # The profile only uses weeks before the test window, so no test day shapes its own correction.

    daily["profile_group"] = profile_groups(daily)
    history = daily[~last_weeks(daily, args.weeks)]
    profile = hourly_profile(history, by="profile_group")
    daily["demand"] = correct_for_stockouts(daily, profile, by="profile_group")
    estimated = daily["demand"].notna()
    uplift = daily.loc[estimated, "demand"].sum() / daily.loc[estimated, "sales"].sum()
    print(
        f"Corrected demand estimated on {estimated.mean():.1%} of days, "
        f"at {uplift:.3f} times recorded sales"
    )

    runs = {
        "LightGBM on raw sales": backtest(daily, args.weeks, "sales"),
        "LightGBM on corrected demand": backtest(daily, args.weeks, "demand"),
    }
    scores = {
        "Same day last week": evaluate(daily, same_day_last_week(daily), args.weeks),
        "7-day moving average": evaluate(daily, moving_average_7(daily), args.weeks),
    }
    for label, forecasts in runs.items():
        scores[f"{label}, P50"] = evaluate(daily, forecasts["p50"], args.weeks)
    print(pd.DataFrame(scores).T.round(3).to_string())

    test = last_weeks(daily, args.weeks)
    stocked = test & (daily["stockout_hours"] == 0)
    for label, forecasts in runs.items():
        for column in ("p80", "p90"):
            below = daily["sales"] <= forecasts[column]
            print(
                f"{label}: sales at or below {column.upper()} on "
                f"{below[test].mean():.1%} of all days, "
                f"{below[stocked].mean():.1%} of fully stocked days"
            )
    policies = {
        "Order last week's sales": same_day_last_week(daily),
        "Order the 7-day average": moving_average_7(daily),
    }
    for label, forecasts in runs.items():
        for column in forecasts.columns:
            policies[f"{label}, {column.upper()}"] = forecasts[column]

    outcomes = {}
    for label, orders in policies.items():
        on_stocked = order_outcomes(orders[stocked], daily.loc[stocked, "sales"])
        on_all = order_outcomes(orders[test], daily.loc[test, "demand"])
        outcomes[label] = {
            f"stocked_{key}": value for key, value in on_stocked.items()
        } | {f"all_{key}": value for key, value in on_all.items()}
    print(pd.DataFrame(outcomes).T.round(3).to_string())


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    logger.setLevel(logging.INFO)
    main()
