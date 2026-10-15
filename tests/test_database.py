import pytest

from config.database import database_from_url


def test_splits_pooled_neon_style_url():
    db = database_from_url(
        "postgresql://binless:p%40ss@ep-x-pooler.eu-west-2.aws.neon.tech/binless"
        "?sslmode=require&channel_binding=require"
    )
    assert db["HOST"] == "ep-x-pooler.eu-west-2.aws.neon.tech"
    assert db["NAME"] == "binless"
    assert db["PASSWORD"] == "p@ss"
    assert db["PORT"] == ""
    assert db["OPTIONS"] == {"sslmode": "require", "channel_binding": "require"}


def test_reads_local_port_and_no_options():
    db = database_from_url("postgres://binless:binless-local@127.0.0.1:5432/binless")
    assert db["PORT"] == "5432"
    assert db["OPTIONS"] == {}


def test_rejects_other_schemes():
    with pytest.raises(ValueError):
        database_from_url("mysql://user:pw@localhost/binless")
