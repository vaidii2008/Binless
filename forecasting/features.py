"""Build the model's features from the daily table without looking ahead."""

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


# forecasting/features.py
def add_features(daily: pd.DataFrame, target_column: str = "sales") -> pd.DataFrame:
    """Return the daily table with the scale, the model features and the scaled target.

    Lags, rolling statistics and the scale only use days before each row's date.
    The scale is the series' mean sales over the previous 28 days, so one model can
    learn from every series whatever its size. It's missing for a series' first
    28 days and for any series that sold nothing in that time.
    """
    sales = daily.groupby(SERIES_KEYS)["sales"]
    scale = sales.transform(lambda s: s.shift(1).rolling(28).mean())
    scale = scale.where(scale > 0)
    return daily.assign(
        scale=scale,
        lag_1=sales.shift(1) / scale,
        lag_7=sales.shift(7) / scale,
        lag_14=sales.shift(14) / scale,
        mean_7=sales.transform(lambda s: s.shift(1).rolling(7).mean()) / scale,
        cv_28=sales.transform(lambda s: s.shift(1).rolling(28).std()) / scale,
        day_of_week=daily["date"].dt.dayofweek,
        target=daily[target_column] / scale,
    )
