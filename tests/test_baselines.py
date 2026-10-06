import pandas as pd

from forecasting.baselines import same_day_last_week


def make_daily(sales_by_store: dict[int, list[float]]) -> pd.DataFrame:
    """Return one product per store with daily sales from 1 April 2024."""
    frames = [
        pd.DataFrame(
            {
                "store_id": store_id,
                "product_id": 1,
                "date": pd.date_range("2024-04-01", periods=len(sales)),
                "sales": sales,
            }
        )
        for store_id, sales in sales_by_store.items()
    ]
    return pd.concat(frames, ignore_index=True)


def test_same_day_last_week_uses_the_value_seven_days_earlier() -> None:
    daily = make_daily({0: [float(day) for day in range(10)]})
    forecast = same_day_last_week(daily)
    assert forecast.iloc[:7].isna().all()
    assert forecast.iloc[7:].tolist() == [0.0, 1.0, 2.0]


def test_same_day_last_week_never_mixes_series() -> None:
    daily = make_daily({0: [1.0] * 8, 1: [5.0] * 8})
    store_1 = same_day_last_week(daily)[daily["store_id"] == 1]
    assert store_1.iloc[:7].isna().all()
    assert store_1.iloc[7] == 5.0
