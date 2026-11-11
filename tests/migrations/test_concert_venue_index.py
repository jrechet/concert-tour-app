"""Integration tests for the `concerts` (venue_id, date_time) composite
index (`b4f6a0d2c8e3_add_concert_venue_start_index`).

Runs the real Alembic migration against a throwaway on-disk SQLite
database, then inspects the resulting index metadata directly, mirroring
`test_concert_date_status_index.py`.

Unlike that migration, this index is also declared on the current model's
`__table_args__`, so bootstrapping straight from `Base.metadata` would
already create it and mask the migration under test. The `concerts` table
is therefore copied into a fresh `MetaData` with that one index stripped
before bootstrapping, leaving every other table (and every other index)
exactly as the current models define them.
"""

import sqlalchemy as sa
import pytest
from alembic import command
from alembic.config import Config

from src import models  # noqa: F401  (registers all models on Base.metadata)
from src import database as database_module
from src.database import Base

# The revision immediately before the venue/date_time composite index migration.
_BASELINE_REVISION = "a7c4e2f8b1d9"

# The revision under test, targeted explicitly rather than "head" so this
# test stays pinned to this migration regardless of migrations added
# afterward.
_TARGET_REVISION = "b4f6a0d2c8e3"

_INDEX_NAME = "ix_concerts_venue_id_date_time"


def _bootstrap_pre_index_schema(engine):
    """Create every table as the current models define them, except with
    `_INDEX_NAME` stripped from `concerts` so the migration under test has
    something to do."""
    metadata = sa.MetaData()
    for table in Base.metadata.tables.values():
        copied = table.to_metadata(metadata)
        if table.name == "concerts":
            for index in list(copied.indexes):
                if index.name == _INDEX_NAME:
                    copied.indexes.remove(index)
    metadata.create_all(bind=engine)


@pytest.fixture
def migrated_db(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'concert_venue_index.db'}"

    bootstrap_engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    _bootstrap_pre_index_schema(bootstrap_engine)
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
    assert indexes[_INDEX_NAME] == ["venue_id", "date_time"]


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
