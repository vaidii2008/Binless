from datetime import date

import pandas as pd

from forecasting.simulation import CATEGORIES, PRODUCTS, simulate_shop

HOURLY_COLUMNS = ["hourly_sales", "hourly_out_of_stock"]


def test_every_category_has_a_full_week_and_trading_day() -> None:
    for category in CATEGORIES.values():
        assert len(category.weekday_factors) == 7
        assert len(category.hourly_weights) == 16


def test_every_product_belongs_to_a_known_category() -> None:
    assert len(PRODUCTS) == 20
    assert {category for _, category, _ in PRODUCTS} <= set(CATEGORIES)


def test_simulation_is_reproducible_and_covers_every_product_day() -> None:
    first = simulate_shop(date(2026, 10, 7), n_days=30, seed=1)
    second = simulate_shop(date(2026, 10, 7), n_days=30, seed=1)
    pd.testing.assert_frame_equal(
        first.drop(columns=HOURLY_COLUMNS), second.drop(columns=HOURLY_COLUMNS)
    )
    assert len(first) == len(PRODUCTS) * 30
    assert first["date"].max() == pd.Timestamp("2026-10-07")


def test_sales_never_exceed_demand_and_some_days_sell_out() -> None:
    daily = simulate_shop(date(2026, 10, 7), n_days=60, seed=1)
    assert (daily["sales"] <= daily["true_demand"]).all()
    assert 0 < (daily["stockout_hours"] > 0).mean() < 0.6
