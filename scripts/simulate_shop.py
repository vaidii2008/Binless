"""Write the simulated shop's history and tomorrow's plan to data/shop/simulated.parquet."""

import argparse
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from forecasting.simulation import SHOP_TIMEZONE, STORE_NAME, simulate_shop

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--today", type=date.fromisoformat, default=datetime.now(SHOP_TIMEZONE).date()
    )
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # One extra day supplies tomorrow's promotions, holiday flag and weather forecast.
    tomorrow = args.today + timedelta(days=1)
    simulated = simulate_shop(tomorrow, args.days + 1, args.seed)
    path = Path("data/shop/simulated.parquet")
    path.parent.mkdir(parents=True, exist_ok=True)
    simulated.to_parquet(path, index=False)

    history = simulated[simulated["date"] < pd.Timestamp(tomorrow)]
    sold_out = (history["stockout_hours"] > 0).mean()
    lost = 1 - history["sales"].sum() / history["true_demand"].sum()
    logger.info(
        "Wrote %d days of %s up to %s, plus tomorrow", args.days, STORE_NAME, args.today
    )
    logger.info(
        "Days with a sell-out: %.1f%%, demand lost: %.1f%%", 100 * sold_out, 100 * lost
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    logger.setLevel(logging.INFO)
    main()
