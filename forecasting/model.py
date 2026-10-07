"""LightGBM quantile models trained on scaled sales."""

import lightgbm as lgb
import numpy as np
import pandas as pd

from forecasting.features import CATEGORICAL_FEATURES, FEATURES

# Starting values, not tuned: small learning steps, and every leaf needs 50 rows
# so a tree can't memorise individual days.
PARAMS = {
    "objective": "quantile",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_data_in_leaf": 50,
    "verbosity": -1,
}
NUM_ROUNDS = 300


def fit_quantile_models(
    train: pd.DataFrame, quantiles: list[float]
) -> dict[float, lgb.Booster]:
    """Return one LightGBM model per quantile, trained on the rows with a target."""
    rows = train[train["target"].notna()]
    dataset = lgb.Dataset(
        rows[FEATURES], label=rows["target"], categorical_feature=CATEGORICAL_FEATURES
    )
    return {
        quantile: lgb.train({**PARAMS, "alpha": quantile}, dataset, NUM_ROUNDS)
        for quantile in quantiles
    }


def predict_quantiles(
    models: dict[float, lgb.Booster], rows: pd.DataFrame
) -> pd.DataFrame:
    """Return forecasts in sales units, one column per quantile, never crossing."""
    quantiles = sorted(models)
    scaled = np.column_stack([models[q].predict(rows[FEATURES]) for q in quantiles])
    scaled = np.sort(np.clip(scaled, 0, None), axis=1)
    forecasts = scaled * rows["scale"].to_numpy()[:, np.newaxis]
    columns = [f"p{round(q * 100)}" for q in quantiles]
    return pd.DataFrame(forecasts, index=rows.index, columns=columns)
