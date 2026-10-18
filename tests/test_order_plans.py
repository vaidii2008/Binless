from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from django.core.management import call_command

from forecasting.planning import save_models, train_shop_models
from forecasting.simulation import PRODUCTS, simulate_shop
from orders.models import Forecast
from orders.plans import latest_forecasts, save_plans


def _plan(units: int) -> dict:
    return {
        "product_name": "Sourdough loaf",
        "category": "Bread",
        "quantiles": {"p50": 8.0, "p90": 10.0},
        "orders": [{"label": "Balanced", "units": units, "sell_out_chance": 50}],
        "reasons": [],
    }


@pytest.mark.django_db
def test_rerunning_a_day_replaces_its_plans() -> None:
    save_plans("Test shop (simulated)", date(2026, 10, 20), [_plan(8)], "v1")
    save_plans("Test shop (simulated)", date(2026, 10, 20), [_plan(9)], "v2")
    forecast = Forecast.objects.get()
    assert forecast.orders[0]["units"] == 9
    assert forecast.model_version == "v2"


@pytest.mark.django_db
def test_latest_forecasts_returns_only_the_newest_day() -> None:
    save_plans("Test shop (simulated)", date(2026, 10, 19), [_plan(7)], "v1")
    save_plans("Test shop (simulated)", date(2026, 10, 20), [_plan(8)], "v1")
    assert [f.date for f in latest_forecasts()] == [date(2026, 10, 20)]


@pytest.mark.django_db
def test_latest_forecasts_is_empty_before_the_first_batch() -> None:
    assert latest_forecasts() == []


@pytest.mark.django_db
def test_forecast_orders_command_saves_tomorrow_for_every_product(
    tmp_path: Path,
) -> None:
    history = simulate_shop(date(2026, 10, 19), n_days=60, seed=5)
    models_dir = tmp_path / "2026-10-19"
    save_models(train_shop_models(history, quantiles=[0.5, 0.9]), models_dir)

    call_command(
        "forecast_orders", "--models", str(models_dir), "--today", "2026-10-19"
    )

    forecasts = latest_forecasts()
    assert len(forecasts) == len(PRODUCTS)
    assert {f.date for f in forecasts} == {pd.Timestamp("2026-10-20").date()}
    assert {f.model_version for f in forecasts} == {"2026-10-19"}
    assert len(forecasts[0].orders) == 4
