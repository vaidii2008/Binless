"""Forecast tomorrow for the simulated shop and write the dashboard's snapshot."""

import json
import logging
from math import ceil
from pathlib import Path

import pandas as pd

from forecasting.explain import top_reasons
from forecasting.features import add_features
from forecasting.model import (
    fit_explanation_model,
    fit_quantile_models,
    predict_quantiles,
)
from forecasting.ordering import adjusted_ratio, order_quantity
from forecasting.simulation import CATEGORIES, SHELF_BALANCE, STORE_NAME

QUANTILES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
SNAPSHOT_PATH = Path("pages/forecast_snapshot.json")

logger = logging.getLogger(__name__)


def main() -> None:
    daily = pd.read_parquet("data/shop/simulated.parquet")
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
        critical_ratio = CATEGORIES[row["category"]].costs.critical_ratio
        orders = []
        for _, shelf_weight in SHELF_BALANCE:
            level = adjusted_ratio(critical_ratio, shelf_weight)
            units = order_quantity(grid.loc[[index]], level).iloc[0]
            orders.append(
                {"units": ceil(units), "sell_out_chance": round(100 * (1 - level))}
            )
        products.append(
            {
                "name": row["product_name"],
                "category": row["category"],
                "typical_day": round(grid.at[index, "p50"]),
                "busy_day": round(grid.at[index, "p90"]),
                "orders": orders,
                "reasons": product_reasons,
            }
        )
    snapshot = {
        "store_name": STORE_NAME,
        "date": tomorrow.date().isoformat(),
        "balance_labels": [label for label, _ in SHELF_BALANCE],
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
