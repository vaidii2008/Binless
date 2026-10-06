import numpy as np
import pandas as pd
import pytest

from forecasting.metrics import bias, wape


def test_wape_is_total_absolute_error_over_total_actual() -> None:
    actual = pd.Series([10.0, 20.0, 30.0])
    forecast = pd.Series([12.0, 18.0, 30.0])
    assert wape(actual, forecast) == pytest.approx(4 / 60)


def test_bias_is_positive_when_the_forecast_is_too_high() -> None:
    actual = pd.Series([10.0, 20.0])
    forecast = pd.Series([15.0, 20.0])
    assert bias(actual, forecast) == pytest.approx(5 / 30)


def test_metrics_skip_rows_without_a_forecast() -> None:
    actual = pd.Series([100.0, 10.0])
    forecast = pd.Series([np.nan, 12.0])
    assert wape(actual, forecast) == pytest.approx(0.2)
    assert bias(actual, forecast) == pytest.approx(0.2)


def test_metrics_reject_zero_total_actual_sales() -> None:
    with pytest.raises(ValueError):
        wape(pd.Series([0.0]), pd.Series([1.0]))
