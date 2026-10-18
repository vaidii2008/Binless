"""Save order plans from the forecasting batch, and read them back for the dashboard."""

from datetime import date

from django.db import transaction

from .models import Forecast, Product, Store


@transaction.atomic
def save_plans(
    store_name: str, order_date: date, plans: list[dict], model_version: str
) -> int:
    """Store each product's plan for order_date and return how many were saved.

    A rerun for the same day replaces that day's plans, so a retried batch never
    leaves duplicates or half a day's orders.
    """
    store, _ = Store.objects.get_or_create(name=store_name)
    for plan in plans:
        product, _ = Product.objects.update_or_create(
            store=store,
            name=plan["product_name"],
            defaults={"category": plan["category"]},
        )
        Forecast.objects.update_or_create(
            product=product,
            date=order_date,
            defaults={
                "quantiles": plan["quantiles"],
                "orders": plan["orders"],
                "reasons": plan["reasons"],
                "model_version": model_version,
            },
        )
    return len(plans)


def latest_forecasts() -> list[Forecast]:
    """Return the forecasts for the most recent order date, in product order."""
    latest = Forecast.objects.order_by("-date").values_list("date", flat=True).first()
    if latest is None:
        return []
    return list(
        Forecast.objects.filter(date=latest)
        .select_related("product__store")
        .order_by("product_id")
    )
