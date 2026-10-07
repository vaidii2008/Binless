import numpy as np
import pandas as pd
import pytest

from forecasting.ordering import order_outcomes


def test_order_outcomes_count_waste_stockouts_and_service() -> None:
    orders = pd.Series([10.0, 10.0, np.nan])
    demand = pd.Series([6.0, 12.0, 5.0])
    outcomes = order_outcomes(orders, demand)
    assert outcomes["waste_pct"] == pytest.approx(4 / 20)
    assert outcomes["stockout_rate"] == pytest.approx(0.5)
    assert outcomes["service_level"] == pytest.approx(16 / 18)
