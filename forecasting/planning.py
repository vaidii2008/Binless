"""Train, save and load a shop's models, and turn them into tomorrow's order plan."""

from dataclasses import dataclass
from math import ceil
from pathlib import Path

import lightgbm as lgb
import pandas as pd

from forecasting.explain import top_reasons
from forecasting.features import add_features
from forecasting.model import (
    fit_explanation_model,
    fit_quantile_models,
    predict_quantiles,
)
from forecasting.ordering import adjusted_ratio, order_quantity

QUANTILES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
EXPLANATION_FILE = "explanation.txt"


@dataclass(frozen=True)
class ShopModels:
    """The quantile models that set orders and the model that explains them."""

    quantile_models: dict[float, lgb.Booster]
    explanation_model: lgb.Booster


def train_shop_models(
    history: pd.DataFrame, quantiles: list[float] = QUANTILES
) -> ShopModels:
    """Return models trained on a shop's daily history of recorded sales."""
    features = add_features(history)
    return ShopModels(
        quantile_models=fit_quantile_models(features, quantiles),
        explanation_model=fit_explanation_model(features),
    )


def save_models(models: ShopModels, directory: Path) -> None:
    """Write each model as a LightGBM text file, named after its quantile."""
    directory.mkdir(parents=True, exist_ok=True)
    for quantile, model in models.quantile_models.items():
        model.save_model(directory / f"p{round(quantile * 100)}.txt")
    models.explanation_model.save_model(directory / EXPLANATION_FILE)


def load_models(directory: Path) -> ShopModels:
    """Return the models that save_models wrote to directory."""
    quantile_models = {
        int(path.stem[1:]) / 100: lgb.Booster(model_file=path)
        for path in directory.glob("p*.txt")
    }
    if not quantile_models:
        raise FileNotFoundError(f"No quantile model files in {directory}")
    return ShopModels(
        quantile_models=quantile_models,
        explanation_model=lgb.Booster(model_file=directory / EXPLANATION_FILE),
    )


def plan_orders(
    daily: pd.DataFrame,
    tomorrow: pd.Timestamp,
    models: ShopModels,
    critical_ratios: dict[str, float],
    shelf_balance: list[tuple[str, float]],
) -> list[dict]:
    """Return tomorrow's plan for each product: its forecast, orders and reasons.

    daily holds each product's history plus a row for tomorrow with its
    promotions, holiday flag and weather forecast. Tomorrow's sales are ignored,
    since a real forecast can't know them. There's one order per shelf_balance
    position, so the dashboard's slider only picks from stored values.
    """
    is_tomorrow = daily["date"] == tomorrow
    features = add_features(daily.assign(sales=daily["sales"].where(~is_tomorrow)))
    rows = features[is_tomorrow]
    grid = predict_quantiles(models.quantile_models, rows)
    reasons = top_reasons(models.explanation_model, rows)

    plans = []
    for (index, row), product_reasons in zip(rows.iterrows(), reasons, strict=True):
        critical_ratio = critical_ratios[row["category"]]
        orders = []
        for label, shelf_weight in shelf_balance:
            level = adjusted_ratio(critical_ratio, shelf_weight)
            units = order_quantity(grid.loc[[index]], level).iloc[0]
            orders.append(
                {
                    "label": label,
                    "units": ceil(units),
                    "sell_out_chance": round(100 * (1 - level)),
                }
            )
        plans.append(
            {
                "product_name": row["product_name"],
                "category": row["category"],
                "quantiles": {
                    column: round(float(grid.at[index, column]), 2)
                    for column in grid.columns
                },
                "orders": orders,
                "reasons": product_reasons,
            }
        )
    return plans
