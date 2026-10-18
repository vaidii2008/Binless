"""Forecast tomorrow for the simulated shop and save its order plan."""

import logging
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand

from forecasting.planning import load_models, plan_orders
from forecasting.simulation import (
    CATEGORIES,
    SHELF_BALANCE,
    SHOP_TIMEZONE,
    STORE_NAME,
    simulate_shop,
)
from orders.plans import save_plans

HISTORY_DAYS = 180

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--models",
            type=Path,
            required=True,
            help="Folder written by scripts/train_shop_models.py",
        )
        parser.add_argument("--today", type=date.fromisoformat)
        parser.add_argument("--seed", type=int, default=42)

    def handle(self, *args, models: Path, today: date | None, seed: int, **options):
        today = today or datetime.now(SHOP_TIMEZONE).date()
        tomorrow = today + timedelta(days=1)
        # One extra day supplies tomorrow's promotions, holiday flag and weather forecast.
        daily = simulate_shop(tomorrow, HISTORY_DAYS + 1, seed)
        critical_ratios = {
            name: category.costs.critical_ratio for name, category in CATEGORIES.items()
        }
        plans = plan_orders(
            daily,
            pd.Timestamp(tomorrow),
            load_models(models),
            critical_ratios,
            SHELF_BALANCE,
        )
        saved = save_plans(STORE_NAME, tomorrow, plans, model_version=models.name)
        logger.info("Wrote %d forecasts for %s", saved, tomorrow)
