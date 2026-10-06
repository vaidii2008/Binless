"""Score the two baselines on the final weeks of a FreshRetailNet-50K subset."""

import argparse

import pandas as pd

from forecasting.baselines import moving_average_7, same_day_last_week
from forecasting.data import daily_from_frn
from forecasting.evaluation import evaluate

BASELINES = {
    "Same day last week": same_day_last_week,
    "7-day moving average": moving_average_7,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/frn/stores_50/train.parquet")
    parser.add_argument("--weeks", type=int, default=4)
    args = parser.parse_args()

    daily = daily_from_frn(pd.read_parquet(args.data))
    scores = {
        name: evaluate(daily, baseline(daily), args.weeks)
        for name, baseline in BASELINES.items()
    }
    print(pd.DataFrame(scores).T.round(3).to_string())


if __name__ == "__main__":
    main()
