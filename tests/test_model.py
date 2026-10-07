import numpy as np
import pandas as pd
import pytest

from forecasting.features import FEATURES
from forecasting.model import fit_quantile_models, predict_quantiles


def make_feature_rows(n_rows: int) -> pd.DataFrame:
    """Return random rows with every model feature, a scale and a target."""
    rng = np.random.default_rng(seed=0)
    rows = pd.DataFrame({feature: rng.uniform(0, 1, n_rows) for feature in FEATURES})
    rows["day_of_week"] = rng.integers(0, 7, n_rows)
    rows["category_id"] = rng.integers(0, 5, n_rows)
    rows["discount"] = rng.choice([0.7, 1.0], n_rows)
    rows["scale"] = rng.uniform(1, 10, n_rows)
    rows["target"] = rng.uniform(0.5, 1.5, n_rows)
    return rows


def test_forecasts_are_in_sales_units_and_never_cross() -> None:
    rows = make_feature_rows(500)
    forecasts = predict_quantiles(fit_quantile_models(rows, [0.5, 0.9]), rows)
    assert list(forecasts.columns) == ["p50", "p90"]
    assert (forecasts["p90"] >= forecasts["p50"]).all()
    assert (forecasts["p50"] / rows["scale"]).between(0.5, 1.5).all()


def test_model_learns_a_discount_effect() -> None:
    rows = make_feature_rows(2000)
    rows["target"] = np.where(rows["discount"] < 1, 2.0, 1.0)
    forecasts = predict_quantiles(fit_quantile_models(rows, [0.5]), rows)
    on_discount = rows["discount"] < 1
    scaled_p50 = forecasts.loc[on_discount, "p50"] / rows.loc[on_discount, "scale"]
    assert scaled_p50.median() == pytest.approx(2.0, rel=0.1)
