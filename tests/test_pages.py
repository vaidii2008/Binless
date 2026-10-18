from datetime import date

import pytest
from django.test import Client
from django.urls import reverse

from orders.plans import save_plans

LABELS = ["Fewer leftovers", "Balanced", "Fuller shelves", "Rarely run out"]


def _plan(name: str, category: str, units: list[int]) -> dict:
    """Return a plan shaped like plan_orders output, with one order per label."""
    return {
        "product_name": name,
        "category": category,
        "quantiles": {"p10": 5.0, "p50": 8.4, "p90": 11.6},
        "orders": [
            {"label": label, "units": count, "sell_out_chance": 50}
            for label, count in zip(LABELS, units, strict=True)
        ],
        "reasons": [{"text": "It's a Friday", "direction": "up"}],
    }


@pytest.fixture
def saved_plans(db) -> None:
    save_plans(
        "Test shop (simulated)",
        date(2026, 10, 20),
        [
            _plan("White sliced pan", "Bread", [20, 22, 24, 26]),
            _plan("Bananas, bunch", "Fruit", [10, 11, 12, 14]),
        ],
        model_version="test",
    )


def test_home_links_to_tomorrows_order(client: Client) -> None:
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert reverse("orders").encode() in response.content


def test_healthz_returns_ok(client: Client) -> None:
    response = client.get(reverse("healthz"))
    assert response.status_code == 200
    assert response.content == b"ok"


@pytest.mark.django_db
def test_orders_page_explains_when_no_forecast_exists(client: Client) -> None:
    response = client.get(reverse("orders"))
    assert response.status_code == 200
    assert b"No forecast has been saved yet" in response.content


def test_orders_page_shows_the_saved_forecast(
    client: Client, saved_plans: None
) -> None:
    response = client.get(reverse("orders"))
    assert response.status_code == 200
    assert b"Tuesday 20 October" in response.content
    assert b"simulated" in response.content
    assert b"White sliced pan" in response.content


def test_orders_grow_as_empty_shelves_matter_more(
    client: Client, saved_plans: None
) -> None:
    fewer = client.get(reverse("order_table"), {"balance": 0}).context["rows"]
    fuller = client.get(reverse("order_table"), {"balance": 3}).context["rows"]
    assert sum(r["order"]["units"] for r in fuller) > sum(
        r["order"]["units"] for r in fewer
    )


def test_order_table_ignores_a_nonsense_position(
    client: Client, saved_plans: None
) -> None:
    assert client.get(reverse("order_table"), {"balance": "lots"}).status_code == 200


def test_results_page_shows_the_benchmark_and_credits_the_dataset(
    client: Client,
) -> None:
    response = client.get(reverse("results"))
    assert response.status_code == 200
    assert b"FreshRetailNet-50K" in response.content
    assert b"31.57" in response.content
