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
        for app in ("config", "pages", "orders")
        for path in (ROOT / app).rglob("*.py")
        if "management" not in path.parts
    ]
    assert paths, "no web modules found"
    for path in paths:
        source = path.read_text()
        for module in BATCH_ONLY_IMPORTS:
            assert not _imports(source, module), f"{path} imports {module}"
