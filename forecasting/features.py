"""Build the model's features from the daily table without looking ahead."""

import numpy as np
import pandas as pd

from forecasting.data import SERIES_KEYS

CATEGORICAL_FEATURES = ["day_of_week", "category_id"]
FEATURES = [
    "lag_1",
    "lag_7",
    "lag_14",
    "mean_7",
    "cv_28",
    *CATEGORICAL_FEATURES,
    "discount",
    "activity",
    "holiday",
    "precipitation",
    "temperature",
    "humidity",
    "wind_level",
]


def add_features(
    daily: pd.DataFrame, target_column: str = "sales", gap: int = 1
) -> pd.DataFrame:
    """Return the daily table with the scale, the model features and the scaled target.

    Lags, rolling statistics and the scale only use days at least `gap` days before
    each row's date: gap=1 forecasts tomorrow, gap=7 forecasts any day of the coming
    week. Lags shorter than the gap would be unknown, so they're NaN. The scale is
    the series' mean sales over 28 days, so one model can learn from every series
    whatever its size. It's missing until a series has 28 days of history and for
    any series that sold nothing in that time. The target is target_column divided
    by the scale, so passing corrected demand trains the model on demand instead of
    recorded sales.
    """
    sales = daily.groupby(SERIES_KEYS)["sales"]
    scale = sales.transform(lambda s: s.shift(gap).rolling(28).mean())
    scale = scale.where(scale > 0)
    lags = {
        f"lag_{days}": sales.shift(days) / scale if days >= gap else np.nan
        for days in (1, 7, 14)
    }
    return daily.assign(
        scale=scale,
        **lags,
        mean_7=sales.transform(lambda s: s.shift(gap).rolling(7).mean()) / scale,
        cv_28=sales.transform(lambda s: s.shift(gap).rolling(28).std()) / scale,
        day_of_week=daily["date"].dt.dayofweek,
        target=daily[target_column] / scale,
    )
