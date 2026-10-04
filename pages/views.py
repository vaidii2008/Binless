# pages/views.py
from django.http import HttpRequest, HttpResponse


def home(request: HttpRequest) -> HttpResponse:
    """Return a placeholder landing page."""
    return HttpResponse("Binless is running.")