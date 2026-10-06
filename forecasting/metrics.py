"""Accuracy measures that compare forecasts with what actually sold."""

import pandas as pd


def wape(actual: pd.Series, forecast: pd.Series) -> float:
    """Return the total absolute error as a share of total actual sales."""
    actual, forecast = _scored(actual, forecast)
    return float((actual - forecast).abs().sum() / actual.sum())


def bias(actual: pd.Series, forecast: pd.Series) -> float:
    """Return the total over-forecast as a share of total actual sales.

    A negative value means the forecast was too low overall.
    """
    actual, forecast = _scored(actual, forecast)
    return float((forecast.sum() - actual.sum()) / actual.sum())


def _scored(actual: pd.Series, forecast: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Return actual and forecast for the rows that have a forecast."""
    has_forecast = forecast.notna()
    if actual[has_forecast].sum() == 0:
        raise ValueError("Actual sales sum to zero on the rows being scored")
    return actual[has_forecast], forecast[has_forecast]
