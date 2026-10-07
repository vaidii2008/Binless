import numpy as np
import pandas as pd
import pytest

from forecasting.stockouts import (
    correct_for_stockouts,
    hourly_profile,
    profile_groups,
    simulate_sellouts,
)

UNIFORM_PROFILE = pd.DataFrame([[1 / 16] * 16], index=[1], columns=range(6, 22))


def test_simulate_sellouts_hides_sales_from_the_cut_hour() -> None:
    hourly_sales = np.zeros(24)
    hourly_sales[[9, 15]] = [1.0, 3.0]
    days = pd.DataFrame(
        {"sales": [4.0], "stockout_hours": [0], "hourly_sales": [hourly_sales]}
    )
    simulated = simulate_sellouts(days, np.array([12]))
    assert simulated["sales"].iloc[0] == pytest.approx(1.0)
    assert simulated["stockout_hours"].iloc[0] == 10
    assert simulated["hourly_out_of_stock"].iloc[0][11:13].tolist() == [0, 1]


def out_of_stock_from(hour: int) -> np.ndarray:
    """Return 24 hourly stock flags, out of stock from the given hour onwards."""
    flags = np.zeros(24, dtype=int)
    flags[hour:] = 1
    return flags


def test_hourly_profile_ignores_days_with_stockouts() -> None:
    morning = np.zeros(24)
    morning[8] = 2.0
    evening = np.zeros(24)
    evening[18] = 5.0
    daily = pd.DataFrame(
        {
            "category_id": [1, 1],
            "sales": [2.0, 5.0],
            "stockout_hours": [0, 3],
            "hourly_sales": [morning, evening],
        }
    )
    profile = hourly_profile(daily, by="category_id")
    assert profile.loc[1, 8] == pytest.approx(1.0)
    assert profile.loc[1].sum() == pytest.approx(1.0)


def test_correction_scales_sales_by_the_share_of_usual_sales_in_stock() -> None:
    daily = pd.DataFrame(
        {
            "category_id": [1, 1, 1],
            "sales": [4.0, 4.0, 0.0],
            "hourly_out_of_stock": [
                np.zeros(24, dtype=int),
                out_of_stock_from(14),
                out_of_stock_from(6),
            ],
        }
    )
    demand = correct_for_stockouts(daily, UNIFORM_PROFILE, by="category_id")
    assert demand.iloc[0] == pytest.approx(4.0)
    assert demand.iloc[1] == pytest.approx(8.0)
    assert np.isnan(demand.iloc[2])


def test_profile_groups_split_categories_by_weekend() -> None:
    daily = pd.DataFrame(
        {"category_id": [3, 3], "date": pd.to_datetime(["2024-04-05", "2024-04-06"])}
    )
    assert profile_groups(daily).tolist() == ["3 weekday", "3 weekend"]
