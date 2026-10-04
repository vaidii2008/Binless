from django.test import Client
from django.urls import reverse


def test_home_returns_200(client: Client) -> None:
    response = client.get(reverse("home"))
    assert response.status_code == 200


def test_healthz_returns_ok(client: Client) -> None:
    response = client.get(reverse("healthz"))
    assert response.status_code == 200
    assert response.content == b"ok"
