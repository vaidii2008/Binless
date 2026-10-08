"""Forecast tomorrow for the simulated demo shop and write the dashboard's snapshot."""

import json
import logging
from pathlib import Path

import pandas as pd

from forecasting.demo_store import CATEGORIES, STORE_NAME
from forecasting.explain import top_reasons
from forecasting.features import add_features
from forecasting.model import (
    fit_explanation_model,
    fit_quantile_models,
    predict_quantiles,
)

QUANTILES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
SNAPSHOT_PATH = Path("pages/demo_snapshot.json")

logger = logging.getLogger(__name__)


def main() -> None:
    daily = pd.read_parquet("data/demo/simulated.parquet")
    tomorrow = daily["date"].max()
    is_tomorrow = daily["date"] == tomorrow
    # The file holds tomorrow's simulated sales too, which a real forecast can't know.
    daily = daily.assign(
        sales=daily["sales"].where(~is_tomorrow),
        true_demand=daily["true_demand"].where(~is_tomorrow),
    )
    features = add_features(daily)
    history = features[~is_tomorrow]
    rows = features[is_tomorrow]

    grid = predict_quantiles(fit_quantile_models(history, QUANTILES), rows)
    reasons = top_reasons(fit_explanation_model(history), rows)
    products = []
    for (index, row), product_reasons in zip(rows.iterrows(), reasons, strict=True):
        products.append(
            {
                "name": row["product_name"],
                "category": row["category"],
                "critical_ratio": round(
                    CATEGORIES[row["category"]].costs.critical_ratio, 3
                ),
                "forecast": {
                    level: round(float(value), 1)
                    for level, value in grid.loc[index].items()
                },
                "reasons": product_reasons,
            }
        )
    snapshot = {
        "store_name": STORE_NAME,
        "date": tomorrow.date().isoformat(),
        "products": products,
    }
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2) + "\n")
    logger.info(
        "Wrote %d products for %s to %s", len(products), tomorrow.date(), SNAPSHOT_PATH
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    logger.setLevel(logging.INFO)
    main()
