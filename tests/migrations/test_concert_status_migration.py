"""Integration tests for the `concerts.status` column migration
(`822d8600f5e7_add_concert_status`).

Like `test_concert_notes_migration.py`, `Concert.status` is already declared
directly on the current model, so bootstrapping via plain
`Base.metadata.create_all` would create the column up front and mask the
migration under test. Instead, `concerts` is bootstrapped here from an
explicit `status`-less table definition mirroring the schema as it existed
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

# The revision immediately before the status column migration.
_BASELINE_REVISION = "c9d1e3f5a7b2"

# The revision under test, targeted explicitly rather than "head" so this
# test stays pinned to the status migration regardless of migrations added
# afterward.
_TARGET_REVISION = "822d8600f5e7"


def _bootstrap_pre_status_schema(engine):
    """Create every table as the current models define them, except
    `concerts`, which is created without its `status` column."""
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
        sa.Column("cancelled_with_tour", sa.Boolean, nullable=False, default=False, server_default="0"),
        sa.Column("notes", sa.String(500), nullable=True),
    )
    metadata.create_all(bind=engine)


@pytest.fixture
def migrated_db(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'concert_status_migration.db'}"

    bootstrap_engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    _bootstrap_pre_status_schema(bootstrap_engine)

    with bootstrap_engine.connect() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO tours (name, artist, start_date, end_date, status) "
                "VALUES ('Existing Tour', 'Existing Artist', '2024-01-01', '2024-01-02', 'planned')"
            )
        )
        conn.execute(
            sa.text(
                "INSERT INTO venues (name, city, country, capacity) "
                "VALUES ('Existing Venue', 'Existing City', 'USA', 100)"
            )
        )
        conn.execute(
            sa.text(
                "INSERT INTO concerts (tour_id, venue_id, date_time, tickets_sold, is_cancelled, cancelled_with_tour) "
                "VALUES (1, 1, '2024-01-01 20:00:00', 0, 0, 0)"
            )
        )
        conn.commit()
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


def _status_column(engine):
    inspector = sa.inspect(engine)
    for column in inspector.get_columns("concerts"):
        if column["name"] == "status":
            return column
    return None


def test_upgrade_adds_non_nullable_status_column(migrated_db):
    engine, _config = migrated_db

    column = _status_column(engine)

    assert column is not None
    assert column["nullable"] is False


def test_upgrade_backfills_existing_rows_with_scheduled(migrated_db):
    engine, _config = migrated_db

    with engine.connect() as conn:
        rows = conn.execute(sa.text("SELECT status FROM concerts")).fetchall()

    assert rows == [("scheduled",)]


def test_upgrade_then_downgrade_runs_cleanly_and_removes_status_column(migrated_db):
    engine, config = migrated_db
    engine.dispose()

    command.downgrade(config, _BASELINE_REVISION)

    engine = sa.create_engine(str(engine.url), connect_args={"check_same_thread": False})
    try:
        assert _status_column(engine) is None
    finally:
        engine.dispose()
