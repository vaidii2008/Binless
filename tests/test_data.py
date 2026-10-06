import pandas as pd

from forecasting.data import daily_from_frn


def test_daily_from_frn_renames_columns_and_sorts_by_series_and_date() -> None:
    raw = pd.DataFrame(
        {
            "store_id": [1, 0, 0],
            "product_id": [7, 7, 7],
            "dt": ["2024-03-28", "2024-03-29", "2024-03-28"],
            "sale_amount": [0.3, 0.2, 0.1],
            "stock_hour6_22_cnt": [5, 3, 0],
        }
    )

    daily = daily_from_frn(raw)

    assert daily["sales"].tolist() == [0.1, 0.2, 0.3]
    assert daily["stockout_hours"].tolist() == [0, 3, 5]
    assert pd.api.types.is_datetime64_any_dtype(daily["date"])
