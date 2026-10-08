"""LightGBM quantile models trained on scaled sales."""

import lightgbm as lgb
import numpy as np
import pandas as pd

from forecasting.features import CATEGORICAL_FEATURES, FEATURES

# Starting values, not tuned: small learning steps, and every leaf needs 50 rows so a tree can't memorise individual days.
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
    dataset = _training_data(train)
    return {
        quantile: lgb.train({**PARAMS, "alpha": quantile}, dataset, NUM_ROUNDS)
        for quantile in quantiles
    }


def fit_explanation_model(train: pd.DataFrame) -> lgb.Booster:
    """Return a mean-regression model used only to explain forecasts.

    LightGBM's per-feature contributions don't add up for quantile objectives,
    which adjust leaf values after each tree is built (LightGBM issue #3998). This
    model learns from the same features and target with an objective whose
    contributions do add up.
    """
    return lgb.train(
        {**PARAMS, "objective": "regression"}, _training_data(train), NUM_ROUNDS
    )


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


def _training_data(train: pd.DataFrame) -> lgb.Dataset:
    """Return the rows that have a target as a LightGBM dataset."""
    rows = train[train["target"].notna()]
    return lgb.Dataset(
        rows[FEATURES], label=rows["target"], categorical_feature=CATEGORICAL_FEATURES
    )
