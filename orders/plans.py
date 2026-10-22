"""Save order plans from the forecasting batch, and read them back for the dashboard."""

from datetime import date

from django.db import transaction

from accounts.models import Organisation

from .models import Forecast, Product, Store


@transaction.atomic
def save_plans(
    store: Store, order_date: date, plans: list[dict], model_version: str
) -> int:
    """Store each product's plan for order_date and return how many were saved.

    A rerun for the same day replaces that day's plans, so a retried batch never
    leaves duplicates or half a day's orders.
    """
    products = Product.objects.for_organisation(store.organisation)
    forecasts = Forecast.objects.for_organisation(store.organisation)
    for plan in plans:
        product, _ = products.update_or_create(
            store=store,
            name=plan["product_name"],
            defaults={"category": plan["category"]},
        )
        forecasts.update_or_create(
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


def latest_forecasts(store: Store) -> list[Forecast]:
    """Return the store's forecasts for its most recent order date, in product order."""
    forecasts = Forecast.objects.for_organisation(store.organisation).filter(
        product__store=store
    )
    latest = forecasts.order_by("-date").values_list("date", flat=True).first()
    if latest is None:
        return []
    return list(
        forecasts.filter(date=latest)
        .select_related("product__store")
        .order_by("product_id")
    )


def sample_store() -> Store | None:
    """Return the simulated shop that anyone can see without signing in."""
    organisation = Organisation.objects.filter(is_sample=True).first()
    if organisation is None:
        return None
    return Store.objects.for_organisation(organisation).order_by("id").first()


SIMULATED_SHOP_NAME = "Sample shop (simulated)"


def open_simulated_shop(organisation: Organisation) -> Store:
    """Create a simulated shop for organisation, starting from the sample shop's order.

    From the next night on, the batch refreshes it with every other simulated shop.
    """
    store = Store.objects.create(
        organisation=organisation, name=SIMULATED_SHOP_NAME, is_simulated=True
    )
    sample = sample_store()
    forecasts = latest_forecasts(sample) if sample else []
    if forecasts:
        plans = [
            {
                "product_name": forecast.product.name,
                "category": forecast.product.category,
                "quantiles": forecast.quantiles,
                "orders": forecast.orders,
                "reasons": forecast.reasons,
            }
            for forecast in forecasts
        ]
        save_plans(store, forecasts[0].date, plans, forecasts[0].model_version)
    return store
