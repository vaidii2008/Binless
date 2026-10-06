"""Simple forecasts that every model has to beat."""

import pandas as pd

from forecasting.data import SERIES_KEYS


def same_day_last_week(daily: pd.DataFrame) -> pd.Series:
    """Forecast each day's sales as the sales seven days earlier in the same series.

    Expects one row per series per consecutive day, sorted by series and date,
    as the data adapters return it. Days without a week of history get NaN.
    """
    return daily.groupby(SERIES_KEYS)["sales"].shift(7)


def moving_average_7(daily: pd.DataFrame) -> pd.Series:
    """Forecast each day's sales as the mean of the seven days before it.

    The shift by one day keeps the day being forecast out of its own average.
    Days without a full week of history get NaN.
    """
    return daily.groupby(SERIES_KEYS)["sales"].transform(
        lambda sales: sales.shift(1).rolling(7).mean()
    )
