"""Tests for the DB-level guarantees on `LineupEntry`: the unique constraint
on (concert_id, set_order) enforced by the database itself (not just the
ORM event listener), and the `created_at` timestamp."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from src.models import LineupEntry
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _build_concert(db_session):
    base_time = datetime(2026, 11, 1, 20, 0, 0)
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name="Test Tour",
        artist="Test Artist",
        start_date=base_time.date(),
        end_date=(base_time + timedelta(days=10)).date(),
        status="planned",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time
    )


def test_created_at_is_populated_on_insert(db_session):
    concert = _build_concert(db_session)
    entry = LineupEntry(concert_id=concert.id, artist_name="Opener", set_order=1)
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)

    assert entry.created_at is not None


def test_duplicate_set_order_violates_db_unique_constraint(db_session):
    """Inserting through Core (bypassing the ORM's `before_insert` event
    listener) must still be rejected by the database's own unique
    constraint, since the constraint - not the listener - is the real
    guarantee against set-order collisions."""
    concert = _build_concert(db_session)
    table = LineupEntry.__table__
    db_session.execute(
        table.insert().values(concert_id=concert.id, artist_name="First Opener", set_order=1)
    )
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.execute(
            table.insert().values(concert_id=concert.id, artist_name="Second Opener", set_order=1)
        )
    db_session.rollback()


def test_concert_lineup_relationship_uses_back_populates(db_session):
    concert = _build_concert(db_session)
    entry = LineupEntry(concert_id=concert.id, artist_name="Opener", set_order=1)
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)

    assert entry.concert.id == concert.id
    assert entry in concert.lineup
