"""Turn forecasts into orders and measure what those orders would have done."""

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
