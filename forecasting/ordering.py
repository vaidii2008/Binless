"""Turn forecasts into orders and measure what those orders would have done."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


def order_outcomes(orders: pd.Series, demand: pd.Series) -> dict[str, float]:
    """Return waste %, stockout rate and service level for orders against demand.

    Waste % is unsold units over ordered units, the stockout rate is the share of
    days demand exceeded the order, and the service level is the share of demand
    served. Rows missing an order or a demand figure are left out.
    """
    scored = orders.notna() & demand.notna()
    ordered, wanted = orders[scored], demand[scored]
    sold = np.minimum(ordered, wanted)
    return {
        "waste_pct": float((ordered - sold).sum() / ordered.sum()),
        "stockout_rate": float((wanted > ordered).mean()),
        "service_level": float(sold.sum() / wanted.sum()),
    }


@dataclass(frozen=True)
class Costs:
    """Per-unit price and costs in euro for a product category. Assumptions, not data."""

    price: float
    unit_cost: float
    salvage: float = 0.0

    @property
    def critical_ratio(self) -> float:
        """Return the share of demand worth covering: lost margin against waste."""
        margin = self.price - self.unit_cost
        waste_cost = self.unit_cost - self.salvage
        return margin / (margin + waste_cost)


def order_quantity(forecasts: pd.DataFrame, critical_ratio: float) -> pd.Series:
    """Return the forecast at the critical ratio, interpolating between quantile columns.

    Columns are named like "p80". A ratio outside the forecast quantiles uses the
    nearest one.
    """
    levels = [int(column[1:]) / 100 for column in forecasts.columns]
    quantity = np.apply_along_axis(
        lambda row: np.interp(critical_ratio, levels, row), 1, forecasts.to_numpy()
    )
    return pd.Series(quantity, index=forecasts.index)
