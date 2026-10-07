"""Estimate demand on days a product sold out, from its usual hourly sales pattern."""

import numpy as np
import pandas as pd

# The stock flags cover 06:00 to 21:59, the hours the products are on sale.
TRADING_HOURS = slice(6, 22)


# Below this share of usual sales, scaling up amplifies noise more than it recovers demand. It's a judgement call that mainly affects products that sold out in the first hours of trading, which the sell-out validation (10:00 onwards) doesn't cover.
MIN_AVAILABLE_SHARE = 0.2


def hourly_profile(daily: pd.DataFrame, by: str) -> pd.DataFrame:
    """Return each group's usual share of trading-hour sales, one column per hour.

    Only fully stocked days with some sales count, so stockouts can't bend the shape.
    """
    stocked = daily[(daily["stockout_hours"] == 0) & (daily["sales"] > 0)]
    hourly = pd.DataFrame(
        np.stack(stocked["hourly_sales"].to_numpy())[:, TRADING_HOURS],
        index=stocked[by],
        columns=range(6, 22),
    )
    totals = hourly.groupby(level=0).sum()
    return totals.div(totals.sum(axis=1), axis=0)


def correct_for_stockouts(
    daily: pd.DataFrame, profile: pd.DataFrame, by: str
) -> pd.Series:
    """Return estimated demand: sales scaled up for the hours a product was out of stock.

    Demand is sales divided by the usual share of sales that falls in the product's
    in-stock trading hours. Days with less than MIN_AVAILABLE_SHARE in stock,
    including full-day stockouts, get NaN because there's too little to scale.
    """
    shares = profile.reindex(daily[by]).to_numpy()
    in_stock = np.stack(daily["hourly_out_of_stock"].to_numpy())[:, TRADING_HOURS] == 0
    available = (shares * in_stock).sum(axis=1)
    demand = daily["sales"] / available
    return demand.where(available >= MIN_AVAILABLE_SHARE)


def simulate_sellouts(days: pd.DataFrame, cut_hours: np.ndarray) -> pd.DataFrame:
    """Return copies of the days as if each sold out at its cut hour and lost the rest."""
    lost = np.arange(24) >= cut_hours[:, np.newaxis]
    hourly = np.where(lost, 0.0, np.stack(days["hourly_sales"].to_numpy()))
    return days.assign(
        sales=hourly.sum(axis=1),
        stockout_hours=lost[:, TRADING_HOURS].sum(axis=1),
        hourly_sales=list(hourly),
        hourly_out_of_stock=list(lost.astype(int)),
    )
