import numpy as np
import pandas as pd
import pytest

from forecasting.features import add_features

LOOKBACK_COLUMNS = ["scale", "lag_1", "lag_7", "lag_14", "mean_7", "cv_28"]


def make_daily(n_days: int) -> pd.DataFrame:
    """Return one series with random daily sales from 1 April 2024."""
    rng = np.random.default_rng(seed=0)
    return pd.DataFrame(
        {
            "store_id": 0,
            "product_id": 1,
            "date": pd.date_range("2024-04-01", periods=n_days),
            "sales": rng.uniform(1.0, 5.0, size=n_days),
        }
    )


def test_features_never_use_the_same_day_or_later_sales() -> None:
    daily = make_daily(40)
    changed = daily.copy()
    changed.loc[30, "sales"] = 1000.0

    before = add_features(daily)[LOOKBACK_COLUMNS]
    after = add_features(changed)[LOOKBACK_COLUMNS]

    pd.testing.assert_frame_equal(before.iloc[:31], after.iloc[:31])


def test_scale_is_the_mean_of_the_previous_28_days() -> None:
    daily = make_daily(30)
    daily["sales"] = np.arange(30, dtype=float)
    features = add_features(daily)
    assert features["scale"].iloc[:28].isna().all()
    assert features.loc[28, "scale"] == pytest.approx(13.5)
    assert features.loc[28, "lag_1"] == pytest.approx(27 / 13.5)


def test_scale_is_missing_after_28_days_without_sales() -> None:
    daily = make_daily(30)
    daily["sales"] = 0.0
    assert add_features(daily)["scale"].isna().all()


def test_target_can_come_from_corrected_demand() -> None:
    daily = make_daily(30).assign(demand=10.0)
    features = add_features(daily, target_column="demand")
    assert features.loc[29, "target"] == pytest.approx(10.0 / features.loc[29, "scale"])
