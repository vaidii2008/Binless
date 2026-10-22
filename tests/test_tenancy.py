from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from accounts.models import Membership, Organisation
from orders.models import Forecast, Product, Store
from orders.plans import latest_forecasts, save_plans


def _plan(product_name: str) -> dict:
    """Return a one-product plan shaped like plan_orders output."""
    return {
        "product_name": product_name,
        "category": "Bread",
        "quantiles": {"p50": 8.0, "p90": 10.0},
        "orders": [{"label": "Balanced", "units": 9, "sell_out_chance": 50}],
        "reasons": [],
    }


@pytest.fixture
def two_shops(db) -> tuple[Store, Store]:
    """Return a shop called Main Street in each of two organisations."""
    shops = []
    for organisation_name, product_name in [
        ("Test organisation A", "Sourdough loaf"),
        ("Test organisation B", "Bagels, 4 pack"),
    ]:
        organisation = Organisation.objects.create(name=organisation_name)
        store = Store.objects.create(organisation=organisation, name="Main Street")
        save_plans(store, date(2026, 10, 21), [_plan(product_name)], "test")
        shops.append(store)
    return shops[0], shops[1]


def test_each_organisation_sees_only_its_own_rows(two_shops) -> None:
    a, b = two_shops
    assert list(Store.objects.for_organisation(a.organisation)) == [a]
    assert [p.name for p in Product.objects.for_organisation(a.organisation)] == [
        "Sourdough loaf"
    ]
    assert [
        f.product.name for f in Forecast.objects.for_organisation(b.organisation)
    ] == ["Bagels, 4 pack"]


def test_products_and_forecasts_take_their_stores_organisation(two_shops) -> None:
    a, b = two_shops
    product = Product.objects.create(
        organisation=b.organisation, store=a, name="Brown soda bread", category="Bread"
    )
    assert product.organisation == a.organisation
    assert Forecast.objects.get(product__store=a).organisation == a.organisation


def test_users_see_only_their_organisations_rows(two_shops) -> None:
    a, b = two_shops
    user = get_user_model().objects.create_user("owner-a")
    Membership.objects.create(
        user=user, organisation=a.organisation, role=Membership.Role.OWNER
    )
    assert list(Store.objects.for_user(user)) == [a]
    assert [f.product.name for f in Forecast.objects.for_user(user)] == [
        "Sourdough loaf"
    ]

    Membership.objects.create(user=user, organisation=b.organisation)
    assert set(Store.objects.for_user(user)) == {a, b}


def test_a_user_with_no_membership_sees_nothing(two_shops) -> None:
    user = get_user_model().objects.create_user("visitor")
    for model in (Store, Product, Forecast):
        assert not model.objects.for_user(user).exists()


def test_latest_forecasts_ignore_newer_days_in_other_organisations(two_shops) -> None:
    a, b = two_shops
    save_plans(b, date(2026, 10, 22), [_plan("Bagels, 4 pack")], "test")
    forecasts = latest_forecasts(a)
    assert [(f.product.name, f.date) for f in forecasts] == [
        ("Sourdough loaf", date(2026, 10, 21))
    ]


def test_new_memberships_default_to_staff(two_shops) -> None:
    a, _ = two_shops
    user = get_user_model().objects.create_user("assistant")
    membership = Membership.objects.create(user=user, organisation=a.organisation)
    assert membership.role == Membership.Role.STAFF


def test_one_membership_per_user_and_organisation(two_shops) -> None:
    a, _ = two_shops
    user = get_user_model().objects.create_user("manager-a")
    Membership.objects.create(user=user, organisation=a.organisation)
    with pytest.raises(IntegrityError):
        Membership.objects.create(user=user, organisation=a.organisation)


def test_shop_names_are_unique_within_an_organisation_only(two_shops) -> None:
    a, b = two_shops
    assert a.name == b.name
    with pytest.raises(IntegrityError):
        Store.objects.create(organisation=a.organisation, name="Main Street")
