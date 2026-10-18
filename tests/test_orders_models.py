from datetime import date

import pytest
from django.db import IntegrityError

from orders.models import Forecast, Product, Store


@pytest.fixture
def product(db) -> Product:
    store = Store.objects.create(name="Test shop (simulated)")
    return Product.objects.create(store=store, name="Sourdough loaf", category="Bread")


def _save_forecast(product: Product, day: date) -> Forecast:
    """Save a forecast with placeholder values for one product and day."""
    return Forecast.objects.create(
        product=product,
        date=day,
        quantiles={"p50": 8.0},
        orders=[],
        reasons=[],
        model_version="test",
    )


@pytest.mark.django_db
def test_rejects_a_second_forecast_for_the_same_day(product: Product) -> None:
    _save_forecast(product, date(2026, 10, 19))
    with pytest.raises(IntegrityError):
        _save_forecast(product, date(2026, 10, 19))


@pytest.mark.django_db
def test_allows_forecasts_for_different_days(product: Product) -> None:
    _save_forecast(product, date(2026, 10, 19))
    _save_forecast(product, date(2026, 10, 20))
    assert product.forecasts.count() == 2
