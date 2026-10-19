from datetime import timedelta

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from orders.plans import latest_forecasts

from . import results

# The slider starts at "Balanced", the plain newsvendor rule.
DEFAULT_BALANCE = 1


def home(request: HttpRequest) -> HttpResponse:
    """Render the landing page with a few lines from tomorrow's order."""
    context = _order_context(request)
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
    """Render tomorrow's order list for the simulated shop."""
    return render(request, "pages/orders.html", _order_context(request))


def order_table(request: HttpRequest) -> HttpResponse:
    """Render only the order table, for the slider to swap in."""
    return render(
        request, "pages/_order_table.html", {**_order_context(request), "partial": True}
    )


def _order_context(request: HttpRequest) -> dict:
    """Return the latest forecasts with every product's order at the chosen slider position."""
    forecasts = latest_forecasts()
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
    today = timezone.localdate()
    return {
        "store_name": forecasts[0].product.store.name,
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
