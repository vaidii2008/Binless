# pages/views.py
from django.http import HttpRequest, HttpResponse


def home(request: HttpRequest) -> HttpResponse:
    """Return a placeholder landing page."""
    return HttpResponse("Binless is running")


def healthz(request: HttpRequest) -> HttpResponse:
    """Return 200 so the Lambda Web Adapter knows Django is ready"""
    return HttpResponse("ok", content_type="text/plain")