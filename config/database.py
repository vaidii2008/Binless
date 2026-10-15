
"""Build Django's database settings from a postgres:// connection URL."""

from urllib.parse import parse_qsl, unquote, urlsplit


def database_from_url(url: str) -> dict:
    """Return a Django DATABASES entry for a postgres:// URL."""
    parts = urlsplit(url)
    if parts.scheme not in ("postgres", "postgresql"):
        # The URL holds the password, so only the scheme goes in the error.
        raise ValueError(f"Unsupported database scheme: {parts.scheme!r}")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parts.path.removeprefix("/"),
        "USER": unquote(parts.username or ""),
        "PASSWORD": unquote(parts.password or ""),
        "HOST": parts.hostname or "",
        "PORT": str(parts.port or ""),
        "OPTIONS": dict(parse_qsl(parts.query)),
    }