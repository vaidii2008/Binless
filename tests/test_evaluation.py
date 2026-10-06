import pandas as pd
import pytest

from forecasting.evaluation import evaluate, last_weeks


def test_last_weeks_selects_the_final_seven_day_blocks() -> None:
    daily = pd.DataFrame({"date": pd.date_range("2024-04-01", periods=30)})
    window = last_weeks(daily, n_weeks=2)
    assert window.sum() == 14
    assert daily.loc[window, "date"].min() == pd.Timestamp("2024-04-17")


def test_evaluate_scores_all_days_and_fully_stocked_days_separately() -> None:
    daily = pd.DataFrame(
        {
            "date": pd.date_range("2024-04-01", periods=2),
            "sales": [10.0, 5.0],
            "stockout_hours": [0, 6],
        }
    )
    forecast = pd.Series([12.0, 8.0])
    scores = evaluate(daily, forecast, n_weeks=1)
    assert scores["wape_all"] == pytest.approx(5 / 15)
    assert scores["wape_stocked"] == pytest.approx(2 / 10)
    assert scores["bias_stocked"] == pytest.approx(0.2)
