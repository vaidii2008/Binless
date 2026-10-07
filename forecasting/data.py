"""Convert source datasets into the daily table the forecasting code works on."""

import pandas as pd

SERIES_KEYS = ["store_id", "product_id"]


# stockout_hours counts the trading hours (06:00 to 22:00) a product was out of stock.
FRN_COLUMNS = {
    "dt": "date",
    "sale_amount": "sales",
    "stock_hour6_22_cnt": "stockout_hours",
    "first_category_id": "category_id",
    "activity_flag": "activity",
    "holiday_flag": "holiday",
    "precpt": "precipitation",
    "avg_temperature": "temperature",
    "avg_humidity": "humidity",
    "avg_wind_level": "wind_level",
    "hours_sale": "hourly_sales",
    "hours_stock_status": "hourly_out_of_stock",
}


def daily_from_frn(raw: pd.DataFrame) -> pd.DataFrame:
    """Return FreshRetailNet-50K rows as a daily table sorted by series and date."""
    daily = raw.rename(columns=FRN_COLUMNS)
    daily["date"] = pd.to_datetime(daily["date"])
    return daily.sort_values([*SERIES_KEYS, "date"], ignore_index=True)
