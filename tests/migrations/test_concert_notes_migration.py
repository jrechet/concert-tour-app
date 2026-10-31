"""Integration tests for the `concerts.notes` column migration
(`a3f8c1d4e7b2_add_concert_notes_column`).

Unlike `test_venue_unique_constraint.py` and `test_concert_date_status_index.py`,
`Concert.notes` is already declared directly on the current model, so
bootstrapping via plain `Base.metadata.create_all` would create the column
up front and mask the migration under test (it would try to add a column
that already exists). Instead, `concerts` is bootstrapped here from an
explicit `notes`-less table definition mirroring the schema as it existed
immediately before this migration, with every other table taken from the
real, current metadata.
"""

import sqlalchemy as sa
import pytest
from alembic import command
from alembic.config import Config

from src import models  # noqa: F401  (registers all models on Base.metadata)
from src import database as database_module
from src.database import Base

# The revision immediately before the notes column migration.
_BASELINE_REVISION = "f1a2b3c4d5e6"

# The revision under test, targeted explicitly rather than "head" so this
# test stays pinned to the notes migration regardless of migrations added
# afterward.
_TARGET_REVISION = "a3f8c1d4e7b2"


def _bootstrap_pre_notes_schema(engine):
    """Create every table as the current models define them, except
    `concerts`, which is created without its `notes` column."""
    metadata = sa.MetaData()
    for table in Base.metadata.tables.values():
        if table.name != "concerts":
            table.to_metadata(metadata)

    sa.Table(
        "concerts",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("tour_id", sa.Integer, sa.ForeignKey("tours.id"), nullable=False, index=True),
        sa.Column("venue_id", sa.Integer, sa.ForeignKey("venues.id"), nullable=False, index=True),
        sa.Column("date_time", sa.DateTime, nullable=False, index=True),
        sa.Column("ticket_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("tickets_sold", sa.Integer, nullable=False, default=0),
        sa.Column("is_cancelled", sa.Boolean, nullable=False, default=False, server_default="0"),
        sa.Column("cancellation_reason", sa.String(500), nullable=True),
    )
    metadata.create_all(bind=engine)


@pytest.fixture
def migrated_db(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'concert_notes_migration.db'}"

    bootstrap_engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    _bootstrap_pre_notes_schema(bootstrap_engine)
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


def _notes_column(engine):
    inspector = sa.inspect(engine)
    for column in inspector.get_columns("concerts"):
        if column["name"] == "notes":
            return column
    return None


def test_upgrade_adds_nullable_notes_column(migrated_db):
    engine, _config = migrated_db

    column = _notes_column(engine)

    assert column is not None
    assert column["nullable"] is True
    assert column["type"].length == 500


def test_upgrade_then_downgrade_runs_cleanly_and_removes_notes_column(migrated_db):
    engine, config = migrated_db
    engine.dispose()

    command.downgrade(config, _BASELINE_REVISION)

    engine = sa.create_engine(str(engine.url), connect_args={"check_same_thread": False})
    try:
        assert _notes_column(engine) is None
    finally:
        engine.dispose()
