"""Backtest LightGBM quantile forecasts against the baselines, retraining weekly."""

import argparse
import logging
import time

import pandas as pd

from forecasting.baselines import moving_average_7, same_day_last_week
from forecasting.data import daily_from_frn
from forecasting.evaluation import evaluate, last_weeks, weekly_folds
from forecasting.features import add_features
from forecasting.model import fit_quantile_models, predict_quantiles

QUANTILES = [0.5, 0.8, 0.9]
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/frn/stores_50/train.parquet")
    parser.add_argument("--weeks", type=int, default=4)
    args = parser.parse_args()

    daily = add_features(daily_from_frn(pd.read_parquet(args.data)))
    weekly_forecasts = []
    folds = weekly_folds(daily, args.weeks)
    for week_number, (start, end) in enumerate(folds, start=1):
        started = time.perf_counter()
        models = fit_quantile_models(daily[daily["date"] < start], QUANTILES)
        week = daily[(daily["date"] >= start) & (daily["date"] < end)]
        weekly_forecasts.append(predict_quantiles(models, week))
        elapsed = time.perf_counter() - started
        logger.info(
            "Week %d of %d from %s: %.0fs",
            week_number,
            len(folds),
            start.date(),
            elapsed,
        )
    forecasts = pd.concat(weekly_forecasts).reindex(daily.index)

    scores = {
        "Same day last week": evaluate(daily, same_day_last_week(daily), args.weeks),
        "7-day moving average": evaluate(daily, moving_average_7(daily), args.weeks),
        "LightGBM P50": evaluate(daily, forecasts["p50"], args.weeks),
    }
    print(pd.DataFrame(scores).T.round(3).to_string())

    test = last_weeks(daily, args.weeks)
    for column in ("p80", "p90"):
        covered = (daily.loc[test, "sales"] <= forecasts.loc[test, column]).mean()
        print(f"Days with sales at or below {column.upper()}: {covered:.1%}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    logger.setLevel(logging.INFO)
    main()
