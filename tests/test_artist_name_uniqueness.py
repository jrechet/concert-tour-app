"""Tests for the `uq_artists_name` unique constraint, its migration, and the
`get_by_name` lookup helper used to pre-check it (#1020).
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
from src.models import Artist
from src.services.artist_service import get_by_name

# The revision immediately before the artists unique-constraint migration,
# i.e. the state of a database that already has `artists` (created by the
# dedicated migration that introduced the table) but not yet the `name`
# constraint.
_BASELINE_REVISION = "f3a8c2e9b6d1"

# The revision under test. Targeted explicitly (rather than "head") so this
# test stays pinned to the artists constraint migration regardless of
# migrations added afterward.
_TARGET_REVISION = "2fa2316309a8"


@pytest.fixture
def migrated_db(tmp_path, monkeypatch):
    """A SQLite file migrated up to and including the constraint migration.

    Mirrors a real deployment: every table is first created from the
    current models via `Base.metadata.create_all` - exactly how
    `src/main.py` bootstraps the app - the database is stamped at
    `_BASELINE_REVISION`, and then `alembic upgrade head` applies the
    migration under test.
    """
    db_url = f"sqlite:///{tmp_path / 'artist_unique_constraint.db'}"

    bootstrap_engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=bootstrap_engine)
    bootstrap_engine.dispose()

    # `migrations/env.py` reads the connection URL from this module-level
    # constant (not a hardcoded URL in the migration itself), so pointing
    # Alembic at the test database is just a matter of overriding it here.
    monkeypatch.setattr(database_module, "SQLALCHEMY_DATABASE_URL", db_url)

    config = Config("alembic.ini")
    command.stamp(config, _BASELINE_REVISION)

    engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session, config, db_url
    finally:
        session.close()
        engine.dispose()


def test_upgrade_against_fresh_database_runs_cleanly(migrated_db):
    _session, config, _db_url = migrated_db

    command.upgrade(config, _TARGET_REVISION)


def test_upgrade_deduplicates_existing_duplicate_names_before_adding_constraint(tmp_path, monkeypatch):
    """A database at `_BASELINE_REVISION` already holding duplicate artist
    names (and a `lineup_entries` row pointing at one of the duplicates)
    must still reach `_TARGET_REVISION` cleanly, with the duplicates merged
    onto one surviving id and the constraint then enforced going forward.

    Built from raw DDL matching the pre-constraint schema rather than
    `Base.metadata.create_all`: the current `Artist` model already declares
    `uq_artists_name`, so creating the table from the model would enforce
    the constraint before the duplicate data this test needs could even be
    inserted.
    """
    db_url = f"sqlite:///{tmp_path / 'artist_dedupe.db'}"
    bind = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    with bind.begin() as conn:
        conn.execute(sa.text("CREATE TABLE artists (id INTEGER PRIMARY KEY, name VARCHAR(200) NOT NULL)"))
        conn.execute(sa.text(
            "CREATE TABLE lineup_entries ("
            "id INTEGER PRIMARY KEY, concert_id INTEGER NOT NULL, artist_id INTEGER, "
            "artist_name VARCHAR(200) NOT NULL, set_order INTEGER NOT NULL)"
        ))
        conn.execute(sa.text("INSERT INTO artists (name) VALUES ('The Duplicates')"))
        conn.execute(sa.text("INSERT INTO artists (name) VALUES ('The Duplicates')"))
        conn.execute(sa.text("INSERT INTO artists (name) VALUES ('Unique Artist')"))
        duplicate_ids = [
            row[0]
            for row in conn.execute(
                sa.text("SELECT id FROM artists WHERE name = 'The Duplicates' ORDER BY id")
            ).fetchall()
        ]
        survivor_id, merged_id = duplicate_ids
        conn.execute(
            sa.text(
                "INSERT INTO lineup_entries (concert_id, artist_id, artist_name, set_order) "
                "VALUES (1, :artist_id, 'The Duplicates', 1)"
            ),
            {"artist_id": merged_id},
        )
    bind.dispose()

    monkeypatch.setattr(database_module, "SQLALCHEMY_DATABASE_URL", db_url)
    config = Config("alembic.ini")
    command.stamp(config, _BASELINE_REVISION)

    command.upgrade(config, _TARGET_REVISION)

    engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    try:
        with engine.begin() as conn:
            survivors = conn.execute(
                sa.text("SELECT id FROM artists WHERE name = 'The Duplicates'")
            ).fetchall()
            assert [row[0] for row in survivors] == [survivor_id]

            entry_artist_id = conn.execute(
                sa.text("SELECT artist_id FROM lineup_entries WHERE concert_id = 1")
            ).scalar()
            assert entry_artist_id == survivor_id

        session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
        try:
            session.add(Artist(name="The Duplicates"))
            with pytest.raises(IntegrityError):
                session.commit()
        finally:
            session.close()
    finally:
        engine.dispose()


def test_downgrade_removes_constraint(migrated_db):
    session, config, db_url = migrated_db
    command.upgrade(config, _TARGET_REVISION)
    session.close()

    command.downgrade(config, _BASELINE_REVISION)

    engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})
    downgraded_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        downgraded_session.add(Artist(name="Repeatable Name"))
        downgraded_session.commit()
        downgraded_session.add(Artist(name="Repeatable Name"))
        downgraded_session.commit()

        assert downgraded_session.query(Artist).filter_by(name="Repeatable Name").count() == 2
    finally:
        downgraded_session.close()
        engine.dispose()


def test_duplicate_artist_name_raises_integrity_error(db_session):
    db_session.add(Artist(name="Solo Artist"))
    db_session.commit()

    db_session.add(Artist(name="Solo Artist"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_get_by_name_returns_the_matching_artist(db_session):
    artist = Artist(name="Findable Artist")
    db_session.add(artist)
    db_session.commit()
    db_session.refresh(artist)

    found = get_by_name(db_session, "Findable Artist")

    assert found is not None
    assert found.id == artist.id


def test_get_by_name_returns_none_when_no_artist_holds_the_name(db_session):
    assert get_by_name(db_session, "Nobody Named This") is None


def test_get_by_name_returns_none_when_only_match_is_excluded(db_session):
    artist = Artist(name="Self Match Artist")
    db_session.add(artist)
    db_session.commit()
    db_session.refresh(artist)

    assert get_by_name(db_session, "Self Match Artist", exclude_id=artist.id) is None


def test_get_by_name_still_finds_a_different_artist_holding_the_name(db_session):
    renaming_artist = Artist(name="Renaming Artist")
    holder = Artist(name="Taken Name")
    db_session.add_all([renaming_artist, holder])
    db_session.commit()
    db_session.refresh(renaming_artist)
    db_session.refresh(holder)

    found = get_by_name(db_session, "Taken Name", exclude_id=renaming_artist.id)

    assert found is not None
    assert found.id == holder.id
