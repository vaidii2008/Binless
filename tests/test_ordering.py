import numpy as np
import pandas as pd
import pytest

from forecasting.ordering import Costs, order_outcomes, order_quantity


def test_order_outcomes_count_waste_stockouts_and_service() -> None:
    orders = pd.Series([10.0, 10.0, np.nan])
    demand = pd.Series([6.0, 12.0, 5.0])
    outcomes = order_outcomes(orders, demand)
    assert outcomes["waste_pct"] == pytest.approx(4 / 20)
    assert outcomes["stockout_rate"] == pytest.approx(0.5)
    assert outcomes["service_level"] == pytest.approx(16 / 18)


def test_critical_ratio_weighs_lost_margin_against_waste() -> None:
    assert Costs(price=2.0, unit_cost=1.0).critical_ratio == pytest.approx(0.5)
    assert Costs(price=3.0, unit_cost=1.0).critical_ratio == pytest.approx(2 / 3)
    assert Costs(price=2.0, unit_cost=1.0, salvage=0.5).critical_ratio == pytest.approx(
        2 / 3
    )


def test_order_quantity_interpolates_between_quantiles() -> None:
    forecasts = pd.DataFrame({"p50": [10.0], "p80": [16.0], "p90": [20.0]})
    assert order_quantity(forecasts, 0.5).iloc[0] == pytest.approx(10.0)
    assert order_quantity(forecasts, 0.6).iloc[0] == pytest.approx(12.0)
    assert order_quantity(forecasts, 0.85).iloc[0] == pytest.approx(18.0)
    assert order_quantity(forecasts, 0.3).iloc[0] == pytest.approx(10.0)
