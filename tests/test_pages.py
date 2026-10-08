from django.test import Client
from django.urls import reverse


def test_home_returns_200(client: Client) -> None:
    response = client.get(reverse("home"))
    assert response.status_code == 200


def test_healthz_returns_ok(client: Client) -> None:
    response = client.get(reverse("healthz"))
    assert response.status_code == 200
    assert response.content == b"ok"


def test_orders_page_shows_simulated_orders(client: Client) -> None:
    response = client.get(reverse("orders"))
    assert response.status_code == 200
    assert b"simulated" in response.content
    assert b"White sliced pan" in response.content


def test_orders_grow_as_empty_shelves_matter_more(client: Client) -> None:
    fewer = client.get(reverse("order_table"), {"balance": 0}).context["rows"]
    fuller = client.get(reverse("order_table"), {"balance": 3}).context["rows"]
    assert sum(r["order"]["units"] for r in fuller) > sum(
        r["order"]["units"] for r in fewer
    )


def test_order_table_ignores_a_nonsense_position(client: Client) -> None:
    assert client.get(reverse("order_table"), {"balance": "lots"}).status_code == 200
