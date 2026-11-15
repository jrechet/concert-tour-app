"""Tests for the `Venue` model's integrity constraints: non-empty name,
positive capacity, and the (name, city) uniqueness constraint that the
`POST`/`PATCH` 409 handling relies on.
"""

import sqlalchemy as sa
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src import models  # noqa: F401  (registers all models on Base.metadata)
from src import database as database_module
from src.database import Base
from src.models import Venue

# The revision immediately before the venues unique-constraint migration,
# i.e. the state of a database that already has `venues` (created the way
# this app actually bootstraps it - see `migrations/env.py`) but not yet the
# (name, city) constraint.
_BASELINE_REVISION = "a3f8c1d4e7b2"

_TARGET_REVISION = "e6f0a9c3b4d7"


def test_persisting_a_venue_with_empty_name_is_rejected(db_session):
    with pytest.raises(ValueError):
        Venue(name="", city="Paris", country="France", capacity=5000)


def test_persisting_a_venue_with_whitespace_only_name_is_rejected(db_session):
    with pytest.raises(ValueError):
        Venue(name="   ", city="Paris", country="France", capacity=5000)


def test_persisting_a_venue_with_zero_capacity_is_allowed(db_session):
    """`0` is an established edge case elsewhere (sold-out/occupancy
    calculations), unlike the `VenueCreate`/`VenueUpdate` API schemas which
    require `capacity > 0`; only a negative capacity is invalid data."""
    venue = Venue(name="Pop-Up Stage", city="Berlin", country="Germany", capacity=0)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)

    assert venue.capacity == 0


def test_persisting_a_venue_with_negative_capacity_is_rejected(db_session):
    with pytest.raises(ValueError):
        Venue(name="Arena", city="Paris", country="France", capacity=-5)


def test_persisting_a_venue_with_null_capacity_succeeds(db_session):
    venue = Venue(name="Arena", city="Paris", country="France", capacity=None)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)

    assert venue.capacity is None


@pytest.fixture
def migrated_session(tmp_path, monkeypatch):
    """A SQLite file migrated up to and including the `venues` unique
    constraint, via the real Alembic migration (not `create_all`) applied
    on top of the app's actual bootstrap (`Base.metadata.create_all` for
    `tours`/`venues`/`concerts`/etc., then Alembic for everything after)."""
    db_url = f"sqlite:///{tmp_path / 'venue_model_constraints.db'}"

    bootstrap_engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=bootstrap_engine)
    bootstrap_engine.dispose()

    monkeypatch.setattr(database_module, "SQLALCHEMY_DATABASE_URL", db_url)

    config = Config("alembic.ini")
    command.stamp(config, _BASELINE_REVISION)
    command.upgrade(config, _TARGET_REVISION)

    engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_duplicate_name_and_city_insert_raises_integrity_error(migrated_session):
    migrated_session.add(Venue(name="The Forum", city="Los Angeles", country="USA", capacity=17500))
    migrated_session.commit()

    migrated_session.add(Venue(name="The Forum", city="Los Angeles", country="Canada", capacity=5000))
    with pytest.raises(IntegrityError):
        migrated_session.commit()
    migrated_session.rollback()
