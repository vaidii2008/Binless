"""Score every forecasting method the same way, on the last weeks of history."""

import pandas as pd

from forecasting.metrics import bias, wape


def last_weeks(daily: pd.DataFrame, n_weeks: int) -> pd.Series:
    """Return a mask selecting the rows in the final n_weeks of the date range."""
    return daily["date"] >= _first_day(daily, n_weeks)


def evaluate(
    daily: pd.DataFrame, forecast: pd.Series, n_weeks: int
) -> dict[str, float]:
    """Return WAPE and bias over the last n_weeks, on all days and on fully stocked days.

    Neither view is exact: sales can understate demand on stockout days, and fully
    stocked days lean towards quieter days. Reporting both shows the range.
    """
    window = last_weeks(daily, n_weeks)
    stocked = window & (daily["stockout_hours"] == 0)
    sales = daily["sales"]
    return {
        "wape_all": wape(sales[window], forecast[window]),
        "bias_all": bias(sales[window], forecast[window]),
        "wape_stocked": wape(sales[stocked], forecast[stocked]),
        "bias_stocked": bias(sales[stocked], forecast[stocked]),
    }


def weekly_folds(
    daily: pd.DataFrame, n_weeks: int
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Return the start and end of each of the final n_weeks; ends are exclusive."""
    first_day = _first_day(daily, n_weeks)
    return [
        (first_day + pd.Timedelta(weeks=week), first_day + pd.Timedelta(weeks=week + 1))
        for week in range(n_weeks)
    ]


def _first_day(daily: pd.DataFrame, n_weeks: int) -> pd.Timestamp:
    """Return the first date of the final n_weeks."""
    return daily["date"].max() - pd.Timedelta(days=7 * n_weeks - 1)
