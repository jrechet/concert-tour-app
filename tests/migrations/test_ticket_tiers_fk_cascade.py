"""Integration tests for the `ticket_tiers.concert_id` FK cascade migration
(`c9d1e3f5a7b2_add_ticket_tiers_concert_fk_cascade`).

`TicketTier.concert_id` already declares `ondelete="CASCADE"` on the
current model, so bootstrapping via plain `Base.metadata.create_all` would
create the FK with that option up front and mask the migration under
test. Instead, `ticket_tiers` is bootstrapped here from an explicit table
definition mirroring the schema as it existed immediately before this
migration (FK with no `ondelete`), with every other table taken from the
real, current metadata.
"""

import sqlalchemy as sa
import pytest
from alembic import command
from alembic.config import Config

from src import models  # noqa: F401  (registers all models on Base.metadata)
from src import database as database_module
from src.database import Base

# The revision immediately before the FK cascade migration.
_BASELINE_REVISION = "b4f6a0d2c8e3"

# The revision under test, targeted explicitly rather than "head" so this
# test stays pinned to this migration regardless of migrations added
# afterward.
_TARGET_REVISION = "c9d1e3f5a7b2"


def _bootstrap_pre_cascade_schema(engine):
    """Create every table as the current models define them, except
    `ticket_tiers`, whose FK has no `ondelete` yet."""
    metadata = sa.MetaData()
    for table in Base.metadata.tables.values():
        if table.name != "ticket_tiers":
            table.to_metadata(metadata)

    sa.Table(
        "ticket_tiers",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("concert_id", sa.Integer, sa.ForeignKey("concerts.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.UniqueConstraint("concert_id", "name", name="uq_ticket_tiers_concert_id_name"),
    )
    metadata.create_all(bind=engine)


@pytest.fixture
def migrated_db(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'ticket_tiers_fk_cascade.db'}"

    bootstrap_engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    _bootstrap_pre_cascade_schema(bootstrap_engine)
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


def _concert_id_fk(engine):
    inspector = sa.inspect(engine)
    for fk in inspector.get_foreign_keys("ticket_tiers"):
        if fk["constrained_columns"] == ["concert_id"]:
            return fk
    return None


def test_upgrade_sets_ondelete_cascade_on_concert_id_fk(migrated_db):
    engine, _config = migrated_db

    fk = _concert_id_fk(engine)

    assert fk is not None
    assert fk["options"].get("ondelete") == "CASCADE"


def test_upgrade_preserves_indexes_and_unique_constraint(migrated_db):
    engine, _config = migrated_db
    inspector = sa.inspect(engine)

    index_names = {index["name"] for index in inspector.get_indexes("ticket_tiers")}
    assert "ix_ticket_tiers_id" in index_names
    assert "ix_ticket_tiers_concert_id" in index_names

    unique_names = {uc["name"] for uc in inspector.get_unique_constraints("ticket_tiers")}
    assert "uq_ticket_tiers_concert_id_name" in unique_names


def test_upgrade_then_downgrade_runs_cleanly_and_removes_cascade(migrated_db):
    engine, config = migrated_db
    engine.dispose()

    command.downgrade(config, _BASELINE_REVISION)

    engine = sa.create_engine(str(engine.url), connect_args={"check_same_thread": False})
    try:
        fk = _concert_id_fk(engine)
        assert fk is not None
        assert fk["options"].get("ondelete") is None
    finally:
        engine.dispose()
