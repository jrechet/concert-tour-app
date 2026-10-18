"""Integration tests for the `concerts` (date_time, is_cancelled) composite
index (`a7c4e2f8b1d9_add_concert_date_time_is_cancelled_index`).

Runs the real Alembic migration against a throwaway on-disk SQLite
database, then inspects the resulting index metadata directly, mirroring
`test_venue_unique_constraint.py`.
"""

import sqlalchemy as sa
import pytest
from alembic import command
from alembic.config import Config

from src import models  # noqa: F401  (registers all models on Base.metadata)
from src import database as database_module
from src.database import Base

# The revision immediately before the composite index migration.
_BASELINE_REVISION = "d3e5f7a9c1b2"

# The revision under test, targeted explicitly rather than "head" so this
# test stays pinned to the composite index migration regardless of
# migrations added afterward.
_TARGET_REVISION = "a7c4e2f8b1d9"

_INDEX_NAME = "ix_concerts_date_time_is_cancelled"


@pytest.fixture
def migrated_db(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'concert_date_status_index.db'}"

    bootstrap_engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=bootstrap_engine)
    bootstrap_engine.dispose()

    monkeypatch.setattr(database_module, "SQLALCHEMY_DATABASE_URL", db_url)

    config = Config("alembic.ini")
    command.stamp(config, _BASELINE_REVISION)
    command.upgrade(config, _TARGET_REVISION)

    engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    try:
        yield engine, config
    finally:
        engine.dispose()


def test_upgrade_creates_composite_index(migrated_db):
    engine, _config = migrated_db
    inspector = sa.inspect(engine)

    indexes = {index["name"]: index["column_names"] for index in inspector.get_indexes("concerts")}

    assert _INDEX_NAME in indexes
    assert indexes[_INDEX_NAME] == ["date_time", "is_cancelled"]


def test_downgrade_removes_composite_index(migrated_db):
    engine, config = migrated_db
    engine.dispose()

    command.downgrade(config, _BASELINE_REVISION)

    engine = sa.create_engine(str(engine.url), connect_args={"check_same_thread": False})
    try:
        inspector = sa.inspect(engine)
        indexes = {index["name"] for index in inspector.get_indexes("concerts")}
        assert _INDEX_NAME not in indexes
    finally:
        engine.dispose()
