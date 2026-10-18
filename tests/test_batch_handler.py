from pathlib import Path

import pytest

from batch import handler


class FakeS3:
    """Stand in for boto3's S3 client with a fixed set of keys."""

    def __init__(self, keys: list[str]) -> None:
        self.keys = keys
        self.downloads: list[str] = []

    def list_objects_v2(self, Bucket: str, Prefix: str) -> dict:
        matching = [key for key in self.keys if key.startswith(Prefix)]
        return {"Contents": [{"Key": key} for key in matching]} if matching else {}

    def download_file(self, bucket: str, key: str, filename: str) -> None:
        self.downloads.append(key)
        Path(filename).write_text("model")


@pytest.fixture(autouse=True)
def models_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(handler, "MODELS_ROOT", tmp_path)


def test_downloads_only_the_requested_version() -> None:
    s3 = FakeS3(["shop/v2/p50.txt", "shop/v2/explanation.txt", "shop/v1/p50.txt"])
    directory = handler.download_models("bucket", "v2", s3)
    assert sorted(p.name for p in directory.iterdir()) == ["explanation.txt", "p50.txt"]
    assert "shop/v1/p50.txt" not in s3.downloads


def test_reuses_files_already_downloaded() -> None:
    handler.download_models("bucket", "v2", FakeS3(["shop/v2/p50.txt"]))
    second = FakeS3(["shop/v2/p50.txt"])
    handler.download_models("bucket", "v2", second)
    assert second.downloads == []


def test_fails_clearly_when_the_version_is_missing() -> None:
    with pytest.raises(FileNotFoundError, match="shop/v9"):
        handler.download_models("bucket", "v9", FakeS3(["shop/v2/p50.txt"]))
