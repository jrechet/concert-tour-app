"""Integration tests for the `concerts.capacity` column migration
(`9b1e4f7a2c6d_add_concert_capacity_column`).

`Concert.capacity` is already declared directly on the current model, so
bootstrapping via plain `Base.metadata.create_all` would create the column
up front and mask the migration under test. Instead, `concerts` is
bootstrapped here from an explicit `capacity`-less table definition mirroring
the schema as it existed immediately before this migration, with every other
table taken from the real, current metadata.
"""

import sqlalchemy as sa
import pytest
from alembic import command
from alembic.config import Config

from src import models  # noqa: F401  (registers all models on Base.metadata)
from src import database as database_module
from src.database import Base
from src.models.concert import ConcertStatus

# The revision immediately before the capacity column migration.
_BASELINE_REVISION = "2fa2316309a8"

# The revision under test, targeted explicitly rather than "head" so this
# test stays pinned to the capacity migration regardless of migrations added
# afterward.
_TARGET_REVISION = "9b1e4f7a2c6d"


def _bootstrap_pre_capacity_schema(engine):
    """Create every table as the current models define them, except
    `concerts`, which is created without its `capacity` column."""
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
        sa.Column("notes", sa.String(500), nullable=True, default=None),
        sa.Column(
            "status",
            sa.Enum(
                ConcertStatus,
                values_callable=lambda enum_cls: [member.value for member in enum_cls],
                native_enum=False,
                name="concert_status",
            ),
            nullable=False,
            default=ConcertStatus.scheduled,
            server_default=ConcertStatus.scheduled.value,
        ),
    )
    metadata.create_all(bind=engine)


@pytest.fixture
def migrated_db(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'concert_capacity_migration.db'}"

    bootstrap_engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    _bootstrap_pre_capacity_schema(bootstrap_engine)
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


def _capacity_column(engine):
    inspector = sa.inspect(engine)
    for column in inspector.get_columns("concerts"):
        if column["name"] == "capacity":
            return column
    return None


def test_upgrade_adds_nullable_capacity_column(migrated_db):
    engine, _config = migrated_db

    column = _capacity_column(engine)

    assert column is not None
    assert column["nullable"] is True
    assert isinstance(column["type"], sa.Integer)


def test_upgrade_then_downgrade_runs_cleanly_and_removes_capacity_column(migrated_db):
    engine, config = migrated_db
    engine.dispose()

    command.downgrade(config, _BASELINE_REVISION)

    engine = sa.create_engine(str(engine.url), connect_args={"check_same_thread": False})
    try:
        assert _capacity_column(engine) is None
    finally:
        engine.dispose()
