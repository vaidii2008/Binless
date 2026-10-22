from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from accounts.models import Membership, Organisation
from orders.models import Store
from orders.plans import latest_forecasts, save_plans

PASSWORD = "fresh-bread-2026"


def _plan(product_name: str) -> dict:
    """Return a one-product plan shaped like plan_orders output."""
    labels = ["Fewer leftovers", "Balanced", "Fuller shelves", "Rarely run out"]
    return {
        "product_name": product_name,
        "category": "Bread",
        "quantiles": {"p50": 8.0, "p90": 10.0},
        "orders": [
            {"label": label, "units": 7 + i, "sell_out_chance": 50}
            for i, label in enumerate(labels)
        ],
        "reasons": [{"text": "It's a Friday", "direction": "up"}],
    }


@pytest.fixture
def sample_shop(db) -> Store:
    """Return the public sample shop with one saved order."""
    organisation = Organisation.objects.create(
        name="Sample organisation (simulated)", is_sample=True
    )
    store = Store.objects.create(
        organisation=organisation,
        name="Rowan Street Grocer (simulated)",
        is_simulated=True,
    )
    save_plans(
        store,
        date(2026, 10, 23),
        [_plan("White sliced pan"), _plan("Bananas, bunch")],
        model_version="test",
    )
    return store


def _sign_up(client: Client, email: str, follow: bool = False):
    """Sign up through the real form and return the response."""
    return client.post(
        reverse("account_signup"),
        {"email": email, "password1": PASSWORD, "password2": PASSWORD},
        follow=follow,
    )


def _shop_of(email: str) -> Store:
    return Store.objects.for_user(get_user_model().objects.get(email=email)).get()


def test_signing_up_makes_an_owner_with_a_simulated_shop(
    client: Client, sample_shop: Store
) -> None:
    _sign_up(client, "owner@example.com")
    user = get_user_model().objects.get(email="owner@example.com")
    assert Membership.objects.get(user=user).role == Membership.Role.OWNER
    shop = _shop_of("owner@example.com")
    assert shop.is_simulated
    assert shop.organisation != sample_shop.organisation
    forecasts = latest_forecasts(shop)
    assert [f.product.name for f in forecasts] == ["White sliced pan", "Bananas, bunch"]
    assert {f.date for f in forecasts} == {date(2026, 10, 23)}


def test_signing_up_lands_on_your_shops(client: Client, sample_shop: Store) -> None:
    response = _sign_up(client, "owner@example.com", follow=True)
    assert response.redirect_chain[-1][0] == reverse("shops")
    assert b"Sample shop (simulated)" in response.content
    assert b"Successfully signed in as owner@example.com" in response.content


def test_signing_up_before_the_first_batch_gives_an_empty_shop(
    client: Client, db
) -> None:
    _sign_up(client, "early@example.com")
    shop = _shop_of("early@example.com")
    assert latest_forecasts(shop) == []
    page = client.get(reverse("shop_orders", args=[shop.pk]))
    assert b"No forecast has been saved yet" in page.content


def test_your_shops_needs_signing_in(client: Client, db) -> None:
    response = client.get(reverse("shops"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("account_login"))


def test_members_reach_only_their_own_shops(client: Client, sample_shop: Store) -> None:
    _sign_up(client, "a@example.com")
    _sign_up(Client(), "b@example.com")
    own, other = _shop_of("a@example.com"), _shop_of("b@example.com")

    assert client.get(reverse("shop_orders", args=[own.pk])).status_code == 200
    assert list(client.get(reverse("shops")).context["stores"]) == [own]
    for name in ("shop_orders", "shop_order_table"):
        for store in (other, sample_shop):
            assert client.get(reverse(name, args=[store.pk])).status_code == 404


def test_a_shop_page_moves_its_own_slider(client: Client, sample_shop: Store) -> None:
    _sign_up(client, "owner@example.com")
    shop = _shop_of("owner@example.com")
    table_url = reverse("shop_order_table", args=[shop.pk])
    page = client.get(reverse("shop_orders", args=[shop.pk]))
    assert f'hx-get="{table_url}"'.encode() in page.content
    table = client.get(table_url, {"balance": 3})
    assert b'hx-swap-oob="innerHTML:#balance-label">Rarely run out' in table.content


def test_signing_in_with_an_email_address(client: Client, sample_shop: Store) -> None:
    _sign_up(client, "owner@example.com")
    client.logout()
    response = client.post(
        reverse("account_login"),
        {"login": "owner@example.com", "password": PASSWORD},
    )
    assert response.status_code == 302
    assert response.url == reverse("shops")


def test_deleting_an_account_removes_its_organisation_and_shops(
    client: Client, sample_shop: Store
) -> None:
    _sign_up(client, "owner@example.com")
    _sign_up(Client(), "neighbour@example.com")

    response = client.post(reverse("delete_account"), follow=True)

    assert b"have been deleted" in response.content
    assert not get_user_model().objects.filter(email="owner@example.com").exists()
    assert not Organisation.objects.filter(name="owner@example.com").exists()
    assert not Store.objects.filter(organisation__name="owner@example.com").exists()
    assert _shop_of("neighbour@example.com")
    assert Store.objects.filter(pk=sample_shop.pk).exists()


def test_deleting_an_account_asks_first(client: Client, sample_shop: Store) -> None:
    _sign_up(client, "owner@example.com")
    response = client.get(reverse("delete_account"))
    assert response.status_code == 200
    assert get_user_model().objects.filter(email="owner@example.com").exists()
