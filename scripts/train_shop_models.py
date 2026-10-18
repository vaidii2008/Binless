"""Train the simulated shop's models and write them to models/shop/<version>.

Upload the folder to the model bucket afterwards, so the batch Lambda can load it.
"""

import argparse
import logging
from datetime import date, datetime
from pathlib import Path

from forecasting.planning import save_models, train_shop_models
from forecasting.simulation import SHOP_TIMEZONE, STORE_NAME, simulate_shop

HISTORY_DAYS = 180

logger = logging.getLogger(__name__)


def main() -> None:
    today = datetime.now(SHOP_TIMEZONE).date()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--today", type=date.fromisoformat, default=today)
    parser.add_argument("--version", default=today.isoformat())
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    history = simulate_shop(args.today, HISTORY_DAYS, args.seed)
    directory = Path("models/shop") / args.version
    save_models(train_shop_models(history), directory)
    logger.info(
        "Trained on %d days of %s up to %s and wrote %s",
        HISTORY_DAYS,
        STORE_NAME,
        args.today,
        directory,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    logger.setLevel(logging.INFO)
    main()
