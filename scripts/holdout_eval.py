"""Score LightGBM once on the held-out evaluation week, using the dataset authors' protocol.

Every day of the evaluation week is forecast from the end of the train split, so
features are at least 7 days old, and the main scores count only stockout-free days.
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from forecasting.baselines import same_day_last_week
from forecasting.data import daily_from_frn
from forecasting.evaluation import evaluate, last_weeks
from forecasting.features import add_features
from forecasting.model import fit_quantile_models, predict_quantiles

# The hourly arrays are only needed for the stockout correction. Leaving them out
# keeps all 898 stores small enough for a laptop's memory.
COLUMNS = [
    "store_id",
    "product_id",
    "dt",
    "sale_amount",
    "stock_hour6_22_cnt",
    "first_category_id",
    "discount",
    "activity_flag",
    "holiday_flag",
    "precpt",
    "avg_temperature",
    "avg_humidity",
    "avg_wind_level",
]

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/frn/stores_898")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    raw = pd.concat(
        pd.read_parquet(data_dir / f"{split}.parquet", columns=COLUMNS)
        for split in ("train", "eval")
    )
    logger.info("Building features for %d rows", len(raw))
    daily = add_features(daily_from_frn(raw), gap=7)

    # The evaluation split is the final 7 days, so last_weeks selects exactly it.
    eval_week = last_weeks(daily, n_weeks=1)
    logger.info("Training on %d rows", (~eval_week).sum())
    models = fit_quantile_models(daily[~eval_week], [0.5])
    model_p50 = predict_quantiles(models, daily[eval_week])["p50"].reindex(daily.index)

    scores = {
        "Same day last week": evaluate(daily, same_day_last_week(daily), n_weeks=1),
        "LightGBM P50": evaluate(daily, model_p50, n_weeks=1),
    }
    stockout_free = eval_week & (daily["stockout_hours"] == 0)
    print(
        f"{eval_week.sum()} store-product days evaluated, {stockout_free.sum()} stockout-free"
    )
    print(pd.DataFrame(scores).T.round(4).to_string())


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    logger.setLevel(logging.INFO)
    main()
