"""Integration tests for the `venues` (name, city) unique constraint.

These run the real Alembic migration (`e6f0a9c3b4d7_add_venues_unique_name_city`)
against a throwaway on-disk SQLite database rather than relying on
`Base.metadata.create_all`, so they exercise the constraint the database
itself enforces, not just the ORM model's declared `__table_args__`.
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


@pytest.fixture
def migrated_db(tmp_path, monkeypatch):
    """A SQLite file migrated up to and including the constraint migration.

    Mirrors a real deployment: `venues` (along with `tours`, `concerts`, and
    `lineup_entries`) is first created from the current models via
    `Base.metadata.create_all` - exactly how `src/main.py` bootstraps the
    app - the database is stamped at `_BASELINE_REVISION`, and then
    `alembic upgrade head` applies the migration under test.
    """
    db_url = f"sqlite:///{tmp_path / 'venue_unique_constraint.db'}"

    bootstrap_engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=bootstrap_engine)
    bootstrap_engine.dispose()

    # `migrations/env.py` reads the connection URL from this module-level
    # constant (not a hardcoded URL in the migration itself), so pointing
    # Alembic at the test database is just a matter of overriding it here.
    monkeypatch.setattr(database_module, "SQLALCHEMY_DATABASE_URL", db_url)

    config = Config("alembic.ini")
    command.stamp(config, _BASELINE_REVISION)
    command.upgrade(config, "head")

    engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session, config
    finally:
        session.close()
        engine.dispose()


def test_duplicate_name_and_city_raises_integrity_error(migrated_db):
    session, _config = migrated_db
    session.add(Venue(name="Madison Square Garden", city="New York", country="USA", capacity=20000))
    session.commit()

    session.add(Venue(name="Madison Square Garden", city="New York", country="Canada", capacity=5000))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_same_name_different_city_succeeds(migrated_db):
    session, _config = migrated_db
    session.add(Venue(name="The Forum", city="Los Angeles", country="USA", capacity=17500))
    session.commit()

    session.add(Venue(name="The Forum", city="Montreal", country="Canada", capacity=21000))
    session.commit()

    venues = session.query(Venue).filter_by(name="The Forum").all()
    assert {v.city for v in venues} == {"Los Angeles", "Montreal"}


def test_downgrade_removes_constraint(migrated_db):
    session, config = migrated_db
    session.close()

    command.downgrade(config, _BASELINE_REVISION)

    engine = sa.create_engine(str(session.bind.url), connect_args={"check_same_thread": False})
    downgraded_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        downgraded_session.add(Venue(name="Wembley Stadium", city="London", country="UK", capacity=90000))
        downgraded_session.commit()
        downgraded_session.add(Venue(name="Wembley Stadium", city="London", country="UK", capacity=90000))
        downgraded_session.commit()
    finally:
        downgraded_session.close()
        engine.dispose()
