"""Turn a forecast's strongest drivers into short reasons a shop owner can read."""

import lightgbm as lgb
import numpy as np
import pandas as pd

from forecasting.features import FEATURES

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

REASONS = {
    "lag_1": lambda row: f"Sold {row['lag_1'] * row['scale']:.0f} yesterday",
    "lag_7": lambda row: (
        f"Sold {row['lag_7'] * row['scale']:.0f} on the same day last week"
    ),
    "lag_14": lambda row: (
        f"Sold {row['lag_14'] * row['scale']:.0f} on the same day two weeks ago"
    ),
    "mean_7": lambda row: (
        f"Averaged {row['mean_7'] * row['scale']:.0f} a day over the last week"
    ),
    "cv_28": lambda row: (
        "Sales have been up and down lately"
        if row["cv_28"] > 0.5
        else "Sales have been steady lately"
    ),
    "day_of_week": lambda row: f"It's a {DAY_NAMES[int(row['day_of_week'])]}",
    "category_id": lambda row: "The usual pattern for this kind of product",
    "discount": lambda row: (
        f"On promotion at {round(100 * (1 - row['discount']))}% off"
        if row["discount"] < 1
        else "Not on promotion"
    ),
    "activity": lambda row: (
        "Part of a store promotion" if row["activity"] else "No store promotion"
    ),
    "holiday": lambda row: "Bank holiday" if row["holiday"] else "Not a bank holiday",
    "precipitation": lambda row: f"{row['precipitation']:.0f} mm of rain forecast",
    "temperature": lambda row: f"{row['temperature']:.0f}°C forecast",
    "humidity": lambda row: f"{row['humidity']:.0f}% humidity forecast",
    "wind_level": lambda row: (
        "Windy forecast" if row["wind_level"] > 3 else "Calm forecast"
    ),
}


def top_reasons(
    model: lgb.Booster, rows: pd.DataFrame, n_reasons: int = 2
) -> list[list[dict[str, str]]]:
    """Return each row's strongest drivers as plain-English reasons with a direction.

    The drivers come from LightGBM's per-feature contributions, so a reason only
    appears when that feature actually moved this row's forecast.
    Pass the model from fit_explanation_model, since contributions from quantile models don't add up
    """
    contributions = model.predict(rows[FEATURES], pred_contrib=True)[:, :-1]
    all_reasons = []
    for row_contributions, (_, row) in zip(contributions, rows.iterrows(), strict=True):
        strongest = np.argsort(-np.abs(row_contributions))[:n_reasons]
        all_reasons.append(
            [
                {
                    "text": REASONS[FEATURES[i]](row),
                    "direction": "up" if row_contributions[i] > 0 else "down",
                }
                for i in strongest
            ]
        )
    return all_reasons
