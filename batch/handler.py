"""Lambda entry point: load the shop's models from S3 and save tomorrow's order."""

import logging
import os
from pathlib import Path

import boto3
import django

# /tmp is the only writable folder on Lambda. A warm environment reuses its files.
MODELS_ROOT = Path("/tmp/models")

logger = logging.getLogger(__name__)


def download_models(bucket: str, version: str, s3_client=None) -> Path:
    """Copy shop/<version>/ from the bucket to /tmp once, and return the folder."""
    directory = MODELS_ROOT / version
    if any(directory.glob("*.txt")):
        return directory
    s3 = s3_client or boto3.client("s3")
    directory.mkdir(parents=True, exist_ok=True)
    listing = s3.list_objects_v2(Bucket=bucket, Prefix=f"shop/{version}/")
    for item in listing.get("Contents", []):
        key = item["Key"]
        s3.download_file(bucket, key, str(directory / Path(key).name))
    if not any(directory.glob("*.txt")):
        raise FileNotFoundError(f"No model files at s3://{bucket}/shop/{version}/")
    return directory


def handler(event: dict, context: object) -> dict:
    """Write tomorrow's forecasts for the simulated shop to Postgres."""
    version = os.environ["MODEL_VERSION"]
    directory = download_models(os.environ["MODEL_BUCKET"], version)
    django.setup()
    # Imported after setup, because Django's apps must be loaded first.
    from django.core.management import call_command

    call_command("forecast_orders", "--models", str(directory))
    logger.info("Batch finished with model version %s", version)
    return {"model_version": version}
