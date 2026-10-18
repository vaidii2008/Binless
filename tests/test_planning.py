from pathlib import Path

import pandas as pd
import pytest

from forecasting.planning import (
    ShopModels,
    load_models,
    plan_orders,
    save_models,
    train_shop_models,
)
from forecasting.simulation import CATEGORIES, PRODUCTS, simulate_shop

TOMORROW = pd.Timestamp("2026-10-20")
SHELF_BALANCE = [("Fewer leftovers", 0.5), ("Rarely run out", 4.0)]
CRITICAL_RATIOS = {name: c.costs.critical_ratio for name, c in CATEGORIES.items()}


@pytest.fixture(scope="module")
def daily() -> pd.DataFrame:
    return simulate_shop(TOMORROW.date(), n_days=60, seed=3)


@pytest.fixture(scope="module")
def models(daily: pd.DataFrame) -> ShopModels:
    return train_shop_models(daily[daily["date"] < TOMORROW], quantiles=[0.5, 0.9])


def test_saved_models_load_with_the_same_predictions(
    models: ShopModels, daily: pd.DataFrame, tmp_path: Path
) -> None:
    save_models(models, tmp_path)
    loaded = load_models(tmp_path)
    assert sorted(loaded.quantile_models) == [0.5, 0.9]
    before = plan_orders(daily, TOMORROW, models, CRITICAL_RATIOS, SHELF_BALANCE)
    after = plan_orders(daily, TOMORROW, loaded, CRITICAL_RATIOS, SHELF_BALANCE)
    assert before == after


def test_load_models_fails_on_an_empty_folder(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_models(tmp_path)


def test_plan_covers_every_product_with_one_order_per_slider_position(
    models: ShopModels, daily: pd.DataFrame
) -> None:
    plans = plan_orders(daily, TOMORROW, models, CRITICAL_RATIOS, SHELF_BALANCE)
    assert [plan["product_name"] for plan in plans] == [name for name, *_ in PRODUCTS]
    for plan in plans:
        assert [order["label"] for order in plan["orders"]] == [
            "Fewer leftovers",
            "Rarely run out",
        ]
        assert plan["orders"][0]["units"] <= plan["orders"][1]["units"]
        assert plan["quantiles"]["p50"] <= plan["quantiles"]["p90"]
        assert plan["reasons"]


def test_plan_ignores_tomorrows_recorded_sales(
    models: ShopModels, daily: pd.DataFrame
) -> None:
    leaked = daily.copy()
    leaked.loc[leaked["date"] == TOMORROW, "sales"] = 10_000
    assert plan_orders(
        leaked, TOMORROW, models, CRITICAL_RATIOS, SHELF_BALANCE
    ) == plan_orders(daily, TOMORROW, models, CRITICAL_RATIOS, SHELF_BALANCE)
