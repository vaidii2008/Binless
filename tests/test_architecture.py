from pathlib import Path

FORECASTING_DIR = Path(__file__).resolve().parent.parent / "forecasting"


def test_forecasting_package_never_imports_django() -> None:
    paths = list(FORECASTING_DIR.rglob("*.py"))
    assert paths, "no modules found in the forecasting package"
    for path in paths:
        source = path.read_text()
        assert "import django" not in source and "from django" not in source, path
