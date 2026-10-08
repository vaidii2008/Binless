from datetime import date

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .snapshot import load_snapshot

# The slider starts at "Balanced", the plain newsvendor rule.
DEFAULT_BALANCE = 1


def home(request: HttpRequest) -> HttpResponse:
    """Return a placeholder landing page."""
    return HttpResponse("Binless is running.")


def healthz(request: HttpRequest) -> HttpResponse:
    """Return 200 so the Lambda Web Adapter knows Django is ready."""
    return HttpResponse("ok", content_type="text/plain")


def orders(request: HttpRequest) -> HttpResponse:
    """Render tomorrow's order list for the simulated shop."""
    return render(request, "pages/orders.html", _order_context(request))


def order_table(request: HttpRequest) -> HttpResponse:
    """Render only the order table, for the slider to swap in."""
    return render(request, "pages/_order_table.html", _order_context(request))


def _order_context(request: HttpRequest) -> dict:
    """Return the snapshot with every product's order at the chosen slider position."""
    snapshot = load_snapshot()
    last_position = len(snapshot["balance_labels"]) - 1
    try:
        position = int(request.GET.get("balance", DEFAULT_BALANCE))
    except ValueError:
        position = DEFAULT_BALANCE
    position = min(max(position, 0), last_position)
    return {
        "store_name": snapshot["store_name"],
        "order_date": date.fromisoformat(snapshot["date"]),
        "label": snapshot["balance_labels"][position],
        "position": position,
        "last_position": last_position,
        "rows": [
            {**product, "order": product["orders"][position]}
            for product in snapshot["products"]
        ],
    }
