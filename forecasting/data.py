"""Convert source datasets into the daily table the forecasting code works on."""

import pandas as pd

SERIES_KEYS = ["store_id", "product_id"]


def daily_from_frn(raw: pd.DataFrame) -> pd.DataFrame:
    """Return FreshRetailNet-50K rows as a daily table sorted by series and date."""
    daily = raw.rename(columns={"dt": "date", "sale_amount": "sales"})
    daily["date"] = pd.to_datetime(daily["date"])
    return daily.sort_values([*SERIES_KEYS, "date"], ignore_index=True)
