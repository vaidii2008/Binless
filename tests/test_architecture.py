import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORECASTING_DIR = ROOT / "forecasting"
# The web image has no pandas, NumPy or LightGBM, so only the batch's code may import them.
BATCH_ONLY_IMPORTS = ("forecasting", "pandas", "numpy", "lightgbm")


def _imports(source: str, module: str) -> bool:
    """Return whether source imports module or one of its submodules."""
    return any(
        line.startswith((f"import {module}", f"from {module}"))
        for line in source.splitlines()
    )


def test_forecasting_package_never_imports_django() -> None:
    paths = list(FORECASTING_DIR.rglob("*.py"))
    assert paths, "no modules found in the forecasting package"
    for path in paths:
        assert not _imports(path.read_text(), "django"), path


def test_web_code_never_imports_the_forecasting_stack() -> None:
    paths = [
        path
        for app in ("config", "accounts", "pages", "orders")
        for path in (ROOT / app).rglob("*.py")
        if "management" not in path.parts
    ]
    assert paths, "no web modules found"
    for path in paths:
        source = path.read_text()
        for module in BATCH_ONLY_IMPORTS:
            assert not _imports(source, module), f"{path} imports {module}"


def test_web_image_can_load_irish_time_without_a_system_time_zone_database() -> None:
    web_requirements = (ROOT / "requirements" / "web.txt").read_text().splitlines()
    assert any(line.startswith("tzdata==") for line in web_requirements)
    # An empty PYTHONTZPATH hides any system database, so Irish time must come from tzdata.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from zoneinfo import ZoneInfo; ZoneInfo('Europe/Dublin')",
        ],
        env={**os.environ, "PYTHONTZPATH": ""},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
