"""Read the forecast snapshot written by scripts/build_forecast_snapshot.py."""

import json
from functools import cache
from pathlib import Path

SNAPSHOT_PATH = Path(__file__).resolve().parent / "forecast_snapshot.json"


@cache
def load_snapshot() -> dict:
    """Return the snapshot, reading the file once per process."""
    return json.loads(SNAPSHOT_PATH.read_text())
