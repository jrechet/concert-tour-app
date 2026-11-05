"""Tests for the `Venue` model's fields and `(name, city)` unique constraint.

The constraint itself lives only in the Alembic migration
(`e6f0a9c3b4d7_add_venues_unique_name_city`), not in the model's
`__table_args__` (see `src/models/venue.py` for why), so these tests run
against a real database migrated up to that revision - exercising the
constraint the database itself enforces - rather than one built via
`Base.metadata.create_all`.
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


@pytest.fixture
def migrated_session(tmp_path, monkeypatch):
    """A SQLite file migrated up to and including the `venues` unique
    constraint, via the real Alembic migration (not `create_all`) applied
    on top of the app's actual bootstrap (`Base.metadata.create_all` for
    `tours`/`venues`/`concerts`/etc., then Alembic for everything after)."""
    db_url = f"sqlite:///{tmp_path / 'venue_model.db'}"

    bootstrap_engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=bootstrap_engine)
    bootstrap_engine.dispose()

    # `migrations/env.py` reads the connection URL from this module-level
    # constant rather than a hardcoded URL, so pointing Alembic at the test
    # database is just a matter of overriding it here.
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


def test_persisting_a_valid_venue_assigns_id_and_round_trips_fields(migrated_session):
    venue = Venue(name="Madison Square Garden", city="New York", country="USA", capacity=20000)
    migrated_session.add(venue)
    migrated_session.commit()
    migrated_session.refresh(venue)

    assert isinstance(venue.id, int)

    persisted = migrated_session.query(Venue).filter(Venue.id == venue.id).first()
    assert persisted.name == "Madison Square Garden"
    assert persisted.city == "New York"
    assert persisted.country == "USA"
    assert persisted.capacity == 20000


def test_duplicate_name_and_city_raises_integrity_error(migrated_session):
    migrated_session.add(Venue(name="The Forum", city="Los Angeles", country="USA", capacity=17500))
    migrated_session.commit()

    migrated_session.add(Venue(name="The Forum", city="Los Angeles", country="USA", capacity=17500))
    with pytest.raises(IntegrityError):
        migrated_session.commit()
    migrated_session.rollback()


def test_same_name_different_city_succeeds(migrated_session):
    migrated_session.add(Venue(name="The Forum", city="Los Angeles", country="USA", capacity=17500))
    migrated_session.commit()

    migrated_session.add(Venue(name="The Forum", city="Montreal", country="Canada", capacity=21000))
    migrated_session.commit()

    venues = migrated_session.query(Venue).filter_by(name="The Forum").all()
    assert {v.city for v in venues} == {"Los Angeles", "Montreal"}


def test_different_name_same_city_succeeds(migrated_session):
    migrated_session.add(Venue(name="The Forum", city="Los Angeles", country="USA", capacity=17500))
    migrated_session.commit()

    migrated_session.add(Venue(name="Crypto.com Arena", city="Los Angeles", country="USA", capacity=20000))
    migrated_session.commit()

    venues = migrated_session.query(Venue).filter_by(city="Los Angeles").all()
    assert {v.name for v in venues} == {"The Forum", "Crypto.com Arena"}
