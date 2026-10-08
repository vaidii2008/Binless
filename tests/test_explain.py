import numpy as np
import pandas as pd

from forecasting.explain import REASONS, top_reasons
from forecasting.features import FEATURES
from forecasting.model import fit_explanation_model


def test_every_feature_has_a_reason() -> None:
    assert set(REASONS) == set(FEATURES)


def test_top_reasons_name_the_feature_that_moved_the_forecast() -> None:
    rng = np.random.default_rng(seed=0)
    rows = pd.DataFrame({feature: rng.uniform(0, 1, 2000) for feature in FEATURES})
    rows["day_of_week"] = rng.integers(0, 7, 2000)
    rows["category_id"] = rng.integers(0, 5, 2000)
    rows["discount"] = rng.choice([0.7, 1.0], 2000)
    rows["activity"] = 0
    rows["holiday"] = 0
    rows["scale"] = 10.0
    rows["target"] = np.where(rows["discount"] < 1, 2.0, 1.0)
    model = fit_explanation_model(rows)

    reasons = top_reasons(model, rows[rows["discount"] < 1].head(1), n_reasons=1)

    assert reasons == [[{"text": "On promotion at 30% off", "direction": "up"}]]
