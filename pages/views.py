from datetime import timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from orders.models import Store
from orders.plans import latest_forecasts, sample_store

from . import results

# The slider starts at "Balanced", the plain newsvendor rule.
DEFAULT_BALANCE = 1
# The shop is in Ireland, so its "today" and "tomorrow" follow Irish time.
SHOP_TIME_ZONE = "Europe/Dublin"


def home(request: HttpRequest) -> HttpResponse:
    """Render the landing page with a few lines from tomorrow's order."""
    context = _order_context(request, sample_store())
    rows = context.get("rows", [])
    return render(
        request,
        "pages/home.html",
        {**context, "preview": rows[:3], "product_count": len(rows)},
    )


def results_page(request: HttpRequest) -> HttpResponse:
    """Render the benchmark results with charts."""
    return render(
        request,
        "pages/results.html",
        {
            "order_policies": results.ORDER_POLICIES,
            "forecast_error": results.FORECAST_ERROR,
            "held_out": results.HELD_OUT,
        },
    )


def healthz(request: HttpRequest) -> HttpResponse:
    """Return 200 so the Lambda Web Adapter knows Django is ready."""
    return HttpResponse("ok", content_type="text/plain")


def orders(request: HttpRequest) -> HttpResponse:
    """Render tomorrow's order list for the public sample shop."""
    context = _order_context(request, sample_store())
    return render(
        request, "pages/orders.html", {**context, "table_url": reverse("order_table")}
    )


def order_table(request: HttpRequest) -> HttpResponse:
    """Render only the sample shop's order table, for the slider to swap in."""
    context = _order_context(request, sample_store())
    return render(request, "pages/_order_table.html", {**context, "partial": True})


@login_required
def shops(request: HttpRequest) -> HttpResponse:
    """List the shops in every organisation the member belongs to."""
    stores = (
        Store.objects.for_user(request.user)
        .select_related("organisation")
        .order_by("organisation__name", "name")
    )
    return render(request, "pages/shops.html", {"stores": stores})


@login_required
def shop_orders(request: HttpRequest, store_id: int) -> HttpResponse:
    """Render tomorrow's order for one of the member's shops."""
    store = _members_store(request, store_id)
    context = _order_context(request, store)
    table_url = reverse("shop_order_table", args=[store.pk])
    return render(request, "pages/orders.html", {**context, "table_url": table_url})


@login_required
def shop_order_table(request: HttpRequest, store_id: int) -> HttpResponse:
    """Render only the order table for one of the member's shops."""
    context = _order_context(request, _members_store(request, store_id))
    return render(request, "pages/_order_table.html", {**context, "partial": True})


def _members_store(request: HttpRequest, store_id: int) -> Store:
    """Return the shop if the member's organisations own it, or raise a 404.

    A 404 rather than a 403, so another organisation's shop looks like no shop at all.
    """
    return get_object_or_404(Store.objects.for_user(request.user), pk=store_id)


def _order_context(request: HttpRequest, store: Store | None) -> dict:
    """Return the shop's latest forecasts, ordered at the slider position."""
    forecasts = latest_forecasts(store) if store else []
    if not forecasts:
        return {"rows": []}
    labels = [order["label"] for order in forecasts[0].orders]
    last_position = len(labels) - 1
    try:
        position = int(request.GET.get("balance", DEFAULT_BALANCE))
    except ValueError:
        position = DEFAULT_BALANCE
    position = min(max(position, 0), last_position)
    order_date = forecasts[0].date
    # Looked up here, not at import, so missing time zone data can't take down /healthz.
    today = timezone.localdate(timezone=ZoneInfo(SHOP_TIME_ZONE))
    return {
        "store_name": store.name,
        "order_date": order_date,
        "is_tomorrow": order_date == today + timedelta(days=1),
        # The batch saves tomorrow's order each night, so a past date means it stopped.
        "out_of_date": order_date < today,
        "labels": labels,
        "label": labels[position],
        "position": position,
        "last_position": last_position,
        "rows": [
            {
                "name": forecast.product.name,
                "category": forecast.product.category,
                "typical_day": round(forecast.quantiles["p50"]),
                "busy_day": round(forecast.quantiles["p90"]),
                "order": forecast.orders[position],
                "reasons": forecast.reasons,
            }
            for forecast in forecasts
        ],
    }
